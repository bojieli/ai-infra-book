#!/usr/bin/env python3
"""Plot only recorded timings and compiler metadata; requires matplotlib."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

root = Path(__file__).resolve().parent
data = json.loads((root / "results/results.json").read_text())
plt.rcParams.update({"font.size": 10, "svg.fonttype": "none"})
fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.3))
for ax, m, n in [(axes[0], 1024, 4096), (axes[1], 1003, 4093)]:
    for layout, color, marker in [("contiguous", "#54728c", "o"), ("transposed", "#008b79", "s"),
                                  ("strided_columns", "#c17629", "^")]:
        rows = sorted([r for r in data["rows"] if r["m"] == m and r["layout"] == layout], key=lambda r:r["tile"])
        med = [r["median_us"] for r in rows]
        err = [[v - min(r["samples_us"]) for r, v in zip(rows, med)],
               [max(r["samples_us"]) - v for r, v in zip(rows, med)]]
        ax.errorbar(range(3), med, yerr=err, color=color, marker=marker, label=layout.replace("_", " "), capsize=3)
    ax.set_title(f"{m:,} × {n:,} input")
    ax.set_xticks(range(3), ["16×16 / 4", "32×32 / 4", "64×64 / 8"])
    ax.set_xlabel("Tile / warps")
    ax.set_ylabel("Microseconds per materialized transpose")
    ax.set_ylim(bottom=0)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=.2)
axes[1].legend(frameon=False)
fig.suptitle("Same Triton program, different physical layouts", fontsize=14)
fig.text(.5, .018, "RTX PRO 6000 Blackwell · FP16 · warm buffers · graph replay · median and min–max of 11 trials · shared GPU",
         ha="center", fontsize=8)
fig.tight_layout(rect=(0,.07,1,.94))
for ext in ["svg", "png"]:
    fig.savefig(root / f"results/layouts.{ext}", dpi=160)
