# 实验10-8：真实verl最小训练闭环

本批完成固定小模型的官方verl → vLLM rollout → reward/advantage → FSDP backward/AdamW → CUDA IPC权重交接 → 再次rollout。主任务和独立控制各完成两次官方更新调用；控制的两次更新都有非零梯度、参数与optimizer状态变化，以及接收端版本1/2的实测权重摘要。这里只完成10-8的最小真实闭环，不代表原实验全部扩展或V4完成。

## 结果与科学负结果

| 运行 | 步1/步2梯度范数 | 两步训练正确回答 | 最终验证 | 参数变化解释 |
|---|---|---|---|---|
| main：算术精确奖励、GRPO | 0 / 0 | 各8/8 | 4/4 | advantage全零；FP32变化逐项吻合AdamW weight decay，BF16不变，不算策略学习 |
| control：预登记固定符号奖励、REINFORCE++ | 1.618257 / 0.049961 | 各8/8 | 2/4 | 两步FP32与BF16均变化；非零梯度、Adam状态和更新公式独立核验通过 |

控制奖励对非空回答按题目固定为+1/-1/+1/-1，与正确率无关。最终验证中7+8回答“11”、3*4回答“7”，另外两题正确；这些错误及全量样本原样保留。控制验证的是非零训练和权重流转，不能得出质量提升结论，也不能将官方日志中的reward/acc名称当作正确率。

完整记录见[独立核验报告](analysis/REPORT.md)、[结构化结果](analysis/summary.json)。原始main/control中保存实际token、两种logprob、reward、advantage、代表性参数/梯度/Adam状态和最终验证；tensor-export.json为CPU离线导出，原始.pt同时保留。analyze.py使用Python标准库独立重算奖励、优势与代表参数更新，核对资源、退出和版本消费顺序，不执行训练。

## 版本与实现边界

verl固定commit `d040717b21af2e23e8e789a3e354cff2394ae2de`。Python3.12.13、Torch2.11.0+cu130、vLLM0.24.0、Transformers5.9.0、Ray2.55.1。官方uv.lock保留原样；唯一显式覆盖为NumPy2.3.5，固定官方wheel SHA以满足依赖声明。environment中提供原锁、pyproject、实际freeze及成功依赖检查。共享vLLM0.23和SGLang环境未修改。

模型为真实训练过的Qwen2.5-0.5B-Instruct，revision `7ae557604adf67be50417f59c2c2f167def9a775`，全部模型文件SHA见model-manifest.json；模型和依赖仅留远端。官方来源、单GPU支持和路径见[SOURCE-REVIEW](SOURCE-REVIEW.md)，任务及预登记控制见[PROTOCOL](PROTOCOL.md)。

实际入口是官方main_ppo的use_v1=false路径，仍由官方RayPPOTrainer/FSDPEngine执行核心计算，该保留入口有deprecated警告。单GPU FSDP使用NO_SHARD；本批实跑vLLM，不包含SGLang。私有patch只观测batch、metrics、optimizer前后张量及真实load_weights后的接收模型，并移动IPC地址至私有目录；完整原SHA/修改后SHA/diff见patch。Ray私有Node adapter负责端口及短session，不替代训练算法。主任务无策略梯度时的AdamW衰减也如实记录。

初始embedding BF16 SHA为 `4e96b0df6d274768cbb7e72404011853d23349999b658dc2f4dfb3c431ea223f`，由独立CPU读取原始safetensors复核。控制版本1为 `7fdc2189107e890dd81461c7a256f7c9649f68ef82c37fd2429385ae338eaddf`，版本2为 `620f2f38687f3b4f4224500d6202e29c6ebf0537b9f7ead10d2b93f0a2b0bdff`。发送端与真正接收模型load_weights后的完整embedding摘要一致，并在后续训练/验证batch之前出现。此证据覆盖代表性完整embedding，不声称逐一hash所有模型参数。

## 资源和实际时间

| 运行 | 总wall秒 | 自身GPU采样峰值GiB | 自身RSS采样峰值GiB |
|---|---:|---:|---:|
| main | 77.037 | 12.906 | 13.122 |
| control | 74.634 | 12.906 | 13.206 |

两次均exit0且清理后remaining_pids为空，CPU12–15、4库线程，RSS含supervisor。满足GPU16GiB/RSS24GiB预算、启动GPUfree10GiB和持续MemAvailable16GiB门槛；采样峰值不等同瞬时峰值。watchdog按私有token/PID出生时间只清理本任务进程，未停止原服务或其他任务。完整采样、阈值及退出在各run目录，最后审计见final-cleanup.json。

| 实际阶段（秒） | main步1 | main步2 | control步1 | control步2 |
|---|---:|---:|---:|---:|
| gen | 5.253 | 0.147 | 5.931 | 0.104 |
| old_log_prob | 1.315 | 0.303 | 0.938 | 0.210 |
| adv | 0.00184 | 0.00068 | 0.00194 | 0.00120 |
| update_actor | 4.763 | 4.861 | 4.756 | 4.017 |
| update_weights | 2.563 | 2.197 | 1.903 | 1.828 |

阶段字段来自实际verl metrics。reward实际计算位于agent loop/gen内部，driver的timing_s/reward只是收集阶段，不能当作全部评分耗时。总wall还含启动/初始化/退出及未分配开销；未单独测得纯初始化或JIT时间。观测累计main8.938秒、control8.705秒跨进程可能重叠，不能直接相减构造纯性能。共享GPU、已准备的私有JIT缓存、不reset共享缓存，无冷启动、隔离性能或其他硬件训练结论。两步使用表格即可，不生成趋势图或拟合质量曲线。

## 复现入口

远端根目录为 `/home/ubuntu/ai-infra-book-experiments/experiments/ch10/10-08`，私有环境为同仓库 `tools/verl-private/verl-project-verl-d040717/.venv`。要求Linux、RTX SM120、驱动595.71.05和现有CUDA13私有工具链路径；资源不足时watchdog退出，不自动借更多资源。私有Ray端口6398、16400–16499必须空闲，不能连接已有集群。

已有私有环境直接运行；重建时在远端执行bash install.sh（需要uv），按冻结官方锁安装、固定NumPy wheel覆盖、准备固定模型并施加校验过的观测patch。远端依赖及模型≤25GiB，本地不下载wheel或模型。每次运行须使用新目录名，避免覆盖正式数据：

```bash
cd /home/ubuntu/ai-infra-book-experiments/experiments/ch10/10-08
VERLRL_RUN=repro_main VERLRL_MODE=main bash run.sh
VERLRL_RUN=repro_control VERLRL_MODE=control bash run.sh
export VERLRL_ROOT="$PWD"
export VERLRL_PRIVATE=/home/ubuntu/ai-infra-book-experiments/tools/verl-private
export VERLRL_MAIN_RUN=repro_main VERLRL_CONTROL_RUN=repro_control
python3 watchdog.py --out export-repro --private "$VERLRL_PRIVATE" -- "$VERLRL_PRIVATE/verl-project-verl-d040717/.venv/bin/python" export_evidence.py
# 上述作业及所需数据传输退出后，使用标准库分析：
python3 analyze.py --main-dir repro_main --control-dir repro_control --output analysis_repro
```

封存的main/control内used-*与Hydra配置是实际执行快照；根目录复现脚本增加了可选重跑目录和安装幂等处理，未变更正式训练计算。根协议最后补充说明模板自动加入system和AdamW默认值，实际prompt全文和token均可复核。最终交付只保留正式main/control、成功CPU导出与必要复现材料；manifest.json覆盖文件SHA，manifest自身不递归hash。正文/inventory/PROGRESS由主agent统一审核回填，恢复/抢占/异步/归一化扩展及跨session最终审计仍未完成。
