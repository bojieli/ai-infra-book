# 9-8 补测：截断页进入真实恢复请求

在独立存储副本中，把正常HiCache恢复轨迹读取的首个KV文件由2,359,296字节截短为2,359,294字节。固定SGLang 0.5.13.post1、Qwen3-8B BF16、1024输入/16输出、Triton attention与wait_complete预取，新引擎就绪后发送真实请求。

**本次请求在60.083秒观察窗口内未完成，也没有向调用方抛出异常。** 首个get产生`OSError: Short read`，日志显示异常从预取I/O辅助线程抛出。窗口到期时模型主进程仍在；监督程序随后只终止本次独立进程组，父进程退出码-9，清理后组成员为空。截断文件保持原损坏哈希。

| 证据 | 实际记录 |
|---|---|
| 模型初始化 | 已出现ready与request_start事件 |
| 存储调用 | 一个get begin，随后一个OSError异常；未记录成功返回 |
| 请求结果 | 生命周期无request_return或request_exception |
| 截止条件 | 从request_start起观察60秒，实际60.083秒 |
| 退出原因 | 实验监督程序执行SIGTERM、必要时SIGKILL清理 |
| 清理范围 | 本次Popen创建的独立进程组；清理后成员为空 |

安装源码快照中，prefetch_io_aux_func仅捕获队列Empty，实际异常栈也经过该函数。这与本次线程异常和请求未完成相符，但本实验只观察一个固定条件：不推断永久死锁、所有超时策略或其他版本行为，也不把监督程序的60秒窗口当成服务SLO或配置超时。没有测量故障概率。

观测器包装原get/set，记录异常后原样重新抛出；不修改恢复算法。原存储目录和已封存结果保持不变。与此前“文件缺失会回退”的模型实测相比，本次截断文件存在却发生读取异常，行为不同；不能把缺失与损坏合并为同一种恢复成功。

results/包含完整引擎日志、请求生命周期、存储异常事件和监督记录；truncated-page.bin保留实际损坏文件，原页已在父实验封存。source-snapshots/保存安装源码。verify.py核对执行源码哈希、损坏文件哈希、异常路径、观察窗口与退出状态，不把负面结果误标为恢复通过。

从仓库根目录离线验证：

```sh
python3 experiments/ch09/09-08/truncated-request/verify.py
python3 experiments/ch09/09-08/truncated-request/verify_manifest.py
```

重跑时使用整个独立9-8实验目录的新副本，保留父目录storage-v3和原consumer轨迹作输入；在此子目录执行`python3 supervise.py`，已有results或storage目录会被拒绝。专用环境安装见父目录ENVIRONMENT.md。脚本只清理自己创建的进程组，不停止共享服务。

端到端截断的单条件观察已完成；其他损坏、格式/身份不兼容、写入中故障、预取策略比较、容量/保存策略、Agent轨迹、V4压缩与远端等仍待，9-8保持partial。calculations未修改或执行，最终跨session复核未开始。
