import tilelang
import tilelang.language as T

@tilelang.jit(out_idx=[3])
def redfuser_ptpc_quant_gemm():
    @T.prim_func
    def kernel(A: T.Tensor([4096, 4096], "float16"), W_fp8: T.Tensor([4096, 4096], "float8_e4m3fn"), W_scale: T.Tensor([4096], "float32"), o: T.Tensor([4096, 4096], "float16")):
        with T.Kernel(32, 32) as (v_n_o, v_m_o):
            A_1 = T.alloc_fragment([128, 128], "float16")
            W_fp8_1 = T.alloc_shared([128, 128], "float8_e4m3fn")
            W_scale_1 = T.alloc_fragment([128], "float32")
            o_1 = T.alloc_fragment([128, 128], "float16")
            max_elem = T.alloc_fragment([128], "float32")
            matmul_NT = T.alloc_fragment([128, 128], "float32")
            prev_max_elem = T.alloc_fragment([128], "float32")
            input_0_0 = T.alloc_fragment([128, 128], "float32")
            rescale_factor_1 = T.alloc_fragment([128], "float32")
            input_1_0 = T.alloc_fragment([128, 128], "float8_e4m3fn")
            T.fill(max_elem[0:128], -1000000.0)
            T.fill(matmul_NT[0:128, 0:128], 0.0)
            for v_k_o in T.Pipelined(0, 32, num_stages=1):
                T.copy(A[v_m_o * 128:v_m_o * 128 + 128, v_k_o * 128:v_k_o * 128 + 128], A_1[0:128, 0:128])
                T.copy(W_fp8[v_n_o * 128:v_n_o * 128 + 128, v_k_o * 128:v_k_o * 128 + 128], W_fp8_1[0:128, 0:128])
                T.copy(max_elem[0:128], prev_max_elem[0:128])
                for m_1, k_1 in T.Parallel(128, 128):
                    input_0_0[m_1, k_1] = T.Cast("float32", T.abs(A_1[m_1, k_1]))
                T.reduce(input_0_0, max_elem, "max", 1, False)
                for m_1 in T.Parallel(128):
                    rescale_factor_1[m_1] = T.pow(max_elem[m_1], -1.0) * prev_max_elem[m_1]
                for m_1, k_1 in T.Parallel(128, 128):
                    input_1_0[m_1, k_1] = T.Cast("float8_e4m3fn", T.Cast("float32", A_1[m_1, k_1]) / (max_elem[m_1] / 448.0))
                for m_1, n_1 in T.Parallel(128, 128):
                    matmul_NT[m_1, n_1] = matmul_NT[m_1, n_1] * rescale_factor_1[m_1]
                T.gemm(input_1_0, W_fp8_1, matmul_NT, transpose_B=True, policy=1)
            T.copy(W_scale[v_n_o * 128:v_n_o * 128 + 128], W_scale_1[0:128])
            for m_1_1, n_1_1 in T.Parallel(128, 128):
                o_1[m_1_1, n_1_1] = T.Cast("float16", matmul_NT[m_1_1, n_1_1] * (max_elem[m_1_1] / 448.0) * W_scale_1[n_1_1])
            T.copy(o_1[0:128, 0:128], o[v_m_o * 128:v_m_o * 128 + 128, v_n_o * 128:v_n_o * 128 + 128])

    return kernel


