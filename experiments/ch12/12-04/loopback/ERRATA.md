# 主复核：一个统计字段名称的澄清

2026-09-09 主 agent 复算194请求、校验95份封存文件及图后确认：summary.json 中 `median_ready_to_body_complete_ms` 的实际定义是 `median((end - send) * 1000)`，即**发出请求至响应体完整接收**，不是连接 ready 至响应体完整接收。原始记录同时保留 connection_ready、send、end，可分别重算。该字段名称不准确，数值未改。

README 主表和图使用 `validation_end - start`，表示尝试开始至校验结束，与此字段不同，不受该命名问题影响。已封存源码、summary 和 manifest 原件保持原状，本说明单独追加。
