# Qwen注意力输入：有限槽与异步供数

时间为声明的离散教学单位，非实测GPU周期。输入槽一直占用到本块矩阵消费结束。

| 路径 | 输入槽 | 输入SMEM bytes | 寄存器中转 bytes | FP32累加器 bytes | 完成时刻 | 输入容量通过 |
|---|---:|---:|---:|---:|---:|---|
| synchronous-register-stage | 1 | 16384 | 131072 | 65536 | 3328 | True |
| synchronous-register-stage | 2 | 32768 | 131072 | 65536 | 3328 | True |
| synchronous-register-stage | 4 | 65536 | 131072 | 65536 | 3328 | True |
| synchronous-register-stage | 8 | 131072 | 131072 | 65536 | 3328 | False |
| asynchronous-direct-to-buffer | 1 | 16384 | 0 | 65536 | 2816 | True |
| asynchronous-direct-to-buffer | 2 | 32768 | 0 | 65536 | 1536 | True |
| asynchronous-direct-to-buffer | 4 | 65536 | 0 | 65536 | 1088 | True |
| asynchronous-direct-to-buffer | 8 | 131072 | 0 | 65536 | 1088 | False |

无槽位背压参考完成于 1088，达到该参考的最小枚举槽数为 4。这不是所有算法或硬件的最小缓冲要求。

## 逐块时序

| 路径/槽数 | 块 | 槽编号 | 发起 | 搬运服务结束 | 数据就绪 | 计算开始 | 计算结束/释放 |
|---|---:|---:|---:|---:|---:|---:|---:|
| synchronous-register-stage/1 | 0 | 0 | 0 | 64 | 704 | 704 | 832 |
| synchronous-register-stage/1 | 1 | 0 | 832 | 896 | 1536 | 1536 | 1664 |
| synchronous-register-stage/1 | 2 | 0 | 1664 | 1728 | 2368 | 2368 | 2496 |
| synchronous-register-stage/1 | 3 | 0 | 2496 | 2560 | 3200 | 3200 | 3328 |
| synchronous-register-stage/2 | 0 | 0 | 0 | 64 | 704 | 704 | 832 |
| synchronous-register-stage/2 | 1 | 1 | 832 | 896 | 1536 | 1536 | 1664 |
| synchronous-register-stage/2 | 2 | 0 | 1664 | 1728 | 2368 | 2368 | 2496 |
| synchronous-register-stage/2 | 3 | 1 | 2496 | 2560 | 3200 | 3200 | 3328 |
| synchronous-register-stage/4 | 0 | 0 | 0 | 64 | 704 | 704 | 832 |
| synchronous-register-stage/4 | 1 | 1 | 832 | 896 | 1536 | 1536 | 1664 |
| synchronous-register-stage/4 | 2 | 2 | 1664 | 1728 | 2368 | 2368 | 2496 |
| synchronous-register-stage/4 | 3 | 3 | 2496 | 2560 | 3200 | 3200 | 3328 |
| synchronous-register-stage/8 | 0 | 0 | 0 | 64 | 704 | 704 | 832 |
| synchronous-register-stage/8 | 1 | 1 | 832 | 896 | 1536 | 1536 | 1664 |
| synchronous-register-stage/8 | 2 | 2 | 1664 | 1728 | 2368 | 2368 | 2496 |
| synchronous-register-stage/8 | 3 | 3 | 2496 | 2560 | 3200 | 3200 | 3328 |
| asynchronous-direct-to-buffer/1 | 0 | 0 | 0 | 64 | 576 | 576 | 704 |
| asynchronous-direct-to-buffer/1 | 1 | 0 | 704 | 768 | 1280 | 1280 | 1408 |
| asynchronous-direct-to-buffer/1 | 2 | 0 | 1408 | 1472 | 1984 | 1984 | 2112 |
| asynchronous-direct-to-buffer/1 | 3 | 0 | 2112 | 2176 | 2688 | 2688 | 2816 |
| asynchronous-direct-to-buffer/2 | 0 | 0 | 0 | 64 | 576 | 576 | 704 |
| asynchronous-direct-to-buffer/2 | 1 | 1 | 64 | 128 | 640 | 704 | 832 |
| asynchronous-direct-to-buffer/2 | 2 | 0 | 704 | 768 | 1280 | 1280 | 1408 |
| asynchronous-direct-to-buffer/2 | 3 | 1 | 832 | 896 | 1408 | 1408 | 1536 |
| asynchronous-direct-to-buffer/4 | 0 | 0 | 0 | 64 | 576 | 576 | 704 |
| asynchronous-direct-to-buffer/4 | 1 | 1 | 64 | 128 | 640 | 704 | 832 |
| asynchronous-direct-to-buffer/4 | 2 | 2 | 128 | 192 | 704 | 832 | 960 |
| asynchronous-direct-to-buffer/4 | 3 | 3 | 192 | 256 | 768 | 960 | 1088 |
| asynchronous-direct-to-buffer/8 | 0 | 0 | 0 | 64 | 576 | 576 | 704 |
| asynchronous-direct-to-buffer/8 | 1 | 1 | 64 | 128 | 640 | 704 | 832 |
| asynchronous-direct-to-buffer/8 | 2 | 2 | 128 | 192 | 704 | 832 | 960 |
| asynchronous-direct-to-buffer/8 | 3 | 3 | 192 | 256 | 768 | 960 | 1088 |

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
    "latency_ticks": 512,
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
            "data_ready": 704,
            "compute_start": 704,
            "compute_end": 832,
            "slot_released": 832,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 704
          },
          {
            "chunk": 1,
            "slot": 0,
            "issue_start": 832,
            "transfer_end": 896,
            "data_ready": 1536,
            "compute_start": 1536,
            "compute_end": 1664,
            "slot_released": 1664,
            "slot_wait_ticks": 768,
            "compute_idle_ticks": 704
          },
          {
            "chunk": 2,
            "slot": 0,
            "issue_start": 1664,
            "transfer_end": 1728,
            "data_ready": 2368,
            "compute_start": 2368,
            "compute_end": 2496,
            "slot_released": 2496,
            "slot_wait_ticks": 768,
            "compute_idle_ticks": 704
          },
          {
            "chunk": 3,
            "slot": 0,
            "issue_start": 2496,
            "transfer_end": 2560,
            "data_ready": 3200,
            "compute_start": 3200,
            "compute_end": 3328,
            "slot_released": 3328,
            "slot_wait_ticks": 768,
            "compute_idle_ticks": 704
          }
        ],
        "finish_tick": 3328,
        "total_compute_busy_ticks": 512,
        "total_compute_idle_ticks": 2816
      },
      "capacity_qualified_finish_tick": 3328
    },
    {
      "mode": "synchronous-register-stage",
      "input_slots": 2,
      "smem_reserved_bytes": 32768,
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
            "data_ready": 704,
            "compute_start": 704,
            "compute_end": 832,
            "slot_released": 832,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 704
          },
          {
            "chunk": 1,
            "slot": 1,
            "issue_start": 832,
            "transfer_end": 896,
            "data_ready": 1536,
            "compute_start": 1536,
            "compute_end": 1664,
            "slot_released": 1664,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 704
          },
          {
            "chunk": 2,
            "slot": 0,
            "issue_start": 1664,
            "transfer_end": 1728,
            "data_ready": 2368,
            "compute_start": 2368,
            "compute_end": 2496,
            "slot_released": 2496,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 704
          },
          {
            "chunk": 3,
            "slot": 1,
            "issue_start": 2496,
            "transfer_end": 2560,
            "data_ready": 3200,
            "compute_start": 3200,
            "compute_end": 3328,
            "slot_released": 3328,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 704
          }
        ],
        "finish_tick": 3328,
        "total_compute_busy_ticks": 512,
        "total_compute_idle_ticks": 2816
      },
      "capacity_qualified_finish_tick": 3328
    },
    {
      "mode": "synchronous-register-stage",
      "input_slots": 4,
      "smem_reserved_bytes": 65536,
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
            "data_ready": 704,
            "compute_start": 704,
            "compute_end": 832,
            "slot_released": 832,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 704
          },
          {
            "chunk": 1,
            "slot": 1,
            "issue_start": 832,
            "transfer_end": 896,
            "data_ready": 1536,
            "compute_start": 1536,
            "compute_end": 1664,
            "slot_released": 1664,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 704
          },
          {
            "chunk": 2,
            "slot": 2,
            "issue_start": 1664,
            "transfer_end": 1728,
            "data_ready": 2368,
            "compute_start": 2368,
            "compute_end": 2496,
            "slot_released": 2496,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 704
          },
          {
            "chunk": 3,
            "slot": 3,
            "issue_start": 2496,
            "transfer_end": 2560,
            "data_ready": 3200,
            "compute_start": 3200,
            "compute_end": 3328,
            "slot_released": 3328,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 704
          }
        ],
        "finish_tick": 3328,
        "total_compute_busy_ticks": 512,
        "total_compute_idle_ticks": 2816
      },
      "capacity_qualified_finish_tick": 3328
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
            "data_ready": 704,
            "compute_start": 704,
            "compute_end": 832,
            "slot_released": 832,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 704
          },
          {
            "chunk": 1,
            "slot": 1,
            "issue_start": 832,
            "transfer_end": 896,
            "data_ready": 1536,
            "compute_start": 1536,
            "compute_end": 1664,
            "slot_released": 1664,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 704
          },
          {
            "chunk": 2,
            "slot": 2,
            "issue_start": 1664,
            "transfer_end": 1728,
            "data_ready": 2368,
            "compute_start": 2368,
            "compute_end": 2496,
            "slot_released": 2496,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 704
          },
          {
            "chunk": 3,
            "slot": 3,
            "issue_start": 2496,
            "transfer_end": 2560,
            "data_ready": 3200,
            "compute_start": 3200,
            "compute_end": 3328,
            "slot_released": 3328,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 704
          }
        ],
        "finish_tick": 3328,
        "total_compute_busy_ticks": 512,
        "total_compute_idle_ticks": 2816
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
            "data_ready": 576,
            "compute_start": 576,
            "compute_end": 704,
            "slot_released": 704,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 576
          },
          {
            "chunk": 1,
            "slot": 0,
            "issue_start": 704,
            "transfer_end": 768,
            "data_ready": 1280,
            "compute_start": 1280,
            "compute_end": 1408,
            "slot_released": 1408,
            "slot_wait_ticks": 640,
            "compute_idle_ticks": 576
          },
          {
            "chunk": 2,
            "slot": 0,
            "issue_start": 1408,
            "transfer_end": 1472,
            "data_ready": 1984,
            "compute_start": 1984,
            "compute_end": 2112,
            "slot_released": 2112,
            "slot_wait_ticks": 640,
            "compute_idle_ticks": 576
          },
          {
            "chunk": 3,
            "slot": 0,
            "issue_start": 2112,
            "transfer_end": 2176,
            "data_ready": 2688,
            "compute_start": 2688,
            "compute_end": 2816,
            "slot_released": 2816,
            "slot_wait_ticks": 640,
            "compute_idle_ticks": 576
          }
        ],
        "finish_tick": 2816,
        "total_compute_busy_ticks": 512,
        "total_compute_idle_ticks": 2304
      },
      "capacity_qualified_finish_tick": 2816
    },
    {
      "mode": "asynchronous-direct-to-buffer",
      "input_slots": 2,
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
            "transfer_end": 64,
            "data_ready": 576,
            "compute_start": 576,
            "compute_end": 704,
            "slot_released": 704,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 576
          },
          {
            "chunk": 1,
            "slot": 1,
            "issue_start": 64,
            "transfer_end": 128,
            "data_ready": 640,
            "compute_start": 704,
            "compute_end": 832,
            "slot_released": 832,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 0
          },
          {
            "chunk": 2,
            "slot": 0,
            "issue_start": 704,
            "transfer_end": 768,
            "data_ready": 1280,
            "compute_start": 1280,
            "compute_end": 1408,
            "slot_released": 1408,
            "slot_wait_ticks": 576,
            "compute_idle_ticks": 448
          },
          {
            "chunk": 3,
            "slot": 1,
            "issue_start": 832,
            "transfer_end": 896,
            "data_ready": 1408,
            "compute_start": 1408,
            "compute_end": 1536,
            "slot_released": 1536,
            "slot_wait_ticks": 64,
            "compute_idle_ticks": 0
          }
        ],
        "finish_tick": 1536,
        "total_compute_busy_ticks": 512,
        "total_compute_idle_ticks": 1024
      },
      "capacity_qualified_finish_tick": 1536
    },
    {
      "mode": "asynchronous-direct-to-buffer",
      "input_slots": 4,
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
            "transfer_end": 64,
            "data_ready": 576,
            "compute_start": 576,
            "compute_end": 704,
            "slot_released": 704,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 576
          },
          {
            "chunk": 1,
            "slot": 1,
            "issue_start": 64,
            "transfer_end": 128,
            "data_ready": 640,
            "compute_start": 704,
            "compute_end": 832,
            "slot_released": 832,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 0
          },
          {
            "chunk": 2,
            "slot": 2,
            "issue_start": 128,
            "transfer_end": 192,
            "data_ready": 704,
            "compute_start": 832,
            "compute_end": 960,
            "slot_released": 960,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 0
          },
          {
            "chunk": 3,
            "slot": 3,
            "issue_start": 192,
            "transfer_end": 256,
            "data_ready": 768,
            "compute_start": 960,
            "compute_end": 1088,
            "slot_released": 1088,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 0
          }
        ],
        "finish_tick": 1088,
        "total_compute_busy_ticks": 512,
        "total_compute_idle_ticks": 576
      },
      "capacity_qualified_finish_tick": 1088
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
            "data_ready": 576,
            "compute_start": 576,
            "compute_end": 704,
            "slot_released": 704,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 576
          },
          {
            "chunk": 1,
            "slot": 1,
            "issue_start": 64,
            "transfer_end": 128,
            "data_ready": 640,
            "compute_start": 704,
            "compute_end": 832,
            "slot_released": 832,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 0
          },
          {
            "chunk": 2,
            "slot": 2,
            "issue_start": 128,
            "transfer_end": 192,
            "data_ready": 704,
            "compute_start": 832,
            "compute_end": 960,
            "slot_released": 960,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 0
          },
          {
            "chunk": 3,
            "slot": 3,
            "issue_start": 192,
            "transfer_end": 256,
            "data_ready": 768,
            "compute_start": 960,
            "compute_end": 1088,
            "slot_released": 1088,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 0
          }
        ],
        "finish_tick": 1088,
        "total_compute_busy_ticks": 512,
        "total_compute_idle_ticks": 576
      },
      "capacity_qualified_finish_tick": null
    }
  ],
  "no_slot_backpressure_finish_tick": 1088,
  "smallest_enumerated_slots_matching_unlimited": 4,
  "fastest_capacity_qualified_async_tick": 1088,
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
