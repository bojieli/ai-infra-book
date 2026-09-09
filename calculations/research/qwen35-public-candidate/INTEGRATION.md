# Qwen3.5 公共接入候选

只新增独立候选，未改共享文件。模块／测试已标准格式化，分号多语句和混合缩进已拆开；已补齐项目的旧“remain gaps/incomplete”算子备注改为reference supplement，公式和范围保留。独立数学与最终差异审查见 ../qwen35-independent-math/FINAL-REVIEW.md。

## 优先合入的文件

按 [merge-guards.json](merge-guards.json) 核对目标before SHA（null表示必须不存在），然后复制同相对路径：

- src/infra_calc/topics/qwen35_forward.py
- src/infra_calc/topics/qwen35_reference_steps.py
- tests/test_qwen35_forward.py
- tests/test_qwen35_reference_steps.py
- sources/qwen3.5-397b-a17b/masking_utils.py

将 [source-lock.append.json](source-lock.append.json) 的唯一新增记录按 `file` 去重追加到公共 sources.lock.json；不要覆盖整个lock。模型已有205条来源以规范化子集SHA绑定，新增后为206条。helper原件SHA与固定commit不变；downloaded_at采用原件mtime并明确标注依据，不伪称原HTTP时间字段。

模块改为公共PROJECT／provenance／read_source／model_config，明确校验mask源已接入；已有研究原件路径保持公共锁原有file值，数据仍可以位于research目录。测试导入的是 `infra_calc.topics`，不导入研究模块，也不读研究目录里的衍生tensor-inventory数字。无需将大规模原件搬目录。

[isolation.json](isolation.json)、[test-output.txt](test-output.txt)、[scenario-test-output.txt](scenario-test-output.txt) 记录隔离公共包验证：21项测试、8场景重放／Markdown全部通过。隔离src来自当时公共版本，配置锁独立追加mask，原件只读链接；共享文件没有被修改。

## CLI：待 F03 合入后按锚点添加，不覆盖整文件

独立import：

```python
from .topics import qwen35_forward
```

在 `parser()` 的sub创建后添加：

```python
qwen35 = sub.add_parser(
    "qwen35-forward", help="Qwen3.5 base-text reference operator ledger"
)
qwen35.add_argument("--inputs", type=Path)
qwen35.add_argument("--format", choices=("json", "md", "csv"), default="json")
qwen35.add_argument("--output", type=Path)
```

在main现有topic分派链添加：

```python
elif args.command == "qwen35-forward":
    inputs = json.loads(args.inputs.read_text()) if args.inputs else {}
    result = qwen35_forward.calculate(**inputs)
```

沿用F03已经加固的JSON输出与错误处理，不增加任何allow_nan=True或旁路写出。`model_list()` 的base_commands追加 `'qwen3.5-397b-a17b': 'qwen35-forward'`；不要把它加入通用Qwen3 Dense/MoE forward分派，架构不同。

## Report：必须早期专用分支

候选module自带markdown，将以下内容放入 `report.markdown()` 的generic分支之前：

```python
if result.get("calculation") == "qwen35-base-text-ledger":
    from .topics.qwen35_forward import markdown as qwen35_markdown
    return qwen35_markdown(result)
```

专用报告分列reference工作、path/state、类别累计与语句接口，明确禁止把两类bytes加成HBM。CSV可沿用公共operator_csv，因为operators保持公共schema；完整weights、source-step接口和状态在JSON。

## Book／reproduce

将 [book-group.json](book-group.json) 的 `qwen35_forward` 组加入book.json，8行均为 `{id, inputs}`，不要重排或覆盖既有组。没有额外CLI默认scenario文件需要绑定，默认值在模块中。

reproduce新增独立import及run中循环，沿用已有save的严格JSON／MD／CSV写出：

```python
qwen35_rows = []
for row in scenarios.get("qwen35_forward", []):
    result = qwen35_forward.calculate(**row["inputs"])
    save(row["id"], result)
    qwen35_rows.append((row["id"], result))
```

README组在写文件和manifest之前加入：

```python
lines.extend(["", "Qwen3.5 基础文本参考路径（非实际运行时间）：", ""])
for name, result in qwen35_rows:
    summary = result["summary"]
    lines.append(
        f"- [{name}]({name}.md)：矩阵工作 {summary['matrix_flops']}；"
        f"路径 {result['execution']['linear_path']['kind']}；"
        "算子边界与补充接口不可相加为HBM。"
    )
```

返回计数新增 `"qwen35_forward_scenarios": len(qwen35_rows)`。公共input_hashes已经包含sources.lock已下载原件、所有src、book；新mask必须先追加来源锁，勿另依赖本候选source-lock.append文件。保留F03的manifest路径／重复／hash校验。

## Outline 插入建议

不生成当前outline.py覆盖候选。在sync函数已有insert机制中，于 `02-模型架构.md` 的 `## 2.5 条件计算与专家数据` 前增加键 `Qwen35-reference`：

```python
insert(
    "02-模型架构.md",
    "Qwen35-reference",
    "[Qwen3.5基础文本](../calculations/results/qwen35-prefill-8192.md)按固定配置与1038个真实checkpoint张量形状核对，"
    "45层DeltaNet、15层gated GQA与60层MoE分列，基础文本396346350336参数、792692717952存储bytes，视觉/MTP另列。"
    "8192 prefill在声明eager矩形attention／chunk64路径计304038065373184矩阵FLOPs；"
    "[单步decode](../calculations/results/qwen35-decode-b1.md)为36977377472，均非实测运行时间。"
    "[65token尾块](../calculations/results/qwen35-chunk-tail-65.md)核心补到128位置；"
    "[初始单token](../calculations/results/qwen35-cold-single-token.md)普通卷积cache先pad到4，conv计算7位置后裁切，不能只计一个有效输出。"
    "[record-past初始别名](../calculations/results/qwen35-cold-single-record-past.md)无last4复制；"
    "已有记录长度未知时保留缺项。两类张量接口有重叠，禁止相加为HBM；primitive后端、allocator及非所选分支不由此验证。"
    "运行 `python3 calculations/calc.py qwen35-forward --format md`，`--inputs`改场景。",
    "## 2.5 条件计算与专家数据",
)
```

不可用本候选勾选整个C11/C12或完整runtime；F02官方输入验收已经独立完成。

## 最小接入验收

复制5文件、按file追加1来源、加5处接入片段和book组之后：来源校验；21个qwen35测试；默认CLI JSON/MD/CSV；8行book参数重放；最后主线统一reproduce/verify-results/sync/render。建议比较默认数值和cold record-past无复制条件。源文件guards只用于新增候选，不捕获正在变动的cli/reproduce SHA以制造虚假覆盖安全；这些共享文件必须在F03之后按上述锚点增量编辑。
