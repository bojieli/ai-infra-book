# 冻结协议：真实文本预取与 packing 恢复

正式运行前固定：Mac CPU，Torch 2.14，主进程 intra2/inter1，两个 DataLoader worker 各1线程，prefetch_factor=2，spawn、顺序返回；模型为复制并绑定SHA的3-8两层width64 byte Transformer（无dropout），CPU FP32，AdamW lr0.001/betas0.9,0.95/eps1e-8/wd0.01，clip1。文本及source.json同3-8固定源，不修改源目录。变长记录长度257+2*(record_id%7)，顺序读实际UTF-8 bytes；每步1×128 next-byte标签，跨记录连续packing，消费128字节保留下一位置，实际训练64步。

正式模型seed固定1061/1062/1063；检查点固定第17/41步，绝不按结果挑点。三个未中断基线、六个前缀保存/终止及六个新PID恢复路径。必须在每个固定位置观测packing剩余>1字节且有已派发未消费、以及worker完成但未消费的预取记录，否则停止修复smoke，不变更正式检查点。数据顺序固定，seed改变初始化。

保存模型、完整Adam、CPU RNG、DataLoader独立Generator、已消费记录游标、packing字节和源位置。记录派发/worker完成/实际消费的差别。恢复从已消费记录游标重读未消费预取记录；不访问私有队列，不宣称序列化队列。重做未消费预处理允许，已提交训练输入不许漏或重复。DataLoader有自己的随机Generator，防止构造新iterator扰动模型RNG；worker执行确定性读取，无随机增强。

checkpoint写入临时文件、flush/fsync、rename及目录fsync后发ready；控制器仅SIGTERM自己start_new_session的子进程组（含其DataLoader workers），核对PGID/PID。新进程从checkpoint恢复到64步，逐步loss/input及最终全部模型/Adam/RNG必须与基线逐位一致。CPU结果完全相等是机制门槛，不泛化不同硬件。

两个预登记负对照仅seed1061/checkpoint17：omit_buffer丢弃packing残留；dispatch_cursor保留buffer但错用已派发游标。二者实际恢复训练到64步，应由独立源位置与状态核验检出错误。负结果保留。正常停止时间、worker记录、重新读取、首次正确恢复步、checkpoint字节、控制器采样自身进程树RSS均保存。非断电持久性、非故障周期优化、非大模型存储吞吐或DataLoader随机增强恢复。

smoke固定seed1061/checkpoint17并训练至20步（基线、前缀/恢复及两负对照），成功后才正式运行。产物≤1GiB，进程树RSS≤4GiB，单进程≤120秒、总体≤20分钟；不使用GPU、不接触其他进程。启动调试失败由成功替代后删除，正式控制全部保留。
