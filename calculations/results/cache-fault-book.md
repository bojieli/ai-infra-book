# cache-fault — 

输入：`{"experiment": "9-8 prefetch policy"}`

来自实际坏页请求记录；未完成观测保留null，成功回退不等于修复存储。

| 结果 | 值 |
| --- | ---: |
| policies | 3 |
| completed_requests | 2 |
| censored_requests | 1 |
| original_page_bytes | 2,359,296 |
| truncated_page_bytes | 2,359,294 |
| removed_bf16_elements | 1 |
| all_corrupt_files_reported_unchanged | `true` |

| 策略 | 完成 | 完成秒 | 未完成观测下界秒 | Short read次数 | 异常距请求秒 | 缓存token | 坏页据记录未变 |
| --- | --- | --- | --- | ---: | ---: | --- | --- |
| wait_complete | False | None | 60.08270208002068 | 1 | 0.08250066498294473 | None | True |
| timeout | True | 3.2465150218922645 | None | 1 | 0.08060687105171382 | 0 | True |
| best_effort | True | 1.1655536629259586 | None | 1 | 0.08892123983241618 | 0 | True |

计量条件：

- 导入三个策略独立进程的封存配置、执行源码、生命周期、I/O异常与监督记录；旧wait_complete不重跑。共同原页逐SHA核验，删末2bytes的预期损坏哈希与三个监督记录一致。
- 最终坏文件未改变来自监督器最终SHA记录，未取得三个运行存储目录的实际坏文件；不把记录核对说成再次读取坏文件。成功返回请求不等于存储已修复。
- wait_complete在约60秒观测窗口未返回，完成时间为null，保留未完成观测下界；不能将观察截止当作一次完成或计算速度比。
- timeout和best_effort均在返回前实际发生Short read，零缓存完成同1024输入／16输出；prefill矩阵为完整重算的逻辑工作，不含后续15decode和实际内核计量。
- 每策略一次、固定顺序、新条件复用编译缓存且其他服务存在，不报告吞吐、p95、SLO或性能排名。原生timeout等待阈值不是整个请求完成时限。
- 成功条件随后即关闭，未测试异常线程后续可用性、容量泄漏或长期服务；输出一致不构成任务质量或完整故障恢复证明。

固定来源：

- [sources/cache-fault/wait_complete/run.py](../../experiments/ch09/09-08/truncated-request/run.py)，SHA256 `2af3dfcb02b9e6fad701753c801a6b5485419b9f5fc66c6f5b72e33ec3f272de`。
- [sources/cache-fault/wait_complete/storage_trace.py](../../experiments/ch09/09-08/truncated-request/storage_trace.py)，SHA256 `7f886632f5d95af217c1ce4936749dc5c83520d411282422506f0f4caa48287b`。
- [sources/cache-fault/wait_complete/supervise.py](../../experiments/ch09/09-08/truncated-request/supervise.py)，SHA256 `734c0b9c8935d5ee30b2be63486d3e84f78f66cc9e73f2ead3711e4886f6ea59`。
- [sources/cache-fault/wait_complete/config.json](../../experiments/ch09/09-08/truncated-request/config.json)，SHA256 `b841e4a3aaea95ad5af1bacb287fd2ab7ac4f93b9f939424c3d282d7b3a0fc35`。
- [sources/cache-fault/wait_complete/inputs.json](../../experiments/ch09/09-08/truncated-request/inputs.json)，SHA256 `8dff397f30621ff9eb41f4ec2c726d5e65d57a704312ea7d80c4957dd2a9e364`。
- [sources/cache-fault/wait_complete/launch.sh](../../experiments/ch09/09-08/truncated-request/launch.sh)，SHA256 `14bf26cde10eba81c738080278b9b21543910d2ff3dd51ddfebcefa3e60236e0`。
- [sources/cache-fault/wait_complete/results/supervisor.json](../../experiments/ch09/09-08/truncated-request/results/supervisor.json)，SHA256 `a04e57c8b8cc049e440ae467b939163da4c47096d88da1f5165e80ac6c54225c`。
- [sources/cache-fault/wait_complete/results/lifecycle.jsonl](../../experiments/ch09/09-08/truncated-request/results/lifecycle.jsonl)，SHA256 `3741f7701c9fbf0a9141368138376ca3ba8650f8a642e65c43cc24096b924419`。
- [sources/cache-fault/wait_complete/results/storage.jsonl](../../experiments/ch09/09-08/truncated-request/results/storage.jsonl)，SHA256 `caacadcf9d1e840545678e8f1407782fdb27f468d92800795070f3f91fa275ac`。
- [sources/cache-fault/timeout/run.py](../../experiments/ch09/09-08/prefetch-policy/timeout/run.py)，SHA256 `2af3dfcb02b9e6fad701753c801a6b5485419b9f5fc66c6f5b72e33ec3f272de`。
- [sources/cache-fault/timeout/storage_trace.py](../../experiments/ch09/09-08/prefetch-policy/timeout/storage_trace.py)，SHA256 `7f886632f5d95af217c1ce4936749dc5c83520d411282422506f0f4caa48287b`。
- [sources/cache-fault/timeout/supervise.py](../../experiments/ch09/09-08/prefetch-policy/timeout/supervise.py)，SHA256 `b888026259021c6851f656097920e8db015b7b90a14f0a5f5daf44ac7012d9db`。
- [sources/cache-fault/timeout/config.json](../../experiments/ch09/09-08/prefetch-policy/timeout/config.json)，SHA256 `5c603645b34389ddecc9dc897f28f8a424e32ba291a0c26d6909d6c49a94bbc1`。
- [sources/cache-fault/timeout/inputs.json](../../experiments/ch09/09-08/prefetch-policy/timeout/inputs.json)，SHA256 `8dff397f30621ff9eb41f4ec2c726d5e65d57a704312ea7d80c4957dd2a9e364`。
- [sources/cache-fault/timeout/launch.sh](../../experiments/ch09/09-08/prefetch-policy/timeout/launch.sh)，SHA256 `537a62809379c6bfd2f559a000a6c86dcf9a39a4986845935fed3ab6f7e7d9ac`。
- [sources/cache-fault/timeout/results/supervisor.json](../../experiments/ch09/09-08/prefetch-policy/timeout/results/supervisor.json)，SHA256 `6b26c821122a22a8ceba6ecd976726f67946e3113e65624c528e9dbb915e6a0e`。
- [sources/cache-fault/timeout/results/lifecycle.jsonl](../../experiments/ch09/09-08/prefetch-policy/timeout/results/lifecycle.jsonl)，SHA256 `51723d2283431e4b21c8e5aa481eb0e33ddffe0c5b327fe8939138a55a4539d9`。
- [sources/cache-fault/timeout/results/storage.jsonl](../../experiments/ch09/09-08/prefetch-policy/timeout/results/storage.jsonl)，SHA256 `50822565f102380309ed194a61e14410d9743d6eebd0f15ba9e37301e668e35f`。
- [sources/cache-fault/best_effort/run.py](../../experiments/ch09/09-08/prefetch-policy/best_effort/run.py)，SHA256 `2af3dfcb02b9e6fad701753c801a6b5485419b9f5fc66c6f5b72e33ec3f272de`。
- [sources/cache-fault/best_effort/storage_trace.py](../../experiments/ch09/09-08/prefetch-policy/best_effort/storage_trace.py)，SHA256 `7f886632f5d95af217c1ce4936749dc5c83520d411282422506f0f4caa48287b`。
- [sources/cache-fault/best_effort/supervise.py](../../experiments/ch09/09-08/prefetch-policy/best_effort/supervise.py)，SHA256 `b888026259021c6851f656097920e8db015b7b90a14f0a5f5daf44ac7012d9db`。
- [sources/cache-fault/best_effort/config.json](../../experiments/ch09/09-08/prefetch-policy/best_effort/config.json)，SHA256 `a9af300ff1fc55f35a4613541db7b46b9de0297d68897024f8b969a6af373b43`。
- [sources/cache-fault/best_effort/inputs.json](../../experiments/ch09/09-08/prefetch-policy/best_effort/inputs.json)，SHA256 `8dff397f30621ff9eb41f4ec2c726d5e65d57a704312ea7d80c4957dd2a9e364`。
- [sources/cache-fault/best_effort/launch.sh](../../experiments/ch09/09-08/prefetch-policy/best_effort/launch.sh)，SHA256 `537a62809379c6bfd2f559a000a6c86dcf9a39a4986845935fed3ab6f7e7d9ac`。
- [sources/cache-fault/best_effort/results/supervisor.json](../../experiments/ch09/09-08/prefetch-policy/best_effort/results/supervisor.json)，SHA256 `093d0933556b80e917ca9d3092bda798ba27a816d957c0f6b645e4db60529fd8`。
- [sources/cache-fault/best_effort/results/lifecycle.jsonl](../../experiments/ch09/09-08/prefetch-policy/best_effort/results/lifecycle.jsonl)，SHA256 `4e76d4d45d21ee28b1e5771daba4d01fbaf61e98688e79e6418eef18c40f06c5`。
- [sources/cache-fault/best_effort/results/storage.jsonl](../../experiments/ch09/09-08/prefetch-policy/best_effort/results/storage.jsonl)，SHA256 `846af625cc7ee219802887f4ce0d8f6e498139de04b6ad5804c652597b0262c7`。
- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
