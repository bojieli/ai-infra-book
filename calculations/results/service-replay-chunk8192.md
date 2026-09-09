# service-replay — 

输入：`{"e2e_limit_ms": 2000, "mean_tpot_limit_ms": 20, "run": "chunk8192", "ttft_limit_ms": 300}`

请求时间来自封存实际交付；SLO阈值为本次分析输入，仅衡量计时达标。

| 结果 | 值 |
| --- | ---: |
| requests | 18 |
| output_tokens | 2,016 |
| joint_timing_passed | 13 |
| joint_timing_pass_fraction | 0.7222222222222222 |
| ttft_passed | 18 |
| e2e_passed | 13 |
| mean_tpot_passed | 18 |
| summed_observation_window_s | 6.777983905747533 |
| timing_goodput_requests_per_s | 1.9179744568257795 |
| request_throughput_per_s | 2.65565694022031 |
| output_throughput_tokens_per_s | 297.4335773046747 |
| multi_token_delivery_events | 0 |

| 轮／请求 | 客户端TTFT ms | 客户端E2E ms | 客户端平均TPOT ms | 引擎排队ms | 联合计时达标 |
| --- | ---: | ---: | ---: | ---: | --- |
| 0/r0 | 15.605543041601777 | 1698.7367870751768 | 17.717170989827107 | 0.013292999938130379 | True |
| 0/r1 | 105.13302101753652 | 2109.6222740598023 | 15.78337994521469 | 0.0064051710069179535 | False |
| 0/r2 | 46.43140407279134 | 1639.0407120343298 | 16.7643085048583 | 0.008299946784973145 | True |
| 0/r3 | 194.99896187335253 | 2012.4284578487277 | 14.310468472247049 | 0.0047120265662670135 | False |
| 0/r4 | 195.5051440745592 | 1542.565309908241 | 14.179580692986125 | 0.014692079275846481 | True |
| 0/r5 | 114.84755086712539 | 1863.8400880154222 | 13.771594780695251 | 0.007078051567077637 | True |
| 1/r0 | 20.09065984748304 | 1613.4660018142313 | 16.772372020702612 | 0.016283011063933372 | True |
| 1/r1 | 99.7937039937824 | 2045.6694921012968 | 15.321856599271767 | 0.004009110853075981 | False |
| 1/r2 | 39.734800811856985 | 1568.7707290053368 | 16.095115033615578 | 0.0049551017582416534 | True |
| 1/r3 | 191.57475396059453 | 1961.5132671315223 | 13.936523725755336 | 0.004458008334040642 | True |
| 1/r4 | 184.25508681684732 | 1481.0622269287705 | 13.65060147486235 | 0.00813603401184082 | True |
| 1/r5 | 105.77252111397684 | 1813.4962490294129 | 13.446643526893197 | 0.003958120942115784 | True |
| 2/r0 | 15.582934953272343 | 1530.6619238108397 | 15.948199882711235 | 0.01902901567518711 | True |
| 2/r1 | 95.96773819066584 | 2102.1113540045917 | 15.7964064237317 | 0.0044549815356731415 | False |
| 2/r2 | 35.20836099050939 | 1471.6848721727729 | 15.120805380865932 | 0.004896195605397224 | True |
| 2/r3 | 189.28233091719449 | 2048.2670720666647 | 14.637675127161183 | 0.006818212568759918 | False |
| 2/r4 | 184.02251391671598 | 1410.600597038865 | 12.911348243391043 | 0.010013114660978317 | True |
| 2/r5 | 104.42638583481312 | 1899.5984888169914 | 14.135213409308491 | 0.005218898877501488 | True |

| 轮 | 实际观测窗秒 | 达标请求 | timing goodput请求/秒 |
| ---: | ---: | ---: | ---: |
| 0 | 2.2645789780654013 | 4 | 1.7663327438538465 |
| 1 | 2.2138507128693163 | 5 | 2.258508205153375 |
| 2 | 2.299554214812815 | 4 | 1.7394675777738087 |

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
