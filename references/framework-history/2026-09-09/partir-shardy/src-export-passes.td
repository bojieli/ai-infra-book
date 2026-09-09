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

include "mlir/Pass/PassBase.td"

def ShardingConstraintToReshardPass : Pass<"sdy-sharding-constraint-to-reshard", "func::FuncOp"> {
  let summary = "Converts ShardingConstraintOp into ReshardOp.";
  let dependentDialects = ["mlir::sdy::SdyDialect"];
}

def SinkDataFlowEdgesPass : Pass<"sdy-sink-data-flow-edges", "func::FuncOp"> {
  let summary = "Sinks all `DataFlowEdgeOp` into their input.";
  let description = [{
    Moves the sharding of each `DataFlowEdgeOp` to its input (the root target of
    the edge), and replaces the op with its input.
  }];
  let dependentDialects = ["mlir::sdy::SdyDialect"];
  //TODO(tomnatan): consider moving the sharding to all targets that can have a sharding attached.

  let options = [
    Option<"sinkDebugShardingOrigins", "sink-debug-sharding-origins", "bool",
           /*default=*/"false",
           "Whether to sink the debug sharding origins info. See "
           "`debug-sharding-origins` option in propagation for more info.">,
    Option<"sinkDebugPropagationEdgeSharding",
           "sink-debug-propagation-edge-sharding", "bool",
           /*default=*/"false",
           "Whether to sink the debug propagation edge sharding info. See "
           "`debug-propagation-edge-sharding` option in propagation for more "
           "info.">,
  ];
}

def SinkFuncDataFlowEdgesPass : Pass<"sdy-sink-func-data-flow-edges", "func::FuncOp"> {
  let summary = "Sinks all `FuncDataFlowEdgeOp` into their input.";
  let description = [{
    Moves the sharding of each `FuncDataFlowEdgeOp` to its input and replaces
    the op with its input.
  }];
  let dependentDialects = ["mlir::sdy::SdyDialect"];
}

def UpdateNonDivisibleInputOutputShardingsPass : Pass<"sdy-update-non-divisible-input-output-shardings", "ModuleOp"> {
  let summary = "Makes FuncOp inputs/outputs evenly sharded, removing any need for padding due to non-divisible shardings.";
  let description = [{
    Users of Shardy expect the function inputs/outputs to be evenly
    divisible/shardable to avoid requiring padding their tensors. Propagation
    may make inputs/outputs have non-divisible shardings, so this pass updates
    them to the largest dimension sharding prefix of the original sharding that
    is evenly sharded.
  }];
  let dependentDialects = ["mlir::sdy::SdyDialect"];
}

def PadForDivisibilityPass : Pass<"sdy-pad-for-divisibility", "func::FuncOp"> {
  let summary = "Pads tensors with non-divisible shardings to divisible shapes.";
  let dependentDialects = ["mlir::sdy::SdyDialect", "mlir::stablehlo::StablehloDialect"];
}

def RemoveSubAxesInInputOutputShardingsPass : Pass<"sdy-remove-sub-axes-in-input-output-shardings", "ModuleOp"> {
  let summary = "Removes sub-axes in input/output shardings.";
  let description = [{
    Some users of Shardy expect the function inputs/outputs to have shardings
    without sub-axes. This pass removes sub-axes and their trailing axes from
    input/output open dimension shardings. This pass is usually after
    `sdy-update-non-divisible-input-output-shardings` to ensure that the removal
    of sub-axes does not introduce any non-divisible shardings.
  }];
  let dependentDialects = ["mlir::sdy::SdyDialect"];
}

def InsertExplicitReshardsPass : Pass<"sdy-insert-explicit-reshards", "func::FuncOp"> {
  let summary = "Inserts explicit reshards to make all operations have compatible shardings.";
  let description = [{
    A compatible sharding essentially means that the operation can accept the
    sharded operands and produce a sharded result without requiring any reshard
    communications (note that the operation might still require communication
    such as all-reduce or halo-swaps).

    After propagation, some operations may still have incompatible shardings.

    Note that when an axis (or sub-axis) is used to shard non-corresponding
    dimensions (e.g. non-contracting dimensions in matmul) across multiple
    tensors, or when an axis shards a dimension in one tensor but not the
    corresponding dimension in the other tensor, it is said that the operation
    has a sharding conflict. Hence, after this pass, the operations become
    conflict-free.

    This pass injects reshard operations explicitly so that, for each operation,
    corresponding dimensions become sharded in the same way across all operands
    and results, and every axis (or sub-axis) can only be used to shard a single
    dimension type.

    Example:

    Input:
    ```mlir
    mesh = <"x"=4, "y"=2>
    %lhs : tensor<8x32xf32> {sdy.sharding=<@mesh, \[{"x"}, {"y"}\]>}
    %rhs : tensor<32x16xf32> {sdy.sharding=<@mesh, \[{"y"}, {"x"}\]>}
    stablehlo.dot %lhs, %rhs {sdy.sharding_per_value=<[<@mesh, \[{"x"}, {}\]>]>}
      : (tensor<8x32xf32>, tensor<32x16xf32>) -> tensor<8x16xf32>
    ```

    Output:
    ```mlir
    sdy.mesh = <"x"=4, "y"=2>
    %lhs : tensor<8x32xf32> {sdy.sharding=<@mesh, \[{"x"}, {"y"}\]>}
    %rhs : tensor<32x16xf32> {sdy.sharding=<@mesh, \[{"y"}, {"x"}\]>}
    %0 = sdy.reshard %rhs <@mesh, \[{"y"}, {}\]> : tensor<32x16xf32>
    stablehlo.dot %lhs, %0 {sdy.sharding_per_value=<[<@mesh, \[{"x"}, {}\]>]>}
      : (tensor<8x32xf32>, tensor<32x16xf32>) -> tensor<8x16xf32>
    ```

    In the example above, `lhs` and `rhs` are both sharded on axis "x" on their
    non-contracting dimensions, which is incompatible. The pass inserts an
    explicit reshard on `rhs` before the dot operation, so that the dot
    operation has compatible shardings.
  }];
  let dependentDialects = ["mlir::sdy::SdyDialect"];
  // TODO(b/402429253): delete when explicit reshards is enabled by default.
  // The non-full version allows us to insert explicit reshards on specific
  // operations for optimizations.
  let options = [
      Option<"enableFullVersion", "enable-full-version",
            "bool", /*default=*/"false",
            "Enable full version.">,
    ];
}

def ResolveSingleDeviceShardingPass
    : Pass<"sdy-resolve-single-device-sharding", "func::FuncOp"> {
  let summary = "Lowers single-device operations into stablehlo.if guarded by target device ID.";
  let dependentDialects = ["mlir::sdy::SdyDialect", "mlir::stablehlo::StablehloDialect"];
  let options = [
    Option<"replicaCount", "replica-count", "int64_t", /*default=*/"1",
           "Number of replicas per partition.">,
    Option<"partitionCount", "partition-count", "int64_t", /*default=*/"1",
           "Number of partitions per replica.">,
  ];
}

def VerifyUnreducedAxesPass : Pass<"sdy-verify-unreduced-axes", "func::FuncOp"> {
  let summary = "Verifies the consistency of unreduced axis usage.";
  let description = [{
    Verifies that for every operation, if its operands have unreduced axes, the
    operation either explicitly reduces them (e.g., via `sdy.reshard`) or passes
    them through to its results (or is a bounding operation like `func.call`).
  }];
  let dependentDialects = ["mlir::sdy::SdyDialect"];
}

def ReshardToCollectivesPass : Pass<"sdy-reshard-to-collectives", "func::FuncOp"> {
  let summary = "Converts ReshardOp into various Shardy collective ops.";
  let description = [{
    Matches reshard ops and rewrites them into various Shardy collective
    ops. After this pass, no reshard ops remain in the module.

    Optionally if `keepRedundantReshards` is true, the only reshard ops that
    remain are the redundant ones. By default it assumes that explicit reshards
    have already been inserted (`sdy-insert-explicit-reshards`) and does not
    keep redundant reshards. It should keep redundant reshards if explicit
    reshards may have not been already inserted.

    Example:

    Input:
    ```mlir
    mesh = <"x"=2, "y"=2, "z"=2>
    %0 : tensor<16x2xf32> {sdy.sharding<@mesh, \[{"x", "y", "z"}, {}\]>
    %1 = sdy.reshard %arg0 <@mesh, \[{"x"}, {}\]> : tensor<16x2xf32>
    ```

    Output:
    ```mlir
    mesh = <"x"=2, "y"=2, "z"=2>
    %0 : tensor<16x2xf32> {sdy.sharding<@mesh, \[{"x", "y", "z"}, {}\]>
    %1 = sdy.all_gather  \[{"y", "z"}, {}\] %arg0 out_sharding=<@mesh, \[{"x"}, {}\]> : tensor<16x2xf32>
    ```

    In the example above, the tensor `%0 : tensor<16x2xf32>` is sharded as
    `\[{"x", "y", "z"}, {}\]`. Then, there's a `reshard` op resharding it as
    `\[{"x"}, {}\]`. On the first axes, since the suffix `{"y", "z"}` is removed
    after the reshard, we infer that we have all-gathered `{"y", "z"}`. The
    second dimension is not changed.

  }];
  let dependentDialects = ["mlir::sdy::SdyDialect"];
  let options = [
      // TODO(enver): Drop keepRedundantReshard option once shardy partitioner
      // migration is complete.
      Option<"keepRedundantReshards", "keep-redundant-reshards",
            "bool", /*default=*/"false",
            "Whether it keeps redundant reshards or removes.">
    ];
}

def OptimizeCollectivesPass : Pass<"sdy-optimize-collectives", "func::FuncOp"> {
  let summary = "Optimizes collective communication operations.";
  let description = [{
    Eliminates redundant collective-permute operations preceding all-to-all
    chains by decomposing split dimensions and fusing into a combined all-to-all.
  }];
  let dependentDialects = [
    "mlir::sdy::SdyDialect",
    "mlir::stablehlo::StablehloDialect",
  ];
}

def RemoveAllGatherReduceScatterForCMV1Pass : Pass<"sdy-remove-all-gather-reduce-scatter-for-cmv1", "func::FuncOp"> {
  let summary = "Removes sdy.all_gather and sdy.reduce_scatter for CMV1.";
  let dependentDialects = ["mlir::sdy::SdyDialect"];
  let description = [{
    Removes all-gather in the pattern all-gather + dot. Removes reduce-scatter
    in the pattern dot + reduce-scatter. This pass is for compatibility with
    collective matmul V1 (CMV1). It is a temporary solution for b/432019089.
  }];
}

def RemoveShardingGroupsPass : Pass<"sdy-remove-sharding-groups", "ModuleOp"> {
  let summary = "Removes ShardingGroupOps after propagation.";
  let dependentDialects = ["mlir::sdy::SdyDialect"];
}

def CloseShardingsPass : Pass<"sdy-close-shardings", "ModuleOp"> {
  let summary = "Closes tensor shardings and drops replicated axes.";
  let dependentDialects = ["mlir::sdy::SdyDialect"];
}

def DropShardingRulesPass : Pass<"sdy-drop-sharding-rules", "func::FuncOp"> {
  let summary = "Drops `OpShardingRuleAttr` from all registered ops.";
  let dependentDialects = ["mlir::sdy::SdyDialect"];
}

def DropShardingAndMeshPass : Pass<"sdy-drop-sharding-and-mesh", "ModuleOp"> {
  let summary = "Removes the mesh op and sharding notation from the program.";
  let dependentDialects = ["mlir::sdy::SdyDialect"];
}

def ConstantOrScalarMergerPass : Pass<"sdy-constant-or-scalar-merger", "func::FuncOp"> {
  let summary = "Merge identical constants and scalar expansions with matching shardings.";
  let description = [{
    Performs a lightweight CSE on constants with identical shardings.

    The import pipeline splits and duplicates the constants and scalar
    expansions such that sharding is not propagated between different uses of a
    constant sub-computation. If the constants have same shardings after
    propagation, this pass merges them to save compilation time. See
    -sdy-constant-or-scalar-splitter for more info.
  }];
  let dependentDialects = ["mlir::sdy::SdyDialect"];
}

def RemovePropagationDebugInfoPass : Pass<"sdy-remove-propagation-debug-info", "ModuleOp"> {
  let summary = "Removes propagation debug info (propagation edges and origin shardings) during export.";
  let dependentDialects = ["mlir::sdy::SdyDialect"];
}

def ConvertGlobalToLocalPass : Pass<"sdy-convert-global-to-local", "ModuleOp"> {
  let summary = "Converts an SDY program from global shapes to local shapes.";
  let description = [{
    Converts an SDY program from global shapes to local shapes by partitioning
    logical dimensions based on sharding attributes.

    This pass leverages a type converter to map RankedTensorType from global
    logical shapes to device-local physical shapes.
  }];
  let dependentDialects = ["mlir::sdy::SdyDialect", "mlir::stablehlo::StablehloDialect"];
  let options = [
      Option<"perDimAllGather", "per-dim-all-gather",
            "bool", /*default=*/"false",
            "Keep per-dimension all-gather without combining them into a single all-gather.">,
      Option<"combineMultiDimensionReduceScatter", "combine-multi-dimension-reduce-scatter",
            "bool", /*default=*/"false",
            "Combine multi-dimension reduce-scatter into a single reduce-scatter.">,
      Option<"enableRGV3", "enable-rgv3", "bool", /*default=*/"true",
           "Use StableHLO ReplicaGroupV3 (mesh-axes based) for collectives.">,
      Option<"replicaCount", "replica-count", "int64_t", /*default=*/"1",
             "Number of replicas (data parallelism).">,
      Option<"partitionCount", "partition-count", "int64_t", /*default=*/"1",
             "Number of partitions (model parallelism).">
    ];
}

def ExportNamedComputationsPass : Pass<"sdy-export-named-computations", "ModuleOp"> {
  let summary = "Outline calls from `NamedComputationOp`.";
  let description = [{
    Creates a pass that converts a `NamedComputationOp` to a `CallOp` with a new
    private function called the `NamedComputationOp`'s `name`. The new `FuncOp`
    and `CallOp` have the same shardings as the original `NamedComputationOp`s
    operands/results.

    If there is a function with the same name as the `NamedComputationOp` in the
    module, the MLIR symbol table will change it to `{name}_#`.
  }];
  let dependentDialects = ["mlir::sdy::SdyDialect"];
}

def PropagateToFuncResultsPass : Pass<"sdy-propagate-to-func-results", "ModuleOp"> {
  let summary = "Propagate shardings from the func terminator to func results.";
  let description = [{
    Copies the shardings of func terminator values to the corresponding `func.func` results,
    except for the main func.
  }];
  let dependentDialects = ["mlir::sdy::SdyDialect"];
}

def UnflattenCallGraphPass : Pass<"sdy-unflatten-call-graph", "ModuleOp"> {
  let summary = "Unflattens the call graph.";
  let description = [{
    Unflattens the graph. It deduplicates functions with the same
    input/output shardings *and* the same origin as desribed by the
    'original_func_name' attribute attached to the functions.
  }];
  let dependentDialects = ["mlir::sdy::SdyDialect"];
  let options = [
    Option<"dedupFunctionsFully", "dedup-functions-fully",
        "bool", /*default=*/"false",
        "If true, regardless of the input and output shardings of functions, "
        "it keeps one callee function for each caller function. The default "
        "is false, meaning it will deduplicate only if the input and output "
        "shardings are the same.">,
  ];
}

def InsertFuncCallReshardsPass : Pass<"sdy-insert-func-call-reshards", "ModuleOp"> {
  let summary = "Inserts reshards for func and call sharding conflicts.";
  let description = [{
    Inserts reshards for func and call sharding conflicts on results.
  }];
  let dependentDialects = ["mlir::sdy::SdyDialect"];
}

def ShardyResolvePermutationFactorsPass : Pass<"sdy-resolve-permutation-factors", "ModuleOp"> {
  let summary = "Resolves sharding on dimensions mapped to kPermutation factors.";
  let description = [{
    Sharding dimensions with `kPermutation` factors may require cross-device
    communication (e.g., halo exchange for windows or collective permutes for
    reverses).

    If `enableHaloExchange` is true, the pass would use an available optimized
    communication logic to resolve the permutation factors. Otherwise, the pass
    would simply insert `sdy.reshard` ops to replicate those dimensions. The
    default of `enableHaloExchange` is true.
  }];
  let dependentDialects = ["mlir::sdy::SdyDialect", "mlir::stablehlo::StablehloDialect"];
  let options = [
      Option<"enableHaloExchange", "enable-halo-exchange",
            "bool", /*default=*/"true",
            "Implement halo exchange logic for windowed operations.">,
      Option<"replicaCount", "replica-count", "int64_t", /*default=*/"1",
             "Number of replicas (data parallelism).">,
      Option<"partitionCount", "partition-count", "int64_t", /*default=*/"1",
             "Number of partitions (model parallelism).">
    ];
}

def PerInstructionPartitioningPass : Pass<"sdy-per-instruction-partitioning", "ModuleOp"> {
  let summary = "Selectively extracts target instructions, runs the partitioner pipeline on them to generate device-local code, and wraps them in sdy.manual_computation.";
  let description = [{
    For debugging and bisection purposes, selectively partitions individual instructions using
    the standalone Shardy partitioner pipeline (resolve-permutation-factors,
    reshard-to-collectives, pad-for-divisibility, convert-global-to-local), and
    wraps the resulting device-local code inside sdy.manual_computation. This
    keeps the rest of the global program intact so XLA SPMD partitions only the
    unwrapped global instructions.
  }];
  let dependentDialects = ["mlir::sdy::SdyDialect", "mlir::stablehlo::StablehloDialect"];
  let options = [
      Option<"filter", "filter",
            "std::string", /*default=*/"\"\"",
            "Filter string for selective partitioning. Can be empty (all sharded ops), "
            "comma-separated op name substrings (e.g. 'dot, pad'), or key-values like "
            "'selectLow=0, selectHigh=10'.">,
      Option<"enableHaloExchange", "enable-halo-exchange",
            "bool", /*default=*/"true",
            "Implement halo exchange logic for windowed operations inside the sub-pipeline.">,
      Option<"replicaCount", "replica-count", "int64_t", /*default=*/"1",
             "Number of replicas (data parallelism).">,
      Option<"partitionCount", "partition-count", "int64_t", /*default=*/"1",
             "Number of partitions (model parallelism).">
    ];
}
