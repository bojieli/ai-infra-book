# 9-10 启动与积压消退：准备协议

本文件保留运行前设计；后续实际结果见README。首批补实际启动路径，整个 9-10 仍未完成，异构 PD/AF、动态并行与视觉等范围不缩小。

复用 9-8 已验证的 SGLang 0.5.13.post1、Qwen3-8B 固定快照、BF16、HiCacheFile、Triton attention、PyTorch sampling、page16、max_running_requests1、disable_cuda_graph。固定配置原样复制，完整1024token输入、16token参考输出和65个缓存文件哈希已独立保存；不直接修改或写入旧缓存目录。每次完整条件复制到新私有目录，空条件新建空目录。

必须在空闲 GPU 窗口执行。先空／完整各一次整组预热，均不计正式结果，确保两条后端路径都被触发；再三轮随机交错空／完整，共六组正式启动。CUDA13及既有TVM JIT缓存目录固定，保留每组server.log；正式组若发现额外编译/JIT，不能把该组延迟直接归因于KV效应，需保留并进一步控制后补测。预热不清OS页缓存，不称物理冷盘测试。

每组实际启动独立HTTP服务，八个请求计划在launch后的0、0.1…0.7秒到达。客户端记录真实到达，等待health就绪后各自发送；这是明确的客户端启动积压，不冒充引擎启动前接收了HTTP，也不是稳定态到达率扫描。记录launch、首次health成功、每请求到达/发送/完成和最后全部响应。ready以100ms轮询观测，有轮询误差；发送线程竞争及顺序以实际时间保存，不按计划假造顺序。

每个请求input_ids和sampling相同，return_logprob用于取得完整output token IDs；与9-8参考token及text核验。允许取得原生output_ids或output_token_logprobs中的ID，二者都缺时判失败，不退化为只检查HTTP200。所有16token都是强制长度输出，非自然语言任务成功证据。缓存来源字段及原生HiCacheFile get/set观测保留。

server.py在导入sglang.launch_server前安装9-8原样的get/set包装；不改变结果。保存线程安全requests、launch命令/PID、server.log及storage.jsonl。finally只终止本次自建process group并wait回收；不清理原服务。失败目录保留，后续须新输出目录。

准备完成后的待执行验证：API参数/HTTP返回结构、warmup实际覆盖、full首次存储命中与empty初始缺失、全部输出ID、无残留进程、正式日志无额外JIT。分析脚本和结果报告仍待基于实际字段完成；目前不得把脚本存在标成实测。

后续执行说明：64个请求输出及收尾已核验；full首次有效命中未出现，虽有真实成功get仍保留为负结果。日志未见额外编译不代表全部JIT内容相同。首批端口预检TIME_WAIT失败及八个预热请求保存，随后仅修SO_REUSEADDR并新目录重跑。具体时间、源配置一致性及尚未定位的差异见README和policy-review.json。

后续空闲窗口运行（需先复制整个目录至RTX）：

    /home/ubuntu/ai-infra-book-experiments/tools/sglang0513-venv/bin/python run.py --output results

脚本自身设置CUDA_HOME/PATH和TVM_FFI_CACHE_DIR，只影响子进程；端口31410须空闲。默认只读9-8/storage-v3，并逐文件核对cache-manifest。独立搬迁可用--cache与--jit-cache显式指定相同来源；配套输入/参考/配置都在本目录，不导入邻近实验源码。

不计算C52的部署预算或摊销交点。图配置固定，本批不宣称已经比较不同图捕获规格；其余首轮要求和最终跨session复核继续保留。
