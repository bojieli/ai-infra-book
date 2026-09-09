# C05 独立集成包

所有文件仅写research/c05-integration/。复核：

```bash
python calculations/research/c05-integration/verify_and_build.py
PYTHONPATH=calculations/src python -m unittest discover -s calculations/tests -p test_ub_scope.py
```

合并顺序：

1. scenarios.json的ub_scope数组合并到scenarios/book.json；10个id保持不变。
2. cli.snippet.py提供import/parser/dispatch；inputs-default.json可复制为scenarios/ub-scope-example.json。
3. renderer.py的函数并入report.py，按report.snippet.py在markdown入口先分派，解决缺顶层summary问题。
4. reproduce.snippet.py提供scenario循环、结果目录索引、计数及外部原件manifest输入。
5. outline.snippet.py提供在1.6.2之前插入的完整正文文本。内容明确只是现代教学计算；原C05不关闭。
6. 统一reproduce与现有验证后，检查10个JSON/Markdown、正文链接和manifest输入。此目录生成的20个产物供审阅，正式产物应由共享reproduce生成至results/。

本包的validation.json包含逐场景结果对照；acceptance-gaps.md给默认数值、独立公式、历史缺项和不可扩大解释的边界。原始模块/API不需为了集成被更改。
