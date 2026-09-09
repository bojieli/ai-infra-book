# Training input supply and checkpoint contention

```json
{
  "calculation": "qwen8-training-input-supply",
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
    "samples": [
      {
        "tokens": 128,
        "stored_bytes": 512,
        "cpu_ns": 164000
      },
      {
        "tokens": 256,
        "stored_bytes": 1024,
        "cpu_ns": 228000
      },
      {
        "tokens": 192,
        "stored_bytes": 768,
        "cpu_ns": 196000
      },
      {
        "tokens": 320,
        "stored_bytes": 1280,
        "cpu_ns": 260000
      },
      {
        "tokens": 64,
        "stored_bytes": 256,
        "cpu_ns": 132000
      },
      {
        "tokens": 448,
        "stored_bytes": 1792,
        "cpu_ns": 324000
      },
      {
        "tokens": 256,
        "stored_bytes": 1024,
        "cpu_ns": 228000
      },
      {
        "tokens": 256,
        "stored_bytes": 1024,
        "cpu_ns": 228000
      }
    ],
    "pack_tokens": 512,
    "host_slots": 2,
    "device_slots": 2,
    "storage_bytes_per_second": 2000000000,
    "h2d_bytes_per_second": 12000000000,
    "packing_ns": 100000,
    "consume_ns": 2000000,
    "checkpoint_every": 0,
    "snapshot_ns": 1000000,
    "snapshot_slots": 1,
    "shared_storage": true
  },
  "packs": [
    {
      "pack": 0,
      "samples": [
        0,
        1
      ],
      "valid_tokens": 384,
      "padding_tokens": 128,
      "stored_bytes": 1536,
      "wire_bytes": 10752
    },
    {
      "pack": 1,
      "samples": [
        2,
        3
      ],
      "valid_tokens": 512,
      "padding_tokens": 0,
      "stored_bytes": 2048,
      "wire_bytes": 10752
    },
    {
      "pack": 2,
      "samples": [
        4,
        5
      ],
      "valid_tokens": 512,
      "padding_tokens": 0,
      "stored_bytes": 2048,
      "wire_bytes": 10752
    },
    {
      "pack": 3,
      "samples": [
        6,
        7
      ],
      "valid_tokens": 512,
      "padding_tokens": 0,
      "stored_bytes": 2048,
      "wire_bytes": 10752
    }
  ],
  "events": [
    {
      "id": "R0",
      "resource": "storage",
      "deps": [],
      "start_exact": "0",
      "end_exact": "3/3906250",
      "service_exact": "3/3906250"
    },
    {
      "id": "P0",
      "resource": "cpu",
      "deps": [
        "R0"
      ],
      "start_exact": "3/3906250",
      "end_exact": "15399/31250000",
      "service_exact": "123/250000"
    },
    {
      "id": "R1",
      "resource": "storage",
      "deps": [
        "R0"
      ],
      "start_exact": "3/3906250",
      "end_exact": "7/3906250",
      "service_exact": "2/1953125"
    },
    {
      "id": "H0",
      "resource": "h2d",
      "deps": [
        "P0"
      ],
      "start_exact": "15399/31250000",
      "end_exact": "15427/31250000",
      "service_exact": "7/7812500"
    },
    {
      "id": "P1",
      "resource": "cpu",
      "deps": [
        "R1",
        "P0"
      ],
      "start_exact": "15399/31250000",
      "end_exact": "16387/15625000",
      "service_exact": "139/250000"
    },
    {
      "id": "C0",
      "resource": "device",
      "deps": [
        "H0"
      ],
      "start_exact": "15427/31250000",
      "end_exact": "77927/31250000",
      "service_exact": "1/500"
    },
    {
      "id": "R2",
      "resource": "storage",
      "deps": [
        "H0",
        "R1"
      ],
      "start_exact": "15427/31250000",
      "end_exact": "15459/31250000",
      "service_exact": "2/1953125"
    },
    {
      "id": "H1",
      "resource": "h2d",
      "deps": [
        "P1",
        "H0"
      ],
      "start_exact": "16387/15625000",
      "end_exact": "16401/15625000",
      "service_exact": "7/7812500"
    },
    {
      "id": "P2",
      "resource": "cpu",
      "deps": [
        "R2",
        "P1"
      ],
      "start_exact": "16387/15625000",
      "end_exact": "50149/31250000",
      "service_exact": "139/250000"
    },
    {
      "id": "R3",
      "resource": "storage",
      "deps": [
        "H1",
        "R2"
      ],
      "start_exact": "16401/15625000",
      "end_exact": "16417/15625000",
      "service_exact": "2/1953125"
    },
    {
      "id": "P3",
      "resource": "cpu",
      "deps": [
        "R3",
        "P2"
      ],
      "start_exact": "50149/31250000",
      "end_exact": "16881/7812500",
      "service_exact": "139/250000"
    },
    {
      "id": "C1",
      "resource": "device",
      "deps": [
        "H1",
        "C0"
      ],
      "start_exact": "77927/31250000",
      "end_exact": "140427/31250000",
      "service_exact": "1/500"
    },
    {
      "id": "H2",
      "resource": "h2d",
      "deps": [
        "P2",
        "C0",
        "H1"
      ],
      "start_exact": "77927/31250000",
      "end_exact": "15591/6250000",
      "service_exact": "7/7812500"
    },
    {
      "id": "C2",
      "resource": "device",
      "deps": [
        "H2",
        "C1"
      ],
      "start_exact": "140427/31250000",
      "end_exact": "202927/31250000",
      "service_exact": "1/500"
    },
    {
      "id": "H3",
      "resource": "h2d",
      "deps": [
        "P3",
        "C1",
        "H2"
      ],
      "start_exact": "140427/31250000",
      "end_exact": "28091/6250000",
      "service_exact": "7/7812500"
    },
    {
      "id": "C3",
      "resource": "device",
      "deps": [
        "H3",
        "C2"
      ],
      "start_exact": "202927/31250000",
      "end_exact": "265427/31250000",
      "service_exact": "1/500"
    }
  ],
  "lifetimes": {
    "host": [
      {
        "start_exact": "0",
        "end_exact": "15427/31250000",
        "bytes": 12288
      },
      {
        "start_exact": "3/3906250",
        "end_exact": "16401/15625000",
        "bytes": 12800
      },
      {
        "start_exact": "15427/31250000",
        "end_exact": "15591/6250000",
        "bytes": 12800
      },
      {
        "start_exact": "16401/15625000",
        "end_exact": "28091/6250000",
        "bytes": 12800
      }
    ],
    "device": [
      {
        "start_exact": "15399/31250000",
        "end_exact": "77927/31250000",
        "bytes": 10752
      },
      {
        "start_exact": "16387/15625000",
        "end_exact": "140427/31250000",
        "bytes": 10752
      },
      {
        "start_exact": "77927/31250000",
        "end_exact": "202927/31250000",
        "bytes": 10752
      },
      {
        "start_exact": "140427/31250000",
        "end_exact": "265427/31250000",
        "bytes": 10752
      }
    ],
    "snapshot": []
  },
  "buffers": {
    "host": {
      "peak_reserved_bytes": 25600,
      "byte_seconds_exact": "174215136/1953125"
    },
    "device": {
      "peak_reserved_bytes": 21504,
      "byte_seconds_exact": "282361632/1953125"
    },
    "snapshot": {
      "peak_reserved_bytes": 0,
      "byte_seconds_exact": "0"
    }
  },
  "summary": {
    "samples": 8,
    "valid_tokens": 1920,
    "padding_tokens": 128,
    "packs": 4,
    "input_storage_bytes": 7680,
    "h2d_bytes": 43008,
    "checkpoint_parameters": 8190735360,
    "checkpoint_bytes_each": 114670295040,
    "checkpoint_write_bytes": 0,
    "cpu_core_seconds_exact": "27/12500",
    "training_end_exact": "265427/31250000",
    "all_durable_exact": "265427/31250000",
    "device_compute_service_exact": "1/125",
    "snapshot_service_before_training_end_exact": "0",
    "device_wait_exact": "15427/31250000",
    "target_sample_rate_exact": "1000",
    "target_input_bytes_per_second_exact": "960000",
    "target_h2d_bytes_per_second_exact": "5376000"
  },
  "scope": [
    "Pre-tokenized sample geometry supplied by caller; next-fit without splitting, dropping or implicit EOS insertion.",
    "One CPU worker; stored bytes, preparation/consumption service and bandwidth are explicit workload assumptions, not measured Qwen performance.",
    "IDs/labels int64, validity bool, segment IDs int32. Segment-aware consumer assumed; full quadratic masks, tokenizer and GPU mask creation excluded.",
    "Two serial storage resources or one shared nonpreemptive resource. Earliest-ready, reads win ties. Checkpoint writes are whole payload jobs, not optimal I/O arbitration.",
    "Checkpoint BF16 weights plus FP32 master and two moments =14P, same declared layout as checkpoint_async; gradients and arbitrary runtime state excluded.",
    "Snapshot uses device service and stalls next consume, bounded snapshot slots retained through write completion; durability equals write completion in this contract.",
    "Host reservation conservatively includes stored pack plus packed wire tensors from read start to H2D end. Runtime peaks and metadata/workspace excluded."
  ]
}
```
