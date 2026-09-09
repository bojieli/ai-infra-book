#!/usr/bin/env python3
"""Regenerate plots from the measured event times, allocations and hardware counters."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parent
out=root/"results"
data=json.loads((out/"results.json").read_text())
traffic=json.loads((out/"traffic.json").read_text())
plt.rcParams.update({"font.size":10,"svg.fonttype":"none"})
fig,axes=plt.subplots(1,3,figsize=(12,4.3))
for backend,color,marker in [("math","#54728c","o"),("flash","#008b79","s")]:
    rows=sorted([r for r in data["rows"] if r["backend"]==backend],key=lambda r:r["n"])
    ns=[r["n"] for r in rows];med=[r["graph_median_us"] for r in rows]
    err=[[v-min(r["graph_samples_us"]) for v,r in zip(med,rows)],
         [max(r["graph_samples_us"])-v for v,r in zip(med,rows)]]
    axes[0].errorbar(ns,med,yerr=err,color=color,marker=marker,capsize=3,label=backend)
    axes[1].plot(ns,[r["peak_increment_bytes"]/2**20 for r in rows],color=color,marker=marker,label=backend)
    t=next(r for r in traffic["rows"] if r["n"]==8192 and r["backend"]==backend)["totals"]
    values=[t["dram__bytes_op_read.sum"],t["dram__bytes_op_write.sum"],t["lts__t_bytes.sum"]]
    offset=-.18 if backend=="math" else .18
    bars=axes[2].bar([i+offset for i in range(3)],[v/2**20 for v in values],width=.34,color=color,label=backend)
    for bar,value in zip(bars,values):
        label=f"{value/2**20:.0f}" if value>=2**20 else f"{value:.0f} B"
        axes[2].annotate(label,(bar.get_x()+bar.get_width()/2,bar.get_height()),xytext=(0,4),textcoords="offset points",ha="center",fontsize=8)
for ax in axes[:2]:
    ax.set_xscale("log",base=2);ax.set_yscale("log")
    ax.set_xticks([128,512,2048,8192],["128","512","2048","8192"])
    ax.set_xlabel("Sequence length")
axes[0].set_title("Measured graph execution")
axes[0].set_ylabel("Microseconds (log scale)")
axes[0].legend(frameon=False)
axes[1].set_title("One eager call: peak allocation")
axes[1].set_ylabel("Incremental allocated MiB (log scale)")
axes[2].set_title("N=8192: measured warm counters")
axes[2].set_ylabel("MiB")
axes[2].set_xticks(range(3),["DRAM\nread","DRAM\nwrite","L2\nrequested"])
axes[2].set_ylim(0,6000)
for ax in axes:
    ax.spines[["top","right"]].set_visible(False)
    ax.grid(axis="y",alpha=.18);ax.set_axisbelow(True)
fig.suptitle("Causal attention: one head, D=128, BF16",fontsize=14)
fig.text(.5,.013,"RTX PRO 6000 Blackwell · warm buffers · timing and counters collected separately · shared GPU · error bars: min–max of 11 trials",ha="center",fontsize=8)
fig.tight_layout(rect=(0,.075,1,.94))
for ext in ["svg","png"]:fig.savefig(out/f"attention.{ext}",dpi=160)
