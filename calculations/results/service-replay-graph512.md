# service-replay — 

输入：`{"e2e_limit_ms": 2000, "mean_tpot_limit_ms": 20, "run": "graph512", "ttft_limit_ms": 300}`

请求时间来自封存实际交付；SLO阈值为本次分析输入，仅衡量计时达标。

| 结果 | 值 |
| --- | ---: |
| requests | 18 |
| output_tokens | 2,016 |
| joint_timing_passed | 8 |
| joint_timing_pass_fraction | 0.4444444444444444 |
| ttft_passed | 18 |
| e2e_passed | 8 |
| mean_tpot_passed | 16 |
| summed_observation_window_s | 7.470910331234336 |
| timing_goodput_requests_per_s | 1.0708199731100572 |
| request_throughput_per_s | 2.4093449394976285 |
| output_throughput_tokens_per_s | 269.8466332237344 |
| multi_token_delivery_events | 0 |

| 轮／请求 | 客户端TTFT ms | 客户端E2E ms | 客户端平均TPOT ms | 引擎排队ms | 联合计时达标 |
| --- | ---: | ---: | ---: | ---: | --- |
| 0/r0 | 15.956866089254618 | 1573.2362810522318 | 16.392414894347127 | 0.01946999691426754 | True |
| 0/r1 | 135.65466087311506 | 2032.7516179531813 | 14.937771315591073 | 0.0039101578295230865 | False |
| 0/r2 | 54.96780690737069 | 1558.0607010051608 | 15.822030464187264 | 27.897360967472196 | True |
| 0/r3 | 272.5106708239764 | 2024.7028809972107 | 13.79678905648216 | 0.0044298358261585236 | False |
| 0/r4 | 220.26088694110513 | 1558.5132278501987 | 14.086866746411511 | 148.81298784166574 | True |
| 0/r5 | 186.62121309898794 | 1900.8940630592406 | 13.498211417009863 | 91.35542414151132 | True |
| 1/r0 | 16.214237082749605 | 1572.097142925486 | 16.377714798344595 | 0.021365936845541 | True |
| 1/r1 | 137.97311298549175 | 2118.129031965509 | 15.591778889606436 | 0.004532979801297188 | False |
| 1/r2 | 57.409738190472126 | 1631.747362203896 | 16.57197498961499 | 28.155151987448335 | True |
| 1/r3 | 283.05747895501554 | 2114.6993960719556 | 14.422377300133386 | 0.004712957888841629 | False |
| 1/r4 | 231.51524714194238 | 1635.9913439955562 | 14.783958914248567 | 151.7095249146223 | True |
| 1/r5 | 197.176911868155 | 1990.7838029321283 | 14.122888906015538 | 93.97243615239859 | True |
| 2/r0 | 24.781016167253256 | 2021.4908220805228 | 21.017997956981784 | 0.022453023120760918 | False |
| 2/r1 | 137.31382810510695 | 2513.387155951932 | 18.709238801943506 | 0.007251976057887077 | False |
| 2/r2 | 56.57148198224604 | 2028.0399851035327 | 20.752300032855647 | 28.353240806609392 | False |
| 2/r3 | 282.164819072932 | 2502.358518075198 | 17.48184014962414 | 0.007513910531997681 | False |
| 2/r4 | 231.0151169076562 | 2037.9420958925039 | 19.020283989314187 | 152.11534593254328 | False |
| 2/r5 | 203.77594721503556 | 2378.3390221651644 | 17.12254389724511 | 93.66091503761709 | False |

| 轮 | 实际观测窗秒 | 达标请求 | timing goodput请求/秒 |
| ---: | ---: | ---: | ---: |
| 0 | 2.301564156077802 | 4 | 1.737948511857509 |
| 1 | 2.3908337890170515 | 4 | 1.6730564953427935 |
| 2 | 2.7785123861394823 | 0 | 0.0 |

计量条件：

- 固定实验8-2四配置各三轮六请求，共72请求核对相同输入／运行源码／输出token；本场景选其中18请求。RTX PRO6000、Qwen8 BF16、vLLM0.23，其他服务驻留、配置按固定顺序执行，未跨配置交错，不推断微小优势。
- 客户端TTFT、E2E与平均TPOT均从同一perf_counter基准交付时间计算；TPOT=(末次-首次交付)/(输出数-1)，合并交付事件使单事件间隔不能冒充逐token ITL。引擎队列与TPOT在自己的monotonic基准内相减，不跨时钟相减。
- 联合计时判据为同一请求TTFT、E2E和平均TPOT三者均不超过显式阈值，边界包含等号；单输出请求无后续间隔，平均TPOT判据不适用。平均TPOT达标不保证每个输出间隔达标。
- 每轮观测窗从最早实际提交到最后实际输出，三轮窗口相加，不拼接重置的时间戳，不含轮间休息／引擎启动。goodput=联合达标请求数/窗口总和，不是三轮goodput等权平均，也不是单项通过率相乘。
- 阈值是新增分析输入，结果只是timing goodput。相同输出token不证明答案质量、任务成功率或生产SLO；没有新运行GPU，没有给设备／到达率外推。

固定来源：

- [sources/service-replay/run.py](../../experiments/ch08/08-02/run.py)，SHA256 `9833622b7e16654e4744e83eeb7f11cee488b582586e6117cc878487597ca5f6`。
- [sources/service-replay/results/measured-chunk512/environment.json](../../experiments/ch08/08-02/results/measured-chunk512/environment.json)，SHA256 `f279e9c379086941b4c7c530b8e83270d73736d784f03911104dd9e407d0f442`。
- [sources/service-replay/results/measured-chunk512/requests.json](../../experiments/ch08/08-02/results/measured-chunk512/requests.json)，SHA256 `281218473d145d45f6e4698d650f8ea7b917b8974c5ebd0846af83ecb23f940d`。
- [sources/service-replay/results/measured-chunk512/events.jsonl](../../experiments/ch08/08-02/results/measured-chunk512/events.jsonl)，SHA256 `fcce27e7e7f8f8684c211c07d1a9be39b28688b9565c4d0bdaee905ecd9d67cd`。
- [sources/service-replay/results/measured-chunk8192/environment.json](../../experiments/ch08/08-02/results/measured-chunk8192/environment.json)，SHA256 `ff10c55c422cbb6ec457752e451a5b34da44e0f5da5d84d5bb9b8b5a94339c34`。
- [sources/service-replay/results/measured-chunk8192/requests.json](../../experiments/ch08/08-02/results/measured-chunk8192/requests.json)，SHA256 `281218473d145d45f6e4698d650f8ea7b917b8974c5ebd0846af83ecb23f940d`。
- [sources/service-replay/results/measured-chunk8192/events.jsonl](../../experiments/ch08/08-02/results/measured-chunk8192/events.jsonl)，SHA256 `bc1d2bf8031d23e7a289336cc74714a15f07356379c3cc020fbef3d912083dae`。
- [sources/service-replay/results/measured-nochunk8192/environment.json](../../experiments/ch08/08-02/results/measured-nochunk8192/environment.json)，SHA256 `71365a3bbc3c399f10bfb9359952490f13ae7caf92c90a9809169f94681f51e6`。
- [sources/service-replay/results/measured-nochunk8192/requests.json](../../experiments/ch08/08-02/results/measured-nochunk8192/requests.json)，SHA256 `281218473d145d45f6e4698d650f8ea7b917b8974c5ebd0846af83ecb23f940d`。
- [sources/service-replay/results/measured-nochunk8192/events.jsonl](../../experiments/ch08/08-02/results/measured-nochunk8192/events.jsonl)，SHA256 `323d8224dfe7767db8e8a985f98cad64cc52ad13c0f3334142c0e88273594160`。
- [sources/service-replay/results/measured-graph512/environment.json](../../experiments/ch08/08-02/results/measured-graph512/environment.json)，SHA256 `574bd9a95a42bf4683bb7dbfac82d109c55ae22ff5f216dae60704cbf8ceac7d`。
- [sources/service-replay/results/measured-graph512/requests.json](../../experiments/ch08/08-02/results/measured-graph512/requests.json)，SHA256 `281218473d145d45f6e4698d650f8ea7b917b8974c5ebd0846af83ecb23f940d`。
- [sources/service-replay/results/measured-graph512/events.jsonl](../../experiments/ch08/08-02/results/measured-graph512/events.jsonl)，SHA256 `b3b4af77de597e2533f7b16eccf557f0eec689dad8bf03c4ba2925bdd3ee025d`。
