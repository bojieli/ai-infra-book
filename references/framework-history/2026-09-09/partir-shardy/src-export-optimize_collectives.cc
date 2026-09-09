/* Copyright 2026 The Shardy Authors.

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

#include <cstdint>
#include <optional>
#include <utility>

#include "mlir/Dialect/Func/IR/FuncOps.h"  // IWYU pragma: keep
#include "mlir/IR/BuiltinOps.h"
#include "mlir/IR/PatternMatch.h"
#include "mlir/IR/SymbolTable.h"
#include "mlir/Pass/Pass.h"  // IWYU pragma: keep
#include "mlir/Support/LogicalResult.h"
#include "mlir/Transforms/GreedyPatternRewriteDriver.h"
#include "shardy/dialect/sdy/ir/dialect.h"  // IWYU pragma: keep
#include "shardy/dialect/sdy/transforms/export/optimize_collectives_util.h"
#include "shardy/dialect/sdy/transforms/export/passes.h"  // IWYU pragma: keep
#include "stablehlo/dialect/StablehloOps.h"               // IWYU pragma: keep

namespace mlir {
namespace sdy {

#define GEN_PASS_DEF_OPTIMIZECOLLECTIVESPASS
#include "shardy/dialect/sdy/transforms/export/passes.h.inc"

namespace {

// Pattern that optimizes collective permute preceding an all-to-all chain.
class CollectivePermuteOptimizationPattern
    : public OpRewritePattern<CollectivePermuteOp> {
 public:
  using OpRewritePattern<CollectivePermuteOp>::OpRewritePattern;

  LogicalResult matchAndRewrite(CollectivePermuteOp cpOp,
                                PatternRewriter& rewriter) const override {
    SymbolTable symbolTable(cpOp->getParentOfType<ModuleOp>());
    std::optional<int64_t> splitDim = getSplitDimension(cpOp, symbolTable);
    if (!splitDim) {
      return failure();
    }

    std::optional<AllToAllChain> chain = extractAllToAllChain(cpOp, *splitDim);
    if (!chain) {
      return failure();
    }

    if (!isChainOptimizable(*chain, *splitDim, symbolTable)) {
      return failure();
    }

    std::optional<AllToAllRewritePlan> plan =
        computeRewritePlan(*chain, *splitDim, symbolTable);
    if (!plan) {
      return failure();
    }

    return rewriteAllToAllChain(*chain, *plan, rewriter);
  }
};

struct OptimizeCollectivesPass
    : public impl::OptimizeCollectivesPassBase<OptimizeCollectivesPass> {
  using OptimizeCollectivesPassBase::OptimizeCollectivesPassBase;

 protected:
  void runOnOperation() final {
    RewritePatternSet patterns(&getContext());
    patterns.add<CollectivePermuteOptimizationPattern>(patterns.getContext());
    if (failed(applyPatternsGreedily(getOperation(), std::move(patterns)))) {
      signalPassFailure();
    }
  }
};

}  // namespace

}  // namespace sdy
}  // namespace mlir
