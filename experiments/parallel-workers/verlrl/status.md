# verl RL worker — 最小真实闭环已核验，待主agent统一审核

正式main/control各完成2次官方verl rollout/reward/advantage/FSDP backward/AdamW调用及最后rollout，均exit0，无遗留自身PID。固定verl commit d040717b21af2e23e8e789a3e354cff2394ae2de，vLLM0.24.0/Torch2.11.0cu130，Qwen2.5-0.5B-Instruct真实固定revision；官方核心算法未替代。源码原SHA、精确观测diff、官方锁和NumPy2.3.5唯一显式覆盖及256包依赖检查已交付。

main两步奖励全1、GRPO advantage/梯度全0。细微FP32变化与AdamW weight decay逐项吻合，BF16不变；不计策略学习。独立预登记control两步梯度范数1.618257、0.049961，FP32/BF16均变化，代表梯度/Adam状态/更新公式独立核验通过，真实接收端版本1/2摘要与发送端及随后rollout对应。control最后算术验证2/4，7+8答11、3*4答7；完整负结果保留，不宣称模型质量提高。

新预算已实际执行：自身GPU采样峰值12.906GiB、RSS峰值13.206GiB（含supervisor），CPU12–15/4线程，MemAvailable和启动GPU余量门槛通过；main77.037秒/control74.634秒。未碰原五GPU服务/OpenROAD/共享环境，最后审计原五服务PID仍在，自身PID为空。共享GPU及温缓存时间不作隔离性能结论。

成功运行、CPU导出及传输均退出后完成离线analyze。被成功替代的启动/依赖调试目录及旧Ray日志已在本地和远端清理；封存仅含最后main/control、成功CPU导出、必要复现版本/源码/协议。284文件，本地材料5,687,856字节（不含manifest自身），远端私有环境13,008,007,168字节；均低于预算。

本地与远端verify_manifest均exit0，manifest SHA256：bae6d718853db39c239e82ffc735152eba8f54a836bd2aaf10d31db36cf19a9b。远端另核验模型全部文件、实际patched源码、原uv.lock及源归档SHA，均通过。可用verify_manifest.py复核，无需启动模型。

交付入口：[中文README](../../ch10/10-08/README.md)、[独立核验](../../ch10/10-08/analysis/REPORT.md)、[完整manifest](../../ch10/10-08/manifest.json)、[协议](../../ch10/10-08/PROTOCOL.md)。根目录提供install/run/watchdog/export/analyze/verify_manifest入口，原始配置与used-*快照在各run。

本批仅最小真实循环完成；恢复/抢占/异步/归一化扩展、完整V4和跨session最终论文审计未完成。正文/inventory/PROGRESS由主agent审核回填；calculations未执行/修改/复制，未git提交、未联系owner、未派生worker。
