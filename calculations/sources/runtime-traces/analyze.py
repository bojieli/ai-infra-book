#!/usr/bin/env python3
"""Extract observed host/device intervals from the archived Nsight SQLite export."""
import json
import sqlite3
from pathlib import Path
root=Path(__file__).resolve().parent
out=root/"results"
c=sqlite3.connect(f"file:{out/'timeline.sqlite'}?mode=ro",uri=True)
c.row_factory=sqlite3.Row
strings=dict(c.execute("select id,value from StringIds"))


def union_ns(intervals):
    total=0;end=None
    for a,b in sorted(intervals):
        if end is None or a>end:total+=b-a
        elif b>end:total+=b-end
        end=b if end is None else max(end,b)
    return total


result={"kind":"Nsight trace analysis, not unprofiled timing", "calls_per_range":3,"ranges":[]}
for span in c.execute("select start,end,text from NVTX_EVENTS where text like 'exp5_8:%' order by start"):
    a,b,label=span
    kernels=[]
    for k in c.execute("select start,end,shortName,demangledName,streamId,graphNodeId from CUPTI_ACTIVITY_KIND_KERNEL where start>=? and end<=? order by start",(a,b)):
        kernels.append({"start_ns":k["start"],"end_ns":k["end"],"name":strings[k["shortName"]],
                        "full_name":strings[k["demangledName"]],"stream":k["streamId"],"graph_node":k["graphNodeId"]})
    apis=[{"start_ns":r["start"],"end_ns":r["end"],"name":strings[r["nameId"]]} for r in c.execute(
        "select start,end,nameId from CUPTI_ACTIVITY_KIND_RUNTIME where start>=? and end<=? order by start",(a,b))]
    copies=[dict(r) for r in c.execute("select start as start_ns,end as end_ns,bytes,copyKind from CUPTI_ACTIVITY_KIND_MEMCPY where start>=? and end<=? order by start",(a,b))]
    activities=kernels+copies
    assert kernels, label
    first=min(k["start_ns"] for k in activities);last=max(k["end_ns"] for k in activities)
    active=union_ns([(k["start_ns"],k["end_ns"]) for k in activities])
    launches=[x for x in apis if "Launch" in x["name"]]
    result["ranges"].append({"label":label.split(":",1)[1],"start_ns":a,"end_ns":b,
        "kernels":kernels,"apis":apis,"copies":copies,"kernel_count":len(kernels),
        "launch_api_count":len(launches),"graph_launch_count":sum("GraphLaunch" in x["name"] for x in launches),
        "device_span_us":(last-first)/1000,"captured_device_active_us":active/1000,
        "uncovered_device_interval_us":(last-first-active)/1000,
        "scope":"Gaps are intervals without this process's captured kernels/copies, not proof the GPU was globally idle"})
(out/"trace-analysis.json").write_text(json.dumps(result,indent=2)+"\n")
for row in result["ranges"]:
    print(row["label"],row["kernel_count"],row["launch_api_count"],round(row["uncovered_device_interval_us"],3))
