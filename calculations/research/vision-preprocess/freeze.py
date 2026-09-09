import hashlib, json
from pathlib import Path
from vision_preprocess import calculate

HERE = Path(__file__).resolve().parent
scenarios = [
    dict(id="vision-preprocess-aligned640", height=640, width=640),
    dict(id="vision-preprocess-nonsquare", height=257, width=385),
    dict(id="vision-preprocess-min-area", height=32, width=32),
    dict(id="vision-preprocess-max-area", height=4608, width=4608),
]
rows = []
for scenario in scenarios:
    result = calculate(**{k: v for k, v in scenario.items() if k != "id"})
    (HERE / (scenario["id"] + ".json")).write_text(json.dumps(result, indent=2) + "\n")
    rows.append(dict(id=scenario["id"], **result["summary"]))
(HERE / "scenarios.json").write_text(json.dumps(scenarios, indent=2) + "\n")
(HERE / "summary.json").write_text(json.dumps(rows, indent=2) + "\n")
lines = [
    "# RGB预处理到视觉入口逐阶段账",
    "",
    "固定官方Qwen配置与CPU generic uint8 bicubic-AA；完整范围与数值证明见CONTRACT.md/numeric-verification.json。",
    "",
    "| 场景 | Resize | Patch shape | FP32输出B | BF16入口B | 语义读B | 语义写B |",
    "|---|---|---|---:|---:|---:|---:|",
]
for r in rows:
    lines.append(
        f"| {r['id']} | {r['resized_height']}×{r['resized_width']} | {r['pixel_values_shape']} | {r['pixel_values_bytes']} | {r['encoder_input_bytes']} | {r['semantic_read_bytes']} | {r['semantic_write_bytes']} |"
    )
example = calculate(257, 385)
lines += [
    "",
    "## 257×385 非方形逐阶段",
    "",
    "| 阶段 | 读B | 写B | 操作 |",
    "|---|---:|---:|---|",
]
for st in example["stages"]:
    lines.append(
        f"| {st['stage']} | {st['semantic_read_bytes']} | {st['semantic_write_bytes']} | {json.dumps(st['operations'])} |"
    )
lines += [
    "",
    "resize_axes保存实际边界tap与INT16系数、精度bits和系数/索引buffer分配；这些整数MAC不计FP32 FLOPs。FP32归一化、时间展开物化及视觉入口cast独立列出。总语义流量已含系数内部访问，子字段不能再加一次。JPEG/PNG decode、CPU调度、设备传输与实际延迟/运行峰值均未计。",
    "",
    "重放：`python freeze.py`；计量测试：`python -m unittest discover -s . -p test_vision_preprocess.py -v`；独立数值：`python numeric_check.py`。",
    "",
    "硬件旧文案修订候选为hardware-prose.patch.json，三个guarded old/new替换仅status/pending/Active注释，不改任何数值，未应用共享配置。",
]
(HERE / "REPORT.md").write_text("\n".join(lines) + "\n")
files = []
for path in HERE.iterdir():
    if path.is_file() and path.name != "bindings.json":
        b = path.read_bytes()
        files.append(
            dict(file=path.name, bytes=len(b), sha256=hashlib.sha256(b).hexdigest())
        )
(HERE / "bindings.json").write_text(
    json.dumps(
        dict(
            files=files,
            tests=6,
            numerical_image_cases=5,
            numerical_resize_kernel_cases=4,
            numerical_geometry_cases=5,
            shared_modified=False,
        ),
        indent=2,
    )
    + "\n"
)
