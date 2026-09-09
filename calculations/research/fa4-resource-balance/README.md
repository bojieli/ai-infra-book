# FA4 单SM资源配比：表1复算候选

以归档官方MLSys论文第2节、3.1.1节公式及表1为来源，绑定PDF、提取文本和官方Qwen3-8B配置SHA。head_dim=128，BF16矩阵吞吐8192 FLOPs/SM/cycle、指数16 results/SM/cycle、SMEM读取128 B/SM/cycle采用论文分析输入；最后一项是论文引用微基准采用的输入，不是整卡HBM带宽或本书实测。

| M×N×d | 资源情景 | 矩阵周期 | SMEM周期 | 指数周期 | 三项资源下界 |
|---|---|---:|---:|---:|---:|
| 128×128×128 | 论文基准 | 1024 | 768 | 1024 | 1024 |
| 256×128×128 | 论文基准 | 2048 | 1536 | 2048 | 2048 |
| 128×128×128 | 仅矩阵供给翻倍 | 512 | 768 | 1024 | 1024 |
| 128×128×128 | 矩阵及指数供给翻倍 | 512 | 768 | 512 | 768 |
| 128×128×128 | 三项供给同时翻倍 | 512 | 384 | 512 | 512 |

四种矩形tile×四组供给，共16场景，逐项输出QK、PV矩阵形状/FLOPs、MMA输出分块数、两路SMEM读取、唯一QKV载荷和精确周期分数。QK每个128×128输出分块从SMEM读Q/K；PV的P从TMEM供给，SMEM只计V。扩大M/N可能重复读取相同操作数，不能以QKV唯一字节替换SMEM访问。

固定真实head_dim，不外推到其他head维度；只接受128的正整数倍矩形tile。因果对角块、padding、完整Softmax归约/缩放、TMEM流量、修正、依赖与启动排空不在这三项下界内。结果不返回完整kernel时延或实测速度；矩阵与指数翻倍是供给反事实，不是另一GPU规格。

复现与验证：

```sh
python3 calculations/research/fa4-resource-balance/calculate.py --output calculations/research/fa4-resource-balance/result.json
python3 calculations/research/fa4-resource-balance/check.py
python3 -m unittest discover -s calculations/research/fa4-resource-balance -p 'test_*.py'
```

独立检查不导入候选，枚举宏分块的Q/K/V读取并重建周期及并列瓶颈，183检查通过。3专项测试覆盖非法维度/倍率、瓶颈切换，以及三份来源各自被破坏时的拒绝。详见[result.json](result.json)和[verification.json](verification.json)。

当前为已检查候选，公共CLI、固定结果注册及正文入口尚待接入；不标C21整体完成。三架构完整注意力资源比较及低精度执行的其余要求仍须分别验收。


公共接入已完成：`python3 calculations/calc.py fa4-resource-balance --format md`。源码位于src/infra_calc/topics/fa4_resource_balance.py，正式输入位于configs/fa4-resource-inputs.json、sources/fa4-resource-balance；结果为results/fa4-qwen8-resource-balance.json/md。16场景与原审核候选一致，来源内容hash不变。806tests784通过22跳过，1795产物/22图及正文网页通过；见相邻fa4-resource-integration/acceptance.json。上述候选记录保留历史，C21其他要求继续待验收。
