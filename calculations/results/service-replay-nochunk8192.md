# service-replay — 

输入：`{"e2e_limit_ms": 2000, "mean_tpot_limit_ms": 20, "run": "nochunk8192", "ttft_limit_ms": 300}`

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
| summed_observation_window_s | 6.926419684896246 |
| timing_goodput_requests_per_s | 1.8768715427896763 |
| request_throughput_per_s | 2.598745213093398 |
| output_throughput_tokens_per_s | 291.0594638664606 |
| multi_token_delivery_events | 0 |

| 轮／请求 | 客户端TTFT ms | 客户端E2E ms | 客户端平均TPOT ms | 引擎排队ms | 联合计时达标 |
| --- | ---: | ---: | ---: | ---: | --- |
| 0/r0 | 15.909706009551883 | 1571.2518668733537 | 16.372022745934757 | 0.020456034690141678 | True |
| 0/r1 | 100.15135700814426 | 2058.6677850224078 | 15.421389196962705 | 0.006201909855008125 | False |
| 0/r2 | 39.16199808008969 | 1524.5409440249205 | 15.63556785205085 | 0.004647066816687584 | True |
| 0/r3 | 201.66908809915185 | 1972.2094449680299 | 13.94126265251085 | 0.006494112312793732 | True |
| 0/r4 | 196.68708997778594 | 1498.3681610319763 | 13.70190601109674 | 0.008335104212164879 | True |
| 0/r5 | 117.09314002655447 | 1825.262530008331 | 13.450152677021862 | 0.004088971763849258 | True |
| 1/r0 | 14.996038982644677 | 1620.130404131487 | 16.896151212093077 | 0.008600996807217598 | True |
| 1/r1 | 112.99912887625396 | 2035.346627002582 | 15.136594473435654 | 0.006675021722912788 | False |
| 1/r2 | 56.34558596648276 | 1563.1464649923146 | 15.86106188448244 | 0.005017966032028198 | True |
| 1/r3 | 198.29674996435642 | 1942.8225948940963 | 13.736423975824723 | 0.004667090252041817 | True |
| 1/r4 | 192.51498812809587 | 1467.299824114889 | 13.4187877472294 | 0.008224043995141983 | True |
| 1/r5 | 111.94866499863565 | 1794.3528660107404 | 13.24727717332366 | 0.004148110747337341 | True |
| 2/r0 | 15.479129971936345 | 1838.926576077938 | 19.19418364322107 | 0.015228986740112305 | True |
| 2/r1 | 97.58731815963984 | 2345.431057969108 | 17.699557006373766 | 0.004878966137766838 | False |
| 2/r2 | 39.2528239171952 | 1852.645639097318 | 19.088345422948663 | 0.004539964720606804 | True |
| 2/r3 | 191.66114600375295 | 2252.3812300059944 | 16.226142393718437 | 0.006729038432240486 | False |
| 2/r4 | 188.80716292187572 | 1742.6824958529323 | 16.356582451905858 | 0.01478707417845726 | True |
| 2/r5 | 109.1754490043968 | 2106.124307960272 | 15.724006763432087 | 0.0071229878813028336 | False |

| 轮 | 实际观测窗秒 | 达标请求 | timing goodput请求/秒 |
| ---: | ---: | ---: | ---: |
| 0 | 2.224835936911404 | 5 | 2.2473567228247746 |
| 1 | 2.194955957122147 | 5 | 2.2779500352962003 |
| 2 | 2.5066277908626944 | 3 | 1.1968270721866943 |

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
