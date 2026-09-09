# apc-trace — 

输入：`{"run": "cache6"}`

命中与时长来自封存Agent回放；矩阵工作按官方配置复算。

| 结果 | 值 |
| --- | ---: |
| agent_requests | 12 |
| input_tokens | 19,556 |
| cached_tokens | 16,304 |
| requests_with_hit | 11 |
| request_hit_fraction_exact | `"11/12"` |
| token_weighted_hit_fraction_exact | `"4076/4889"` |
| mean_per_request_cached_fraction_exact | `"238696123296413652170375117/332391608212373434606550760"` |
| full_matrix_flops | 284,309,306,474,496 |
| hit_matrix_flops | 48,184,267,112,448 |
| saved_matrix_flops | 236,125,039,362,048 |
| matrix_work_saved_fraction_exact | `"150124257/180758989"` |
| cumulative_reused_kv_logical_bytes | 2,404,122,624 |
| agent_request_wall_s | 0.4402657246682793 |
| pressure_request_wall_s | 0 |
| replay_elapsed_s | 0.44365672394633293 |
| between_requests_s | 0.0033909992780536413 |
| median_delivery_ttft_s | 0.03520110191311687 |
| all_five_run_output_tokens_match | `true` |
| pressure_inputs_match | `true` |

| 轮 | 输入token | 命中token | 剩余矩阵 FLOPs | 省下矩阵 FLOPs | 实测TTFT秒 |
| --- | ---: | ---: | ---: | ---: | ---: |
| agent-0 | 210 | 0 | 2931534528512 | 0 | 0.05742731690406799 |
| agent-1 | 316 | 192 | 1742408646656 | 2678102949888 | 0.040783493081107736 |
| agent-2 | 670 | 304 | 5190785761280 | 4250370834432 | 0.029521348886191845 |
| agent-3 | 884 | 656 | 3272131346432 | 9239951572992 | 0.03666883986443281 |
| agent-4 | 1233 | 880 | 5125032181760 | 12453190041600 | 0.0306921589653939 |
| agent-5 | 1447 | 1216 | 3391673335808 | 17328538386432 | 0.037850657012313604 |
| agent-6 | 1796 | 1440 | 5286479396864 | 20615764377600 | 0.03373336396180093 |
| agent-7 | 2010 | 1792 | 3274097229824 | 25841199218688 | 0.03351433691568673 |
| agent-8 | 2359 | 2000 | 5449913729024 | 28963307520000 | 0.029815166955813766 |
| agent-9 | 2573 | 2352 | 3392328630272 | 34305008467968 | 0.03825478604994714 |
| agent-10 | 2922 | 2560 | 5615335178240 | 37495819468800 | 0.03864116291515529 |
| agent-11 | 3136 | 2912 | 3512547147776 | 42953786523648 | 0.03321600495837629 |

计量条件：

- 实验8-4固定12轮真实Agent输入，各轮仅生成一个token，不重跑工具或继续真实多token Agent任务。RTX共享GPU／vLLM0.23.0、Qwen3-8B BF16、eager、分块预算512、每条件单次串行回放。
- 命中数来自引擎记录，核对冻结prompt ID哈希、所有配置输出相同及两组干扰输入相同。请求命中率指cached>0的请求占比；token加权命中与每请求缓存比例平均分列。
- 矩阵工作为官方full前向减history=cached的suffix前向，保留suffix对命中历史的注意力与末token logits；数学工作不包括chunk额外启动、实际HBM和查找成本。命中工作节省不直接转换为实测加速。
- 累计复用KV逻辑字节按每轮相加，不是缓存驻留峰值或唯一物理页数。同一历史可能多轮重复命中，缺少块寿命记录不能推出容量占用时间。
- Agent请求墙钟、干扰请求墙钟和整段回放时间分开；between_requests含显式间隔与主机开销，不能把整段时间都归因于Agent推理。
- 6GiB与1GiB干扰条件、0.2秒间隔及关闭APC分别对照；单次共享GPU回放不证明通用TTL、显著性能收益或混合排队效果。

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
- [sources/apc-traces/cache6.log](../../experiments/ch08/08-04/cache6.log)，SHA256 `0b56b597f59325f4cb502b124cd8ea7d6e9f073e7b563d7b68d0eb08d05cb9da`。
- [sources/apc-traces/gap6.log](../../experiments/ch08/08-04/gap6.log)，SHA256 `510faaaa6b8c0889a212795c4da3c8c3039ded76fe1f1e1d3d786c315b8df121`。
- [sources/apc-traces/inputs/agent-prompts.json](../../experiments/ch08/08-04/inputs/agent-prompts.json)，SHA256 `6819e3779cc050416e0c8dd29f10b8f6c6a38b01670141139e20619011f3f4d5`。
- [sources/apc-traces/nocache6.log](../../experiments/ch08/08-04/nocache6.log)，SHA256 `77627070d168e4cdb5c3c679298733e64a80b5ebb65cec29ac7f7bfae6e80dc1`。
- [sources/apc-traces/pressure1.log](../../experiments/ch08/08-04/pressure1.log)，SHA256 `a7da0fe14e98623d016c633fac25b545edeb0a9ee87b4335e091bf51dda98775`。
- [sources/apc-traces/pressure6.log](../../experiments/ch08/08-04/pressure6.log)，SHA256 `09a181aa4c58f8856542b0f4c327c31b1f8b91e47fa7fb21570bf185bdd9a693`。
- [sources/apc-traces/results/cache6/environment.json](../../experiments/ch08/08-04/results/cache6/environment.json)，SHA256 `4cc0b306ac4e24891216500da814d75701b7fd3f5974f1551a80f2428a53ef47`。
- [sources/apc-traces/results/cache6/requests.jsonl](../../experiments/ch08/08-04/results/cache6/requests.jsonl)，SHA256 `fa0afa473c892ee8a7d12e8e4bd3a7218e86c7e2aaeed27b6a4103bf59f6aa16`。
- [sources/apc-traces/results/gap6/environment.json](../../experiments/ch08/08-04/results/gap6/environment.json)，SHA256 `6f6315d0f03978f00e936c84a5991480291883245d46441f13a21d486dce622c`。
- [sources/apc-traces/results/gap6/requests.jsonl](../../experiments/ch08/08-04/results/gap6/requests.jsonl)，SHA256 `6cf0c6c0b7ddda31a619e01ba23c7485c4e04a4fa19837b56636ef9d133a0cd4`。
- [sources/apc-traces/results/nocache6/environment.json](../../experiments/ch08/08-04/results/nocache6/environment.json)，SHA256 `f291a908d5fb096b86419f5a8671196c2cdaa5547835ec78fac9e20fbf3ecefa`。
- [sources/apc-traces/results/nocache6/requests.jsonl](../../experiments/ch08/08-04/results/nocache6/requests.jsonl)，SHA256 `d8d64f7077ffaba23d8a074850dc7235d6574283bacdf14b958ddb3261119874`。
- [sources/apc-traces/results/pressure1/environment.json](../../experiments/ch08/08-04/results/pressure1/environment.json)，SHA256 `72dcfb6f7ae0256f08d2fc03f0d5128aca7c7cc3b73f18970d2b619c26701fdc`。
- [sources/apc-traces/results/pressure1/requests.jsonl](../../experiments/ch08/08-04/results/pressure1/requests.jsonl)，SHA256 `86bec5bdf01aa905ebb888a7cd8bfa4b448d3c78423cf979d5cfd667723214dc`。
- [sources/apc-traces/results/pressure6/environment.json](../../experiments/ch08/08-04/results/pressure6/environment.json)，SHA256 `a71f489b2dd2d2fab55afbe0562a4794ffc7f21ee1dd3663ccd15c394087f65f`。
- [sources/apc-traces/results/pressure6/requests.jsonl](../../experiments/ch08/08-04/results/pressure6/requests.jsonl)，SHA256 `32eaa7223a3aa360474f43348cf458a8c68e5e9043a36e54479974cdb9f0019e`。
- [sources/apc-traces/run.py](../../experiments/ch08/08-04/run.py)，SHA256 `200b1eddf801b24227ddb1579b949c29ebd63963d9423e36f13b63be7ef9ba7d`。
