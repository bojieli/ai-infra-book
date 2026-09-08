# DeepSpeed 与 SuperOffload 的实验入口

用于当前 10.1.2、实验 10-1 的训练卸载案例。这里保存发布文章、固定配置定义和官方示例；没有执行下载的代码或安装依赖，也没有审计完整训练引擎。[推算及取舍](../../../../case-studies/training-offload-and-casting.md)与[论文阅读记录](../../../proceedings/ASPLOS/2026/superoffload-reading.json)分别保存。

| 来源 | 固定范围 | 本轮用途 |
|---|---|---|
| [PyTorch 发布文章](pytorch-superoffload.html) | 2025-10-09，article 文字及图注 | 核对 DeepSpeed 0.18.0 起的发布说明与四种机制；文章图像未作为新的性能读数 |
| [DeepSpeed v0.18.0 配置](offload-config-v0180.py) | `79caae1c04fca210345bdeb03bcacf87b1ac2f23`，2025-10-07 | 全文 115 行；`super_offload`、ratio、CPU 核比例与 ZeRO Stage 3 的范围 |
| [官方示例 README](examples-readme.md) | `931169269a844a44a4c6cb97d9f563b42852d736`，提交时间 2026-08-26 | 全文 111 行；示例模型、配置与 NUMA／MPAM 建议 |
| [Qwen3-14B 启动脚本](finetune_qwen3-14b_1gpu.sh) | 同一示例提交，全文 130 行 | 静态读取生成配置与启动参数，不执行 shell、训练或数据下载 |
| [依赖表](requirements.txt) | 同一示例提交，全文 9 行 | 宽松版本范围不能代替实验锁定版本 |

两份 GitHub commit 响应用于固定身份，不计作机制正文。[sources.json](sources.json)记录七份响应，[readings.json](readings.json)记录五份内容的已读范围；提交时间不等于特性引入时间。

示例的两条分支都采用 ZeRO Stage 3，`superoffload` 额外设置优化器 `ratio=0.90` 和 `cpuadam_cores_perc=0.90`；`zerooffload` 分支省略这些字段。v0.18.0 配置中 ratio 默认 1.0。正式实验需固定运行版本并核对解析后的配置，不能把它当成只改变一个布尔开关的消融。

所选脚本使用 BF16、最大长度 4096、默认 batch 4、activation checkpointing、20 个 warmup steps 与 10 个 bench steps；它没有在启动命令中加入 README 建议的 `--bind_cores_to_rank`。训练入口 `finetune_zero3.py` 和底层 Adam／ZeRO 执行链尚未阅读，脚本中的 token 长度、数据比例和基准步数是否真正如何执行，不能仅凭这些变量宣称已验证。

依赖表允许 `deepspeed>=0.17.0`，而发布文章说明 0.18.0 起提供该功能。实验应锁定确认可用的完整软件组合，再验证硬件与数据。README 的约 500 TFLOPS／高 50% 与发布文章的最高 600 TFLOPS／4 倍不是同一组完整测量条件，本轮均未移入正文比较。
