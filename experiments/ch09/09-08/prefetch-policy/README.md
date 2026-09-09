# 9-8 补测：同一坏页下的预取策略

固定SGLang 0.5.13.post1、Qwen3-8B BF16、1024输入/16输出，把同一个KV文件截短2字节。沿用此前wait_complete原始结果，新增timeout与best_effort两个独立进程、独立存储副本，每策略一个真实请求；未改原生后端或恢复算法。

| 策略 | 实际get/Short read | 请求结果 | 请求用时 | 存储复用 |
|---|---|---|---:|---:|
| wait_complete（既有记录） | 各1次 | 60.083秒观察窗口内未完成 | 未测得完成时间 | 未返回 |
| timeout | 各1次 | 输出与参考一致，正常关闭 | 3.247 s | 0 token |
| best_effort | 各1次 | 输出与参考一致，正常关闭 | 1.166 s | 0 token |

三次异常均发生在请求开始后约0.08–0.09秒。新增两条件确实在完成前读到坏页，不是完全跳过读取；随后零缓存命中完成本次请求。timeout保留原生默认等待参数，源码按base=2.0s、每1024token增加0.1s、上限30s决定等待，不能将此阈值当成请求完成时限。

**完成请求不等于修复存储。** 三个副本的截断文件都保持原损坏哈希；异常日志仍来自预取I/O线程。新增两引擎在首请求完成后立即正常关闭，没有测试该线程能否继续服务后续存储读取、故障后容量泄漏或长期可用性。不得把一次成功回退写成整套缓存系统恢复正常。

每策略一次、固定顺序；新运行复用原CUDA13编译缓存，旧wait_complete请求则根本没有完成。因此表内时间只描述这些调用，不作吞吐优劣、加速比、p95或SLO结论。所有原有服务保持运行，其他负载未独占控制。

analyze.py对照三个真实配置，确认仅预取策略参数不同；校验执行源码、同一损坏哈希、实际异常事件、输出token、命中字段与退出状态。wait_complete原始证据保留在../truncated-request，不重复跑也不改旧封存。两个子目录的results/保存引擎日志、调用/生命周期事件及监督记录。

从仓库根目录复核：

```sh
python3 experiments/ch09/09-08/prefetch-policy/analyze.py
python3 experiments/ch09/09-08/prefetch-policy/verify_manifest.py
```

重跑使用完整9-8目录的新副本，保留原storage-v3与consumer轨迹作输入；在timeout或best_effort目录执行`python3 supervise.py`，已存在results/storage则拒绝覆盖。安装见父实验ENVIRONMENT.md。监督器只在需要时清理本次Popen独立进程组；新增两次父进程退出码均0，清理后无成员。

原请求故障、缺页与后端边界分别见[截断请求](../truncated-request/README.md)、[缺页重算](../missing-pages/README.md)、[文件后端契约](../storage-contract/README.md)。其他故障、连续请求可用性、容量与预取收益扫描、Agent轨迹、V4状态、保存策略与远端比较继续保留，9-8仍partial。calculations未修改或执行，最终跨session复核未开始。
