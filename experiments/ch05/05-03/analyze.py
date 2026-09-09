#!/usr/bin/env python3
"""Sum only the requested hardware counters from actual Nsight raw exports."""
import csv
import json
from pathlib import Path
root=Path(__file__).resolve().parent
out=root/"results"
collection=json.loads((out/"counters/collection.json").read_text())
rows=[]
for record in collection["records"]:
    source=out/"counters"/record["csv"]
    raw=list(csv.DictReader(source.open()))
    units=raw[0]
    for metric in collection["metrics"]:
        assert units[metric]==("ns" if metric=="gpu__time_duration.sum" else "byte"),(metric,units[metric])
    kernels=[]
    for item in raw:
        if not item["ID"].isdigit():continue
        values={metric:float(item[metric].replace(",","")) for metric in collection["metrics"]}
        kernels.append({"id":int(item["ID"]),"name":item["Kernel Name"],"metrics":values})
    assert kernels,source
    totals={metric:sum(k["metrics"][metric] for k in kernels) for metric in collection["metrics"]}
    rows.append({"n":record["n"],"backend":record["backend"],"kernel_count":len(kernels),"kernels":kernels,
                 "totals":totals,"source_csv":"counters/"+record["csv"],"source_report":"counters/"+record["report"]})
result={"kind":"hardware_counter_measurement","collection":collection,"rows":rows,
        "scope":"Kernel-scoped counter sums after warmup, cache-control none. Zero DRAM counts do not imply zero logical accesses; dirty cache lines may be written after the sampled kernels. L2 counter measures requested bytes."}
(out/"traffic.json").write_text(json.dumps(result,indent=2)+"\n")
for row in rows:
    print(row["n"],row["backend"],row["kernel_count"],row["totals"])
