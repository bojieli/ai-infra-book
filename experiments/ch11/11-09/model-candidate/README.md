# 11-9 已有替换模型候选的同任务实测

状态：候选模型两次实测完成，11-9整体partial。复用RTX主机已完整缓存的Qwen3-VL-30B-A3B-Instruct-FP8快照d9748a51ae66354c4dad665aab2c71f26cf2c8cd，没有重复下载。纯文本输入，image/video上限0，APCoff，贪心、1000总生成上限；同修复任务、六例检查及独立1013例标准。

它是另一具体部署候选，不预先称更好模型。与原Qwen3-8B比较时，结构、激活方式、checkpoint精度和模板同时改变，不能把结果单归参数量或FP8。输入文本相同但tokenizer/模板不保证相同IDs；本候选实际输入157token。

## 结果

| 轮次 | 输出token | 结束 | 首token秒 | 模型＋原检查秒 | 原六例 |
|---|---:|---|---:|---:|---:|
| 0 | 175 | stop | 0.672886 | 6.210548 | 3/6 |
| 1 | 175 | stop | 0.035005 | 5.453028 | 3/6 |

两次完整代码相同。模型使用sorted避免原地排序，但result的首项直接引用输入内层列表；合并或后来修改输出仍可能改变输入。

独立1013例中，两次均有615例满足值正确及调用后输入不变，但进一步修改返回值检查别名时，其中614例失败，严格标准仅1/1013通过。额外别名标准单列，不把615与原六例混为同一口径。两个请求均不满足质量门槛，verified_usable_s及费用仍为空；自然结束不能当作任务完成。

首请求和第二次TTFT差异明显，没有拆分首次内核准备开销，不把两样本当稳定尾延迟或优化后吞吐。启动日志记载权重加载约19秒、模型加载显存29.28GiB，另有默认MoE配置未调优提示；初始化不包含在请求计时中。文件大小、模型加载显存和整机峰值不是同一量。

## 证据与复现

run.py/fixture.py独立携带相同任务和工具，check_code.py/check_all.py独立携带连通分量oracle及别名检查。配置和软件版本见results/environment.json。model-metadata.json记录HF快照、JSON文件哈希和四个权重分片大小，model-config.json保留实际结构/量化配置；没有计算32GB权重逐字哈希，不将这些元数据称完整权重内容校验。

在相同vLLM专用环境、无results的独立副本执行：

    python run.py --model /local/path/to/fixed/Qwen3-VL-30B-A3B-Instruct-FP8/snapshot
    python check_all.py

后者在受限子进程运行独立检查，原始stdout/stderr保留。python3 analyze.py离线核验源码、模型config哈希、请求输入/用量/代码/六例及1013例计数。run.log、模型完整答案、token IDs、测试反馈和工作目录全部封存于manifest.json。AST约束不是通用安全沙箱。

模型已关闭，gpu-after.txt显示原四项GPU服务仍在；没有终止原服务或修改calculations。当前没有可据以计算成功任务成本的合格候选；更多任务/候选、实际环境恢复及货币成本仍待，最终跨session实验与论文复核未开始。
