# V4编译产物身份核对与静态PTX计数

在本地experiments/和calculations/的PTX及device_kernel.cu中检索，记录范围及hash见[artifact-search.json](artifact-search.json)。目前没有找到可绑定到官方TileLang fp8_gemm_kernel的同名编译产物。已检查的真实FP8产物是SGLang的_w8a8_block_fp8_matmul；不能据此填入官方TileLang坐标账的缺失字段。

来源是已完成的四层截断V4原生运行探针缓存，Triton3.6.0、PTX8.8、sm_120a、128线程/块。编译缓存存在不单独证明该特化被实际launch或绑定哪个矩阵形状；也不代表完整V4运行或质量验收。

| 静态编译事实 | 数量 |
|---|---:|
| PTX可执行文本位置 | 889 |
| cp.async.cg.shared.global位置 | 36 |
| cp.async.commit_group位置 | 6 |
| cp.async.wait_group位置 | 2 |
| ldmatrix位置 | 24 |
| FP8 mma.sync位置 | 64 |
| 编译metadata shared bytes | 49664 |

PTX有17个pred、537个b32、230个b64虚拟寄存器声明，不能当作实际每线程硬件寄存器数。metadata的num_stages=3、tmem_size=0、tensordesc_meta=[]均按原值保留，不推广为其他内核或设备能力。

[完整结果](result.json)列全部opcode直方图和每条指令的原行号、谓词、操作数。循环/谓词/warp及SASS进一步展开尚未结合，因此不计算动态指令数或把36×16B当作总流量。物理HBM、实际硬件寄存器和官方TileLang指令数保持未知。

复现：`python3 calculations/research/v4-compiled-backend-audit/analyze.py`。独立全文件正则统计与逐行解析直方图一致，889条原行定位和3产物SHA检查通过，见[verification.json](verification.json)。

本审查提供已有后端的编译证据与身份边界。C23仍需匹配目标内核的编译参数/源码revision/产物，以及动态路径或调用绑定；不能拿不同后端的计数关闭目标缺口。
