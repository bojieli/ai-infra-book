// RUN: sdy_opt %s -sdy-reshard-to-collectives | FileCheck %s

sdy.mesh @mesh1d_6 = <["x"=6]>
sdy.mesh @mesh2d = <["x"=2, "y"=2]>
sdy.mesh @mesh2d_4x2 = <["x"=4, "y"=2]>
sdy.mesh @mesh2d_2x8 = <["x"=2, "y"=8]>
sdy.mesh @mesh2d_2x3 = <["x"=2, "y"=3]>
sdy.mesh @mesh2d_4x6 = <["x"=4, "y"=6]>
sdy.mesh @mesh2d_non_iota = <["x"=2, "y"=2], device_ids=[3, 2, 1, 0]>
sdy.mesh @mesh2d_non_iota_2 = <["x"=2, "y"=2], device_ids=[3, 1, 2, 0]>
sdy.mesh @mesh3d = <["x"=2, "y"=2, "z"=2]>
sdy.mesh @mesh3d_4x2x4 = <["x"=4, "y"=2, "z"=4]>
sdy.mesh @mesh3d_4x6x2 = <["x"=4, "y"=6, "z"=2]>
sdy.mesh @mesh3d_4x6x5 = <["x"=4, "y"=6, "z"=5]>
sdy.mesh @mesh4d = <["x"=2, "y"=2, "z"=2, "w"=2]>
sdy.mesh @mesh4d_z4 = <["x"=2, "y"=2, "z"=4, "w"=2]>
sdy.mesh @mesh4d_w4 = <["x"=2, "y"=2, "z"=2, "w"=4]>
sdy.mesh @mesh4d_w16 = <["x"=2, "y"=2, "z"=2, "w"=16]>
sdy.mesh @mesh6d = <["x"=2, "y"=2, "z"=2, "w"=2, "u"=2, "v"=2]>
sdy.mesh @empty_mesh = <[]>
sdy.mesh @empty_mesh_another = <[]>
sdy.mesh @single_dev_0 = <[], device_ids=[0]>


// CHECK-LABEL: func @redundant_reshard_fully_replicated
func.func @redundant_reshard_fully_replicated(%arg0 : tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh2d, [{}, {}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: return %arg0
  %0 = sdy.reshard %arg0 <@mesh2d, [{}, {}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @redundant_reshard_fully_replicated_different_meshes
func.func @redundant_reshard_fully_replicated_different_meshes(%arg0 : tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh2d_2x3, [{}, {}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: return %arg0
  %0 = sdy.reshard %arg0 <@mesh1d_6, [{}, {}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @redundant_reshard_fully_replicated_same_mesh_different_device_ids
func.func @redundant_reshard_fully_replicated_same_mesh_different_device_ids(%arg0 : tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh2d, [{}, {}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: return %arg0
  %0 = sdy.reshard %arg0 <@mesh2d_non_iota, [{}, {}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @redundant_reshard_fully_replicated_same_empty_meshes
func.func @redundant_reshard_fully_replicated_same_empty_meshes(%arg0 : tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@empty_mesh, [{}, {}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: return %arg0
  %0 = sdy.reshard %arg0 <@empty_mesh, [{}, {}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @redundant_reshard_fully_replicated_different_empty_meshes
func.func @redundant_reshard_fully_replicated_different_empty_meshes(%arg0 : tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@empty_mesh, [{}, {}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: return %arg0
  %0 = sdy.reshard %arg0 <@empty_mesh_another, [{}, {}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @redundant_reshard_fully_replicated_input_mesh_nonempty_output_mesh_empty
func.func @redundant_reshard_fully_replicated_input_mesh_nonempty_output_mesh_empty(%arg0 : tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh2d, [{}, {}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: return %arg0
  %0 = sdy.reshard %arg0 <@empty_mesh, [{}, {}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @redundant_reshard
func.func @redundant_reshard(%arg0 : tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh2d, [{"x"}, {"y"}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: return %arg0
  %0 = sdy.reshard %arg0 <@mesh2d, [{"x", ?}, {"y", ?}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @reshard_from_sharded_to_fully_replicated_same_meshes
func.func @reshard_from_sharded_to_fully_replicated_same_meshes(%arg0 : tensor<24x8xf32> {sdy.sharding = #sdy.sharding<@mesh1d_6, [{"x"}, {}]>}) -> tensor<24x8xf32> {
  // CHECK-NEXT: %[[ALL_GATHER:.*]] = sdy.all_gather [{"x"}, {}] %arg0 out_sharding=<@mesh1d_6, [{}, {}]>
  // CHECK-NEXT: return %[[ALL_GATHER]]
  %0 = sdy.reshard %arg0 <@mesh1d_6, [{}, {}]> : tensor<24x8xf32>
  return %0 : tensor<24x8xf32>
}

// CHECK-LABEL: func @reshard_from_sharded_to_fully_replicated_different_meshes
func.func @reshard_from_sharded_to_fully_replicated_different_meshes(%arg0 : tensor<24x8xf32> {sdy.sharding = #sdy.sharding<@mesh1d_6, [{"x"}, {}]>}) -> tensor<24x8xf32> {
  // CHECK-NEXT: %[[ALL_GATHER:.*]] = sdy.all_gather [{"x"}, {}] %arg0 out_sharding=<@mesh1d_6, [{}, {}]>
  // CHECK-NEXT: return %[[ALL_GATHER]]
  %0 = sdy.reshard %arg0 <@mesh2d_2x3, [{}, {}]> : tensor<24x8xf32>
  return %0 : tensor<24x8xf32>
}

// CHECK-LABEL: func @reshard_from_sharded_to_sharded_different_meshes
func.func @reshard_from_sharded_to_sharded_different_meshes(%arg0 : tensor<24x8xf32> {sdy.sharding = #sdy.sharding<@mesh1d_6, [{"x"}, {}]>}) -> (tensor<24x8xf32> {sdy.sharding = #sdy.sharding<@mesh2d_2x3, [{"x"}, {}]>}) {
  // CHECK-NEXT: %[[RESHARD:.*]] = sdy.reshard %arg0 <@mesh2d_2x3, [{"x"}, {}]>
  // CHECK-NEXT: return %[[RESHARD]]
  %0 = sdy.reshard %arg0 <@mesh2d_2x3, [{"x"}, {}]> : tensor<24x8xf32>
  return %0 : tensor<24x8xf32>
}

// CHECK-LABEL: func @all_gather_single_axis
func.func @all_gather_single_axis(%arg0 : tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh2d, [{"y"}, {"x"}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: sdy.all_gather [{}, {"x"}] %arg0 out_sharding=<@mesh2d, [{"y"}, {}]>
  %0 = sdy.reshard %arg0 <@mesh2d, [{"y"}, {}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @all_gather_multiple_axes
func.func @all_gather_multiple_axes(%arg0 : tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh3d, [{"x", "y", "z"}, {}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: sdy.all_gather [{"y", "z"}, {}] %arg0 out_sharding=<@mesh3d, [{"x"}, {}]>
  %0 = sdy.reshard %arg0 <@mesh3d, [{"x"}, {}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @all_gather_multiple_dims
func.func @all_gather_multiple_dims(%arg0 : tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh3d, [{"y", "z"}, {"x"}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: sdy.all_gather [{"z"}, {}] %arg0 out_sharding=<@mesh3d, [{"y"}, {"x"}]>
  %0 = sdy.reshard %arg0 <@mesh3d, [{"y"}, {"x"}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @all_gather_with_subaxis
func.func @all_gather_with_subaxis(%arg0 : tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh2d_2x8, [{"y"}, {"x"}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: sdy.all_gather [{"y":(4)2}, {}] %arg0 out_sharding=<@mesh2d_2x8, [{"y":(1)4}, {"x"}]>
 %0 = sdy.reshard %arg0 <@mesh2d_2x8, [{"y":(1)4}, {"x"}]> :  tensor<16x8xf32>
 return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @all_slice_multiple_axes
func.func @all_slice_multiple_axes(%arg0 : tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh3d, [{}, {}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: sdy.all_slice [{"x"}, {"y", "z"}] %arg0 out_sharding=<@mesh3d, [{"x"}, {"y", "z"}]>
  %0 = sdy.reshard %arg0 <@mesh3d, [{"x"}, {"y", "z"}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @all_slice_with_subaxis
func.func @all_slice_with_subaxis(%arg0 : tensor<16x8xf32>) -> tensor<16x8xf32> {
  // CHECK-NEXT: sdy.all_slice [{"x"}, {"y", "z"}] %arg0 out_sharding=<@mesh3d, [{"x"}, {"y", "z"}]>
  %0 = sdy.reshard %arg0 <@mesh3d, [{"x"}, {"y", "z"}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @all_slice_minor_axis
func.func @all_slice_minor_axis(%arg0 : tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh3d, [{"x"}, {"y"}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: sdy.all_slice [{}, {"z"}] %arg0 out_sharding=<@mesh3d, [{"x"}, {"y", "z"}]>
  %0 = sdy.reshard %arg0 <@mesh3d, [{"x"}, {"y", "z"}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @all_slice_missing_input_sharding
func.func @all_slice_missing_input_sharding(%arg0 : tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh3d, [{}, {}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: sdy.all_slice [{"x"}, {"y", "z"}] %arg0 out_sharding=<@mesh3d, [{"x"}, {"y", "z"}]>
  %0 = sdy.reshard %arg0 <@mesh3d, [{"x"}, {"y", "z"}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @all_to_all_single_axis
func.func @all_to_all_single_axis(%arg0 : tensor<16x8x8xf32> {sdy.sharding = #sdy.sharding<@mesh3d, [{"x"}, {"y"}, {}]>}) -> tensor<16x8x8xf32> {
  // CHECK-NEXT: sdy.all_to_all [{"x"}: 0->2] %arg0 out_sharding=<@mesh3d, [{}, {"y"}, {"x"}]>
  %0 = sdy.reshard %arg0 <@mesh3d, [{}, {"y"}, {"x"}]> : tensor<16x8x8xf32>
  return %0 : tensor<16x8x8xf32>
}

// CHECK-LABEL: func @all_to_all_multiple_axes
func.func @all_to_all_multiple_axes(%arg0 : tensor<16x8x8xf32> {sdy.sharding = #sdy.sharding<@mesh3d, [{"x"}, {}, {"y", "z"}]>}) -> tensor<16x8x8xf32> {
  // CHECK-NEXT: sdy.all_to_all [{"y", "z"}: 2->1] %arg0 out_sharding=<@mesh3d, [{"x"}, {"y", "z"}, {}]>
  %0 = sdy.reshard %arg0 <@mesh3d, [{"x"}, {"y", "z"}, {}]> : tensor<16x8x8xf32>
  return %0 : tensor<16x8x8xf32>
}

// CHECK-LABEL: func @all_to_all_move_partial_axes_from_src_dim_to_non_empty_tgt_dim
func.func @all_to_all_move_partial_axes_from_src_dim_to_non_empty_tgt_dim(%arg0 : tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh3d, [{"x", "z"}, {"y"}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: sdy.all_to_all [{"z"}: 0->1] %arg0 out_sharding=<@mesh3d, [{"x"}, {"y", "z"}]>
  %0 = sdy.reshard %arg0 <@mesh3d, [{"x"}, {"y", "z"}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @two_all_to_alls_different_tgt_dims
func.func @two_all_to_alls_different_tgt_dims(%arg0 : tensor<16x8x8xf32> {sdy.sharding = #sdy.sharding<@mesh3d_4x2x4, [{}, {"y", "x"}, {}]>}) -> tensor<16x8x8xf32> {
  // CHECK-NEXT: %[[ALL_TO_ALL_0:.*]] = sdy.all_to_all [{"x"}: 1->0] %arg0 out_sharding=<@mesh3d_4x2x4, [{"x"}, {"y"}, {}]>
  // CHECK-NEXT: %[[ALL_TO_ALL_1:.*]] = sdy.all_to_all [{"y"}: 1->2] %[[ALL_TO_ALL_0]] out_sharding=<@mesh3d_4x2x4, [{"x"}, {}, {"y"}]>
  // CHECK-NEXT: return %[[ALL_TO_ALL_1]]
  %0 = sdy.reshard %arg0 <@mesh3d_4x2x4, [{"x"}, {}, {"y"}]> : tensor<16x8x8xf32>
  return %0 : tensor<16x8x8xf32>
}

// CHECK-LABEL: func @two_all_to_alls_tgt_dim_not_empty
func.func @two_all_to_alls_tgt_dim_not_empty(%arg0 : tensor<16x8x8xf32> {sdy.sharding = #sdy.sharding<@mesh3d_4x2x4, [{"x"}, {"y", "z"}, {}]>}) -> tensor<16x8x8xf32> {
  // CHECK-NEXT: %[[ALL_TO_ALL_0:.*]] = sdy.all_to_all [{"z"}: 1->0] %arg0 out_sharding=<@mesh3d_4x2x4, [{"x", "z"}, {"y"}, {}]>
  // CHECK-NEXT: %[[ALL_TO_ALL_1:.*]] = sdy.all_to_all [{"y"}: 1->2] %[[ALL_TO_ALL_0]] out_sharding=<@mesh3d_4x2x4, [{"x", "z"}, {}, {"y"}]>
  // CHECK-NEXT: return %[[ALL_TO_ALL_1]]
  %0 = sdy.reshard %arg0 <@mesh3d_4x2x4, [{"x", "z"}, {}, {"y"}]> : tensor<16x8x8xf32>
  return %0 : tensor<16x8x8xf32>
}

// CHECK-LABEL: func @two_all_to_alls_same_tgt_dim_reverse_order
func.func @two_all_to_alls_same_tgt_dim_reverse_order(%arg0 : tensor<16x8x8xf32> {sdy.sharding = #sdy.sharding<@mesh3d, [{"y"}, {"x"}, {}]>}) -> tensor<16x8x8xf32> {
  // CHECK-NEXT: %[[ALL_TO_ALL_0:.*]] = sdy.all_to_all [{"x"}: 1->2] %arg0 out_sharding=<@mesh3d, [{"y"}, {}, {"x"}]>
  // CHECK-NEXT: %[[ALL_TO_ALL_1:.*]] = sdy.all_to_all [{"y"}: 0->2] %[[ALL_TO_ALL_0]] out_sharding=<@mesh3d, [{}, {}, {"x", "y"}]>
  // CHECK-NEXT: return %[[ALL_TO_ALL_1]]
  %0 = sdy.reshard %arg0 <@mesh3d, [{}, {}, {"x", "y"}]> : tensor<16x8x8xf32>
  return %0 : tensor<16x8x8xf32>
}

// CHECK-LABEL: func @two_all_to_alls_same_tgt_dim_non_contiguous
func.func @two_all_to_alls_same_tgt_dim_non_contiguous(%arg0 : tensor<16x8x8xf32> {sdy.sharding = #sdy.sharding<@mesh3d, [{"y"}, {"x", "z"}, {}]>}) -> tensor<16x8x8xf32> {
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %arg0 out_sharding=<@mesh3d, [{"x"}, {"y", "z"}, {}]>
  // CHECK-NEXT: %[[ALL_TO_ALL_0:.*]] = sdy.all_to_all [{"x"}: 0->2] %[[COLLECTIVE_PERMUTE]] out_sharding=<@mesh3d, [{}, {"y", "z"}, {"x"}]>
  // CHECK-NEXT: %[[ALL_TO_ALL_1:.*]] = sdy.all_to_all [{"y", "z"}: 1->2] %[[ALL_TO_ALL_0]] out_sharding=<@mesh3d, [{}, {}, {"x", "y", "z"}]>
  // CHECK-NEXT: return %[[ALL_TO_ALL_1]]
  %0 = sdy.reshard %arg0 <@mesh3d, [{}, {}, {"x", "y", "z"}]> : tensor<16x8x8xf32>
  return %0 : tensor<16x8x8xf32>
}

// CHECK-LABEL: func @slice_then_all_to_alls
func.func @slice_then_all_to_alls(%arg0 : tensor<16x8x8xf32> {sdy.sharding = #sdy.sharding<@mesh3d_4x2x4, [{}, {"y", "z"}, {}]>}) -> tensor<16x8x8xf32> {
  // CHECK-NEXT: %[[ALL_SLICE:.*]] = sdy.all_slice [{"x"}, {}, {}] %arg0 out_sharding=<@mesh3d_4x2x4, [{"x"}, {"y", "z"}, {}]>
  // CHECK-NEXT: %[[ALL_TO_ALL_0:.*]] = sdy.all_to_all [{"z"}: 1->0] %[[ALL_SLICE]] out_sharding=<@mesh3d_4x2x4, [{"x", "z"}, {"y"}, {}]>
  // CHECK-NEXT: %[[ALL_TO_ALL_1:.*]] = sdy.all_to_all [{"y"}: 1->2] %[[ALL_TO_ALL_0]] out_sharding=<@mesh3d_4x2x4, [{"x", "z"}, {}, {"y"}]>
  // CHECK-NEXT: return %[[ALL_TO_ALL_1]]
  %0 = sdy.reshard %arg0 <@mesh3d_4x2x4, [{"x", "z"}, {}, {"y"}]> : tensor<16x8x8xf32>
  return %0 : tensor<16x8x8xf32>
}

// CHECK-LABEL: func @all_to_all_subaxis_then_all_gather
func.func @all_to_all_subaxis_then_all_gather(%arg0 : tensor<16x8x8xf32> {sdy.sharding = #sdy.sharding<@mesh3d_4x2x4, [{"x"}, {"z", "y"}, {}]>}) -> tensor<16x8x8xf32> {
  // CHECK-NEXT: %[[ALL_TO_ALL_0:.*]] = sdy.all_to_all [{"y"}: 1->2] %arg0 out_sharding=<@mesh3d_4x2x4, [{"x"}, {"z"}, {"y"}]>
  // CHECK-NEXT: %[[ALL_TO_ALL_1:.*]] = sdy.all_to_all [{"z":(2)2}: 1->0] %[[ALL_TO_ALL_0]] out_sharding=<@mesh3d_4x2x4, [{"x", "z":(2)2}, {"z":(1)2}, {"y"}]>
  // CHECK-NEXT: %[[ALL_GATHER:.*]] = sdy.all_gather [{}, {"z":(1)2}, {}] %[[ALL_TO_ALL_1]] out_sharding=<@mesh3d_4x2x4, [{"x", "z":(2)2}, {}, {"y"}]>
  // CHECK-NEXT: return %[[ALL_GATHER]]
  %0 = sdy.reshard %arg0 <@mesh3d_4x2x4, [{"x", "z":(2)2}, {}, {"y"}]> : tensor<16x8x8xf32>
  return %0 : tensor<16x8x8xf32>
}

// CHECK-LABEL: func @all_to_all_subaxis_and_full_axis_then_all_gather
func.func @all_to_all_subaxis_and_full_axis_then_all_gather(%arg0 : tensor<16x8x8xf32> {sdy.sharding = #sdy.sharding<@mesh4d_z4, [{"x"}, {"z", "w", "y"}, {}]>}) -> tensor<16x8x8xf32> {
  // CHECK-NEXT: %[[ALL_TO_ALL_0:.*]] = sdy.all_to_all [{"y"}: 1->2] %arg0 out_sharding=<@mesh4d_z4, [{"x"}, {"z", "w"}, {"y"}]>
  // CHECK-NEXT: %[[ALL_TO_ALL_1:.*]] = sdy.all_to_all [{"z":(2)2, "w"}: 1->0] %[[ALL_TO_ALL_0]] out_sharding=<@mesh4d_z4, [{"x", "z":(2)2, "w"}, {"z":(1)2}, {"y"}]>
  // CHECK-NEXT: %[[ALL_GATHER:.*]] = sdy.all_gather [{}, {"z":(1)2}, {}] %[[ALL_TO_ALL_1]] out_sharding=<@mesh4d_z4, [{"x", "z":(2)2, "w"}, {}, {"y"}]>
  // CHECK-NEXT: return %[[ALL_GATHER]]
  %0 = sdy.reshard %arg0 <@mesh4d_z4, [{"x", "z":(2)2, "w"}, {}, {"y"}]> : tensor<16x8x8xf32>
  return %0 : tensor<16x8x8xf32>
}

// CHECK-LABEL: func @slice_on_src_dim_then_all_to_all
func.func @slice_on_src_dim_then_all_to_all(%arg0 : tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh4d_w4, [{}, {"w":(1)2}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: %[[ALL_SLICE:.*]] = sdy.all_slice [{}, {"w":(2)2}] %arg0 out_sharding=<@mesh4d_w4, [{}, {"w"}]>
  // CHECK-NEXT: %[[ALL_TO_ALL:.*]] = sdy.all_to_all [{"w"}: 1->0] %[[ALL_SLICE]] out_sharding=<@mesh4d_w4, [{"w"}, {}]>
  // CHECK-NEXT: return %[[ALL_TO_ALL]]
  %0 = sdy.reshard %arg0 <@mesh4d_w4, [{"w"}, {}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @slice_on_src_dim_then_all_to_all_multiple_axes
func.func @slice_on_src_dim_then_all_to_all_multiple_axes(%arg0 : tensor<16x8x8xf32> {sdy.sharding = #sdy.sharding<@mesh3d, [{}, {"x"}, {}]>}) -> tensor<16x8x8xf32> {
  // CHECK-NEXT: %[[ALL_SLICE:.*]] = sdy.all_slice [{}, {"y", "z"}, {}] %arg0 out_sharding=<@mesh3d, [{}, {"x", "y", "z"}, {}]>
  // CHECK-NEXT: %[[ALL_TO_ALL:.*]] = sdy.all_to_all [{"x", "y", "z"}: 1->2] %[[ALL_SLICE]] out_sharding=<@mesh3d, [{}, {}, {"x", "y", "z"}]>
  // CHECK-NEXT: return %[[ALL_TO_ALL]]
  %0 = sdy.reshard %arg0 <@mesh3d, [{}, {}, {"x", "y", "z"}]> : tensor<16x8x8xf32>
  return %0 : tensor<16x8x8xf32>
}

// CHECK-LABEL: func @slice_on_src_dim_then_two_all_to_alls
func.func @slice_on_src_dim_then_two_all_to_alls(%arg0 : tensor<16x8x8xf32> {sdy.sharding = #sdy.sharding<@mesh3d, [{"z"}, {"x"}, {}]>}) -> tensor<16x8x8xf32> {
  // CHECK-NEXT: %[[ALL_SLICE:.*]] = sdy.all_slice [{}, {"y"}, {}] %arg0 out_sharding=<@mesh3d, [{"z"}, {"x", "y"}, {}]>
  // CHECK-NEXT: %[[ALL_TO_ALL_0:.*]] = sdy.all_to_all [{"x", "y"}: 1->2] %[[ALL_SLICE]] out_sharding=<@mesh3d, [{"z"}, {}, {"x", "y"}]>
  // CHECK-NEXT: %[[ALL_TO_ALL_1:.*]] = sdy.all_to_all [{"z"}: 0->2] %[[ALL_TO_ALL_0]] out_sharding=<@mesh3d, [{}, {}, {"x", "y", "z"}]>
  // CHECK-NEXT: return %[[ALL_TO_ALL_1]]
  %0 = sdy.reshard %arg0 <@mesh3d, [{}, {}, {"x", "y", "z"}]> : tensor<16x8x8xf32>
  return %0 : tensor<16x8x8xf32>
}

// CHECK-LABEL: func @slice_on_src_dim_then_two_all_to_alls_2
func.func @slice_on_src_dim_then_two_all_to_alls_2(%arg0 : tensor<16x8x8xf32> {sdy.sharding = #sdy.sharding<@mesh3d, [{"y"}, {"x"}, {}]>}) -> tensor<16x8x8xf32> {
  // CHECK-NEXT: %[[ALL_SLICE:.*]] = sdy.all_slice [{"z"}, {}, {}] %arg0 out_sharding=<@mesh3d, [{"y", "z"}, {"x"}, {}]>
  // CHECK-NEXT: %[[ALL_TO_ALL_0:.*]] = sdy.all_to_all [{"x"}: 1->2] %[[ALL_SLICE]] out_sharding=<@mesh3d, [{"y", "z"}, {}, {"x"}]>
  // CHECK-NEXT: %[[ALL_TO_ALL_1:.*]] = sdy.all_to_all [{"y", "z"}: 0->2] %[[ALL_TO_ALL_0]] out_sharding=<@mesh3d, [{}, {}, {"x", "y", "z"}]>
  // CHECK-NEXT: return %[[ALL_TO_ALL_1]]
  %0 = sdy.reshard %arg0 <@mesh3d, [{}, {}, {"x", "y", "z"}]> : tensor<16x8x8xf32>
  return %0 : tensor<16x8x8xf32>
}

// CHECK-LABEL: func @slice_on_src_dim_then_two_all_to_alls_diff_tgts
func.func @slice_on_src_dim_then_two_all_to_alls_diff_tgts(%arg0 : tensor<16x8x8xf32> {sdy.sharding = #sdy.sharding<@mesh3d, [{}, {"x", "y"}, {}]>}) -> tensor<16x8x8xf32> {
  // CHECK-NEXT: %[[ALL_SLICE:.*]] = sdy.all_slice [{}, {"z"}, {}] %arg0 out_sharding=<@mesh3d, [{}, {"x", "y", "z"}, {}]>
  // CHECK-NEXT: %[[ALL_TO_ALL_0:.*]] = sdy.all_to_all [{"y", "z"}: 1->2] %[[ALL_SLICE]] out_sharding=<@mesh3d, [{}, {"x"}, {"y", "z"}]>
  // CHECK-NEXT: %[[ALL_TO_ALL_1:.*]] = sdy.all_to_all [{"x"}: 1->0] %[[ALL_TO_ALL_0]] out_sharding=<@mesh3d, [{"x"}, {}, {"y", "z"}]>
  // CHECK-NEXT: return %[[ALL_TO_ALL_1]]
  %0 = sdy.reshard %arg0 <@mesh3d, [{"x"}, {}, {"y", "z"}]> : tensor<16x8x8xf32>
  return %0 : tensor<16x8x8xf32>
}

// CHECK-LABEL: func @slice_on_src_dim_then_all_to_all_and_all_gather
func.func @slice_on_src_dim_then_all_to_all_and_all_gather(%arg0: tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh4d_w4, [{"y", "z", "w":(1)2}, {}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: %[[ALL_SLICE:.*]] = sdy.all_slice [{"w":(2)2}, {"x"}] %arg0 out_sharding=<@mesh4d_w4, [{"y", "z", "w"}, {"x"}]>
  // CHECK-NEXT: %[[ALL_TO_ALL:.*]] = sdy.all_to_all [{"w"}: 0->1] %[[ALL_SLICE]] out_sharding=<@mesh4d_w4, [{"y", "z"}, {"x", "w"}]>
  // CHECK-NEXT: %[[ALL_GATHER:.*]] = sdy.all_gather [{"z"}, {}] %[[ALL_TO_ALL]] out_sharding=<@mesh4d_w4, [{"y"}, {"x", "w"}]>
  // CHECK-NEXT: return %[[ALL_GATHER]]
  %0 = sdy.reshard %arg0 <@mesh4d_w4, [{"y"}, {"x", "w"}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @slice_on_multiple_src_dims
func.func @slice_on_multiple_src_dims(%arg0 : tensor<16x8x8xf32> {sdy.sharding = #sdy.sharding<@mesh4d, [{"z"}, {"x"}, {}]>}) -> tensor<16x8x8xf32> {
  // CHECK-NEXT: %[[ALL_SLICE:.*]] = sdy.all_slice [{"w"}, {"y"}, {}] %arg0 out_sharding=<@mesh4d, [{"z", "w"}, {"x", "y"}, {}]>
  // CHECK-NEXT: %[[ALL_TO_ALL_0:.*]] = sdy.all_to_all [{"x", "y"}: 1->2] %[[ALL_SLICE]] out_sharding=<@mesh4d, [{"z", "w"}, {}, {"x", "y"}]>
  // CHECK-NEXT: %[[ALL_TO_ALL_1:.*]] = sdy.all_to_all [{"z", "w"}: 0->2] %[[ALL_TO_ALL_0]] out_sharding=<@mesh4d, [{}, {}, {"x", "y", "z", "w"}]>
  // CHECK-NEXT: return %[[ALL_TO_ALL_1]]
  %0 = sdy.reshard %arg0 <@mesh4d, [{}, {}, {"x", "y", "z", "w"}]> : tensor<16x8x8xf32>
  return %0 : tensor<16x8x8xf32>
}

// CHECK-LABEL: func @slice_on_one_src_dim_but_not_other
func.func @slice_on_one_src_dim_but_not_other(%arg0 : tensor<2x8x8xf32> {sdy.sharding = #sdy.sharding<@mesh4d, [{"z"}, {"x"}, {}]>}) -> tensor<2x8x8xf32> {
  // CHECK-NEXT: %[[ALL_SLICE:.*]] = sdy.all_slice [{}, {"y"}, {"w"}] %arg0 out_sharding=<@mesh4d, [{"z"}, {"x", "y"}, {"w"}]>
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %[[ALL_SLICE]] out_sharding=<@mesh4d, [{"y"}, {"z", "w"}, {"x"}]>
  // CHECK-NEXT: %[[ALL_TO_ALL_0:.*]] = sdy.all_to_all [{"y"}: 0->2] %[[COLLECTIVE_PERMUTE]] out_sharding=<@mesh4d, [{}, {"z", "w"}, {"x", "y"}]>
  // CHECK-NEXT: %[[ALL_TO_ALL_1:.*]] = sdy.all_to_all [{"z", "w"}: 1->2] %[[ALL_TO_ALL_0]] out_sharding=<@mesh4d, [{}, {}, {"x", "y", "z", "w"}]>
  // CHECK-NEXT: return %[[ALL_TO_ALL_1]]
  %0 = sdy.reshard %arg0 <@mesh4d, [{}, {}, {"x", "y", "z", "w"}]> : tensor<2x8x8xf32>
  return %0 : tensor<2x8x8xf32>
}

// CHECK-LABEL: func @slice_on_src_dim_considering_existing_axes_on_src_dim
func.func @slice_on_src_dim_considering_existing_axes_on_src_dim(%arg0 : tensor<8x4xf32> {sdy.sharding = #sdy.sharding<@mesh3d, [{"x", "y"}, {}]>}) -> tensor<8x4xf32> {
  // CHECK-NEXT: %[[ALL_SLICE:.*]] = sdy.all_slice [{"z"}, {}] %arg0 out_sharding=<@mesh3d, [{"x", "y", "z"}, {}]>
  // CHECK-NEXT: %[[ALL_TO_ALL:.*]] = sdy.all_to_all [{"y", "z"}: 0->1] %[[ALL_SLICE]] out_sharding=<@mesh3d, [{"x"}, {"y", "z"}]>
  // CHECK-NEXT: return %[[ALL_TO_ALL]]
  %0 = sdy.reshard %arg0 <@mesh3d, [{"x"}, {"y", "z"}]> : tensor<8x4xf32>
  return %0 : tensor<8x4xf32>
}

// CHECK-LABEL: func @slice_on_src_dim_and_replace_axis_in_another_dim
func.func @slice_on_src_dim_and_replace_axis_in_another_dim(%arg0 : tensor<16x8x8xf32> {sdy.sharding = #sdy.sharding<@mesh4d, [{"z"}, {"x"}, {}]>}) -> tensor<16x8x8xf32> {
  // CHECK-NEXT: %[[ALL_SLICE:.*]] = sdy.all_slice [{}, {"y"}, {}] %arg0 out_sharding=<@mesh4d, [{"z"}, {"x", "y"}, {}]>
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %[[ALL_SLICE]] out_sharding=<@mesh4d, [{"w"}, {"x", "y"}, {}]>
  // CHECK-NEXT: %[[ALL_TO_ALL:.*]] = sdy.all_to_all [{"x", "y"}: 1->2] %[[COLLECTIVE_PERMUTE]] out_sharding=<@mesh4d, [{"w"}, {}, {"x", "y"}]>
  // CHECK-NEXT: return %[[ALL_TO_ALL]]
  %0 = sdy.reshard %arg0 <@mesh4d, [{"w"}, {}, {"x", "y"}]> : tensor<16x8x8xf32>
  return %0 : tensor<16x8x8xf32>
}

// CHECK-LABEL: func @cannot_slice_on_src_dim_output_sharded
func.func @cannot_slice_on_src_dim_output_sharded(%arg0 : tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh3d, [{}, {"x"}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: %[[ALL_SLICE:.*]] = sdy.all_slice [{"y", "z"}, {}] %arg0 out_sharding=<@mesh3d, [{"y", "z"}, {"x"}]>
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %[[ALL_SLICE]] out_sharding=<@mesh3d, [{"x", "y"}, {"z"}]>
  // CHECK-NEXT: return %[[COLLECTIVE_PERMUTE]]
  %0 = sdy.reshard %arg0 <@mesh3d, [{"x", "y"}, {"z"}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @cannot_slice_on_src_dim_tgt_dim_sharded
func.func @cannot_slice_on_src_dim_tgt_dim_sharded(%arg0 : tensor<16x8x8xf32> {sdy.sharding = #sdy.sharding<@mesh3d, [{}, {"x"}, {"z"}]>}) -> tensor<16x8x8xf32> {
  // CHECK-NEXT: %[[ALL_SLICE:.*]] = sdy.all_slice [{}, {}, {"y"}] %arg0 out_sharding=<@mesh3d, [{}, {"x"}, {"z", "y"}]>
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %[[ALL_SLICE]] out_sharding=<@mesh3d, [{}, {"z"}, {"x", "y"}]>
  // CHECK-NEXT: %[[ALL_TO_ALL:.*]] = sdy.all_to_all [{"z"}: 1->2] %[[COLLECTIVE_PERMUTE]] out_sharding=<@mesh3d, [{}, {}, {"x", "y", "z"}]>
  // CHECK-NEXT: return %[[ALL_TO_ALL]]
  %0 = sdy.reshard %arg0 <@mesh3d, [{}, {}, {"x", "y", "z"}]> : tensor<16x8x8xf32>
  return %0 : tensor<16x8x8xf32>
}

// CHECK-LABEL: func @cannot_slice_on_src_dim_axes_out_of_order
func.func @cannot_slice_on_src_dim_axes_out_of_order(%arg0 : tensor<4x10xf32> {sdy.sharding = #sdy.sharding<@mesh3d, [{}, {"x", "z"}]>}) -> tensor<4x10xf32> {
  // CHECK-NEXT: %[[ALL_SLICE:.*]] = sdy.all_slice [{"y"}, {}] %arg0 out_sharding=<@mesh3d, [{"y"}, {"x", "z"}]>
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %[[ALL_SLICE]] out_sharding=<@mesh3d, [{"x"}, {"y", "z"}]>
  // CHECK-NEXT: %[[ALL_TO_ALL:.*]] = sdy.all_to_all [{"y", "z"}: 1->0] %[[COLLECTIVE_PERMUTE]] out_sharding=<@mesh3d, [{"x", "y", "z"}, {}]>
  // CHECK-NEXT: return %[[ALL_TO_ALL]]
  %0 = sdy.reshard %arg0 <@mesh3d, [{"x", "y", "z"}, {}]> : tensor<4x10xf32>
  return %0 : tensor<4x10xf32>
}

// CHECK-LABEL: func @cannot_slice_on_src_dim_axes_non_contiguous
func.func @cannot_slice_on_src_dim_axes_non_contiguous(%arg0 : tensor<4x10xf32> {sdy.sharding = #sdy.sharding<@mesh4d, [{}, {"z", "w", "y"}]>}) -> tensor<4x10xf32> {
  // CHECK-NEXT: %[[ALL_SLICE:.*]] = sdy.all_slice [{"x"}, {}] %arg0 out_sharding=<@mesh4d, [{"x"}, {"z", "w", "y"}]>
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %[[ALL_SLICE]] out_sharding=<@mesh4d, [{"x"}, {"w", "y", "z"}]>
  // CHECK-NEXT: %[[ALL_TO_ALL:.*]] = sdy.all_to_all [{"y", "z"}: 1->0] %[[COLLECTIVE_PERMUTE]] out_sharding=<@mesh4d, [{"x", "y", "z"}, {"w"}]>
  // CHECK-NEXT: %[[ALL_GATHER:.*]] = sdy.all_gather [{}, {"w"}] %[[ALL_TO_ALL]] out_sharding=<@mesh4d, [{"x", "y", "z"}, {}]>
  // CHECK-NEXT: return %[[ALL_GATHER]]
  %0 = sdy.reshard %arg0 <@mesh4d, [{"x", "y", "z"}, {}]> : tensor<4x10xf32>
  return %0 : tensor<4x10xf32>
}

// CHECK-LABEL: func @cannot_slice_on_src_dim_size_too_small
func.func @cannot_slice_on_src_dim_size_too_small(%arg0 : tensor<16x4xf32> {sdy.sharding = #sdy.sharding<@mesh3d, [{}, {"x"}]>}) -> tensor<16x4xf32> {
  // CHECK-NEXT: %[[ALL_SLICE:.*]] = sdy.all_slice [{"y", "z"}, {}] %arg0 out_sharding=<@mesh3d, [{"y", "z"}, {"x"}]>
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %[[ALL_SLICE]] out_sharding=<@mesh3d, [{"x", "y"}, {"z"}]>
  // CHECK-NEXT: %[[ALL_TO_ALL:.*]] = sdy.all_to_all [{"z"}: 1->0] %[[COLLECTIVE_PERMUTE]] out_sharding=<@mesh3d, [{"x", "y", "z"}, {}]>
  // CHECK-NEXT: return %[[ALL_TO_ALL]]
  %0 = sdy.reshard %arg0 <@mesh3d, [{"x", "y", "z"}, {}]> : tensor<16x4xf32>
  return %0 : tensor<16x4xf32>
}

// TODO(tomnatan): this can be optimized by slicing "z" on dimension 0.
// CHECK-LABEL: func @cannot_slice_on_src_dim_size_too_small_2
func.func @cannot_slice_on_src_dim_size_too_small_2(%arg0 : tensor<16x4x8xf32> {sdy.sharding = #sdy.sharding<@mesh3d, [{}, {"x", "y"}, {}]>}) -> tensor<16x4x8xf32> {
  // CHECK-NEXT: %[[ALL_SLICE:.*]] = sdy.all_slice [{}, {}, {"z"}] %arg0 out_sharding=<@mesh3d, [{}, {"x", "y"}, {"z"}]>
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %[[ALL_SLICE]] out_sharding=<@mesh3d, [{}, {"x", "z"}, {"y"}]>
  // CHECK-NEXT: %[[ALL_TO_ALL_0:.*]] = sdy.all_to_all [{"z"}: 1->2] %[[COLLECTIVE_PERMUTE]] out_sharding=<@mesh3d, [{}, {"x"}, {"y", "z"}]>
  // CHECK-NEXT: %[[ALL_TO_ALL_1:.*]] = sdy.all_to_all [{"x"}: 1->0] %[[ALL_TO_ALL_0]] out_sharding=<@mesh3d, [{"x"}, {}, {"y", "z"}]>
  // CHECK-NEXT: return %[[ALL_TO_ALL_1]]
  %0 = sdy.reshard %arg0 <@mesh3d, [{"x"}, {}, {"y", "z"}]> : tensor<16x4x8xf32>
  return %0 : tensor<16x4x8xf32>
}

// CHECK-LABEL: func @cannot_slice_on_src_dim_considering_existing_axes_on_src_dim
func.func @cannot_slice_on_src_dim_considering_existing_axes_on_src_dim(%arg0 : tensor<4x4xf32> {sdy.sharding = #sdy.sharding<@mesh3d, [{"x", "y"}, {}]>}) -> tensor<4x4xf32> {
  // CHECK-NEXT: %[[ALL_SLICE:.*]] = sdy.all_slice [{}, {"z"}] %arg0 out_sharding=<@mesh3d, [{"x", "y"}, {"z"}]>
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %[[ALL_SLICE]] out_sharding=<@mesh3d, [{"x", "z"}, {"y"}]>
  // CHECK-NEXT: %[[ALL_TO_ALL:.*]] = sdy.all_to_all [{"z"}: 0->1] %[[COLLECTIVE_PERMUTE]] out_sharding=<@mesh3d, [{"x"}, {"y", "z"}]>
  // CHECK-NEXT: return %[[ALL_TO_ALL]]
  %0 = sdy.reshard %arg0 <@mesh3d, [{"x"}, {"y", "z"}]> : tensor<4x4xf32>
  return %0 : tensor<4x4xf32>
}

// CHECK-LABEL: func @cannot_slice_on_src_dim_size_non_divisible
func.func @cannot_slice_on_src_dim_size_non_divisible(%arg0 : tensor<4x10xf32> {sdy.sharding = #sdy.sharding<@mesh2d, [{}, {"x"}]>}) -> tensor<4x10xf32> {
  // CHECK-NEXT: %[[ALL_SLICE:.*]] = sdy.all_slice [{"y"}, {}] %arg0 out_sharding=<@mesh2d, [{"y"}, {"x"}]>
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %[[ALL_SLICE]] out_sharding=<@mesh2d, [{"x"}, {"y"}]>
  // CHECK-NEXT: %[[ALL_TO_ALL:.*]] = sdy.all_to_all [{"y"}: 1->0] %[[COLLECTIVE_PERMUTE]] out_sharding=<@mesh2d, [{"x", "y"}, {}]>
  // CHECK-NEXT: return %[[ALL_TO_ALL]]
  %0 = sdy.reshard %arg0 <@mesh2d, [{"x", "y"}, {}]> : tensor<4x10xf32>
  return %0 : tensor<4x10xf32>
}

// CHECK-LABEL: func @replace_same_size_axes_same_dim
func.func @replace_same_size_axes_same_dim(%arg0 : tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh3d, [{"z"}, {"y"}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %arg0 out_sharding=<@mesh3d, [{"z"}, {"x"}]>
  // CHECK-NEXT: return %[[COLLECTIVE_PERMUTE]]
  %0 = sdy.reshard %arg0 <@mesh3d, [{"z"}, {"x"}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @replace_smaller_axis_with_bigger_same_dim
func.func @replace_smaller_axis_with_bigger_same_dim(%arg0 : tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh3d_4x2x4, [{"z"}, {"y"}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: %[[ALL_SLICE:.*]] = sdy.all_slice [{}, {"x":(1)2}] %arg0 out_sharding=<@mesh3d_4x2x4, [{"z"}, {"y", "x":(1)2}]>
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %[[ALL_SLICE]] out_sharding=<@mesh3d_4x2x4, [{"z"}, {"x"}]>
  // CHECK-NEXT: return %[[COLLECTIVE_PERMUTE]]
  %0 = sdy.reshard %arg0 <@mesh3d_4x2x4, [{"z"}, {"x"}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @replace_bigger_axis_with_smaller_same_dim
func.func @replace_bigger_axis_with_smaller_same_dim(%arg0 : tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh3d_4x2x4, [{"z"}, {"x"}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %arg0 out_sharding=<@mesh3d_4x2x4, [{"z"}, {"y", "x":(2)2}]>
  // CHECK-NEXT: %[[ALL_GATHER:.*]] = sdy.all_gather [{}, {"x":(2)2}] %[[COLLECTIVE_PERMUTE]] out_sharding=<@mesh3d_4x2x4, [{"z"}, {"y"}]
  // CHECK-NEXT: return %[[ALL_GATHER]]
  %0 = sdy.reshard %arg0 <@mesh3d_4x2x4, [{"z"}, {"y"}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @replace_major_most_axis_in_dim
func.func @replace_major_most_axis_in_dim(%arg0 : tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh4d, [{"x", "y", "z"}, {}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %arg0 out_sharding=<@mesh4d, [{"w", "y", "z"}, {}]>
  // CHECK-NEXT: return %[[COLLECTIVE_PERMUTE]]
  %0 = sdy.reshard %arg0 <@mesh4d, [{"w", "y", "z"}, {}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @replace_major_most_axis_then_all_gather
func.func @replace_major_most_axis_then_all_gather(%arg0 : tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh3d, [{"x", "y"}, {}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %arg0 out_sharding=<@mesh3d, [{"z", "y"}, {}]>
  // CHECK-NEXT: %[[ALL_GATHER:.*]] = sdy.all_gather [{"y"}, {}] %[[COLLECTIVE_PERMUTE]] out_sharding=<@mesh3d, [{"z"}, {}]>
  // CHECK-NEXT: return %[[ALL_GATHER]]
  %0 = sdy.reshard %arg0 <@mesh3d, [{"z"}, {}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @replace_major_most_axis_then_all_gather_sub_axis
func.func @replace_major_most_axis_then_all_gather_sub_axis(%arg0 : tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh3d_4x2x4, [{"x", "z"}, {}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %arg0 out_sharding=<@mesh3d_4x2x4, [{"y", "x":(2)2, "z"}, {}]>
  // CHECK-NEXT: %[[ALL_GATHER:.*]] = sdy.all_gather [{"x":(2)2, "z"}, {}] %[[COLLECTIVE_PERMUTE]] out_sharding=<@mesh3d_4x2x4, [{"y"}, {}]>
  // CHECK-NEXT: return %[[ALL_GATHER]]
  %0 = sdy.reshard %arg0 <@mesh3d_4x2x4, [{"y"}, {}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @replace_major_most_axis_then_all_gather_two_dims
func.func @replace_major_most_axis_then_all_gather_two_dims(%arg0 : tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh3d, [{"x", "y"}, {"z"}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %arg0 out_sharding=<@mesh3d, [{"z", "y"}, {"x"}]>
  // CHECK-NEXT: %[[ALL_GATHER:.*]] = sdy.all_gather [{"y"}, {"x"}] %[[COLLECTIVE_PERMUTE]] out_sharding=<@mesh3d, [{"z"}, {}]>
  // CHECK-NEXT: return %[[ALL_GATHER]]
  %0 = sdy.reshard %arg0 <@mesh3d, [{"z"}, {}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @replace_same_size_axes_diff_dims
func.func @replace_same_size_axes_diff_dims(%arg0 : tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh2d, [{"x"}, {}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: %[[ALL_SLICE:.*]] = sdy.all_slice [{}, {"y"}] %arg0 out_sharding=<@mesh2d, [{"x"}, {"y"}]>
  // CHECK-NEXT: %[[ALL_GATHER:.*]] = sdy.all_gather [{"x"}, {}] %[[ALL_SLICE]] out_sharding=<@mesh2d, [{}, {"y"}]>
  // CHECK-NEXT: return %[[ALL_GATHER]]
  %0 = sdy.reshard %arg0 <@mesh2d, [{}, {"y"}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @replace_bigger_axis_with_smaller_diff_dims
func.func @replace_bigger_axis_with_smaller_diff_dims(%arg0 : tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh2d_4x2, [{"x"}, {}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: %[[ALL_SLICE:.*]] = sdy.all_slice [{}, {"y"}] %arg0 out_sharding=<@mesh2d_4x2, [{"x"}, {"y"}]>
  // CHECK-NEXT: %[[ALL_GATHER:.*]] = sdy.all_gather [{"x"}, {}] %[[ALL_SLICE]] out_sharding=<@mesh2d_4x2, [{}, {"y"}]>
  // CHECK-NEXT: return %[[ALL_GATHER]]
  %0 = sdy.reshard %arg0 <@mesh2d_4x2, [{}, {"y"}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @replace_multiple_axes_diff_dims
func.func @replace_multiple_axes_diff_dims(%arg0 : tensor<8x8x8x8xf32> {sdy.sharding = #sdy.sharding<@mesh6d, [{"x"}, {"y", "z"}, {}, {}]>}) -> tensor<8x8x8x8xf32> {
  // CHECK-NEXT: %[[ALL_SLICE:.*]] = sdy.all_slice [{}, {}, {"w", "u"}, {"v"}] %arg0 out_sharding=<@mesh6d, [{"x"}, {"y", "z"}, {"w", "u"}, {"v"}]>
  // CHECK-NEXT: %[[ALL_GATHER:.*]] = sdy.all_gather [{"x"}, {"y", "z"}, {}, {}] %[[ALL_SLICE]] out_sharding=<@mesh6d, [{}, {}, {"w", "u"}, {"v"}]>
  // CHECK-NEXT: return %[[ALL_GATHER]]
  %0 = sdy.reshard %arg0 <@mesh6d, [{}, {}, {"w", "u"}, {"v"}]> : tensor<8x8x8x8xf32>
  return %0 : tensor<8x8x8x8xf32>
}

// CHECK-LABEL: func @replace_smaller_axis_with_bigger_diff_dims
func.func @replace_smaller_axis_with_bigger_diff_dims(%arg0 : tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh2d_4x2, [{"y"}, {}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: %[[ALL_SLICE:.*]] = sdy.all_slice [{}, {"x"}] %arg0 out_sharding=<@mesh2d_4x2, [{"y"}, {"x"}]>
  // CHECK-NEXT: %[[ALL_GATHER:.*]] = sdy.all_gather [{"y"}, {}] %[[ALL_SLICE]] out_sharding=<@mesh2d_4x2, [{}, {"x"}]>
  // CHECK-NEXT: return %[[ALL_GATHER]]
  %0 = sdy.reshard %arg0 <@mesh2d_4x2, [{}, {"x"}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @slice_tgt_dim_then_all_to_all_then_all_gather
func.func @slice_tgt_dim_then_all_to_all_then_all_gather(%arg0: tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh4d_w4, [{"y", "z", "w"}, {}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: %[[ALL_SLICE:.*]] = sdy.all_slice [{}, {"x"}] %arg0 out_sharding=<@mesh4d_w4, [{"y", "z", "w"}, {"x"}]>
  // CHECK-NEXT: %[[ALL_TO_ALL:.*]] = sdy.all_to_all [{"w"}: 0->1] %[[ALL_SLICE]] out_sharding=<@mesh4d_w4, [{"y", "z"}, {"x", "w"}]>
  // CHECK-NEXT: %[[ALL_GATHER:.*]] = sdy.all_gather [{"z"}, {}] %[[ALL_TO_ALL]] out_sharding=<@mesh4d_w4, [{"y"}, {"x", "w"}]>
  // CHECK-NEXT: return %[[ALL_GATHER]]
  %0 = sdy.reshard %arg0 <@mesh4d_w4, [{"y"}, {"x", "w"}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @swap_same_size_axes_between_dims
func.func @swap_same_size_axes_between_dims(%arg0 : tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh2d, [{"x"}, {"y"}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %arg0 out_sharding=<@mesh2d, [{"y"}, {"x"}]>
  // CHECK-NEXT: return %[[COLLECTIVE_PERMUTE]]
  %0 = sdy.reshard %arg0 <@mesh2d, [{"y"}, {"x"}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @swap_diff_size_axes_between_dims
func.func @swap_diff_size_axes_between_dims(%arg0 : tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh2d_4x2, [{"x"}, {"y"}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %arg0 out_sharding=<@mesh2d_4x2, [{"y", "x":(2)2}, {"x":(1)2}]>
  // CHECK-NEXT: %[[ALL_TO_ALL:.*]] = sdy.all_to_all [{"x":(2)2}: 0->1] %[[COLLECTIVE_PERMUTE]] out_sharding=<@mesh2d_4x2, [{"y"}, {"x"}]>
  // CHECK-NEXT: return %[[ALL_TO_ALL]]
  %0 = sdy.reshard %arg0 <@mesh2d_4x2, [{"y"}, {"x"}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @slice_and_swap_axes_between_dims
func.func @slice_and_swap_axes_between_dims(%arg0 : tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh3d, [{"x"}, {"y"}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: %[[ALL_SLICE:.*]] = sdy.all_slice [{"z"}, {}] %arg0 out_sharding=<@mesh3d, [{"x", "z"}, {"y"}]>
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %[[ALL_SLICE]] out_sharding=<@mesh3d, [{"x", "y"}, {"z"}]>
  // CHECK-NEXT: return %[[COLLECTIVE_PERMUTE]]
  %0 = sdy.reshard %arg0 <@mesh3d, [{"x", "y"}, {"z"}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @swap_axes_between_dims_then_all_to_all
func.func @swap_axes_between_dims_then_all_to_all(%arg0 : tensor<8x8x8xf32> {sdy.sharding = #sdy.sharding<@mesh2d, [{"x"}, {"y"}, {}]>}) -> tensor<8x8x8xf32> {
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %arg0 out_sharding=<@mesh2d, [{"y"}, {"x"}, {}]>
  // CHECK-NEXT: %[[ALL_TO_ALL:.*]] = sdy.all_to_all [{"y"}: 0->2] %[[COLLECTIVE_PERMUTE]] out_sharding=<@mesh2d, [{}, {"x"}, {"y"}]>
  // CHECK-NEXT: return %[[ALL_TO_ALL]]
  %0 = sdy.reshard %arg0 <@mesh2d, [{}, {"x"}, {"y"}]> : tensor<8x8x8xf32>
  return %0 : tensor<8x8x8xf32>
}

// CHECK-LABEL: func @slice_sub_axes_then_swap_between_dims
func.func @slice_sub_axes_then_swap_between_dims(%arg0 : tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh3d_4x2x4, [{"z"}, {"y"}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: %[[ALL_SLICE:.*]] = sdy.all_slice [{"x":(2)2}, {"x":(1)2}] %arg0 out_sharding=<@mesh3d_4x2x4, [{"z", "x":(2)2}, {"y", "x":(1)2}]>
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %[[ALL_SLICE]] out_sharding=<@mesh3d_4x2x4, [{"y", "z"}, {"x"}]>
  // CHECK-NEXT: return %[[COLLECTIVE_PERMUTE]]
  %0 = sdy.reshard %arg0 <@mesh3d_4x2x4, [{"y", "z"}, {"x"}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @swap_sub_axes_then_all_to_all_and_all_gather
func.func @swap_sub_axes_then_all_to_all_and_all_gather(%arg0 : tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh3d_4x2x4, [{"z", "y"}, {"x"}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %arg0 out_sharding=<@mesh3d_4x2x4, [{"x", "z":(1)2}, {"y", "z":(2)2}]>
  // CHECK-NEXT: %[[ALL_TO_ALL:.*]] = sdy.all_to_all [{"z":(2)2}: 1->0] %[[COLLECTIVE_PERMUTE]] out_sharding=<@mesh3d_4x2x4, [{"x", "z"}, {"y"}]>
  // CHECK-NEXT: %[[ALL_GATHER:.*]] = sdy.all_gather [{}, {"y"}] %[[ALL_TO_ALL]] out_sharding=<@mesh3d_4x2x4, [{"x", "z"}, {}]>
  // CHECK-NEXT: return %[[ALL_GATHER]]
  %0 = sdy.reshard %arg0 <@mesh3d_4x2x4, [{"x", "z"}, {}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @reorder_axes_single_dim
func.func @reorder_axes_single_dim(%arg0 : tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh3d_4x2x4, [{"x", "y"}, {"z"}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %arg0 out_sharding=<@mesh3d_4x2x4, [{"y", "x"}, {"z"}]>
  // CHECK-NEXT: return %[[COLLECTIVE_PERMUTE]]
  %0 = sdy.reshard %arg0 <@mesh3d_4x2x4, [{"y", "x"}, {"z"}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @reorder_axes_across_dims
func.func @reorder_axes_across_dims(%arg0 : tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh3d_4x2x4, [{"x", "y"}, {"z"}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %arg0 out_sharding=<@mesh3d_4x2x4, [{"y", "z"}, {"x"}]>
  // CHECK-NEXT: return %[[COLLECTIVE_PERMUTE]]
  %0 = sdy.reshard %arg0 <@mesh3d_4x2x4, [{"y", "z"}, {"x"}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @slice_then_reorder_axes
func.func @slice_then_reorder_axes(%arg0 : tensor<16x8x8xf32> {sdy.sharding = #sdy.sharding<@mesh2d, [{"y"}, {}, {}]>}) -> tensor<16x8x8xf32> {
  // CHECK-NEXT: %[[ALL_SLICE:.*]] = sdy.all_slice [{"x"}, {}, {}] %arg0 out_sharding=<@mesh2d, [{"y", "x"}, {}, {}]>
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %[[ALL_SLICE]] out_sharding=<@mesh2d, [{"x", "y"}, {}, {}]>
  // CHECK-NEXT: return %[[COLLECTIVE_PERMUTE]]
  %0 = sdy.reshard %arg0 <@mesh2d, [{"x", "y"}, {}, {}]> : tensor<16x8x8xf32>
  return %0 : tensor<16x8x8xf32>
}

// CHECK-LABEL: func @reorder_axes_for_all_gather
func.func @reorder_axes_for_all_gather(%arg0 : tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh3d, [{"y", "x", "z"}, {}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %arg0 out_sharding=<@mesh3d, [{"z", "x", "y"}, {}]>
  // CHECK-NEXT: %[[ALL_GATHER:.*]] = sdy.all_gather [{"x", "y"}, {}] %[[COLLECTIVE_PERMUTE]] out_sharding=<@mesh3d, [{"z"}, {}]>
  // CHECK-NEXT: return %[[ALL_GATHER]]
  %0 = sdy.reshard %arg0 <@mesh3d, [{"z"}, {}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @reorder_axes_for_all_to_all_then_all_gather_single_axis
func.func @reorder_axes_for_all_to_all_then_all_gather_single_axis(%arg0 : tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh3d, [{"y", "x", "z"}, {}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %arg0 out_sharding=<@mesh3d, [{"z", "x", "y"}, {}]>
  // CHECK-NEXT: %[[ALL_TO_ALL:.*]] = sdy.all_to_all [{"y"}: 0->1] %[[COLLECTIVE_PERMUTE]] out_sharding=<@mesh3d, [{"z", "x"}, {"y"}]>
  // CHECK-NEXT: %[[ALL_GATHER:.*]] = sdy.all_gather [{"x"}, {}] %[[ALL_TO_ALL]] out_sharding=<@mesh3d, [{"z"}, {"y"}]>
  // CHECK-NEXT: return %[[ALL_GATHER]]
  %0 = sdy.reshard %arg0 <@mesh3d, [{"z"}, {"y"}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @reorder_axes_for_all_to_all_then_all_gather_remaining_axes
func.func @reorder_axes_for_all_to_all_then_all_gather_remaining_axes(%arg0 : tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh3d, [{"z", "y", "x"}, {}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %arg0 out_sharding=<@mesh3d, [{"z", "x", "y"}, {}]>
  // CHECK-NEXT: %[[ALL_TO_ALL:.*]] = sdy.all_to_all [{"y"}: 0->1] %[[COLLECTIVE_PERMUTE]] out_sharding=<@mesh3d, [{"z", "x"}, {"y"}]>
  // CHECK-NEXT: %[[ALL_GATHER:.*]] = sdy.all_gather [{"z", "x"}, {}] %[[ALL_TO_ALL]] out_sharding=<@mesh3d, [{}, {"y"}]>
  // CHECK-NEXT: return %[[ALL_GATHER]]
  %0 = sdy.reshard %arg0 <@mesh3d, [{}, {"y"}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @all_to_all_axes_at_src_out_of_order
func.func @all_to_all_axes_at_src_out_of_order(%arg0 : tensor<16x8x8xf32> {sdy.sharding = #sdy.sharding<@mesh2d, [{}, {"y", "x"}, {}]>}) -> tensor<16x8x8xf32> {
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %arg0 out_sharding=<@mesh2d, [{}, {"x", "y"}, {}]>
  // CHECK-NEXT: %[[ALL_TO_ALL:.*]] = sdy.all_to_all [{"x", "y"}: 1->0] %[[COLLECTIVE_PERMUTE]] out_sharding=<@mesh2d, [{"x", "y"}, {}, {}]>
  // CHECK-NEXT: return %[[ALL_TO_ALL]]
  %0 = sdy.reshard %arg0 <@mesh2d, [{"x", "y"}, {}, {}]> : tensor<16x8x8xf32>
  return %0 : tensor<16x8x8xf32>
}

// CHECK-LABEL: func @all_to_all_axes_at_src_and_tgt_out_of_order
func.func @all_to_all_axes_at_src_and_tgt_out_of_order(%arg0 : tensor<16x8x8xf32> {sdy.sharding = #sdy.sharding<@mesh3d_4x2x4, [{"z"}, {"y", "x"}, {}]>}) -> tensor<16x8x8xf32> {
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %arg0 out_sharding=<@mesh3d_4x2x4, [{"x"}, {"y", "z"}, {}]>
  // CHECK-NEXT: %[[ALL_TO_ALL:.*]] = sdy.all_to_all [{"y", "z"}: 1->0] %[[COLLECTIVE_PERMUTE]] out_sharding=<@mesh3d_4x2x4, [{"x", "y", "z"}, {}, {}]>
  // CHECK-NEXT: return %[[ALL_TO_ALL]]
  %0 = sdy.reshard %arg0 <@mesh3d_4x2x4, [{"x", "y", "z"}, {}, {}]> : tensor<16x8x8xf32>
  return %0 : tensor<16x8x8xf32>
}

// CHECK-LABEL: func @all_to_all_two_tgt_dims_src_out_of_order
func.func @all_to_all_two_tgt_dims_src_out_of_order(%arg0 : tensor<16x8x8xf32> {sdy.sharding = #sdy.sharding<@mesh3d_4x2x4, [{}, {"x", "z", "y"}, {}]>}) -> tensor<16x8x8xf32> {
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %arg0 out_sharding=<@mesh3d_4x2x4, [{}, {"x", "y", "z"}, {}]>
  // CHECK-NEXT: %[[ALL_TO_ALL_0:.*]] = sdy.all_to_all [{"z"}: 1->2] %[[COLLECTIVE_PERMUTE]] out_sharding=<@mesh3d_4x2x4, [{}, {"x", "y"}, {"z"}]>
  // CHECK-NEXT: %[[ALL_TO_ALL_1:.*]] = sdy.all_to_all [{"x", "y"}: 1->0] %[[ALL_TO_ALL_0]] out_sharding=<@mesh3d_4x2x4, [{"x", "y"}, {}, {"z"}]>
  // CHECK-NEXT: return %[[ALL_TO_ALL_1]]
  %0 = sdy.reshard %arg0 <@mesh3d_4x2x4, [{"x", "y"}, {}, {"z"}]> : tensor<16x8x8xf32>
  return %0 : tensor<16x8x8xf32>
}

// CHECK-LABEL: func @all_to_all_two_tgt_dims_src_out_of_order_2
func.func @all_to_all_two_tgt_dims_src_out_of_order_2(%arg0 : tensor<16x8x8xf32> {sdy.sharding = #sdy.sharding<@mesh3d_4x2x4, [{}, {"y", "z", "x"}, {}]>}) -> tensor<16x8x8xf32> {
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %arg0 out_sharding=<@mesh3d_4x2x4, [{}, {"x", "y", "z"}, {}]>
  // CHECK-NEXT: %[[ALL_TO_ALL_0:.*]] = sdy.all_to_all [{"z"}: 1->2] %[[COLLECTIVE_PERMUTE]] out_sharding=<@mesh3d_4x2x4, [{}, {"x", "y"}, {"z"}]>
  // CHECK-NEXT: %[[ALL_TO_ALL_1:.*]] = sdy.all_to_all [{"x", "y"}: 1->0] %[[ALL_TO_ALL_0]] out_sharding=<@mesh3d_4x2x4, [{"x", "y"}, {}, {"z"}]>
  // CHECK-NEXT: return %[[ALL_TO_ALL_1]]
  %0 = sdy.reshard %arg0 <@mesh3d_4x2x4, [{"x", "y"}, {}, {"z"}]> : tensor<16x8x8xf32>
  return %0 : tensor<16x8x8xf32>
}

// CHECK-LABEL: func @all_to_all_and_gather_src_dim_out_of_order
func.func @all_to_all_and_gather_src_dim_out_of_order(%arg0 : tensor<16x8x8xf32> {sdy.sharding = #sdy.sharding<@mesh4d_z4, [{"x"}, {"y", "z", "w"}, {}]>}) -> tensor<16x8x8xf32> {
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %arg0 out_sharding=<@mesh4d_z4, [{"x"}, {"z", "w", "y"}, {}]>
  // CHECK-NEXT: %[[ALL_TO_ALL_0:.*]] = sdy.all_to_all [{"y"}: 1->2] %[[COLLECTIVE_PERMUTE]] out_sharding=<@mesh4d_z4, [{"x"}, {"z", "w"}, {"y"}]>
  // CHECK-NEXT: %[[ALL_TO_ALL_1:.*]] = sdy.all_to_all [{"z":(2)2, "w"}: 1->0] %[[ALL_TO_ALL_0]] out_sharding=<@mesh4d_z4, [{"x", "z":(2)2, "w"}, {"z":(1)2}, {"y"}]>
  // CHECK-NEXT: %[[ALL_GATHER:.*]] = sdy.all_gather [{}, {"z":(1)2}, {}] %[[ALL_TO_ALL_1]] out_sharding=<@mesh4d_z4, [{"x", "z":(2)2, "w"}, {}, {"y"}]>
  // CHECK-NEXT: return %[[ALL_GATHER]]
  %0 = sdy.reshard %arg0 <@mesh4d_z4, [{"x", "z":(2)2, "w"}, {}, {"y"}]> : tensor<16x8x8xf32>
  return %0 : tensor<16x8x8xf32>
}

// CHECK-LABEL: func @reorder_sub_axes
func.func @reorder_sub_axes(%arg0: tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh4d_w4, [{"y", "w":(1)2, "z", "w":(2)2}, {}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: %[[ALL_SLICE:.*]] = sdy.all_slice [{}, {"x"}] %arg0 out_sharding=<@mesh4d_w4, [{"y", "w":(1)2, "z", "w":(2)2}, {"x"}]>
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %[[ALL_SLICE]] out_sharding=<@mesh4d_w4, [{"y", "z", "w"}, {"x"}]>
  // CHECK-NEXT: %[[ALL_TO_ALL:.*]] = sdy.all_to_all [{"w"}: 0->1] %[[COLLECTIVE_PERMUTE]] out_sharding=<@mesh4d_w4, [{"y", "z"}, {"x", "w"}]>
  // CHECK-NEXT: %[[ALL_GATHER:.*]] = sdy.all_gather [{"z"}, {}] %[[ALL_TO_ALL]] out_sharding=<@mesh4d_w4, [{"y"}, {"x", "w"}]>
  // CHECK-NEXT: return %[[ALL_GATHER]]
  %0 = sdy.reshard %arg0 <@mesh4d_w4, [{"y"}, {"x", "w"}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @replace_sub_axes
func.func @replace_sub_axes(%arg0: tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh4d_w4, [{"y", "z", "w":(2)2}, {}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: %[[ALL_SLICE:.*]] = sdy.all_slice [{}, {"x", "w":(1)2}] %arg0 out_sharding=<@mesh4d_w4, [{"y", "z", "w":(2)2}, {"x", "w":(1)2}]>
  // CHECK-NEXT: %[[ALL_TO_ALL:.*]] = sdy.all_to_all [{"w":(2)2}: 0->1] %[[ALL_SLICE]] out_sharding=<@mesh4d_w4, [{"y", "z"}, {"x", "w"}]>
  // CHECK-NEXT: %[[ALL_GATHER:.*]] = sdy.all_gather [{"z"}, {}] %[[ALL_TO_ALL]] out_sharding=<@mesh4d_w4, [{"y"}, {"x", "w"}]>
  // CHECK-NEXT: return %[[ALL_GATHER]]
  %0 = sdy.reshard %arg0 <@mesh4d_w4, [{"y"}, {"x", "w"}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @replace_sub_axes_2
func.func @replace_sub_axes_2(%arg0: tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh4d_w16, [{"y", "w":(4)2, "z", "w":(1)2}, {}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: %[[ALL_SLICE:.*]] = sdy.all_slice [{}, {"x", "w":(2)2, "w":(8)2}] %arg0 out_sharding=<@mesh4d_w16, [{"y", "w":(4)2, "z", "w":(1)2}, {"x", "w":(2)2, "w":(8)2}]>
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %[[ALL_SLICE]] out_sharding=<@mesh4d_w16, [{"y", "z", "w":(1)2, "w":(8)2}, {"x", "w":(2)4}]>
  // CHECK-NEXT: %[[ALL_TO_ALL:.*]] = sdy.all_to_all [{"w":(8)2}: 0->1] %[[COLLECTIVE_PERMUTE]] out_sharding=<@mesh4d_w16, [{"y", "z", "w":(1)2}, {"x", "w":(2)8}]>
  // CHECK-NEXT: %[[ALL_GATHER:.*]] = sdy.all_gather [{"z", "w":(1)2}, {}] %[[ALL_TO_ALL]] out_sharding=<@mesh4d_w16, [{"y"}, {"x", "w":(2)8}]>
  // CHECK-NEXT: return %[[ALL_GATHER]]
  %0 = sdy.reshard %arg0 <@mesh4d_w16, [{"y"}, {"x", "w":(2)8}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @replace_sub_axes_3
func.func @replace_sub_axes_3(%arg0: tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh4d_w16, [{"y", "w":(4)2, "z", "w":(1)2}, {}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: %[[ALL_SLICE:.*]] = sdy.all_slice [{}, {"x", "w":(2)2, "w":(8)2}] %arg0 out_sharding=<@mesh4d_w16, [{"y", "w":(4)2, "z", "w":(1)2}, {"x", "w":(2)2, "w":(8)2}]>
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %[[ALL_SLICE]] out_sharding=<@mesh4d_w16, [{"y", "z", "w":(4)4}, {"x", "w":(1)4}]>
  // CHECK-NEXT: %[[ALL_TO_ALL:.*]] = sdy.all_to_all [{"w":(4)4}: 0->1] %[[COLLECTIVE_PERMUTE]] out_sharding=<@mesh4d_w16, [{"y", "z"}, {"x", "w"}]>
  // CHECK-NEXT: %[[ALL_GATHER:.*]] = sdy.all_gather [{"z"}, {}] %[[ALL_TO_ALL]] out_sharding=<@mesh4d_w16, [{"y"}, {"x", "w"}]>
  // CHECK-NEXT: return %[[ALL_GATHER]]
  %0 = sdy.reshard %arg0 <@mesh4d_w16, [{"y"}, {"x", "w"}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @reorder_device_ids
func.func @reorder_device_ids(%arg0 : tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh2d, [{"x"}, {"y"}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %arg0 out_sharding=<@mesh2d_non_iota, [{"x"}, {"y"}]>
  // CHECK-NEXT: return %[[COLLECTIVE_PERMUTE]]
  %0 = sdy.reshard %arg0 <@mesh2d_non_iota, [{"x"}, {"y"}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @reorder_axes_and_device_ids
func.func @reorder_axes_and_device_ids(%arg0 : tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh2d, [{"x", "y"}, {}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %arg0 out_sharding=<@mesh2d_non_iota, [{"y", "x"}, {}]>
  // CHECK-NEXT: return %[[COLLECTIVE_PERMUTE]]
  %0 = sdy.reshard %arg0 <@mesh2d_non_iota, [{"y", "x"}, {}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @reorder_device_ids_then_all_gather
func.func @reorder_device_ids_then_all_gather(%arg0 : tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh2d, [{"x"}, {"y"}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %arg0 out_sharding=<@mesh2d_non_iota, [{"x"}, {"y"}]>
  // CHECK-NEXT: %[[ALL_GATHER:.*]] = sdy.all_gather [{}, {"y"}] %[[COLLECTIVE_PERMUTE]] out_sharding=<@mesh2d_non_iota, [{"x"}, {}]>
  // CHECK-NEXT: return %[[ALL_GATHER]]
  %0 = sdy.reshard %arg0 <@mesh2d_non_iota, [{"x"}, {}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @slice_then_reorder_axes_and_device_ids
func.func @slice_then_reorder_axes_and_device_ids(%arg0 : tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh2d, [{"x"}, {}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: %[[ALL_SLICE:.*]] = sdy.all_slice [{"y"}, {}] %arg0 out_sharding=<@mesh2d, [{"x", "y"}, {}]>
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %[[ALL_SLICE]] out_sharding=<@mesh2d_non_iota, [{"y", "x"}, {}]>
  // CHECK-NEXT: return %[[COLLECTIVE_PERMUTE]]
  %0 = sdy.reshard %arg0 <@mesh2d_non_iota, [{"y", "x"}, {}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @slice_then_reorder_device_ids_then_all_to_all
func.func @slice_then_reorder_device_ids_then_all_to_all(%arg0 : tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh2d_non_iota, [{"x"}, {}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: %[[ALL_SLICE:.*]] = sdy.all_slice [{"y"}, {}] %arg0 out_sharding=<@mesh2d_non_iota, [{"x", "y"}, {}]>
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %[[ALL_SLICE]] out_sharding=<@mesh2d_non_iota_2, [{"x", "y"}, {}]>
  // CHECK-NEXT: %[[ALL_TO_ALL:.*]] = sdy.all_to_all [{"x", "y"}: 0->1] %[[COLLECTIVE_PERMUTE]] out_sharding=<@mesh2d_non_iota_2, [{}, {"x", "y"}]>
  // CHECK-NEXT: return %[[ALL_TO_ALL]]
  %0 = sdy.reshard %arg0 <@mesh2d_non_iota_2, [{}, {"x", "y"}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// This test also verifies that axes aren't reordered when it's not necessary,
// even when device ids are reordered.
// CHECK-LABEL: func @reorder_device_ids_then_two_all_to_alls
func.func @reorder_device_ids_then_two_all_to_alls(%arg0 : tensor<16x8x8xf32> {sdy.sharding = #sdy.sharding<@mesh2d, [{}, {"y", "x"}, {}]>}) -> tensor<16x8x8xf32> {
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %arg0 out_sharding=<@mesh2d_non_iota, [{}, {"y", "x"}, {}]>
  // CHECK-NEXT: %[[ALL_TO_ALL_0:.*]] = sdy.all_to_all [{"x"}: 1->0] %[[COLLECTIVE_PERMUTE]] out_sharding=<@mesh2d_non_iota, [{"x"}, {"y"}, {}]>
  // CHECK-NEXT: %[[ALL_TO_ALL_1:.*]] = sdy.all_to_all [{"y"}: 1->2] %[[ALL_TO_ALL_0]] out_sharding=<@mesh2d_non_iota, [{"x"}, {}, {"y"}]>
  // CHECK-NEXT: return %[[ALL_TO_ALL_1]]
  %0 = sdy.reshard %arg0 <@mesh2d_non_iota, [{"x"}, {}, {"y"}]> : tensor<16x8x8xf32>
  return %0 : tensor<16x8x8xf32>
}

// CHECK-LABEL: func @reshard_on_while_block_arg
func.func @reshard_on_while_block_arg(%arg0: tensor<32x96xf32>, %arg1: tensor<i1>) -> tensor<32x96xf32> {
  // CHECK-NEXT: stablehlo.while(%iterArg = %arg0) : tensor<32x96xf32>
  // CHECK-SAME:  attributes {sdy.sharding = #sdy.sharding_per_value<[<@mesh2d, [{"x"}, {}]>]>}
  // CHECK:        do {
  // CHECK-NEXT:     %[[ALL_TO_ALL:.*]] = sdy.all_to_all [{"x"}: 0->1] %iterArg out_sharding=<@mesh2d, [{}, {"x"}]>
  // CHECK-NEXT:     stablehlo.return %[[ALL_TO_ALL]]
  // CHECK-NEXT:   }
  %0 = stablehlo.while(%iterArg = %arg0) : tensor<32x96xf32>
    attributes {sdy.sharding = #sdy.sharding_per_value<[<@mesh2d, [{"x"}, {}]>]>}
    cond {
    stablehlo.return %arg1 : tensor<i1>
  } do {
    %1 = sdy.reshard %iterArg <@mesh2d, [{}, {"x"}]> : tensor<32x96xf32>
    stablehlo.return %1 : tensor<32x96xf32>
  }
  return %0 : tensor<32x96xf32>
}

// CHECK-LABEL: func @replace_smaller_axis_with_bigger_same_dim_non_divisible
func.func @replace_smaller_axis_with_bigger_same_dim_non_divisible(%arg0: tensor<12x12xf32> {sdy.sharding = #sdy.sharding<@mesh2d_2x3, [{"x"}, {}]>}) -> tensor<12x12xf32> {
  // CHECK-NEXT: %[[ALL_SLICE:.*]] = sdy.all_slice [{"y"}, {}] %arg0 out_sharding=<@mesh2d_2x3, [{"x", "y"}, {}]>
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %[[ALL_SLICE]] out_sharding=<@mesh2d_2x3, [{"y", "x"}, {}]>
  // CHECK-NEXT: %[[ALL_GATHER:.*]] = sdy.all_gather [{"x"}, {}] %[[COLLECTIVE_PERMUTE]] out_sharding=<@mesh2d_2x3, [{"y"}, {}]>
  // CHECK-NEXT: return %[[ALL_GATHER]]
 %0 = sdy.reshard %arg0 <@mesh2d_2x3, [{"y"}, {}]> : tensor<12x12xf32>
 return %0 : tensor<12x12xf32>
}

// CHECK-LABEL: func @replace_bigger_axis_with_smaller_same_dim_non_divisible
func.func @replace_bigger_axis_with_smaller_same_dim_non_divisible(%arg0: tensor<12x12xf32> {sdy.sharding = #sdy.sharding<@mesh2d_2x3, [{"y"}, {}]>}) -> tensor<12x12xf32> {
  // CHECK-NEXT: %[[ALL_SLICE:.*]] = sdy.all_slice [{"x"}, {}] %arg0 out_sharding=<@mesh2d_2x3, [{"y", "x"}, {}]>
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %[[ALL_SLICE]] out_sharding=<@mesh2d_2x3, [{"x", "y"}, {}]>
  // CHECK-NEXT: %[[ALL_GATHER:.*]] = sdy.all_gather [{"y"}, {}] %[[COLLECTIVE_PERMUTE]] out_sharding=<@mesh2d_2x3, [{"x"}, {}]>
  // CHECK-NEXT: return %[[ALL_GATHER]]
 %0 = sdy.reshard %arg0 <@mesh2d_2x3, [{"x"}, {}]> : tensor<12x12xf32>
 return %0 : tensor<12x12xf32>
}

// CHECK-LABEL: func @replace_smaller_axis_with_bigger_gcd_greater_than_one
func.func @replace_smaller_axis_with_bigger_gcd_greater_than_one(%arg0: tensor<12x12xf32> {sdy.sharding = #sdy.sharding<@mesh2d_4x6, [{"x"}, {}]>}) -> tensor<12x12xf32> {
  // CHECK-NEXT: %[[ALL_SLICE:.*]] = sdy.all_slice [{"y":(1)3}, {}] %arg0 out_sharding=<@mesh2d_4x6, [{"x", "y":(1)3}, {}]>
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %[[ALL_SLICE]] out_sharding=<@mesh2d_4x6, [{"y", "x":(1)2}, {}]>
  // CHECK-NEXT: %[[ALL_GATHER:.*]] = sdy.all_gather [{"x":(1)2}, {}] %[[COLLECTIVE_PERMUTE]] out_sharding=<@mesh2d_4x6, [{"y"}, {}]>
  // CHECK-NEXT: return %[[ALL_GATHER]]
 %0 = sdy.reshard %arg0 <@mesh2d_4x6, [{"y"}, {}]> : tensor<12x12xf32>
 return %0 : tensor<12x12xf32>
}

// CHECK-LABEL: func @replace_bigger_axis_with_smaller_gcd_greater_than_one
func.func @replace_bigger_axis_with_smaller_gcd_greater_than_one(%arg0: tensor<12x12xf32> {sdy.sharding = #sdy.sharding<@mesh2d_4x6, [{"y"}, {}]>}) -> tensor<12x12xf32> {
  // CHECK-NEXT: %[[ALL_SLICE:.*]] = sdy.all_slice [{"x":(1)2}, {}] %arg0 out_sharding=<@mesh2d_4x6, [{"y", "x":(1)2}, {}]>
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %[[ALL_SLICE]] out_sharding=<@mesh2d_4x6, [{"x", "y":(1)3}, {}]>
  // CHECK-NEXT: %[[ALL_GATHER:.*]] = sdy.all_gather [{"y":(1)3}, {}] %[[COLLECTIVE_PERMUTE]] out_sharding=<@mesh2d_4x6, [{"x"}, {}]>
  // CHECK-NEXT: return %[[ALL_GATHER]]
 %0 = sdy.reshard %arg0 <@mesh2d_4x6, [{"x"}, {}]> : tensor<12x12xf32>
 return %0 : tensor<12x12xf32>
}

// CHECK-LABEL: func @swap_non_divisible_axes_diff_dim
func.func @swap_non_divisible_axes_diff_dim(%arg0: tensor<12x12xf32> {sdy.sharding = #sdy.sharding<@mesh2d_2x3, [{"x"}, {"y"}]>}) -> tensor<12x12xf32> {
  // CHECK-NEXT: %[[ALL_TO_ALL:.*]] = sdy.all_to_all [{"x"}: 0->1] %arg0 out_sharding=<@mesh2d_2x3, [{}, {"y", "x"}]>
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %[[ALL_TO_ALL]] out_sharding=<@mesh2d_2x3, [{}, {"x", "y"}]>
  // CHECK-NEXT: %[[ALL_TO_ALL:.*]] = sdy.all_to_all [{"y"}: 1->0] %[[COLLECTIVE_PERMUTE]] out_sharding=<@mesh2d_2x3, [{"y"}, {"x"}]>
  // CHECK-NEXT: return %[[ALL_TO_ALL]]
 %0 = sdy.reshard %arg0 <@mesh2d_2x3, [{"y"}, {"x"}]> : tensor<12x12xf32>
 return %0 : tensor<12x12xf32>
}

// CHECK-LABEL: func @replace_axes_and_all_gather_gcd_greater_than_one
func.func @replace_axes_and_all_gather_gcd_greater_than_one(%arg0: tensor<12x12xf32> {sdy.sharding = #sdy.sharding<@mesh2d_4x6, [{"x"}, {"y":(1)2}]>}) -> tensor<12x12xf32> {
  // CHECK-NEXT: %[[ALL_SLICE:.*]] = sdy.all_slice [{"y":(2)3}, {}] %arg0 out_sharding=<@mesh2d_4x6, [{"x", "y":(2)3}, {"y":(1)2}]>
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %[[ALL_SLICE]] out_sharding=<@mesh2d_4x6, [{"y", "x":(1)2}, {"x":(2)2}]>
  // CHECK-NEXT: %[[ALL_GATHER:.*]] = sdy.all_gather [{"x":(1)2}, {"x":(2)2}] %[[COLLECTIVE_PERMUTE]] out_sharding=<@mesh2d_4x6, [{"y"}, {}]>
  // CHECK-NEXT: return %[[ALL_GATHER]]
 %0 = sdy.reshard %arg0 <@mesh2d_4x6, [{"y"}, {}]> : tensor<12x12xf32>
 return %0 : tensor<12x12xf32>
}

// CHECK-LABEL: func @replace_axes_and_all_gather_gcd_greater_than_one_2
func.func @replace_axes_and_all_gather_gcd_greater_than_one_2(%arg0: tensor<12x12xf32> {sdy.sharding = #sdy.sharding<@mesh3d_4x6x2, [{"x"}, {"z"}]>}) -> tensor<12x12xf32> {
  // CHECK-NEXT: %[[ALL_SLICE:.*]] = sdy.all_slice [{"y":(1)3}, {}] %arg0 out_sharding=<@mesh3d_4x6x2, [{"x", "y":(1)3}, {"z"}]>
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %[[ALL_SLICE]] out_sharding=<@mesh3d_4x6x2, [{"y", "x":(1)2}, {"z"}]>
  // CHECK-NEXT: %[[ALL_GATHER:.*]] = sdy.all_gather [{"x":(1)2}, {"z"}] %[[COLLECTIVE_PERMUTE]] out_sharding=<@mesh3d_4x6x2, [{"y"}, {}]>
  // CHECK-NEXT: return %[[ALL_GATHER]]
 %0 = sdy.reshard %arg0 <@mesh3d_4x6x2, [{"y"}, {}]> : tensor<12x12xf32>
 return %0 : tensor<12x12xf32>
}

// CHECK-LABEL: func @replace_axes_and_all_gather_gcd_greater_than_one_3
func.func @replace_axes_and_all_gather_gcd_greater_than_one_3(%arg0: tensor<12x10xf32> {sdy.sharding = #sdy.sharding<@mesh3d_4x6x5, [{"x"}, {"z"}]>}) -> tensor<12x10xf32> {
  // CHECK-NEXT: %[[ALL_SLICE:.*]] = sdy.all_slice [{"y":(1)3}, {}] %arg0 out_sharding=<@mesh3d_4x6x5, [{"x", "y":(1)3}, {"z"}]>
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %[[ALL_SLICE]] out_sharding=<@mesh3d_4x6x5, [{"y", "x":(1)2}, {"z"}]>
  // CHECK-NEXT: %[[ALL_GATHER:.*]] = sdy.all_gather [{"x":(1)2}, {"z"}] %[[COLLECTIVE_PERMUTE]] out_sharding=<@mesh3d_4x6x5, [{"y"}, {}]>
  // CHECK-NEXT: return %[[ALL_GATHER]]
 %0 = sdy.reshard %arg0 <@mesh3d_4x6x5, [{"y"}, {}]> : tensor<12x10xf32>
 return %0 : tensor<12x10xf32>
}

// CHECK-LABEL: func @out_unreduced_axes_preserved
func.func @out_unreduced_axes_preserved(%arg0 : tensor<16x8xf32> {sdy.sharding=#sdy.sharding<@mesh3d, [{"y", "z"}, {}], unreduced={"x"}>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: %[[COLLECTIVE_PERMUTE:.*]] = sdy.collective_permute %arg0 out_sharding=<@mesh3d, [{"z", "y"}, {}], unreduced={"x"}>
  // CHECK-NEXT: %[[ALL_TO_ALL:.*]] = sdy.all_to_all [{"y"}: 0->1] %[[COLLECTIVE_PERMUTE]] out_sharding=<@mesh3d, [{"z"}, {"y"}], unreduced={"x"}>
  // CHECK-NEXT: %[[ALL_GATHER:.*]] = sdy.all_gather [{"z"}, {}] %[[ALL_TO_ALL]] out_sharding=<@mesh3d, [{}, {"y"}], unreduced={"x"}>
  // CHECK-NEXT: return %[[ALL_GATHER]]
  %0 = sdy.reshard %arg0 <@mesh3d, [{}, {"y"}], unreduced={"x"}> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// TODO(b/391138813): Add proper support for axes that can't co-exist

// LABEL: func @reshard_with_non_divisible_subaxes_same_pre_size
// func.func @reshard_with_non_divisible_subaxes_same_pre_size(%arg0 : tensor<6x2xf32> {sdy.sharding=#sdy.sharding<@mesh1d_6, [{"x":(1)2}, {}]>}) -> tensor<6x2xf32> {
//   NEXT: %[[ALL_GATHER:.*]] = sdy.all_gather [{"x":(1)2}, {}] %arg0 out_sharding=<@mesh1d_6, [{}, {}]>
//   NEXT: %[[ALL_SLICE:.*]] = sdy.all_slice [{"x":(1)3}, {}] %[[ALL_GATHER]] out_sharding=<@mesh1d_6, [{"x":(1)3}, {}]>
//   NEXT: return %[[ALL_SLICE]]
//  %0 = sdy.reshard %arg0 <@mesh1d_6, [{"x":(1)3}, {}]> :  tensor<6x2xf32>
//  return %0 : tensor<6x2xf32>
// }

// LABEL: func @reshard_with_non_divisible_overlapping_subaxes
// func.func @reshard_with_non_divisible_overlapping_subaxes(%arg0 : tensor<6x2xf32> {sdy.sharding=#sdy.sharding<@mesh1d_6, [{"x":(2)3}, {}]>}) -> tensor<6x2xf32> {
//   NEXT: %[[ALL_GATHER:.*]] = sdy.all_gather [{"x":(2)3}, {}] %arg0 out_sharding=<@mesh1d_6, [{}, {}]>
//   NEXT: %[[ALL_SLICE:.*]] = sdy.all_slice [{"x":(1)3}, {}] %[[ALL_GATHER]] out_sharding=<@mesh1d_6, [{"x":(1)3}, {}]>
//   NEXT: return %[[ALL_SLICE]]
//  %0 = sdy.reshard %arg0 <@mesh1d_6, [{"x":(1)3}, {}]> :  tensor<6x2xf32>
//  return %0 : tensor<6x2xf32>
// }

// LABEL: func @reshard_with_non_divisible_overlapping_diff_dim
// func.func @reshard_with_non_divisible_overlapping_diff_dim(%arg0 : tensor<6x2xf32> {sdy.sharding=#sdy.sharding<@mesh1d_6, [{"x":(2)3}, {}]>}) -> tensor<6x2xf32> {
//   NEXT: %[[ALL_GATHER:.*]] = sdy.all_gather [{"x":(2)3}, {}] %arg0 out_sharding=<@mesh1d_6, [{}, {}]>
//   NEXT: %[[ALL_SLICE:.*]] = sdy.all_slice [{}, {"x":(1)3}] %[[ALL_GATHER]] out_sharding=<@mesh1d_6, [{}, {"x":(1)3}]>
//   NEXT: return %[[ALL_SLICE]]
//  %0 = sdy.reshard %arg0 <@mesh1d_6, [{}, {"x":(1)3}]> :  tensor<6x2xf32>
//  return %0 : tensor<6x2xf32>
// }

// CHECK-LABEL: func @reshard_with_propagation_barrier
// CHECK-SAME:    %[[ARG0:.*]]: tensor<8x8x8xf32>
func.func @reshard_with_propagation_barrier(
    %arg0: tensor<8x8x8xf32> {sdy.sharding = #sdy.sharding<@mesh3d, [{"x"}, {"y"}, {"z"}]>})
    -> tensor<8x8x8xf32> {
  %0 = sdy.propagation_barrier %arg0 allowed_direction=BACKWARD : tensor<8x8x8xf32>

  // CHECK-NEXT: %[[BARRIER:.*]] = sdy.propagation_barrier %[[ARG0]]
  // CHECK-NEXT: %[[ALL_GATHER:.*]] = sdy.all_gather [{"x"}, {"y"}, {"z"}] %[[ARG0]] out_sharding=<@mesh3d, [{}, {}, {}]>
  // CHECK-NEXT: return %[[ALL_GATHER]]
  %1 = sdy.reshard %0 <@mesh3d, [{}, {}, {}]> : tensor<8x8x8xf32>

  return %1 : tensor<8x8x8xf32>
}

//===----------------------------------------------------------------------===//
// Single-Device Reshard Tests (Preserved as sdy.reshard)
//===----------------------------------------------------------------------===//

// CHECK-LABEL: func @single_device_in_sharding
// CHECK-SAME: (%[[ARG0:.*]]: tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@single_dev_0, []>}) -> tensor<16x8xf32> {
func.func @single_device_in_sharding(%arg0 : tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@single_dev_0, []>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: %[[RESHARD:.*]] = sdy.reshard %[[ARG0]] <@mesh2d, [{}, {}]> : tensor<16x8xf32>
  // CHECK-NEXT: return %[[RESHARD]] : tensor<16x8xf32>
  %0 = sdy.reshard %arg0 <@mesh2d, [{}, {}]> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}

// CHECK-LABEL: func @single_device_out_sharding
// CHECK-SAME: (%[[ARG0:.*]]: tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh2d, [{}, {}]>}) -> tensor<16x8xf32> {
func.func @single_device_out_sharding(%arg0 : tensor<16x8xf32> {sdy.sharding = #sdy.sharding<@mesh2d, [{}, {}]>}) -> tensor<16x8xf32> {
  // CHECK-NEXT: %[[RESHARD:.*]] = sdy.reshard %[[ARG0]] <@single_dev_0, []> : tensor<16x8xf32>
  // CHECK-NEXT: return %[[RESHARD]] : tensor<16x8xf32>
  %0 = sdy.reshard %arg0 <@single_dev_0, []> : tensor<16x8xf32>
  return %0 : tensor<16x8xf32>
}


