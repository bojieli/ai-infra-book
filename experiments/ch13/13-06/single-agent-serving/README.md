# 实验 13-6：单 Agent 的持续 serving 成本

已完成离线估算；未新增 GPU 测量，也未实际连续运行 30 天。完整表格在 [RESULTS.md](RESULTS.md)，机器可读结果在 [results.json](results.json)。所有输入已冻结于 sources，来源和 SHA256 见 [manifest.json](manifest.json)。

## 复算

从仓库根目录执行 `python3 experiments/ch13/13-06/single-agent-serving/run.py`。仅依赖 Python 标准库，无需联网或其他未提交的实验目录。脚本校验九份输入哈希、模型参数合计、逐层 KV 大小及容量候选边界，再生成全部结果。

## 定义与公式

一名员工是一条串行 Agent 轨迹，24×7 decode，没有并行子 Agent；工具等待置零。一个月取 30 天。历史在固定长度附近周期压缩或换段，不能无限增长；压缩与重建开销另作敏感性分析。这里只比较供给成本，不假定不同模型能完成相同质量的工作。

设每人速度 r token/s、池小时租价 h、实际持续共享人数 B。每人月输出为 2.592r 百万 token，月租分摊为 720h/B，每百万成本为两者之比。API 按输出及实际计费输入分别乘单价。预留实例中每小时不可重叠开销 t 秒，使产出乘 (3600-t)/3600，单位成本乘其倒数。

## 已有测量如何使用

[sources/batch-summary.json](sources/batch-summary.json) 与 [原实验说明快照](sources/batch-readme.md)来自实验 08-01：Qwen3-8B BF16、vLLM 0.23、RTX PRO 6000 Workstation，设备仍有其他服务驻留。这里选 8K 前缀场景，其中 6144 token 是共享前缀，生成长度为 256，三个重复试验。取记录中的请求平均 token 间隔的中位数，再取倒数；它不是尾延迟保证。另列有限批次总吞吐除以人数得到的含 prefill 成本，两个分母独立核算。

将这些短批次的 decode 间隔外推整月，并按公开 GPU 起租价归一化。未验证出租节点可复现此速度，未验证持续批处理、周期压缩后的稳态，更不能把共享前缀收益推广到无关用户。只有池持续饱和且对称分摊时才能按 B 分账。30 token/s 筛选仅比较已测四个点。

## 价格与模型情景

价格快照日期为 2026-09-09，币种 USD。[Runpod RTX PRO 6000](https://www.runpod.io/gpu-models/rtx-pro-6000) 的 Secure Cloud 起价为 $2.09/GPU·h；用于统一核算，不是对实验主机的实际采购账单。另购存储、网络、控制服务和运维尚未计入。

API 使用 Together 精确端点的每百万输入／输出价格：[Llama 3 8B Lite](https://www.together.ai/models/llama-3-8b-instruct-lite) 为 0.14／0.14，[Llama 3.3 70B Turbo](https://www.together.ai/models/llama-3-3-70b) 为 1.04／1.04，[Qwen3 235B Instruct 2507](https://www.together.ai/models/qwen3-235b-a22b-instruct-2507-fp8) 为 0.20／0.60。20、50、100 token/s 是待满足的单流速度情景，未测服务速度及持续额度。API 模型与本地模型并非相同检查点；不据此判断同质量服务的优劣。输入按完整单价做 1%／16 倍敏感性分析，真实缓存折扣应以账单替换。

容量采用本书三份模型张量核算快照，按总权重与独立 BF16 KV 相加。每张卡按十进制 96 GB 的 80% 可用容量，候选卡数为 1、2、4、8、16、32、64。它是可汇总容量筛选，未验证 TP/EP 切分、逐卡不均匀、互联和速度。4-bit 为每参数 0.5 字节加 5% 元数据的情景，未证明量化质量；128K 仅为容量压力测试，未声明模型均支持该长度。这里独立 KV 不套用测量中的共享前缀。

卸载采用 BF16 单卡、均匀权重驻留／专家访问、有效 H2D 25 GB/s 的条件算例：缺失比例乘每步逻辑活跃权重读取量，得到每步换入量，带宽除以该量得到仅传输速度上限。MoE 仍需保存所有专家。该假设下的成本下限不适用于任意缓存策略；未测 CPU 算专家、实际卸载后端，也未计主机内存价格。
