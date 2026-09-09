# service-replay — 

输入：`{"e2e_limit_ms": 2000, "mean_tpot_limit_ms": 20, "run": "chunk512", "ttft_limit_ms": 300}`

请求时间来自封存实际交付；SLO阈值为本次分析输入，仅衡量计时达标。

| 结果 | 值 |
| --- | ---: |
| requests | 18 |
| output_tokens | 2,016 |
| joint_timing_passed | 9 |
| joint_timing_pass_fraction | 0.5 |
| ttft_passed | 18 |
| e2e_passed | 9 |
| mean_tpot_passed | 18 |
| summed_observation_window_s | 7.541148112155497 |
| timing_goodput_requests_per_s | 1.193452225861072 |
| request_throughput_per_s | 2.386904451722144 |
| output_throughput_tokens_per_s | 267.33329859288017 |
| multi_token_delivery_events | 0 |

| 轮／请求 | 客户端TTFT ms | 客户端E2E ms | 客户端平均TPOT ms | 引擎排队ms | 联合计时达标 |
| --- | ---: | ---: | ---: | ---: | --- |
| 0/r0 | 15.318992082029581 | 1845.3334660734981 | 19.263310252541775 | 0.016767997294664383 | True |
| 0/r1 | 134.7593921236694 | 2364.49775705114 | 17.556994999428902 | 0.004064058884978294 | False |
| 0/r2 | 54.12935116328299 | 1826.0197651106864 | 18.651478041551616 | 27.53309183754027 | True |
| 0/r3 | 274.1795659530908 | 2376.043183961883 | 16.550107228415687 | 0.003997934982180595 | False |
| 0/r4 | 223.7936039455235 | 1850.3661339636892 | 17.121816105454375 | 149.52777791768312 | True |
| 0/r5 | 194.86291985958815 | 2275.7278110366315 | 16.384762922653884 | 93.18584389984608 | False |
| 1/r0 | 23.66205188445747 | 1574.3477188516408 | 16.323007020707195 | 0.020305858924984932 | True |
| 1/r1 | 129.81678801588714 | 2158.7042501196265 | 15.975491827588499 | 0.004446133971214294 | False |
| 1/r2 | 50.81948381848633 | 1557.0668010041118 | 15.855234917743426 | 0.005251960828900337 | True |
| 1/r3 | 267.78574008494616 | 2153.6885760724545 | 14.8496286298229 | 0.003959052264690399 | False |
| 1/r4 | 215.5377499293536 | 1661.5915899164975 | 15.221619368285724 | 147.65050308778882 | True |
| 1/r5 | 181.19688192382455 | 2030.5254207924008 | 14.561642038335247 | 90.96035012044013 | False |
| 2/r0 | 22.204698994755745 | 1709.4887939747423 | 17.76088521031565 | 0.02053612843155861 | True |
| 2/r1 | 140.83512919023633 | 2141.9026711955667 | 15.756437338624648 | 0.0072640832513570786 | False |
| 2/r2 | 60.76653185300529 | 1651.7438779119402 | 16.747129958515103 | 27.85361697897315 | True |
| 2/r3 | 267.44989585131407 | 2158.7205880787224 | 14.891895214389042 | 0.007255934178829193 | False |
| 2/r4 | 216.11512918025255 | 1631.6494380589575 | 14.900361146091631 | 149.41617101430893 | True |
| 2/r5 | 187.34329286962748 | 2034.4301250297576 | 14.543990804410473 | 91.96610609069467 | False |

| 轮 | 实际观测窗秒 | 达标请求 | timing goodput请求/秒 |
| ---: | ---: | ---: | ---: |
| 0 | 2.676192771177739 | 3 | 1.1209954799630373 |
| 1 | 2.4304061718285084 | 3 | 1.2343615790536606 |
| 2 | 2.43454916914925 | 3 | 1.2322610025774696 |

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
