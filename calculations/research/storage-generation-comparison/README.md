# 实验4-3：容量与带宽代际对照候选

固定官方Qwen3-8B／235B配置，调用公共逐张量存储适配器；五个硬件规格通过公共来源校验。54工作负载覆盖B1/8/32、最终保留8K/32K位置、16/8/4-bit声明格式及MoE两种路由；810行分别只替换H100基准容量、只替换带宽和使用所选产品的两项规格。

下面只展示4-bit、B8、8K保留位置的产品组合；完整逐张量和所有反事实对照见[result.json](result.json)。GB均为十进制；时间只是所计接口载荷按峰值带宽服务的条件预算。

| 工作负载 | 常驻权重 GB | 本步已计载荷 GB |
|---|---:|---:|
| qwen3-8b-b8-h8191-w4-balanced | 6.071347 | 14.491609 |
| qwen3-235b-a22b-b8-h8191-w4-balanced | 123.142036 | 75.967159 |
| qwen3-235b-a22b-b8-h8191-w4-concentrated | 123.142036 | 24.737406 |

| 工作负载 | 硬件 | 容量条件通过 | 载荷服务预算 ms |
|---|---|---|---:|
| qwen3-8b-b8-h8191-w4-balanced | a100-80gb-sxm | 是（有条件） | 7.107214 |
| qwen3-8b-b8-h8191-w4-balanced | h100-sxm | 是（有条件） | 4.325853 |
| qwen3-8b-b8-h8191-w4-balanced | h200-sxm | 是（有条件） | 3.019085 |
| qwen3-8b-b8-h8191-w4-balanced | b200-sxm | 是（有条件） | 1.811451 |
| qwen3-8b-b8-h8191-w4-balanced | m2-max-38gpu-96gb | 是（有条件） | 36.229023 |
| qwen3-235b-a22b-b8-h8191-w4-balanced | a100-80gb-sxm | 否 | 37.257067 |
| qwen3-235b-a22b-b8-h8191-w4-balanced | h100-sxm | 否 | 22.676764 |
| qwen3-235b-a22b-b8-h8191-w4-balanced | h200-sxm | 是（有条件） | 15.826492 |
| qwen3-235b-a22b-b8-h8191-w4-balanced | b200-sxm | 是（有条件） | 9.495895 |
| qwen3-235b-a22b-b8-h8191-w4-balanced | m2-max-38gpu-96gb | 否 | 189.917898 |
| qwen3-235b-a22b-b8-h8191-w4-concentrated | a100-80gb-sxm | 否 | 12.132127 |
| qwen3-235b-a22b-b8-h8191-w4-concentrated | h100-sxm | 否 | 7.384300 |
| qwen3-235b-a22b-b8-h8191-w4-concentrated | h200-sxm | 是（有条件） | 5.153626 |
| qwen3-235b-a22b-b8-h8191-w4-concentrated | b200-sxm | 是（有条件） | 3.092176 |
| qwen3-235b-a22b-b8-h8191-w4-concentrated | m2-max-38gpu-96gb | 否 | 61.843515 |

容量失败时仍展示算术服务预算，但结果中的capacity_qualified_payload_service_seconds为null，不能解释为该设备能运行此模型。全专家常驻；每步只读被选中专家。当前embedding按批内不同token ID读B行，LM head读全矩阵。先前KV读、当前KV操作数读和追加写分列；内部转发可能避免当前KV的片外读。

低位格式沿用公共capacity-scan的分组scale和逐行尾组，未证明量化质量或真实解量化缓冲。2GiB工作区是声明预留；激活中间态、转换临时访问、缓存命中及完整执行开销没有被计算为零。Apple统一内存仍由CPU/OS共享。

复现：

```sh
python3 calculations/research/storage-generation-comparison/calculate.py --output calculations/research/storage-generation-comparison/result.json
python3 calculations/research/storage-generation-comparison/check.py
python3 -m unittest discover -s calculations/research/storage-generation-comparison -p 'test_*.py'
```

独立check不导入候选或模型适配器，从原始config重建矩阵、参数、低位字节与KV闭式，6384项通过；3专项tests验证一字节容量边界、独立资源替换与非法输入。当前为审核候选，仍待公共CLI、固定场景、结果注册及正文接入，未据此勾选C22。


公共接入现已完成：统一命令`python3 calculations/calc.py storage-generation-comparison --format md`，结果位于results/storage-generation-qwen8-235.json/md。JSON全量等于本审核候选，803项公共tests中781通过22跳过；1793产物/22图及正文网页验证通过。详见相邻storage-generation-integration/acceptance.json；上文候选阶段记录作为历史保留，C22其余要求仍待验收。
