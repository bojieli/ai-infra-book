# 8-5 第一轮固定协议

原题核对：outlines/08-单实例推理.md 实验8-5、outlines/extensions/08-单实例推理.md 第203–215行、inventory 8-5（pending_measurement，evidence空）；授权目录初始为空。未执行、复制 calculations 内容。

Target：Qwen/Qwen3-8B revision b968826d9c46dd6066d109eabc6255188de91218，直接读取已有缓存；BF16。DFlash：z-lab/Qwen3-8B-DFlash-b16 revision 9b41424b7109f9c5413454f481b09a82b85333f4；仅下载config与权重，合计<2GiB，LFS SHA256验证。引擎 vLLM 0.23.0，官方提交0fc695fc6d1d82e9a5ac6835ac8e4e1c83703665，核对安装源码hash；不patch共享环境。

对照：AR、DFlash K=7、K=15（验证块含bonus，分别8/16）。相同target tokenizer/chat template，enable_thinking=False；temperature=0，seed=42，max_tokens=128，自然EOS不忽略。禁止通过改变输出上限掩盖截断。两类任务：整数运算、文档键值提取；各短/长，长文档约2K token；精确输入token在第一次运行保存，后续严格复用。并发1与2，正式各两轮，每个配置先同形状预热一轮并完整保留。

执行：单GPU实验进程，TP=1，V1多进程关闭，eager禁用CUDA Graph，禁用APC与异步调度，max_model_len=4096，max_num_batched_tokens=512，max_num_seqs=2，显式KV预算1.25GiB；PyTorch分配上限22GiB，NVML每0.5秒观测本进程、24GiB守护上限。启动前至少27GiB可用，否则保存阻断退出；不得杀其他进程。CUDA/Triton/FlashInfer/HF等写缓存重定向至授权远端目录。

记录：加载wall、预热wall、正式每请求提交到首token TTFT与最终输出wall；逐步可见token事件、最终token_ids、finish_reason/stop_reason；官方StatLoggerBase扩展口保存scheduler真实spec_decoding_stats，包括num_drafts、num_draft_tokens、num_accepted_tokens、按位置接受数；并发时仅将其解释为调度轮聚合，不伪造逐请求归因。逐步wall含CPU/同步/起草/验证，不能充当GPU独立kernel时间。GPU全局/进程内存、Torch峰值、退出与清理保存。

质量：跨配置逐请求token完全相等检查；另以预设精确答案判定，不丢弃错误、截断、不同输出。CPU/GPU均共享，所有计时是共享环境局部测量，不能声称隔离速度或普适增益。

仍须明确：本轮没有EAGLE3.1/DFlash2公开记录独立复算、动态预算/实际图档位、kernel级草稿/验证/回退分段或历史草稿变体；不得将阶段性结果标记原题全部完成。不做最终跨session审计。

最终启动配置：Transformers 5 显式 return_dict=False；AR 与 DFlash 均通过官方 VLLM_USE_FLASHINFER_SAMPLER=0 使用原生采样后端。正式 greedy 由 temperature=0 确定，采样目标不变。

对照修订：正式日志显示AR默认Model Runner V2、DFlash因官方支持限制自动选择V1。原AR封存raw/ar-v2，不用作单变量主要对照。追加VLLM_USE_V2_MODEL_RUNNER=0运行AR-V1，使用相同inputs与其他参数；DFlash两组原本即V1，不重复。最终主表采用AR-V1，AR-V2仅保留为额外混杂证据。
