# Qwen注意力输入：有限槽与异步供数

时间为声明的离散教学单位，非实测GPU周期。输入槽一直占用到本块矩阵消费结束。

| 路径 | 输入槽 | 输入SMEM bytes | 寄存器中转 bytes | FP32累加器 bytes | 完成时刻 | 输入容量通过 |
|---|---:|---:|---:|---:|---:|---|
| synchronous-register-stage | 1 | 8192 | 131072 | 65536 | 2304 | True |
| synchronous-register-stage | 2 | 16384 | 131072 | 65536 | 2304 | True |
| synchronous-register-stage | 4 | 32768 | 131072 | 65536 | 2304 | True |
| synchronous-register-stage | 8 | 65536 | 131072 | 65536 | 2304 | True |
| asynchronous-direct-to-buffer | 1 | 8192 | 0 | 65536 | 1792 | True |
| asynchronous-direct-to-buffer | 2 | 16384 | 0 | 65536 | 960 | True |
| asynchronous-direct-to-buffer | 4 | 32768 | 0 | 65536 | 672 | True |
| asynchronous-direct-to-buffer | 8 | 65536 | 0 | 65536 | 672 | True |

无槽位背压参考完成于 672，达到该参考的最小枚举槽数为 4。这不是所有算法或硬件的最小缓冲要求。

## 逐块时序

| 路径/槽数 | 块 | 槽编号 | 发起 | 搬运服务结束 | 数据就绪 | 计算开始 | 计算结束/释放 |
|---|---:|---:|---:|---:|---:|---:|---:|
| synchronous-register-stage/1 | 0 | 0 | 0 | 32 | 224 | 224 | 288 |
| synchronous-register-stage/1 | 1 | 0 | 288 | 320 | 512 | 512 | 576 |
| synchronous-register-stage/1 | 2 | 0 | 576 | 608 | 800 | 800 | 864 |
| synchronous-register-stage/1 | 3 | 0 | 864 | 896 | 1088 | 1088 | 1152 |
| synchronous-register-stage/1 | 4 | 0 | 1152 | 1184 | 1376 | 1376 | 1440 |
| synchronous-register-stage/1 | 5 | 0 | 1440 | 1472 | 1664 | 1664 | 1728 |
| synchronous-register-stage/1 | 6 | 0 | 1728 | 1760 | 1952 | 1952 | 2016 |
| synchronous-register-stage/1 | 7 | 0 | 2016 | 2048 | 2240 | 2240 | 2304 |
| synchronous-register-stage/2 | 0 | 0 | 0 | 32 | 224 | 224 | 288 |
| synchronous-register-stage/2 | 1 | 1 | 288 | 320 | 512 | 512 | 576 |
| synchronous-register-stage/2 | 2 | 0 | 576 | 608 | 800 | 800 | 864 |
| synchronous-register-stage/2 | 3 | 1 | 864 | 896 | 1088 | 1088 | 1152 |
| synchronous-register-stage/2 | 4 | 0 | 1152 | 1184 | 1376 | 1376 | 1440 |
| synchronous-register-stage/2 | 5 | 1 | 1440 | 1472 | 1664 | 1664 | 1728 |
| synchronous-register-stage/2 | 6 | 0 | 1728 | 1760 | 1952 | 1952 | 2016 |
| synchronous-register-stage/2 | 7 | 1 | 2016 | 2048 | 2240 | 2240 | 2304 |
| synchronous-register-stage/4 | 0 | 0 | 0 | 32 | 224 | 224 | 288 |
| synchronous-register-stage/4 | 1 | 1 | 288 | 320 | 512 | 512 | 576 |
| synchronous-register-stage/4 | 2 | 2 | 576 | 608 | 800 | 800 | 864 |
| synchronous-register-stage/4 | 3 | 3 | 864 | 896 | 1088 | 1088 | 1152 |
| synchronous-register-stage/4 | 4 | 0 | 1152 | 1184 | 1376 | 1376 | 1440 |
| synchronous-register-stage/4 | 5 | 1 | 1440 | 1472 | 1664 | 1664 | 1728 |
| synchronous-register-stage/4 | 6 | 2 | 1728 | 1760 | 1952 | 1952 | 2016 |
| synchronous-register-stage/4 | 7 | 3 | 2016 | 2048 | 2240 | 2240 | 2304 |
| synchronous-register-stage/8 | 0 | 0 | 0 | 32 | 224 | 224 | 288 |
| synchronous-register-stage/8 | 1 | 1 | 288 | 320 | 512 | 512 | 576 |
| synchronous-register-stage/8 | 2 | 2 | 576 | 608 | 800 | 800 | 864 |
| synchronous-register-stage/8 | 3 | 3 | 864 | 896 | 1088 | 1088 | 1152 |
| synchronous-register-stage/8 | 4 | 4 | 1152 | 1184 | 1376 | 1376 | 1440 |
| synchronous-register-stage/8 | 5 | 5 | 1440 | 1472 | 1664 | 1664 | 1728 |
| synchronous-register-stage/8 | 6 | 6 | 1728 | 1760 | 1952 | 1952 | 2016 |
| synchronous-register-stage/8 | 7 | 7 | 2016 | 2048 | 2240 | 2240 | 2304 |
| asynchronous-direct-to-buffer/1 | 0 | 0 | 0 | 32 | 160 | 160 | 224 |
| asynchronous-direct-to-buffer/1 | 1 | 0 | 224 | 256 | 384 | 384 | 448 |
| asynchronous-direct-to-buffer/1 | 2 | 0 | 448 | 480 | 608 | 608 | 672 |
| asynchronous-direct-to-buffer/1 | 3 | 0 | 672 | 704 | 832 | 832 | 896 |
| asynchronous-direct-to-buffer/1 | 4 | 0 | 896 | 928 | 1056 | 1056 | 1120 |
| asynchronous-direct-to-buffer/1 | 5 | 0 | 1120 | 1152 | 1280 | 1280 | 1344 |
| asynchronous-direct-to-buffer/1 | 6 | 0 | 1344 | 1376 | 1504 | 1504 | 1568 |
| asynchronous-direct-to-buffer/1 | 7 | 0 | 1568 | 1600 | 1728 | 1728 | 1792 |
| asynchronous-direct-to-buffer/2 | 0 | 0 | 0 | 32 | 160 | 160 | 224 |
| asynchronous-direct-to-buffer/2 | 1 | 1 | 32 | 64 | 192 | 224 | 288 |
| asynchronous-direct-to-buffer/2 | 2 | 0 | 224 | 256 | 384 | 384 | 448 |
| asynchronous-direct-to-buffer/2 | 3 | 1 | 288 | 320 | 448 | 448 | 512 |
| asynchronous-direct-to-buffer/2 | 4 | 0 | 448 | 480 | 608 | 608 | 672 |
| asynchronous-direct-to-buffer/2 | 5 | 1 | 512 | 544 | 672 | 672 | 736 |
| asynchronous-direct-to-buffer/2 | 6 | 0 | 672 | 704 | 832 | 832 | 896 |
| asynchronous-direct-to-buffer/2 | 7 | 1 | 736 | 768 | 896 | 896 | 960 |
| asynchronous-direct-to-buffer/4 | 0 | 0 | 0 | 32 | 160 | 160 | 224 |
| asynchronous-direct-to-buffer/4 | 1 | 1 | 32 | 64 | 192 | 224 | 288 |
| asynchronous-direct-to-buffer/4 | 2 | 2 | 64 | 96 | 224 | 288 | 352 |
| asynchronous-direct-to-buffer/4 | 3 | 3 | 96 | 128 | 256 | 352 | 416 |
| asynchronous-direct-to-buffer/4 | 4 | 0 | 224 | 256 | 384 | 416 | 480 |
| asynchronous-direct-to-buffer/4 | 5 | 1 | 288 | 320 | 448 | 480 | 544 |
| asynchronous-direct-to-buffer/4 | 6 | 2 | 352 | 384 | 512 | 544 | 608 |
| asynchronous-direct-to-buffer/4 | 7 | 3 | 416 | 448 | 576 | 608 | 672 |
| asynchronous-direct-to-buffer/8 | 0 | 0 | 0 | 32 | 160 | 160 | 224 |
| asynchronous-direct-to-buffer/8 | 1 | 1 | 32 | 64 | 192 | 224 | 288 |
| asynchronous-direct-to-buffer/8 | 2 | 2 | 64 | 96 | 224 | 288 | 352 |
| asynchronous-direct-to-buffer/8 | 3 | 3 | 96 | 128 | 256 | 352 | 416 |
| asynchronous-direct-to-buffer/8 | 4 | 4 | 128 | 160 | 288 | 416 | 480 |
| asynchronous-direct-to-buffer/8 | 5 | 5 | 160 | 192 | 320 | 480 | 544 |
| asynchronous-direct-to-buffer/8 | 6 | 6 | 192 | 224 | 352 | 544 | 608 |
| asynchronous-direct-to-buffer/8 | 7 | 7 | 224 | 256 | 384 | 608 | 672 |

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
    "tile_k": 16,
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
  "chunks": 8,
  "chunk_flops": 524288,
  "total_flops": 4194304,
  "chunk_input_bytes": 8192,
  "rows": [
    {
      "mode": "synchronous-register-stage",
      "input_slots": 1,
      "smem_reserved_bytes": 8192,
      "smem_capacity_passes": true,
      "register_staging_reserved_bytes": 8192,
      "accumulator_reserved_bytes": 65536,
      "register_interface_bytes": 131072,
      "external_input_payload_bytes": 65536,
      "timing": {
        "chunks": [
          {
            "chunk": 0,
            "slot": 0,
            "issue_start": 0,
            "transfer_end": 32,
            "data_ready": 224,
            "compute_start": 224,
            "compute_end": 288,
            "slot_released": 288,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 224
          },
          {
            "chunk": 1,
            "slot": 0,
            "issue_start": 288,
            "transfer_end": 320,
            "data_ready": 512,
            "compute_start": 512,
            "compute_end": 576,
            "slot_released": 576,
            "slot_wait_ticks": 256,
            "compute_idle_ticks": 224
          },
          {
            "chunk": 2,
            "slot": 0,
            "issue_start": 576,
            "transfer_end": 608,
            "data_ready": 800,
            "compute_start": 800,
            "compute_end": 864,
            "slot_released": 864,
            "slot_wait_ticks": 256,
            "compute_idle_ticks": 224
          },
          {
            "chunk": 3,
            "slot": 0,
            "issue_start": 864,
            "transfer_end": 896,
            "data_ready": 1088,
            "compute_start": 1088,
            "compute_end": 1152,
            "slot_released": 1152,
            "slot_wait_ticks": 256,
            "compute_idle_ticks": 224
          },
          {
            "chunk": 4,
            "slot": 0,
            "issue_start": 1152,
            "transfer_end": 1184,
            "data_ready": 1376,
            "compute_start": 1376,
            "compute_end": 1440,
            "slot_released": 1440,
            "slot_wait_ticks": 256,
            "compute_idle_ticks": 224
          },
          {
            "chunk": 5,
            "slot": 0,
            "issue_start": 1440,
            "transfer_end": 1472,
            "data_ready": 1664,
            "compute_start": 1664,
            "compute_end": 1728,
            "slot_released": 1728,
            "slot_wait_ticks": 256,
            "compute_idle_ticks": 224
          },
          {
            "chunk": 6,
            "slot": 0,
            "issue_start": 1728,
            "transfer_end": 1760,
            "data_ready": 1952,
            "compute_start": 1952,
            "compute_end": 2016,
            "slot_released": 2016,
            "slot_wait_ticks": 256,
            "compute_idle_ticks": 224
          },
          {
            "chunk": 7,
            "slot": 0,
            "issue_start": 2016,
            "transfer_end": 2048,
            "data_ready": 2240,
            "compute_start": 2240,
            "compute_end": 2304,
            "slot_released": 2304,
            "slot_wait_ticks": 256,
            "compute_idle_ticks": 224
          }
        ],
        "finish_tick": 2304,
        "total_compute_busy_ticks": 512,
        "total_compute_idle_ticks": 1792
      },
      "capacity_qualified_finish_tick": 2304
    },
    {
      "mode": "synchronous-register-stage",
      "input_slots": 2,
      "smem_reserved_bytes": 16384,
      "smem_capacity_passes": true,
      "register_staging_reserved_bytes": 8192,
      "accumulator_reserved_bytes": 65536,
      "register_interface_bytes": 131072,
      "external_input_payload_bytes": 65536,
      "timing": {
        "chunks": [
          {
            "chunk": 0,
            "slot": 0,
            "issue_start": 0,
            "transfer_end": 32,
            "data_ready": 224,
            "compute_start": 224,
            "compute_end": 288,
            "slot_released": 288,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 224
          },
          {
            "chunk": 1,
            "slot": 1,
            "issue_start": 288,
            "transfer_end": 320,
            "data_ready": 512,
            "compute_start": 512,
            "compute_end": 576,
            "slot_released": 576,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 224
          },
          {
            "chunk": 2,
            "slot": 0,
            "issue_start": 576,
            "transfer_end": 608,
            "data_ready": 800,
            "compute_start": 800,
            "compute_end": 864,
            "slot_released": 864,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 224
          },
          {
            "chunk": 3,
            "slot": 1,
            "issue_start": 864,
            "transfer_end": 896,
            "data_ready": 1088,
            "compute_start": 1088,
            "compute_end": 1152,
            "slot_released": 1152,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 224
          },
          {
            "chunk": 4,
            "slot": 0,
            "issue_start": 1152,
            "transfer_end": 1184,
            "data_ready": 1376,
            "compute_start": 1376,
            "compute_end": 1440,
            "slot_released": 1440,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 224
          },
          {
            "chunk": 5,
            "slot": 1,
            "issue_start": 1440,
            "transfer_end": 1472,
            "data_ready": 1664,
            "compute_start": 1664,
            "compute_end": 1728,
            "slot_released": 1728,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 224
          },
          {
            "chunk": 6,
            "slot": 0,
            "issue_start": 1728,
            "transfer_end": 1760,
            "data_ready": 1952,
            "compute_start": 1952,
            "compute_end": 2016,
            "slot_released": 2016,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 224
          },
          {
            "chunk": 7,
            "slot": 1,
            "issue_start": 2016,
            "transfer_end": 2048,
            "data_ready": 2240,
            "compute_start": 2240,
            "compute_end": 2304,
            "slot_released": 2304,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 224
          }
        ],
        "finish_tick": 2304,
        "total_compute_busy_ticks": 512,
        "total_compute_idle_ticks": 1792
      },
      "capacity_qualified_finish_tick": 2304
    },
    {
      "mode": "synchronous-register-stage",
      "input_slots": 4,
      "smem_reserved_bytes": 32768,
      "smem_capacity_passes": true,
      "register_staging_reserved_bytes": 8192,
      "accumulator_reserved_bytes": 65536,
      "register_interface_bytes": 131072,
      "external_input_payload_bytes": 65536,
      "timing": {
        "chunks": [
          {
            "chunk": 0,
            "slot": 0,
            "issue_start": 0,
            "transfer_end": 32,
            "data_ready": 224,
            "compute_start": 224,
            "compute_end": 288,
            "slot_released": 288,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 224
          },
          {
            "chunk": 1,
            "slot": 1,
            "issue_start": 288,
            "transfer_end": 320,
            "data_ready": 512,
            "compute_start": 512,
            "compute_end": 576,
            "slot_released": 576,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 224
          },
          {
            "chunk": 2,
            "slot": 2,
            "issue_start": 576,
            "transfer_end": 608,
            "data_ready": 800,
            "compute_start": 800,
            "compute_end": 864,
            "slot_released": 864,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 224
          },
          {
            "chunk": 3,
            "slot": 3,
            "issue_start": 864,
            "transfer_end": 896,
            "data_ready": 1088,
            "compute_start": 1088,
            "compute_end": 1152,
            "slot_released": 1152,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 224
          },
          {
            "chunk": 4,
            "slot": 0,
            "issue_start": 1152,
            "transfer_end": 1184,
            "data_ready": 1376,
            "compute_start": 1376,
            "compute_end": 1440,
            "slot_released": 1440,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 224
          },
          {
            "chunk": 5,
            "slot": 1,
            "issue_start": 1440,
            "transfer_end": 1472,
            "data_ready": 1664,
            "compute_start": 1664,
            "compute_end": 1728,
            "slot_released": 1728,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 224
          },
          {
            "chunk": 6,
            "slot": 2,
            "issue_start": 1728,
            "transfer_end": 1760,
            "data_ready": 1952,
            "compute_start": 1952,
            "compute_end": 2016,
            "slot_released": 2016,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 224
          },
          {
            "chunk": 7,
            "slot": 3,
            "issue_start": 2016,
            "transfer_end": 2048,
            "data_ready": 2240,
            "compute_start": 2240,
            "compute_end": 2304,
            "slot_released": 2304,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 224
          }
        ],
        "finish_tick": 2304,
        "total_compute_busy_ticks": 512,
        "total_compute_idle_ticks": 1792
      },
      "capacity_qualified_finish_tick": 2304
    },
    {
      "mode": "synchronous-register-stage",
      "input_slots": 8,
      "smem_reserved_bytes": 65536,
      "smem_capacity_passes": true,
      "register_staging_reserved_bytes": 8192,
      "accumulator_reserved_bytes": 65536,
      "register_interface_bytes": 131072,
      "external_input_payload_bytes": 65536,
      "timing": {
        "chunks": [
          {
            "chunk": 0,
            "slot": 0,
            "issue_start": 0,
            "transfer_end": 32,
            "data_ready": 224,
            "compute_start": 224,
            "compute_end": 288,
            "slot_released": 288,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 224
          },
          {
            "chunk": 1,
            "slot": 1,
            "issue_start": 288,
            "transfer_end": 320,
            "data_ready": 512,
            "compute_start": 512,
            "compute_end": 576,
            "slot_released": 576,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 224
          },
          {
            "chunk": 2,
            "slot": 2,
            "issue_start": 576,
            "transfer_end": 608,
            "data_ready": 800,
            "compute_start": 800,
            "compute_end": 864,
            "slot_released": 864,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 224
          },
          {
            "chunk": 3,
            "slot": 3,
            "issue_start": 864,
            "transfer_end": 896,
            "data_ready": 1088,
            "compute_start": 1088,
            "compute_end": 1152,
            "slot_released": 1152,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 224
          },
          {
            "chunk": 4,
            "slot": 4,
            "issue_start": 1152,
            "transfer_end": 1184,
            "data_ready": 1376,
            "compute_start": 1376,
            "compute_end": 1440,
            "slot_released": 1440,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 224
          },
          {
            "chunk": 5,
            "slot": 5,
            "issue_start": 1440,
            "transfer_end": 1472,
            "data_ready": 1664,
            "compute_start": 1664,
            "compute_end": 1728,
            "slot_released": 1728,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 224
          },
          {
            "chunk": 6,
            "slot": 6,
            "issue_start": 1728,
            "transfer_end": 1760,
            "data_ready": 1952,
            "compute_start": 1952,
            "compute_end": 2016,
            "slot_released": 2016,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 224
          },
          {
            "chunk": 7,
            "slot": 7,
            "issue_start": 2016,
            "transfer_end": 2048,
            "data_ready": 2240,
            "compute_start": 2240,
            "compute_end": 2304,
            "slot_released": 2304,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 224
          }
        ],
        "finish_tick": 2304,
        "total_compute_busy_ticks": 512,
        "total_compute_idle_ticks": 1792
      },
      "capacity_qualified_finish_tick": 2304
    },
    {
      "mode": "asynchronous-direct-to-buffer",
      "input_slots": 1,
      "smem_reserved_bytes": 8192,
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
            "transfer_end": 32,
            "data_ready": 160,
            "compute_start": 160,
            "compute_end": 224,
            "slot_released": 224,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 160
          },
          {
            "chunk": 1,
            "slot": 0,
            "issue_start": 224,
            "transfer_end": 256,
            "data_ready": 384,
            "compute_start": 384,
            "compute_end": 448,
            "slot_released": 448,
            "slot_wait_ticks": 192,
            "compute_idle_ticks": 160
          },
          {
            "chunk": 2,
            "slot": 0,
            "issue_start": 448,
            "transfer_end": 480,
            "data_ready": 608,
            "compute_start": 608,
            "compute_end": 672,
            "slot_released": 672,
            "slot_wait_ticks": 192,
            "compute_idle_ticks": 160
          },
          {
            "chunk": 3,
            "slot": 0,
            "issue_start": 672,
            "transfer_end": 704,
            "data_ready": 832,
            "compute_start": 832,
            "compute_end": 896,
            "slot_released": 896,
            "slot_wait_ticks": 192,
            "compute_idle_ticks": 160
          },
          {
            "chunk": 4,
            "slot": 0,
            "issue_start": 896,
            "transfer_end": 928,
            "data_ready": 1056,
            "compute_start": 1056,
            "compute_end": 1120,
            "slot_released": 1120,
            "slot_wait_ticks": 192,
            "compute_idle_ticks": 160
          },
          {
            "chunk": 5,
            "slot": 0,
            "issue_start": 1120,
            "transfer_end": 1152,
            "data_ready": 1280,
            "compute_start": 1280,
            "compute_end": 1344,
            "slot_released": 1344,
            "slot_wait_ticks": 192,
            "compute_idle_ticks": 160
          },
          {
            "chunk": 6,
            "slot": 0,
            "issue_start": 1344,
            "transfer_end": 1376,
            "data_ready": 1504,
            "compute_start": 1504,
            "compute_end": 1568,
            "slot_released": 1568,
            "slot_wait_ticks": 192,
            "compute_idle_ticks": 160
          },
          {
            "chunk": 7,
            "slot": 0,
            "issue_start": 1568,
            "transfer_end": 1600,
            "data_ready": 1728,
            "compute_start": 1728,
            "compute_end": 1792,
            "slot_released": 1792,
            "slot_wait_ticks": 192,
            "compute_idle_ticks": 160
          }
        ],
        "finish_tick": 1792,
        "total_compute_busy_ticks": 512,
        "total_compute_idle_ticks": 1280
      },
      "capacity_qualified_finish_tick": 1792
    },
    {
      "mode": "asynchronous-direct-to-buffer",
      "input_slots": 2,
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
            "transfer_end": 32,
            "data_ready": 160,
            "compute_start": 160,
            "compute_end": 224,
            "slot_released": 224,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 160
          },
          {
            "chunk": 1,
            "slot": 1,
            "issue_start": 32,
            "transfer_end": 64,
            "data_ready": 192,
            "compute_start": 224,
            "compute_end": 288,
            "slot_released": 288,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 0
          },
          {
            "chunk": 2,
            "slot": 0,
            "issue_start": 224,
            "transfer_end": 256,
            "data_ready": 384,
            "compute_start": 384,
            "compute_end": 448,
            "slot_released": 448,
            "slot_wait_ticks": 160,
            "compute_idle_ticks": 96
          },
          {
            "chunk": 3,
            "slot": 1,
            "issue_start": 288,
            "transfer_end": 320,
            "data_ready": 448,
            "compute_start": 448,
            "compute_end": 512,
            "slot_released": 512,
            "slot_wait_ticks": 32,
            "compute_idle_ticks": 0
          },
          {
            "chunk": 4,
            "slot": 0,
            "issue_start": 448,
            "transfer_end": 480,
            "data_ready": 608,
            "compute_start": 608,
            "compute_end": 672,
            "slot_released": 672,
            "slot_wait_ticks": 128,
            "compute_idle_ticks": 96
          },
          {
            "chunk": 5,
            "slot": 1,
            "issue_start": 512,
            "transfer_end": 544,
            "data_ready": 672,
            "compute_start": 672,
            "compute_end": 736,
            "slot_released": 736,
            "slot_wait_ticks": 32,
            "compute_idle_ticks": 0
          },
          {
            "chunk": 6,
            "slot": 0,
            "issue_start": 672,
            "transfer_end": 704,
            "data_ready": 832,
            "compute_start": 832,
            "compute_end": 896,
            "slot_released": 896,
            "slot_wait_ticks": 128,
            "compute_idle_ticks": 96
          },
          {
            "chunk": 7,
            "slot": 1,
            "issue_start": 736,
            "transfer_end": 768,
            "data_ready": 896,
            "compute_start": 896,
            "compute_end": 960,
            "slot_released": 960,
            "slot_wait_ticks": 32,
            "compute_idle_ticks": 0
          }
        ],
        "finish_tick": 960,
        "total_compute_busy_ticks": 512,
        "total_compute_idle_ticks": 448
      },
      "capacity_qualified_finish_tick": 960
    },
    {
      "mode": "asynchronous-direct-to-buffer",
      "input_slots": 4,
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
            "transfer_end": 32,
            "data_ready": 160,
            "compute_start": 160,
            "compute_end": 224,
            "slot_released": 224,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 160
          },
          {
            "chunk": 1,
            "slot": 1,
            "issue_start": 32,
            "transfer_end": 64,
            "data_ready": 192,
            "compute_start": 224,
            "compute_end": 288,
            "slot_released": 288,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 0
          },
          {
            "chunk": 2,
            "slot": 2,
            "issue_start": 64,
            "transfer_end": 96,
            "data_ready": 224,
            "compute_start": 288,
            "compute_end": 352,
            "slot_released": 352,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 0
          },
          {
            "chunk": 3,
            "slot": 3,
            "issue_start": 96,
            "transfer_end": 128,
            "data_ready": 256,
            "compute_start": 352,
            "compute_end": 416,
            "slot_released": 416,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 0
          },
          {
            "chunk": 4,
            "slot": 0,
            "issue_start": 224,
            "transfer_end": 256,
            "data_ready": 384,
            "compute_start": 416,
            "compute_end": 480,
            "slot_released": 480,
            "slot_wait_ticks": 96,
            "compute_idle_ticks": 0
          },
          {
            "chunk": 5,
            "slot": 1,
            "issue_start": 288,
            "transfer_end": 320,
            "data_ready": 448,
            "compute_start": 480,
            "compute_end": 544,
            "slot_released": 544,
            "slot_wait_ticks": 32,
            "compute_idle_ticks": 0
          },
          {
            "chunk": 6,
            "slot": 2,
            "issue_start": 352,
            "transfer_end": 384,
            "data_ready": 512,
            "compute_start": 544,
            "compute_end": 608,
            "slot_released": 608,
            "slot_wait_ticks": 32,
            "compute_idle_ticks": 0
          },
          {
            "chunk": 7,
            "slot": 3,
            "issue_start": 416,
            "transfer_end": 448,
            "data_ready": 576,
            "compute_start": 608,
            "compute_end": 672,
            "slot_released": 672,
            "slot_wait_ticks": 32,
            "compute_idle_ticks": 0
          }
        ],
        "finish_tick": 672,
        "total_compute_busy_ticks": 512,
        "total_compute_idle_ticks": 160
      },
      "capacity_qualified_finish_tick": 672
    },
    {
      "mode": "asynchronous-direct-to-buffer",
      "input_slots": 8,
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
            "transfer_end": 32,
            "data_ready": 160,
            "compute_start": 160,
            "compute_end": 224,
            "slot_released": 224,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 160
          },
          {
            "chunk": 1,
            "slot": 1,
            "issue_start": 32,
            "transfer_end": 64,
            "data_ready": 192,
            "compute_start": 224,
            "compute_end": 288,
            "slot_released": 288,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 0
          },
          {
            "chunk": 2,
            "slot": 2,
            "issue_start": 64,
            "transfer_end": 96,
            "data_ready": 224,
            "compute_start": 288,
            "compute_end": 352,
            "slot_released": 352,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 0
          },
          {
            "chunk": 3,
            "slot": 3,
            "issue_start": 96,
            "transfer_end": 128,
            "data_ready": 256,
            "compute_start": 352,
            "compute_end": 416,
            "slot_released": 416,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 0
          },
          {
            "chunk": 4,
            "slot": 4,
            "issue_start": 128,
            "transfer_end": 160,
            "data_ready": 288,
            "compute_start": 416,
            "compute_end": 480,
            "slot_released": 480,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 0
          },
          {
            "chunk": 5,
            "slot": 5,
            "issue_start": 160,
            "transfer_end": 192,
            "data_ready": 320,
            "compute_start": 480,
            "compute_end": 544,
            "slot_released": 544,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 0
          },
          {
            "chunk": 6,
            "slot": 6,
            "issue_start": 192,
            "transfer_end": 224,
            "data_ready": 352,
            "compute_start": 544,
            "compute_end": 608,
            "slot_released": 608,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 0
          },
          {
            "chunk": 7,
            "slot": 7,
            "issue_start": 224,
            "transfer_end": 256,
            "data_ready": 384,
            "compute_start": 608,
            "compute_end": 672,
            "slot_released": 672,
            "slot_wait_ticks": 0,
            "compute_idle_ticks": 0
          }
        ],
        "finish_tick": 672,
        "total_compute_busy_ticks": 512,
        "total_compute_idle_ticks": 160
      },
      "capacity_qualified_finish_tick": 672
    }
  ],
  "no_slot_backpressure_finish_tick": 672,
  "smallest_enumerated_slots_matching_unlimited": 4,
  "fastest_capacity_qualified_async_tick": 672,
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
