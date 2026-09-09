/* Copyright 2024 The Shardy Authors.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
==============================================================================*/

#include "shardy/dialect/sdy/transforms/propagation/user_priority_propagation.h"

#include <cassert>
#include <cstdint>
#include <iterator>
#include <memory>
#include <utility>
#include <variant>

#include "llvm/ADT/DenseSet.h"
#include "llvm/ADT/MapVector.h"
#include "llvm/ADT/STLExtras.h"
#include "llvm/Support/FormatVariadic.h"
#include "mlir/IR/BuiltinOps.h"
#include "mlir/IR/MLIRContext.h"
#include "mlir/IR/SymbolTable.h"
#include "mlir/IR/Value.h"
#include "mlir/Pass/Pass.h"
#include "mlir/Pass/PassManager.h"
#include "mlir/Pass/PassRegistry.h"
#include "mlir/Support/LLVM.h"
#include "mlir/Support/LogicalResult.h"
#include "shardy/common/file_utils.h"
#include "shardy/dialect/sdy/ir/dialect.h"
#include "shardy/dialect/sdy/transforms/common/propagation_options.h"
#include "shardy/dialect/sdy/transforms/common/sharding_walker.h"
#include "shardy/dialect/sdy/transforms/propagation/basic_propagation.h"
#include "shardy/dialect/sdy/transforms/propagation/op_priority_propagation.h"
#include "shardy/dialect/sdy/transforms/propagation/sharding_group_map.h"

namespace mlir {
namespace sdy {

#define GEN_PASS_DEF_USERPRIORITYPROPAGATIONPASS
#include "shardy/dialect/sdy/transforms/propagation/passes.h.inc"

namespace {

// A value or func result and its original sharding.
struct ShardingReference {
  ValueOrFuncResult valueOrFuncResult;
  TensorShardingAttr sharding;

  ShardingReference(const ValueOrFuncResult& valueOrFuncResult,
                    TensorShardingAttr sharding)
      : valueOrFuncResult(valueOrFuncResult), sharding(sharding) {}
};

// References to a subset of value and function result shardings of a function.
using ShardingReferences = SmallVector<ShardingReference>;

using PriorityToShardingReferences =
    llvm::SmallMapVector<int64_t, ShardingReferences, 4>;

using PriorityShardingReferences = std::pair<int64_t, ShardingReferences>;

// Returns an updated sharding of `curSharding` by setting the sharding of each
// dimension whose priority equals `curPriority` to the corresponding dimension
// sharding in `originalSharding`, and removing the sharding axes from the
// replicated set.
TensorShardingAttr getUpdatedShardingForPriority(
    TensorShardingAttr curSharding, TensorShardingAttr originalSharding,
    int64_t curPriority) {
  assert(curSharding);
  SmallVector<DimensionShardingAttr> newDimShardings(
      curSharding.getDimShardings());
  llvm::SmallDenseSet<AxisRefAttr> seenAxesWithCurrentPriority;
  for (auto [newDimSharding, originalDimSharding] :
       llvm::zip_equal(newDimShardings, originalSharding.getDimShardings())) {
    if (originalDimSharding.getPriorityOrDefault() == curPriority) {
      assert(newDimSharding.getIsClosed() && newDimSharding.emptyAxes());
      newDimSharding = originalDimSharding.dropPriority();
      seenAxesWithCurrentPriority.insert(originalDimSharding.axis_begin(),
                                         originalDimSharding.axis_end());
    }
  }
  // No need to sort the new vector since `copy_if` maintains order.
  SmallVector<AxisRefAttr> newReplicatedAxes;
  llvm::copy_if(curSharding.getReplicatedAxes(),
                std::back_inserter(newReplicatedAxes), [&](AxisRefAttr axis) {
                  return !seenAxesWithCurrentPriority.contains(axis);
                });
  return TensorShardingAttr::get(
      curSharding.getContext(), curSharding.getMeshOrRef(), newDimShardings,
      newReplicatedAxes, curSharding.getUnreducedAxes(),
      curSharding.getReductionOp());
}

// Updates the current sharding of all referenced values and function results in
// `shardingReferences` for the given priority (see
// `getUpdatedShardingForPriority`).
void updateReferencedShardingsForPriority(
    const ShardingReferences& shardingReferences, int64_t curPriority) {
  for (const auto& [valueOrFuncResult, originalSharding] : shardingReferences) {
    transformSharding(
        valueOrFuncResult,
        [&, originalSharding = originalSharding](TensorShardingAttr sharding) {
          return getUpdatedShardingForPriority(sharding, originalSharding,
                                               curPriority);
        });
  }
}

// Returns an initialized sharding for the first iteration (priority 0) such
// that all dimension shardings in `originalSharding` that have a priority >0
// become empty and closed, and their original sharding axes are moved to the
// replicated set.
//
// Dimension shardings with an explicit priority 0 will be the same except their
// priority is dropped.
TensorShardingAttr getInitializedSharding(TensorShardingAttr originalSharding,
                                          const SymbolTable& symbolTable) {
  MLIRContext* ctx = originalSharding.getContext();
  SmallVector<DimensionShardingAttr> newDimShardings(
      originalSharding.getDimShardings());
  SmallVector<AxisRefAttr> newReplicatedAxes(
      originalSharding.getReplicatedAxes());
  for (DimensionShardingAttr& dimSharding : newDimShardings) {
    if (dimSharding.getPriorityOrDefault() == 0) {
      dimSharding = dimSharding.dropPriority();
    } else {
      newReplicatedAxes.append(dimSharding.axis_begin(),
                               dimSharding.axis_end());
      dimSharding = DimensionShardingAttr::get(ctx, {}, /*isClosed=*/true);
    }
  }
  MeshAttr mesh = originalSharding.getMesh(symbolTable);
  assert(mesh && "unknown mesh");
  llvm::sort(newReplicatedAxes, AxisRefAttr::getMeshComparator(mesh));
  // TODO(tomnatan): we need to merge split axes and split them again when
  // updating? or can we assume we won't see split axes?

  return TensorShardingAttr::get(
      ctx, originalSharding.getMeshOrRef(), newDimShardings, newReplicatedAxes,
      originalSharding.getUnreducedAxes(), originalSharding.getReductionOp());
}

// Clears `priorities` and add all non-zero priorities in `sharding` to it.
void clearAndAddNonZeroPriorities(TensorShardingAttr sharding,
                                  llvm::SmallDenseSet<int64_t>& priorities) {
  priorities.clear();
  for (DimensionShardingAttr dimSharding : sharding.getDimShardings()) {
    if (int64_t priority = dimSharding.getPriorityOrDefault(); priority > 0) {
      priorities.insert(priority);
    }
  }
}

// Traverses `moduleOp` and for each value or func result with a sharding:
//   - Adds {value / func result, sharding} to the sharding references of each
//     non-zero priority in its dimension shardings.
//   - Initializes the tensor's current sharding for the first iteration (see
//     `getInitializedSharding`).
// If a dimension sharding doesn't have a user-defined priority,
// `kDefaultPriority` is used.
//
// Returns a vector of `PriorityShardingReferences` sorted by priority.
SmallVector<PriorityShardingReferences>
getShardingReferencesPerPriorityAndInitialize(ModuleOp moduleOp,
                                              const SymbolTable& symbolTable) {
  PriorityToShardingReferences priorityToShardingReferences;
  llvm::SmallDenseSet<int64_t> prioritiesInSharding;
  transformShardings(moduleOp, [&](TensorShardingAttr sharding,
                                   const ValueOrFuncResult& valueOrFuncResult) {
    // TODO(b/380881922): We should be adding the data flow edges into the map
    // to make sure the in/out shardings on ManualComputationOp are updated.
    // TODO(b/391545244): remove the extra `*value` check which is only needed
    // since we add a null `Value` during the `transformShardings` walk.
    if (auto* value = std::get_if<Value>(&valueOrFuncResult);
        value && *value && DataFlowEdgeOp::lookup(*value)) {
      return sharding;
    }
    clearAndAddNonZeroPriorities(sharding, prioritiesInSharding);
    for (int64_t priority : prioritiesInSharding) {
      priorityToShardingReferences[priority].emplace_back(valueOrFuncResult,
                                                          sharding);
    }
    return getInitializedSharding(sharding, symbolTable);
  });
  // Finally we take the vector of `priorityToShardingReferences` and sort it by
  // priority.
  SmallVector<PriorityShardingReferences> priorityShardingReferencesVec =
      priorityToShardingReferences.takeVector();
  llvm::sort(
      priorityShardingReferencesVec,
      [](const PriorityShardingReferences& a,
         const PriorityShardingReferences& b) { return a.first < b.first; });

  return priorityShardingReferencesVec;
}

// The user-priority propagation pass that uses the default implementation of
// `UserPriorityPropagationPassImpl`.
struct UserPriorityPropagationPass
    : public impl::UserPriorityPropagationPassBase<
          UserPriorityPropagationPass> {
  using UserPriorityPropagationPassBase::UserPriorityPropagationPassBase;

  explicit UserPriorityPropagationPass(const PropagationOptions& options,
                                       int curDumpIndex) {
    setPropagationOptions(options);
    this->dumpIndex = curDumpIndex;
  }
};

void saveModuleOpAfterPriority(ModuleOp moduleOp, StringRef dumpDirectory,
                               int64_t priority, int dumpIndex) {
  saveModuleOp(
      moduleOp, dumpDirectory,
      llvm::formatv("propagation_after_user_priority_{0}", priority).str(),
      dumpIndex);
}

}  // namespace

LogicalResult UserPriorityPropagationPassImpl::propagate(
    ModuleOp moduleOp, const SymbolTable& symbolTable,
    const ShardingGroupMap& shardingGroupMap,
    GetDirectionToPropagateFn getDirectionToPropagate) {
  SmallVector<PriorityShardingReferences> shardingReferencesPerPriority =
      getShardingReferencesPerPriorityAndInitialize(moduleOp, symbolTable);
  // We first run the first iteration (priority 0):
  if (failed(OpPriorityPropagationPassImpl::propagate(
          moduleOp, symbolTable, shardingGroupMap, getDirectionToPropagate))) {
    return failure();
  }
  int64_t prevPriority = 0;
  // Then we run the remaining iterations (priority >0):
  for (const auto& [priority, shardingReferences] :
       shardingReferencesPerPriority) {
    saveModuleOpAfterPriority(moduleOp, dumpDirectory, prevPriority, dumpIndex);
    updateReferencedShardingsForPriority(shardingReferences, priority);
    if (failed(OpPriorityPropagationPassImpl::propagate(
            moduleOp, symbolTable, shardingGroupMap,
            getDirectionToPropagate))) {
      return failure();
    }
    prevPriority = priority;
  }

  return success();
}

std::unique_ptr<Pass> createUserPriorityPropagationPass(
    const PropagationOptions& options, int dumpIndex) {
  return std::make_unique<UserPriorityPropagationPass>(options, dumpIndex);
}

}  // namespace sdy
}  // namespace mlir
