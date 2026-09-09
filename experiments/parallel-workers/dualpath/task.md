你是主实验session授权启动的独立Codex CLI worker，负责实验12-6真实双路径传输部分。先读 outlines/12-端边云协同.md 及 extensions 同章的实验12-6，与现有 experiments/ch12/12-04/loopback、h3-multistream README 避免重复。计算/轨迹模拟归 calculations/ 另一session，禁止执行、修改、复制其任务或联系其作者。

唯一可写目录 experiments/ch12/12-06/ 和 experiments/parallel-workers/dualpath/status.md。其他目录只读，禁止编辑正文/总进展/inventory/research/references/skeleton，禁止git提交、再启动agents/Codex。先写status，结束更新结果和未覆盖要求。

执行有界的真实本机socket双路径实验：用独立进程/真实TCP或QUIC连接传送相同有序音频样式数据、打断通知、工具结果，对照复制与故障后切换。必须实际关闭/中断连接并记录客户端/服务端收发、取消ack、重复字节/去重/乱序及应用完成，不能仅sleep模拟网络并称真实WAN。可以固定生成PCM夹具与真实软件消费/取消，明确非TTS模型/物理播放/蜂窝能耗。实际传输是本worker范围，数学扫描不做。需事前协议、相同payload/SHA、重复试验、无故障/单路径故障/共同端点故障负例、独立验收正确性，保留失败。若范围需要调整，依证据做合理有界判断。

仅Mac CPU/socket，禁止GPU/MPS/SSH。CPU总不超过2线程，内存<2GiB，数据<500MB。可用 experiments/tools/http3-venv（aioquic1.3/h11/Pillow），experiments/.venv绘图，不改共享venv。端口动态分配并实际清理，不碰他人服务。其他CPU worker共存，时间仅实现观测，不能做隔离性能因果结论。不要复跑12-4同一HTTP基准。独立目录run/analyze/plot/README/原始记录/环境版本/源hash，绘图QA。正文简洁候选句放自己README由主agent回填。只完成本有界实验，不做最终跨session审计，不宣称12-6所有WAN/电量要求完成。
