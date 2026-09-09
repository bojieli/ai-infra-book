# 实验 10-4：A100／A800／H20 训练公开记录准备

本轮完成了公开来源冻结与离线核验，**尚未完成原题要求的同模型跨硬件训练校准**。没有找到可将 Qwen3-8B 或 Qwen3-235B 在 A100、A800、H20 上按相同精度、batch、序列长度、训练方式和并行布局比较的完整稳态原始训练记录。公开配置、作者汇总、日志截图和可解析原始文本分开保存；没有用推理吞吐、H100 记录或硬件峰值填补训练步时间，也没有生成缺失的时间分解图。

本目录是 10-4 首轮实验的配套记录工作，不是全书论文增补审计。没有访问或执行 calculations；没有改正文、inventory、PROGRESS 或另一 session 的研究；没有启动 GPU、训练或权重下载。

## 原题与本地已有来源

原题 `outlines/extensions/10-训练系统.md` 的实验 10-4 要求：对 Qwen3-8B 与 Qwen3-235B 候选切分，先比较同形态 A100／A800，再以 H20 具体训练步或注明假设的有效性能校准。原有 `case-studies/inference-training-scenarios.md` 已明确 H20 缺少同条件训练测量，并区分计算代理与实测。本轮不重做该计算。

原有 A800 Lenovo 指南、A100 80GB 数据表与 H20 vGPU 支持表继续使用本地原件，不重复下载。`local-read-scope.json` 保存路径与 SHA，以及实际阅读范围；登记文件 SHA 不代表已重读整篇 PDF。

## 找到的记录及使用边界

| 来源 | 硬件与训练对象 | 实际可取得的数据 | 本轮判断 |
|---|---|---|---|
| VisionBraille 作者模型卡与 GitHub | 8×H20；Qwen3-8B 扩展盲文词表；BF16、全参 SFT、ZeRO3、AdamW、长度上限2048 | 各阶段 YAML、DeepSpeed JSON、作者结果模型文件清单 | 配置可追溯，没有逐步时间；词表/任务已变，不能称原始 Qwen3-8B 同条件性能 |
| Qwen 官方 ms-swift 指南 | 16×A800 80GiB；Qwen3-30B-A3B-Base；全参 SFT，TP2、EP8、microbatch1、global16、packing、长度8192、全重计算 | 命令与作者汇总9.6s/it；另列 ZeRO3 为91.2s/it | 实际作者训练汇总，异模型且无逐步日志；表中不同框架配置不应默认完全相同，更不能作为A100/H20配对 |
| ms-swift 3.8 文档 | 8×A800；Qwen2.5-14B；全参8K | Megatron9.04、ZeRO2 10.32、ZeRO3 10.56s/it汇总 | 未公开可对齐的原始步序列及全部 benchmark 参数；只作单硬件软件案例 |
| ms-swift 作者在 Qwen HF discussion25 | 8×H20；Qwen3-235B-A22B-Instruct-2507 | 实际 LoRA 命令、约3.5s/it描述、原始日志与显存截图 | 正文“full-parameter”与命令冲突，按 LoRA 处理；不是全参记录、不是原始文本 trace |
| attn-signs 作者模型卡 | 2×A100；Qwen3-8B；BF16、LoRA、ZeRO3、长度4096、每卡batch1、累积8 | 配置块、约12h描述、模型仓库文件列表 | 无逐步日志；另写“GPU hours 12h”，与2卡12h墙钟解释冲突，不推算稳态步时或GPU总时 |
| 96kevinli29 作者仓库 | Qwen3-8B-Base／A100-40G 配方入口 | Slurm/verl全参脚本、README、完整树 | 配方存在不证明实际完成；内存注释是估计，没有公开记录可解析 |
| Pai-Megatron-Patch 协作者 issue529 | 8×H20；Moonlight-16B-A3B-Instruct；BF16 SFT，TP/PP/CP/ETP1、EP8、global8、长度2048 | 成功首步原始文本一行与命令 | 可解析但仅iteration1：49.4495s，不能作为稳态或Qwen结果 |
| verl fully_async_policy 作者文档 | H20；包括Qwen3-235B | 权重同步汇总58.57/23.70s，trainer64/rollout64；其他RL配置与公开W&B链接 | 这两数是同步阶段，不是训练步；不计入硬件训练吞吐 |
| vime issue160 作者实验报告 | Qwen3-4B；A100及A800训练作业内的权重更新 | update_weights阶段汇总，A10048步均值20.3s／A800约19–21s | 非完整训练步且缺48行raw；不据此归因A100/A800互联差异 |

来源链接：[VisionBraille模型卡](https://huggingface.co/Violet-yo/Vision-Braille-Qwen3-8B)、[作者代码](https://github.com/AlanYWu/VisionBraille)、[Qwen官方训练指南](https://github.com/QwenLM/Qwen3/blob/7a2f61ffc7a20d47efcd2bf97f6f2bf52729042e/docs/source/training/ms_swift.md)、[swift3.8文档](https://swift.readthedocs.io/en/v3.8/Megatron-SWIFT/Quick-start.html)、[Qwen235讨论](https://huggingface.co/Qwen/Qwen3-235B-A22B-Instruct-2507/discussions/25)、[A100作者模型卡](https://huggingface.co/attn-signs/Qwen3-8b-ru/blob/b625de3d88f05040ae15298d5d52439aac7b515a/README.md)、[A100脚本](https://github.com/96kevinli29/base-model-sft-verl)、[H20原始文本](https://github.com/alibaba/Pai-Megatron-Patch/issues/529#issuecomment-2753325466)、[verl作者文档](https://github.com/verl-project/verl/blob/89dad2d7a82dbd0e6740788fd755ecb09613c72f/verl/experimental/fully_async_policy/README.md)、[vime阶段报告](https://github.com/vllm-project/vime/issues/160)。

## 原始记录核验

`analyze.py` 只使用标准库，逐份验证 `sources.json` 的文件大小和 SHA，再从 Pai 协作者 `lostkevin` 的原始 comment ID 2753325466 解析真实文本。该行计划10000步但只公开第1步，global batch8、lm loss4.714077、skipped0、nan0。**不推断剩余9999步已完成**，不计算稳态中位数、MFU、token/s或完成天数。作者另说明历史 Megatron-0314 重计算存在辅助损失重复计数问题；当前主分支固定 SHA 不能冒充这次历史执行版本。

Qwen235 原始 screenshot 已目视阅读，能看见日志显示 iteration1、5、10；末个显示约3.5013s，但它是原生日志的屏幕图像，采样间隔与计时平均窗口没有完整执行源码绑定。本轮不进行OCR造出“原始trace”，不把三个显示点当三条逐步事件。命令明确 rank8/alpha32/all-linear LoRA。3.5s路径是EP8、micro2、global16、max_length2048；另一9.5s路径同时变更PP4/EP2、micro8和CPU optimizer offload，硬件只写8×80GiB，不能擅自标A100或A800。显存截图没有GPU型号栏，H20身份依据作者文字。

VisionBraille阶段1配置每卡batch20、累积2；阶段配置应分别读取，不能将单阶段batch套到全部训练。作者提供的是可复现输入配置和最终模型，不等于完整运行日志。冻结 Git tree 未截断且没有匹配日志、trainer_state或TensorBoard文件；HF文件清单也无训练日志。这里的“未找到”限定为本轮检查的公开路径，不声称作者从未记录或任何地方都不存在。

## 原题仍缺的证据

| 对象 | A100 | A800 | H20 |
|---|---|---|---|
| 固定 Qwen3-8B 全参、同数据/长度/batch/软件布局 | 缺实际稳态raw；有配方 | 本轮未找到合格原始步记录 | 有作者全参配置，缺实际时间raw，且词表已扩展 |
| 固定 Qwen3-235B 全参、同数据/长度/batch/软件布局 | 缺 | 缺 | LoRA截图与RL同步阶段不能填此项 |
| 仅改变同形态A100/A800互联的配对 | 本轮没有合格原始配对 | 本轮没有合格原始配对 | 不以H100替代 |

因此 `analysis/summary.json` 的 `steady_state_step_estimate_s`、`cross_hardware_speedup` 保持 null，`deadline_calibration_eligible=false`。图10-4的计算／通信／暴露等待分解还需要真实 profiler 或阶段事件，完整总步时也不能自动分解成三部分。

## 下一次实际取数要求

1. 先固定 Qwen3-8B 的完整权重／tokenizer／数据 SHA、训练目标（全参SFT或CPT）、精度、优化器、长度与packing语义、每卡microbatch及global有效token数，再把相同执行脚本部署到同形态 A100/A800；记录GPU确切型号、驱动、CUDA、框架commit、NVLink拓扑与跨节点网络。不能用“支持该卡”代替运行记录。
2. H20独立记录原配置的容量可行性。若必须更改切分、重计算、offload或batch，标为另一个配置；先保留相同任务的结果，不将速度差全部归因硬件。235B需要实际多卡/主机内存条件，当前单RTX不具备原多卡实验的替代身份。
3. 记录预先约定的warmup与正式步段、每步起止wall、真实有效token数、loss/梯度有限性、跳步、保存/验证/数据等待，以及阶段profiler；保留完成退出和全部正式步。至少能判断首步编译/初始化与稳态的边界，不能只取最快三步。
4. 这些数据齐全后再作跨硬件比较；本轮不执行计算模型、下载模型或启动新训练。公共W&B入口不等于本轮已下载其history，本轮没有将未取得的数据用图或数字补齐。

## 重放与封存

```sh
python3 experiments/ch10/10-04/analyze.py --out /tmp/ch10-04-author-analysis-new
python3 experiments/ch10/10-04/verify.py
```

`--out` 必须不存在；不覆盖原始JSON。`fetch.py`仅供显式小文件源下载，有8MB单文件上限和已存在文件复用，不下载权重。`sources.json` 保存原始URL、固定commit路径、取得时间、SHA与大小；动态讨论API以本地SHA冻结，不能伪称不可变URL。`manifest.json`覆盖本目录除自身之外的交付文件。仅保留成功取得的证据，没有失败HTTP响应或探测转录；原作者成功首步、截图和科学限制保留。
