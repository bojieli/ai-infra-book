# 9-6：用提交关联区分两次专家GEMM

只分析此前成功的完整模型profiler原件，没有重跑模型。全部 **221,648个CUDA kernel** 均通过correlation找到对应Runtime或Driver API提交，双方External id一致。按提交所在CPU线程及时间范围，归入 **9408次互不重叠的vllm::moe_forward调用**，其中共有77568个kernel；另144080个kernel在这些MoE范围之外。

每个MoE调用恰好包含两次`fused_moe_kernel`。已核对两次提交和同一CUDA stream上的执行顺序，结合所存TRITON专家源码，分别对应gate/up投影和down投影。没有按GPU时间是否落进CPU范围来猜归属，因为异步kernel可以在CPU范围结束后执行。

| 已关联的MoE部分 | 记录kernel duration之和 ms |
|---|---:|
| 第一次专家GEMM，9408次 | 353.578 |
| 第二次专家GEMM，9408次 | 203.660 |
| 其余MoE范围内kernel，58752次 | 170.673 |

这里是记录到的kernel duration求和，不是完整调用延迟、独占关键路径或无profiler性能。现已按External id对应的CPU算子细分其余kernel，并核对提交的完整时间范围。最终求和还验证了aten::sum嵌套在_moe_C::moe_sum及同一MoE调用内。单卡没有专家并行网络通信，不能把这些本地算子统一叫网络dispatch/combine。

| 互不重复的kernel归属 | kernel次数 | duration和 ms |
|---|---:|---:|
| aten::mm（作用未再推断） | 10176 | 25.592 |
| _moe_C::topk_softmax | 9408 | 29.257 |
| aten::copy_（作用未再推断） | 768 | 0.959 |
| _C::per_token_group_fp8_quant | 9408 | 17.247 |
| _moe_C::moe_align_block_size | 1536 | 6.322 |
| 第一次专家GEMM | 9408 | 353.578 |
| _C::silu_and_mul_per_block_quant | 9408 | 47.982 |
| 第二次专家GEMM | 9408 | 203.660 |
| 最终moe_sum中的aten::sum | 9408 | 37.074 |
| aten::fill_（作用未再推断） | 8640 | 6.240 |

此表合计77568 kernel，每个仅计一次。排列算子的1536是GPU kernel数，不是CPU算子调用数；一个CPU调用可以发射多个kernel。最终求和是本地专家输出归约，不是跨设备combine。

## 证据和复现

`trace.json.gz`是此前profile目录中GPU worker轨迹的逐字副本，SHA256为`90b5fc4dbfdafb7b8a1f8f7242fe7a8f0fe7293c7f920eb19f35a4883619a24b`。原四题输出和路由一致性已在该实验核验；这里不重复宣称执行了新的质量测试。

`analyze.py`只依赖Python标准库；读取完整gzip JSON，需留足解压和Python对象的主存。`runtime-sources/`保存当时安装源码，TRITON实现中的第一次权重投影、激活/量化、第二次投影和moe_sum顺序是语义依据。`results/scopes.json`保存每次CPU External id、范围、输入维度、kernel数，以及两次GEMM的关联ID、提交/GPU时间、stream和duration；`analysis.json`汇总全部匹配与未归入MoE的数量。新增`kernel-links.jsonl.gz`逐kernel保存对应MoE ID、CPU算子/External id、correlation、stream、提交和GPU时间及归属；最终求和另保存父_moe_C::moe_sum的External id。gzip固定mtime，可逐字节重放。

```sh
python3 analyze.py
python3 analyze.py /tmp/moe-phase-review
```

断言覆盖correlation唯一性、Runtime/Driver覆盖、External id相等、CPU scope互不重叠、提交的完整范围、每scope两次GEMM及同stream执行顺序。分析不会悄悄丢掉未匹配kernel；若任何关联缺失即停止。较早仅查Runtime的分析版本已由覆盖Runtime/Driver的最终脚本替代，没有保留失败分析日志。

下一步仍需解释普通mm/copy/fill的具体作用、实际padding及各输入批次；多设备放置/复制、暴露通信和DBO/TBO仍待。9-6保持部分完成，calculations/C49未动。
