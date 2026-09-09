# Qwen注意力输入：有限槽与异步供数

时间为声明的离散教学单位，非实测GPU周期。输入槽一直占用到本块矩阵消费结束。

| 路径 | 输入槽 | 输入SMEM bytes | 寄存器中转 bytes | FP32累加器 bytes | 完成时刻 | 输入容量通过 |
|---|---:|---:|---:|---:|---:|---|
| synchronous-register-stage | 1 | 32768 | 131072 | 65536 | 1536 | True |
| synchronous-register-stage | 2 | 65536 | 131072 | 65536 | 1536 | True |
| synchronous-register-stage | 4 | 131072 | 131072 | 65536 | 1536 | False |
| synchronous-register-stage | 8 | 262144 | 131072 | 65536 | 1536 | False |
| asynchronous-direct-to-buffer | 1 | 32768 | 0 | 65536 | 1024 | True |
| asynchronous-direct-to-buffer | 2 | 65536 | 0 | 65536 | 768 | True |
| asynchronous-direct-to-buffer | 4 | 131072 | 0 | 65536 | 768 | False |
| asynchronous-direct-to-buffer | 8 | 262144 | 0 | 65536 | 768 | False |

无槽位背压参考完成于 768，达到该参考的最小枚举槽数为 2。这不是所有算法或硬件的最小缓冲要求。

## 逐块时序

| 路径/槽数 | 块 | 槽编号 | 发起 | 搬运服务结束 | 数据就绪 | 计算开始 | 计算结束/释放 |
|---|---:|---:|---:|---:|---:|---:|---:|
| synchronous-register-stage/1 | 0 | 0 | 0 | 128 | 512 | 512 | 768 |
| synchronous-register-stage/1 | 1 | 0 | 768 | 896 | 1280 | 1280 | 1536 |
| synchronous-register-stage/2 | 0 | 0 | 0 | 128 | 512 | 512 | 768 |
| synchronous-register-stage/2 | 1 | 1 | 768 | 896 | 1280 | 1280 | 1536 |
| synchronous-register-stage/4 | 0 | 0 | 0 | 128 | 512 | 512 | 768 |
| synchronous-register-stage/4 | 1 | 1 | 768 | 896 | 1280 | 1280 | 1536 |
| synchronous-register-stage/8 | 0 | 0 | 0 | 128 | 512 | 512 | 768 |
| synchronous-register-stage/8 | 1 | 1 | 768 | 896 | 1280 | 1280 | 1536 |
| asynchronous-direct-to-buffer/1 | 0 | 0 | 0 | 128 | 256 | 256 | 512 |
| asynchronous-direct-to-buffer/1 | 1 | 0 | 512 | 640 | 768 | 768 | 1024 |
| asynchronous-direct-to-buffer/2 | 0 | 0 | 0 | 128 | 256 | 256 | 512 |
| asynchronous-direct-to-buffer/2 | 1 | 1 | 128 | 256 | 384 | 512 | 768 |
| asynchronous-direct-to-buffer/4 | 0 | 0 | 0 | 128 | 256 | 256 | 512 |
| asynchronous-direct-to-buffer/4 | 1 | 1 | 128 | 256 | 384 | 512 | 768 |
| asynchronous-direct-to-buffer/8 | 0 | 0 | 0 | 128 | 256 | 256 | 512 |
| asynchronous-direct-to-buffer/8 | 1 | 1 | 128 | 256 | 384 | 512 | 768 |

## 假设与完整输入

- One rectangular QK GEMM split along real head_dim. Chunks accumulate serially into FP32 scores; no causal mask or instruction legality is inferred.
- Tick is an abstract scheduling unit, not a GPU clock measurement. All rates/latencies are declared effective inputs. Each service duration rounds up separately.
- Input issue consumes one bandwidth server for load_ticks; completion has additional latency and may overlap later issues. At most slots loads/consumers can own storage.
- Slot is acquired at issue and released at compute end, with same-tick reuse. Input is not assumed copied into hidden extra buffers before compute finishes.
- Synchronous mode serializes load, extra register ingress/egress service, and compute. Async removes that declared staging path; actual instructions/address/descriptor costs remain unmodeled.
- SMEM input capacity, register staging and FP32 accumulator capacities are separate tiers. Only SMEM capacity is screened; passing it does not prove complete resource feasibility.
- Time ends when final QK accumulator is ready. Output write, softmax/PV, launch, bank conflicts and synchronization overhead are not measured or set to zero.
- No-slot reference allocates one slot per chunk. Reported saturation is finite-workload and enumerated-slot specific, not a universal minimum.

```json
{
  "calculation": "qwen-attention-input-pipeline",
  "model": "qwen3-8b",
  "sources": [
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
    "tile_m": 128,
    "tile_n": 128,
    "tile_k": 64,
    "latency_ticks": 128,
    "input_bytes_per_tick": 256,
    "matrix_flops_per_tick": 8192,
    "register_bytes_per_tick": 256,
    "capacity_bytes": 65536
  },
  "shapes": {
    "Q": [
      128,
      128
    ],
    "K_math": [
      128,
      128
    ],
    "scores": [
      128,
      128
    ]
  },
  "chunks": 2,
  "chunk_flops": 2097152,
  "total_flops": 4194304,
  "chunk_input_bytes": 32768,
  "rows": [
    {
      "mode": "synchronous-register-stage",
      "input_slots": 1,
      "smem_reserved_bytes": 32768,
      "smem_capacity_passes": true,
      "register_staging_reserved_bytes": 32768,
      "accumulator_reserved_bytes": 65536,
      "register_interface_bytes": 131072,
      "external_input_payload_bytes": 65536,
      "timing": {
        "chunks": [
          {
            "chunk": 0,
            "slot": 0,
            "issue_start": 0,
            "transfer_end": 128,
            "data_ready": 512,
            "compute_start": 512,
            "compute_end": 768,
            "slot_released": 768,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 512
          },
          {
            "chunk": 1,
            "slot": 0,
            "issue_start": 768,
            "transfer_end": 896,
            "data_ready": 1280,
            "compute_start": 1280,
            "compute_end": 1536,
            "slot_released": 1536,
            "slot_wait_ticks": 640,
            "compute_idle_ticks": 512
          }
        ],
        "finish_tick": 1536,
        "total_compute_busy_ticks": 512,
        "total_compute_idle_ticks": 1024
      },
      "capacity_qualified_finish_tick": 1536
    },
    {
      "mode": "synchronous-register-stage",
      "input_slots": 2,
      "smem_reserved_bytes": 65536,
      "smem_capacity_passes": true,
      "register_staging_reserved_bytes": 32768,
      "accumulator_reserved_bytes": 65536,
      "register_interface_bytes": 131072,
      "external_input_payload_bytes": 65536,
      "timing": {
        "chunks": [
          {
            "chunk": 0,
            "slot": 0,
            "issue_start": 0,
            "transfer_end": 128,
            "data_ready": 512,
            "compute_start": 512,
            "compute_end": 768,
            "slot_released": 768,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 512
          },
          {
            "chunk": 1,
            "slot": 1,
            "issue_start": 768,
            "transfer_end": 896,
            "data_ready": 1280,
            "compute_start": 1280,
            "compute_end": 1536,
            "slot_released": 1536,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 512
          }
        ],
        "finish_tick": 1536,
        "total_compute_busy_ticks": 512,
        "total_compute_idle_ticks": 1024
      },
      "capacity_qualified_finish_tick": 1536
    },
    {
      "mode": "synchronous-register-stage",
      "input_slots": 4,
      "smem_reserved_bytes": 131072,
      "smem_capacity_passes": false,
      "register_staging_reserved_bytes": 32768,
      "accumulator_reserved_bytes": 65536,
      "register_interface_bytes": 131072,
      "external_input_payload_bytes": 65536,
      "timing": {
        "chunks": [
          {
            "chunk": 0,
            "slot": 0,
            "issue_start": 0,
            "transfer_end": 128,
            "data_ready": 512,
            "compute_start": 512,
            "compute_end": 768,
            "slot_released": 768,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 512
          },
          {
            "chunk": 1,
            "slot": 1,
            "issue_start": 768,
            "transfer_end": 896,
            "data_ready": 1280,
            "compute_start": 1280,
            "compute_end": 1536,
            "slot_released": 1536,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 512
          }
        ],
        "finish_tick": 1536,
        "total_compute_busy_ticks": 512,
        "total_compute_idle_ticks": 1024
      },
      "capacity_qualified_finish_tick": null
    },
    {
      "mode": "synchronous-register-stage",
      "input_slots": 8,
      "smem_reserved_bytes": 262144,
      "smem_capacity_passes": false,
      "register_staging_reserved_bytes": 32768,
      "accumulator_reserved_bytes": 65536,
      "register_interface_bytes": 131072,
      "external_input_payload_bytes": 65536,
      "timing": {
        "chunks": [
          {
            "chunk": 0,
            "slot": 0,
            "issue_start": 0,
            "transfer_end": 128,
            "data_ready": 512,
            "compute_start": 512,
            "compute_end": 768,
            "slot_released": 768,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 512
          },
          {
            "chunk": 1,
            "slot": 1,
            "issue_start": 768,
            "transfer_end": 896,
            "data_ready": 1280,
            "compute_start": 1280,
            "compute_end": 1536,
            "slot_released": 1536,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 512
          }
        ],
        "finish_tick": 1536,
        "total_compute_busy_ticks": 512,
        "total_compute_idle_ticks": 1024
      },
      "capacity_qualified_finish_tick": null
    },
    {
      "mode": "asynchronous-direct-to-buffer",
      "input_slots": 1,
      "smem_reserved_bytes": 32768,
      "smem_capacity_passes": true,
      "register_staging_reserved_bytes": 0,
      "accumulator_reserved_bytes": 65536,
      "register_interface_bytes": 0,
      "external_input_payload_bytes": 65536,
      "timing": {
        "chunks": [
          {
            "chunk": 0,
            "slot": 0,
            "issue_start": 0,
            "transfer_end": 128,
            "data_ready": 256,
            "compute_start": 256,
            "compute_end": 512,
            "slot_released": 512,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 256
          },
          {
            "chunk": 1,
            "slot": 0,
            "issue_start": 512,
            "transfer_end": 640,
            "data_ready": 768,
            "compute_start": 768,
            "compute_end": 1024,
            "slot_released": 1024,
            "slot_wait_ticks": 384,
            "compute_idle_ticks": 256
          }
        ],
        "finish_tick": 1024,
        "total_compute_busy_ticks": 512,
        "total_compute_idle_ticks": 512
      },
      "capacity_qualified_finish_tick": 1024
    },
    {
      "mode": "asynchronous-direct-to-buffer",
      "input_slots": 2,
      "smem_reserved_bytes": 65536,
      "smem_capacity_passes": true,
      "register_staging_reserved_bytes": 0,
      "accumulator_reserved_bytes": 65536,
      "register_interface_bytes": 0,
      "external_input_payload_bytes": 65536,
      "timing": {
        "chunks": [
          {
            "chunk": 0,
            "slot": 0,
            "issue_start": 0,
            "transfer_end": 128,
            "data_ready": 256,
            "compute_start": 256,
            "compute_end": 512,
            "slot_released": 512,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 256
          },
          {
            "chunk": 1,
            "slot": 1,
            "issue_start": 128,
            "transfer_end": 256,
            "data_ready": 384,
            "compute_start": 512,
            "compute_end": 768,
            "slot_released": 768,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 0
          }
        ],
        "finish_tick": 768,
        "total_compute_busy_ticks": 512,
        "total_compute_idle_ticks": 256
      },
      "capacity_qualified_finish_tick": 768
    },
    {
      "mode": "asynchronous-direct-to-buffer",
      "input_slots": 4,
      "smem_reserved_bytes": 131072,
      "smem_capacity_passes": false,
      "register_staging_reserved_bytes": 0,
      "accumulator_reserved_bytes": 65536,
      "register_interface_bytes": 0,
      "external_input_payload_bytes": 65536,
      "timing": {
        "chunks": [
          {
            "chunk": 0,
            "slot": 0,
            "issue_start": 0,
            "transfer_end": 128,
            "data_ready": 256,
            "compute_start": 256,
            "compute_end": 512,
            "slot_released": 512,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 256
          },
          {
            "chunk": 1,
            "slot": 1,
            "issue_start": 128,
            "transfer_end": 256,
            "data_ready": 384,
            "compute_start": 512,
            "compute_end": 768,
            "slot_released": 768,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 0
          }
        ],
        "finish_tick": 768,
        "total_compute_busy_ticks": 512,
        "total_compute_idle_ticks": 256
      },
      "capacity_qualified_finish_tick": null
    },
    {
      "mode": "asynchronous-direct-to-buffer",
      "input_slots": 8,
      "smem_reserved_bytes": 262144,
      "smem_capacity_passes": false,
      "register_staging_reserved_bytes": 0,
      "accumulator_reserved_bytes": 65536,
      "register_interface_bytes": 0,
      "external_input_payload_bytes": 65536,
      "timing": {
        "chunks": [
          {
            "chunk": 0,
            "slot": 0,
            "issue_start": 0,
            "transfer_end": 128,
            "data_ready": 256,
            "compute_start": 256,
            "compute_end": 512,
            "slot_released": 512,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 256
          },
          {
            "chunk": 1,
            "slot": 1,
            "issue_start": 128,
            "transfer_end": 256,
            "data_ready": 384,
            "compute_start": 512,
            "compute_end": 768,
            "slot_released": 768,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 0
          }
        ],
        "finish_tick": 768,
        "total_compute_busy_ticks": 512,
        "total_compute_idle_ticks": 256
      },
      "capacity_qualified_finish_tick": null
    }
  ],
  "no_slot_backpressure_finish_tick": 768,
  "smallest_enumerated_slots_matching_unlimited": 2,
  "fastest_capacity_qualified_async_tick": 768,
  "assumptions": [
    "One rectangular QK GEMM split along real head_dim. Chunks accumulate serially into FP32 scores; no causal mask or instruction legality is inferred.",
    "Tick is an abstract scheduling unit, not a GPU clock measurement. All rates/latencies are declared effective inputs. Each service duration rounds up separately.",
    "Input issue consumes one bandwidth server for load_ticks; completion has additional latency and may overlap later issues. At most slots loads/consumers can own storage.",
    "Slot is acquired at issue and released at compute end, with same-tick reuse. Input is not assumed copied into hidden extra buffers before compute finishes.",
    "Synchronous mode serializes load, extra register ingress/egress service, and compute. Async removes that declared staging path; actual instructions/address/descriptor costs remain unmodeled.",
    "SMEM input capacity, register staging and FP32 accumulator capacities are separate tiers. Only SMEM capacity is screened; passing it does not prove complete resource feasibility.",
    "Time ends when final QK accumulator is ready. Output write, softmax/PV, launch, bank conflicts and synchronization overhead are not measured or set to zero.",
    "No-slot reference allocates one slot per chunk. Reported saturation is finite-workload and enumerated-slot specific, not a universal minimum."
  ]
}
```
