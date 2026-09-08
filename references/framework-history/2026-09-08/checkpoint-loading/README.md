# 检查点与权重加载的历史核对

核对日期 2026-09-08。`sources.json` 保留 9 个官方响应及哈希：8 个内容来源，另一个是 HTTP 200 的客户端重定向页。重定向原件保留，实际文档跟到 PyTorch 2.14。所有阅读范围已写入记录；未执行下载代码或运行保存／加载实验。

| 来源 | 已读范围与采用位置 |
| --- | --- |
| [vLLM v0.6.0 loader](vllm-060-loader.py) | 495–657 行，2024 年 rank 专用预分片读写路径；其他 loader 未读。 |
| [vLLM v0.9.2 loader](vllm-092-loader.py) | 完整文件；2025 版本中的 S3、Run:ai 与本地文件分支。 |
| [vLLM 固定主线 loader](vllm-current-loader.py) | 完整文件，提交 `51da0ca66c8065619c79e35dff97aa99aeaf5644`；未审其依赖及所有量化布局。 |
| [固定主线内存文档](vllm-current-memory.md) | 完整文档；采用 TP／预分片段。实际磁盘读取仍需区分页缓存和共享存储。 |
| [PyTorch 2024 公告](pytorch-2024-blog.html) | article 全文及页首日期；页面显示 2024-06-12 与 2024-11-13，正文比较线程异步保存，图曲线／代码截图未独立读取。 |
| [PyTorch 2025 公告](pytorch-2025-blog.html) | article 全文及页首日期；页面显示 2025-04-30 与 2025-05-03，进程与计划缓存组合结果，未独立量化曲线。 |
| [stable 重定向](pytorch-current-doc.html) | 只包含版本重定向，不当 API 文档正文。 |
| [PyTorch 2.14 API](pytorch-214-doc.html) | AsyncSaveResponse、async_save、AsyncStager、DefaultStager 的完整 API 项；其余文档未读。 |
| [2.14 saver 源码](pytorch-214-saver.py) | 195–414 行，确认条件返回对象、默认线程及内部 stager 配置；未审 StorageWriter 与各执行器。 |

vLLM 三个取样点说明某个版本已存在的行为，不证明功能首次引入日期。预分片 state_dict 的 rank／布局绑定与 ByteCheckpoint 的全局张量表示不同；不能直接跨 TP 复用文件，不能将推理权重文件视为完整训练状态。

PyTorch 文档默认值与可选路径分开：`async_save` 默认 THREAD，只有 staging 返回 Future 才返回双完成对象。API 返回、快照可安全使用、存储完成分别核对；本轮未证明所有 StorageWriter 的持久化承诺。

本次仅深化第 10.6／11.4 及已有实验，详见[算例与论文范围](../../../../case-studies/checkpoint-layout-and-loading.md)。来源原地址、版本与获取时间见[清单](sources.json)。
