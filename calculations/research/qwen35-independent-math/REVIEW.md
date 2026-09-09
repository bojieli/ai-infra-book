Qwen3.5核心数学独立审查快照

初始主模块SHA：`867aab31852f507fa8b8358984776f9afa7e880570a6022729dcb1b5e4bacc18`。主模块和reference_steps各只读复制一次，计算检查只加载快照，不导入作者正在修改的helper。原件/配置及快照绑定见snapshot-manifest.json。未修改shared或作者目录。

**核心矩阵/Delta递推未发现错误；发现一处record_past接口复制误计。** 作者已消息确认修复该误计，但本报告只对已冻结初始快照负责，修复待最终差异审查验证。

独立数值验证采用普通Python列表/float，不调用作者算子计数或模型payload：实现逐token状态衰减、delta更新和Q读出；另独立实现chunk辅助矩阵、两个unit-lower solve、跨chunk扫描。36例覆盖T=1/2/3/4/5/9，C=2/4/64，零及非零初态；输出与末state最大误差2.7755575615628914e-17。尾块用q/k/v/beta=0及log-decay=0补齐，验证不会改变有效token输出与最终state。该验证证明所选数学关系，不证明PyTorch/GPU三角求解器的执行指令数。

四个完整快照ledger场景：B1/T1/S0，B1/T1/S3，B2/T3/S7，B1/T65/S0。核对结果：

| 项目 | 独立核对结果 |
| --- | --- |
| chunk六个GEMM | 每head/chunk总矩阵FLOPs为6*C*KD*VD+4*C²*KD+2*C²*VD；KD=VD时化为6*C*D²+6*C²*D，与账本一致 |
| 两个unit-lower solve | 共C*(C-1)*(KD+VD)普通乘减；unit diagonal不需要除法，与账本一致 |
| recurrent cached T1 | K读state、outer更新、Q读state按FMA=2共6*B*VH*KD*VD；另state衰减及delta scalar，未重复计矩阵 |
| Q/K头复制 | 16个key heads、64个value heads，Q/K各复制4倍；state按64头，KD/VD各128，未按16头少算state |
| 状态dtype/容量 | 45*B*64*128*128*4字节FP32 recurrent；非record_past conv固定槽45*B*12288*4*2字节，BF16接口与FP32 state分开 |
| router/专家 | router2*M*H*E每层；routed矩阵6*(10M)*H*F每层，与各expert histogram求和相同；各count≤M且总10M可满足每token distinct top10的聚合度约束 |
| shared expert | gate/up/down加独立H→1 gate，每层执行一次；60层都计shared，不以routed active count替代 |
| history边界 | S>0且T1走recurrent，即使record_pastTrue仍如此；T>1有初态走chunk。record_past只改变这里的conv/cache分支，不应强迫切换Delta核心 |

发现F01：初始snapshot的supplement对S0/T2/record_pastTrue仍添加`conv.cache_copy_last4`，每层声称2*12288*4=98304字节copy。固定cache_utils.update_conv_state的record_past分支实际是`self.conv_states[state_idx]=full_conv_states`，没有last4 copy；T2时实际缓存还仅两位置。应仅not record_past计copy，record_past初始长度T已知可明列驻留45*B*12288*T*2字节；已有记录且保留长不明时留null合理。已同时发作者和主线。作者报告已修，但尚未对最终freeze作差异核验。

范围限制：快照明确full_forward_exact=False；此前未闭合mask/norm/gate详细接口不是本报告认可为精确全forward的依据。作者正在补充这些内容，需独立冻结版本后核差异。算子接口及source-statement接口存在重叠，不能相加为HBM流量或峰值内存。源码替换FLA、导出inverse构建分支、路由topk实现比较次数、实际CUDA执行均不在本次纯数学核验范围。

复现：

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=calculations/src python3 calculations/research/qwen35-independent-math/check_math.py
```

结果在results.json。无需PyTorch/NumPy或模型权重。
