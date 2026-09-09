# V4 expert preflight

Status: in progress — locating remote runtime and reading unmodified SM120 implementation before protocol freeze.
Scope: six cached layer-0 real MXFP4 experts; synthetic BF16 input and routing; no full model, no calculations, no shared environment changes, no child agents.
Limits: one GPU process, GPU ≤3 GiB, CPU 4 threads, RAM ≤8 GiB; require ≥4 GiB free before launch. Local raw artifacts ≤500 MiB.

协议已冻结：PROTOCOL.md。已完整读取原 SM120 forward/slot kernel、Marlin bridge 及 OffloaderV1；checkpoint 六专家 I8/F8_E8M0 布局和原 loader [w1;w3] 核对完成。远端空闲 36294 MiB。即将以独立 watchdog 启动：真实切片 smoke 通过后才完整形状；逐元素 2% relative + 0.2% RMS floor、relative-L2 1%，不随结果修改。

远端 run 已退出 0：PID 2724667，GPU sampled peak 1050 MiB，进程树 RSS sampled peak 1640910848 bytes，Torch allocated peak 363039744 bytes。真实切片 smoke 通过；M1/M8、六单专家、零权重、invalid-slot、置换、clamp 控制、原函数 profiler、官方 OffloaderV1 已执行。正在退出后传输约243 MiB结果，尚未判定完整数值是否通过；下一步独立分析与完整误差留档。

独立分析：所有保存的 CPU 参考/stages 经本地 NumPy FP64 从 raw packed 重算逐位一致；36 tensor SHA 与 assembled 布局核验通过。数值预设门槛未全通过：main_m8 10/32768 元素失败（relative-L2 0.000392407）；padded/zero_slot 各2、permuted/unclamped各10，为相关复现而非独立事件。M1、六单专家、active clamp均通过。所有 exact controls 包括 OffloaderV1 均通过。保持门槛不变，正完成 README 与失败清单，交主agent审核，不再启动GPU测试。

完成，交主agent统一审核：README.md、PROTOCOL.md、standalone run.py/launch.py/reference.py/analyze.py、所有真实 raw/assembled/input/output/reference、profiler、OffloaderV1、运行退出和内存记录、全部逐元素误差/失败均保存在 expert-preflight/。原始远端结果传输 SHA 已逐项核验，源函数/bridge/offloader 运行后 hash 未变，协议 hash 未变。运行与分析流程 exit 0；数值门槛 all_numerical_cases_pass=false，exact controls 全 true。未放宽门槛，未为全V4放行，未再启动GPU测试。后续解释与整体决策留主agent审核。
