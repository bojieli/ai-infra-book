# nic-budget — historical simple forwarding

输入：`{"baseline_packets_per_core_second": null, "cpu_target_utilization": "1/2", "encapsulation_bytes": 0, "link_bits_per_second": 40000000000, "link_utilization": "1", "packet_mix": null, "pcie": null, "retained_host_work": "1", "wire_overhead_bytes": 20}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| mean_wire_bytes_per_packet_exact | `"84"` |
| mean_work_multiplier_exact | `"1"` |
| packets_per_second_exact | `"1250000000/21"` |
| original_frame_bytes_per_second_exact | `"80000000000/21"` |
| wire_bytes_per_second_exact | `"5000000000"` |
| retained_host_work_exact | `"1"` |
| dedicated_cpu_cores | `[12, 6]` |
| complete_virtualization_cpu_cores | `null` |

| 历史/声明每核包率 | 忙核秒/秒 | 留余量后的核当量 | 专用整数核 |
| --- | --- | --- | --- |
| 10000000 | 125/21 | 250/21 | 12 |
| 20000000 | 125/42 | 125/21 | 6 |

包数分布：`[{"frame_bytes": 64, "wire_bytes": 84, "packet_share_exact": "1", "work_multiplier_exact": "1", "packets_per_second_exact": "1250000000/21"}]`

独立PCIe约束：`null`

计量条件：

- Historical thesis §4.2.1 reports 40 Gbps approximately 60 Mpps and simple forwarding 10–20 Mpps/core. This is the historical baseline, not a modern CPU benchmark or complete virtualization measurement.
- Default wire budget is a declared 64-byte Ethernet frame including FCS plus 8-byte preamble/SFD and 12-byte interpacket gap. Frame bytes are not application payload; encapsulation adds wire bytes before packet-rate conversion.
- Mixture shares are by packet count. Rate divides wire bytes/s by weighted mean wire occupancy, not a weighted mean of each class full-line packet rate. Fragmentation and MTU changes are not inferred.
- Work multipliers, target utilization and retained host work are declared comparisons. Busy core-seconds differ from allocated integer cores; linear multicore scaling is assumed, not established.
- Offload reduces only the declared host packet work. PCIe and in-flight constraints, when supplied, remain even if retained host work is zero; hardware processing, full host work, costs and SLOs are unknown.
- PCIe byte and concurrency limits are necessary resource bounds for one declared shared service, not sufficient throughput guarantees. No advertised link rate is silently used as effective payload service.

固定来源：

- [../references/files/papers/bojieli-phd-thesis.pdf](https://01.me/files/pubs/bojieli-phd-thesis.pdf)，SHA256 `ea0c815d15b6f9da0e08d8f12cb11cc028cf3c566d2d3b1d0725941fa5b6360c`。
- [../references/text/bojieli-phd-thesis.txt](https://01.me/files/pubs/bojieli-phd-thesis.pdf)，SHA256 `132f5448ad23fd2b3c39c364cf1810cf17417cf07852d239ec2910443055f6dd`。
