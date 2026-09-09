# 主复核：两个解释器的区别

本实验实际使用 `/home/ubuntu/sglang-venv/bin/python`，导入用户site-packages中的Torch2.10.0+cu128，以及该环境Transformers5.8.1；原始 `results/source-addendum.json` 已精确保存路径。主任务先前提供的 `/home/ubuntu/ai-infra-book-experiments/tools/sglang0513-venv/bin/python` 是另一环境，主agent当前实查仍导入该私有site-packages的Torch2.11.0+cu130。

因此本次版本差异是选择了不同解释器，不是已证明提供的环境发生版本漂移。允许保留已成功的CPU执行，不为版本重跑；原README/数据/manifest保持封存。运行和数值结论仅对应实际2.10环境。
