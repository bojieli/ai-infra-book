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

#include "llvm/Support/CommandLine.h"
#include "mlir/Dialect/Func/IR/FuncOps.h"
#include "mlir/Pass/PassManager.h"
#include "mlir/Pass/PassOptions.h"
#include "mlir/Pass/PassRegistry.h"
#include "mlir/Support/LLVM.h"
#include "mlir/Transforms/Passes.h"
#include "shardy/common/file_utils.h"
#include "shardy/dialect/sdy/transforms/common/propagation_options.h"
#include "shardy/dialect/sdy/transforms/export/passes.h"
#include "shardy/dialect/sdy/transforms/import/passes.h"
#include "shardy/dialect/sdy/transforms/propagation/auto_partitioner_registry.h"
#include "shardy/dialect/sdy/transforms/propagation/passes.h"
#include "shardy/dialect/sdy/transforms/propagation/user_priority_propagation.h"

namespace mlir {
namespace sdy {

namespace {

void populateExportOptions(ExportOptions& options,
                           const PropagationOptions& propOptions) {
  options.replicaCount = propOptions.replicaCount;
  options.partitionCount = propOptions.partitionCount;
  options.keepShardingRules = propOptions.keepShardingRules;
  options.dumpDirectory = propOptions.dumpDirectory.str();
  options.avoidExportForPartitioning = propOptions.avoidExportForPartitioning;
  options.enableInsertExplicitCollectives =
      propOptions.enableInsertExplicitCollectives;
  options.removeAllGatherReduceScatterForCMV1 =
      propOptions.removeAllGatherReduceScatterForCMV1;
  options.dumpShardingOrigins = propOptions.debugShardingOrigins;
  options.dumpPropagationEdges = propOptions.debugPropagationEdgeSharding;
  // TODO(enver): Drop avoidReshardsOnCalls in favor of dedupFunctionsFully.
  options.avoidReshardsOnCalls = propOptions.dedupFunctionsFully;
  options.updateNonDivisibleInputOutputShardings =
      propOptions.updateNonDivisibleInputOutputShardings;
  options.inlineMeshes = propOptions.inlineMeshes;
  options.enablePerInstructionPartitioning =
      propOptions.enablePerInstructionPartitioning;
  options.perInstructionPartitioningFilter =
      propOptions.perInstructionPartitioningFilter;
}

}  // namespace

void addPropagationPipeline(OpPassManager& pm, int& dumpIndex,
                            const PropagationOptions& options) {
  addImportPipeline(pm, dumpIndex, options);
  if (options.dedupFunctionsFully) {  // Aggressive compilation mode.
    pm.addPass(createAddFuncDataFlowEdgesPass());
  } else {  // Conservative compilation mode.
    pm.addPass(createFlattenCallGraphPass());
    pm.addPass(createSymbolDCEPass());  // After FlattenCallGraphPass.
    pm.addPass(createImportFuncCallsPass());
    pm.addPass(createSymbolDCEPass());  // After ImportFuncCallsPass.
    // TODO(b/517993355): Move ApplyShardingConstraints and ShardingGroupImport
    // passes back to the import pipeline and before inlining.
    pm.addPass(
        createApplyShardingConstraintsPass(ApplyShardingConstraintsPassOptions{
            options.debugShardingOrigins,
            options.debugPropagationEdgeSharding}));
    // The sharding group import pass must run after applying sharding
    // constraints. This ensures we can detect sharding conflicts between group
    // members which have pre-propagation shardings due to sharding constraints.
    pm.addPass(createShardingGroupImportPass());
  }
  {
    PropagationOptions optionsWithKeepShardingRules = options;
    optionsWithKeepShardingRules.keepShardingRules = true;
    // We intentionally don't increment the dump index here, since this pass
    // might dump 0 to multiple files, and will use a nested dump index.
    pm.addPass(createPreOrderFuncsPass());
    pm.addPass(createUserPriorityPropagationPass(optionsWithKeepShardingRules,
                                                 dumpIndex));
  }
  if (options.dedupFunctionsFully) {  // Aggressive compilation mode.
    pm.addPass(createPropagateToFuncResultsPass());
    pm.addNestedPass<func::FuncOp>(createSinkFuncDataFlowEdgesPass());
  } else {  // Conservative compilation mode.
    pm.addPass(createExportNamedComputationsPass());
    pm.addPass(createPropagateToFuncResultsPass());
  }
  pm.addPass(createUnflattenCallGraphPass());
  pm.addPass(createSymbolDCEPass());  // After UnflattenCallGraphPass.
  if (options.enableAutoPartitioning) {
    pm.addPass(createSaveModuleOpPass(options.dumpDirectory,
                                      "propagation_before_auto_partitioning",
                                      dumpIndex++));
    AutoPartitionerRegistry::addPasses(pm);
  }
  pm.addPass(createInsertFuncCallReshardsPass());
  ExportOptions exportOptions;
  populateExportOptions(exportOptions, options);
  addExportPipeline(pm, dumpIndex, exportOptions);
}

void addPropagationPipeline(OpPassManager& pm,
                            const PropagationOptions& options) {
  int dumpIndex = 1;
  addPropagationPipeline(pm, dumpIndex, options);
}

namespace {

struct PropagationOptionsOptions
    : public PassPipelineOptions<PropagationOptionsOptions> {
  Option<bool> dedupFunctionsFully{
      *this, "dedup-functions-fully",
      llvm::cl::desc("Whether to dedup functions fully."),
      llvm::cl::init(false)};
};

}  // namespace

void registerPropagationPipeline() {
  PassPipelineRegistration<PropagationOptionsOptions>(
      "sdy-propagation-pipeline",
      "Runs the SDY propagation pass, preceded by a sequence of import passes "
      "needed as a pre-processing step for propagation",
      [](OpPassManager& pm, const PropagationOptionsOptions& options) {
        PropagationOptions propOptions;
        propOptions.dedupFunctionsFully = options.dedupFunctionsFully;
        propOptions.inlineMeshes = false;

        return addPropagationPipeline(pm, propOptions);
      });
}

}  // namespace sdy
}  // namespace mlir
