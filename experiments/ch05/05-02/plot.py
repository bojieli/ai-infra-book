#!/usr/bin/env python3
"""Regenerate figures from recorded measurements; no CUDA required."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

root = Path(__file__).resolve().parent
data = json.loads((root / "results/results.json").read_text())
plt.rcParams.update({"font.size": 10, "svg.fonttype": "none"})
fig, axes = plt.subplots(1, 3, figsize=(11, 3.9), sharey=False)
colors = {"separate": "#54728c", "fused": "#008b79"}
for ax, tokens in zip(axes, [1, 32, 1024]):
    for offset, mode in [(-0.18, "separate"), (0.18, "fused")]:
        rows = [r for r in data["rows"] if r["tokens"] == tokens and r["mode"] == mode]
        medians = [r["graph_median_us"] for r in rows]
        errors = [[v - min(r["graph_samples_us"]) for r, v in zip(rows, medians)],
                  [max(r["graph_samples_us"]) - v for r, v in zip(rows, medians)]]
        ax.bar([i + offset for i in range(3)], medians, width=.34, label=mode,
               color=colors[mode], yerr=errors, capsize=3)
    ax.set_title(f"{tokens:,} tokens × 12,288")
    ax.set_xticks(range(3), ["256 / 4", "1024 / 4", "4096 / 8"])
    ax.set_xlabel("Elements per block / warps")
    ax.set_ylabel("Microseconds per chain")
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_axisbelow(True)
    ax.grid(axis="y", alpha=.2)
axes[0].legend(frameon=False)
fig.suptitle("SwiGLU activation: fusion and launch geometry", fontsize=14)
fig.text(.5, .015, "RTX PRO 6000 Blackwell · BF16 · warm buffers · CUDA Graph · median and min–max of 11 trials · shared GPU",
         ha="center", fontsize=8)
fig.tight_layout(rect=(0, .06, 1, .94))
fig.savefig(root / "results/fusion.svg")
fig.savefig(root / "results/fusion.png", dpi=160)
