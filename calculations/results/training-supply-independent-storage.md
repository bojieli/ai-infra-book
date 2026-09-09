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
        "tokens": 512,
        "stored_bytes": 8192,
        "cpu_ns": 100000
      },
      {
        "tokens": 512,
        "stored_bytes": 8192,
        "cpu_ns": 100000
      },
      {
        "tokens": 512,
        "stored_bytes": 8192,
        "cpu_ns": 100000
      },
      {
        "tokens": 512,
        "stored_bytes": 8192,
        "cpu_ns": 100000
      },
      {
        "tokens": 512,
        "stored_bytes": 8192,
        "cpu_ns": 100000
      },
      {
        "tokens": 512,
        "stored_bytes": 8192,
        "cpu_ns": 100000
      },
      {
        "tokens": 512,
        "stored_bytes": 8192,
        "cpu_ns": 100000
      },
      {
        "tokens": 512,
        "stored_bytes": 8192,
        "cpu_ns": 100000
      },
      {
        "tokens": 512,
        "stored_bytes": 8192,
        "cpu_ns": 100000
      },
      {
        "tokens": 512,
        "stored_bytes": 8192,
        "cpu_ns": 100000
      },
      {
        "tokens": 512,
        "stored_bytes": 8192,
        "cpu_ns": 100000
      },
      {
        "tokens": 512,
        "stored_bytes": 8192,
        "cpu_ns": 100000
      }
    ],
    "pack_tokens": 512,
    "host_slots": 1,
    "device_slots": 1,
    "storage_bytes_per_second": 2000000000,
    "h2d_bytes_per_second": 12000000000,
    "packing_ns": 100000,
    "consume_ns": 2000000,
    "checkpoint_every": 2,
    "snapshot_ns": 1000000,
    "snapshot_slots": 8,
    "shared_storage": false
  },
  "packs": [
    {
      "pack": 0,
      "samples": [
        0
      ],
      "valid_tokens": 512,
      "padding_tokens": 0,
      "stored_bytes": 8192,
      "wire_bytes": 10752
    },
    {
      "pack": 1,
      "samples": [
        1
      ],
      "valid_tokens": 512,
      "padding_tokens": 0,
      "stored_bytes": 8192,
      "wire_bytes": 10752
    },
    {
      "pack": 2,
      "samples": [
        2
      ],
      "valid_tokens": 512,
      "padding_tokens": 0,
      "stored_bytes": 8192,
      "wire_bytes": 10752
    },
    {
      "pack": 3,
      "samples": [
        3
      ],
      "valid_tokens": 512,
      "padding_tokens": 0,
      "stored_bytes": 8192,
      "wire_bytes": 10752
    },
    {
      "pack": 4,
      "samples": [
        4
      ],
      "valid_tokens": 512,
      "padding_tokens": 0,
      "stored_bytes": 8192,
      "wire_bytes": 10752
    },
    {
      "pack": 5,
      "samples": [
        5
      ],
      "valid_tokens": 512,
      "padding_tokens": 0,
      "stored_bytes": 8192,
      "wire_bytes": 10752
    },
    {
      "pack": 6,
      "samples": [
        6
      ],
      "valid_tokens": 512,
      "padding_tokens": 0,
      "stored_bytes": 8192,
      "wire_bytes": 10752
    },
    {
      "pack": 7,
      "samples": [
        7
      ],
      "valid_tokens": 512,
      "padding_tokens": 0,
      "stored_bytes": 8192,
      "wire_bytes": 10752
    },
    {
      "pack": 8,
      "samples": [
        8
      ],
      "valid_tokens": 512,
      "padding_tokens": 0,
      "stored_bytes": 8192,
      "wire_bytes": 10752
    },
    {
      "pack": 9,
      "samples": [
        9
      ],
      "valid_tokens": 512,
      "padding_tokens": 0,
      "stored_bytes": 8192,
      "wire_bytes": 10752
    },
    {
      "pack": 10,
      "samples": [
        10
      ],
      "valid_tokens": 512,
      "padding_tokens": 0,
      "stored_bytes": 8192,
      "wire_bytes": 10752
    },
    {
      "pack": 11,
      "samples": [
        11
      ],
      "valid_tokens": 512,
      "padding_tokens": 0,
      "stored_bytes": 8192,
      "wire_bytes": 10752
    }
  ],
  "events": [
    {
      "id": "R0",
      "resource": "read_storage",
      "deps": [],
      "start_exact": "0",
      "end_exact": "8/1953125",
      "service_exact": "8/1953125"
    },
    {
      "id": "P0",
      "resource": "cpu",
      "deps": [
        "R0"
      ],
      "start_exact": "8/1953125",
      "end_exact": "3189/15625000",
      "service_exact": "1/5000"
    },
    {
      "id": "H0",
      "resource": "h2d",
      "deps": [
        "P0"
      ],
      "start_exact": "3189/15625000",
      "end_exact": "3203/15625000",
      "service_exact": "7/7812500"
    },
    {
      "id": "C0",
      "resource": "device",
      "deps": [
        "H0"
      ],
      "start_exact": "3203/15625000",
      "end_exact": "34453/15625000",
      "service_exact": "1/500"
    },
    {
      "id": "R1",
      "resource": "read_storage",
      "deps": [
        "H0",
        "R0"
      ],
      "start_exact": "3203/15625000",
      "end_exact": "3267/15625000",
      "service_exact": "8/1953125"
    },
    {
      "id": "P1",
      "resource": "cpu",
      "deps": [
        "R1",
        "P0"
      ],
      "start_exact": "3267/15625000",
      "end_exact": "799/1953125",
      "service_exact": "1/5000"
    },
    {
      "id": "H1",
      "resource": "h2d",
      "deps": [
        "P1",
        "C0",
        "H0"
      ],
      "start_exact": "34453/15625000",
      "end_exact": "34467/15625000",
      "service_exact": "7/7812500"
    },
    {
      "id": "C1",
      "resource": "device",
      "deps": [
        "H1",
        "C0"
      ],
      "start_exact": "34467/15625000",
      "end_exact": "65717/15625000",
      "service_exact": "1/500"
    },
    {
      "id": "R2",
      "resource": "read_storage",
      "deps": [
        "H1",
        "R1"
      ],
      "start_exact": "34467/15625000",
      "end_exact": "34531/15625000",
      "service_exact": "8/1953125"
    },
    {
      "id": "P2",
      "resource": "cpu",
      "deps": [
        "R2",
        "P1"
      ],
      "start_exact": "34531/15625000",
      "end_exact": "4707/1953125",
      "service_exact": "1/5000"
    },
    {
      "id": "H2",
      "resource": "h2d",
      "deps": [
        "P2",
        "C1",
        "H1"
      ],
      "start_exact": "65717/15625000",
      "end_exact": "65731/15625000",
      "service_exact": "7/7812500"
    },
    {
      "id": "S1",
      "resource": "device",
      "deps": [
        "C1"
      ],
      "start_exact": "65717/15625000",
      "end_exact": "40671/7812500",
      "service_exact": "1/1000"
    },
    {
      "id": "R3",
      "resource": "read_storage",
      "deps": [
        "H2",
        "R2"
      ],
      "start_exact": "65731/15625000",
      "end_exact": "13159/3125000",
      "service_exact": "8/1953125"
    },
    {
      "id": "P3",
      "resource": "cpu",
      "deps": [
        "R3",
        "P2"
      ],
      "start_exact": "13159/3125000",
      "end_exact": "1723/390625",
      "service_exact": "1/5000"
    },
    {
      "id": "C2",
      "resource": "device",
      "deps": [
        "H2",
        "C1",
        "S1"
      ],
      "start_exact": "40671/7812500",
      "end_exact": "14074/1953125",
      "service_exact": "1/500"
    },
    {
      "id": "W1",
      "resource": "write_storage",
      "deps": [
        "S1"
      ],
      "start_exact": "40671/7812500",
      "end_exact": "447971511/7812500",
      "service_exact": "22396542/390625"
    },
    {
      "id": "H3",
      "resource": "h2d",
      "deps": [
        "P3",
        "C2",
        "H2"
      ],
      "start_exact": "14074/1953125",
      "end_exact": "56303/7812500",
      "service_exact": "7/7812500"
    },
    {
      "id": "C3",
      "resource": "device",
      "deps": [
        "H3",
        "C2"
      ],
      "start_exact": "56303/7812500",
      "end_exact": "17982/1953125",
      "service_exact": "1/500"
    },
    {
      "id": "R4",
      "resource": "read_storage",
      "deps": [
        "H3",
        "R3"
      ],
      "start_exact": "56303/7812500",
      "end_exact": "11267/1562500",
      "service_exact": "8/1953125"
    },
    {
      "id": "P4",
      "resource": "cpu",
      "deps": [
        "R4",
        "P3"
      ],
      "start_exact": "11267/1562500",
      "end_exact": "23159/3125000",
      "service_exact": "1/5000"
    },
    {
      "id": "H4",
      "resource": "h2d",
      "deps": [
        "P4",
        "C3",
        "H3"
      ],
      "start_exact": "17982/1953125",
      "end_exact": "14387/1562500",
      "service_exact": "7/7812500"
    },
    {
      "id": "S3",
      "resource": "device",
      "deps": [
        "C3"
      ],
      "start_exact": "17982/1953125",
      "end_exact": "159481/15625000",
      "service_exact": "1/1000"
    },
    {
      "id": "R5",
      "resource": "read_storage",
      "deps": [
        "H4",
        "R4"
      ],
      "start_exact": "14387/1562500",
      "end_exact": "71967/7812500",
      "service_exact": "8/1953125"
    },
    {
      "id": "P5",
      "resource": "cpu",
      "deps": [
        "R5",
        "P4"
      ],
      "start_exact": "71967/7812500",
      "end_exact": "147059/15625000",
      "service_exact": "1/5000"
    },
    {
      "id": "C4",
      "resource": "device",
      "deps": [
        "H4",
        "C3",
        "S3"
      ],
      "start_exact": "159481/15625000",
      "end_exact": "190731/15625000",
      "service_exact": "1/500"
    },
    {
      "id": "H5",
      "resource": "h2d",
      "deps": [
        "P5",
        "C4",
        "H4"
      ],
      "start_exact": "190731/15625000",
      "end_exact": "38149/3125000",
      "service_exact": "7/7812500"
    },
    {
      "id": "C5",
      "resource": "device",
      "deps": [
        "H5",
        "C4"
      ],
      "start_exact": "38149/3125000",
      "end_exact": "44399/3125000",
      "service_exact": "1/500"
    },
    {
      "id": "R6",
      "resource": "read_storage",
      "deps": [
        "H5",
        "R5"
      ],
      "start_exact": "38149/3125000",
      "end_exact": "190809/15625000",
      "service_exact": "8/1953125"
    },
    {
      "id": "P6",
      "resource": "cpu",
      "deps": [
        "R6",
        "P5"
      ],
      "start_exact": "190809/15625000",
      "end_exact": "96967/7812500",
      "service_exact": "1/5000"
    },
    {
      "id": "H6",
      "resource": "h2d",
      "deps": [
        "P6",
        "C5",
        "H5"
      ],
      "start_exact": "44399/3125000",
      "end_exact": "222009/15625000",
      "service_exact": "7/7812500"
    },
    {
      "id": "S5",
      "resource": "device",
      "deps": [
        "C5"
      ],
      "start_exact": "44399/3125000",
      "end_exact": "11881/781250",
      "service_exact": "1/1000"
    },
    {
      "id": "R7",
      "resource": "read_storage",
      "deps": [
        "H6",
        "R6"
      ],
      "start_exact": "222009/15625000",
      "end_exact": "222073/15625000",
      "service_exact": "8/1953125"
    },
    {
      "id": "P7",
      "resource": "cpu",
      "deps": [
        "R7",
        "P6"
      ],
      "start_exact": "222073/15625000",
      "end_exact": "112599/7812500",
      "service_exact": "1/5000"
    },
    {
      "id": "C6",
      "resource": "device",
      "deps": [
        "H6",
        "C5",
        "S5"
      ],
      "start_exact": "11881/781250",
      "end_exact": "26887/1562500",
      "service_exact": "1/500"
    },
    {
      "id": "H7",
      "resource": "h2d",
      "deps": [
        "P7",
        "C6",
        "H6"
      ],
      "start_exact": "26887/1562500",
      "end_exact": "67221/3906250",
      "service_exact": "7/7812500"
    },
    {
      "id": "C7",
      "resource": "device",
      "deps": [
        "H7",
        "C6"
      ],
      "start_exact": "67221/3906250",
      "end_exact": "150067/7812500",
      "service_exact": "1/500"
    },
    {
      "id": "R8",
      "resource": "read_storage",
      "deps": [
        "H7",
        "R7"
      ],
      "start_exact": "67221/3906250",
      "end_exact": "67237/3906250",
      "service_exact": "8/1953125"
    },
    {
      "id": "P8",
      "resource": "cpu",
      "deps": [
        "R8",
        "P7"
      ],
      "start_exact": "67237/3906250",
      "end_exact": "272073/15625000",
      "service_exact": "1/5000"
    },
    {
      "id": "H8",
      "resource": "h2d",
      "deps": [
        "P8",
        "C7",
        "H7"
      ],
      "start_exact": "150067/7812500",
      "end_exact": "75037/3906250",
      "service_exact": "7/7812500"
    },
    {
      "id": "S7",
      "resource": "device",
      "deps": [
        "C7"
      ],
      "start_exact": "150067/7812500",
      "end_exact": "315759/15625000",
      "service_exact": "1/1000"
    },
    {
      "id": "R9",
      "resource": "read_storage",
      "deps": [
        "H8",
        "R8"
      ],
      "start_exact": "75037/3906250",
      "end_exact": "75053/3906250",
      "service_exact": "8/1953125"
    },
    {
      "id": "P9",
      "resource": "cpu",
      "deps": [
        "R9",
        "P8"
      ],
      "start_exact": "75053/3906250",
      "end_exact": "303337/15625000",
      "service_exact": "1/5000"
    },
    {
      "id": "C8",
      "resource": "device",
      "deps": [
        "H8",
        "C7",
        "S7"
      ],
      "start_exact": "315759/15625000",
      "end_exact": "347009/15625000",
      "service_exact": "1/500"
    },
    {
      "id": "H9",
      "resource": "h2d",
      "deps": [
        "P9",
        "C8",
        "H8"
      ],
      "start_exact": "347009/15625000",
      "end_exact": "347023/15625000",
      "service_exact": "7/7812500"
    },
    {
      "id": "C9",
      "resource": "device",
      "deps": [
        "H9",
        "C8"
      ],
      "start_exact": "347023/15625000",
      "end_exact": "378273/15625000",
      "service_exact": "1/500"
    },
    {
      "id": "R10",
      "resource": "read_storage",
      "deps": [
        "H9",
        "R9"
      ],
      "start_exact": "347023/15625000",
      "end_exact": "347087/15625000",
      "service_exact": "8/1953125"
    },
    {
      "id": "P10",
      "resource": "cpu",
      "deps": [
        "R10",
        "P9"
      ],
      "start_exact": "347087/15625000",
      "end_exact": "87553/3906250",
      "service_exact": "1/5000"
    },
    {
      "id": "H10",
      "resource": "h2d",
      "deps": [
        "P10",
        "C9",
        "H9"
      ],
      "start_exact": "378273/15625000",
      "end_exact": "378287/15625000",
      "service_exact": "7/7812500"
    },
    {
      "id": "S9",
      "resource": "device",
      "deps": [
        "C9"
      ],
      "start_exact": "378273/15625000",
      "end_exact": "196949/7812500",
      "service_exact": "1/1000"
    },
    {
      "id": "R11",
      "resource": "read_storage",
      "deps": [
        "H10",
        "R10"
      ],
      "start_exact": "378287/15625000",
      "end_exact": "378351/15625000",
      "service_exact": "8/1953125"
    },
    {
      "id": "P11",
      "resource": "cpu",
      "deps": [
        "R11",
        "P10"
      ],
      "start_exact": "378351/15625000",
      "end_exact": "95369/3906250",
      "service_exact": "1/5000"
    },
    {
      "id": "C10",
      "resource": "device",
      "deps": [
        "H10",
        "C9",
        "S9"
      ],
      "start_exact": "196949/7812500",
      "end_exact": "106287/3906250",
      "service_exact": "1/500"
    },
    {
      "id": "H11",
      "resource": "h2d",
      "deps": [
        "P11",
        "C10",
        "H10"
      ],
      "start_exact": "106287/3906250",
      "end_exact": "212581/7812500",
      "service_exact": "7/7812500"
    },
    {
      "id": "C11",
      "resource": "device",
      "deps": [
        "H11",
        "C10"
      ],
      "start_exact": "212581/7812500",
      "end_exact": "114103/3906250",
      "service_exact": "1/500"
    },
    {
      "id": "S11",
      "resource": "device",
      "deps": [
        "C11"
      ],
      "start_exact": "114103/3906250",
      "end_exact": "472037/15625000",
      "service_exact": "1/1000"
    },
    {
      "id": "W3",
      "resource": "write_storage",
      "deps": [
        "S3",
        "W1"
      ],
      "start_exact": "447971511/7812500",
      "end_exact": "895902351/7812500",
      "service_exact": "22396542/390625"
    },
    {
      "id": "W5",
      "resource": "write_storage",
      "deps": [
        "S5",
        "W3"
      ],
      "start_exact": "895902351/7812500",
      "end_exact": "1343833191/7812500",
      "service_exact": "22396542/390625"
    },
    {
      "id": "W7",
      "resource": "write_storage",
      "deps": [
        "S7",
        "W5"
      ],
      "start_exact": "1343833191/7812500",
      "end_exact": "1791764031/7812500",
      "service_exact": "22396542/390625"
    },
    {
      "id": "W9",
      "resource": "write_storage",
      "deps": [
        "S9",
        "W7"
      ],
      "start_exact": "1791764031/7812500",
      "end_exact": "2239694871/7812500",
      "service_exact": "22396542/390625"
    },
    {
      "id": "W11",
      "resource": "write_storage",
      "deps": [
        "S11",
        "W9"
      ],
      "start_exact": "2239694871/7812500",
      "end_exact": "2687625711/7812500",
      "service_exact": "22396542/390625"
    }
  ],
  "lifetimes": {
    "host": [
      {
        "start_exact": "0",
        "end_exact": "3203/15625000",
        "bytes": 18944
      },
      {
        "start_exact": "3203/15625000",
        "end_exact": "34467/15625000",
        "bytes": 18944
      },
      {
        "start_exact": "34467/15625000",
        "end_exact": "65731/15625000",
        "bytes": 18944
      },
      {
        "start_exact": "65731/15625000",
        "end_exact": "56303/7812500",
        "bytes": 18944
      },
      {
        "start_exact": "56303/7812500",
        "end_exact": "14387/1562500",
        "bytes": 18944
      },
      {
        "start_exact": "14387/1562500",
        "end_exact": "38149/3125000",
        "bytes": 18944
      },
      {
        "start_exact": "38149/3125000",
        "end_exact": "222009/15625000",
        "bytes": 18944
      },
      {
        "start_exact": "222009/15625000",
        "end_exact": "67221/3906250",
        "bytes": 18944
      },
      {
        "start_exact": "67221/3906250",
        "end_exact": "75037/3906250",
        "bytes": 18944
      },
      {
        "start_exact": "75037/3906250",
        "end_exact": "347023/15625000",
        "bytes": 18944
      },
      {
        "start_exact": "347023/15625000",
        "end_exact": "378287/15625000",
        "bytes": 18944
      },
      {
        "start_exact": "378287/15625000",
        "end_exact": "212581/7812500",
        "bytes": 18944
      }
    ],
    "device": [
      {
        "start_exact": "3189/15625000",
        "end_exact": "34453/15625000",
        "bytes": 10752
      },
      {
        "start_exact": "34453/15625000",
        "end_exact": "65717/15625000",
        "bytes": 10752
      },
      {
        "start_exact": "65717/15625000",
        "end_exact": "14074/1953125",
        "bytes": 10752
      },
      {
        "start_exact": "14074/1953125",
        "end_exact": "17982/1953125",
        "bytes": 10752
      },
      {
        "start_exact": "17982/1953125",
        "end_exact": "190731/15625000",
        "bytes": 10752
      },
      {
        "start_exact": "190731/15625000",
        "end_exact": "44399/3125000",
        "bytes": 10752
      },
      {
        "start_exact": "44399/3125000",
        "end_exact": "26887/1562500",
        "bytes": 10752
      },
      {
        "start_exact": "26887/1562500",
        "end_exact": "150067/7812500",
        "bytes": 10752
      },
      {
        "start_exact": "150067/7812500",
        "end_exact": "347009/15625000",
        "bytes": 10752
      },
      {
        "start_exact": "347009/15625000",
        "end_exact": "378273/15625000",
        "bytes": 10752
      },
      {
        "start_exact": "378273/15625000",
        "end_exact": "106287/3906250",
        "bytes": 10752
      },
      {
        "start_exact": "106287/3906250",
        "end_exact": "114103/3906250",
        "bytes": 10752
      }
    ],
    "snapshot": [
      {
        "start_exact": "65717/15625000",
        "end_exact": "447971511/7812500",
        "bytes": 114670295040
      },
      {
        "start_exact": "17982/1953125",
        "end_exact": "895902351/7812500",
        "bytes": 114670295040
      },
      {
        "start_exact": "44399/3125000",
        "end_exact": "1343833191/7812500",
        "bytes": 114670295040
      },
      {
        "start_exact": "150067/7812500",
        "end_exact": "1791764031/7812500",
        "bytes": 114670295040
      },
      {
        "start_exact": "378273/15625000",
        "end_exact": "2239694871/7812500",
        "bytes": 114670295040
      },
      {
        "start_exact": "114103/3906250",
        "end_exact": "2687625711/7812500",
        "bytes": 114670295040
      }
    ]
  },
  "buffers": {
    "host": {
      "peak_reserved_bytes": 18944,
      "byte_seconds_exact": "1006783616/1953125"
    },
    "device": {
      "peak_reserved_bytes": 10752,
      "byte_seconds_exact": "609131712/1953125"
    },
    "snapshot": {
      "peak_reserved_bytes": 688021770240,
      "byte_seconds_exact": "10785897666903147264/78125"
    }
  },
  "summary": {
    "samples": 12,
    "valid_tokens": 6144,
    "padding_tokens": 0,
    "packs": 12,
    "input_storage_bytes": 98304,
    "h2d_bytes": 129024,
    "checkpoint_parameters": 8190735360,
    "checkpoint_bytes_each": 114670295040,
    "checkpoint_write_bytes": 688021770240,
    "cpu_core_seconds_exact": "3/1250",
    "training_end_exact": "114103/3906250",
    "all_durable_exact": "2687625711/7812500",
    "device_compute_service_exact": "3/125",
    "snapshot_service_before_training_end_exact": "1/200",
    "device_wait_exact": "3287/15625000",
    "target_sample_rate_exact": "500",
    "target_input_bytes_per_second_exact": "4096000",
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
