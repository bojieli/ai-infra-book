# 首次执行偏差

首次执行命令为 `experiments/tools/http3-venv/bin/python experiments/ch12/12-04/loopback/run.py --output experiments/ch12/12-04/loopback/smoke`，未传 --smoke。因此虽然输出目录名为 smoke，实际 environment.smoke=false，完整执行3trial×8条件×8请求=192，加两个独立warmup，共194。没有先完成小规模smoke；如实保留该准备流程偏差，不把目录名当运行参数，也不重新运行同批来改名。

原 PROTOCOL 的smoke文字写每条件2请求，脚本实现每条件4请求以容纳4 lanes；该模式本次没有执行，不能声称做了2或4请求smoke。正式条件每组8请求没有变。协议原文保留，主分析校验本批194数量及environment.smoke=false。

实际脚本exit0，终端输出 requests194/failures0/server_errors[]。结果逐请求、服务端收到的数据、TLS/ALPN与QUIC qlog已独立核验。启动前没有单独记录主机其他任务；主审指出同时存在PID50035，后续只读ps/cwd检查保留在coexisting-process.txt，不能声称主机独占。该实验没有使用RTX或安装系统服务。
