# 计时初版保留

四条件执行完成，但backend end_s取在SQLite事务开始前，不能当提交完成时刻。此批仅保留程序执行与计时检查，不纳入正式积压曲线。正式版本在SQLite事务提交后记录end_s，另保留commit_start_s。不修改初版原件。
