# 8-5 推测解码 worker 状态

阶段：第一轮真实对照及本worker产物QA完成；原题仍部分覆盖，等待主agent统一回填。未做最终跨session审计。

产物：experiments/ch08/08-05/README.md、PROTOCOL.md、scripts/、raw/、evidence/、results/与manifest.json。

已完成：读取原题/extensions/inventory，原8-5无已有实测；官方/已安装vLLM0.23源码hash一致；Qwen3-8B固定缓存revision b968826d9c46dd6066d109eabc6255188de91218；DFlash revision 9b41424b7109f9c5413454f481b09a82b85333f4，2097259104字节权重仅远端下载并核LFS hash。

AR-V1、DFlash K7/K15各8预热+16正式请求，短50/53与长2276/2279输入token，计算/提取两类，c1/c2，两轮；greedy、non-thinking、相同输入/tokenizer/上限。原AR默认V2发现混杂后封存，追加同V1控制，未重复DFlash。

结果：32对DFlash/AR正式输出token完全一致，但严格质量各8/16：短math算对719却违反只输出整数；长math答709；lookup全部正确。全部自然stop，无128上限截断。正式真实accepted/drafted为K7 368/504（72次draft）、K15 376/840（56次draft）；不含bonus。峰值采样AR17706、K7 20894、K15 20814 MiB，低于24GiB。

本worker41项QA通过、图已视觉检查；传输正常退出后分析，远端/本地hash一致。三次完整启动失败封存；所有最终进程exit0，最终GPU恢复初始五个服务/60956MiB，无本worker残留。CPU/GPU共享，计时不称隔离。未修改共享SG/vLLM依赖、未杀任何他人服务、未提交git、未启动agents；正文/inventory/总进展未写。

本地目录约126MiB（含私有分析venv），证据文件约3.5MB，drafter不回传；远端仅本实验目录保留权重/缓存/原始记录。

未覆盖：kernel级草稿/验证/回退分段、真实验证行和回退索引、动态预算/实际图档位、长输出及代码/开放式任务、更高并发、随机采样分布、EAGLE3.1/DFlash2公开记录独立复算、历史草稿变体。calculation内容未执行/复制/联系owner；不以n-gram替代论文方法。
