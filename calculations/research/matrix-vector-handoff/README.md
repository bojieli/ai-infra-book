# 矩阵—向量交接：完整行依赖与有限槽候选

复用公共request_dag调度器，以官方Qwen3-8B head_dim128构造单头128×128完整因果分数矩阵，比较整块和32行分组的QK→Softmax→PV。矩阵使用完整矩形计算（含随后屏蔽的上三角），每组行须先完成全部头维收缩和全部键位置，不能将K方向部分和当作Softmax输入。

| 路径/行组/槽 | 首次向量开工 | 完成时间 | 声明交接容量 bytes |
|---|---:|---:|---:|
| staged-rows128-slots1 | 1536 | 5118 | 98304 |
| staged-rows32-slots1 | 384 | 5120 | 24576 |
| staged-rows32-slots2 | 384 | 3200 | 49152 |
| staged-rows32-slots4 | 384 | 3200 | 98304 |
| direct-rows128-slots1 | 1024 | 4350 | 98304 |
| direct-rows32-slots1 | 256 | 4352 | 24576 |
| direct-rows32-slots2 | 256 | 3008 | 49152 |
| direct-rows32-slots4 | 256 | 3008 | 98304 |

全部时间是教学tick，各类运算率和接口速率均在scenario中显式给出。矩阵服务由QK/PV共用；向量服务按基本算术、比较、指数和除法串行计时；两个方向交接共用同一接口。逐阶段分别向上取整，因此分组的舍入开销可能略大，早开工不自动等于早完成。

每个完整问题跨单元载荷共98304B：FP32分数65536B，加BF16概率32768B。staged路径对此计两次接口服务（写入再读取），共196608B；direct路径只计一次跨单元服务98304B。这里是明确的路径假设，不是已验证的NVIDIA、昇腾或Apple具体实现，也不是HBM量。

槽位含分开的FP32分数和BF16概率预留，从QK开始占用至PV结束；两槽复用依赖显式加入DAG，不能在Softmax开始或概率生成后提前释放。其他累加器、输入、最终输出写回、mask生成/写入、cast、bank冲突与指令开销不在本子账中。

因果屏蔽元素共8128，但本物化执行情景的逐元素Softmax仍覆盖完整矩形；不将有效三角运算量冒充这条执行路径的稠密GEMM量。输出仍保留未知的实测kernel时间和实际指令数。

复现：

```sh
python3 calculations/research/matrix-vector-handoff/calculate.py --output calculations/research/matrix-vector-handoff/result.json
python3 calculations/research/matrix-vector-handoff/check.py
python3 -m unittest discover -s calculations/research/matrix-vector-handoff -p 'test_*.py'
```

独立逐tick模拟不导入候选/公共DAG调度器，重建服务需求并检查370项时序、资源和槽位/载荷守恒；4专项tests检查容量±1B、路径载荷、完整行依赖和非法输入，全部通过。候选待公共CLI、固定场景与正文接入；未将抽象direct路径当作实际厂商专用通路，C23整体不勾选。


公共接入已完成：`python3 calculations/calc.py matrix-vector-handoff --inputs calculations/scenarios/matrix-vector-example.json --format md`。八固定场景及16JSON/MD产物全同候选，16实际CLI输出亦通过核对；817tests795通过22跳过、1827产物/22图和正文网页通过，见相邻matrix-vector-integration/acceptance.json。上述候选记录保留历史，厂商实际路径映射及C23其他要求未据此完成。
