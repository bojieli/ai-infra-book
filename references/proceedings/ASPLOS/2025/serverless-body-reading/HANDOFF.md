# 交接：Dilu / Medusa 指定正文比较

本包只新增第 11 章相关的两篇指定正文阅读，不新增摘要、论文或模型评估结果。原 PDF、完整摘要与身份首页仍沿用 `../parallel-pim-serverless/`，该封包未修改；共享 manifest、coverage、verifier、outline 和 Git 均未修改。

阅读记录为 2 篇、17 个物理 PDF 页：Dilu 4、6、7、8、9、11、12、13；Medusa 5–13。后者第 13 页主要用于 artifact 环境核对，故同时分列 16 页主要正文与 1 页 appendix。未声称全文阅读。实际看图共 9 页，逐页观察记在 `reading-records.json`。

重点结论见 `READINGS.md`。Dilu 的纵向份额是 kernel-block token admission，5 ms 是控制周期，<1 ms 的 scaling overhead 不是模型冷启动。Medusa 是 graph/KV 初始化信息物化，不能写成用户 KV 历史内容持久化；其 Qwen1.5-4B 的 2.85/2.48/1.67 s 是 loading phase 的关键路径。53.0% p99 TTFT 来自 warm execution environment 下的特定模型/RPS 配置。

论文与代码之间保留两个实际问题：Dilu 固定版本 README 指向的 vertical scaling README 返回 404；Medusa 研究 fork 的 `vllm/__init__.py` 声明 0.3.1，README 要求修改 PyTorch/SPDK 和特定 CUDA/driver，并没有固定全部依赖 commit。只静态读元数据、README 与该版本字符串文件，未构建、未执行第三方脚本。

一个需要保留的组合问题：Dilu 动态共置改变显存占用，Medusa 则复用离线测得的可用显存。两者无缝组合没有被这些材料验证；图、形状、kernel 版本和容量信息的失效条件应继续明确。

从仓库根独立核验：

```sh
python references/proceedings/ASPLOS/2025/serverless-body-reading/verify.py
```

需要系统 Poppler 的 `pdfinfo`、`pdftotext` 与 Python 标准库。核验入口重新从原 PDF 提取 17 页并逐字节比较；原始文本使用默认 `pdftotext -f N -l N`，没有 `-raw`、没有 `-layout`、没有手删栏间碎片。图像用 `pdftoppm -scale-to 1600 -singlefile -png` 生成；双栏表格和时间线的语义来自实际看图，不靠文本串的先后顺序推测。验证不会执行下载的代码，也不会访问网络。

此外核验两条正式 manifest DOI、首页标题与全部作者、原 PDF 哈希与页数、历史响应记录、6 条新 HTTP 响应（5 成功、1 个 404）、2 个 Git commit 与固定 URL、12 项独立关键路径计算。验证器只写本目录 `validation.json`；GitHub API 和 raw 文件原始响应留在本目录，失败不覆盖、不隐藏。

根任务若接入总索引，请按 DOI `10.1145/3669940.3707251` 和 `10.1145/3669940.3707285` 升级 selected-sections 阅读状态；不能把这两个已有摘要/已有 PDF 再计一次。保持第 11 章现有主节和实验编号，只把“先调份额，再启动实例，再缩短 loading”的对照和失效前提放进既有问题。无需为了这两篇另起大纲结构。
