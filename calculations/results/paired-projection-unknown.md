# 配对投影：时间费用与平均功率条件

墙钟记录为11组每组16调用平均值的中位数，不是单次调用p95。两端使用相同BF16夹具和Qwen8 Q投影形状，数值不是checkpoint权重。

| M | 权重模式 | MPS墙钟代理秒 | CUDA墙钟代理秒 | RTX/Mac费用率或平均功率持平比 |
|---:|---|---:|---:|---:|
| 1 | reused | 0.000165986999 | 4.29181237e-05 | 3.86752694 |
| 1 | rotating | 0.000182650998 | 5.18660672e-05 | 3.5215895 |
| 256 | reused | 0.001835375 | 3.26489971e-05 | 56.215356 |
| 256 | rotating | 0.00183522393 | 3.34776996e-05 | 54.8192963 |

若同一服务窗口的RTX/Mac整机小时费用率低于持平比，RTX的时间费用代理较低；等号持平。对声明的平均整机功率比同理。这不是实际报价或测得的能耗。

| M/模式 | MPS费用代理 | CUDA费用代理 | MPS焦耳代理 | CUDA焦耳代理 |
|---|---:|---:|---:|---:|
| 1/reused | 未知 | 未知 | 未知 | 未知 |
| 1/rotating | 未知 | 未知 | 未知 | 未知 |
| 256/reused | 未知 | 未知 | 未知 | 未知 |
| 256/rotating | 未知 | 未知 | 未知 | 未知 |

## 适用范围

- Recorded wall samples are 11 trial averages, each from 16 calls plus submission/synchronization, divided by16. Their median is not median single-call latency or p95.
- MPS and CUDA use matching BF16 input/weight fixtures and Qwen3-8B Q-projection dimensions. Original reference checks are reported, not rerun here; whole-model quality and MPS internal accumulation precision are not established.
- Compare only the same M and reused/rotating mode. Rotation is not proof of cold DRAM. Wall-to-wall comparison includes host/runtime differences; CUDA event time is not substituted for MPS wall time.
- RTX is cheaper in the declared active-time proxy iff its hourly whole-system cost divided by Mac cost is below t_Mac/t_RTX; equality ties. The same algebra holds for declared average whole-system watts.
- Rates and watts are user-declared scenario inputs for the same service window. They are not hardware price, rental quote, TDP, measured energy or total ownership cost.
- No synchronized power trace or cost input exists in the timing source. Unknowns remain null; applying a declared constant power to median time gives a proxy, not measured median energy.
- Fractions preserve arithmetic on recorded decimal values, not physical clock accuracy. Initialization, idle lifecycle, utilization and whole application quality/cost remain outside this task proxy.

## 原始来源与完整计算

```json
{
  "calculation": "paired-projection-conditional-cost",
  "sources": [
    {
      "file": "sources/paired-projection-cost/projection.py",
      "sha256": "1f8964bacba740acc4cb109575772bd80ee6bb072b40c90820e19a8bcdb88b95"
    },
    {
      "file": "sources/paired-projection-cost/results/projection-manifest.json",
      "sha256": "8ec2d01b7b1dce23f608a14b030989bb86d5d15f5bfa48b53a55cc9806252eee"
    },
    {
      "file": "sources/paired-projection-cost/results/projection-mps/results.json",
      "sha256": "9bafff934c938ecdee061d16b3e57c7a955e9a783d3394185f2712345dfa6f15"
    },
    {
      "file": "sources/paired-projection-cost/results/projection-cuda/results.json",
      "sha256": "bd462666e45e1cd42226b1780729b1b3da26bf853a766cbdccb136455f3694b9"
    }
  ],
  "model_sources": [
    {
      "file": "configs/models/qwen3-8b/config.json",
      "url": "https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json",
      "revision": "b968826d9c46dd6066d109eabc6255188de91218",
      "sha256": "f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30"
    },
    {
      "file": "sources/qwen3-8b/model.safetensors.index.json",
      "url": "https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json",
      "revision": "b968826d9c46dd6066d109eabc6255188de91218",
      "sha256": "f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc"
    },
    {
      "file": "sources/qwen3/modeling_qwen3.py",
      "url": "https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py",
      "revision": "0720e206c6ba28887e4d60ef60a6a089f6c1cc76",
      "sha256": "704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2"
    },
    {
      "file": "sources/qwen3/modeling_qwen3_moe.py",
      "url": "https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py",
      "revision": "0720e206c6ba28887e4d60ef60a6a089f6c1cc76",
      "sha256": "3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8"
    }
  ],
  "scenario": {
    "hourly_cost_units": null,
    "whole_system_watts": null
  },
  "rows": [
    {
      "m": 1,
      "n": 4096,
      "k": 4096,
      "mode": "reused",
      "matrix_flops": 33554432,
      "times_seconds_exact": {
        "mps": {
          "numerator": 8299349974549841,
          "denominator": 50000000000000000000
        },
        "cuda": {
          "numerator": 4291812365408987,
          "denominator": 100000000000000000000
        }
      },
      "reported_reference_max_abs_error": {
        "mps": "0.03125",
        "cuda": "0.03125"
      },
      "rtx_over_mac_rate_tie_ratio": {
        "numerator": 16598699949099682,
        "denominator": 4291812365408987
      },
      "cost_per_call_proxy": null,
      "joules_per_call_proxy": null,
      "lower_declared_cost": null,
      "lower_declared_energy": null,
      "measured_task_energy_joules": null,
      "observed_cost_per_call": null
    },
    {
      "m": 1,
      "n": 4096,
      "k": 4096,
      "mode": "rotating",
      "matrix_flops": 33554432,
      "times_seconds_exact": {
        "mps": {
          "numerator": 18265099788550287,
          "denominator": 100000000000000000000
        },
        "cuda": {
          "numerator": 5186606722418219,
          "denominator": 100000000000000000000
        }
      },
      "reported_reference_max_abs_error": {
        "mps": "0.03125",
        "cuda": "0.03125"
      },
      "rtx_over_mac_rate_tie_ratio": {
        "numerator": 18265099788550287,
        "denominator": 5186606722418219
      },
      "cost_per_call_proxy": null,
      "joules_per_call_proxy": null,
      "lower_declared_cost": null,
      "lower_declared_energy": null,
      "measured_task_energy_joules": null,
      "observed_cost_per_call": null
    },
    {
      "m": 256,
      "n": 4096,
      "k": 4096,
      "mode": "reused",
      "matrix_flops": 8589934592,
      "times_seconds_exact": {
        "mps": {
          "numerator": 9176874991680961,
          "denominator": 5000000000000000000
        },
        "cuda": {
          "numerator": 3264899714849889,
          "denominator": 100000000000000000000
        }
      },
      "reported_reference_max_abs_error": {
        "mps": "0.0625",
        "cuda": "0.0625"
      },
      "rtx_over_mac_rate_tie_ratio": {
        "numerator": 183537499833619220,
        "denominator": 3264899714849889
      },
      "cost_per_call_proxy": null,
      "joules_per_call_proxy": null,
      "lower_declared_cost": null,
      "lower_declared_energy": null,
      "measured_task_energy_joules": null,
      "observed_cost_per_call": null
    },
    {
      "m": 256,
      "n": 4096,
      "k": 4096,
      "mode": "rotating",
      "matrix_flops": 8589934592,
      "times_seconds_exact": {
        "mps": {
          "numerator": 3670447869808413,
          "denominator": 2000000000000000000
        },
        "cuda": {
          "numerator": 3347769961692393,
          "denominator": 100000000000000000000
        }
      },
      "reported_reference_max_abs_error": {
        "mps": "0.0625",
        "cuda": "0.0625"
      },
      "rtx_over_mac_rate_tie_ratio": {
        "numerator": 61174131163473550,
        "denominator": 1115923320564131
      },
      "cost_per_call_proxy": null,
      "joules_per_call_proxy": null,
      "lower_declared_cost": null,
      "lower_declared_energy": null,
      "measured_task_energy_joules": null,
      "observed_cost_per_call": null
    }
  ],
  "assumptions": [
    "Recorded wall samples are 11 trial averages, each from 16 calls plus submission/synchronization, divided by16. Their median is not median single-call latency or p95.",
    "MPS and CUDA use matching BF16 input/weight fixtures and Qwen3-8B Q-projection dimensions. Original reference checks are reported, not rerun here; whole-model quality and MPS internal accumulation precision are not established.",
    "Compare only the same M and reused/rotating mode. Rotation is not proof of cold DRAM. Wall-to-wall comparison includes host/runtime differences; CUDA event time is not substituted for MPS wall time.",
    "RTX is cheaper in the declared active-time proxy iff its hourly whole-system cost divided by Mac cost is below t_Mac/t_RTX; equality ties. The same algebra holds for declared average whole-system watts.",
    "Rates and watts are user-declared scenario inputs for the same service window. They are not hardware price, rental quote, TDP, measured energy or total ownership cost.",
    "No synchronized power trace or cost input exists in the timing source. Unknowns remain null; applying a declared constant power to median time gives a proxy, not measured median energy.",
    "Fractions preserve arithmetic on recorded decimal values, not physical clock accuracy. Initialization, idle lifecycle, utilization and whole application quality/cost remain outside this task proxy."
  ]
}
```
