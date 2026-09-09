# AOT ID: ['1_inference']
from ctypes import c_void_p, c_long, c_int
import torch
import math
import random
import os
import tempfile
from math import inf, nan
from cmath import nanj
from torch._inductor.hooks import run_intermediate_hooks
from torch._inductor.utils import maybe_profile
from torch._inductor.codegen.memory_planning import _align as align
from torch import device, empty_strided
from torch._inductor.async_compile import AsyncCompile
from torch._inductor.select_algorithm import extern_kernels
import triton
import triton.language as tl
from torch._inductor.runtime.triton_heuristics import start_graph, end_graph
from torch._C import _cuda_getCurrentRawStream as get_raw_stream

aten = torch.ops.aten
inductor_ops = torch.ops.inductor
_quantized = torch.ops._quantized
assert_size_stride = torch._C._dynamo.guards.assert_size_stride
assert_alignment = torch._C._dynamo.guards.assert_alignment
empty_strided_cpu = torch._C._dynamo.guards._empty_strided_cpu
empty_strided_cpu_pinned = torch._C._dynamo.guards._empty_strided_cpu_pinned
empty_strided_cuda = torch._C._dynamo.guards._empty_strided_cuda
empty_strided_xpu = torch._C._dynamo.guards._empty_strided_xpu
empty_strided_mtia = torch._C._dynamo.guards._empty_strided_mtia
reinterpret_tensor = torch._C._dynamo.guards._reinterpret_tensor
alloc_from_pool = torch.ops.inductor._alloc_from_pool
async_compile = AsyncCompile()
empty_strided_p2p = torch._C._distributed_c10d._SymmetricMemory.empty_strided_p2p


# kernel path: /tmp/torchinductor_ubuntu/2c/c2cugunifnljeq3sixyodxhraarc2jeb4gtjh7fhm62y7qijgdog.py
# Topologically Sorted Source Nodes: [float_1, silu, float_2, mul, abs_1, amax], Original ATen: [aten._to_copy, aten.silu, aten.mul, aten.abs, aten.amax]
# Source node to ATen node mapping:
#   abs_1 => abs_1
#   amax => amax
#   float_1 => convert_element_type
#   float_2 => convert_element_type_1
#   mul => mul_1
#   silu => mul, sigmoid
# Graph fragment:
#   %arg0_1 : Tensor "bf16[1, 12288][12288, 1]cuda:0" = PlaceHolder[target=arg0_1]
#   %arg1_1 : Tensor "bf16[1, 12288][12288, 1]cuda:0" = PlaceHolder[target=arg1_1]
#   %convert_element_type : Tensor "f32[1, 12288][12288, 1]cuda:0"[num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%arg0_1, torch.float32), kwargs = {})
#   %sigmoid : Tensor "f32[1, 12288][12288, 1]cuda:0"[num_users=1] = call_function[target=torch.ops.aten.sigmoid.default](args = (%convert_element_type,), kwargs = {})
#   %mul : Tensor "f32[1, 12288][12288, 1]cuda:0"[num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type, %sigmoid), kwargs = {})
#   %convert_element_type_1 : Tensor "f32[1, 12288][12288, 1]cuda:0"[num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%arg1_1, torch.float32), kwargs = {})
#   %mul_1 : Tensor "f32[1, 12288][12288, 1]cuda:0"[num_users=2] = call_function[target=torch.ops.aten.mul.Tensor](args = (%mul, %convert_element_type_1), kwargs = {})
#   %abs_1 : Tensor "f32[1, 12288][12288, 1]cuda:0"[num_users=1] = call_function[target=torch.ops.aten.abs.default](args = (%mul_1,), kwargs = {})
#   %amax : Tensor "f32[1, 1][1, 1]cuda:0"[num_users=1] = call_function[target=torch.ops.aten.amax.default](args = (%abs_1, [-1], True), kwargs = {})
#   return %buf1
triton_red_fused__to_copy_abs_amax_mul_silu_0 = async_compile.triton('triton_red_fused__to_copy_abs_amax_mul_silu_0', '''
import triton
import triton.language as tl

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.reduction(
    size_hints={'x': 2, 'r0_': 8192},
    reduction_hint=ReductionHint.INNER,
    filename=__file__,
    triton_meta={'signature': {'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'out_ptr0': '*fp32', 'xnumel': 'i32', 'r0_numel': 'i32', 'XBLOCK': 'constexpr', 'R0_BLOCK': 'constexpr'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=188, cc=120, major=12, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, max_threads_per_block=1024, warp_size=32), 'constants': {}, 'native_matmul': False, 'configs': [{(0,): [['tt.divisibility', 16]], (1,): [['tt.divisibility', 16]], (2,): [['tt.divisibility', 16]], (4,): [['tt.divisibility', 16]]}], 'enable_fp_fusion': False},
    inductor_meta={'grid_type': 'Grid1D', 'autotune_hints': set(), 'kernel_name': 'triton_red_fused__to_copy_abs_amax_mul_silu_0', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': False, 'atomic_add_found': False, 'num_load': 2, 'num_store': 1, 'num_reduction': 1, 'backend_hash': '92025B7F7887B63B7E2E081949457B6F5D4FE41E179BB00C0C96468C7AE5D1D0', 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False, 'deterministic': False, 'force_filter_reduction_configs': False, 'are_deterministic_algorithms_enabled': False, 'tiling_scores': {'x': 4, 'r0_': 49152}}
)
@triton.jit
def triton_red_fused__to_copy_abs_amax_mul_silu_0(in_ptr0, in_ptr1, out_ptr0, xnumel, r0_numel, XBLOCK : tl.constexpr, R0_BLOCK : tl.constexpr):
    xnumel = 2
    r0_numel = 6144
    rnumel = r0_numel
    RBLOCK: tl.constexpr = R0_BLOCK
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:, None]
    xmask = xindex < xnumel
    r0_base = tl.arange(0, R0_BLOCK)[None, :]
    rbase = r0_base
    x0 = xindex
    _tmp13 = tl.full([XBLOCK, R0_BLOCK], float("-inf"), tl.float32)
    for r0_offset in range(0, r0_numel, R0_BLOCK):
        r0_index = r0_offset + r0_base
        r0_mask = r0_index < r0_numel
        roffset = r0_offset
        rindex = r0_index
        r0_1 = r0_index
        tmp0 = tl.load(in_ptr0 + (r0_1 + 6144*x0), r0_mask & xmask, eviction_policy='evict_first', other=0.0).to(tl.float32)
        tmp6 = tl.load(in_ptr1 + (r0_1 + 6144*x0), r0_mask & xmask, eviction_policy='evict_first', other=0.0).to(tl.float32)
        tmp1 = tmp0.to(tl.bfloat16)
        tmp2 = tmp1.to(tl.float32)
        tmp3 = tmp2.to(tl.float32)
        tmp4 = tl.sigmoid(tmp3)
        tmp5 = tmp3 * tmp4
        tmp7 = tmp6.to(tl.bfloat16)
        tmp8 = tmp7.to(tl.float32)
        tmp9 = tmp8.to(tl.float32)
        tmp10 = tmp5 * tmp9
        tmp11 = tl_math.abs(tmp10)
        tmp12 = tl.broadcast_to(tmp11, [XBLOCK, R0_BLOCK])
        tmp14 = triton_helpers.maximum(_tmp13, tmp12)
        _tmp13 = tl.where(r0_mask & xmask, tmp14, _tmp13)
    tmp13 = triton_helpers.max2(_tmp13, 1)[:, None]
    tl.store(out_ptr0 + (x0), tmp13, xmask)
''', device_str='cuda')


# kernel path: /tmp/torchinductor_ubuntu/wh/cwhslrj5pf24r6ddk6ubdau7gfxag6r26h26esapka2czdcwb76t.py
# Topologically Sorted Source Nodes: [float_1, silu, float_2, mul, abs_1, amax, div, s], Original ATen: [aten._to_copy, aten.silu, aten.mul, aten.abs, aten.amax, aten.div, aten.clamp_min]
# Source node to ATen node mapping:
#   abs_1 => abs_1
#   amax => amax
#   div => div
#   float_1 => convert_element_type
#   float_2 => convert_element_type_1
#   mul => mul_1
#   s => clamp_min
#   silu => mul, sigmoid
# Graph fragment:
#   %buf1 : Tensor "f32[1, 1, 2][2, 2, 1]cuda:0" = PlaceHolder[target=buf1]
#   %amax : Tensor "f32[1, 1][1, 1]cuda:0" = PlaceHolder[target=amax]
#   %convert_element_type : Tensor "f32[1, 12288][12288, 1]cuda:0"[num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%arg0_1, torch.float32), kwargs = {})
#   %sigmoid : Tensor "f32[1, 12288][12288, 1]cuda:0"[num_users=1] = call_function[target=torch.ops.aten.sigmoid.default](args = (%convert_element_type,), kwargs = {})
#   %mul : Tensor "f32[1, 12288][12288, 1]cuda:0"[num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type, %sigmoid), kwargs = {})
#   %convert_element_type_1 : Tensor "f32[1, 12288][12288, 1]cuda:0"[num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%arg1_1, torch.float32), kwargs = {})
#   %mul_1 : Tensor "f32[1, 12288][12288, 1]cuda:0"[num_users=2] = call_function[target=torch.ops.aten.mul.Tensor](args = (%mul, %convert_element_type_1), kwargs = {})
#   %abs_1 : Tensor "f32[1, 12288][12288, 1]cuda:0"[num_users=1] = call_function[target=torch.ops.aten.abs.default](args = (%mul_1,), kwargs = {})
#   %amax : Tensor "f32[1, 1][1, 1]cuda:0"[num_users=1] = call_function[target=torch.ops.aten.amax.default](args = (%abs_1, [-1], True), kwargs = {})
#   %div : Tensor "f32[1, 1][1, 1]cuda:0"[num_users=1] = call_function[target=torch.ops.aten.div.Tensor](args = (%amax, 448.0), kwargs = {})
#   %clamp_min : Tensor "f32[1, 1][1, 1]cuda:0"[num_users=2] = call_function[target=torch.ops.aten.clamp_min.default](args = (%div, 1e-08), kwargs = {})
#   return %amax,%clamp_min
triton_per_fused__to_copy_abs_amax_clamp_min_div_mul_silu_1 = async_compile.triton('triton_per_fused__to_copy_abs_amax_clamp_min_div_mul_silu_1', '''
import triton
import triton.language as tl

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.persistent_reduction(
    size_hints={'x': 1, 'r0_': 2},
    reduction_hint=ReductionHint.INNER,
    filename=__file__,
    triton_meta={'signature': {'in_out_ptr0': '*fp32', 'in_ptr0': '*fp32', 'xnumel': 'constexpr', 'r0_numel': 'i32', 'XBLOCK': 'constexpr'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=188, cc=120, major=12, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, max_threads_per_block=1024, warp_size=32), 'constants': {'xnumel': 1}, 'native_matmul': False, 'configs': [{(0,): [['tt.divisibility', 16]], (1,): [['tt.divisibility', 16]]}], 'enable_fp_fusion': False},
    inductor_meta={'grid_type': 'Grid1D', 'autotune_hints': set(), 'kernel_name': 'triton_per_fused__to_copy_abs_amax_clamp_min_div_mul_silu_1', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': None, 'atomic_add_found': False, 'num_load': 1, 'num_store': 1, 'num_reduction': 1, 'backend_hash': '92025B7F7887B63B7E2E081949457B6F5D4FE41E179BB00C0C96468C7AE5D1D0', 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False, 'deterministic': False, 'force_filter_reduction_configs': False, 'are_deterministic_algorithms_enabled': False, 'tiling_scores': {'r0_': 2}}
)
@triton.jit
def triton_per_fused__to_copy_abs_amax_clamp_min_div_mul_silu_1(in_out_ptr0, in_ptr0, xnumel, r0_numel, XBLOCK : tl.constexpr):
    xnumel = 1
    r0_numel = 2
    R0_BLOCK: tl.constexpr = 2
    rnumel = r0_numel
    RBLOCK: tl.constexpr = R0_BLOCK
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:, None]
    xmask = tl.full([XBLOCK], True, tl.int1)[:, None]
    r0_index = tl.arange(0, R0_BLOCK)[None, :]
    r0_offset = 0
    r0_mask = tl.full([R0_BLOCK], True, tl.int1)[None, :]
    roffset = r0_offset
    rindex = r0_index
    r0_0 = r0_index
    tmp0 = tl.load(in_ptr0 + (r0_0), None)
    tmp1 = tl.broadcast_to(tmp0, [XBLOCK, R0_BLOCK])
    tmp3 = triton_helpers.max2(tmp1, 1)[:, None].to(tl.float32)
    tmp4 = 0.002232142857142857
    tmp5 = tmp3 * tmp4
    tmp6 = 1e-08
    tmp7 = triton_helpers.maximum(tmp5, tmp6)
    tl.debug_barrier()
    tl.store(in_out_ptr0 + (tl.full([1, 1], 0, tl.int32).broadcast_to(XBLOCK, 1)), tmp7, None)
''', device_str='cuda')


# kernel path: /tmp/torchinductor_ubuntu/on/conkjbhz3eb2i7oe7z5qahnap5mmvy5rl5mdvxydx5zlc6dgbkfg.py
# Topologically Sorted Source Nodes: [float_1, silu, float_2, mul, truediv, clamp, to_1], Original ATen: [aten._to_copy, aten.silu, aten.mul, aten.div, aten.clamp]
# Source node to ATen node mapping:
#   clamp => clamp_max, clamp_min_1
#   float_1 => convert_element_type
#   float_2 => convert_element_type_1
#   mul => mul_1
#   silu => mul, sigmoid
#   to_1 => convert_element_type_4
#   truediv => div_1
# Graph fragment:
#   %arg0_1 : Tensor "bf16[1, 12288][12288, 1]cuda:0" = PlaceHolder[target=arg0_1]
#   %arg1_1 : Tensor "bf16[1, 12288][12288, 1]cuda:0" = PlaceHolder[target=arg1_1]
#   %clamp_min : Tensor "f32[1, 1][1, 1]cuda:0" = PlaceHolder[target=clamp_min]
#   %convert_element_type : Tensor "f32[1, 12288][12288, 1]cuda:0"[num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%arg0_1, torch.float32), kwargs = {})
#   %sigmoid : Tensor "f32[1, 12288][12288, 1]cuda:0"[num_users=1] = call_function[target=torch.ops.aten.sigmoid.default](args = (%convert_element_type,), kwargs = {})
#   %mul : Tensor "f32[1, 12288][12288, 1]cuda:0"[num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type, %sigmoid), kwargs = {})
#   %convert_element_type_1 : Tensor "f32[1, 12288][12288, 1]cuda:0"[num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%arg1_1, torch.float32), kwargs = {})
#   %mul_1 : Tensor "f32[1, 12288][12288, 1]cuda:0"[num_users=2] = call_function[target=torch.ops.aten.mul.Tensor](args = (%mul, %convert_element_type_1), kwargs = {})
#   %div_1 : Tensor "f32[1, 12288][12288, 1]cuda:0"[num_users=1] = call_function[target=torch.ops.aten.div.Tensor](args = (%mul_1, %clamp_min), kwargs = {})
#   %clamp_min_1 : Tensor "f32[1, 12288][12288, 1]cuda:0"[num_users=1] = call_function[target=torch.ops.aten.clamp_min.default](args = (%div_1, -448), kwargs = {})
#   %clamp_max : Tensor "f32[1, 12288][12288, 1]cuda:0"[num_users=1] = call_function[target=torch.ops.aten.clamp_max.default](args = (%clamp_min_1, 448), kwargs = {})
#   %convert_element_type_4 : Tensor "f8e4m3fn[1, 12288][12288, 1]cuda:0"[num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%clamp_max, torch.float8_e4m3fn), kwargs = {})
#   return %convert_element_type_4
triton_poi_fused__to_copy_clamp_div_mul_silu_2 = async_compile.triton('triton_poi_fused__to_copy_clamp_div_mul_silu_2', '''
import triton
import triton.language as tl

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.pointwise(
    size_hints={'x': 16384}, 
    filename=__file__,
    triton_meta={'signature': {'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'in_ptr2': '*fp32', 'out_ptr0': '*fp8e4nv', 'xnumel': 'i32', 'XBLOCK': 'constexpr'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=188, cc=120, major=12, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, max_threads_per_block=1024, warp_size=32), 'constants': {}, 'native_matmul': False, 'configs': [{(0,): [['tt.divisibility', 16]], (1,): [['tt.divisibility', 16]], (2,): [['tt.divisibility', 16]], (3,): [['tt.divisibility', 16]], (4,): [['tt.divisibility', 16]]}], 'enable_fp_fusion': False},
    inductor_meta={'grid_type': 'Grid1D', 'autotune_hints': set(), 'kernel_name': 'triton_poi_fused__to_copy_clamp_div_mul_silu_2', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': False, 'atomic_add_found': False, 'num_load': 3, 'num_store': 1, 'num_reduction': 0, 'backend_hash': '92025B7F7887B63B7E2E081949457B6F5D4FE41E179BB00C0C96468C7AE5D1D0', 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False, 'deterministic': False, 'force_filter_reduction_configs': False, 'are_deterministic_algorithms_enabled': False, 'tiling_scores': {'x': 73728}},
    min_elem_per_thread=2
)
@triton.jit
def triton_poi_fused__to_copy_clamp_div_mul_silu_2(in_ptr0, in_ptr1, in_ptr2, out_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 12288
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = tl.full([XBLOCK], True, tl.int1)[:]
    x0 = xindex
    tmp0 = tl.load(in_ptr0 + (x0), None).to(tl.float32)
    tmp6 = tl.load(in_ptr1 + (x0), None).to(tl.float32)
    tmp11 = tl.load(in_ptr2 + (0))
    tmp12 = tl.broadcast_to(tmp11, [XBLOCK])
    tmp1 = tmp0.to(tl.bfloat16)
    tmp2 = tmp1.to(tl.float32)
    tmp3 = tmp2.to(tl.float32)
    tmp4 = tl.sigmoid(tmp3)
    tmp5 = tmp3 * tmp4
    tmp7 = tmp6.to(tl.bfloat16)
    tmp8 = tmp7.to(tl.float32)
    tmp9 = tmp8.to(tl.float32)
    tmp10 = tmp5 * tmp9
    tmp13 = (tmp10 / tmp12)
    tmp14 = -448.0
    tmp15 = triton_helpers.maximum(tmp13, tmp14)
    tmp16 = 448.0
    tmp17 = triton_helpers.minimum(tmp15, tmp16)
    tmp18 = tmp17.to(tl.float8e4nv)
    tl.store(out_ptr0 + (x0), tmp18, None)
''', device_str='cuda')


async_compile.wait(globals())
del async_compile

class Runner:
    def __init__(self, partitions):
        self.partitions = partitions

    def recursively_apply_fns(self, fns):
        new_callables = []
        for fn, c in zip(fns, self.partitions):
            new_callables.append(fn(c))
        self.partitions = new_callables

    def call(self, args):
        arg0_1, arg1_1 = args
        args.clear()
        assert_size_stride(arg0_1, (1, 12288), (12288, 1))
        assert_size_stride(arg1_1, (1, 12288), (12288, 1))
        with torch.cuda._DeviceGuard(0):
            torch.cuda.set_device(0)
            buf1 = empty_strided_cuda((1, 1, 2), (2, 2, 1), torch.float32)
            # Topologically Sorted Source Nodes: [float_1, silu, float_2, mul, abs_1, amax], Original ATen: [aten._to_copy, aten.silu, aten.mul, aten.abs, aten.amax]
            stream0 = get_raw_stream(0)
            triton_red_fused__to_copy_abs_amax_mul_silu_0.run(arg0_1, arg1_1, buf1, 2, 6144, stream=stream0)
            buf2 = empty_strided_cuda((1, 1), (1, 1), torch.float32)
            buf3 = buf2; del buf2  # reuse
            # Topologically Sorted Source Nodes: [float_1, silu, float_2, mul, abs_1, amax, div, s], Original ATen: [aten._to_copy, aten.silu, aten.mul, aten.abs, aten.amax, aten.div, aten.clamp_min]
            stream0 = get_raw_stream(0)
            triton_per_fused__to_copy_abs_amax_clamp_min_div_mul_silu_1.run(buf3, buf1, 1, 2, stream=stream0)
            del buf1
            buf4 = empty_strided_cuda((1, 12288), (12288, 1), torch.float8_e4m3fn)
            # Topologically Sorted Source Nodes: [float_1, silu, float_2, mul, truediv, clamp, to_1], Original ATen: [aten._to_copy, aten.silu, aten.mul, aten.div, aten.clamp]
            stream0 = get_raw_stream(0)
            triton_poi_fused__to_copy_clamp_div_mul_silu_2.run(arg0_1, arg1_1, buf3, buf4, 12288, stream=stream0)
            del arg0_1
            del arg1_1
        return (buf4, buf3, )

runner = Runner(partitions=[])
call = runner.call
recursively_apply_fns = runner.recursively_apply_fns


def benchmark_compiled_module(times=10, repeat=10):
    from torch._dynamo.testing import rand_strided
    from torch._inductor.utils import print_performance
    arg0_1 = rand_strided((1, 12288), (12288, 1), device='cuda:0', dtype=torch.bfloat16)
    arg1_1 = rand_strided((1, 12288), (12288, 1), device='cuda:0', dtype=torch.bfloat16)
    fn = lambda: call([arg0_1, arg1_1])
    return print_performance(fn, times=times, repeat=repeat)


if __name__ == "__main__":
    from torch._inductor.wrapper_benchmark import compiled_module_main
    compiled_module_main('None', benchmark_compiled_module)
