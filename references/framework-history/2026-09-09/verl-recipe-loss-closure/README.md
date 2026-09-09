# 固定 verl 配方的 loss／梯度更新补读

本包仅补实验 10-8 的 `verl@d040717b21af2e23e8e789a3e354cff2394ae2de` 单卡 CP/SP=1、DP=1、FSDP NO_SHARD 调用路径。结论及精确行号见[编辑审读报告](../../../../research/2026-infra-survey/qa/verl-recipe-loss-closure.md)。

- `raw/`：只按此固定提交获取的九个源码原字节；不导入、不执行。
- `sources.json`：逐文件 URL、HTTP 状态、获取时间、响应头、字节数与 SHA-256。
- `reused-sources.json`：26 个现有实验材料的 SHA 和时间；不重复复制原实验数据。
- `reading.json`：实际正文/源码选读范围、结构化 JSON 字段及只核 hash 的边界。
- `verify.py`、`verification.json`：自写标准库静态核验与标量运算结果。

在仓库根目录运行：

```bash
python references/framework-history/2026-09-09/verl-recipe-loss-closure/verify.py
```

已闭合共同 loss 分母、mini/micro 划分、累积、裁剪和一次 optimizer 调用。实际 `use_no_sync_for_gradient_accumulation=False`，不能声称启用了最后微批才跨卡同步。没有新 GPU 实验，也没有扩大到其他框架或版本。
