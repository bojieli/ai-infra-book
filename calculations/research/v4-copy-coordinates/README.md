# V4共享专家FP8内核：搬运坐标与地址覆盖候选

从官方Flash配置与kernel.py读取共享专家w1/w3/w2三次实际FP8矩阵调用。默认32个token、单层、world_size1；w1/w3为[32,4096]×[4096,2048]，w2为[32,2048]×[2048,4096]。源码分块32×128×128，输入/权重FP8、缩放E8M0、输出BF16和累加FP32。

| 调用 | grid块数 | K轮次总数 | A搬运 bytes | B搬运 bytes | A scale bytes | B scale bytes | 输出 bytes |
|---|---:|---:|---:|---:|---:|---:|---:|
| shared.w1 | 16 | 512 | 2097152 | 8388608 | 16384 | 512 | 131072 |
| shared.w3 | 16 | 512 | 2097152 | 8388608 | 16384 | 512 | 131072 |
| shared.w2 | 32 | 512 | 2097152 | 8388608 | 16384 | 512 | 262144 |

每个tile记录张量内起点、字节偏移、行数、每行有效字节和stride。区域是跨行的矩形，不能把起始至终止的整个地址跨度算成有效传输量。逐输出块保留全部K轮次，因此N分块会重复读取A，M分块会重复读取B；不同调用之间也不自动抵消读取。

计数的是源级T.copy和scale索引访问。现有源码没有编译PTX/SASS证据，load/store指令数量、整数地址指令、TMA descriptor数量及物理HBM字节均为null。num_stages=4不被解释为已证明四份物理缓冲或真实重叠。

补充接口核对：已归档PTX ISA第5.5.8节称tensor-map为128字节opaque对象，第9.7.9.27节规定global_address/global_stride更新值为b64。这些规格不能证明当前TileLang内核生成了tensor-map或tensormap.replace；本结果不把规范对象大小乘以T.copy调用数来伪造描述符流量。

复现：

```sh
python3 calculations/research/v4-copy-coordinates/calculate.py --output calculations/research/v4-copy-coordinates/result.json
python3 calculations/research/v4-copy-coordinates/check.py
python3 -m unittest discover -s calculations/research/v4-copy-coordinates -p 'test_*.py'
```

独立逐行区间覆盖、重复次数和扁平偏移检查518361项通过；3专项tests覆盖batch增加后的权重重读、跨行区域和尾块拒绝。输入形状限制为M32/N128/K128对齐；不猜测非对齐谓词。完整量化、门控、所有43层及运行时仍由其他工作包计量。

候选待公共CLI/固定场景/正文接入。C23的实际编译地址/描述符/指令和专用矩阵—向量交接仍待证据，不能将本源级坐标审查当作完整后端分析。


公共接入已完成：`python3 calculations/calc.py v4-copy-coordinates --rows 32 --format md`；支持M64固定对照。正式结果为results/v4-copy-coordinates-m32/m64.json/md，四次CLI同候选、四冻结文件同CLI；公共M32/M64独立检查518361/1028473项通过。813tests791通过22跳过、1811产物/22图和正文网页通过，见相邻v4-copy-integration/acceptance.json。上述候选阶段作为历史保留，编译指令/描述符及C23其余范围继续待办。
