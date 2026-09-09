# Qwen注意力输入：有限槽与异步供数

时间为声明的离散教学单位，非实测GPU周期。输入槽一直占用到本块矩阵消费结束。

| 路径 | 输入槽 | 输入SMEM bytes | 寄存器中转 bytes | FP32累加器 bytes | 完成时刻 | 输入容量通过 |
|---|---:|---:|---:|---:|---:|---|
| synchronous-register-stage | 1 | 16384 | 131072 | 65536 | 1792 | True |
| synchronous-register-stage | 2 | 32768 | 131072 | 65536 | 1792 | False |
| synchronous-register-stage | 4 | 65536 | 131072 | 65536 | 1792 | False |
| synchronous-register-stage | 8 | 131072 | 131072 | 65536 | 1792 | False |
| asynchronous-direct-to-buffer | 1 | 16384 | 0 | 65536 | 1280 | True |
| asynchronous-direct-to-buffer | 2 | 32768 | 0 | 65536 | 768 | False |
| asynchronous-direct-to-buffer | 4 | 65536 | 0 | 65536 | 704 | False |
| asynchronous-direct-to-buffer | 8 | 131072 | 0 | 65536 | 704 | False |

无槽位背压参考完成于 704，达到该参考的最小枚举槽数为 4。这不是所有算法或硬件的最小缓冲要求。

## 逐块时序

| 路径/槽数 | 块 | 槽编号 | 发起 | 搬运服务结束 | 数据就绪 | 计算开始 | 计算结束/释放 |
|---|---:|---:|---:|---:|---:|---:|---:|
| synchronous-register-stage/1 | 0 | 0 | 0 | 64 | 320 | 320 | 448 |
| synchronous-register-stage/1 | 1 | 0 | 448 | 512 | 768 | 768 | 896 |
| synchronous-register-stage/1 | 2 | 0 | 896 | 960 | 1216 | 1216 | 1344 |
| synchronous-register-stage/1 | 3 | 0 | 1344 | 1408 | 1664 | 1664 | 1792 |
| synchronous-register-stage/2 | 0 | 0 | 0 | 64 | 320 | 320 | 448 |
| synchronous-register-stage/2 | 1 | 1 | 448 | 512 | 768 | 768 | 896 |
| synchronous-register-stage/2 | 2 | 0 | 896 | 960 | 1216 | 1216 | 1344 |
| synchronous-register-stage/2 | 3 | 1 | 1344 | 1408 | 1664 | 1664 | 1792 |
| synchronous-register-stage/4 | 0 | 0 | 0 | 64 | 320 | 320 | 448 |
| synchronous-register-stage/4 | 1 | 1 | 448 | 512 | 768 | 768 | 896 |
| synchronous-register-stage/4 | 2 | 2 | 896 | 960 | 1216 | 1216 | 1344 |
| synchronous-register-stage/4 | 3 | 3 | 1344 | 1408 | 1664 | 1664 | 1792 |
| synchronous-register-stage/8 | 0 | 0 | 0 | 64 | 320 | 320 | 448 |
| synchronous-register-stage/8 | 1 | 1 | 448 | 512 | 768 | 768 | 896 |
| synchronous-register-stage/8 | 2 | 2 | 896 | 960 | 1216 | 1216 | 1344 |
| synchronous-register-stage/8 | 3 | 3 | 1344 | 1408 | 1664 | 1664 | 1792 |
| asynchronous-direct-to-buffer/1 | 0 | 0 | 0 | 64 | 192 | 192 | 320 |
| asynchronous-direct-to-buffer/1 | 1 | 0 | 320 | 384 | 512 | 512 | 640 |
| asynchronous-direct-to-buffer/1 | 2 | 0 | 640 | 704 | 832 | 832 | 960 |
| asynchronous-direct-to-buffer/1 | 3 | 0 | 960 | 1024 | 1152 | 1152 | 1280 |
| asynchronous-direct-to-buffer/2 | 0 | 0 | 0 | 64 | 192 | 192 | 320 |
| asynchronous-direct-to-buffer/2 | 1 | 1 | 64 | 128 | 256 | 320 | 448 |
| asynchronous-direct-to-buffer/2 | 2 | 0 | 320 | 384 | 512 | 512 | 640 |
| asynchronous-direct-to-buffer/2 | 3 | 1 | 448 | 512 | 640 | 640 | 768 |
| asynchronous-direct-to-buffer/4 | 0 | 0 | 0 | 64 | 192 | 192 | 320 |
| asynchronous-direct-to-buffer/4 | 1 | 1 | 64 | 128 | 256 | 320 | 448 |
| asynchronous-direct-to-buffer/4 | 2 | 2 | 128 | 192 | 320 | 448 | 576 |
| asynchronous-direct-to-buffer/4 | 3 | 3 | 192 | 256 | 384 | 576 | 704 |
| asynchronous-direct-to-buffer/8 | 0 | 0 | 0 | 64 | 192 | 192 | 320 |
| asynchronous-direct-to-buffer/8 | 1 | 1 | 64 | 128 | 256 | 320 | 448 |
| asynchronous-direct-to-buffer/8 | 2 | 2 | 128 | 192 | 320 | 448 | 576 |
| asynchronous-direct-to-buffer/8 | 3 | 3 | 192 | 256 | 384 | 576 | 704 |

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
    "tile_k": 32,
    "latency_ticks": 128,
    "input_bytes_per_tick": 256,
    "matrix_flops_per_tick": 8192,
    "register_bytes_per_tick": 256,
    "capacity_bytes": 16384
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
  "chunks": 4,
  "chunk_flops": 1048576,
  "total_flops": 4194304,
  "chunk_input_bytes": 16384,
  "rows": [
    {
      "mode": "synchronous-register-stage",
      "input_slots": 1,
      "smem_reserved_bytes": 16384,
      "smem_capacity_passes": true,
      "register_staging_reserved_bytes": 16384,
      "accumulator_reserved_bytes": 65536,
      "register_interface_bytes": 131072,
      "external_input_payload_bytes": 65536,
      "timing": {
        "chunks": [
          {
            "chunk": 0,
            "slot": 0,
            "issue_start": 0,
            "transfer_end": 64,
            "data_ready": 320,
            "compute_start": 320,
            "compute_end": 448,
            "slot_released": 448,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 320
          },
          {
            "chunk": 1,
            "slot": 0,
            "issue_start": 448,
            "transfer_end": 512,
            "data_ready": 768,
            "compute_start": 768,
            "compute_end": 896,
            "slot_released": 896,
            "slot_wait_ticks": 384,
            "compute_idle_ticks": 320
          },
          {
            "chunk": 2,
            "slot": 0,
            "issue_start": 896,
            "transfer_end": 960,
            "data_ready": 1216,
            "compute_start": 1216,
            "compute_end": 1344,
            "slot_released": 1344,
            "slot_wait_ticks": 384,
            "compute_idle_ticks": 320
          },
          {
            "chunk": 3,
            "slot": 0,
            "issue_start": 1344,
            "transfer_end": 1408,
            "data_ready": 1664,
            "compute_start": 1664,
            "compute_end": 1792,
            "slot_released": 1792,
            "slot_wait_ticks": 384,
            "compute_idle_ticks": 320
          }
        ],
        "finish_tick": 1792,
        "total_compute_busy_ticks": 512,
        "total_compute_idle_ticks": 1280
      },
      "capacity_qualified_finish_tick": 1792
    },
    {
      "mode": "synchronous-register-stage",
      "input_slots": 2,
      "smem_reserved_bytes": 32768,
      "smem_capacity_passes": false,
      "register_staging_reserved_bytes": 16384,
      "accumulator_reserved_bytes": 65536,
      "register_interface_bytes": 131072,
      "external_input_payload_bytes": 65536,
      "timing": {
        "chunks": [
          {
            "chunk": 0,
            "slot": 0,
            "issue_start": 0,
            "transfer_end": 64,
            "data_ready": 320,
            "compute_start": 320,
            "compute_end": 448,
            "slot_released": 448,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 320
          },
          {
            "chunk": 1,
            "slot": 1,
            "issue_start": 448,
            "transfer_end": 512,
            "data_ready": 768,
            "compute_start": 768,
            "compute_end": 896,
            "slot_released": 896,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 320
          },
          {
            "chunk": 2,
            "slot": 0,
            "issue_start": 896,
            "transfer_end": 960,
            "data_ready": 1216,
            "compute_start": 1216,
            "compute_end": 1344,
            "slot_released": 1344,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 320
          },
          {
            "chunk": 3,
            "slot": 1,
            "issue_start": 1344,
            "transfer_end": 1408,
            "data_ready": 1664,
            "compute_start": 1664,
            "compute_end": 1792,
            "slot_released": 1792,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 320
          }
        ],
        "finish_tick": 1792,
        "total_compute_busy_ticks": 512,
        "total_compute_idle_ticks": 1280
      },
      "capacity_qualified_finish_tick": null
    },
    {
      "mode": "synchronous-register-stage",
      "input_slots": 4,
      "smem_reserved_bytes": 65536,
      "smem_capacity_passes": false,
      "register_staging_reserved_bytes": 16384,
      "accumulator_reserved_bytes": 65536,
      "register_interface_bytes": 131072,
      "external_input_payload_bytes": 65536,
      "timing": {
        "chunks": [
          {
            "chunk": 0,
            "slot": 0,
            "issue_start": 0,
            "transfer_end": 64,
            "data_ready": 320,
            "compute_start": 320,
            "compute_end": 448,
            "slot_released": 448,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 320
          },
          {
            "chunk": 1,
            "slot": 1,
            "issue_start": 448,
            "transfer_end": 512,
            "data_ready": 768,
            "compute_start": 768,
            "compute_end": 896,
            "slot_released": 896,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 320
          },
          {
            "chunk": 2,
            "slot": 2,
            "issue_start": 896,
            "transfer_end": 960,
            "data_ready": 1216,
            "compute_start": 1216,
            "compute_end": 1344,
            "slot_released": 1344,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 320
          },
          {
            "chunk": 3,
            "slot": 3,
            "issue_start": 1344,
            "transfer_end": 1408,
            "data_ready": 1664,
            "compute_start": 1664,
            "compute_end": 1792,
            "slot_released": 1792,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 320
          }
        ],
        "finish_tick": 1792,
        "total_compute_busy_ticks": 512,
        "total_compute_idle_ticks": 1280
      },
      "capacity_qualified_finish_tick": null
    },
    {
      "mode": "synchronous-register-stage",
      "input_slots": 8,
      "smem_reserved_bytes": 131072,
      "smem_capacity_passes": false,
      "register_staging_reserved_bytes": 16384,
      "accumulator_reserved_bytes": 65536,
      "register_interface_bytes": 131072,
      "external_input_payload_bytes": 65536,
      "timing": {
        "chunks": [
          {
            "chunk": 0,
            "slot": 0,
            "issue_start": 0,
            "transfer_end": 64,
            "data_ready": 320,
            "compute_start": 320,
            "compute_end": 448,
            "slot_released": 448,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 320
          },
          {
            "chunk": 1,
            "slot": 1,
            "issue_start": 448,
            "transfer_end": 512,
            "data_ready": 768,
            "compute_start": 768,
            "compute_end": 896,
            "slot_released": 896,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 320
          },
          {
            "chunk": 2,
            "slot": 2,
            "issue_start": 896,
            "transfer_end": 960,
            "data_ready": 1216,
            "compute_start": 1216,
            "compute_end": 1344,
            "slot_released": 1344,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 320
          },
          {
            "chunk": 3,
            "slot": 3,
            "issue_start": 1344,
            "transfer_end": 1408,
            "data_ready": 1664,
            "compute_start": 1664,
            "compute_end": 1792,
            "slot_released": 1792,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 320
          }
        ],
        "finish_tick": 1792,
        "total_compute_busy_ticks": 512,
        "total_compute_idle_ticks": 1280
      },
      "capacity_qualified_finish_tick": null
    },
    {
      "mode": "asynchronous-direct-to-buffer",
      "input_slots": 1,
      "smem_reserved_bytes": 16384,
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
            "transfer_end": 64,
            "data_ready": 192,
            "compute_start": 192,
            "compute_end": 320,
            "slot_released": 320,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 192
          },
          {
            "chunk": 1,
            "slot": 0,
            "issue_start": 320,
            "transfer_end": 384,
            "data_ready": 512,
            "compute_start": 512,
            "compute_end": 640,
            "slot_released": 640,
            "slot_wait_ticks": 256,
            "compute_idle_ticks": 192
          },
          {
            "chunk": 2,
            "slot": 0,
            "issue_start": 640,
            "transfer_end": 704,
            "data_ready": 832,
            "compute_start": 832,
            "compute_end": 960,
            "slot_released": 960,
            "slot_wait_ticks": 256,
            "compute_idle_ticks": 192
          },
          {
            "chunk": 3,
            "slot": 0,
            "issue_start": 960,
            "transfer_end": 1024,
            "data_ready": 1152,
            "compute_start": 1152,
            "compute_end": 1280,
            "slot_released": 1280,
            "slot_wait_ticks": 256,
            "compute_idle_ticks": 192
          }
        ],
        "finish_tick": 1280,
        "total_compute_busy_ticks": 512,
        "total_compute_idle_ticks": 768
      },
      "capacity_qualified_finish_tick": 1280
    },
    {
      "mode": "asynchronous-direct-to-buffer",
      "input_slots": 2,
      "smem_reserved_bytes": 32768,
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
            "transfer_end": 64,
            "data_ready": 192,
            "compute_start": 192,
            "compute_end": 320,
            "slot_released": 320,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 192
          },
          {
            "chunk": 1,
            "slot": 1,
            "issue_start": 64,
            "transfer_end": 128,
            "data_ready": 256,
            "compute_start": 320,
            "compute_end": 448,
            "slot_released": 448,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 0
          },
          {
            "chunk": 2,
            "slot": 0,
            "issue_start": 320,
            "transfer_end": 384,
            "data_ready": 512,
            "compute_start": 512,
            "compute_end": 640,
            "slot_released": 640,
            "slot_wait_ticks": 192,
            "compute_idle_ticks": 64
          },
          {
            "chunk": 3,
            "slot": 1,
            "issue_start": 448,
            "transfer_end": 512,
            "data_ready": 640,
            "compute_start": 640,
            "compute_end": 768,
            "slot_released": 768,
            "slot_wait_ticks": 64,
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
      "input_slots": 4,
      "smem_reserved_bytes": 65536,
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
            "transfer_end": 64,
            "data_ready": 192,
            "compute_start": 192,
            "compute_end": 320,
            "slot_released": 320,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 192
          },
          {
            "chunk": 1,
            "slot": 1,
            "issue_start": 64,
            "transfer_end": 128,
            "data_ready": 256,
            "compute_start": 320,
            "compute_end": 448,
            "slot_released": 448,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 0
          },
          {
            "chunk": 2,
            "slot": 2,
            "issue_start": 128,
            "transfer_end": 192,
            "data_ready": 320,
            "compute_start": 448,
            "compute_end": 576,
            "slot_released": 576,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 0
          },
          {
            "chunk": 3,
            "slot": 3,
            "issue_start": 192,
            "transfer_end": 256,
            "data_ready": 384,
            "compute_start": 576,
            "compute_end": 704,
            "slot_released": 704,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 0
          }
        ],
        "finish_tick": 704,
        "total_compute_busy_ticks": 512,
        "total_compute_idle_ticks": 192
      },
      "capacity_qualified_finish_tick": null
    },
    {
      "mode": "asynchronous-direct-to-buffer",
      "input_slots": 8,
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
            "transfer_end": 64,
            "data_ready": 192,
            "compute_start": 192,
            "compute_end": 320,
            "slot_released": 320,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 192
          },
          {
            "chunk": 1,
            "slot": 1,
            "issue_start": 64,
            "transfer_end": 128,
            "data_ready": 256,
            "compute_start": 320,
            "compute_end": 448,
            "slot_released": 448,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 0
          },
          {
            "chunk": 2,
            "slot": 2,
            "issue_start": 128,
            "transfer_end": 192,
            "data_ready": 320,
            "compute_start": 448,
            "compute_end": 576,
            "slot_released": 576,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 0
          },
          {
            "chunk": 3,
            "slot": 3,
            "issue_start": 192,
            "transfer_end": 256,
            "data_ready": 384,
            "compute_start": 576,
            "compute_end": 704,
            "slot_released": 704,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 0
          }
        ],
        "finish_tick": 704,
        "total_compute_busy_ticks": 512,
        "total_compute_idle_ticks": 192
      },
      "capacity_qualified_finish_tick": null
    }
  ],
  "no_slot_backpressure_finish_tick": 704,
  "smallest_enumerated_slots_matching_unlimited": 4,
  "fastest_capacity_qualified_async_tick": 1280,
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
