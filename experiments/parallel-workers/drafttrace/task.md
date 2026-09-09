你是用户授权的独立Codex CLI worker。负责8-5第一轮实跑仍缺少的真实draft/verify/rollback阶段与验证行观测。已有 experiments/ch08/08-05/README.md/PROTOCOL/scripts/raw/75文件manifest已主复核封存；所有旧文件只读，不复跑用于改写原性能结论。

唯一可写 experiments/ch08/08-05/kernel-trace/ 与 experiments/parallel-workers/drafttrace/status.md，远端同名目录。其他正文/总进展/inventory/research/references/实验只读；calculations不执行不修改不复制，不联系其owner；禁止git提交、再派生agent/Codex。先写status，持续更新。

当前GPU已由主agent确认仅原五服务（5875/1953199/1970308/1219611/3614304）；HiCache GPU部分已结束且未残留。你启动前仍需nvidia-smi和/proc重验，不得停止原服务。可使用单个实验GPU进程≤24GiB、CPU≤4线程。root无GPU任务；vision只用CPU，共享资源时间不当隔离性能。不得改任何共享vLLM/SG依赖。

复用同一vLLM0.23环境 /home/ubuntu/vllm023-venv/bin/python、target Qwen3-8B固定缓存、已下载drafter /home/ubuntu/ai-infra-book-experiments/ch08/08-05/weights/Qwen3-8B-DFlash-b16（revision 9b41424b7109f9c5413454f481b09a82b85333f4），禁止重复下载。照原正式AR-V1控制、DFlash K7/K15、相同输入token、greedy/no-thinking/自然stop/128上限/固定KV预算/enforce_eager/APC-off/async-off/FLASH_ATTN等。实际原脚本会写硬编码父ROOT/raw，所以复制成独立runner并改所有写路径，不可执行旧runner覆盖append旧记录。旧启动问题已解决：chat template return_dict=False、VLLM_USE_FLASHINFER_SAMPLER=0、IterationStats正确序列化、AR强制VLLM_USE_V2_MODEL_RUNNER=0。

先读固定已安装DFlash/proposer/model_runner/rejection_sampler源码，固定可观察的真实函数边界。独立插桩只加NVTX/record_function/元数据记录，不改模型或分支；保存原函数源码/hash及wrapper差异。用实际torch profiler或现有Nsight Systems采集热请求的GPU kernel/copy与CPU阶段，不用CPU submit时间冒充GPU阶段。每个完整已知请求/step实际draft tokens、验证input行数/shape、接受长度、拒绝/回退位置或有效KV截断等应来自真实执行元数据，带request ID；聚合字段不可强行分给请求。必要的设备值读回会同步，要明确这是观测批不是原性能批。

有界批：先一个短任务单并发smoke确认输出对原参考精确一致，再同一四输入/两并发的AR-V1/K7/K15各一轮带profile/事件观测；正式性能不重新排名。保留原math质量失败，不能用更快错误答案称成功。任何不支持的阶段边界/回退索引如确实拿不到，写unknown与实际API依据，不编造；但先认真检查源代码，尽可能完成真正的验证/回退链。

真实profiler工具已安装 /home/ubuntu/ai-infra-book-experiments/tools/nsys/extracted/opt/nvidia/nsight-systems-cli/2026.4.1/target-linux-x64/nsys，Torch profiler也可。原始记录本地新增≤1GiB；原始trace大则保留远端hash/必要导出，不丢失败证据。必须等待运行和传输exit后分析，独立数值/token比较、图QA、中文README与未完成范围，主agent统一回填。不得把profile扰动时间当稳定加速结果。只完成本有界缺口，不做最终跨session审计或宣称全8-5完成。
