// RUN: sdy_opt %s -split-input-file -sdy-user-priority-propagate 2>&1 | FileCheck %s

sdy.mesh @mesh = <["a"=2, "b"=2, "c"=2]>

// CHECK-LABEL: func @no_priorities(
// CHECK-SAME:      %arg0: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a"}, {"b"}]>},
// CHECK-SAME:      %arg1: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a", ?}, {"b", ?}]>},
// CHECK-SAME:      %arg2: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a", ?}, {"b", ?}]>})
// CHECK-SAME:  -> (tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a", ?}, {"b", ?}]>}) {
func.func @no_priorities(%arg0: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a"}, {"b"}]>},
                         %arg1: tensor<8x8xf32>, %arg2: tensor<8x8xf32>) -> tensor<8x8xf32> {
  // CHECK-NEXT: %[[ADD:.*]] = stablehlo.add %arg0, %arg1 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"a", ?}, {"b", ?}]>]>}
  // CHECK-NEXT: stablehlo.divide %[[ADD]], %arg2 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"a", ?}, {"b", ?}]>]>}
  %0 = stablehlo.add %arg0, %arg1 : tensor<8x8xf32>
  %1 = stablehlo.divide %0, %arg2 : tensor<8x8xf32>
  return %1 : tensor<8x8xf32>
}

// -----
sdy.mesh @mesh = <["a"=2, "b"=2, "c"=2]>

// CHECK-LABEL: func @skipped_priorities(
// CHECK-SAME:      %arg0: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a"}, {"b"}]>},
// CHECK-SAME:      %arg1: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a", ?}, {"c", ?}]>},
// CHECK-SAME:      %arg2: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a", ?}, {"c", ?}]>})
// CHECK-SAME:  -> (tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a", ?}, {"c", ?}]>}) {
func.func @skipped_priorities(%arg0: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a"}, {"b"}p4]>},
                              %arg1: tensor<8x8xf32>, %arg2: tensor<8x8xf32>) -> tensor<8x8xf32> {
  // CHECK-NEXT: %[[ADD:.*]] = stablehlo.add %arg0, %arg1 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"a", ?}, {"c", ?}]>]>}
  // CHECK-NEXT: stablehlo.divide %[[ADD]], %arg2 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"a", ?}, {"c", ?}]>]>}
  %0 = stablehlo.add %arg0, %arg1 : tensor<8x8xf32>
  %1 = stablehlo.divide %0, %arg2 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{?}, {"c", ?}p1]>]>} : tensor<8x8xf32>
  return %1 : tensor<8x8xf32>
}

// -----
sdy.mesh @mesh = <["a"=2, "b"=2, "c"=2]>

// CHECK-LABEL: func @arg_lower_priority_than_return_value(
// CHECK-SAME:      %arg0: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a", ?}, {"b"}]>},
// CHECK-SAME:      %arg1: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"c", ?}, {"b", ?}]>},
// CHECK-SAME:      %arg2: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"c", ?}, {"b", ?}]>},
// CHECK-SAME:      %arg3: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"c", ?}, {"b", ?}]>})
// CHECK-SAME:  -> (tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"c", ?}, {"b", ?}]>}) {
func.func @arg_lower_priority_than_return_value(
    %arg0: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a", ?}p1, {"b"}p1]>},
    %arg1: tensor<8x8xf32>, %arg2: tensor<8x8xf32>, %arg3: tensor<8x8xf32>) -> tensor<8x8xf32> {
  // CHECK-NEXT: %[[ADD_0:.*]] = stablehlo.add %arg0, %arg1 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"c", ?}, {"b", ?}]>]>}
  // CHECK-NEXT: %[[ADD_1:.*]] = stablehlo.add %[[ADD_0]], %arg2 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"c", ?}, {"b", ?}]>]>}
  // CHECK-NEXT: stablehlo.divide %[[ADD_1]], %arg3 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"c"}, {"b", ?}]>]>}
  %0 = stablehlo.add %arg0, %arg1 : tensor<8x8xf32>
  %1 = stablehlo.add %0, %arg2 : tensor<8x8xf32>
  %2 = stablehlo.divide %1, %arg3 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"c"}p0, {?}]>]>} : tensor<8x8xf32>
  return %2 : tensor<8x8xf32>
}

// -----
sdy.mesh @mesh = <["a"=2, "b"=2, "c"=2]>

// CHECK-LABEL: func @arg_lower_priority_than_return_value_with_replicated(
// CHECK-SAME:      %arg0: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a"}, {"b"}]>},
// CHECK-SAME:      %arg1: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"c", ?}, {"b", ?}]>},
// CHECK-SAME:      %arg2: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"c", ?}, {"b", ?}]>},
// CHECK-SAME:      %arg3: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"c", ?}, {?}]>})
// CHECK-SAME:  -> (tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"c", ?}, {?}]>}) {
func.func @arg_lower_priority_than_return_value_with_replicated(
      %arg0: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a"}p1, {"b"}p1]>},
      %arg1: tensor<8x8xf32>, %arg2: tensor<8x8xf32>, %arg3: tensor<8x8xf32>)
      -> tensor<8x8xf32> {
  // CHECK-NEXT: %[[ADD_0:.*]] = stablehlo.add %arg0, %arg1 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"c", ?}, {"b", ?}]>]>}
  // CHECK-NEXT: %[[ADD_1:.*]] = stablehlo.add %[[ADD_0]], %arg2 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"c", ?}, {"b", ?}]>]>}
  // CHECK-NEXT: stablehlo.divide %[[ADD_1]], %arg3 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"c"}, {?}], replicated={"b"}>]>}
  %0 = stablehlo.add %arg0, %arg1 : tensor<8x8xf32>
  %1 = stablehlo.add %0, %arg2 : tensor<8x8xf32>
  %2 = stablehlo.divide %1, %arg3 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"c"}p0, {?}], replicated={"b"}>]>} : tensor<8x8xf32>
  return %2 : tensor<8x8xf32>
}

// -----
sdy.mesh @mesh = <["a"=2, "b"=2, "c"=2]>

// CHECK-LABEL: func @arg_higher_priority_than_return_value(
// CHECK-SAME:      %arg0: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a", ?}, {"b", ?}]>},
// CHECK-SAME:      %arg1: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a"}, {"b"}]>},
// CHECK-SAME:      %arg2: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a", ?}, {"b", ?}]>},
// CHECK-SAME:      %arg3: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{?}, {"b", ?}]>})
// CHECK-SAME:  -> (tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"c", ?}, {"b", ?}]>}) {
func.func @arg_higher_priority_than_return_value(
      %arg0: tensor<8x8xf32>, %arg1: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a"}p0, {"b"}p0]>},
      %arg2: tensor<8x8xf32>, %arg3: tensor<8x8xf32>) -> tensor<8x8xf32> {
  // CHECK-NEXT: %[[ADD_0:.*]] = stablehlo.add %arg0, %arg1 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"a", ?}, {"b", ?}]>]>}
  // CHECK-NEXT: %[[ADD_1:.*]] = stablehlo.add %[[ADD_0]], %arg2 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"a", ?}, {"b", ?}]>]>}
  // CHECK-NEXT: stablehlo.divide %[[ADD_1]], %arg3 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"c", ?}, {"b", ?}]>]>}
  %0 = stablehlo.add %arg0, %arg1 : tensor<8x8xf32>
  %1 = stablehlo.add %0, %arg2 : tensor<8x8xf32>
  %2 = stablehlo.divide %1, %arg3 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"c", ?}p1, {?}]>]>} : tensor<8x8xf32>
  return %2 : tensor<8x8xf32>
}

// -----
sdy.mesh @mesh = <["a"=2, "b"=2, "c"=2]>

// CHECK-LABEL: func @result_lower_priority_than_arg(
// CHECK-SAME:      %arg0: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"c", ?}, {"b", ?}]>},
// CHECK-SAME:      %arg1: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"c"}, {"b", ?}]>},
// CHECK-SAME:      %arg2: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"c", ?}, {"b", ?}]>},
// CHECK-SAME:      %arg3: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"c", ?}, {"b", ?}]>})
// CHECK-SAME:  -> (tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a", ?}, {"b"}]>}) {
func.func @result_lower_priority_than_arg(
    %arg0: tensor<8x8xf32>,
    %arg1: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"c"}p0, {?}]>},
    %arg2: tensor<8x8xf32>, %arg3: tensor<8x8xf32>)
    -> (tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a", ?}p1, {"b"}p1]>}) {
  // CHECK-NEXT: %[[ADD_0:.*]] = stablehlo.add %arg0, %arg1 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"c", ?}, {"b", ?}]>]>}
  // CHECK-NEXT: %[[ADD_1:.*]] = stablehlo.add %[[ADD_0]], %arg2 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"c", ?}, {"b", ?}]>]>}
  // CHECK-NEXT: stablehlo.divide %[[ADD_1]], %arg3 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"c", ?}, {"b", ?}]>]>}
  %0 = stablehlo.add %arg0, %arg1 : tensor<8x8xf32>
  %1 = stablehlo.add %0, %arg2 : tensor<8x8xf32>
  %2 = stablehlo.divide %1, %arg3 : tensor<8x8xf32>
  return %2 : tensor<8x8xf32>
}

// -----
sdy.mesh @mesh = <["a"=2, "b"=2, "c"=2]>

// CHECK-LABEL: func @result_higher_priority_than_arg(
// CHECK-SAME:      %arg0: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"c", ?}, {"b", ?}]>},
// CHECK-SAME:      %arg1: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a", ?}, {"b", ?}]>},
// CHECK-SAME:      %arg2: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a", ?}, {"b", ?}]>},
// CHECK-SAME:      %arg3: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a", ?}, {"b", ?}]>})
// CHECK-SAME:  -> (tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a"}, {"b"}]>}) {
func.func @result_higher_priority_than_arg(
      %arg0: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"c", ?}p1, {?}]>},
      %arg1: tensor<8x8xf32>, %arg2: tensor<8x8xf32>, %arg3: tensor<8x8xf32>)
      -> (tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a"}p0, {"b"}p0]>}) {
  // CHECK-NEXT: %[[ADD_0:.*]] = stablehlo.add %arg0, %arg1 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"a", ?}, {"b", ?}]>]>}
  // CHECK-NEXT: %[[ADD_1:.*]] = stablehlo.add %[[ADD_0]], %arg2 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"a", ?}, {"b", ?}]>]>}
  // CHECK-NEXT: stablehlo.divide %[[ADD_1]], %arg3 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"a", ?}, {"b", ?}]>]>}
  %0 = stablehlo.add %arg0, %arg1 : tensor<8x8xf32>
  %1 = stablehlo.add %0, %arg2 : tensor<8x8xf32>
  %2 = stablehlo.divide %1, %arg3 : tensor<8x8xf32>
  return %2 : tensor<8x8xf32>
}

// -----
sdy.mesh @mesh = <["a"=2, "b"=2, "c"=2]>

// CHECK-LABEL: func @dim_with_lower_priority_gets_further_sharded_by_higher(
// CHECK-SAME:      %arg0: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"b", "a", ?}, {}]>},
// CHECK-SAME:      %arg1: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"c", ?}, {?}]>},
// CHECK-SAME:      %arg2: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"b", "a", ?}, {?}]>},
// CHECK-SAME:      %arg3: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"c", ?}, {?}]>})
func.func @dim_with_lower_priority_gets_further_sharded_by_higher(
    %arg0: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"b", ?}p1, {}]>},
    %arg1: tensor<8x8xf32>, %arg2: tensor<8x8xf32>, %arg3: tensor<8x8xf32>)
    -> (tensor<8x8xf32>, tensor<8x8xf32>) {
  // CHECK-NEXT: %[[ADD_0:.*]] = stablehlo.add %arg0, %arg1 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"c", ?}, {?}]>]>}
  // CHECK-NEXT: %[[ADD_1:.*]] = stablehlo.add %arg0, %arg2 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"b", "a", ?}, {}]>]>}
  // CHECK-NEXT: stablehlo.divide %[[ADD_0]], %arg3 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"c", ?}, {}]>]>}
  %0 = stablehlo.add %arg0, %arg1 : tensor<8x8xf32>
  %1 = stablehlo.add %arg0, %arg2 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"b", "a", ?}p0, {}]>]>} : tensor<8x8xf32>
  %2 = stablehlo.divide %0, %arg3 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"c", ?}p0, {}]>]>} : tensor<8x8xf32>
  return %1, %2 : tensor<8x8xf32>, tensor<8x8xf32>
}

// -----
sdy.mesh @mesh = <["a"=2, "b"=2, "c"=2]>

// CHECK-LABEL: func @different_priorities_with_closed_empty_dim(
// CHECK-SAME:      %arg0: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a"}, {"b"}]>},
// CHECK-SAME:      %arg1: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a", ?}, {"b", ?}]>},
// CHECK-SAME:      %arg2: tensor<8x8xf32>,
// CHECK-SAME:      %arg3: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"c", ?}, {?}]>})
// CHECK-SAME:  -> (tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"c", ?}, {?}]>}) {
func.func @different_priorities_with_closed_empty_dim(
    %arg0: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a"}p0, {"b"}p0]>},
    %arg1: tensor<8x8xf32>, %arg2: tensor<8x8xf32>, %arg3: tensor<8x8xf32>) -> tensor<8x8xf32> {
  // CHECK-NEXT: %[[ADD_0:.*]] = stablehlo.add %arg0, %arg1 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"a", ?}, {"b", ?}]>]>}
  // CHECK-NEXT: %[[ADD_1:.*]] = stablehlo.add %[[ADD_0]], %arg2 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"c"}, {}]>]>}
  // CHECK-NEXT: stablehlo.divide %[[ADD_1]], %arg3 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"c", ?}, {?}]>]>}
  %0 = stablehlo.add %arg0, %arg1 : tensor<8x8xf32>
  %1 = stablehlo.add %0, %arg2 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"c"}p1, {}]>]>} : tensor<8x8xf32>
  %2 = stablehlo.divide %1, %arg3 : tensor<8x8xf32>
  return %2 : tensor<8x8xf32>
}

// -----
sdy.mesh @mesh = <["a"=2, "b"=2, "c"=2]>

// CHECK-LABEL: func @open_empty_dim_with_priority(
// CHECK-SAME:      %arg0: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a"}, {"b"}]>},
// CHECK-SAME:      %arg1: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a", ?}, {"b", ?}]>},
// CHECK-SAME:      %arg2: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a", ?}, {"c", ?}]>},
// CHECK-SAME:      %arg3: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a", ?}, {"c"}]>})
// CHECK-SAME:  -> (tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a", ?}, {"c", ?}]>}) {
func.func @open_empty_dim_with_priority(
    %arg0: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a"}p0, {"b"}p0]>},
    %arg1: tensor<8x8xf32>,
    %arg2: tensor<8x8xf32>,
    %arg3: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{?}, {"c"}p0]>}) -> tensor<8x8xf32> {
  // CHECK-NEXT: %[[ADD_0:.*]] = stablehlo.add %arg0, %arg1 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"a", ?}, {"b", ?}]>]>}
  // CHECK-NEXT: %[[ADD_1:.*]] = stablehlo.add %[[ADD_0]], %arg2 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"a", ?}, {"c", ?}]>]>}
  // CHECK-NEXT: stablehlo.divide %[[ADD_1]], %arg3 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"a", ?}, {"c", ?}]>]>}
  %0 = stablehlo.add %arg0, %arg1 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{?}, {?}p1]>]>} : tensor<8x8xf32>
  %1 = stablehlo.add %0, %arg2 : tensor<8x8xf32>
  %2 = stablehlo.divide %1, %arg3 : tensor<8x8xf32>
  return %2 : tensor<8x8xf32>
}

// -----
sdy.mesh @mesh = <["a"=2, "b"=2, "c"=2]>

// This test case simulates the benefit of using priorities for applying Batch Parallelism + ZeRO
// CHECK-LABEL: func @different_priorities_from_args(
// CHECK-SAME:      %arg0: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a"}, {?}]>},
// CHECK-SAME:      %arg1: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a", ?}, {?}]>},
// CHECK-SAME:      %arg2: tensor<8x16xf32> {sdy.sharding = #sdy.sharding<@mesh, [{?}, {"a"}]>})
// CHECK-SAME:  -> (tensor<8x16xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a", ?}, {?}]>}) {
func.func @different_priorities_from_args(
    %arg0: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a"}p0, {?}]>},
    %arg1: tensor<8x8xf32>, %arg2: tensor<8x16xf32> {sdy.sharding = #sdy.sharding<@mesh, [{?}, {"a"}p1]>}) -> tensor<8x16xf32> {
  // CHECK-NEXT: %[[ADD:.*]] = stablehlo.add %arg0, %arg1 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"a", ?}, {?}]>]>}
  // CHECK-NEXT: stablehlo.dot_general %[[ADD]], %arg2, contracting_dims = [1] x [0]
  // CHECK-SAME:   {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"a", ?}, {?}]>]>}
  %0 = stablehlo.add %arg0, %arg1 : tensor<8x8xf32>
  %1 = stablehlo.dot_general %0, %arg2, contracting_dims = [1] x [0] : (tensor<8x8xf32>, tensor<8x16xf32>) -> tensor<8x16xf32>
  return %1 : tensor<8x16xf32>
}

// -----
sdy.mesh @mesh = <["a"=2, "b"=2, "c"=2]>

// CHECK-LABEL: func @different_priorities_from_ops(
// CHECK-SAME:      %arg0: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{?}, {"a", ?}]>},
// CHECK-SAME:      %arg1: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a", ?}, {?}]>},
// CHECK-SAME:      %arg2: tensor<8x16xf32>)
// CHECK-SAME:  -> (tensor<8x16xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a", ?}, {?}]>}) {
func.func @different_priorities_from_ops(%arg0: tensor<8x8xf32>, %arg1: tensor<8x8xf32>,
                                         %arg2: tensor<8x16xf32>) -> tensor<8x16xf32> {
  // CHECK-NEXT: %[[ADD_0:.*]] = stablehlo.add %arg0, %arg0 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{?}, {"a"}]>]>}
  // CHECK-NEXT: %[[ADD_1:.*]] = stablehlo.add %[[ADD_0]], %arg1 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"a", ?}, {?}]>]>}
  // CHECK-NEXT: stablehlo.dot_general %[[ADD_1]], %arg2, contracting_dims = [1] x [0]
  // CHECK-SAME:   {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"a"}, {?}]>]>}
  %0 = stablehlo.add %arg0, %arg0 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{?}, {"a"}p1]>]>} : tensor<8x8xf32>
  %1 = stablehlo.add %0, %arg1 : tensor<8x8xf32>
  %2 = stablehlo.dot_general %1, %arg2, contracting_dims = [1] x [0] {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"a"}p0, {?}]>]>} : (tensor<8x8xf32>, tensor<8x16xf32>) -> tensor<8x16xf32>
  return %2 : tensor<8x16xf32>
}

// -----
sdy.mesh @mesh = <["a"=2, "b"=2, "c"=2]>

// CHECK-LABEL: func @different_sharding_constraint_priorities(
// CHECK-SAME:      %arg0: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a", ?}, {?}]>},
// CHECK-SAME:      %arg1: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{?}, {"a", ?}]>})
// CHECK-SAME:  -> (tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a", ?}, {?}]>}) {
func.func @different_sharding_constraint_priorities(%arg0: tensor<8x8xf32>, %arg1: tensor<8x8xf32>) -> tensor<8x8xf32> {
  // CHECK-NEXT: %[[SHARDING_CONSTRAINT0:.*]] = sdy.sharding_constraint %arg0 <@mesh, [{"a"}, {?}]>
  // CHECK-NEXT: %[[SHARDING_CONSTRAINT1:.*]] = sdy.sharding_constraint %arg1 <@mesh, [{?}, {"a"}]>
  // CHECK-NEXT: %[[ADD:.*]] = stablehlo.add %[[SHARDING_CONSTRAINT1]], %[[SHARDING_CONSTRAINT1]] {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"a", ?}, {?}]>]>}
  // CHECK-NEXT: stablehlo.add %[[SHARDING_CONSTRAINT0]], %[[ADD]] {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"a", ?}, {?}]>]>}
  %0 = sdy.sharding_constraint %arg0 <@mesh, [{"a"}p0, {?}]> : tensor<8x8xf32>
  %1 = sdy.sharding_constraint %arg1 <@mesh, [{?}, {"a"}p1]> : tensor<8x8xf32>
  %2 = stablehlo.add %1, %1 : tensor<8x8xf32>
  %3 = stablehlo.add %0, %2 : tensor<8x8xf32>
  return %3 : tensor<8x8xf32>
}

// -----
sdy.mesh @mesh = <["a"=2, "b"=2, "c"=2]>

// CHECK-LABEL: func @propagate_to_multi_result_op_with_priorities
func.func @propagate_to_multi_result_op_with_priorities(
    %arg0: tensor<4x64x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{}, {}, {"a"}p0]>},
    %arg1: tensor<4x64x8xf32>,
    %arg2: tensor<4x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{}, {"b"}p1]>})
    -> (tensor<4x8xf32>, tensor<4x8xf32>) {
  // CHECK-NEXT: %[[CONST:.*]] = stablehlo.constant dense<0.000000e+00>
  // CHECK-NEXT: %[[REDUCE:.*]]:2 = stablehlo.reduce(%arg0 init: %[[CONST]]), (%arg1 init: %[[CONST]]) across dimensions = [1]
  // CHECK-SAME:   {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{?}, {"a", ?}]>, <@mesh, [{?}, {"a", ?}]>]>}
  // CHECK:      stablehlo.add %[[REDUCE]]#1, %arg2 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{?}, {"a", ?}]>]>} :
  %0 = stablehlo.constant dense<0.000000e+00> : tensor<f32>
  %1:2 = stablehlo.reduce(%arg0 init: %0), (%arg1 init: %0) across dimensions = [1] :
    (tensor<4x64x8xf32>, tensor<4x64x8xf32>, tensor<f32>, tensor<f32>) -> (tensor<4x8xf32>, tensor<4x8xf32>)
    reducer(%arg3: tensor<f32>, %arg5: tensor<f32>) (%arg4: tensor<f32>, %arg6: tensor<f32>)  {
      %2 = stablehlo.add %arg3, %arg5 : tensor<f32>
      %3 = stablehlo.add %arg4, %arg6 : tensor<f32>
      stablehlo.return %2, %3 : tensor<f32>, tensor<f32>
    }
  %2 = stablehlo.add %1#1, %arg2 : tensor<4x8xf32>
  return %1#0, %2 : tensor<4x8xf32>, tensor<4x8xf32>
}

// -----
sdy.mesh @mesh = <["a"=2, "b"=2, "c"=2]>

// CHECK-LABEL: func @propagate_from_multi_result_op_with_priorities(
// CHECK-SAME:      %arg0: tensor<4x64x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{?}, {?}, {"b", ?}]>},
// CHECK-SAME:      %arg1: tensor<4x64x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{?}, {?}, {"b", ?}]>})
func.func @propagate_from_multi_result_op_with_priorities(
    %arg0: tensor<4x64x8xf32>, %arg1: tensor<4x64x8xf32>) -> tensor<4x8xf32> {
  // CHECK-NEXT: %[[CONST:.*]] = stablehlo.constant dense<0.000000e+00>
  // CHECK-NEXT: %[[REDUCE:.*]]:2 = stablehlo.reduce(%arg0 init: %[[CONST]]), (%arg1 init: %[[CONST]]) across dimensions = [1]
  // CHECK-SAME:   {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{?}, {"a"}]>, <@mesh, [{?}, {"b"}]>]>}
  // CHECK:      %[[ADD_0:.*]] = stablehlo.add %[[REDUCE]]#0, %[[REDUCE]]#0 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{?}, {"b", ?}]>]>}
  // CHECK-NEXT: %[[ADD_1:.*]] = stablehlo.add %[[REDUCE]]#1, %[[REDUCE]]#1 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{?}, {"b", ?}]>]>}
  // CHECK-NEXT: stablehlo.add %[[ADD_0]], %[[ADD_1]] {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{?}, {"b", ?}]>]>}
  %0 = stablehlo.constant dense<0.000000e+00> : tensor<f32>
  %1:2 = stablehlo.reduce(%arg0 init: %0), (%arg1 init: %0) across dimensions = [1]
    {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{?}, {"a"}p1]>, <@mesh, [{?}, {"b"}p0]>]>} :
    (tensor<4x64x8xf32>, tensor<4x64x8xf32>, tensor<f32>, tensor<f32>) -> (tensor<4x8xf32>, tensor<4x8xf32>)
    reducer(%arg2: tensor<f32>, %arg4: tensor<f32>) (%arg3: tensor<f32>, %arg5: tensor<f32>)  {
      %2 = stablehlo.add %arg2, %arg4 : tensor<f32>
      %3 = stablehlo.add %arg3, %arg5 : tensor<f32>
      stablehlo.return %2, %3 : tensor<f32>, tensor<f32>
    }
  %2 = stablehlo.add %1#0, %1#0 : tensor<4x8xf32>
  %3 = stablehlo.add %1#1, %1#1 : tensor<4x8xf32>
  %4 = stablehlo.add %2, %3 : tensor<4x8xf32>
  return %4 : tensor<4x8xf32>
}

// -----
sdy.mesh @mesh = <["a"=2, "b"=2, "c"=2]>

// CHECK-LABEL: func @manual_computation_shardings_with_priority(
// CHECK-SAME:      %arg0: tensor<32x32xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"c"}, {?}]>},
// CHECK-SAME:      %arg1: tensor<32x32xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a", ?}, {"b", ?}]>})
// CHECK-SAME:  -> (tensor<32x32xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a", ?}, {"b", ?}]>}) {
func.func @manual_computation_shardings_with_priority(
    %arg0: tensor<32x32xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"c"}p2, {?}]>},
    %arg1: tensor<32x32xf32> ) -> tensor<32x32xf32> {
  // CHECK-NEXT: %[[ADD_0:.*]] = stablehlo.add %arg0, %arg0 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"a", "b", ?}, {?}]>]>}
  // CHECK-NEXT: %[[MC:.*]] = sdy.manual_computation(%[[ADD_0]], %arg1)
  // CHECK-SAME:   in_shardings=[<@mesh, [{"a", "b"}p1, {?}]>, <@mesh, [{"a", ?}p1, {?}]>]
  // CHECK-SAME:   out_shardings=[<@mesh, [{"a", ?}, {"b", ?}p0]>]
  // CHECK-SAME:   manual_axes={"a"} (%arg2: tensor<16x32xf32>, %arg3: tensor<16x32xf32>) {
  // CHECK-NEXT:   %[[EDGE_1:.*]] = sdy.data_flow_edge %arg2 sharding=<@mesh, [{"b"}, {?}]> : tensor<16x32xf32>
  // CHECK-NEXT:   %[[EDGE_2:.*]] = sdy.data_flow_edge %arg3 sharding=<@mesh, [{?}, {"b", ?}]> : tensor<16x32xf32>
  // CHECK-NEXT:   %[[ADD_1:.*]] = stablehlo.add %[[EDGE_1]], %[[EDGE_2]] {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{?}, {"b", ?}]>]>}
  // CHECK-NEXT:   sdy.return %[[ADD_1]]
  // CHECK-NEXT: }
  // CHECK-NEXT: %[[EDGE_3:.*]] = sdy.data_flow_edge %[[MC]] sharding=<@mesh, [{"a", ?}, {"b", ?}]> : tensor<32x32xf32>
  // CHECK-NEXT: return %[[EDGE_3]] : tensor<32x32xf32>
  %0 = stablehlo.add %arg0, %arg0 : tensor<32x32xf32>
  %1 = sdy.manual_computation(%0, %arg1)
      in_shardings=[<@mesh, [{"a", "b"}p1, {?}]>, <@mesh, [{"a", ?}p1, {?}]>]
      out_shardings=[<@mesh, [{"a", ?}, {"b", ?}p0]>] manual_axes={"a"}
      (%arg2: tensor<16x32xf32>, %arg3: tensor<16x32xf32>) {
    %3 = sdy.data_flow_edge %arg2 sharding=<@mesh, [{"b"}p1, {?}]> : tensor<16x32xf32>
    %4 = sdy.data_flow_edge %arg3 sharding=<@mesh, [{?}p1, {?}]> : tensor<16x32xf32>
    %5 = stablehlo.add %3, %4 : tensor<16x32xf32>
    sdy.return %5 : tensor<16x32xf32>
  } : (tensor<32x32xf32>, tensor<32x32xf32>) -> tensor<32x32xf32>
  %2 = sdy.data_flow_edge %1 sharding=<@mesh, [{"a", ?}, {"b", ?}p0]> : tensor<32x32xf32>
  func.return %2 : tensor<32x32xf32>
}

// -----
sdy.mesh @mesh = <["a"=2, "b"=2, "c"=2]>

// CHECK-LABEL: func @manual_computation_sharding_with_low_priority(
// CHECK-SAME:      %arg0: tensor<32x32xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"c"}, {}]>},
// CHECK-SAME:      %arg1: tensor<32x32xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a", "b", ?}, {?}]>})
// CHECK-SAME:  -> (tensor<32x32xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"c"}, {}]>}) {
func.func @manual_computation_sharding_with_low_priority(
    %arg0: tensor<32x32xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"c"}p1, {}]>},
    %arg1: tensor<32x32xf32>) -> (tensor<32x32xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"c"}p1, {}]>}) {
  // TODO(b/380881922): The `%0 = stablehlo.add` should have the sharding
  // `[{"c", ?}, {?}]>]`, but instead it has `[{"a", "b", ?}, {?}]>]`.
  %0 = stablehlo.add %arg0, %arg0 : tensor<32x32xf32>
  %1 = sdy.manual_computation(%0, %arg1)
      in_shardings=[<@mesh, [{"a", "b"}p2, {}]>, <@mesh, [{"a", "b"}p0, {}]>]
      out_shardings=[<@mesh, [{"a", "b"}p2, {}]>] manual_axes={"a"}
      (%arg2: tensor<16x32xf32>, %arg3: tensor<16x32xf32>) {
    %4 = sdy.data_flow_edge %arg2 sharding=<@mesh, [{"b"}p2, {}]> : tensor<16x32xf32>
    %5 = sdy.data_flow_edge %arg3 sharding=<@mesh, [{"b"}p0, {}]> : tensor<16x32xf32>
    %6 = stablehlo.add %4, %5 : tensor<16x32xf32>
    sdy.return %6 : tensor<16x32xf32>
  } : (tensor<32x32xf32>, tensor<32x32xf32>) -> tensor<32x32xf32>
  %2 = sdy.data_flow_edge %1 sharding=<@mesh, [{"a", "b"}p2, {}]> : tensor<32x32xf32>
  %3 = stablehlo.add %2, %2 : tensor<32x32xf32>
  func.return %3 : tensor<32x32xf32>
}

// -----
sdy.mesh @mesh = <["a"=2, "b"=2, "c"=2]>

// Tests user based priority propagation with op based priority propagation.
// - For %arg0/%arg1 we make use of user based priorities. Since %arg0 is p1 but
//   %arg1 is p0, then the first `stablehlo.add` uses the sharding from %arg1
//   and thus is sharded on "a" on dim 1. If %arg0 were p0, then it actually
//   would have been on dim 0.
// - For %1/%2/%3 we make use of op based priorities. Since we propagate
//   element-wise first, the last 2 adds are sharded on "b" on dim 0. If op
//   based priorities was disabled, then the second last add would have actually
//   been partitioned on dim 1.
//
// CHECK-LABEL: func @user_based_and_op_based(
// CHECK-SAME:      %arg0: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a", ?}, {?}]>},
// CHECK-SAME:      %arg1: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a", ?}, {"b", ?}]>})
// CHECK-SAME:      -> (tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"b", ?}, {?}]>}) {
func.func @user_based_and_op_based(
    %arg0: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a", ?}p1, {?}]>},
    %arg1: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a", ?}p0, {"b", ?}p0]>})
    -> (tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"b", ?}p0, {?}]>}) {
  // CHECK:      %[[ADD_0:.*]] = stablehlo.add %arg0, %arg0 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"b", ?}, {"a", ?}]>]>} : tensor<8x8xf32>
  // CHECK-NEXT: %[[DOT:.*]] = stablehlo.dot_general %[[ADD_0]], %arg1, contracting_dims = [1] x [0] {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"b", ?}, {?}]>]>} : (tensor<8x8xf32>, tensor<8x8xf32>) -> tensor<8x8xf32>
  // CHECK-NEXT: %[[ADD_1:.*]] = stablehlo.add %[[DOT]], %[[DOT]] {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"b", ?}, {?}]>]>} : tensor<8x8xf32>
  // CHECK-NEXT: %[[ADD_2:.*]] = stablehlo.add %[[ADD_1]], %[[ADD_1]] {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"b", ?}, {?}]>]>} : tensor<8x8xf32>
  // CHECK-NEXT: return %[[ADD_2]] : tensor<8x8xf32>
  %0 = stablehlo.add %arg0, %arg0 : tensor<8x8xf32>
  %1 = stablehlo.dot_general %0, %arg1, contracting_dims = [1] x [0] : (tensor<8x8xf32>, tensor<8x8xf32>) -> tensor<8x8xf32>
  %2 = stablehlo.add %1, %1 : tensor<8x8xf32>
  %3 = stablehlo.add %2, %2 : tensor<8x8xf32>
  return %3 : tensor<8x8xf32>
}

// -----
sdy.mesh @mesh = <["a"=2, "b"=2, "c"=2]>
sdy.mesh @maximal_mesh = <[], device_ids=[0]>

// Nothing should be propagated, but this verifies the `transformShardings`
// sharding walker is able to handle a maximal sharding with no returned values.
// CHECK-LABEL: func @maximal_sharding_no_results
// CHECK-SAME:      (%arg0: tensor<8x8xf32>) -> tensor<8x8xf32> {
func.func @maximal_sharding_no_results(%arg0: tensor<8x8xf32>) -> tensor<8x8xf32> {
  // CHECK-NEXT: stablehlo.custom_call @xla_python_cpu_callback(%arg0) {has_side_effect = true, sdy.sharding = #sdy.sharding_per_value<[<@maximal_mesh, []>]>} : (tensor<8x8xf32>) -> ()
  // CHECK-NEXT: return %arg0 : tensor<8x8xf32>
  stablehlo.custom_call @xla_python_cpu_callback(%arg0) {has_side_effect = true, sdy.sharding = #sdy.sharding_per_value<[<@maximal_mesh, []>]>} : (tensor<8x8xf32>) -> ()
  return %arg0 : tensor<8x8xf32>
}

// -----
sdy.mesh @mesh = <["a"=2, "b"=2, "c"=2]>

// CHECK-LABEL: func @unreduced_custom_reduction_op(
// CHECK-SAME:      %arg0: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a", ?}, {?}]>},
// CHECK-SAME:      %arg1: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a", ?}, {"b", ?}]>})
// CHECK-SAME:  -> (tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{?}, {"b", ?}]>}) {
func.func @unreduced_custom_reduction_op(
    %arg0: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a", ?}p1, {?}]>},
    %arg1: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"a", ?}p0, {"b", ?}p0]>})
    -> tensor<8x8xf32> {
  // CHECK:      %[[ADD_0:.*]] = stablehlo.add %arg0, %arg0 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{?}, {"a", ?}]>]>} : tensor<8x8xf32>
  // CHECK-NEXT: %[[DOT:.*]] = stablehlo.dot_general %[[ADD_0]], %arg1, contracting_dims = [1] x [0] {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{?}, {"b", ?}], unreduced=max{"c"}>]>} : (tensor<8x8xf32>, tensor<8x8xf32>) -> tensor<8x8xf32>
  // CHECK-NEXT: return %[[DOT]] : tensor<8x8xf32>
  %0 = stablehlo.add %arg0, %arg0 : tensor<8x8xf32>
  %1 = stablehlo.dot_general %0, %arg1, contracting_dims = [1] x [0] {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{?}p0, {?}], unreduced=max{"c"}>]>} : (tensor<8x8xf32>, tensor<8x8xf32>) -> tensor<8x8xf32>
  return %1 : tensor<8x8xf32>
}
