# 公共迁移说明

将 `src/infra_calc/topics/` 下两个文件放到同名公共目录，将两个测试放到 `calculations/tests/`。模块之间正常相对 import；没有研究目录路径、动态源码加载或额外运行时依赖。`v4_training_primitives.calculate` 和 `v4_hc_training.calculate` 均与原冻结函数 AST 完全相同，六份结果与原结果逐字段相同。

建议 CLI topic 名为 `v4-training-primitives` 与 `v4-hc-training`，共用输入参数 `batch`、`tokens`；每个模块均提供 `calculate(**scenario)` 与专用 `markdown(result)`。`book.append.json` 按 topic 分组，每组是三个扁平场景（one-row、128、batch2）。展示中必须维持当前 scope：两者是可微数学子图，均不等于完整 V4 训练。hc 报告已经包含一次 split，不要再与 primitive 报告整项相加。

`sources.lock.subset.json` 仅保存已在公共锁中的完整来源记录，无新增记录需要 append。`bindings.json` 同时绑定模块、测试、六份 JSON/MD、原冻结候选及公共 helper 依赖。`verify_public.py` 检查所有原件 bytes/SHA，并拒绝任何数值测试 skip。

候选独立验证：

```sh
/Users/boj/miniconda3/bin/python calculations/research/v4-hc-training-completion/public/verify_public.py
```

迁入后数值验证：

```sh
/Users/boj/miniconda3/bin/python -m unittest discover -s calculations/tests -p 'test_v4*training*.py' -v
```

7 项数值/契约测试通过、0skip。无 torch 的解释器可继续运行纯计数测试，数值用例显式 skip；这种结果不能代替上述实际数值验收。独立审查在 `research/v4-training-independent/REVIEW.md`，92 检查通过；公共候选只做 import/format/report 迁移，数学不变。

报告每个结果均给摘要，并完整展开全部记录叶字段，包括来源、unknown、特殊调用、索引、保存范围和 hc 事件图。验证器断言每个叶字段都已进入报告。
