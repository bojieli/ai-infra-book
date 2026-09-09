# 官方证据与阅读范围

- [vLLM v0.23.0 release身份](https://api.github.com/repos/vllm-project/vllm/git/ref/tags/v0.23.0)：提交0fc695fc6d1d82e9a5ac6835ac8e4e1c83703665。
- [固定SpeculativeConfig](https://github.com/vllm-project/vllm/blob/0fc695fc6d1d82e9a5ac6835ac8e4e1c83703665/vllm/config/speculative.py)：DFlash方法选择、parallel_drafting和非因果attention支持条件。
- [固定DFlashProposer](https://github.com/vllm-project/vllm/blob/0fc695fc6d1d82e9a5ac6835ac8e4e1c83703665/vllm/v1/spec_decode/dflash.py)：bonus加K mask query、目标隐藏状态作为context、被拒token位置处理；本轮重点阅读前180行，不宣称全引擎源码审计。
- [Qwen3 DFlash模型](https://github.com/vllm-project/vllm/blob/0fc695fc6d1d82e9a5ac6835ac8e4e1c83703665/vllm/model_executor/models/qwen3_dflash.py)：归档用于模型架构、载入路径复核。
- [真实接受统计](https://github.com/vllm-project/vllm/blob/0fc695fc6d1d82e9a5ac6835ac8e4e1c83703665/vllm/v1/spec_decode/metrics.py)：num_accepted_tokens不含bonus；1+accepted/drafts仅为引擎平均接受长度约定，不等于最终交付token数量。
- [日志扩展接口](https://github.com/vllm-project/vllm/blob/0fc695fc6d1d82e9a5ac6835ac8e4e1c83703665/vllm/v1/metrics/loggers.py)：StatLoggerBase，SchedulerStats/IterationStats不是稳定API；固定版本读取其实际类型。
- [官方drafter卡片](https://huggingface.co/z-lab/Qwen3-8B-DFlash-b16/blob/9b41424b7109f9c5413454f481b09a82b85333f4/README.md)：绑定Qwen3-8B non-thinking，vLLM推荐method=dflash与FLASH_ATTN，K=15。卡片中的速度仅发布者报告，不采用为本地实测。

API和固定源码均独立下载到本目录；没有从calculations复制任何内容。初始查找中不存在的官方源码/文档路径返回404后，改从已安装源文件定位；不会将404当作方法不支持证据。EAGLE候选目录仅查元数据，未下载、未运行。

Runner补核：[固定VllmConfig](https://github.com/vllm-project/vllm/blob/0fc695fc6d1d82e9a5ac6835ac8e4e1c83703665/vllm/config/vllm.py)第500–542及不支持列表，确认DFlash自动回退V1；[envs](https://github.com/vllm-project/vllm/blob/0fc695fc6d1d82e9a5ac6835ac8e4e1c83703665/vllm/envs.py)确认VLLM_USE_V2_MODEL_RUNNER=0官方开关。AR追加同V1控制，不patch任何共享文件。
