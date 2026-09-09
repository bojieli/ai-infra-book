# F02 最终有限输入验收

**可勾选F02：原11类模型及用户新增6类的必要官方配置、选定模型实现与辅助来源均已有固定、可核验输入。** 本次不把来源验收扩大成完整forward/runtime支持，也不要求下载全部权重才能完成来源输入准备。

正式记录为 `../../inventory/f02-source-review.json`，完整绑定498条根来源和48条辅助来源记录；全部逐文件核对SHA256与长度，辅助来源的路径、锁文件哈希及完整记录同样入库存。根来源按model/file排序后对完整记录作canonical哈希，整公共锁哈希仅为获取时快照。

原11项：Qwen3-8B、32B、30B-A3B、235B-A22B、通用70B代表、DeepSeekV3、V4Flash、V4Pro、KimiK3、Qwen3.5、Qwen3VL。新增6项：Qwen3Omni、FishS2Pro、QwenImage2512、FLUX2klein4B、MiniMaxH3、Wan2.2TI2V5B。Qwen3共享实现、FLA、fast-hadamard、FP8格式、图像来源、视觉/音频/视频实现与codec辅助锁一并绑定，没有只看每模型根config。

通用70B明确采用 **DeepSeek官方DeepSeek-R1-Distill-Llama-70B**，固定revision b1c0b44b4369b597ad119a196caf79a9c40e141e。它是基于Llama70B的蒸馏模型，不是Meta Llama3.1-70B-Instruct的同一checkpoint。旧Meta来源仍保留未授权401状态、原身份与原revision，本次不重复尝试gated下载、不绕过授权，也不把公开模型冒充该模型。F02原文只要求70B代表，因此这个公开代表满足该范围。

Qwen3.5的204条必要源均已合入公共锁并带实际获取时间。独立94分片/1038基础文本形状审查证据已绑定；没有再次下载头或权重。

K3仅执行一次当前官方模型API查询：2026-09-09返回的revision与固定 f831ab66814297da540d832a5235f8e904f29d06 **完全相同**。因此本次只存API原件、URL、时间与哈希，未重取config/model或96个头。现有69个A_log的128对96差异仍是同一固定版本的已知来源矛盾，不得伪称官方已纠正，也不能让同revision重复下载无限占用任务。此次允许接受的是必要来源齐备，不是这69个参数的运行兼容性。

后续计算中真正具体的工作仍保留：K3矛盾解决后才能宣称完整checkpoint运行加载；Qwen3.5完整forward及视觉/MTP运行路径；各生成/VL/Omni请求图；需要实际字符串/媒体运行时再补完整tokenizer、processor及安装依赖闭包。以上均不被F02勾选抹去。源锁保证可复核选定输入，不保证每个动态kernel替换、融合、内部数值行为或硬件实测已完成。

70B adapter新增modeling_rope_utils.py已独立从固定URL重取并逐字节核验，revision与选定modeling_llama.py一致。删除这一新增记录可精确恢复先前497条来源列表，48条辅助记录完全未变；库存保留完整旧验收历史。
