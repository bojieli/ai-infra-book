# 执行前协议：真实模型抢占与持久token恢复

固定Mac M2 Max96GiB、缓存官方Qwen3-8B-MLX-4bit revision383413e909f3bc5303ce195ebbdf0339c5a1a2a3，MLX0.32.2/mlx-lm0.31.3。原模型所有文件SHA先检查，不复制权重、不改共享库。Mac Metal单worker，自己的进程组RSS与MLX active各≤16GiB，单worker300秒、总任务1800秒；仅终止自己start_new_session的精确PGID。

两个正式新任务：JSON整数数组101..164；从固定打乱表中提取24个编号和值、按编号升序输出JSON对象。完整文本和期望答案冻结tasks.json，禁止根据smoke或结果替换。温度0/argmax、关闭thinking、总输出上限768。严格JSON结构、整数类型／准确键值与顺序、无额外文本，自然EOS才合格。

固定阈值K32/96，三个策略baseline/restart/preserve：2任务×2阈值×3策略=12条正式逻辑路径。baseline在两个K下实际分别执行，属于相同任务的配对重复，不当独立任务数。正式顺序用seed1104打乱。smoke单独使用JSON整数11..26、K8、上限128，三个策略各一次，只排除IPC/持久化/生命周期错误，正式任务不根据smoke质量改动。

使用自己的同步单步model/argmax/mx.eval/synchronize循环，而非有提前一步计算的mlx_lm.generate_step。所有策略原prompt均按256token分块prefill，返回每token后等管理器确认再做下一模型步。preserve新进程用原prompt重建，然后将已提交prefix token按64token块实际teacher-forcing重建KV，再从下一个序号真实argmax生成。批量重建可能改变数值路径，须真实检验输出分歧，不能强制后缀与baseline相同。无随机采样、无speculative、无KV迁移。

独立本地HTTP管理器SQLite WAL/synchronous=FULL，以(request_id,seq)唯一键提交token（含EOS），绑定模型和prompt身份。相同key相同token计重复，相同key不同token记冲突并返回409，不能静默覆盖。EOS及最终quality分别记录。restart从原prompt重做并重投相同序号；preserve从数据库查询已提交前缀与高水位。

两个中断策略在第K个非EOS token提交事务之后、ACK返回之前阻塞handler。控制器确认ready，再SIGKILL自身生成进程组；管理器继续存活，新PID重启同一策略。此为提交后ACK未返回的受控中断，不是物理网络丢包。若模型自然EOS早于K，记录未触发抢占，不改阈值。length/质量失败/序号冲突/数值分歧是科学结果，全部保留。

记录真实token IDs、模型call输入长度及KV offset、生成／投递／事务时间、数据库副本、进程生命周期、模型加载／prefill／prefix KV重建／后续decode、重复投递与唯一提交数、RSS/MLX内存。KV重建不是零工作。只统计实测工作和同批最终有效结果，不做C63费用、资源存活或预期损失模型。不把同步逐token事务提交runner当mlx-lm常规吞吐。已有8-7生成和11-9 Collector记录不作为本次新结果。
