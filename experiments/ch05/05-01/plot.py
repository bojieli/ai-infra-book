#!/usr/bin/env python3
"""Regenerate the CPU timing figure from local raw results."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
root = Path(__file__).resolve().parent
data = json.loads((root / "results/results.json").read_text())
plt.rcParams.update({"font.size": 10, "svg.fonttype": "none"})
fig, axes = plt.subplots(2,2,figsize=(11,6.7))
for ax, shape in zip(axes.flat, [(64,64,64),(128,512,64),(256,128,256),(127,257,65)]):
    rows = [r for r in data["rows"] if (r["m"],r["k"],r["n"]) == shape]
    med = [r["median_us"] for r in rows]
    err = [[v - min(r["samples_us"]) for r,v in zip(rows,med)],
           [max(r["samples_us"]) - v for r,v in zip(rows,med)]]
    labels = [r["method"] if not r["tile"] else f"b{r['tile']}" for r in rows]
    colors = ["#aa7254", "#008b79"] + ["#54728c"] * 6
    for i, (value, color) in enumerate(zip(med, colors)):
        ax.errorbar(i, value, yerr=[[err[0][i]], [err[1][i]]],
                    fmt="o", color=color, capsize=3, markersize=6)
    ax.set_xticks(range(8), labels, fontsize=9)
    ax.set_title(f"M={shape[0]}, K={shape[1]}, N={shape[2]}")
    ax.set_ylabel("Microseconds (log scale)")
    ax.set_yscale("log")
    ax.spines[["top","right"]].set_visible(False)
    ax.set_axisbelow(True)
    ax.grid(axis="y", alpha=.2)
fig.suptitle("CPU matmul: loop order and blocking", fontsize=14)
fig.text(.5,.015,"Apple M2 Max · one unpinned CPU thread · FP32 · hot buffers · b = cubic tile size · median and min–max of 9 trials",
         ha="center",fontsize=8)
fig.tight_layout(rect=(0,.05,1,.94))
for ext in ["svg","png"]:
    fig.savefig(root / f"results/loops.{ext}",dpi=160)
