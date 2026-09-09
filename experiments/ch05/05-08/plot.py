#!/usr/bin/env python3
"""Unprofiled execution times and independently captured host/device timelines."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
root=Path(__file__).resolve().parent
out=root/"results"
data=json.loads((out/"results.json").read_text())
trace=json.loads((out/"trace-analysis.json").read_text())
plt.rcParams.update({"font.size":10,"svg.fonttype":"none"})
fig,axes=plt.subplots(1,3,figsize=(11.5,4.2))
for ax,m,labels,title in [(axes[0],32,["eager","fused","graph","fused_graph"],"Full FFN, 32 tokens"),
                         (axes[1],257,["fused_graph","fused_graph_copy","fused_graph_pad512"],"257 tokens: boundaries"),
                         (axes[2],32,["fused_graph","fused_graph_micro4","fused_graph_micro8"],"32 tokens: microbatches")]:
    rows=[next(r for r in data["rows"] if r["tokens"]==m and r["label"]==label) for label in labels]
    med=[r["median_us"] for r in rows]
    err=[[v-min(r["samples_us"]) for r,v in zip(rows,med)],[max(r["samples_us"])-v for r,v in zip(rows,med)]]
    ax.bar(range(len(rows)),med,color="#008b79",yerr=err,capsize=3)
    ax.set_xticks(range(len(rows)),[x.replace("fused_graph","F+G").replace("_","\n") for x in labels],fontsize=9)
    ax.set_ylabel("Microseconds per original batch")
    ax.set_title(title)
    ax.spines[["top","right"]].set_visible(False)
    ax.grid(axis="y",alpha=.2);ax.set_axisbelow(True)
fig.suptitle("Launch savings in a complete Qwen3-shaped FFN",fontsize=14)
fig.text(.5,.015,"RTX PRO 6000 Blackwell · random BF16 weights · unprofiled · median and min–max of 11 trials · shared GPU",ha="center",fontsize=8)
fig.tight_layout(rect=(0,.08,1,.94))
for ext in ["svg","png"]:fig.savefig(out/f"execution.{ext}",dpi=160)
plt.close(fig)

labels=["eager","fused","graph","fused_graph"]
spans=[next(r for r in trace["ranges"] if r["label"]==label) for label in labels]
limit=max((r["end_ns"]-r["start_ns"])/1000 for r in spans)
fig,axes=plt.subplots(4,1,figsize=(11,7.8),sharex=True)
for ax,row in zip(axes,spans):
    origin=row["start_ns"]
    for api in row["apis"]:
        waiting="Synchronize" in api["name"]
        ax.broken_barh([((api["start_ns"]-origin)/1000,(api["end_ns"]-api["start_ns"])/1000)],
                       (1.1,.55),facecolors="#c7cbd1" if waiting else "#54728c")
    for k in row["kernels"]:
        pointwise="elementwise" in k["name"] or k["name"]=="activation"
        ax.broken_barh([((k["start_ns"]-origin)/1000,(k["end_ns"]-k["start_ns"])/1000)],
                       (.1,.55),facecolors="#c17629" if pointwise else "#008b79")
    ax.set_yticks([.38,1.38],["GPU","Host"])
    ax.set_ylim(-.1,1.9);ax.set_xlim(0,limit)
    ax.set_title(f"{row['label']} — 3 calls, {row['kernel_count']} GPU kernels, {row['launch_api_count']} launch APIs",loc="left",fontsize=10)
    ax.spines[["top","right","left"]].set_visible(False)
    ax.grid(axis="x",alpha=.15)
axes[-1].set_xlabel("Microseconds since each NVTX range began (same scale)")
fig.suptitle("Observed host and device timeline: 32 tokens",fontsize=14)
fig.legend(handles=[Patch(color="#54728c",label="CUDA API"),Patch(color="#c7cbd1",label="Host synchronization wait"),
                    Patch(color="#008b79",label="GEMM / reduction"),Patch(color="#c17629",label="Activation")],
           loc="upper center",bbox_to_anchor=(.5,.946),ncol=4,frameon=False,fontsize=9)
fig.text(.5,.014,"Nsight Systems 2026.4.1 · graph node tracing · profiling changes timings; use the separate unprofiled run for performance",ha="center",fontsize=8)
fig.tight_layout(rect=(0,.05,1,.89))
for ext in ["svg","png"]:fig.savefig(out/f"timeline.{ext}",dpi=160)
