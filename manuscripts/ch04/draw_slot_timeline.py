"""Regenerate Figure 4-23 from the chapter's two checked-in schedules."""
import json
from pathlib import Path
import subprocess
from xml.etree import ElementTree as ET

HERE = Path(__file__).resolve().parent
RESULTS = HERE.parents[1] / "calculations/results"
OUTPUT = HERE / "figure-4-davinci-attention-timeline"
colors = {"qk": "#31729a", "pv": "#38547c", "softmax": "#227866",
          "scores": "#ac591e", "probabilities": "#84406a"}
rows = {"matrix": 0, "handoff": 1, "vector": 2}
svg = ET.Element("svg", xmlns="http://www.w3.org/2000/svg", width="920", height="445",
                 viewBox="0 0 920 445", style="font:14px sans-serif")


def label(x, y, value, **attrs):
    ET.SubElement(svg, "text", x=str(x), y=str(y), **attrs).text = str(value)


def xpos(tick):
    return 100 + tick * 0.245


def bar(row, start, end, color, caption, detail):
    x, width = xpos(start), xpos(end) - xpos(start)
    rect = ET.SubElement(svg, "rect", x=str(x), y=str(row), width=str(width),
                         height="18", fill=color, stroke="white")
    ET.SubElement(rect, "title").text = f"{detail} [{start}, {end})"
    if caption:
        label(x + width / 2, row + 14, caption, fill="white", **{"text-anchor": "middle"})


ET.SubElement(svg, "rect", width="100%", height="100%", fill="white")
for index, (path, name) in enumerate([("staged", "写出再读入"), ("direct", "直接传递")]):
    data = json.loads((RESULTS / f"matrix-vector-{path}-rows32-slots2.json").read_text())
    top = 45 + 205 * index
    label(15, top - 18, f"{name} · {data['summary']['finish_tick']} tick", **{"font-weight": "bold"})
    for tick in range(0, 3201, 400):
        x = str(xpos(tick))
        ET.SubElement(svg, "line", x1=x, x2=x, y1=str(top), y2=str(top + 126), stroke="#dadde1")
        label(x, top + 145, tick, **{"text-anchor": "middle"})
    for row, title in enumerate(["矩阵", "交接", "Softmax", "槽 0", "槽 1"]):
        label(24, top + 26 * row + 14, title)
    for task in data["timeline"]:
        group, phase = task["id"].split(".")
        caption = {"qk": "QK", "pv": "PV", "softmax": group.upper()}.get(phase, "")
        bar(top + 26 * rows[task["resource"]], task["start_tick"], task["end_tick"],
            colors[phase], caption, task["id"])
    for slot in data["slot_ownership"]:
        group = slot["group"]
        bar(top + 26 * (3 + slot["slot"]), slot["start_tick"], slot["release_tick"],
            ["#495563", "#657382"][group // 2], f"G{group}", f"slot {slot['slot']} G{group}")

label(100, 428, "教学 tick     交接方向")
for x, phase, name in [(285, "scores", "QK → Softmax"), (465, "probabilities", "Softmax → PV")]:
    ET.SubElement(svg, "rect", x=str(x), y="415", width="20", height="14", fill=colors[phase])
    label(x + 26, 428, name)
ET.ElementTree(svg).write(OUTPUT.with_suffix(".svg"), encoding="utf-8", xml_declaration=True)
for fmt in ["png", "pdf"]:
    subprocess.run(["rsvg-convert", "-f", fmt, "-o", OUTPUT.with_suffix("." + fmt),
                    OUTPUT.with_suffix(".svg")], check=True)
