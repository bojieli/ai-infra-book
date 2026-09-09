# 实验9-7：共享KV池

- [固定前缀与4/8GiB容量对照](shared-kv/README.md)：两个独立引擎的真实写入、取回、驻留与回收；两组各72记录，共用24条重算参考。
- [真实Agent历史完整生成回放](agent-history/README.md)：两个实例交替处理12轮历史，三条件三重复；保留输出一致性门槛失败、生成KV写入与下一轮前缀身份变化。

已完成子目录各自可运行、各自封存。现有结果限定同GPU/CPU池；跨主机和实际PD交接仍待。C50计算与其他session工作未修改。

- [历史序列化检查](history-prefix/README.md)：四种拼接方式，保留前缀的两种方式11/11通过；CPU tokenizer实测。
- [保留前缀后的GPU回放](history-preserved/README.md)：108生成完成，实际取回上一轮生成KV241token/重复，但共享第9请求提前finish，严格输出等价仍失败。

- [退出后的共享内存回收](pool-reclamation/README.md)：发现进程退出后仍有本任务68GiB命名池，核对归属及全机无引用后已回收；原先无残留进程不代表池已释放。
