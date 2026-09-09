# 首轮13-7：先冻结、后执行的新K192预测

未知条件为K192，绝非把已知K32/96测量改名为预测。原11-4两个task prompt/expected、model revision、greedy、不thinking、768上限、原prompt256分块、prefix64分块、逐tokenSQLite确认及commit-before-ACK SIGKILL全部保持。新增5个完整trial，每trial两任务×baseline/restart/preserve三策略=6路径，合计30路径、10个配对比值。每trial内以同一个seed1307连续随机流打乱6路径；具体完整顺序冻结future-plan.json。不得提前停止或按最好结果挑轮次。

主指标R为10个(task,trial)配对的 preserve完整窗口/restart完整窗口 的中位数；窗口沿11-4从第一worker创建返回到最后worker退出。预测范围[0.70,1.00]，主观把握65%，不是统计置信区间；另预测20条恢复路径全部自然EOS、严格任务验收且完整token与本trial baseline相同。两门槛必须同时满足才支持联合预测。R低于0.70同样判数值区间失准，即使方向更有利，也不改原区间。

最强已知反例：11-4 sequence K96 preserve12.800s，restart11.619s，比值约1.102，说明省重复采样不保证总窗口更短。该历史结果放known-evidence，与新观察严格分开。增大K可能增加避免的串行decode，但重新加载、prefill、prefix重建和SQLite／调度开销仍存在，预测没有假设这些成本为零。

未来执行一次一个Mac Metal worker，自身RSS/MLX active≤16GiB，单worker300秒、总1800秒，复用已SHA核对完整Qwen3-8B-MLX-4bit，不下载/复制权重，不改原11-4。沿用当前热文件缓存与smoke已运行状态，不清系统缓存，不额外暖模型；每worker重新加载权重。同机CPU后台可能共存，不能作独占因果或生产速度承诺；记录真实顺序与各阶段，不能根据共存情况事后删不利轮次。

冻结prediction.json observation=null及其SHA，执行前保存创建UTC、deadline和来源摘要。截止2026-09-16T15:59:59Z（新加坡23:59:59）。今日运行也只能在冻结之后。原件不可覆盖；新观察、评判和修订另文件追加。任何任务失败/冲突/截断均保留并使质量门槛失败，不能从分母剔除；全30路径不完整则状态pending_incomplete，不填R直到全记录就绪，截止无完整观察为expired_unobserved。超期数据标late，不能追认按期命中。

原第13章13.5.2要求预测、已知反例、观察和修订并列；本实验不执行C76/C63计算，不展开最终跨session论文审计。若超出硬件/模型/runner条件，另登记out_of_scope而不拿来支持原预测。源脚本、任务、顺序和模型身份均在冻结文件中绑定SHA。
