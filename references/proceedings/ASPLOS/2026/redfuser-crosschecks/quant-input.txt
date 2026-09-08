import tvm
from tvm import te, topi
from tvm.script import ir as I
from tvm.script import tir as T

from tvm.redfuser import (
    DecomposeReduction,
    UnifyBindOuterLoops,
    TileByAnnotation,
    BlockizeInnerLoops,
    MergeFusedLoops,
    EliminateUnitLoops,
    TransformIOBuffers,
    SetBufferScope,
    HoistTLCopy,
    BindBlockIdx,
    MoveAllocBuffer,
    UnifyGemmDtype,
    GenerateOnlineExpr,
)
from tvm.target.codegen import function_to_tilelang_script
from pathlib import Path
current_dir = Path(__file__).parent


def redfuser_ptpc_gemm(A, W_fp8, W_scale, dtype):
    quant, scale = topi.nn.per_axis_fp8_quant(A, axis=1, reduce_axis_name="k", varargs_names=["m"])
    o_quant = topi.nn.matmul(quant, W_fp8, transpose_b=True, out_dtype="float32", reduce_axis_name="k", varargs_names=["m", "n"])
    o = te.compute(o_quant.shape, lambda *indices: te.multiply(te.multiply(o_quant[indices], scale[indices[:-1]]), W_scale[indices[-1:]]).astype(dtype), name="T_o", varargs_names=["m", "n"])
    return o


@I.ir_module
class Module:
    @T.prim_func
    def redfuser_ptpc_quant_gemm(A: T.Buffer((4096, 4096), "float16"), W_fp8: T.Buffer((4096, 4096), "float8_e4m3fn"), W_scale: T.Buffer((4096,), "float32"), T_o: T.Buffer((4096, 4096), "float16")):
        T.func_attr({"global_symbol": "main", "layout_free_buffers": [1], "tir.noalias": True})
        # with T.block("root"):
        T_max_elem = T.alloc_buffer((4096,))
        T_matmul_NT = T.alloc_buffer((4096, 4096))
        prev_T_max_elem = T.alloc_buffer((4096,))
        input_0_0 = T.alloc_buffer((4096, 4096))
        rescale_factor_1 = T.alloc_buffer((4096,))
        input_1_0 = T.alloc_buffer((4096, 4096), "float8_e4m3fn")
        for m in T.serial(4096, annotations={"bind": "vblockIdx.1", "name": "m"}):
            for k in T.serial(4096, annotations={"name": "k", "tag": "fused"}):
                with T.block("reduction0"):
                    v_m, v_k = T.axis.remap("SR", [m, k])
                    T.reads(A[v_m, v_k])
                    T.writes(T_max_elem[v_m], prev_T_max_elem[v_m], input_0_0[v_m, v_k])
                    with T.init():
                        T_max_elem[v_m] = T.float32(-1000000.0)
                    prev_T_max_elem[v_m] = T_max_elem[v_m]
                    input_0_0[v_m, v_k] = T.Cast("float32", T.fabs(A[v_m, v_k]))
                    T_max_elem[v_m] = T.max(T_max_elem[v_m], input_0_0[v_m, v_k])
        for m in T.serial(4096, annotations={"bind": "vblockIdx.1", "name": "m"}):
            for n in T.serial(4096, annotations={"bind": "vblockIdx.0", "name": "n"}):
                for k in T.serial(4096, annotations={"name": "k", "tag": "fused"}):
                    with T.block("reduction1"):
                        v_m, v_n, v_k = T.axis.remap("SSR", [m, n, k])
                        T.reads(T_max_elem[v_m], prev_T_max_elem[v_m], A[v_m, v_k], W_fp8[v_n, v_k])
                        T.writes(T_matmul_NT[v_m, v_n], rescale_factor_1[v_m], input_1_0[v_m, v_k])
                        with T.init():
                            T_matmul_NT[v_m, v_n] = T.float32(0.0)
                        rescale_factor_1[v_m] = T.pow(T_max_elem[v_m], T.float32(-1.0)) * prev_T_max_elem[v_m]
                        input_1_0[v_m, v_k] = T.Cast("float8_e4m3fn", T.Cast("float32", A[v_m, v_k]) / (T_max_elem[v_m] / T.float32(448.0)))
                        T_matmul_NT[v_m, v_n] = T_matmul_NT[v_m, v_n] * rescale_factor_1[v_m]
                        T_matmul_NT[v_m, v_n] = T_matmul_NT[v_m, v_n] + T.Cast("float32", input_1_0[v_m, v_k]) * T.Cast("float32", W_fp8[v_n, v_k])
        for m in T.serial(4096, annotations={"bind": "vblockIdx.1", "name": "m"}):
            for n in T.serial(4096, annotations={"bind": "vblockIdx.0", "name": "n"}):
                with T.block("epilogue0"):
                    v_m, v_n = T.axis.remap("SS", [m, n])
                    T.reads(T_matmul_NT[v_m, v_n], T_max_elem[v_m], W_scale[v_n])
                    T.writes(T_o[v_m, v_n])
                    T_o[v_m, v_n] = T.Cast("float16", T_matmul_NT[v_m, v_n] * (T_max_elem[v_m] / T.float32(448.0)) * W_scale[v_n])


def main(func_name, tile_map):
    # A = te.placeholder([4096, 4096], "float16", name="A")
    # W_fp8 = te.placeholder([4096, 4096], "float8_e4m3fn", name="W_fp8")
    # W_scale = te.placeholder([4096, ], "float32", name="W_scale")
    # o = redfuser_ptpc_gemm(A, W_fp8, W_scale, dtype="float16")
    # func = te.create_prim_func([A, W_fp8, W_scale, o])

    # mod = tvm.IRModule({func_name: func})
    # mod.show()
    mod = Module
    
    passes = tvm.transform.Sequential([
        # generate online expr
        # GenerateOnlineExpr,
        # tiling
        UnifyBindOuterLoops,
        TileByAnnotation(tile_map),
        # eliminate unit loops and merge fused loops
        EliminateUnitLoops,
        MergeFusedLoops,
        # cache IO buffers and set buffer scope
        TransformIOBuffers,
        SetBufferScope,
        # blockize inner loops
        DecomposeReduction,
        BlockizeInnerLoops,
        # compact alloc_buffer size
        tvm.tir.transform.CompactBufferAllocation(
            is_strict=True, remove_trivial_dims=True
        ),
        # convert to tilelang builtins
        tvm.tir.transform.ConvertToTileLangBuiltins(),
        UnifyGemmDtype,
        HoistTLCopy,
        MoveAllocBuffer,
        BindBlockIdx
        ]
    )

    mod = passes(mod)
    mod.show()

    import_stmt = "import tilelang\nimport tilelang.language as T\n\n"
    tilelang_prog = import_stmt + function_to_tilelang_script(func_name, mod[func_name])
    print(tilelang_prog, file=open(current_dir.joinpath("generated", f"generated_{func_name}.py"), "w"))
    print(f"Generated code saved to {current_dir.joinpath('generated', f'generated_{func_name}.py')}")


if __name__ == "__main__":
    tile_map = {"m": 128, "n": 128, "k": 128}
    main("redfuser_ptpc_quant_gemm", tile_map)
