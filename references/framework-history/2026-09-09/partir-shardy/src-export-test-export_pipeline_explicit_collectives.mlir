// RUN: sdy_opt %s -split-input-file -sdy-export-pipeline='enable-insert-explicit-collectives=true remove-all-gather-reduce-scatter-for-cmv1=true' 2>&1 | FileCheck %s

sdy.mesh @mesh = <["x"=2, "y"=2, "z"=2]>

// CHECK-LABEL: func @reduce_scatter_fusion
func.func @reduce_scatter_fusion(%arg0: tensor<16x8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{}, {"x"}, {}]>}) -> (tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"x"}, {"y"}]>}) {
  // CHECK: %0 = stablehlo.reduce(%arg0 init: %cst) applies stablehlo.add across dimensions = [1] : (tensor<16x8x8xf32>, tensor<f32>) -> tensor<16x8xf32>
  // CHECK-NEXT: %1 = sdy.reduce_scatter [{"x"}, {}] %0 out_sharding=<mesh<["x"=2, "y"=2, "z"=2]>, [{"x"}, {}]> : tensor<16x8xf32>
  // CHECK-NEXT: %2 = sdy.all_slice [{}, {"y"}] %1 out_sharding=<mesh<["x"=2, "y"=2, "z"=2]>, [{"x"}, {"y"}]> : tensor<16x8xf32>
  // CHECK-NEXT: return %2 : tensor<16x8xf32>
  %0 = stablehlo.constant dense<0.000000e+00> : tensor<f32>
  %1 = stablehlo.reduce(%arg0 init: %0) applies stablehlo.add across dimensions = [1] : (tensor<16x8x8xf32>, tensor<f32>) -> tensor<16x8xf32>
  %2 = sdy.sharding_constraint %1 <@mesh, [{"x"}, {"y"}]> : tensor<16x8xf32>
  return %2 : tensor<16x8xf32>
}

// -----
sdy.mesh @mesh = <["x"=2, "y"=2, "z"=2]>

// CHECK-LABEL: func @all_slice_all_gather
func.func @all_slice_all_gather(%arg0 : tensor<16x2xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"y"}, {}]>}) -> (tensor<16x2xf32> {sdy.sharding = #sdy.sharding<@mesh, [{}, {"x"}]>}) {
  // CHECK: %0 = sdy.all_slice [{}, {"x"}] %arg0 out_sharding=<mesh<["x"=2, "y"=2, "z"=2]>, [{"y"}, {"x"}]> : tensor<16x2xf32>
  // CHECK-NEXT: %1 = sdy.all_gather [{"y"}, {}] %0 out_sharding=<mesh<["x"=2, "y"=2, "z"=2]>, [{}, {"x"}]> : tensor<16x2xf32>
  // CHECK-NEXT: return %1 : tensor<16x2xf32>
  %0 = sdy.sharding_constraint %arg0 <@mesh, [{}, {"x"}]> : tensor<16x2xf32>
  return %0 : tensor<16x2xf32>
}

// -----
sdy.mesh @mesh = <["x"=2, "y"=2, "z"=2]>

// CHECK-LABEL: func @reshard_of_reshard
func.func @reshard_of_reshard(%arg0 : tensor<16x2xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"y"}, {}]>}) -> (tensor<16x2xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"y"}, {"x"}]>}) {
  // CHECK: %0 = sdy.all_slice [{}, {"x"}] %arg0 out_sharding=<mesh<["x"=2, "y"=2, "z"=2]>, [{"y"}, {"x"}]> : tensor<16x2xf32>
  // CHECK-NEXT: return %0 : tensor<16x2xf32>
  %0 = sdy.sharding_constraint %arg0 <@mesh, [{}, {"x"}]> : tensor<16x2xf32>
  %1 = sdy.sharding_constraint %0 <@mesh, [{"y"}, {"x"}]> : tensor<16x2xf32>
  return %1 : tensor<16x2xf32>
}

// -----
sdy.mesh @mesh = <["x"=2, "y"=2, "z"=2]>

// CHECK-LABEL: func @all_to_all_fusion
func.func @all_to_all_fusion(%arg0 : tensor<64x16x8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"x"}, {"y"}, {}, {}]>}) -> (tensor<64x16x8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{}, {}, {"x"}, {"y"}]>}) {
  // CHECK-NEXT: %0 = sdy.all_to_all [{"x"}: 0->2, {"y"}: 1->3] %arg0 out_sharding=<mesh<["x"=2, "y"=2, "z"=2]>, [{}, {}, {"x"}, {"y"}]> : tensor<64x16x8x8xf32>
  // CHECK-NEXT: return %0 : tensor<64x16x8x8xf32>
  %0 = sdy.reshard %arg0 <@mesh, [{}, {"y"}, {"x"}, {}]> : tensor<64x16x8x8xf32>
  %1 = sdy.reshard %0 <@mesh, [{}, {}, {"x"}, {"y"}]> : tensor<64x16x8x8xf32>
  return %1 : tensor<64x16x8x8xf32>
}

// -----
sdy.mesh @mesh = <["x"=2, "y"=2, "z"=2]>

// CHECK-LABEL: func @dot_general_with_unreduced_result
func.func @dot_general_with_unreduced_result(
    %arg0: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"x"}, {"y"}]>},
    %arg1: tensor<8x16xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"y"}, {}]>})
    -> (tensor<8x16xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"x"}, {}]>}) {
  // CHECK-NEXT: %[[DOT_GENERAL:.*]] = stablehlo.dot_general %arg0, %arg1
  // CHECK-SAME:   {sdy.sharding = #sdy.sharding_per_value<[<mesh<["x"=2, "y"=2, "z"=2]>, [{"x"}, {}], unreduced={"y"}>]>}
  // CHECK-NEXT: %[[ALL_REDUCE:.*]] = sdy.all_reduce {"y"} %[[DOT_GENERAL]] out_sharding=<mesh<["x"=2, "y"=2, "z"=2]>, [{"x"}, {}]>
  // CHECK-NEXT: %[[ADD:.*]] = stablehlo.add %[[ALL_REDUCE]], %[[ALL_REDUCE]] {sdy.sharding = #sdy.sharding_per_value<[<mesh<["x"=2, "y"=2, "z"=2]>, [{"x"}, {}]>]>}
  // CHECK-NEXT: return %[[ADD]]
  %0 = stablehlo.dot_general %arg0, %arg1, contracting_dims = [1] x [0]
    {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"x"}, {}], unreduced={"y"}>]>} :
    (tensor<8x8xf32>, tensor<8x16xf32>) -> tensor<8x16xf32>
  %reshard = sdy.reshard %0 <@mesh, [{"x"}, {}]> : tensor<8x16xf32>
  %1 = stablehlo.add %reshard, %reshard {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"x"}, {}]>]>} : tensor<8x16xf32>
  return %1 : tensor<8x16xf32>
}

// -----
sdy.mesh @mesh = <["x"=2, "y"=2, "z"=2]>

// CHECK-LABEL: func @dot_general_with_unreduced_result_fully_delayed
func.func @dot_general_with_unreduced_result_fully_delayed(
    %arg0: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"x"}, {"y", "z"}]>},
    %arg1: tensor<8x16xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"y", "z"}, {}]>})
    -> (tensor<8x16xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"x"}, {}]>}) {
  // CHECK-NEXT: %[[DOT_GENERAL:.*]] = stablehlo.dot_general %arg0, %arg1
  // CHECK-SAME:   {sdy.sharding = #sdy.sharding_per_value<[<mesh<["x"=2, "y"=2, "z"=2]>, [{"x"}, {}], unreduced={"y", "z"}>]>}
  // CHECK-NEXT: %[[ADD:.*]] = stablehlo.add %[[DOT_GENERAL]], %[[DOT_GENERAL]] {sdy.sharding = #sdy.sharding_per_value<[<mesh<["x"=2, "y"=2, "z"=2]>, [{"x"}, {}], unreduced={"y", "z"}>]>}
  // CHECK-NEXT: %[[ALL_REDUCE:.*]] = sdy.all_reduce {"y", "z"} %1 out_sharding=<mesh<["x"=2, "y"=2, "z"=2]>, [{"x"}, {}]>
  // CHECK-NEXT: return %[[ALL_REDUCE]]
  %0 = stablehlo.dot_general %arg0, %arg1, contracting_dims = [1] x [0]
    {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"x"}, {}], unreduced={"y", "z"}>]>} :
    (tensor<8x8xf32>, tensor<8x16xf32>) -> tensor<8x16xf32>
  %1 = stablehlo.add %0, %0 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"x"}, {}], unreduced={"y", "z"}>]>} : tensor<8x16xf32>
  %reshard = sdy.reshard %1 <@mesh, [{"x"}, {}]> : tensor<8x16xf32>
  return %reshard : tensor<8x16xf32>
}

// -----
sdy.mesh @mesh = <["x"=2, "y"=2, "z"=2]>

// CHECK-LABEL: func @dot_general_with_unreduced_result_partially_delayed
func.func @dot_general_with_unreduced_result_partially_delayed(
    %arg0: tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"x"}, {"y", "z"}]>},
    %arg1: tensor<8x16xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"y", "z"}, {}]>})
    -> (tensor<8x16xf32> {sdy.sharding = #sdy.sharding<@mesh, [{"x"}, {}]>}) {
  // CHECK-NEXT: %[[DOT_GENERAL:.*]] = stablehlo.dot_general %arg0, %arg1
  // CHECK-SAME:   {sdy.sharding = #sdy.sharding_per_value<[<mesh<["x"=2, "y"=2, "z"=2]>, [{"x"}, {}], unreduced={"y", "z"}>]>}
  // CHECK-NEXT: %[[ALL_REDUCE_Y:.*]] = sdy.all_reduce {"y"} %0 out_sharding=<mesh<["x"=2, "y"=2, "z"=2]>, [{"x"}, {}], unreduced={"z"}>
  // CHECK-NEXT: %[[ADD:.*]] = stablehlo.add %[[ALL_REDUCE_Y]], %[[ALL_REDUCE_Y]] {sdy.sharding = #sdy.sharding_per_value<[<mesh<["x"=2, "y"=2, "z"=2]>, [{"x"}, {}], unreduced={"z"}>]>}
  // CHECK-NEXT: %[[ALL_REDUCE_Z:.*]] = sdy.all_reduce {"z"} %[[ADD]] out_sharding=<mesh<["x"=2, "y"=2, "z"=2]>, [{"x"}, {}]>
  // CHECK-NEXT: return %[[ALL_REDUCE_Z]]
  %0 = stablehlo.dot_general %arg0, %arg1, contracting_dims = [1] x [0]
    {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"x"}, {}], unreduced={"y", "z"}>]>} :
    (tensor<8x8xf32>, tensor<8x16xf32>) -> tensor<8x16xf32>
  %reshard = sdy.reshard %0 <@mesh, [{"x"}, {}], unreduced={"z"}> : tensor<8x16xf32>
  %1 = stablehlo.add %reshard, %reshard {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"x"}, {}], unreduced={"z"}>]>} : tensor<8x16xf32>
  %reshard_ret = sdy.reshard %1 <@mesh, [{"x"}, {}]> : tensor<8x16xf32>
  return %reshard_ret : tensor<8x16xf32>
}

// -----
sdy.mesh @mesh = <["a"=2, "b"=2, "c"=2]>

// test: call_with_shardings
// CHECK-LABEL: func @main
func.func @main(%arg0: tensor<8x2xi32>, %arg1: tensor<4x2xi32>) -> tensor<12x2xi32> {
  // CHECK-NEXT: %0 = sdy.all_slice [{"a"}, {}] %arg0 out_sharding=<mesh<["a"=2, "b"=2, "c"=2]>, [{"a"}, {}]>
  // CHECK-NEXT: %1:2 = call @foo(%0, %arg1) {sdy.sharding = #sdy.sharding_per_value<[<mesh<["a"=2, "b"=2, "c"=2]>, [{"a"}, {}]>, <mesh<["a"=2, "b"=2, "c"=2]>, [{}, {}]>]>}
  // CHECK-NEXT: %2 = sdy.all_to_all [{"a"}: 0->1] %1#0 out_sharding=<mesh<["a"=2, "b"=2, "c"=2]>, [{}, {"a"}]>
  // CHECK-NEXT: %3 = sdy.all_slice [{}, {"a"}] %1#1 out_sharding=<mesh<["a"=2, "b"=2, "c"=2]>, [{}, {"a"}]> : tensor<4x2xi32>
  // CHECK-NEXT: %4 = stablehlo.concatenate %2, %3, dim = 0 {sdy.sharding = #sdy.sharding_per_value<[<mesh<["a"=2, "b"=2, "c"=2]>, [{}, {"a"}]>]>}
  // CHECK-NEXT: %5 = sdy.all_gather [{}, {"a"}] %4 out_sharding=<mesh<["a"=2, "b"=2, "c"=2]>, [{}, {}]>
  // CHECK-NEXT: return %5
  %0:2 = call @foo(%arg0, %arg1) {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{"a"}, {}]>, <@mesh, [{}, {}]>]>} : (tensor<8x2xi32>, tensor<4x2xi32>) -> (tensor<8x2xi32>, tensor<4x2xi32>)
  %1 = stablehlo.concatenate %0#0, %0#1, dim=0 {sdy.sharding = #sdy.sharding_per_value<[<@mesh, [{}, {"a"}]>]>} : (tensor<8x2xi32>, tensor<4x2xi32>) -> tensor<12x2xi32>
  return %1 : tensor<12x2xi32>
}

func.func private @foo(%arg0: tensor<8x2xi32> {sdy.sharding = #sdy.sharding<@mesh, [{"a"}, {}]>}, %arg1: tensor<4x2xi32> {sdy.sharding = #sdy.sharding<@mesh, [{}, {}]>})
    -> (tensor<8x2xi32> {sdy.sharding = #sdy.sharding<@mesh, [{"a"}, {}]>}, tensor<4x2xi32> {sdy.sharding = #sdy.sharding<@mesh, [{}, {}]>})
    attributes {sdy.original_func_name = "foo"} {
  return %arg0, %arg1 : tensor<8x2xi32>, tensor<4x2xi32>
}

// TODO: Add more tests.

// -----
sdy.mesh @mesh_rs = <["x"=2, "y"=2, "z"=2]>

// CHECK-LABEL: func @reduce_unreduced_to_sharded_max
func.func @reduce_unreduced_to_sharded_max(
    %arg0: tensor<8x8x8xf32> {sdy.sharding = #sdy.sharding<@mesh_rs, [{"x"}, {}, {"y"}]>})
    -> (tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh_rs, [{"x"}, {"y"}]>}) {
  // CHECK-NEXT: %[[CST:.*]] = stablehlo.constant dense<0.000000e+00> : tensor<f32>
  // CHECK-NEXT: %[[REDUCE:.*]] = stablehlo.reduce(%arg0 init: %[[CST]]) applies stablehlo.maximum across dimensions = [2]
  // CHECK-SAME:   {sdy.sharding = #sdy.sharding_per_value<[<mesh<["x"=2, "y"=2, "z"=2]>, [{"x"}, {}], unreduced=max{"y"}>]>}
  // CHECK-NEXT: %[[REDUCE_SCATTER:.*]] = sdy.reduce_scatter max [{}, {"y"}] %[[REDUCE]] out_sharding=<mesh<["x"=2, "y"=2, "z"=2]>, [{"x"}, {"y"}]>
  // CHECK-NEXT: return %[[REDUCE_SCATTER]]
  %cst = stablehlo.constant dense<0.000000e+00> : tensor<f32>
  %0 = stablehlo.reduce(%arg0 init: %cst) applies stablehlo.maximum across dimensions = [2]
    {sdy.sharding = #sdy.sharding_per_value<[<@mesh_rs, [{"x"}, {}], unreduced=max{"y"}>]>} :
    (tensor<8x8x8xf32>, tensor<f32>) -> tensor<8x8xf32>
  %reshard = sdy.reshard %0 <@mesh_rs, [{"x"}, {"y"}]> : tensor<8x8xf32>
  return %reshard : tensor<8x8xf32>
}

// -----
sdy.mesh @mesh_rs = <["x"=2, "y"=2, "z"=2]>

// CHECK-LABEL: func @reduce_unreduced_to_sharded_min
func.func @reduce_unreduced_to_sharded_min(
    %arg0: tensor<8x8x8xf32> {sdy.sharding = #sdy.sharding<@mesh_rs, [{"x"}, {}, {"y"}]>})
    -> (tensor<8x8xf32> {sdy.sharding = #sdy.sharding<@mesh_rs, [{"x"}, {"y"}]>}) {
  // CHECK-NEXT: %[[CST:.*]] = stablehlo.constant dense<0.000000e+00> : tensor<f32>
  // CHECK-NEXT: %[[REDUCE:.*]] = stablehlo.reduce(%arg0 init: %[[CST]]) applies stablehlo.minimum across dimensions = [2]
  // CHECK-SAME:   {sdy.sharding = #sdy.sharding_per_value<[<mesh<["x"=2, "y"=2, "z"=2]>, [{"x"}, {}], unreduced=min{"y"}>]>}
  // CHECK-NEXT: %[[REDUCE_SCATTER:.*]] = sdy.reduce_scatter min [{}, {"y"}] %[[REDUCE]] out_sharding=<mesh<["x"=2, "y"=2, "z"=2]>, [{"x"}, {"y"}]>
  // CHECK-NEXT: return %[[REDUCE_SCATTER]]
  %cst = stablehlo.constant dense<0.000000e+00> : tensor<f32>
  %0 = stablehlo.reduce(%arg0 init: %cst) applies stablehlo.minimum across dimensions = [2]
    {sdy.sharding = #sdy.sharding_per_value<[<@mesh_rs, [{"x"}, {}], unreduced=min{"y"}>]>} :
    (tensor<8x8x8xf32>, tensor<f32>) -> tensor<8x8xf32>
  %reshard = sdy.reshard %0 <@mesh_rs, [{"x"}, {"y"}]> : tensor<8x8xf32>
  return %reshard : tensor<8x8xf32>
}
