# 真实梯度的两级集合通信

参数：`model.layers.0.mlp.gate_proj.weight`；形状 [12288, 4096]；每rank 201,326,592 bytes。
组织：flat_interleaved；每服务器NIC数：2。

| 阶段 | 轮数 | 发送 bytes | 跨服务器发送 bytes | 串行屏障下界 seconds（精确） |
| --- | ---: | ---: | ---: | ---: |
| flat | 14 | 2818572288 | 2818572288 | 5509399/156250000 |

全网发送 2,818,572,288 bytes；跨服务器 2,818,572,288 bytes；标量归约加法 352,321,536 次。
串行屏障下界 5509399/156250000 seconds；预算未被此必要下界排除：True。实际训练期限是否可行仍未知。

| 物理资源 | bytes | 声明 bytes/s | 必要服务 seconds（精确） |
| --- | ---: | ---: | ---: |
| cut.0->1 | 1409286144 | 40000000000 | 344064/9765625 |
| cut.1->0 | 1409286144 | 40000000000 | 344064/9765625 |
| rank0.rx | 352321536 | 200000000000 | 86016/48828125 |
| rank0.tx | 352321536 | 200000000000 | 86016/48828125 |
| rank1.rx | 352321536 | 200000000000 | 86016/48828125 |
| rank1.tx | 352321536 | 200000000000 | 86016/48828125 |
| rank2.rx | 352321536 | 200000000000 | 86016/48828125 |
| rank2.tx | 352321536 | 200000000000 | 86016/48828125 |
| rank3.rx | 352321536 | 200000000000 | 86016/48828125 |
| rank3.tx | 352321536 | 200000000000 | 86016/48828125 |
| rank4.rx | 352321536 | 200000000000 | 86016/48828125 |
| rank4.tx | 352321536 | 200000000000 | 86016/48828125 |
| rank5.rx | 352321536 | 200000000000 | 86016/48828125 |
| rank5.tx | 352321536 | 200000000000 | 86016/48828125 |
| rank6.rx | 352321536 | 200000000000 | 86016/48828125 |
| rank6.tx | 352321536 | 200000000000 | 86016/48828125 |
| rank7.rx | 352321536 | 200000000000 | 86016/48828125 |
| rank7.tx | 352321536 | 200000000000 | 86016/48828125 |
| server0.egress | 1409286144 | 40000000000 | 344064/9765625 |
| server0.ingress | 1409286144 | 40000000000 | 344064/9765625 |
| server0.nic0.rx | 704643072 | 25000000000 | 1376256/48828125 |
| server0.nic0.tx | 704643072 | 25000000000 | 1376256/48828125 |
| server0.nic1.rx | 704643072 | 25000000000 | 1376256/48828125 |
| server0.nic1.tx | 704643072 | 25000000000 | 1376256/48828125 |
| server1.egress | 1409286144 | 40000000000 | 344064/9765625 |
| server1.ingress | 1409286144 | 40000000000 | 344064/9765625 |
| server1.nic0.rx | 704643072 | 25000000000 | 1376256/48828125 |
| server1.nic0.tx | 704643072 | 25000000000 | 1376256/48828125 |
| server1.nic1.rx | 704643072 | 25000000000 | 1376256/48828125 |
| server1.nic1.tx | 704643072 | 25000000000 | 1376256/48828125 |
| shared_cut.bidirectional | 2818572288 | 80000000000 | 344064/9765625 |

- One real first-layer gate parameter gradient per rank; each rank contributes different sample data to the same coordinates. Not activations, whole-model gradients, or framework buckets.
- FP32/BF16 are declared gradient wire/operand widths. Rank contribution identities prove algebraic sum coverage, not floating-point reassociation equivalence or backend accumulation precision.
- Two servers each own four fixed ranks. Hierarchy executes local RS, corresponding-owner two-rank AR, local AG with stage/round barriers; no overlapping stages or unmodeled algorithm substitutions.
- Remote messages stripe disjoint whole-element intervals over one/two NICs, never duplicate payload. Each source/destination NIC, shared egress/ingress and shared bidirectional cut has its own declared rate; shared40GB/s server edges do not grow with NIC count.
- All rates and startup are teaching inputs. Each round bound is max(resource bytes/rate)+startup; serialized barrier bounds omit reduction work, propagation, buffering, topology latency and interference. They are not executable timing or deadline guarantees.
- Logical network sends count payload once. Endpoint receive, NIC, ingress and cut counters represent distinct resource demands; their sum is not additional gradient payload or HBM traffic.
- No padding is introduced. Missing paths/resources or invalid rates reject. Budget pass only means this communication lower bound has not excluded the candidate; real training feasibility remains unknown.

完整逐轮消息、NIC区间和贡献身份：

```json
{
  "calculation": "hierarchical-gradient",
  "scenario": {
    "model": "qwen3-8b",
    "gradient_dtype": "FP32",
    "algorithm": "flat_interleaved",
    "nics_per_server": 2,
    "startup_ns": 2000,
    "budget_ns": 40000000,
    "bandwidth_overrides": null
  },
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
  "gradient": {
    "parameter": "model.layers.0.mlp.gate_proj.weight",
    "template": "model.layers.{layer}.mlp.gate_proj.weight",
    "shape": [
      12288,
      4096
    ],
    "elements": 50331648,
    "bytes_per_element": 4,
    "bytes_per_rank": 201326592,
    "selected_parameter_copies": 1,
    "template_layer_copies": 36,
    "initial_contributors_per_rank": 1,
    "chunks": 8,
    "chunk_elements": 6291456
  },
  "rank_mapping": [
    {
      "rank": 0,
      "server": 0,
      "card": 0
    },
    {
      "rank": 1,
      "server": 0,
      "card": 1
    },
    {
      "rank": 2,
      "server": 0,
      "card": 2
    },
    {
      "rank": 3,
      "server": 0,
      "card": 3
    },
    {
      "rank": 4,
      "server": 1,
      "card": 0
    },
    {
      "rank": 5,
      "server": 1,
      "card": 1
    },
    {
      "rank": 6,
      "server": 1,
      "card": 2
    },
    {
      "rank": 7,
      "server": 1,
      "card": 3
    }
  ],
  "flat_ring_order": [
    0,
    4,
    1,
    5,
    2,
    6,
    3,
    7
  ],
  "rounds": [
    {
      "round": 0,
      "stage": "flat",
      "phase": "reduce_scatter",
      "step": 0,
      "messages": [
        {
          "sender": 0,
          "receiver": 4,
          "operation": "reduce",
          "chunks": [
            0
          ],
          "element_start": 0,
          "element_stop": 6291456,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 0,
              "contributors": [
                0
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r0:nic0",
              "receiver": "r4:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 0,
              "element_stop": 3145728,
              "path": [
                "rank0.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank4.rx"
              ]
            },
            {
              "sender": "r0:nic1",
              "receiver": "r4:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 3145728,
              "element_stop": 6291456,
              "path": [
                "rank0.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank4.rx"
              ]
            }
          ]
        },
        {
          "sender": 4,
          "receiver": 1,
          "operation": "reduce",
          "chunks": [
            1
          ],
          "element_start": 6291456,
          "element_stop": 12582912,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 1,
              "contributors": [
                4
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r4:nic0",
              "receiver": "r1:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 6291456,
              "element_stop": 9437184,
              "path": [
                "rank4.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank1.rx"
              ]
            },
            {
              "sender": "r4:nic1",
              "receiver": "r1:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 9437184,
              "element_stop": 12582912,
              "path": [
                "rank4.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank1.rx"
              ]
            }
          ]
        },
        {
          "sender": 1,
          "receiver": 5,
          "operation": "reduce",
          "chunks": [
            2
          ],
          "element_start": 12582912,
          "element_stop": 18874368,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 2,
              "contributors": [
                1
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r1:nic0",
              "receiver": "r5:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 12582912,
              "element_stop": 15728640,
              "path": [
                "rank1.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank5.rx"
              ]
            },
            {
              "sender": "r1:nic1",
              "receiver": "r5:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 15728640,
              "element_stop": 18874368,
              "path": [
                "rank1.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank5.rx"
              ]
            }
          ]
        },
        {
          "sender": 5,
          "receiver": 2,
          "operation": "reduce",
          "chunks": [
            3
          ],
          "element_start": 18874368,
          "element_stop": 25165824,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 3,
              "contributors": [
                5
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r5:nic0",
              "receiver": "r2:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 18874368,
              "element_stop": 22020096,
              "path": [
                "rank5.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank2.rx"
              ]
            },
            {
              "sender": "r5:nic1",
              "receiver": "r2:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 22020096,
              "element_stop": 25165824,
              "path": [
                "rank5.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank2.rx"
              ]
            }
          ]
        },
        {
          "sender": 2,
          "receiver": 6,
          "operation": "reduce",
          "chunks": [
            4
          ],
          "element_start": 25165824,
          "element_stop": 31457280,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 4,
              "contributors": [
                2
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r2:nic0",
              "receiver": "r6:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 25165824,
              "element_stop": 28311552,
              "path": [
                "rank2.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank6.rx"
              ]
            },
            {
              "sender": "r2:nic1",
              "receiver": "r6:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 28311552,
              "element_stop": 31457280,
              "path": [
                "rank2.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank6.rx"
              ]
            }
          ]
        },
        {
          "sender": 6,
          "receiver": 3,
          "operation": "reduce",
          "chunks": [
            5
          ],
          "element_start": 31457280,
          "element_stop": 37748736,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 5,
              "contributors": [
                6
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r6:nic0",
              "receiver": "r3:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 31457280,
              "element_stop": 34603008,
              "path": [
                "rank6.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank3.rx"
              ]
            },
            {
              "sender": "r6:nic1",
              "receiver": "r3:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 34603008,
              "element_stop": 37748736,
              "path": [
                "rank6.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank3.rx"
              ]
            }
          ]
        },
        {
          "sender": 3,
          "receiver": 7,
          "operation": "reduce",
          "chunks": [
            6
          ],
          "element_start": 37748736,
          "element_stop": 44040192,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 6,
              "contributors": [
                3
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r3:nic0",
              "receiver": "r7:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 37748736,
              "element_stop": 40894464,
              "path": [
                "rank3.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank7.rx"
              ]
            },
            {
              "sender": "r3:nic1",
              "receiver": "r7:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 40894464,
              "element_stop": 44040192,
              "path": [
                "rank3.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank7.rx"
              ]
            }
          ]
        },
        {
          "sender": 7,
          "receiver": 0,
          "operation": "reduce",
          "chunks": [
            7
          ],
          "element_start": 44040192,
          "element_stop": 50331648,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 7,
              "contributors": [
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r7:nic0",
              "receiver": "r0:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 44040192,
              "element_stop": 47185920,
              "path": [
                "rank7.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank0.rx"
              ]
            },
            {
              "sender": "r7:nic1",
              "receiver": "r0:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 47185920,
              "element_stop": 50331648,
              "path": [
                "rank7.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank0.rx"
              ]
            }
          ]
        }
      ],
      "edges": [
        {
          "sender": "r0:nic0",
          "receiver": "r4:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 0,
          "element_stop": 3145728,
          "path": [
            "rank0.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank4.rx"
          ]
        },
        {
          "sender": "r0:nic1",
          "receiver": "r4:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 3145728,
          "element_stop": 6291456,
          "path": [
            "rank0.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank4.rx"
          ]
        },
        {
          "sender": "r4:nic0",
          "receiver": "r1:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 6291456,
          "element_stop": 9437184,
          "path": [
            "rank4.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank1.rx"
          ]
        },
        {
          "sender": "r4:nic1",
          "receiver": "r1:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 9437184,
          "element_stop": 12582912,
          "path": [
            "rank4.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank1.rx"
          ]
        },
        {
          "sender": "r1:nic0",
          "receiver": "r5:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 12582912,
          "element_stop": 15728640,
          "path": [
            "rank1.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank5.rx"
          ]
        },
        {
          "sender": "r1:nic1",
          "receiver": "r5:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 15728640,
          "element_stop": 18874368,
          "path": [
            "rank1.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank5.rx"
          ]
        },
        {
          "sender": "r5:nic0",
          "receiver": "r2:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 18874368,
          "element_stop": 22020096,
          "path": [
            "rank5.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank2.rx"
          ]
        },
        {
          "sender": "r5:nic1",
          "receiver": "r2:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 22020096,
          "element_stop": 25165824,
          "path": [
            "rank5.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank2.rx"
          ]
        },
        {
          "sender": "r2:nic0",
          "receiver": "r6:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 25165824,
          "element_stop": 28311552,
          "path": [
            "rank2.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank6.rx"
          ]
        },
        {
          "sender": "r2:nic1",
          "receiver": "r6:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 28311552,
          "element_stop": 31457280,
          "path": [
            "rank2.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank6.rx"
          ]
        },
        {
          "sender": "r6:nic0",
          "receiver": "r3:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 31457280,
          "element_stop": 34603008,
          "path": [
            "rank6.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank3.rx"
          ]
        },
        {
          "sender": "r6:nic1",
          "receiver": "r3:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 34603008,
          "element_stop": 37748736,
          "path": [
            "rank6.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank3.rx"
          ]
        },
        {
          "sender": "r3:nic0",
          "receiver": "r7:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 37748736,
          "element_stop": 40894464,
          "path": [
            "rank3.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank7.rx"
          ]
        },
        {
          "sender": "r3:nic1",
          "receiver": "r7:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 40894464,
          "element_stop": 44040192,
          "path": [
            "rank3.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank7.rx"
          ]
        },
        {
          "sender": "r7:nic0",
          "receiver": "r0:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 44040192,
          "element_stop": 47185920,
          "path": [
            "rank7.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank0.rx"
          ]
        },
        {
          "sender": "r7:nic1",
          "receiver": "r0:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 47185920,
          "element_stop": 50331648,
          "path": [
            "rank7.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank0.rx"
          ]
        }
      ],
      "resource_bytes": {
        "rank0.tx": 25165824,
        "server0.nic0.tx": 50331648,
        "server0.egress": 100663296,
        "cut.0->1": 100663296,
        "shared_cut.bidirectional": 201326592,
        "server1.ingress": 100663296,
        "server1.nic0.rx": 50331648,
        "rank4.rx": 25165824,
        "server0.nic1.tx": 50331648,
        "server1.nic1.rx": 50331648,
        "rank4.tx": 25165824,
        "server1.nic0.tx": 50331648,
        "server1.egress": 100663296,
        "cut.1->0": 100663296,
        "server0.ingress": 100663296,
        "server0.nic0.rx": 50331648,
        "rank1.rx": 25165824,
        "server1.nic1.tx": 50331648,
        "server0.nic1.rx": 50331648,
        "rank1.tx": 25165824,
        "rank5.rx": 25165824,
        "rank5.tx": 25165824,
        "rank2.rx": 25165824,
        "rank2.tx": 25165824,
        "rank6.rx": 25165824,
        "rank6.tx": 25165824,
        "rank3.rx": 25165824,
        "rank3.tx": 25165824,
        "rank7.rx": 25165824,
        "rank7.tx": 25165824,
        "rank0.rx": 25165824
      },
      "resource_lower_seconds_exact": "24576/9765625",
      "barrier_lower_seconds_exact": "787057/312500000",
      "barrier_start_seconds_exact": "0",
      "barrier_finish_seconds_exact": "787057/312500000"
    },
    {
      "round": 1,
      "stage": "flat",
      "phase": "reduce_scatter",
      "step": 1,
      "messages": [
        {
          "sender": 0,
          "receiver": 4,
          "operation": "reduce",
          "chunks": [
            7
          ],
          "element_start": 44040192,
          "element_stop": 50331648,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 7,
              "contributors": [
                0,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r0:nic0",
              "receiver": "r4:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 44040192,
              "element_stop": 47185920,
              "path": [
                "rank0.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank4.rx"
              ]
            },
            {
              "sender": "r0:nic1",
              "receiver": "r4:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 47185920,
              "element_stop": 50331648,
              "path": [
                "rank0.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank4.rx"
              ]
            }
          ]
        },
        {
          "sender": 4,
          "receiver": 1,
          "operation": "reduce",
          "chunks": [
            0
          ],
          "element_start": 0,
          "element_stop": 6291456,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 0,
              "contributors": [
                0,
                4
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r4:nic0",
              "receiver": "r1:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 0,
              "element_stop": 3145728,
              "path": [
                "rank4.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank1.rx"
              ]
            },
            {
              "sender": "r4:nic1",
              "receiver": "r1:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 3145728,
              "element_stop": 6291456,
              "path": [
                "rank4.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank1.rx"
              ]
            }
          ]
        },
        {
          "sender": 1,
          "receiver": 5,
          "operation": "reduce",
          "chunks": [
            1
          ],
          "element_start": 6291456,
          "element_stop": 12582912,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 1,
              "contributors": [
                1,
                4
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r1:nic0",
              "receiver": "r5:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 6291456,
              "element_stop": 9437184,
              "path": [
                "rank1.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank5.rx"
              ]
            },
            {
              "sender": "r1:nic1",
              "receiver": "r5:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 9437184,
              "element_stop": 12582912,
              "path": [
                "rank1.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank5.rx"
              ]
            }
          ]
        },
        {
          "sender": 5,
          "receiver": 2,
          "operation": "reduce",
          "chunks": [
            2
          ],
          "element_start": 12582912,
          "element_stop": 18874368,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 2,
              "contributors": [
                1,
                5
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r5:nic0",
              "receiver": "r2:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 12582912,
              "element_stop": 15728640,
              "path": [
                "rank5.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank2.rx"
              ]
            },
            {
              "sender": "r5:nic1",
              "receiver": "r2:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 15728640,
              "element_stop": 18874368,
              "path": [
                "rank5.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank2.rx"
              ]
            }
          ]
        },
        {
          "sender": 2,
          "receiver": 6,
          "operation": "reduce",
          "chunks": [
            3
          ],
          "element_start": 18874368,
          "element_stop": 25165824,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 3,
              "contributors": [
                2,
                5
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r2:nic0",
              "receiver": "r6:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 18874368,
              "element_stop": 22020096,
              "path": [
                "rank2.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank6.rx"
              ]
            },
            {
              "sender": "r2:nic1",
              "receiver": "r6:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 22020096,
              "element_stop": 25165824,
              "path": [
                "rank2.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank6.rx"
              ]
            }
          ]
        },
        {
          "sender": 6,
          "receiver": 3,
          "operation": "reduce",
          "chunks": [
            4
          ],
          "element_start": 25165824,
          "element_stop": 31457280,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 4,
              "contributors": [
                2,
                6
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r6:nic0",
              "receiver": "r3:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 25165824,
              "element_stop": 28311552,
              "path": [
                "rank6.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank3.rx"
              ]
            },
            {
              "sender": "r6:nic1",
              "receiver": "r3:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 28311552,
              "element_stop": 31457280,
              "path": [
                "rank6.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank3.rx"
              ]
            }
          ]
        },
        {
          "sender": 3,
          "receiver": 7,
          "operation": "reduce",
          "chunks": [
            5
          ],
          "element_start": 31457280,
          "element_stop": 37748736,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 5,
              "contributors": [
                3,
                6
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r3:nic0",
              "receiver": "r7:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 31457280,
              "element_stop": 34603008,
              "path": [
                "rank3.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank7.rx"
              ]
            },
            {
              "sender": "r3:nic1",
              "receiver": "r7:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 34603008,
              "element_stop": 37748736,
              "path": [
                "rank3.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank7.rx"
              ]
            }
          ]
        },
        {
          "sender": 7,
          "receiver": 0,
          "operation": "reduce",
          "chunks": [
            6
          ],
          "element_start": 37748736,
          "element_stop": 44040192,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 6,
              "contributors": [
                3,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r7:nic0",
              "receiver": "r0:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 37748736,
              "element_stop": 40894464,
              "path": [
                "rank7.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank0.rx"
              ]
            },
            {
              "sender": "r7:nic1",
              "receiver": "r0:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 40894464,
              "element_stop": 44040192,
              "path": [
                "rank7.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank0.rx"
              ]
            }
          ]
        }
      ],
      "edges": [
        {
          "sender": "r0:nic0",
          "receiver": "r4:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 44040192,
          "element_stop": 47185920,
          "path": [
            "rank0.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank4.rx"
          ]
        },
        {
          "sender": "r0:nic1",
          "receiver": "r4:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 47185920,
          "element_stop": 50331648,
          "path": [
            "rank0.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank4.rx"
          ]
        },
        {
          "sender": "r4:nic0",
          "receiver": "r1:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 0,
          "element_stop": 3145728,
          "path": [
            "rank4.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank1.rx"
          ]
        },
        {
          "sender": "r4:nic1",
          "receiver": "r1:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 3145728,
          "element_stop": 6291456,
          "path": [
            "rank4.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank1.rx"
          ]
        },
        {
          "sender": "r1:nic0",
          "receiver": "r5:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 6291456,
          "element_stop": 9437184,
          "path": [
            "rank1.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank5.rx"
          ]
        },
        {
          "sender": "r1:nic1",
          "receiver": "r5:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 9437184,
          "element_stop": 12582912,
          "path": [
            "rank1.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank5.rx"
          ]
        },
        {
          "sender": "r5:nic0",
          "receiver": "r2:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 12582912,
          "element_stop": 15728640,
          "path": [
            "rank5.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank2.rx"
          ]
        },
        {
          "sender": "r5:nic1",
          "receiver": "r2:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 15728640,
          "element_stop": 18874368,
          "path": [
            "rank5.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank2.rx"
          ]
        },
        {
          "sender": "r2:nic0",
          "receiver": "r6:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 18874368,
          "element_stop": 22020096,
          "path": [
            "rank2.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank6.rx"
          ]
        },
        {
          "sender": "r2:nic1",
          "receiver": "r6:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 22020096,
          "element_stop": 25165824,
          "path": [
            "rank2.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank6.rx"
          ]
        },
        {
          "sender": "r6:nic0",
          "receiver": "r3:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 25165824,
          "element_stop": 28311552,
          "path": [
            "rank6.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank3.rx"
          ]
        },
        {
          "sender": "r6:nic1",
          "receiver": "r3:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 28311552,
          "element_stop": 31457280,
          "path": [
            "rank6.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank3.rx"
          ]
        },
        {
          "sender": "r3:nic0",
          "receiver": "r7:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 31457280,
          "element_stop": 34603008,
          "path": [
            "rank3.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank7.rx"
          ]
        },
        {
          "sender": "r3:nic1",
          "receiver": "r7:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 34603008,
          "element_stop": 37748736,
          "path": [
            "rank3.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank7.rx"
          ]
        },
        {
          "sender": "r7:nic0",
          "receiver": "r0:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 37748736,
          "element_stop": 40894464,
          "path": [
            "rank7.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank0.rx"
          ]
        },
        {
          "sender": "r7:nic1",
          "receiver": "r0:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 40894464,
          "element_stop": 44040192,
          "path": [
            "rank7.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank0.rx"
          ]
        }
      ],
      "resource_bytes": {
        "rank0.tx": 25165824,
        "server0.nic0.tx": 50331648,
        "server0.egress": 100663296,
        "cut.0->1": 100663296,
        "shared_cut.bidirectional": 201326592,
        "server1.ingress": 100663296,
        "server1.nic0.rx": 50331648,
        "rank4.rx": 25165824,
        "server0.nic1.tx": 50331648,
        "server1.nic1.rx": 50331648,
        "rank4.tx": 25165824,
        "server1.nic0.tx": 50331648,
        "server1.egress": 100663296,
        "cut.1->0": 100663296,
        "server0.ingress": 100663296,
        "server0.nic0.rx": 50331648,
        "rank1.rx": 25165824,
        "server1.nic1.tx": 50331648,
        "server0.nic1.rx": 50331648,
        "rank1.tx": 25165824,
        "rank5.rx": 25165824,
        "rank5.tx": 25165824,
        "rank2.rx": 25165824,
        "rank2.tx": 25165824,
        "rank6.rx": 25165824,
        "rank6.tx": 25165824,
        "rank3.rx": 25165824,
        "rank3.tx": 25165824,
        "rank7.rx": 25165824,
        "rank7.tx": 25165824,
        "rank0.rx": 25165824
      },
      "resource_lower_seconds_exact": "24576/9765625",
      "barrier_lower_seconds_exact": "787057/312500000",
      "barrier_start_seconds_exact": "787057/312500000",
      "barrier_finish_seconds_exact": "787057/156250000"
    },
    {
      "round": 2,
      "stage": "flat",
      "phase": "reduce_scatter",
      "step": 2,
      "messages": [
        {
          "sender": 0,
          "receiver": 4,
          "operation": "reduce",
          "chunks": [
            6
          ],
          "element_start": 37748736,
          "element_stop": 44040192,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 6,
              "contributors": [
                0,
                3,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r0:nic0",
              "receiver": "r4:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 37748736,
              "element_stop": 40894464,
              "path": [
                "rank0.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank4.rx"
              ]
            },
            {
              "sender": "r0:nic1",
              "receiver": "r4:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 40894464,
              "element_stop": 44040192,
              "path": [
                "rank0.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank4.rx"
              ]
            }
          ]
        },
        {
          "sender": 4,
          "receiver": 1,
          "operation": "reduce",
          "chunks": [
            7
          ],
          "element_start": 44040192,
          "element_stop": 50331648,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 7,
              "contributors": [
                0,
                4,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r4:nic0",
              "receiver": "r1:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 44040192,
              "element_stop": 47185920,
              "path": [
                "rank4.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank1.rx"
              ]
            },
            {
              "sender": "r4:nic1",
              "receiver": "r1:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 47185920,
              "element_stop": 50331648,
              "path": [
                "rank4.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank1.rx"
              ]
            }
          ]
        },
        {
          "sender": 1,
          "receiver": 5,
          "operation": "reduce",
          "chunks": [
            0
          ],
          "element_start": 0,
          "element_stop": 6291456,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 0,
              "contributors": [
                0,
                1,
                4
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r1:nic0",
              "receiver": "r5:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 0,
              "element_stop": 3145728,
              "path": [
                "rank1.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank5.rx"
              ]
            },
            {
              "sender": "r1:nic1",
              "receiver": "r5:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 3145728,
              "element_stop": 6291456,
              "path": [
                "rank1.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank5.rx"
              ]
            }
          ]
        },
        {
          "sender": 5,
          "receiver": 2,
          "operation": "reduce",
          "chunks": [
            1
          ],
          "element_start": 6291456,
          "element_stop": 12582912,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 1,
              "contributors": [
                1,
                4,
                5
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r5:nic0",
              "receiver": "r2:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 6291456,
              "element_stop": 9437184,
              "path": [
                "rank5.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank2.rx"
              ]
            },
            {
              "sender": "r5:nic1",
              "receiver": "r2:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 9437184,
              "element_stop": 12582912,
              "path": [
                "rank5.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank2.rx"
              ]
            }
          ]
        },
        {
          "sender": 2,
          "receiver": 6,
          "operation": "reduce",
          "chunks": [
            2
          ],
          "element_start": 12582912,
          "element_stop": 18874368,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 2,
              "contributors": [
                1,
                2,
                5
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r2:nic0",
              "receiver": "r6:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 12582912,
              "element_stop": 15728640,
              "path": [
                "rank2.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank6.rx"
              ]
            },
            {
              "sender": "r2:nic1",
              "receiver": "r6:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 15728640,
              "element_stop": 18874368,
              "path": [
                "rank2.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank6.rx"
              ]
            }
          ]
        },
        {
          "sender": 6,
          "receiver": 3,
          "operation": "reduce",
          "chunks": [
            3
          ],
          "element_start": 18874368,
          "element_stop": 25165824,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 3,
              "contributors": [
                2,
                5,
                6
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r6:nic0",
              "receiver": "r3:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 18874368,
              "element_stop": 22020096,
              "path": [
                "rank6.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank3.rx"
              ]
            },
            {
              "sender": "r6:nic1",
              "receiver": "r3:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 22020096,
              "element_stop": 25165824,
              "path": [
                "rank6.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank3.rx"
              ]
            }
          ]
        },
        {
          "sender": 3,
          "receiver": 7,
          "operation": "reduce",
          "chunks": [
            4
          ],
          "element_start": 25165824,
          "element_stop": 31457280,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 4,
              "contributors": [
                2,
                3,
                6
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r3:nic0",
              "receiver": "r7:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 25165824,
              "element_stop": 28311552,
              "path": [
                "rank3.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank7.rx"
              ]
            },
            {
              "sender": "r3:nic1",
              "receiver": "r7:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 28311552,
              "element_stop": 31457280,
              "path": [
                "rank3.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank7.rx"
              ]
            }
          ]
        },
        {
          "sender": 7,
          "receiver": 0,
          "operation": "reduce",
          "chunks": [
            5
          ],
          "element_start": 31457280,
          "element_stop": 37748736,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 5,
              "contributors": [
                3,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r7:nic0",
              "receiver": "r0:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 31457280,
              "element_stop": 34603008,
              "path": [
                "rank7.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank0.rx"
              ]
            },
            {
              "sender": "r7:nic1",
              "receiver": "r0:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 34603008,
              "element_stop": 37748736,
              "path": [
                "rank7.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank0.rx"
              ]
            }
          ]
        }
      ],
      "edges": [
        {
          "sender": "r0:nic0",
          "receiver": "r4:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 37748736,
          "element_stop": 40894464,
          "path": [
            "rank0.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank4.rx"
          ]
        },
        {
          "sender": "r0:nic1",
          "receiver": "r4:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 40894464,
          "element_stop": 44040192,
          "path": [
            "rank0.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank4.rx"
          ]
        },
        {
          "sender": "r4:nic0",
          "receiver": "r1:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 44040192,
          "element_stop": 47185920,
          "path": [
            "rank4.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank1.rx"
          ]
        },
        {
          "sender": "r4:nic1",
          "receiver": "r1:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 47185920,
          "element_stop": 50331648,
          "path": [
            "rank4.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank1.rx"
          ]
        },
        {
          "sender": "r1:nic0",
          "receiver": "r5:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 0,
          "element_stop": 3145728,
          "path": [
            "rank1.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank5.rx"
          ]
        },
        {
          "sender": "r1:nic1",
          "receiver": "r5:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 3145728,
          "element_stop": 6291456,
          "path": [
            "rank1.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank5.rx"
          ]
        },
        {
          "sender": "r5:nic0",
          "receiver": "r2:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 6291456,
          "element_stop": 9437184,
          "path": [
            "rank5.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank2.rx"
          ]
        },
        {
          "sender": "r5:nic1",
          "receiver": "r2:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 9437184,
          "element_stop": 12582912,
          "path": [
            "rank5.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank2.rx"
          ]
        },
        {
          "sender": "r2:nic0",
          "receiver": "r6:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 12582912,
          "element_stop": 15728640,
          "path": [
            "rank2.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank6.rx"
          ]
        },
        {
          "sender": "r2:nic1",
          "receiver": "r6:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 15728640,
          "element_stop": 18874368,
          "path": [
            "rank2.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank6.rx"
          ]
        },
        {
          "sender": "r6:nic0",
          "receiver": "r3:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 18874368,
          "element_stop": 22020096,
          "path": [
            "rank6.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank3.rx"
          ]
        },
        {
          "sender": "r6:nic1",
          "receiver": "r3:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 22020096,
          "element_stop": 25165824,
          "path": [
            "rank6.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank3.rx"
          ]
        },
        {
          "sender": "r3:nic0",
          "receiver": "r7:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 25165824,
          "element_stop": 28311552,
          "path": [
            "rank3.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank7.rx"
          ]
        },
        {
          "sender": "r3:nic1",
          "receiver": "r7:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 28311552,
          "element_stop": 31457280,
          "path": [
            "rank3.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank7.rx"
          ]
        },
        {
          "sender": "r7:nic0",
          "receiver": "r0:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 31457280,
          "element_stop": 34603008,
          "path": [
            "rank7.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank0.rx"
          ]
        },
        {
          "sender": "r7:nic1",
          "receiver": "r0:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 34603008,
          "element_stop": 37748736,
          "path": [
            "rank7.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank0.rx"
          ]
        }
      ],
      "resource_bytes": {
        "rank0.tx": 25165824,
        "server0.nic0.tx": 50331648,
        "server0.egress": 100663296,
        "cut.0->1": 100663296,
        "shared_cut.bidirectional": 201326592,
        "server1.ingress": 100663296,
        "server1.nic0.rx": 50331648,
        "rank4.rx": 25165824,
        "server0.nic1.tx": 50331648,
        "server1.nic1.rx": 50331648,
        "rank4.tx": 25165824,
        "server1.nic0.tx": 50331648,
        "server1.egress": 100663296,
        "cut.1->0": 100663296,
        "server0.ingress": 100663296,
        "server0.nic0.rx": 50331648,
        "rank1.rx": 25165824,
        "server1.nic1.tx": 50331648,
        "server0.nic1.rx": 50331648,
        "rank1.tx": 25165824,
        "rank5.rx": 25165824,
        "rank5.tx": 25165824,
        "rank2.rx": 25165824,
        "rank2.tx": 25165824,
        "rank6.rx": 25165824,
        "rank6.tx": 25165824,
        "rank3.rx": 25165824,
        "rank3.tx": 25165824,
        "rank7.rx": 25165824,
        "rank7.tx": 25165824,
        "rank0.rx": 25165824
      },
      "resource_lower_seconds_exact": "24576/9765625",
      "barrier_lower_seconds_exact": "787057/312500000",
      "barrier_start_seconds_exact": "787057/156250000",
      "barrier_finish_seconds_exact": "2361171/312500000"
    },
    {
      "round": 3,
      "stage": "flat",
      "phase": "reduce_scatter",
      "step": 3,
      "messages": [
        {
          "sender": 0,
          "receiver": 4,
          "operation": "reduce",
          "chunks": [
            5
          ],
          "element_start": 31457280,
          "element_stop": 37748736,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 5,
              "contributors": [
                0,
                3,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r0:nic0",
              "receiver": "r4:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 31457280,
              "element_stop": 34603008,
              "path": [
                "rank0.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank4.rx"
              ]
            },
            {
              "sender": "r0:nic1",
              "receiver": "r4:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 34603008,
              "element_stop": 37748736,
              "path": [
                "rank0.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank4.rx"
              ]
            }
          ]
        },
        {
          "sender": 4,
          "receiver": 1,
          "operation": "reduce",
          "chunks": [
            6
          ],
          "element_start": 37748736,
          "element_stop": 44040192,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 6,
              "contributors": [
                0,
                3,
                4,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r4:nic0",
              "receiver": "r1:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 37748736,
              "element_stop": 40894464,
              "path": [
                "rank4.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank1.rx"
              ]
            },
            {
              "sender": "r4:nic1",
              "receiver": "r1:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 40894464,
              "element_stop": 44040192,
              "path": [
                "rank4.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank1.rx"
              ]
            }
          ]
        },
        {
          "sender": 1,
          "receiver": 5,
          "operation": "reduce",
          "chunks": [
            7
          ],
          "element_start": 44040192,
          "element_stop": 50331648,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 7,
              "contributors": [
                0,
                1,
                4,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r1:nic0",
              "receiver": "r5:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 44040192,
              "element_stop": 47185920,
              "path": [
                "rank1.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank5.rx"
              ]
            },
            {
              "sender": "r1:nic1",
              "receiver": "r5:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 47185920,
              "element_stop": 50331648,
              "path": [
                "rank1.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank5.rx"
              ]
            }
          ]
        },
        {
          "sender": 5,
          "receiver": 2,
          "operation": "reduce",
          "chunks": [
            0
          ],
          "element_start": 0,
          "element_stop": 6291456,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 0,
              "contributors": [
                0,
                1,
                4,
                5
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r5:nic0",
              "receiver": "r2:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 0,
              "element_stop": 3145728,
              "path": [
                "rank5.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank2.rx"
              ]
            },
            {
              "sender": "r5:nic1",
              "receiver": "r2:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 3145728,
              "element_stop": 6291456,
              "path": [
                "rank5.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank2.rx"
              ]
            }
          ]
        },
        {
          "sender": 2,
          "receiver": 6,
          "operation": "reduce",
          "chunks": [
            1
          ],
          "element_start": 6291456,
          "element_stop": 12582912,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 1,
              "contributors": [
                1,
                2,
                4,
                5
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r2:nic0",
              "receiver": "r6:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 6291456,
              "element_stop": 9437184,
              "path": [
                "rank2.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank6.rx"
              ]
            },
            {
              "sender": "r2:nic1",
              "receiver": "r6:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 9437184,
              "element_stop": 12582912,
              "path": [
                "rank2.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank6.rx"
              ]
            }
          ]
        },
        {
          "sender": 6,
          "receiver": 3,
          "operation": "reduce",
          "chunks": [
            2
          ],
          "element_start": 12582912,
          "element_stop": 18874368,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 2,
              "contributors": [
                1,
                2,
                5,
                6
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r6:nic0",
              "receiver": "r3:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 12582912,
              "element_stop": 15728640,
              "path": [
                "rank6.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank3.rx"
              ]
            },
            {
              "sender": "r6:nic1",
              "receiver": "r3:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 15728640,
              "element_stop": 18874368,
              "path": [
                "rank6.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank3.rx"
              ]
            }
          ]
        },
        {
          "sender": 3,
          "receiver": 7,
          "operation": "reduce",
          "chunks": [
            3
          ],
          "element_start": 18874368,
          "element_stop": 25165824,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 3,
              "contributors": [
                2,
                3,
                5,
                6
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r3:nic0",
              "receiver": "r7:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 18874368,
              "element_stop": 22020096,
              "path": [
                "rank3.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank7.rx"
              ]
            },
            {
              "sender": "r3:nic1",
              "receiver": "r7:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 22020096,
              "element_stop": 25165824,
              "path": [
                "rank3.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank7.rx"
              ]
            }
          ]
        },
        {
          "sender": 7,
          "receiver": 0,
          "operation": "reduce",
          "chunks": [
            4
          ],
          "element_start": 25165824,
          "element_stop": 31457280,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 4,
              "contributors": [
                2,
                3,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r7:nic0",
              "receiver": "r0:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 25165824,
              "element_stop": 28311552,
              "path": [
                "rank7.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank0.rx"
              ]
            },
            {
              "sender": "r7:nic1",
              "receiver": "r0:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 28311552,
              "element_stop": 31457280,
              "path": [
                "rank7.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank0.rx"
              ]
            }
          ]
        }
      ],
      "edges": [
        {
          "sender": "r0:nic0",
          "receiver": "r4:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 31457280,
          "element_stop": 34603008,
          "path": [
            "rank0.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank4.rx"
          ]
        },
        {
          "sender": "r0:nic1",
          "receiver": "r4:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 34603008,
          "element_stop": 37748736,
          "path": [
            "rank0.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank4.rx"
          ]
        },
        {
          "sender": "r4:nic0",
          "receiver": "r1:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 37748736,
          "element_stop": 40894464,
          "path": [
            "rank4.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank1.rx"
          ]
        },
        {
          "sender": "r4:nic1",
          "receiver": "r1:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 40894464,
          "element_stop": 44040192,
          "path": [
            "rank4.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank1.rx"
          ]
        },
        {
          "sender": "r1:nic0",
          "receiver": "r5:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 44040192,
          "element_stop": 47185920,
          "path": [
            "rank1.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank5.rx"
          ]
        },
        {
          "sender": "r1:nic1",
          "receiver": "r5:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 47185920,
          "element_stop": 50331648,
          "path": [
            "rank1.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank5.rx"
          ]
        },
        {
          "sender": "r5:nic0",
          "receiver": "r2:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 0,
          "element_stop": 3145728,
          "path": [
            "rank5.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank2.rx"
          ]
        },
        {
          "sender": "r5:nic1",
          "receiver": "r2:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 3145728,
          "element_stop": 6291456,
          "path": [
            "rank5.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank2.rx"
          ]
        },
        {
          "sender": "r2:nic0",
          "receiver": "r6:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 6291456,
          "element_stop": 9437184,
          "path": [
            "rank2.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank6.rx"
          ]
        },
        {
          "sender": "r2:nic1",
          "receiver": "r6:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 9437184,
          "element_stop": 12582912,
          "path": [
            "rank2.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank6.rx"
          ]
        },
        {
          "sender": "r6:nic0",
          "receiver": "r3:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 12582912,
          "element_stop": 15728640,
          "path": [
            "rank6.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank3.rx"
          ]
        },
        {
          "sender": "r6:nic1",
          "receiver": "r3:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 15728640,
          "element_stop": 18874368,
          "path": [
            "rank6.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank3.rx"
          ]
        },
        {
          "sender": "r3:nic0",
          "receiver": "r7:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 18874368,
          "element_stop": 22020096,
          "path": [
            "rank3.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank7.rx"
          ]
        },
        {
          "sender": "r3:nic1",
          "receiver": "r7:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 22020096,
          "element_stop": 25165824,
          "path": [
            "rank3.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank7.rx"
          ]
        },
        {
          "sender": "r7:nic0",
          "receiver": "r0:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 25165824,
          "element_stop": 28311552,
          "path": [
            "rank7.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank0.rx"
          ]
        },
        {
          "sender": "r7:nic1",
          "receiver": "r0:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 28311552,
          "element_stop": 31457280,
          "path": [
            "rank7.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank0.rx"
          ]
        }
      ],
      "resource_bytes": {
        "rank0.tx": 25165824,
        "server0.nic0.tx": 50331648,
        "server0.egress": 100663296,
        "cut.0->1": 100663296,
        "shared_cut.bidirectional": 201326592,
        "server1.ingress": 100663296,
        "server1.nic0.rx": 50331648,
        "rank4.rx": 25165824,
        "server0.nic1.tx": 50331648,
        "server1.nic1.rx": 50331648,
        "rank4.tx": 25165824,
        "server1.nic0.tx": 50331648,
        "server1.egress": 100663296,
        "cut.1->0": 100663296,
        "server0.ingress": 100663296,
        "server0.nic0.rx": 50331648,
        "rank1.rx": 25165824,
        "server1.nic1.tx": 50331648,
        "server0.nic1.rx": 50331648,
        "rank1.tx": 25165824,
        "rank5.rx": 25165824,
        "rank5.tx": 25165824,
        "rank2.rx": 25165824,
        "rank2.tx": 25165824,
        "rank6.rx": 25165824,
        "rank6.tx": 25165824,
        "rank3.rx": 25165824,
        "rank3.tx": 25165824,
        "rank7.rx": 25165824,
        "rank7.tx": 25165824,
        "rank0.rx": 25165824
      },
      "resource_lower_seconds_exact": "24576/9765625",
      "barrier_lower_seconds_exact": "787057/312500000",
      "barrier_start_seconds_exact": "2361171/312500000",
      "barrier_finish_seconds_exact": "787057/78125000"
    },
    {
      "round": 4,
      "stage": "flat",
      "phase": "reduce_scatter",
      "step": 4,
      "messages": [
        {
          "sender": 0,
          "receiver": 4,
          "operation": "reduce",
          "chunks": [
            4
          ],
          "element_start": 25165824,
          "element_stop": 31457280,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 4,
              "contributors": [
                0,
                2,
                3,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r0:nic0",
              "receiver": "r4:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 25165824,
              "element_stop": 28311552,
              "path": [
                "rank0.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank4.rx"
              ]
            },
            {
              "sender": "r0:nic1",
              "receiver": "r4:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 28311552,
              "element_stop": 31457280,
              "path": [
                "rank0.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank4.rx"
              ]
            }
          ]
        },
        {
          "sender": 4,
          "receiver": 1,
          "operation": "reduce",
          "chunks": [
            5
          ],
          "element_start": 31457280,
          "element_stop": 37748736,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 5,
              "contributors": [
                0,
                3,
                4,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r4:nic0",
              "receiver": "r1:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 31457280,
              "element_stop": 34603008,
              "path": [
                "rank4.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank1.rx"
              ]
            },
            {
              "sender": "r4:nic1",
              "receiver": "r1:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 34603008,
              "element_stop": 37748736,
              "path": [
                "rank4.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank1.rx"
              ]
            }
          ]
        },
        {
          "sender": 1,
          "receiver": 5,
          "operation": "reduce",
          "chunks": [
            6
          ],
          "element_start": 37748736,
          "element_stop": 44040192,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 6,
              "contributors": [
                0,
                1,
                3,
                4,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r1:nic0",
              "receiver": "r5:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 37748736,
              "element_stop": 40894464,
              "path": [
                "rank1.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank5.rx"
              ]
            },
            {
              "sender": "r1:nic1",
              "receiver": "r5:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 40894464,
              "element_stop": 44040192,
              "path": [
                "rank1.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank5.rx"
              ]
            }
          ]
        },
        {
          "sender": 5,
          "receiver": 2,
          "operation": "reduce",
          "chunks": [
            7
          ],
          "element_start": 44040192,
          "element_stop": 50331648,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 7,
              "contributors": [
                0,
                1,
                4,
                5,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r5:nic0",
              "receiver": "r2:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 44040192,
              "element_stop": 47185920,
              "path": [
                "rank5.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank2.rx"
              ]
            },
            {
              "sender": "r5:nic1",
              "receiver": "r2:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 47185920,
              "element_stop": 50331648,
              "path": [
                "rank5.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank2.rx"
              ]
            }
          ]
        },
        {
          "sender": 2,
          "receiver": 6,
          "operation": "reduce",
          "chunks": [
            0
          ],
          "element_start": 0,
          "element_stop": 6291456,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 0,
              "contributors": [
                0,
                1,
                2,
                4,
                5
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r2:nic0",
              "receiver": "r6:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 0,
              "element_stop": 3145728,
              "path": [
                "rank2.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank6.rx"
              ]
            },
            {
              "sender": "r2:nic1",
              "receiver": "r6:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 3145728,
              "element_stop": 6291456,
              "path": [
                "rank2.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank6.rx"
              ]
            }
          ]
        },
        {
          "sender": 6,
          "receiver": 3,
          "operation": "reduce",
          "chunks": [
            1
          ],
          "element_start": 6291456,
          "element_stop": 12582912,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 1,
              "contributors": [
                1,
                2,
                4,
                5,
                6
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r6:nic0",
              "receiver": "r3:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 6291456,
              "element_stop": 9437184,
              "path": [
                "rank6.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank3.rx"
              ]
            },
            {
              "sender": "r6:nic1",
              "receiver": "r3:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 9437184,
              "element_stop": 12582912,
              "path": [
                "rank6.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank3.rx"
              ]
            }
          ]
        },
        {
          "sender": 3,
          "receiver": 7,
          "operation": "reduce",
          "chunks": [
            2
          ],
          "element_start": 12582912,
          "element_stop": 18874368,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 2,
              "contributors": [
                1,
                2,
                3,
                5,
                6
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r3:nic0",
              "receiver": "r7:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 12582912,
              "element_stop": 15728640,
              "path": [
                "rank3.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank7.rx"
              ]
            },
            {
              "sender": "r3:nic1",
              "receiver": "r7:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 15728640,
              "element_stop": 18874368,
              "path": [
                "rank3.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank7.rx"
              ]
            }
          ]
        },
        {
          "sender": 7,
          "receiver": 0,
          "operation": "reduce",
          "chunks": [
            3
          ],
          "element_start": 18874368,
          "element_stop": 25165824,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 3,
              "contributors": [
                2,
                3,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r7:nic0",
              "receiver": "r0:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 18874368,
              "element_stop": 22020096,
              "path": [
                "rank7.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank0.rx"
              ]
            },
            {
              "sender": "r7:nic1",
              "receiver": "r0:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 22020096,
              "element_stop": 25165824,
              "path": [
                "rank7.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank0.rx"
              ]
            }
          ]
        }
      ],
      "edges": [
        {
          "sender": "r0:nic0",
          "receiver": "r4:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 25165824,
          "element_stop": 28311552,
          "path": [
            "rank0.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank4.rx"
          ]
        },
        {
          "sender": "r0:nic1",
          "receiver": "r4:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 28311552,
          "element_stop": 31457280,
          "path": [
            "rank0.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank4.rx"
          ]
        },
        {
          "sender": "r4:nic0",
          "receiver": "r1:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 31457280,
          "element_stop": 34603008,
          "path": [
            "rank4.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank1.rx"
          ]
        },
        {
          "sender": "r4:nic1",
          "receiver": "r1:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 34603008,
          "element_stop": 37748736,
          "path": [
            "rank4.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank1.rx"
          ]
        },
        {
          "sender": "r1:nic0",
          "receiver": "r5:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 37748736,
          "element_stop": 40894464,
          "path": [
            "rank1.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank5.rx"
          ]
        },
        {
          "sender": "r1:nic1",
          "receiver": "r5:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 40894464,
          "element_stop": 44040192,
          "path": [
            "rank1.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank5.rx"
          ]
        },
        {
          "sender": "r5:nic0",
          "receiver": "r2:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 44040192,
          "element_stop": 47185920,
          "path": [
            "rank5.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank2.rx"
          ]
        },
        {
          "sender": "r5:nic1",
          "receiver": "r2:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 47185920,
          "element_stop": 50331648,
          "path": [
            "rank5.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank2.rx"
          ]
        },
        {
          "sender": "r2:nic0",
          "receiver": "r6:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 0,
          "element_stop": 3145728,
          "path": [
            "rank2.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank6.rx"
          ]
        },
        {
          "sender": "r2:nic1",
          "receiver": "r6:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 3145728,
          "element_stop": 6291456,
          "path": [
            "rank2.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank6.rx"
          ]
        },
        {
          "sender": "r6:nic0",
          "receiver": "r3:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 6291456,
          "element_stop": 9437184,
          "path": [
            "rank6.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank3.rx"
          ]
        },
        {
          "sender": "r6:nic1",
          "receiver": "r3:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 9437184,
          "element_stop": 12582912,
          "path": [
            "rank6.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank3.rx"
          ]
        },
        {
          "sender": "r3:nic0",
          "receiver": "r7:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 12582912,
          "element_stop": 15728640,
          "path": [
            "rank3.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank7.rx"
          ]
        },
        {
          "sender": "r3:nic1",
          "receiver": "r7:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 15728640,
          "element_stop": 18874368,
          "path": [
            "rank3.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank7.rx"
          ]
        },
        {
          "sender": "r7:nic0",
          "receiver": "r0:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 18874368,
          "element_stop": 22020096,
          "path": [
            "rank7.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank0.rx"
          ]
        },
        {
          "sender": "r7:nic1",
          "receiver": "r0:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 22020096,
          "element_stop": 25165824,
          "path": [
            "rank7.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank0.rx"
          ]
        }
      ],
      "resource_bytes": {
        "rank0.tx": 25165824,
        "server0.nic0.tx": 50331648,
        "server0.egress": 100663296,
        "cut.0->1": 100663296,
        "shared_cut.bidirectional": 201326592,
        "server1.ingress": 100663296,
        "server1.nic0.rx": 50331648,
        "rank4.rx": 25165824,
        "server0.nic1.tx": 50331648,
        "server1.nic1.rx": 50331648,
        "rank4.tx": 25165824,
        "server1.nic0.tx": 50331648,
        "server1.egress": 100663296,
        "cut.1->0": 100663296,
        "server0.ingress": 100663296,
        "server0.nic0.rx": 50331648,
        "rank1.rx": 25165824,
        "server1.nic1.tx": 50331648,
        "server0.nic1.rx": 50331648,
        "rank1.tx": 25165824,
        "rank5.rx": 25165824,
        "rank5.tx": 25165824,
        "rank2.rx": 25165824,
        "rank2.tx": 25165824,
        "rank6.rx": 25165824,
        "rank6.tx": 25165824,
        "rank3.rx": 25165824,
        "rank3.tx": 25165824,
        "rank7.rx": 25165824,
        "rank7.tx": 25165824,
        "rank0.rx": 25165824
      },
      "resource_lower_seconds_exact": "24576/9765625",
      "barrier_lower_seconds_exact": "787057/312500000",
      "barrier_start_seconds_exact": "787057/78125000",
      "barrier_finish_seconds_exact": "787057/62500000"
    },
    {
      "round": 5,
      "stage": "flat",
      "phase": "reduce_scatter",
      "step": 5,
      "messages": [
        {
          "sender": 0,
          "receiver": 4,
          "operation": "reduce",
          "chunks": [
            3
          ],
          "element_start": 18874368,
          "element_stop": 25165824,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 3,
              "contributors": [
                0,
                2,
                3,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r0:nic0",
              "receiver": "r4:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 18874368,
              "element_stop": 22020096,
              "path": [
                "rank0.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank4.rx"
              ]
            },
            {
              "sender": "r0:nic1",
              "receiver": "r4:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 22020096,
              "element_stop": 25165824,
              "path": [
                "rank0.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank4.rx"
              ]
            }
          ]
        },
        {
          "sender": 4,
          "receiver": 1,
          "operation": "reduce",
          "chunks": [
            4
          ],
          "element_start": 25165824,
          "element_stop": 31457280,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 4,
              "contributors": [
                0,
                2,
                3,
                4,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r4:nic0",
              "receiver": "r1:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 25165824,
              "element_stop": 28311552,
              "path": [
                "rank4.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank1.rx"
              ]
            },
            {
              "sender": "r4:nic1",
              "receiver": "r1:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 28311552,
              "element_stop": 31457280,
              "path": [
                "rank4.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank1.rx"
              ]
            }
          ]
        },
        {
          "sender": 1,
          "receiver": 5,
          "operation": "reduce",
          "chunks": [
            5
          ],
          "element_start": 31457280,
          "element_stop": 37748736,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 5,
              "contributors": [
                0,
                1,
                3,
                4,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r1:nic0",
              "receiver": "r5:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 31457280,
              "element_stop": 34603008,
              "path": [
                "rank1.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank5.rx"
              ]
            },
            {
              "sender": "r1:nic1",
              "receiver": "r5:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 34603008,
              "element_stop": 37748736,
              "path": [
                "rank1.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank5.rx"
              ]
            }
          ]
        },
        {
          "sender": 5,
          "receiver": 2,
          "operation": "reduce",
          "chunks": [
            6
          ],
          "element_start": 37748736,
          "element_stop": 44040192,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 6,
              "contributors": [
                0,
                1,
                3,
                4,
                5,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r5:nic0",
              "receiver": "r2:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 37748736,
              "element_stop": 40894464,
              "path": [
                "rank5.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank2.rx"
              ]
            },
            {
              "sender": "r5:nic1",
              "receiver": "r2:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 40894464,
              "element_stop": 44040192,
              "path": [
                "rank5.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank2.rx"
              ]
            }
          ]
        },
        {
          "sender": 2,
          "receiver": 6,
          "operation": "reduce",
          "chunks": [
            7
          ],
          "element_start": 44040192,
          "element_stop": 50331648,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 7,
              "contributors": [
                0,
                1,
                2,
                4,
                5,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r2:nic0",
              "receiver": "r6:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 44040192,
              "element_stop": 47185920,
              "path": [
                "rank2.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank6.rx"
              ]
            },
            {
              "sender": "r2:nic1",
              "receiver": "r6:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 47185920,
              "element_stop": 50331648,
              "path": [
                "rank2.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank6.rx"
              ]
            }
          ]
        },
        {
          "sender": 6,
          "receiver": 3,
          "operation": "reduce",
          "chunks": [
            0
          ],
          "element_start": 0,
          "element_stop": 6291456,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 0,
              "contributors": [
                0,
                1,
                2,
                4,
                5,
                6
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r6:nic0",
              "receiver": "r3:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 0,
              "element_stop": 3145728,
              "path": [
                "rank6.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank3.rx"
              ]
            },
            {
              "sender": "r6:nic1",
              "receiver": "r3:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 3145728,
              "element_stop": 6291456,
              "path": [
                "rank6.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank3.rx"
              ]
            }
          ]
        },
        {
          "sender": 3,
          "receiver": 7,
          "operation": "reduce",
          "chunks": [
            1
          ],
          "element_start": 6291456,
          "element_stop": 12582912,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 1,
              "contributors": [
                1,
                2,
                3,
                4,
                5,
                6
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r3:nic0",
              "receiver": "r7:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 6291456,
              "element_stop": 9437184,
              "path": [
                "rank3.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank7.rx"
              ]
            },
            {
              "sender": "r3:nic1",
              "receiver": "r7:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 9437184,
              "element_stop": 12582912,
              "path": [
                "rank3.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank7.rx"
              ]
            }
          ]
        },
        {
          "sender": 7,
          "receiver": 0,
          "operation": "reduce",
          "chunks": [
            2
          ],
          "element_start": 12582912,
          "element_stop": 18874368,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 2,
              "contributors": [
                1,
                2,
                3,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r7:nic0",
              "receiver": "r0:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 12582912,
              "element_stop": 15728640,
              "path": [
                "rank7.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank0.rx"
              ]
            },
            {
              "sender": "r7:nic1",
              "receiver": "r0:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 15728640,
              "element_stop": 18874368,
              "path": [
                "rank7.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank0.rx"
              ]
            }
          ]
        }
      ],
      "edges": [
        {
          "sender": "r0:nic0",
          "receiver": "r4:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 18874368,
          "element_stop": 22020096,
          "path": [
            "rank0.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank4.rx"
          ]
        },
        {
          "sender": "r0:nic1",
          "receiver": "r4:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 22020096,
          "element_stop": 25165824,
          "path": [
            "rank0.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank4.rx"
          ]
        },
        {
          "sender": "r4:nic0",
          "receiver": "r1:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 25165824,
          "element_stop": 28311552,
          "path": [
            "rank4.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank1.rx"
          ]
        },
        {
          "sender": "r4:nic1",
          "receiver": "r1:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 28311552,
          "element_stop": 31457280,
          "path": [
            "rank4.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank1.rx"
          ]
        },
        {
          "sender": "r1:nic0",
          "receiver": "r5:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 31457280,
          "element_stop": 34603008,
          "path": [
            "rank1.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank5.rx"
          ]
        },
        {
          "sender": "r1:nic1",
          "receiver": "r5:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 34603008,
          "element_stop": 37748736,
          "path": [
            "rank1.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank5.rx"
          ]
        },
        {
          "sender": "r5:nic0",
          "receiver": "r2:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 37748736,
          "element_stop": 40894464,
          "path": [
            "rank5.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank2.rx"
          ]
        },
        {
          "sender": "r5:nic1",
          "receiver": "r2:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 40894464,
          "element_stop": 44040192,
          "path": [
            "rank5.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank2.rx"
          ]
        },
        {
          "sender": "r2:nic0",
          "receiver": "r6:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 44040192,
          "element_stop": 47185920,
          "path": [
            "rank2.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank6.rx"
          ]
        },
        {
          "sender": "r2:nic1",
          "receiver": "r6:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 47185920,
          "element_stop": 50331648,
          "path": [
            "rank2.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank6.rx"
          ]
        },
        {
          "sender": "r6:nic0",
          "receiver": "r3:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 0,
          "element_stop": 3145728,
          "path": [
            "rank6.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank3.rx"
          ]
        },
        {
          "sender": "r6:nic1",
          "receiver": "r3:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 3145728,
          "element_stop": 6291456,
          "path": [
            "rank6.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank3.rx"
          ]
        },
        {
          "sender": "r3:nic0",
          "receiver": "r7:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 6291456,
          "element_stop": 9437184,
          "path": [
            "rank3.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank7.rx"
          ]
        },
        {
          "sender": "r3:nic1",
          "receiver": "r7:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 9437184,
          "element_stop": 12582912,
          "path": [
            "rank3.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank7.rx"
          ]
        },
        {
          "sender": "r7:nic0",
          "receiver": "r0:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 12582912,
          "element_stop": 15728640,
          "path": [
            "rank7.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank0.rx"
          ]
        },
        {
          "sender": "r7:nic1",
          "receiver": "r0:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 15728640,
          "element_stop": 18874368,
          "path": [
            "rank7.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank0.rx"
          ]
        }
      ],
      "resource_bytes": {
        "rank0.tx": 25165824,
        "server0.nic0.tx": 50331648,
        "server0.egress": 100663296,
        "cut.0->1": 100663296,
        "shared_cut.bidirectional": 201326592,
        "server1.ingress": 100663296,
        "server1.nic0.rx": 50331648,
        "rank4.rx": 25165824,
        "server0.nic1.tx": 50331648,
        "server1.nic1.rx": 50331648,
        "rank4.tx": 25165824,
        "server1.nic0.tx": 50331648,
        "server1.egress": 100663296,
        "cut.1->0": 100663296,
        "server0.ingress": 100663296,
        "server0.nic0.rx": 50331648,
        "rank1.rx": 25165824,
        "server1.nic1.tx": 50331648,
        "server0.nic1.rx": 50331648,
        "rank1.tx": 25165824,
        "rank5.rx": 25165824,
        "rank5.tx": 25165824,
        "rank2.rx": 25165824,
        "rank2.tx": 25165824,
        "rank6.rx": 25165824,
        "rank6.tx": 25165824,
        "rank3.rx": 25165824,
        "rank3.tx": 25165824,
        "rank7.rx": 25165824,
        "rank7.tx": 25165824,
        "rank0.rx": 25165824
      },
      "resource_lower_seconds_exact": "24576/9765625",
      "barrier_lower_seconds_exact": "787057/312500000",
      "barrier_start_seconds_exact": "787057/62500000",
      "barrier_finish_seconds_exact": "2361171/156250000"
    },
    {
      "round": 6,
      "stage": "flat",
      "phase": "reduce_scatter",
      "step": 6,
      "messages": [
        {
          "sender": 0,
          "receiver": 4,
          "operation": "reduce",
          "chunks": [
            2
          ],
          "element_start": 12582912,
          "element_stop": 18874368,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 2,
              "contributors": [
                0,
                1,
                2,
                3,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r0:nic0",
              "receiver": "r4:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 12582912,
              "element_stop": 15728640,
              "path": [
                "rank0.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank4.rx"
              ]
            },
            {
              "sender": "r0:nic1",
              "receiver": "r4:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 15728640,
              "element_stop": 18874368,
              "path": [
                "rank0.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank4.rx"
              ]
            }
          ]
        },
        {
          "sender": 4,
          "receiver": 1,
          "operation": "reduce",
          "chunks": [
            3
          ],
          "element_start": 18874368,
          "element_stop": 25165824,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 3,
              "contributors": [
                0,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r4:nic0",
              "receiver": "r1:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 18874368,
              "element_stop": 22020096,
              "path": [
                "rank4.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank1.rx"
              ]
            },
            {
              "sender": "r4:nic1",
              "receiver": "r1:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 22020096,
              "element_stop": 25165824,
              "path": [
                "rank4.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank1.rx"
              ]
            }
          ]
        },
        {
          "sender": 1,
          "receiver": 5,
          "operation": "reduce",
          "chunks": [
            4
          ],
          "element_start": 25165824,
          "element_stop": 31457280,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 4,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r1:nic0",
              "receiver": "r5:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 25165824,
              "element_stop": 28311552,
              "path": [
                "rank1.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank5.rx"
              ]
            },
            {
              "sender": "r1:nic1",
              "receiver": "r5:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 28311552,
              "element_stop": 31457280,
              "path": [
                "rank1.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank5.rx"
              ]
            }
          ]
        },
        {
          "sender": 5,
          "receiver": 2,
          "operation": "reduce",
          "chunks": [
            5
          ],
          "element_start": 31457280,
          "element_stop": 37748736,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 5,
              "contributors": [
                0,
                1,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r5:nic0",
              "receiver": "r2:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 31457280,
              "element_stop": 34603008,
              "path": [
                "rank5.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank2.rx"
              ]
            },
            {
              "sender": "r5:nic1",
              "receiver": "r2:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 34603008,
              "element_stop": 37748736,
              "path": [
                "rank5.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank2.rx"
              ]
            }
          ]
        },
        {
          "sender": 2,
          "receiver": 6,
          "operation": "reduce",
          "chunks": [
            6
          ],
          "element_start": 37748736,
          "element_stop": 44040192,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 6,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r2:nic0",
              "receiver": "r6:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 37748736,
              "element_stop": 40894464,
              "path": [
                "rank2.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank6.rx"
              ]
            },
            {
              "sender": "r2:nic1",
              "receiver": "r6:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 40894464,
              "element_stop": 44040192,
              "path": [
                "rank2.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank6.rx"
              ]
            }
          ]
        },
        {
          "sender": 6,
          "receiver": 3,
          "operation": "reduce",
          "chunks": [
            7
          ],
          "element_start": 44040192,
          "element_stop": 50331648,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 7,
              "contributors": [
                0,
                1,
                2,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r6:nic0",
              "receiver": "r3:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 44040192,
              "element_stop": 47185920,
              "path": [
                "rank6.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank3.rx"
              ]
            },
            {
              "sender": "r6:nic1",
              "receiver": "r3:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 47185920,
              "element_stop": 50331648,
              "path": [
                "rank6.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank3.rx"
              ]
            }
          ]
        },
        {
          "sender": 3,
          "receiver": 7,
          "operation": "reduce",
          "chunks": [
            0
          ],
          "element_start": 0,
          "element_stop": 6291456,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 0,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r3:nic0",
              "receiver": "r7:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 0,
              "element_stop": 3145728,
              "path": [
                "rank3.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank7.rx"
              ]
            },
            {
              "sender": "r3:nic1",
              "receiver": "r7:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 3145728,
              "element_stop": 6291456,
              "path": [
                "rank3.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank7.rx"
              ]
            }
          ]
        },
        {
          "sender": 7,
          "receiver": 0,
          "operation": "reduce",
          "chunks": [
            1
          ],
          "element_start": 6291456,
          "element_stop": 12582912,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 1,
              "contributors": [
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r7:nic0",
              "receiver": "r0:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 6291456,
              "element_stop": 9437184,
              "path": [
                "rank7.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank0.rx"
              ]
            },
            {
              "sender": "r7:nic1",
              "receiver": "r0:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 9437184,
              "element_stop": 12582912,
              "path": [
                "rank7.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank0.rx"
              ]
            }
          ]
        }
      ],
      "edges": [
        {
          "sender": "r0:nic0",
          "receiver": "r4:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 12582912,
          "element_stop": 15728640,
          "path": [
            "rank0.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank4.rx"
          ]
        },
        {
          "sender": "r0:nic1",
          "receiver": "r4:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 15728640,
          "element_stop": 18874368,
          "path": [
            "rank0.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank4.rx"
          ]
        },
        {
          "sender": "r4:nic0",
          "receiver": "r1:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 18874368,
          "element_stop": 22020096,
          "path": [
            "rank4.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank1.rx"
          ]
        },
        {
          "sender": "r4:nic1",
          "receiver": "r1:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 22020096,
          "element_stop": 25165824,
          "path": [
            "rank4.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank1.rx"
          ]
        },
        {
          "sender": "r1:nic0",
          "receiver": "r5:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 25165824,
          "element_stop": 28311552,
          "path": [
            "rank1.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank5.rx"
          ]
        },
        {
          "sender": "r1:nic1",
          "receiver": "r5:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 28311552,
          "element_stop": 31457280,
          "path": [
            "rank1.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank5.rx"
          ]
        },
        {
          "sender": "r5:nic0",
          "receiver": "r2:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 31457280,
          "element_stop": 34603008,
          "path": [
            "rank5.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank2.rx"
          ]
        },
        {
          "sender": "r5:nic1",
          "receiver": "r2:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 34603008,
          "element_stop": 37748736,
          "path": [
            "rank5.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank2.rx"
          ]
        },
        {
          "sender": "r2:nic0",
          "receiver": "r6:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 37748736,
          "element_stop": 40894464,
          "path": [
            "rank2.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank6.rx"
          ]
        },
        {
          "sender": "r2:nic1",
          "receiver": "r6:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 40894464,
          "element_stop": 44040192,
          "path": [
            "rank2.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank6.rx"
          ]
        },
        {
          "sender": "r6:nic0",
          "receiver": "r3:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 44040192,
          "element_stop": 47185920,
          "path": [
            "rank6.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank3.rx"
          ]
        },
        {
          "sender": "r6:nic1",
          "receiver": "r3:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 47185920,
          "element_stop": 50331648,
          "path": [
            "rank6.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank3.rx"
          ]
        },
        {
          "sender": "r3:nic0",
          "receiver": "r7:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 0,
          "element_stop": 3145728,
          "path": [
            "rank3.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank7.rx"
          ]
        },
        {
          "sender": "r3:nic1",
          "receiver": "r7:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 3145728,
          "element_stop": 6291456,
          "path": [
            "rank3.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank7.rx"
          ]
        },
        {
          "sender": "r7:nic0",
          "receiver": "r0:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 6291456,
          "element_stop": 9437184,
          "path": [
            "rank7.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank0.rx"
          ]
        },
        {
          "sender": "r7:nic1",
          "receiver": "r0:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 9437184,
          "element_stop": 12582912,
          "path": [
            "rank7.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank0.rx"
          ]
        }
      ],
      "resource_bytes": {
        "rank0.tx": 25165824,
        "server0.nic0.tx": 50331648,
        "server0.egress": 100663296,
        "cut.0->1": 100663296,
        "shared_cut.bidirectional": 201326592,
        "server1.ingress": 100663296,
        "server1.nic0.rx": 50331648,
        "rank4.rx": 25165824,
        "server0.nic1.tx": 50331648,
        "server1.nic1.rx": 50331648,
        "rank4.tx": 25165824,
        "server1.nic0.tx": 50331648,
        "server1.egress": 100663296,
        "cut.1->0": 100663296,
        "server0.ingress": 100663296,
        "server0.nic0.rx": 50331648,
        "rank1.rx": 25165824,
        "server1.nic1.tx": 50331648,
        "server0.nic1.rx": 50331648,
        "rank1.tx": 25165824,
        "rank5.rx": 25165824,
        "rank5.tx": 25165824,
        "rank2.rx": 25165824,
        "rank2.tx": 25165824,
        "rank6.rx": 25165824,
        "rank6.tx": 25165824,
        "rank3.rx": 25165824,
        "rank3.tx": 25165824,
        "rank7.rx": 25165824,
        "rank7.tx": 25165824,
        "rank0.rx": 25165824
      },
      "resource_lower_seconds_exact": "24576/9765625",
      "barrier_lower_seconds_exact": "787057/312500000",
      "barrier_start_seconds_exact": "2361171/156250000",
      "barrier_finish_seconds_exact": "5509399/312500000"
    },
    {
      "round": 7,
      "stage": "flat",
      "phase": "all_gather",
      "step": 0,
      "messages": [
        {
          "sender": 0,
          "receiver": 4,
          "operation": "copy",
          "chunks": [
            1
          ],
          "element_start": 6291456,
          "element_stop": 12582912,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 1,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r0:nic0",
              "receiver": "r4:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 6291456,
              "element_stop": 9437184,
              "path": [
                "rank0.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank4.rx"
              ]
            },
            {
              "sender": "r0:nic1",
              "receiver": "r4:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 9437184,
              "element_stop": 12582912,
              "path": [
                "rank0.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank4.rx"
              ]
            }
          ]
        },
        {
          "sender": 4,
          "receiver": 1,
          "operation": "copy",
          "chunks": [
            2
          ],
          "element_start": 12582912,
          "element_stop": 18874368,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 2,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r4:nic0",
              "receiver": "r1:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 12582912,
              "element_stop": 15728640,
              "path": [
                "rank4.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank1.rx"
              ]
            },
            {
              "sender": "r4:nic1",
              "receiver": "r1:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 15728640,
              "element_stop": 18874368,
              "path": [
                "rank4.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank1.rx"
              ]
            }
          ]
        },
        {
          "sender": 1,
          "receiver": 5,
          "operation": "copy",
          "chunks": [
            3
          ],
          "element_start": 18874368,
          "element_stop": 25165824,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 3,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r1:nic0",
              "receiver": "r5:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 18874368,
              "element_stop": 22020096,
              "path": [
                "rank1.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank5.rx"
              ]
            },
            {
              "sender": "r1:nic1",
              "receiver": "r5:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 22020096,
              "element_stop": 25165824,
              "path": [
                "rank1.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank5.rx"
              ]
            }
          ]
        },
        {
          "sender": 5,
          "receiver": 2,
          "operation": "copy",
          "chunks": [
            4
          ],
          "element_start": 25165824,
          "element_stop": 31457280,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 4,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r5:nic0",
              "receiver": "r2:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 25165824,
              "element_stop": 28311552,
              "path": [
                "rank5.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank2.rx"
              ]
            },
            {
              "sender": "r5:nic1",
              "receiver": "r2:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 28311552,
              "element_stop": 31457280,
              "path": [
                "rank5.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank2.rx"
              ]
            }
          ]
        },
        {
          "sender": 2,
          "receiver": 6,
          "operation": "copy",
          "chunks": [
            5
          ],
          "element_start": 31457280,
          "element_stop": 37748736,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 5,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r2:nic0",
              "receiver": "r6:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 31457280,
              "element_stop": 34603008,
              "path": [
                "rank2.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank6.rx"
              ]
            },
            {
              "sender": "r2:nic1",
              "receiver": "r6:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 34603008,
              "element_stop": 37748736,
              "path": [
                "rank2.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank6.rx"
              ]
            }
          ]
        },
        {
          "sender": 6,
          "receiver": 3,
          "operation": "copy",
          "chunks": [
            6
          ],
          "element_start": 37748736,
          "element_stop": 44040192,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 6,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r6:nic0",
              "receiver": "r3:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 37748736,
              "element_stop": 40894464,
              "path": [
                "rank6.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank3.rx"
              ]
            },
            {
              "sender": "r6:nic1",
              "receiver": "r3:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 40894464,
              "element_stop": 44040192,
              "path": [
                "rank6.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank3.rx"
              ]
            }
          ]
        },
        {
          "sender": 3,
          "receiver": 7,
          "operation": "copy",
          "chunks": [
            7
          ],
          "element_start": 44040192,
          "element_stop": 50331648,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 7,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r3:nic0",
              "receiver": "r7:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 44040192,
              "element_stop": 47185920,
              "path": [
                "rank3.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank7.rx"
              ]
            },
            {
              "sender": "r3:nic1",
              "receiver": "r7:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 47185920,
              "element_stop": 50331648,
              "path": [
                "rank3.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank7.rx"
              ]
            }
          ]
        },
        {
          "sender": 7,
          "receiver": 0,
          "operation": "copy",
          "chunks": [
            0
          ],
          "element_start": 0,
          "element_stop": 6291456,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 0,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r7:nic0",
              "receiver": "r0:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 0,
              "element_stop": 3145728,
              "path": [
                "rank7.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank0.rx"
              ]
            },
            {
              "sender": "r7:nic1",
              "receiver": "r0:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 3145728,
              "element_stop": 6291456,
              "path": [
                "rank7.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank0.rx"
              ]
            }
          ]
        }
      ],
      "edges": [
        {
          "sender": "r0:nic0",
          "receiver": "r4:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 6291456,
          "element_stop": 9437184,
          "path": [
            "rank0.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank4.rx"
          ]
        },
        {
          "sender": "r0:nic1",
          "receiver": "r4:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 9437184,
          "element_stop": 12582912,
          "path": [
            "rank0.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank4.rx"
          ]
        },
        {
          "sender": "r4:nic0",
          "receiver": "r1:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 12582912,
          "element_stop": 15728640,
          "path": [
            "rank4.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank1.rx"
          ]
        },
        {
          "sender": "r4:nic1",
          "receiver": "r1:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 15728640,
          "element_stop": 18874368,
          "path": [
            "rank4.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank1.rx"
          ]
        },
        {
          "sender": "r1:nic0",
          "receiver": "r5:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 18874368,
          "element_stop": 22020096,
          "path": [
            "rank1.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank5.rx"
          ]
        },
        {
          "sender": "r1:nic1",
          "receiver": "r5:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 22020096,
          "element_stop": 25165824,
          "path": [
            "rank1.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank5.rx"
          ]
        },
        {
          "sender": "r5:nic0",
          "receiver": "r2:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 25165824,
          "element_stop": 28311552,
          "path": [
            "rank5.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank2.rx"
          ]
        },
        {
          "sender": "r5:nic1",
          "receiver": "r2:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 28311552,
          "element_stop": 31457280,
          "path": [
            "rank5.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank2.rx"
          ]
        },
        {
          "sender": "r2:nic0",
          "receiver": "r6:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 31457280,
          "element_stop": 34603008,
          "path": [
            "rank2.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank6.rx"
          ]
        },
        {
          "sender": "r2:nic1",
          "receiver": "r6:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 34603008,
          "element_stop": 37748736,
          "path": [
            "rank2.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank6.rx"
          ]
        },
        {
          "sender": "r6:nic0",
          "receiver": "r3:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 37748736,
          "element_stop": 40894464,
          "path": [
            "rank6.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank3.rx"
          ]
        },
        {
          "sender": "r6:nic1",
          "receiver": "r3:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 40894464,
          "element_stop": 44040192,
          "path": [
            "rank6.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank3.rx"
          ]
        },
        {
          "sender": "r3:nic0",
          "receiver": "r7:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 44040192,
          "element_stop": 47185920,
          "path": [
            "rank3.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank7.rx"
          ]
        },
        {
          "sender": "r3:nic1",
          "receiver": "r7:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 47185920,
          "element_stop": 50331648,
          "path": [
            "rank3.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank7.rx"
          ]
        },
        {
          "sender": "r7:nic0",
          "receiver": "r0:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 0,
          "element_stop": 3145728,
          "path": [
            "rank7.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank0.rx"
          ]
        },
        {
          "sender": "r7:nic1",
          "receiver": "r0:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 3145728,
          "element_stop": 6291456,
          "path": [
            "rank7.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank0.rx"
          ]
        }
      ],
      "resource_bytes": {
        "rank0.tx": 25165824,
        "server0.nic0.tx": 50331648,
        "server0.egress": 100663296,
        "cut.0->1": 100663296,
        "shared_cut.bidirectional": 201326592,
        "server1.ingress": 100663296,
        "server1.nic0.rx": 50331648,
        "rank4.rx": 25165824,
        "server0.nic1.tx": 50331648,
        "server1.nic1.rx": 50331648,
        "rank4.tx": 25165824,
        "server1.nic0.tx": 50331648,
        "server1.egress": 100663296,
        "cut.1->0": 100663296,
        "server0.ingress": 100663296,
        "server0.nic0.rx": 50331648,
        "rank1.rx": 25165824,
        "server1.nic1.tx": 50331648,
        "server0.nic1.rx": 50331648,
        "rank1.tx": 25165824,
        "rank5.rx": 25165824,
        "rank5.tx": 25165824,
        "rank2.rx": 25165824,
        "rank2.tx": 25165824,
        "rank6.rx": 25165824,
        "rank6.tx": 25165824,
        "rank3.rx": 25165824,
        "rank3.tx": 25165824,
        "rank7.rx": 25165824,
        "rank7.tx": 25165824,
        "rank0.rx": 25165824
      },
      "resource_lower_seconds_exact": "24576/9765625",
      "barrier_lower_seconds_exact": "787057/312500000",
      "barrier_start_seconds_exact": "5509399/312500000",
      "barrier_finish_seconds_exact": "787057/39062500"
    },
    {
      "round": 8,
      "stage": "flat",
      "phase": "all_gather",
      "step": 1,
      "messages": [
        {
          "sender": 0,
          "receiver": 4,
          "operation": "copy",
          "chunks": [
            0
          ],
          "element_start": 0,
          "element_stop": 6291456,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 0,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r0:nic0",
              "receiver": "r4:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 0,
              "element_stop": 3145728,
              "path": [
                "rank0.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank4.rx"
              ]
            },
            {
              "sender": "r0:nic1",
              "receiver": "r4:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 3145728,
              "element_stop": 6291456,
              "path": [
                "rank0.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank4.rx"
              ]
            }
          ]
        },
        {
          "sender": 4,
          "receiver": 1,
          "operation": "copy",
          "chunks": [
            1
          ],
          "element_start": 6291456,
          "element_stop": 12582912,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 1,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r4:nic0",
              "receiver": "r1:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 6291456,
              "element_stop": 9437184,
              "path": [
                "rank4.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank1.rx"
              ]
            },
            {
              "sender": "r4:nic1",
              "receiver": "r1:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 9437184,
              "element_stop": 12582912,
              "path": [
                "rank4.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank1.rx"
              ]
            }
          ]
        },
        {
          "sender": 1,
          "receiver": 5,
          "operation": "copy",
          "chunks": [
            2
          ],
          "element_start": 12582912,
          "element_stop": 18874368,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 2,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r1:nic0",
              "receiver": "r5:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 12582912,
              "element_stop": 15728640,
              "path": [
                "rank1.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank5.rx"
              ]
            },
            {
              "sender": "r1:nic1",
              "receiver": "r5:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 15728640,
              "element_stop": 18874368,
              "path": [
                "rank1.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank5.rx"
              ]
            }
          ]
        },
        {
          "sender": 5,
          "receiver": 2,
          "operation": "copy",
          "chunks": [
            3
          ],
          "element_start": 18874368,
          "element_stop": 25165824,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 3,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r5:nic0",
              "receiver": "r2:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 18874368,
              "element_stop": 22020096,
              "path": [
                "rank5.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank2.rx"
              ]
            },
            {
              "sender": "r5:nic1",
              "receiver": "r2:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 22020096,
              "element_stop": 25165824,
              "path": [
                "rank5.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank2.rx"
              ]
            }
          ]
        },
        {
          "sender": 2,
          "receiver": 6,
          "operation": "copy",
          "chunks": [
            4
          ],
          "element_start": 25165824,
          "element_stop": 31457280,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 4,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r2:nic0",
              "receiver": "r6:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 25165824,
              "element_stop": 28311552,
              "path": [
                "rank2.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank6.rx"
              ]
            },
            {
              "sender": "r2:nic1",
              "receiver": "r6:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 28311552,
              "element_stop": 31457280,
              "path": [
                "rank2.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank6.rx"
              ]
            }
          ]
        },
        {
          "sender": 6,
          "receiver": 3,
          "operation": "copy",
          "chunks": [
            5
          ],
          "element_start": 31457280,
          "element_stop": 37748736,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 5,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r6:nic0",
              "receiver": "r3:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 31457280,
              "element_stop": 34603008,
              "path": [
                "rank6.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank3.rx"
              ]
            },
            {
              "sender": "r6:nic1",
              "receiver": "r3:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 34603008,
              "element_stop": 37748736,
              "path": [
                "rank6.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank3.rx"
              ]
            }
          ]
        },
        {
          "sender": 3,
          "receiver": 7,
          "operation": "copy",
          "chunks": [
            6
          ],
          "element_start": 37748736,
          "element_stop": 44040192,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 6,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r3:nic0",
              "receiver": "r7:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 37748736,
              "element_stop": 40894464,
              "path": [
                "rank3.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank7.rx"
              ]
            },
            {
              "sender": "r3:nic1",
              "receiver": "r7:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 40894464,
              "element_stop": 44040192,
              "path": [
                "rank3.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank7.rx"
              ]
            }
          ]
        },
        {
          "sender": 7,
          "receiver": 0,
          "operation": "copy",
          "chunks": [
            7
          ],
          "element_start": 44040192,
          "element_stop": 50331648,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 7,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r7:nic0",
              "receiver": "r0:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 44040192,
              "element_stop": 47185920,
              "path": [
                "rank7.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank0.rx"
              ]
            },
            {
              "sender": "r7:nic1",
              "receiver": "r0:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 47185920,
              "element_stop": 50331648,
              "path": [
                "rank7.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank0.rx"
              ]
            }
          ]
        }
      ],
      "edges": [
        {
          "sender": "r0:nic0",
          "receiver": "r4:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 0,
          "element_stop": 3145728,
          "path": [
            "rank0.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank4.rx"
          ]
        },
        {
          "sender": "r0:nic1",
          "receiver": "r4:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 3145728,
          "element_stop": 6291456,
          "path": [
            "rank0.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank4.rx"
          ]
        },
        {
          "sender": "r4:nic0",
          "receiver": "r1:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 6291456,
          "element_stop": 9437184,
          "path": [
            "rank4.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank1.rx"
          ]
        },
        {
          "sender": "r4:nic1",
          "receiver": "r1:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 9437184,
          "element_stop": 12582912,
          "path": [
            "rank4.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank1.rx"
          ]
        },
        {
          "sender": "r1:nic0",
          "receiver": "r5:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 12582912,
          "element_stop": 15728640,
          "path": [
            "rank1.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank5.rx"
          ]
        },
        {
          "sender": "r1:nic1",
          "receiver": "r5:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 15728640,
          "element_stop": 18874368,
          "path": [
            "rank1.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank5.rx"
          ]
        },
        {
          "sender": "r5:nic0",
          "receiver": "r2:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 18874368,
          "element_stop": 22020096,
          "path": [
            "rank5.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank2.rx"
          ]
        },
        {
          "sender": "r5:nic1",
          "receiver": "r2:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 22020096,
          "element_stop": 25165824,
          "path": [
            "rank5.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank2.rx"
          ]
        },
        {
          "sender": "r2:nic0",
          "receiver": "r6:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 25165824,
          "element_stop": 28311552,
          "path": [
            "rank2.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank6.rx"
          ]
        },
        {
          "sender": "r2:nic1",
          "receiver": "r6:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 28311552,
          "element_stop": 31457280,
          "path": [
            "rank2.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank6.rx"
          ]
        },
        {
          "sender": "r6:nic0",
          "receiver": "r3:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 31457280,
          "element_stop": 34603008,
          "path": [
            "rank6.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank3.rx"
          ]
        },
        {
          "sender": "r6:nic1",
          "receiver": "r3:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 34603008,
          "element_stop": 37748736,
          "path": [
            "rank6.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank3.rx"
          ]
        },
        {
          "sender": "r3:nic0",
          "receiver": "r7:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 37748736,
          "element_stop": 40894464,
          "path": [
            "rank3.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank7.rx"
          ]
        },
        {
          "sender": "r3:nic1",
          "receiver": "r7:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 40894464,
          "element_stop": 44040192,
          "path": [
            "rank3.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank7.rx"
          ]
        },
        {
          "sender": "r7:nic0",
          "receiver": "r0:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 44040192,
          "element_stop": 47185920,
          "path": [
            "rank7.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank0.rx"
          ]
        },
        {
          "sender": "r7:nic1",
          "receiver": "r0:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 47185920,
          "element_stop": 50331648,
          "path": [
            "rank7.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank0.rx"
          ]
        }
      ],
      "resource_bytes": {
        "rank0.tx": 25165824,
        "server0.nic0.tx": 50331648,
        "server0.egress": 100663296,
        "cut.0->1": 100663296,
        "shared_cut.bidirectional": 201326592,
        "server1.ingress": 100663296,
        "server1.nic0.rx": 50331648,
        "rank4.rx": 25165824,
        "server0.nic1.tx": 50331648,
        "server1.nic1.rx": 50331648,
        "rank4.tx": 25165824,
        "server1.nic0.tx": 50331648,
        "server1.egress": 100663296,
        "cut.1->0": 100663296,
        "server0.ingress": 100663296,
        "server0.nic0.rx": 50331648,
        "rank1.rx": 25165824,
        "server1.nic1.tx": 50331648,
        "server0.nic1.rx": 50331648,
        "rank1.tx": 25165824,
        "rank5.rx": 25165824,
        "rank5.tx": 25165824,
        "rank2.rx": 25165824,
        "rank2.tx": 25165824,
        "rank6.rx": 25165824,
        "rank6.tx": 25165824,
        "rank3.rx": 25165824,
        "rank3.tx": 25165824,
        "rank7.rx": 25165824,
        "rank7.tx": 25165824,
        "rank0.rx": 25165824
      },
      "resource_lower_seconds_exact": "24576/9765625",
      "barrier_lower_seconds_exact": "787057/312500000",
      "barrier_start_seconds_exact": "787057/39062500",
      "barrier_finish_seconds_exact": "7083513/312500000"
    },
    {
      "round": 9,
      "stage": "flat",
      "phase": "all_gather",
      "step": 2,
      "messages": [
        {
          "sender": 0,
          "receiver": 4,
          "operation": "copy",
          "chunks": [
            7
          ],
          "element_start": 44040192,
          "element_stop": 50331648,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 7,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r0:nic0",
              "receiver": "r4:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 44040192,
              "element_stop": 47185920,
              "path": [
                "rank0.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank4.rx"
              ]
            },
            {
              "sender": "r0:nic1",
              "receiver": "r4:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 47185920,
              "element_stop": 50331648,
              "path": [
                "rank0.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank4.rx"
              ]
            }
          ]
        },
        {
          "sender": 4,
          "receiver": 1,
          "operation": "copy",
          "chunks": [
            0
          ],
          "element_start": 0,
          "element_stop": 6291456,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 0,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r4:nic0",
              "receiver": "r1:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 0,
              "element_stop": 3145728,
              "path": [
                "rank4.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank1.rx"
              ]
            },
            {
              "sender": "r4:nic1",
              "receiver": "r1:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 3145728,
              "element_stop": 6291456,
              "path": [
                "rank4.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank1.rx"
              ]
            }
          ]
        },
        {
          "sender": 1,
          "receiver": 5,
          "operation": "copy",
          "chunks": [
            1
          ],
          "element_start": 6291456,
          "element_stop": 12582912,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 1,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r1:nic0",
              "receiver": "r5:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 6291456,
              "element_stop": 9437184,
              "path": [
                "rank1.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank5.rx"
              ]
            },
            {
              "sender": "r1:nic1",
              "receiver": "r5:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 9437184,
              "element_stop": 12582912,
              "path": [
                "rank1.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank5.rx"
              ]
            }
          ]
        },
        {
          "sender": 5,
          "receiver": 2,
          "operation": "copy",
          "chunks": [
            2
          ],
          "element_start": 12582912,
          "element_stop": 18874368,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 2,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r5:nic0",
              "receiver": "r2:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 12582912,
              "element_stop": 15728640,
              "path": [
                "rank5.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank2.rx"
              ]
            },
            {
              "sender": "r5:nic1",
              "receiver": "r2:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 15728640,
              "element_stop": 18874368,
              "path": [
                "rank5.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank2.rx"
              ]
            }
          ]
        },
        {
          "sender": 2,
          "receiver": 6,
          "operation": "copy",
          "chunks": [
            3
          ],
          "element_start": 18874368,
          "element_stop": 25165824,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 3,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r2:nic0",
              "receiver": "r6:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 18874368,
              "element_stop": 22020096,
              "path": [
                "rank2.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank6.rx"
              ]
            },
            {
              "sender": "r2:nic1",
              "receiver": "r6:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 22020096,
              "element_stop": 25165824,
              "path": [
                "rank2.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank6.rx"
              ]
            }
          ]
        },
        {
          "sender": 6,
          "receiver": 3,
          "operation": "copy",
          "chunks": [
            4
          ],
          "element_start": 25165824,
          "element_stop": 31457280,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 4,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r6:nic0",
              "receiver": "r3:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 25165824,
              "element_stop": 28311552,
              "path": [
                "rank6.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank3.rx"
              ]
            },
            {
              "sender": "r6:nic1",
              "receiver": "r3:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 28311552,
              "element_stop": 31457280,
              "path": [
                "rank6.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank3.rx"
              ]
            }
          ]
        },
        {
          "sender": 3,
          "receiver": 7,
          "operation": "copy",
          "chunks": [
            5
          ],
          "element_start": 31457280,
          "element_stop": 37748736,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 5,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r3:nic0",
              "receiver": "r7:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 31457280,
              "element_stop": 34603008,
              "path": [
                "rank3.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank7.rx"
              ]
            },
            {
              "sender": "r3:nic1",
              "receiver": "r7:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 34603008,
              "element_stop": 37748736,
              "path": [
                "rank3.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank7.rx"
              ]
            }
          ]
        },
        {
          "sender": 7,
          "receiver": 0,
          "operation": "copy",
          "chunks": [
            6
          ],
          "element_start": 37748736,
          "element_stop": 44040192,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 6,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r7:nic0",
              "receiver": "r0:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 37748736,
              "element_stop": 40894464,
              "path": [
                "rank7.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank0.rx"
              ]
            },
            {
              "sender": "r7:nic1",
              "receiver": "r0:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 40894464,
              "element_stop": 44040192,
              "path": [
                "rank7.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank0.rx"
              ]
            }
          ]
        }
      ],
      "edges": [
        {
          "sender": "r0:nic0",
          "receiver": "r4:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 44040192,
          "element_stop": 47185920,
          "path": [
            "rank0.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank4.rx"
          ]
        },
        {
          "sender": "r0:nic1",
          "receiver": "r4:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 47185920,
          "element_stop": 50331648,
          "path": [
            "rank0.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank4.rx"
          ]
        },
        {
          "sender": "r4:nic0",
          "receiver": "r1:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 0,
          "element_stop": 3145728,
          "path": [
            "rank4.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank1.rx"
          ]
        },
        {
          "sender": "r4:nic1",
          "receiver": "r1:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 3145728,
          "element_stop": 6291456,
          "path": [
            "rank4.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank1.rx"
          ]
        },
        {
          "sender": "r1:nic0",
          "receiver": "r5:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 6291456,
          "element_stop": 9437184,
          "path": [
            "rank1.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank5.rx"
          ]
        },
        {
          "sender": "r1:nic1",
          "receiver": "r5:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 9437184,
          "element_stop": 12582912,
          "path": [
            "rank1.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank5.rx"
          ]
        },
        {
          "sender": "r5:nic0",
          "receiver": "r2:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 12582912,
          "element_stop": 15728640,
          "path": [
            "rank5.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank2.rx"
          ]
        },
        {
          "sender": "r5:nic1",
          "receiver": "r2:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 15728640,
          "element_stop": 18874368,
          "path": [
            "rank5.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank2.rx"
          ]
        },
        {
          "sender": "r2:nic0",
          "receiver": "r6:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 18874368,
          "element_stop": 22020096,
          "path": [
            "rank2.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank6.rx"
          ]
        },
        {
          "sender": "r2:nic1",
          "receiver": "r6:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 22020096,
          "element_stop": 25165824,
          "path": [
            "rank2.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank6.rx"
          ]
        },
        {
          "sender": "r6:nic0",
          "receiver": "r3:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 25165824,
          "element_stop": 28311552,
          "path": [
            "rank6.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank3.rx"
          ]
        },
        {
          "sender": "r6:nic1",
          "receiver": "r3:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 28311552,
          "element_stop": 31457280,
          "path": [
            "rank6.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank3.rx"
          ]
        },
        {
          "sender": "r3:nic0",
          "receiver": "r7:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 31457280,
          "element_stop": 34603008,
          "path": [
            "rank3.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank7.rx"
          ]
        },
        {
          "sender": "r3:nic1",
          "receiver": "r7:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 34603008,
          "element_stop": 37748736,
          "path": [
            "rank3.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank7.rx"
          ]
        },
        {
          "sender": "r7:nic0",
          "receiver": "r0:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 37748736,
          "element_stop": 40894464,
          "path": [
            "rank7.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank0.rx"
          ]
        },
        {
          "sender": "r7:nic1",
          "receiver": "r0:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 40894464,
          "element_stop": 44040192,
          "path": [
            "rank7.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank0.rx"
          ]
        }
      ],
      "resource_bytes": {
        "rank0.tx": 25165824,
        "server0.nic0.tx": 50331648,
        "server0.egress": 100663296,
        "cut.0->1": 100663296,
        "shared_cut.bidirectional": 201326592,
        "server1.ingress": 100663296,
        "server1.nic0.rx": 50331648,
        "rank4.rx": 25165824,
        "server0.nic1.tx": 50331648,
        "server1.nic1.rx": 50331648,
        "rank4.tx": 25165824,
        "server1.nic0.tx": 50331648,
        "server1.egress": 100663296,
        "cut.1->0": 100663296,
        "server0.ingress": 100663296,
        "server0.nic0.rx": 50331648,
        "rank1.rx": 25165824,
        "server1.nic1.tx": 50331648,
        "server0.nic1.rx": 50331648,
        "rank1.tx": 25165824,
        "rank5.rx": 25165824,
        "rank5.tx": 25165824,
        "rank2.rx": 25165824,
        "rank2.tx": 25165824,
        "rank6.rx": 25165824,
        "rank6.tx": 25165824,
        "rank3.rx": 25165824,
        "rank3.tx": 25165824,
        "rank7.rx": 25165824,
        "rank7.tx": 25165824,
        "rank0.rx": 25165824
      },
      "resource_lower_seconds_exact": "24576/9765625",
      "barrier_lower_seconds_exact": "787057/312500000",
      "barrier_start_seconds_exact": "7083513/312500000",
      "barrier_finish_seconds_exact": "787057/31250000"
    },
    {
      "round": 10,
      "stage": "flat",
      "phase": "all_gather",
      "step": 3,
      "messages": [
        {
          "sender": 0,
          "receiver": 4,
          "operation": "copy",
          "chunks": [
            6
          ],
          "element_start": 37748736,
          "element_stop": 44040192,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 6,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r0:nic0",
              "receiver": "r4:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 37748736,
              "element_stop": 40894464,
              "path": [
                "rank0.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank4.rx"
              ]
            },
            {
              "sender": "r0:nic1",
              "receiver": "r4:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 40894464,
              "element_stop": 44040192,
              "path": [
                "rank0.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank4.rx"
              ]
            }
          ]
        },
        {
          "sender": 4,
          "receiver": 1,
          "operation": "copy",
          "chunks": [
            7
          ],
          "element_start": 44040192,
          "element_stop": 50331648,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 7,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r4:nic0",
              "receiver": "r1:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 44040192,
              "element_stop": 47185920,
              "path": [
                "rank4.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank1.rx"
              ]
            },
            {
              "sender": "r4:nic1",
              "receiver": "r1:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 47185920,
              "element_stop": 50331648,
              "path": [
                "rank4.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank1.rx"
              ]
            }
          ]
        },
        {
          "sender": 1,
          "receiver": 5,
          "operation": "copy",
          "chunks": [
            0
          ],
          "element_start": 0,
          "element_stop": 6291456,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 0,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r1:nic0",
              "receiver": "r5:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 0,
              "element_stop": 3145728,
              "path": [
                "rank1.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank5.rx"
              ]
            },
            {
              "sender": "r1:nic1",
              "receiver": "r5:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 3145728,
              "element_stop": 6291456,
              "path": [
                "rank1.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank5.rx"
              ]
            }
          ]
        },
        {
          "sender": 5,
          "receiver": 2,
          "operation": "copy",
          "chunks": [
            1
          ],
          "element_start": 6291456,
          "element_stop": 12582912,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 1,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r5:nic0",
              "receiver": "r2:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 6291456,
              "element_stop": 9437184,
              "path": [
                "rank5.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank2.rx"
              ]
            },
            {
              "sender": "r5:nic1",
              "receiver": "r2:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 9437184,
              "element_stop": 12582912,
              "path": [
                "rank5.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank2.rx"
              ]
            }
          ]
        },
        {
          "sender": 2,
          "receiver": 6,
          "operation": "copy",
          "chunks": [
            2
          ],
          "element_start": 12582912,
          "element_stop": 18874368,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 2,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r2:nic0",
              "receiver": "r6:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 12582912,
              "element_stop": 15728640,
              "path": [
                "rank2.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank6.rx"
              ]
            },
            {
              "sender": "r2:nic1",
              "receiver": "r6:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 15728640,
              "element_stop": 18874368,
              "path": [
                "rank2.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank6.rx"
              ]
            }
          ]
        },
        {
          "sender": 6,
          "receiver": 3,
          "operation": "copy",
          "chunks": [
            3
          ],
          "element_start": 18874368,
          "element_stop": 25165824,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 3,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r6:nic0",
              "receiver": "r3:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 18874368,
              "element_stop": 22020096,
              "path": [
                "rank6.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank3.rx"
              ]
            },
            {
              "sender": "r6:nic1",
              "receiver": "r3:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 22020096,
              "element_stop": 25165824,
              "path": [
                "rank6.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank3.rx"
              ]
            }
          ]
        },
        {
          "sender": 3,
          "receiver": 7,
          "operation": "copy",
          "chunks": [
            4
          ],
          "element_start": 25165824,
          "element_stop": 31457280,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 4,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r3:nic0",
              "receiver": "r7:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 25165824,
              "element_stop": 28311552,
              "path": [
                "rank3.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank7.rx"
              ]
            },
            {
              "sender": "r3:nic1",
              "receiver": "r7:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 28311552,
              "element_stop": 31457280,
              "path": [
                "rank3.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank7.rx"
              ]
            }
          ]
        },
        {
          "sender": 7,
          "receiver": 0,
          "operation": "copy",
          "chunks": [
            5
          ],
          "element_start": 31457280,
          "element_stop": 37748736,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 5,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r7:nic0",
              "receiver": "r0:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 31457280,
              "element_stop": 34603008,
              "path": [
                "rank7.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank0.rx"
              ]
            },
            {
              "sender": "r7:nic1",
              "receiver": "r0:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 34603008,
              "element_stop": 37748736,
              "path": [
                "rank7.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank0.rx"
              ]
            }
          ]
        }
      ],
      "edges": [
        {
          "sender": "r0:nic0",
          "receiver": "r4:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 37748736,
          "element_stop": 40894464,
          "path": [
            "rank0.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank4.rx"
          ]
        },
        {
          "sender": "r0:nic1",
          "receiver": "r4:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 40894464,
          "element_stop": 44040192,
          "path": [
            "rank0.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank4.rx"
          ]
        },
        {
          "sender": "r4:nic0",
          "receiver": "r1:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 44040192,
          "element_stop": 47185920,
          "path": [
            "rank4.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank1.rx"
          ]
        },
        {
          "sender": "r4:nic1",
          "receiver": "r1:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 47185920,
          "element_stop": 50331648,
          "path": [
            "rank4.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank1.rx"
          ]
        },
        {
          "sender": "r1:nic0",
          "receiver": "r5:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 0,
          "element_stop": 3145728,
          "path": [
            "rank1.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank5.rx"
          ]
        },
        {
          "sender": "r1:nic1",
          "receiver": "r5:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 3145728,
          "element_stop": 6291456,
          "path": [
            "rank1.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank5.rx"
          ]
        },
        {
          "sender": "r5:nic0",
          "receiver": "r2:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 6291456,
          "element_stop": 9437184,
          "path": [
            "rank5.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank2.rx"
          ]
        },
        {
          "sender": "r5:nic1",
          "receiver": "r2:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 9437184,
          "element_stop": 12582912,
          "path": [
            "rank5.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank2.rx"
          ]
        },
        {
          "sender": "r2:nic0",
          "receiver": "r6:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 12582912,
          "element_stop": 15728640,
          "path": [
            "rank2.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank6.rx"
          ]
        },
        {
          "sender": "r2:nic1",
          "receiver": "r6:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 15728640,
          "element_stop": 18874368,
          "path": [
            "rank2.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank6.rx"
          ]
        },
        {
          "sender": "r6:nic0",
          "receiver": "r3:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 18874368,
          "element_stop": 22020096,
          "path": [
            "rank6.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank3.rx"
          ]
        },
        {
          "sender": "r6:nic1",
          "receiver": "r3:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 22020096,
          "element_stop": 25165824,
          "path": [
            "rank6.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank3.rx"
          ]
        },
        {
          "sender": "r3:nic0",
          "receiver": "r7:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 25165824,
          "element_stop": 28311552,
          "path": [
            "rank3.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank7.rx"
          ]
        },
        {
          "sender": "r3:nic1",
          "receiver": "r7:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 28311552,
          "element_stop": 31457280,
          "path": [
            "rank3.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank7.rx"
          ]
        },
        {
          "sender": "r7:nic0",
          "receiver": "r0:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 31457280,
          "element_stop": 34603008,
          "path": [
            "rank7.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank0.rx"
          ]
        },
        {
          "sender": "r7:nic1",
          "receiver": "r0:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 34603008,
          "element_stop": 37748736,
          "path": [
            "rank7.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank0.rx"
          ]
        }
      ],
      "resource_bytes": {
        "rank0.tx": 25165824,
        "server0.nic0.tx": 50331648,
        "server0.egress": 100663296,
        "cut.0->1": 100663296,
        "shared_cut.bidirectional": 201326592,
        "server1.ingress": 100663296,
        "server1.nic0.rx": 50331648,
        "rank4.rx": 25165824,
        "server0.nic1.tx": 50331648,
        "server1.nic1.rx": 50331648,
        "rank4.tx": 25165824,
        "server1.nic0.tx": 50331648,
        "server1.egress": 100663296,
        "cut.1->0": 100663296,
        "server0.ingress": 100663296,
        "server0.nic0.rx": 50331648,
        "rank1.rx": 25165824,
        "server1.nic1.tx": 50331648,
        "server0.nic1.rx": 50331648,
        "rank1.tx": 25165824,
        "rank5.rx": 25165824,
        "rank5.tx": 25165824,
        "rank2.rx": 25165824,
        "rank2.tx": 25165824,
        "rank6.rx": 25165824,
        "rank6.tx": 25165824,
        "rank3.rx": 25165824,
        "rank3.tx": 25165824,
        "rank7.rx": 25165824,
        "rank7.tx": 25165824,
        "rank0.rx": 25165824
      },
      "resource_lower_seconds_exact": "24576/9765625",
      "barrier_lower_seconds_exact": "787057/312500000",
      "barrier_start_seconds_exact": "787057/31250000",
      "barrier_finish_seconds_exact": "8657627/312500000"
    },
    {
      "round": 11,
      "stage": "flat",
      "phase": "all_gather",
      "step": 4,
      "messages": [
        {
          "sender": 0,
          "receiver": 4,
          "operation": "copy",
          "chunks": [
            5
          ],
          "element_start": 31457280,
          "element_stop": 37748736,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 5,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r0:nic0",
              "receiver": "r4:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 31457280,
              "element_stop": 34603008,
              "path": [
                "rank0.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank4.rx"
              ]
            },
            {
              "sender": "r0:nic1",
              "receiver": "r4:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 34603008,
              "element_stop": 37748736,
              "path": [
                "rank0.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank4.rx"
              ]
            }
          ]
        },
        {
          "sender": 4,
          "receiver": 1,
          "operation": "copy",
          "chunks": [
            6
          ],
          "element_start": 37748736,
          "element_stop": 44040192,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 6,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r4:nic0",
              "receiver": "r1:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 37748736,
              "element_stop": 40894464,
              "path": [
                "rank4.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank1.rx"
              ]
            },
            {
              "sender": "r4:nic1",
              "receiver": "r1:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 40894464,
              "element_stop": 44040192,
              "path": [
                "rank4.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank1.rx"
              ]
            }
          ]
        },
        {
          "sender": 1,
          "receiver": 5,
          "operation": "copy",
          "chunks": [
            7
          ],
          "element_start": 44040192,
          "element_stop": 50331648,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 7,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r1:nic0",
              "receiver": "r5:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 44040192,
              "element_stop": 47185920,
              "path": [
                "rank1.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank5.rx"
              ]
            },
            {
              "sender": "r1:nic1",
              "receiver": "r5:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 47185920,
              "element_stop": 50331648,
              "path": [
                "rank1.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank5.rx"
              ]
            }
          ]
        },
        {
          "sender": 5,
          "receiver": 2,
          "operation": "copy",
          "chunks": [
            0
          ],
          "element_start": 0,
          "element_stop": 6291456,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 0,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r5:nic0",
              "receiver": "r2:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 0,
              "element_stop": 3145728,
              "path": [
                "rank5.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank2.rx"
              ]
            },
            {
              "sender": "r5:nic1",
              "receiver": "r2:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 3145728,
              "element_stop": 6291456,
              "path": [
                "rank5.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank2.rx"
              ]
            }
          ]
        },
        {
          "sender": 2,
          "receiver": 6,
          "operation": "copy",
          "chunks": [
            1
          ],
          "element_start": 6291456,
          "element_stop": 12582912,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 1,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r2:nic0",
              "receiver": "r6:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 6291456,
              "element_stop": 9437184,
              "path": [
                "rank2.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank6.rx"
              ]
            },
            {
              "sender": "r2:nic1",
              "receiver": "r6:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 9437184,
              "element_stop": 12582912,
              "path": [
                "rank2.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank6.rx"
              ]
            }
          ]
        },
        {
          "sender": 6,
          "receiver": 3,
          "operation": "copy",
          "chunks": [
            2
          ],
          "element_start": 12582912,
          "element_stop": 18874368,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 2,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r6:nic0",
              "receiver": "r3:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 12582912,
              "element_stop": 15728640,
              "path": [
                "rank6.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank3.rx"
              ]
            },
            {
              "sender": "r6:nic1",
              "receiver": "r3:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 15728640,
              "element_stop": 18874368,
              "path": [
                "rank6.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank3.rx"
              ]
            }
          ]
        },
        {
          "sender": 3,
          "receiver": 7,
          "operation": "copy",
          "chunks": [
            3
          ],
          "element_start": 18874368,
          "element_stop": 25165824,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 3,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r3:nic0",
              "receiver": "r7:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 18874368,
              "element_stop": 22020096,
              "path": [
                "rank3.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank7.rx"
              ]
            },
            {
              "sender": "r3:nic1",
              "receiver": "r7:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 22020096,
              "element_stop": 25165824,
              "path": [
                "rank3.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank7.rx"
              ]
            }
          ]
        },
        {
          "sender": 7,
          "receiver": 0,
          "operation": "copy",
          "chunks": [
            4
          ],
          "element_start": 25165824,
          "element_stop": 31457280,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 4,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r7:nic0",
              "receiver": "r0:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 25165824,
              "element_stop": 28311552,
              "path": [
                "rank7.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank0.rx"
              ]
            },
            {
              "sender": "r7:nic1",
              "receiver": "r0:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 28311552,
              "element_stop": 31457280,
              "path": [
                "rank7.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank0.rx"
              ]
            }
          ]
        }
      ],
      "edges": [
        {
          "sender": "r0:nic0",
          "receiver": "r4:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 31457280,
          "element_stop": 34603008,
          "path": [
            "rank0.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank4.rx"
          ]
        },
        {
          "sender": "r0:nic1",
          "receiver": "r4:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 34603008,
          "element_stop": 37748736,
          "path": [
            "rank0.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank4.rx"
          ]
        },
        {
          "sender": "r4:nic0",
          "receiver": "r1:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 37748736,
          "element_stop": 40894464,
          "path": [
            "rank4.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank1.rx"
          ]
        },
        {
          "sender": "r4:nic1",
          "receiver": "r1:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 40894464,
          "element_stop": 44040192,
          "path": [
            "rank4.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank1.rx"
          ]
        },
        {
          "sender": "r1:nic0",
          "receiver": "r5:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 44040192,
          "element_stop": 47185920,
          "path": [
            "rank1.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank5.rx"
          ]
        },
        {
          "sender": "r1:nic1",
          "receiver": "r5:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 47185920,
          "element_stop": 50331648,
          "path": [
            "rank1.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank5.rx"
          ]
        },
        {
          "sender": "r5:nic0",
          "receiver": "r2:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 0,
          "element_stop": 3145728,
          "path": [
            "rank5.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank2.rx"
          ]
        },
        {
          "sender": "r5:nic1",
          "receiver": "r2:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 3145728,
          "element_stop": 6291456,
          "path": [
            "rank5.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank2.rx"
          ]
        },
        {
          "sender": "r2:nic0",
          "receiver": "r6:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 6291456,
          "element_stop": 9437184,
          "path": [
            "rank2.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank6.rx"
          ]
        },
        {
          "sender": "r2:nic1",
          "receiver": "r6:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 9437184,
          "element_stop": 12582912,
          "path": [
            "rank2.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank6.rx"
          ]
        },
        {
          "sender": "r6:nic0",
          "receiver": "r3:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 12582912,
          "element_stop": 15728640,
          "path": [
            "rank6.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank3.rx"
          ]
        },
        {
          "sender": "r6:nic1",
          "receiver": "r3:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 15728640,
          "element_stop": 18874368,
          "path": [
            "rank6.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank3.rx"
          ]
        },
        {
          "sender": "r3:nic0",
          "receiver": "r7:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 18874368,
          "element_stop": 22020096,
          "path": [
            "rank3.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank7.rx"
          ]
        },
        {
          "sender": "r3:nic1",
          "receiver": "r7:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 22020096,
          "element_stop": 25165824,
          "path": [
            "rank3.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank7.rx"
          ]
        },
        {
          "sender": "r7:nic0",
          "receiver": "r0:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 25165824,
          "element_stop": 28311552,
          "path": [
            "rank7.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank0.rx"
          ]
        },
        {
          "sender": "r7:nic1",
          "receiver": "r0:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 28311552,
          "element_stop": 31457280,
          "path": [
            "rank7.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank0.rx"
          ]
        }
      ],
      "resource_bytes": {
        "rank0.tx": 25165824,
        "server0.nic0.tx": 50331648,
        "server0.egress": 100663296,
        "cut.0->1": 100663296,
        "shared_cut.bidirectional": 201326592,
        "server1.ingress": 100663296,
        "server1.nic0.rx": 50331648,
        "rank4.rx": 25165824,
        "server0.nic1.tx": 50331648,
        "server1.nic1.rx": 50331648,
        "rank4.tx": 25165824,
        "server1.nic0.tx": 50331648,
        "server1.egress": 100663296,
        "cut.1->0": 100663296,
        "server0.ingress": 100663296,
        "server0.nic0.rx": 50331648,
        "rank1.rx": 25165824,
        "server1.nic1.tx": 50331648,
        "server0.nic1.rx": 50331648,
        "rank1.tx": 25165824,
        "rank5.rx": 25165824,
        "rank5.tx": 25165824,
        "rank2.rx": 25165824,
        "rank2.tx": 25165824,
        "rank6.rx": 25165824,
        "rank6.tx": 25165824,
        "rank3.rx": 25165824,
        "rank3.tx": 25165824,
        "rank7.rx": 25165824,
        "rank7.tx": 25165824,
        "rank0.rx": 25165824
      },
      "resource_lower_seconds_exact": "24576/9765625",
      "barrier_lower_seconds_exact": "787057/312500000",
      "barrier_start_seconds_exact": "8657627/312500000",
      "barrier_finish_seconds_exact": "2361171/78125000"
    },
    {
      "round": 12,
      "stage": "flat",
      "phase": "all_gather",
      "step": 5,
      "messages": [
        {
          "sender": 0,
          "receiver": 4,
          "operation": "copy",
          "chunks": [
            4
          ],
          "element_start": 25165824,
          "element_stop": 31457280,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 4,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r0:nic0",
              "receiver": "r4:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 25165824,
              "element_stop": 28311552,
              "path": [
                "rank0.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank4.rx"
              ]
            },
            {
              "sender": "r0:nic1",
              "receiver": "r4:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 28311552,
              "element_stop": 31457280,
              "path": [
                "rank0.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank4.rx"
              ]
            }
          ]
        },
        {
          "sender": 4,
          "receiver": 1,
          "operation": "copy",
          "chunks": [
            5
          ],
          "element_start": 31457280,
          "element_stop": 37748736,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 5,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r4:nic0",
              "receiver": "r1:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 31457280,
              "element_stop": 34603008,
              "path": [
                "rank4.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank1.rx"
              ]
            },
            {
              "sender": "r4:nic1",
              "receiver": "r1:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 34603008,
              "element_stop": 37748736,
              "path": [
                "rank4.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank1.rx"
              ]
            }
          ]
        },
        {
          "sender": 1,
          "receiver": 5,
          "operation": "copy",
          "chunks": [
            6
          ],
          "element_start": 37748736,
          "element_stop": 44040192,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 6,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r1:nic0",
              "receiver": "r5:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 37748736,
              "element_stop": 40894464,
              "path": [
                "rank1.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank5.rx"
              ]
            },
            {
              "sender": "r1:nic1",
              "receiver": "r5:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 40894464,
              "element_stop": 44040192,
              "path": [
                "rank1.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank5.rx"
              ]
            }
          ]
        },
        {
          "sender": 5,
          "receiver": 2,
          "operation": "copy",
          "chunks": [
            7
          ],
          "element_start": 44040192,
          "element_stop": 50331648,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 7,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r5:nic0",
              "receiver": "r2:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 44040192,
              "element_stop": 47185920,
              "path": [
                "rank5.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank2.rx"
              ]
            },
            {
              "sender": "r5:nic1",
              "receiver": "r2:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 47185920,
              "element_stop": 50331648,
              "path": [
                "rank5.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank2.rx"
              ]
            }
          ]
        },
        {
          "sender": 2,
          "receiver": 6,
          "operation": "copy",
          "chunks": [
            0
          ],
          "element_start": 0,
          "element_stop": 6291456,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 0,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r2:nic0",
              "receiver": "r6:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 0,
              "element_stop": 3145728,
              "path": [
                "rank2.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank6.rx"
              ]
            },
            {
              "sender": "r2:nic1",
              "receiver": "r6:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 3145728,
              "element_stop": 6291456,
              "path": [
                "rank2.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank6.rx"
              ]
            }
          ]
        },
        {
          "sender": 6,
          "receiver": 3,
          "operation": "copy",
          "chunks": [
            1
          ],
          "element_start": 6291456,
          "element_stop": 12582912,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 1,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r6:nic0",
              "receiver": "r3:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 6291456,
              "element_stop": 9437184,
              "path": [
                "rank6.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank3.rx"
              ]
            },
            {
              "sender": "r6:nic1",
              "receiver": "r3:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 9437184,
              "element_stop": 12582912,
              "path": [
                "rank6.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank3.rx"
              ]
            }
          ]
        },
        {
          "sender": 3,
          "receiver": 7,
          "operation": "copy",
          "chunks": [
            2
          ],
          "element_start": 12582912,
          "element_stop": 18874368,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 2,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r3:nic0",
              "receiver": "r7:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 12582912,
              "element_stop": 15728640,
              "path": [
                "rank3.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank7.rx"
              ]
            },
            {
              "sender": "r3:nic1",
              "receiver": "r7:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 15728640,
              "element_stop": 18874368,
              "path": [
                "rank3.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank7.rx"
              ]
            }
          ]
        },
        {
          "sender": 7,
          "receiver": 0,
          "operation": "copy",
          "chunks": [
            3
          ],
          "element_start": 18874368,
          "element_stop": 25165824,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 3,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r7:nic0",
              "receiver": "r0:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 18874368,
              "element_stop": 22020096,
              "path": [
                "rank7.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank0.rx"
              ]
            },
            {
              "sender": "r7:nic1",
              "receiver": "r0:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 22020096,
              "element_stop": 25165824,
              "path": [
                "rank7.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank0.rx"
              ]
            }
          ]
        }
      ],
      "edges": [
        {
          "sender": "r0:nic0",
          "receiver": "r4:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 25165824,
          "element_stop": 28311552,
          "path": [
            "rank0.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank4.rx"
          ]
        },
        {
          "sender": "r0:nic1",
          "receiver": "r4:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 28311552,
          "element_stop": 31457280,
          "path": [
            "rank0.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank4.rx"
          ]
        },
        {
          "sender": "r4:nic0",
          "receiver": "r1:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 31457280,
          "element_stop": 34603008,
          "path": [
            "rank4.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank1.rx"
          ]
        },
        {
          "sender": "r4:nic1",
          "receiver": "r1:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 34603008,
          "element_stop": 37748736,
          "path": [
            "rank4.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank1.rx"
          ]
        },
        {
          "sender": "r1:nic0",
          "receiver": "r5:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 37748736,
          "element_stop": 40894464,
          "path": [
            "rank1.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank5.rx"
          ]
        },
        {
          "sender": "r1:nic1",
          "receiver": "r5:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 40894464,
          "element_stop": 44040192,
          "path": [
            "rank1.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank5.rx"
          ]
        },
        {
          "sender": "r5:nic0",
          "receiver": "r2:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 44040192,
          "element_stop": 47185920,
          "path": [
            "rank5.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank2.rx"
          ]
        },
        {
          "sender": "r5:nic1",
          "receiver": "r2:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 47185920,
          "element_stop": 50331648,
          "path": [
            "rank5.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank2.rx"
          ]
        },
        {
          "sender": "r2:nic0",
          "receiver": "r6:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 0,
          "element_stop": 3145728,
          "path": [
            "rank2.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank6.rx"
          ]
        },
        {
          "sender": "r2:nic1",
          "receiver": "r6:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 3145728,
          "element_stop": 6291456,
          "path": [
            "rank2.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank6.rx"
          ]
        },
        {
          "sender": "r6:nic0",
          "receiver": "r3:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 6291456,
          "element_stop": 9437184,
          "path": [
            "rank6.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank3.rx"
          ]
        },
        {
          "sender": "r6:nic1",
          "receiver": "r3:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 9437184,
          "element_stop": 12582912,
          "path": [
            "rank6.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank3.rx"
          ]
        },
        {
          "sender": "r3:nic0",
          "receiver": "r7:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 12582912,
          "element_stop": 15728640,
          "path": [
            "rank3.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank7.rx"
          ]
        },
        {
          "sender": "r3:nic1",
          "receiver": "r7:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 15728640,
          "element_stop": 18874368,
          "path": [
            "rank3.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank7.rx"
          ]
        },
        {
          "sender": "r7:nic0",
          "receiver": "r0:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 18874368,
          "element_stop": 22020096,
          "path": [
            "rank7.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank0.rx"
          ]
        },
        {
          "sender": "r7:nic1",
          "receiver": "r0:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 22020096,
          "element_stop": 25165824,
          "path": [
            "rank7.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank0.rx"
          ]
        }
      ],
      "resource_bytes": {
        "rank0.tx": 25165824,
        "server0.nic0.tx": 50331648,
        "server0.egress": 100663296,
        "cut.0->1": 100663296,
        "shared_cut.bidirectional": 201326592,
        "server1.ingress": 100663296,
        "server1.nic0.rx": 50331648,
        "rank4.rx": 25165824,
        "server0.nic1.tx": 50331648,
        "server1.nic1.rx": 50331648,
        "rank4.tx": 25165824,
        "server1.nic0.tx": 50331648,
        "server1.egress": 100663296,
        "cut.1->0": 100663296,
        "server0.ingress": 100663296,
        "server0.nic0.rx": 50331648,
        "rank1.rx": 25165824,
        "server1.nic1.tx": 50331648,
        "server0.nic1.rx": 50331648,
        "rank1.tx": 25165824,
        "rank5.rx": 25165824,
        "rank5.tx": 25165824,
        "rank2.rx": 25165824,
        "rank2.tx": 25165824,
        "rank6.rx": 25165824,
        "rank6.tx": 25165824,
        "rank3.rx": 25165824,
        "rank3.tx": 25165824,
        "rank7.rx": 25165824,
        "rank7.tx": 25165824,
        "rank0.rx": 25165824
      },
      "resource_lower_seconds_exact": "24576/9765625",
      "barrier_lower_seconds_exact": "787057/312500000",
      "barrier_start_seconds_exact": "2361171/78125000",
      "barrier_finish_seconds_exact": "10231741/312500000"
    },
    {
      "round": 13,
      "stage": "flat",
      "phase": "all_gather",
      "step": 6,
      "messages": [
        {
          "sender": 0,
          "receiver": 4,
          "operation": "copy",
          "chunks": [
            3
          ],
          "element_start": 18874368,
          "element_stop": 25165824,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 3,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r0:nic0",
              "receiver": "r4:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 18874368,
              "element_stop": 22020096,
              "path": [
                "rank0.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank4.rx"
              ]
            },
            {
              "sender": "r0:nic1",
              "receiver": "r4:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 22020096,
              "element_stop": 25165824,
              "path": [
                "rank0.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank4.rx"
              ]
            }
          ]
        },
        {
          "sender": 4,
          "receiver": 1,
          "operation": "copy",
          "chunks": [
            4
          ],
          "element_start": 25165824,
          "element_stop": 31457280,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 4,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r4:nic0",
              "receiver": "r1:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 25165824,
              "element_stop": 28311552,
              "path": [
                "rank4.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank1.rx"
              ]
            },
            {
              "sender": "r4:nic1",
              "receiver": "r1:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 28311552,
              "element_stop": 31457280,
              "path": [
                "rank4.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank1.rx"
              ]
            }
          ]
        },
        {
          "sender": 1,
          "receiver": 5,
          "operation": "copy",
          "chunks": [
            5
          ],
          "element_start": 31457280,
          "element_stop": 37748736,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 5,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r1:nic0",
              "receiver": "r5:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 31457280,
              "element_stop": 34603008,
              "path": [
                "rank1.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank5.rx"
              ]
            },
            {
              "sender": "r1:nic1",
              "receiver": "r5:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 34603008,
              "element_stop": 37748736,
              "path": [
                "rank1.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank5.rx"
              ]
            }
          ]
        },
        {
          "sender": 5,
          "receiver": 2,
          "operation": "copy",
          "chunks": [
            6
          ],
          "element_start": 37748736,
          "element_stop": 44040192,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 6,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r5:nic0",
              "receiver": "r2:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 37748736,
              "element_stop": 40894464,
              "path": [
                "rank5.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank2.rx"
              ]
            },
            {
              "sender": "r5:nic1",
              "receiver": "r2:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 40894464,
              "element_stop": 44040192,
              "path": [
                "rank5.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank2.rx"
              ]
            }
          ]
        },
        {
          "sender": 2,
          "receiver": 6,
          "operation": "copy",
          "chunks": [
            7
          ],
          "element_start": 44040192,
          "element_stop": 50331648,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 7,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r2:nic0",
              "receiver": "r6:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 44040192,
              "element_stop": 47185920,
              "path": [
                "rank2.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank6.rx"
              ]
            },
            {
              "sender": "r2:nic1",
              "receiver": "r6:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 47185920,
              "element_stop": 50331648,
              "path": [
                "rank2.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank6.rx"
              ]
            }
          ]
        },
        {
          "sender": 6,
          "receiver": 3,
          "operation": "copy",
          "chunks": [
            0
          ],
          "element_start": 0,
          "element_stop": 6291456,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 0,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r6:nic0",
              "receiver": "r3:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 0,
              "element_stop": 3145728,
              "path": [
                "rank6.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank3.rx"
              ]
            },
            {
              "sender": "r6:nic1",
              "receiver": "r3:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 3145728,
              "element_stop": 6291456,
              "path": [
                "rank6.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank3.rx"
              ]
            }
          ]
        },
        {
          "sender": 3,
          "receiver": 7,
          "operation": "copy",
          "chunks": [
            1
          ],
          "element_start": 6291456,
          "element_stop": 12582912,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 1,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r3:nic0",
              "receiver": "r7:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 6291456,
              "element_stop": 9437184,
              "path": [
                "rank3.tx",
                "server0.nic0.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic0.rx",
                "rank7.rx"
              ]
            },
            {
              "sender": "r3:nic1",
              "receiver": "r7:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 9437184,
              "element_stop": 12582912,
              "path": [
                "rank3.tx",
                "server0.nic1.tx",
                "server0.egress",
                "cut.0->1",
                "shared_cut.bidirectional",
                "server1.ingress",
                "server1.nic1.rx",
                "rank7.rx"
              ]
            }
          ]
        },
        {
          "sender": 7,
          "receiver": 0,
          "operation": "copy",
          "chunks": [
            2
          ],
          "element_start": 12582912,
          "element_stop": 18874368,
          "bytes": 25165824,
          "contributions": [
            {
              "chunk": 2,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ],
          "remote": true,
          "stripes": [
            {
              "sender": "r7:nic0",
              "receiver": "r0:nic0",
              "bytes": 12582912,
              "nic": 0,
              "element_start": 12582912,
              "element_stop": 15728640,
              "path": [
                "rank7.tx",
                "server1.nic0.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic0.rx",
                "rank0.rx"
              ]
            },
            {
              "sender": "r7:nic1",
              "receiver": "r0:nic1",
              "bytes": 12582912,
              "nic": 1,
              "element_start": 15728640,
              "element_stop": 18874368,
              "path": [
                "rank7.tx",
                "server1.nic1.tx",
                "server1.egress",
                "cut.1->0",
                "shared_cut.bidirectional",
                "server0.ingress",
                "server0.nic1.rx",
                "rank0.rx"
              ]
            }
          ]
        }
      ],
      "edges": [
        {
          "sender": "r0:nic0",
          "receiver": "r4:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 18874368,
          "element_stop": 22020096,
          "path": [
            "rank0.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank4.rx"
          ]
        },
        {
          "sender": "r0:nic1",
          "receiver": "r4:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 22020096,
          "element_stop": 25165824,
          "path": [
            "rank0.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank4.rx"
          ]
        },
        {
          "sender": "r4:nic0",
          "receiver": "r1:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 25165824,
          "element_stop": 28311552,
          "path": [
            "rank4.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank1.rx"
          ]
        },
        {
          "sender": "r4:nic1",
          "receiver": "r1:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 28311552,
          "element_stop": 31457280,
          "path": [
            "rank4.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank1.rx"
          ]
        },
        {
          "sender": "r1:nic0",
          "receiver": "r5:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 31457280,
          "element_stop": 34603008,
          "path": [
            "rank1.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank5.rx"
          ]
        },
        {
          "sender": "r1:nic1",
          "receiver": "r5:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 34603008,
          "element_stop": 37748736,
          "path": [
            "rank1.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank5.rx"
          ]
        },
        {
          "sender": "r5:nic0",
          "receiver": "r2:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 37748736,
          "element_stop": 40894464,
          "path": [
            "rank5.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank2.rx"
          ]
        },
        {
          "sender": "r5:nic1",
          "receiver": "r2:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 40894464,
          "element_stop": 44040192,
          "path": [
            "rank5.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank2.rx"
          ]
        },
        {
          "sender": "r2:nic0",
          "receiver": "r6:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 44040192,
          "element_stop": 47185920,
          "path": [
            "rank2.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank6.rx"
          ]
        },
        {
          "sender": "r2:nic1",
          "receiver": "r6:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 47185920,
          "element_stop": 50331648,
          "path": [
            "rank2.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank6.rx"
          ]
        },
        {
          "sender": "r6:nic0",
          "receiver": "r3:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 0,
          "element_stop": 3145728,
          "path": [
            "rank6.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank3.rx"
          ]
        },
        {
          "sender": "r6:nic1",
          "receiver": "r3:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 3145728,
          "element_stop": 6291456,
          "path": [
            "rank6.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank3.rx"
          ]
        },
        {
          "sender": "r3:nic0",
          "receiver": "r7:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 6291456,
          "element_stop": 9437184,
          "path": [
            "rank3.tx",
            "server0.nic0.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic0.rx",
            "rank7.rx"
          ]
        },
        {
          "sender": "r3:nic1",
          "receiver": "r7:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 9437184,
          "element_stop": 12582912,
          "path": [
            "rank3.tx",
            "server0.nic1.tx",
            "server0.egress",
            "cut.0->1",
            "shared_cut.bidirectional",
            "server1.ingress",
            "server1.nic1.rx",
            "rank7.rx"
          ]
        },
        {
          "sender": "r7:nic0",
          "receiver": "r0:nic0",
          "bytes": 12582912,
          "nic": 0,
          "element_start": 12582912,
          "element_stop": 15728640,
          "path": [
            "rank7.tx",
            "server1.nic0.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic0.rx",
            "rank0.rx"
          ]
        },
        {
          "sender": "r7:nic1",
          "receiver": "r0:nic1",
          "bytes": 12582912,
          "nic": 1,
          "element_start": 15728640,
          "element_stop": 18874368,
          "path": [
            "rank7.tx",
            "server1.nic1.tx",
            "server1.egress",
            "cut.1->0",
            "shared_cut.bidirectional",
            "server0.ingress",
            "server0.nic1.rx",
            "rank0.rx"
          ]
        }
      ],
      "resource_bytes": {
        "rank0.tx": 25165824,
        "server0.nic0.tx": 50331648,
        "server0.egress": 100663296,
        "cut.0->1": 100663296,
        "shared_cut.bidirectional": 201326592,
        "server1.ingress": 100663296,
        "server1.nic0.rx": 50331648,
        "rank4.rx": 25165824,
        "server0.nic1.tx": 50331648,
        "server1.nic1.rx": 50331648,
        "rank4.tx": 25165824,
        "server1.nic0.tx": 50331648,
        "server1.egress": 100663296,
        "cut.1->0": 100663296,
        "server0.ingress": 100663296,
        "server0.nic0.rx": 50331648,
        "rank1.rx": 25165824,
        "server1.nic1.tx": 50331648,
        "server0.nic1.rx": 50331648,
        "rank1.tx": 25165824,
        "rank5.rx": 25165824,
        "rank5.tx": 25165824,
        "rank2.rx": 25165824,
        "rank2.tx": 25165824,
        "rank6.rx": 25165824,
        "rank6.tx": 25165824,
        "rank3.rx": 25165824,
        "rank3.tx": 25165824,
        "rank7.rx": 25165824,
        "rank7.tx": 25165824,
        "rank0.rx": 25165824
      },
      "resource_lower_seconds_exact": "24576/9765625",
      "barrier_lower_seconds_exact": "787057/312500000",
      "barrier_start_seconds_exact": "10231741/312500000",
      "barrier_finish_seconds_exact": "5509399/156250000"
    }
  ],
  "ownership_boundaries": [
    {
      "after": "initial",
      "round_count": 0,
      "ranks": [
        {
          "rank": 0,
          "chunks": [
            {
              "chunk": 0,
              "contributors": [
                0
              ]
            },
            {
              "chunk": 1,
              "contributors": [
                0
              ]
            },
            {
              "chunk": 2,
              "contributors": [
                0
              ]
            },
            {
              "chunk": 3,
              "contributors": [
                0
              ]
            },
            {
              "chunk": 4,
              "contributors": [
                0
              ]
            },
            {
              "chunk": 5,
              "contributors": [
                0
              ]
            },
            {
              "chunk": 6,
              "contributors": [
                0
              ]
            },
            {
              "chunk": 7,
              "contributors": [
                0
              ]
            }
          ]
        },
        {
          "rank": 1,
          "chunks": [
            {
              "chunk": 0,
              "contributors": [
                1
              ]
            },
            {
              "chunk": 1,
              "contributors": [
                1
              ]
            },
            {
              "chunk": 2,
              "contributors": [
                1
              ]
            },
            {
              "chunk": 3,
              "contributors": [
                1
              ]
            },
            {
              "chunk": 4,
              "contributors": [
                1
              ]
            },
            {
              "chunk": 5,
              "contributors": [
                1
              ]
            },
            {
              "chunk": 6,
              "contributors": [
                1
              ]
            },
            {
              "chunk": 7,
              "contributors": [
                1
              ]
            }
          ]
        },
        {
          "rank": 2,
          "chunks": [
            {
              "chunk": 0,
              "contributors": [
                2
              ]
            },
            {
              "chunk": 1,
              "contributors": [
                2
              ]
            },
            {
              "chunk": 2,
              "contributors": [
                2
              ]
            },
            {
              "chunk": 3,
              "contributors": [
                2
              ]
            },
            {
              "chunk": 4,
              "contributors": [
                2
              ]
            },
            {
              "chunk": 5,
              "contributors": [
                2
              ]
            },
            {
              "chunk": 6,
              "contributors": [
                2
              ]
            },
            {
              "chunk": 7,
              "contributors": [
                2
              ]
            }
          ]
        },
        {
          "rank": 3,
          "chunks": [
            {
              "chunk": 0,
              "contributors": [
                3
              ]
            },
            {
              "chunk": 1,
              "contributors": [
                3
              ]
            },
            {
              "chunk": 2,
              "contributors": [
                3
              ]
            },
            {
              "chunk": 3,
              "contributors": [
                3
              ]
            },
            {
              "chunk": 4,
              "contributors": [
                3
              ]
            },
            {
              "chunk": 5,
              "contributors": [
                3
              ]
            },
            {
              "chunk": 6,
              "contributors": [
                3
              ]
            },
            {
              "chunk": 7,
              "contributors": [
                3
              ]
            }
          ]
        },
        {
          "rank": 4,
          "chunks": [
            {
              "chunk": 0,
              "contributors": [
                4
              ]
            },
            {
              "chunk": 1,
              "contributors": [
                4
              ]
            },
            {
              "chunk": 2,
              "contributors": [
                4
              ]
            },
            {
              "chunk": 3,
              "contributors": [
                4
              ]
            },
            {
              "chunk": 4,
              "contributors": [
                4
              ]
            },
            {
              "chunk": 5,
              "contributors": [
                4
              ]
            },
            {
              "chunk": 6,
              "contributors": [
                4
              ]
            },
            {
              "chunk": 7,
              "contributors": [
                4
              ]
            }
          ]
        },
        {
          "rank": 5,
          "chunks": [
            {
              "chunk": 0,
              "contributors": [
                5
              ]
            },
            {
              "chunk": 1,
              "contributors": [
                5
              ]
            },
            {
              "chunk": 2,
              "contributors": [
                5
              ]
            },
            {
              "chunk": 3,
              "contributors": [
                5
              ]
            },
            {
              "chunk": 4,
              "contributors": [
                5
              ]
            },
            {
              "chunk": 5,
              "contributors": [
                5
              ]
            },
            {
              "chunk": 6,
              "contributors": [
                5
              ]
            },
            {
              "chunk": 7,
              "contributors": [
                5
              ]
            }
          ]
        },
        {
          "rank": 6,
          "chunks": [
            {
              "chunk": 0,
              "contributors": [
                6
              ]
            },
            {
              "chunk": 1,
              "contributors": [
                6
              ]
            },
            {
              "chunk": 2,
              "contributors": [
                6
              ]
            },
            {
              "chunk": 3,
              "contributors": [
                6
              ]
            },
            {
              "chunk": 4,
              "contributors": [
                6
              ]
            },
            {
              "chunk": 5,
              "contributors": [
                6
              ]
            },
            {
              "chunk": 6,
              "contributors": [
                6
              ]
            },
            {
              "chunk": 7,
              "contributors": [
                6
              ]
            }
          ]
        },
        {
          "rank": 7,
          "chunks": [
            {
              "chunk": 0,
              "contributors": [
                7
              ]
            },
            {
              "chunk": 1,
              "contributors": [
                7
              ]
            },
            {
              "chunk": 2,
              "contributors": [
                7
              ]
            },
            {
              "chunk": 3,
              "contributors": [
                7
              ]
            },
            {
              "chunk": 4,
              "contributors": [
                7
              ]
            },
            {
              "chunk": 5,
              "contributors": [
                7
              ]
            },
            {
              "chunk": 6,
              "contributors": [
                7
              ]
            },
            {
              "chunk": 7,
              "contributors": [
                7
              ]
            }
          ]
        }
      ]
    },
    {
      "after": "flat:reduce_scatter",
      "round_count": 7,
      "ranks": [
        {
          "rank": 0,
          "chunks": [
            {
              "chunk": 1,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ]
        },
        {
          "rank": 1,
          "chunks": [
            {
              "chunk": 3,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ]
        },
        {
          "rank": 2,
          "chunks": [
            {
              "chunk": 5,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ]
        },
        {
          "rank": 3,
          "chunks": [
            {
              "chunk": 7,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ]
        },
        {
          "rank": 4,
          "chunks": [
            {
              "chunk": 2,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ]
        },
        {
          "rank": 5,
          "chunks": [
            {
              "chunk": 4,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ]
        },
        {
          "rank": 6,
          "chunks": [
            {
              "chunk": 6,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ]
        },
        {
          "rank": 7,
          "chunks": [
            {
              "chunk": 0,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ]
        }
      ]
    },
    {
      "after": "flat:all_gather",
      "round_count": 14,
      "ranks": [
        {
          "rank": 0,
          "chunks": [
            {
              "chunk": 0,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 1,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 2,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 3,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 4,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 5,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 6,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 7,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ]
        },
        {
          "rank": 1,
          "chunks": [
            {
              "chunk": 0,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 1,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 2,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 3,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 4,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 5,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 6,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 7,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ]
        },
        {
          "rank": 2,
          "chunks": [
            {
              "chunk": 0,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 1,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 2,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 3,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 4,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 5,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 6,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 7,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ]
        },
        {
          "rank": 3,
          "chunks": [
            {
              "chunk": 0,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 1,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 2,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 3,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 4,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 5,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 6,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 7,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ]
        },
        {
          "rank": 4,
          "chunks": [
            {
              "chunk": 0,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 1,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 2,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 3,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 4,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 5,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 6,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 7,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ]
        },
        {
          "rank": 5,
          "chunks": [
            {
              "chunk": 0,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 1,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 2,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 3,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 4,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 5,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 6,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 7,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ]
        },
        {
          "rank": 6,
          "chunks": [
            {
              "chunk": 0,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 1,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 2,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 3,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 4,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 5,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 6,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 7,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ]
        },
        {
          "rank": 7,
          "chunks": [
            {
              "chunk": 0,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 1,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 2,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 3,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 4,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 5,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 6,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            },
            {
              "chunk": 7,
              "contributors": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7
              ]
            }
          ]
        }
      ]
    }
  ],
  "resources": [
    {
      "resource": "cut.0->1",
      "bytes": 1409286144,
      "bandwidth_bytes_per_second": 40000000000,
      "service_seconds_exact": "344064/9765625"
    },
    {
      "resource": "cut.1->0",
      "bytes": 1409286144,
      "bandwidth_bytes_per_second": 40000000000,
      "service_seconds_exact": "344064/9765625"
    },
    {
      "resource": "rank0.rx",
      "bytes": 352321536,
      "bandwidth_bytes_per_second": 200000000000,
      "service_seconds_exact": "86016/48828125"
    },
    {
      "resource": "rank0.tx",
      "bytes": 352321536,
      "bandwidth_bytes_per_second": 200000000000,
      "service_seconds_exact": "86016/48828125"
    },
    {
      "resource": "rank1.rx",
      "bytes": 352321536,
      "bandwidth_bytes_per_second": 200000000000,
      "service_seconds_exact": "86016/48828125"
    },
    {
      "resource": "rank1.tx",
      "bytes": 352321536,
      "bandwidth_bytes_per_second": 200000000000,
      "service_seconds_exact": "86016/48828125"
    },
    {
      "resource": "rank2.rx",
      "bytes": 352321536,
      "bandwidth_bytes_per_second": 200000000000,
      "service_seconds_exact": "86016/48828125"
    },
    {
      "resource": "rank2.tx",
      "bytes": 352321536,
      "bandwidth_bytes_per_second": 200000000000,
      "service_seconds_exact": "86016/48828125"
    },
    {
      "resource": "rank3.rx",
      "bytes": 352321536,
      "bandwidth_bytes_per_second": 200000000000,
      "service_seconds_exact": "86016/48828125"
    },
    {
      "resource": "rank3.tx",
      "bytes": 352321536,
      "bandwidth_bytes_per_second": 200000000000,
      "service_seconds_exact": "86016/48828125"
    },
    {
      "resource": "rank4.rx",
      "bytes": 352321536,
      "bandwidth_bytes_per_second": 200000000000,
      "service_seconds_exact": "86016/48828125"
    },
    {
      "resource": "rank4.tx",
      "bytes": 352321536,
      "bandwidth_bytes_per_second": 200000000000,
      "service_seconds_exact": "86016/48828125"
    },
    {
      "resource": "rank5.rx",
      "bytes": 352321536,
      "bandwidth_bytes_per_second": 200000000000,
      "service_seconds_exact": "86016/48828125"
    },
    {
      "resource": "rank5.tx",
      "bytes": 352321536,
      "bandwidth_bytes_per_second": 200000000000,
      "service_seconds_exact": "86016/48828125"
    },
    {
      "resource": "rank6.rx",
      "bytes": 352321536,
      "bandwidth_bytes_per_second": 200000000000,
      "service_seconds_exact": "86016/48828125"
    },
    {
      "resource": "rank6.tx",
      "bytes": 352321536,
      "bandwidth_bytes_per_second": 200000000000,
      "service_seconds_exact": "86016/48828125"
    },
    {
      "resource": "rank7.rx",
      "bytes": 352321536,
      "bandwidth_bytes_per_second": 200000000000,
      "service_seconds_exact": "86016/48828125"
    },
    {
      "resource": "rank7.tx",
      "bytes": 352321536,
      "bandwidth_bytes_per_second": 200000000000,
      "service_seconds_exact": "86016/48828125"
    },
    {
      "resource": "server0.egress",
      "bytes": 1409286144,
      "bandwidth_bytes_per_second": 40000000000,
      "service_seconds_exact": "344064/9765625"
    },
    {
      "resource": "server0.ingress",
      "bytes": 1409286144,
      "bandwidth_bytes_per_second": 40000000000,
      "service_seconds_exact": "344064/9765625"
    },
    {
      "resource": "server0.nic0.rx",
      "bytes": 704643072,
      "bandwidth_bytes_per_second": 25000000000,
      "service_seconds_exact": "1376256/48828125"
    },
    {
      "resource": "server0.nic0.tx",
      "bytes": 704643072,
      "bandwidth_bytes_per_second": 25000000000,
      "service_seconds_exact": "1376256/48828125"
    },
    {
      "resource": "server0.nic1.rx",
      "bytes": 704643072,
      "bandwidth_bytes_per_second": 25000000000,
      "service_seconds_exact": "1376256/48828125"
    },
    {
      "resource": "server0.nic1.tx",
      "bytes": 704643072,
      "bandwidth_bytes_per_second": 25000000000,
      "service_seconds_exact": "1376256/48828125"
    },
    {
      "resource": "server1.egress",
      "bytes": 1409286144,
      "bandwidth_bytes_per_second": 40000000000,
      "service_seconds_exact": "344064/9765625"
    },
    {
      "resource": "server1.ingress",
      "bytes": 1409286144,
      "bandwidth_bytes_per_second": 40000000000,
      "service_seconds_exact": "344064/9765625"
    },
    {
      "resource": "server1.nic0.rx",
      "bytes": 704643072,
      "bandwidth_bytes_per_second": 25000000000,
      "service_seconds_exact": "1376256/48828125"
    },
    {
      "resource": "server1.nic0.tx",
      "bytes": 704643072,
      "bandwidth_bytes_per_second": 25000000000,
      "service_seconds_exact": "1376256/48828125"
    },
    {
      "resource": "server1.nic1.rx",
      "bytes": 704643072,
      "bandwidth_bytes_per_second": 25000000000,
      "service_seconds_exact": "1376256/48828125"
    },
    {
      "resource": "server1.nic1.tx",
      "bytes": 704643072,
      "bandwidth_bytes_per_second": 25000000000,
      "service_seconds_exact": "1376256/48828125"
    },
    {
      "resource": "shared_cut.bidirectional",
      "bytes": 2818572288,
      "bandwidth_bytes_per_second": 80000000000,
      "service_seconds_exact": "344064/9765625"
    }
  ],
  "stages": [
    {
      "stage": "flat",
      "rounds": 14,
      "send_bytes": 2818572288,
      "remote_send_bytes": 2818572288,
      "barrier_lower_seconds_exact": "5509399/156250000"
    }
  ],
  "traffic_account": {
    "logical_send_bytes": 2818572288,
    "resources": [
      {
        "resource": "cut.0->1",
        "bytes": 1409286144,
        "bandwidth_bytes_per_second": 40000000000,
        "service_seconds": 0.0352321536
      },
      {
        "resource": "cut.1->0",
        "bytes": 1409286144,
        "bandwidth_bytes_per_second": 40000000000,
        "service_seconds": 0.0352321536
      },
      {
        "resource": "rank0.rx",
        "bytes": 352321536,
        "bandwidth_bytes_per_second": 200000000000,
        "service_seconds": 0.00176160768
      },
      {
        "resource": "rank0.tx",
        "bytes": 352321536,
        "bandwidth_bytes_per_second": 200000000000,
        "service_seconds": 0.00176160768
      },
      {
        "resource": "rank1.rx",
        "bytes": 352321536,
        "bandwidth_bytes_per_second": 200000000000,
        "service_seconds": 0.00176160768
      },
      {
        "resource": "rank1.tx",
        "bytes": 352321536,
        "bandwidth_bytes_per_second": 200000000000,
        "service_seconds": 0.00176160768
      },
      {
        "resource": "rank2.rx",
        "bytes": 352321536,
        "bandwidth_bytes_per_second": 200000000000,
        "service_seconds": 0.00176160768
      },
      {
        "resource": "rank2.tx",
        "bytes": 352321536,
        "bandwidth_bytes_per_second": 200000000000,
        "service_seconds": 0.00176160768
      },
      {
        "resource": "rank3.rx",
        "bytes": 352321536,
        "bandwidth_bytes_per_second": 200000000000,
        "service_seconds": 0.00176160768
      },
      {
        "resource": "rank3.tx",
        "bytes": 352321536,
        "bandwidth_bytes_per_second": 200000000000,
        "service_seconds": 0.00176160768
      },
      {
        "resource": "rank4.rx",
        "bytes": 352321536,
        "bandwidth_bytes_per_second": 200000000000,
        "service_seconds": 0.00176160768
      },
      {
        "resource": "rank4.tx",
        "bytes": 352321536,
        "bandwidth_bytes_per_second": 200000000000,
        "service_seconds": 0.00176160768
      },
      {
        "resource": "rank5.rx",
        "bytes": 352321536,
        "bandwidth_bytes_per_second": 200000000000,
        "service_seconds": 0.00176160768
      },
      {
        "resource": "rank5.tx",
        "bytes": 352321536,
        "bandwidth_bytes_per_second": 200000000000,
        "service_seconds": 0.00176160768
      },
      {
        "resource": "rank6.rx",
        "bytes": 352321536,
        "bandwidth_bytes_per_second": 200000000000,
        "service_seconds": 0.00176160768
      },
      {
        "resource": "rank6.tx",
        "bytes": 352321536,
        "bandwidth_bytes_per_second": 200000000000,
        "service_seconds": 0.00176160768
      },
      {
        "resource": "rank7.rx",
        "bytes": 352321536,
        "bandwidth_bytes_per_second": 200000000000,
        "service_seconds": 0.00176160768
      },
      {
        "resource": "rank7.tx",
        "bytes": 352321536,
        "bandwidth_bytes_per_second": 200000000000,
        "service_seconds": 0.00176160768
      },
      {
        "resource": "server0.egress",
        "bytes": 1409286144,
        "bandwidth_bytes_per_second": 40000000000,
        "service_seconds": 0.0352321536
      },
      {
        "resource": "server0.ingress",
        "bytes": 1409286144,
        "bandwidth_bytes_per_second": 40000000000,
        "service_seconds": 0.0352321536
      },
      {
        "resource": "server0.nic0.rx",
        "bytes": 704643072,
        "bandwidth_bytes_per_second": 25000000000,
        "service_seconds": 0.02818572288
      },
      {
        "resource": "server0.nic0.tx",
        "bytes": 704643072,
        "bandwidth_bytes_per_second": 25000000000,
        "service_seconds": 0.02818572288
      },
      {
        "resource": "server0.nic1.rx",
        "bytes": 704643072,
        "bandwidth_bytes_per_second": 25000000000,
        "service_seconds": 0.02818572288
      },
      {
        "resource": "server0.nic1.tx",
        "bytes": 704643072,
        "bandwidth_bytes_per_second": 25000000000,
        "service_seconds": 0.02818572288
      },
      {
        "resource": "server1.egress",
        "bytes": 1409286144,
        "bandwidth_bytes_per_second": 40000000000,
        "service_seconds": 0.0352321536
      },
      {
        "resource": "server1.ingress",
        "bytes": 1409286144,
        "bandwidth_bytes_per_second": 40000000000,
        "service_seconds": 0.0352321536
      },
      {
        "resource": "server1.nic0.rx",
        "bytes": 704643072,
        "bandwidth_bytes_per_second": 25000000000,
        "service_seconds": 0.02818572288
      },
      {
        "resource": "server1.nic0.tx",
        "bytes": 704643072,
        "bandwidth_bytes_per_second": 25000000000,
        "service_seconds": 0.02818572288
      },
      {
        "resource": "server1.nic1.rx",
        "bytes": 704643072,
        "bandwidth_bytes_per_second": 25000000000,
        "service_seconds": 0.02818572288
      },
      {
        "resource": "server1.nic1.tx",
        "bytes": 704643072,
        "bandwidth_bytes_per_second": 25000000000,
        "service_seconds": 0.02818572288
      },
      {
        "resource": "shared_cut.bidirectional",
        "bytes": 2818572288,
        "bandwidth_bytes_per_second": 80000000000,
        "service_seconds": 0.0352321536
      }
    ],
    "rounds": [
      {
        "round": 0,
        "phase": "reduce_scatter",
        "resource_bytes": {
          "rank0.tx": 25165824,
          "server0.nic0.tx": 50331648,
          "server0.egress": 100663296,
          "cut.0->1": 100663296,
          "shared_cut.bidirectional": 201326592,
          "server1.ingress": 100663296,
          "server1.nic0.rx": 50331648,
          "rank4.rx": 25165824,
          "server0.nic1.tx": 50331648,
          "server1.nic1.rx": 50331648,
          "rank4.tx": 25165824,
          "server1.nic0.tx": 50331648,
          "server1.egress": 100663296,
          "cut.1->0": 100663296,
          "server0.ingress": 100663296,
          "server0.nic0.rx": 50331648,
          "rank1.rx": 25165824,
          "server1.nic1.tx": 50331648,
          "server0.nic1.rx": 50331648,
          "rank1.tx": 25165824,
          "rank5.rx": 25165824,
          "rank5.tx": 25165824,
          "rank2.rx": 25165824,
          "rank2.tx": 25165824,
          "rank6.rx": 25165824,
          "rank6.tx": 25165824,
          "rank3.rx": 25165824,
          "rank3.tx": 25165824,
          "rank7.rx": 25165824,
          "rank7.tx": 25165824,
          "rank0.rx": 25165824
        },
        "resource_lower_seconds": 0.0025165824,
        "barrier_lower_with_startup_seconds": 0.0025185824
      },
      {
        "round": 1,
        "phase": "reduce_scatter",
        "resource_bytes": {
          "rank0.tx": 25165824,
          "server0.nic0.tx": 50331648,
          "server0.egress": 100663296,
          "cut.0->1": 100663296,
          "shared_cut.bidirectional": 201326592,
          "server1.ingress": 100663296,
          "server1.nic0.rx": 50331648,
          "rank4.rx": 25165824,
          "server0.nic1.tx": 50331648,
          "server1.nic1.rx": 50331648,
          "rank4.tx": 25165824,
          "server1.nic0.tx": 50331648,
          "server1.egress": 100663296,
          "cut.1->0": 100663296,
          "server0.ingress": 100663296,
          "server0.nic0.rx": 50331648,
          "rank1.rx": 25165824,
          "server1.nic1.tx": 50331648,
          "server0.nic1.rx": 50331648,
          "rank1.tx": 25165824,
          "rank5.rx": 25165824,
          "rank5.tx": 25165824,
          "rank2.rx": 25165824,
          "rank2.tx": 25165824,
          "rank6.rx": 25165824,
          "rank6.tx": 25165824,
          "rank3.rx": 25165824,
          "rank3.tx": 25165824,
          "rank7.rx": 25165824,
          "rank7.tx": 25165824,
          "rank0.rx": 25165824
        },
        "resource_lower_seconds": 0.0025165824,
        "barrier_lower_with_startup_seconds": 0.0025185824
      },
      {
        "round": 2,
        "phase": "reduce_scatter",
        "resource_bytes": {
          "rank0.tx": 25165824,
          "server0.nic0.tx": 50331648,
          "server0.egress": 100663296,
          "cut.0->1": 100663296,
          "shared_cut.bidirectional": 201326592,
          "server1.ingress": 100663296,
          "server1.nic0.rx": 50331648,
          "rank4.rx": 25165824,
          "server0.nic1.tx": 50331648,
          "server1.nic1.rx": 50331648,
          "rank4.tx": 25165824,
          "server1.nic0.tx": 50331648,
          "server1.egress": 100663296,
          "cut.1->0": 100663296,
          "server0.ingress": 100663296,
          "server0.nic0.rx": 50331648,
          "rank1.rx": 25165824,
          "server1.nic1.tx": 50331648,
          "server0.nic1.rx": 50331648,
          "rank1.tx": 25165824,
          "rank5.rx": 25165824,
          "rank5.tx": 25165824,
          "rank2.rx": 25165824,
          "rank2.tx": 25165824,
          "rank6.rx": 25165824,
          "rank6.tx": 25165824,
          "rank3.rx": 25165824,
          "rank3.tx": 25165824,
          "rank7.rx": 25165824,
          "rank7.tx": 25165824,
          "rank0.rx": 25165824
        },
        "resource_lower_seconds": 0.0025165824,
        "barrier_lower_with_startup_seconds": 0.0025185824
      },
      {
        "round": 3,
        "phase": "reduce_scatter",
        "resource_bytes": {
          "rank0.tx": 25165824,
          "server0.nic0.tx": 50331648,
          "server0.egress": 100663296,
          "cut.0->1": 100663296,
          "shared_cut.bidirectional": 201326592,
          "server1.ingress": 100663296,
          "server1.nic0.rx": 50331648,
          "rank4.rx": 25165824,
          "server0.nic1.tx": 50331648,
          "server1.nic1.rx": 50331648,
          "rank4.tx": 25165824,
          "server1.nic0.tx": 50331648,
          "server1.egress": 100663296,
          "cut.1->0": 100663296,
          "server0.ingress": 100663296,
          "server0.nic0.rx": 50331648,
          "rank1.rx": 25165824,
          "server1.nic1.tx": 50331648,
          "server0.nic1.rx": 50331648,
          "rank1.tx": 25165824,
          "rank5.rx": 25165824,
          "rank5.tx": 25165824,
          "rank2.rx": 25165824,
          "rank2.tx": 25165824,
          "rank6.rx": 25165824,
          "rank6.tx": 25165824,
          "rank3.rx": 25165824,
          "rank3.tx": 25165824,
          "rank7.rx": 25165824,
          "rank7.tx": 25165824,
          "rank0.rx": 25165824
        },
        "resource_lower_seconds": 0.0025165824,
        "barrier_lower_with_startup_seconds": 0.0025185824
      },
      {
        "round": 4,
        "phase": "reduce_scatter",
        "resource_bytes": {
          "rank0.tx": 25165824,
          "server0.nic0.tx": 50331648,
          "server0.egress": 100663296,
          "cut.0->1": 100663296,
          "shared_cut.bidirectional": 201326592,
          "server1.ingress": 100663296,
          "server1.nic0.rx": 50331648,
          "rank4.rx": 25165824,
          "server0.nic1.tx": 50331648,
          "server1.nic1.rx": 50331648,
          "rank4.tx": 25165824,
          "server1.nic0.tx": 50331648,
          "server1.egress": 100663296,
          "cut.1->0": 100663296,
          "server0.ingress": 100663296,
          "server0.nic0.rx": 50331648,
          "rank1.rx": 25165824,
          "server1.nic1.tx": 50331648,
          "server0.nic1.rx": 50331648,
          "rank1.tx": 25165824,
          "rank5.rx": 25165824,
          "rank5.tx": 25165824,
          "rank2.rx": 25165824,
          "rank2.tx": 25165824,
          "rank6.rx": 25165824,
          "rank6.tx": 25165824,
          "rank3.rx": 25165824,
          "rank3.tx": 25165824,
          "rank7.rx": 25165824,
          "rank7.tx": 25165824,
          "rank0.rx": 25165824
        },
        "resource_lower_seconds": 0.0025165824,
        "barrier_lower_with_startup_seconds": 0.0025185824
      },
      {
        "round": 5,
        "phase": "reduce_scatter",
        "resource_bytes": {
          "rank0.tx": 25165824,
          "server0.nic0.tx": 50331648,
          "server0.egress": 100663296,
          "cut.0->1": 100663296,
          "shared_cut.bidirectional": 201326592,
          "server1.ingress": 100663296,
          "server1.nic0.rx": 50331648,
          "rank4.rx": 25165824,
          "server0.nic1.tx": 50331648,
          "server1.nic1.rx": 50331648,
          "rank4.tx": 25165824,
          "server1.nic0.tx": 50331648,
          "server1.egress": 100663296,
          "cut.1->0": 100663296,
          "server0.ingress": 100663296,
          "server0.nic0.rx": 50331648,
          "rank1.rx": 25165824,
          "server1.nic1.tx": 50331648,
          "server0.nic1.rx": 50331648,
          "rank1.tx": 25165824,
          "rank5.rx": 25165824,
          "rank5.tx": 25165824,
          "rank2.rx": 25165824,
          "rank2.tx": 25165824,
          "rank6.rx": 25165824,
          "rank6.tx": 25165824,
          "rank3.rx": 25165824,
          "rank3.tx": 25165824,
          "rank7.rx": 25165824,
          "rank7.tx": 25165824,
          "rank0.rx": 25165824
        },
        "resource_lower_seconds": 0.0025165824,
        "barrier_lower_with_startup_seconds": 0.0025185824
      },
      {
        "round": 6,
        "phase": "reduce_scatter",
        "resource_bytes": {
          "rank0.tx": 25165824,
          "server0.nic0.tx": 50331648,
          "server0.egress": 100663296,
          "cut.0->1": 100663296,
          "shared_cut.bidirectional": 201326592,
          "server1.ingress": 100663296,
          "server1.nic0.rx": 50331648,
          "rank4.rx": 25165824,
          "server0.nic1.tx": 50331648,
          "server1.nic1.rx": 50331648,
          "rank4.tx": 25165824,
          "server1.nic0.tx": 50331648,
          "server1.egress": 100663296,
          "cut.1->0": 100663296,
          "server0.ingress": 100663296,
          "server0.nic0.rx": 50331648,
          "rank1.rx": 25165824,
          "server1.nic1.tx": 50331648,
          "server0.nic1.rx": 50331648,
          "rank1.tx": 25165824,
          "rank5.rx": 25165824,
          "rank5.tx": 25165824,
          "rank2.rx": 25165824,
          "rank2.tx": 25165824,
          "rank6.rx": 25165824,
          "rank6.tx": 25165824,
          "rank3.rx": 25165824,
          "rank3.tx": 25165824,
          "rank7.rx": 25165824,
          "rank7.tx": 25165824,
          "rank0.rx": 25165824
        },
        "resource_lower_seconds": 0.0025165824,
        "barrier_lower_with_startup_seconds": 0.0025185824
      },
      {
        "round": 7,
        "phase": "all_gather",
        "resource_bytes": {
          "rank0.tx": 25165824,
          "server0.nic0.tx": 50331648,
          "server0.egress": 100663296,
          "cut.0->1": 100663296,
          "shared_cut.bidirectional": 201326592,
          "server1.ingress": 100663296,
          "server1.nic0.rx": 50331648,
          "rank4.rx": 25165824,
          "server0.nic1.tx": 50331648,
          "server1.nic1.rx": 50331648,
          "rank4.tx": 25165824,
          "server1.nic0.tx": 50331648,
          "server1.egress": 100663296,
          "cut.1->0": 100663296,
          "server0.ingress": 100663296,
          "server0.nic0.rx": 50331648,
          "rank1.rx": 25165824,
          "server1.nic1.tx": 50331648,
          "server0.nic1.rx": 50331648,
          "rank1.tx": 25165824,
          "rank5.rx": 25165824,
          "rank5.tx": 25165824,
          "rank2.rx": 25165824,
          "rank2.tx": 25165824,
          "rank6.rx": 25165824,
          "rank6.tx": 25165824,
          "rank3.rx": 25165824,
          "rank3.tx": 25165824,
          "rank7.rx": 25165824,
          "rank7.tx": 25165824,
          "rank0.rx": 25165824
        },
        "resource_lower_seconds": 0.0025165824,
        "barrier_lower_with_startup_seconds": 0.0025185824
      },
      {
        "round": 8,
        "phase": "all_gather",
        "resource_bytes": {
          "rank0.tx": 25165824,
          "server0.nic0.tx": 50331648,
          "server0.egress": 100663296,
          "cut.0->1": 100663296,
          "shared_cut.bidirectional": 201326592,
          "server1.ingress": 100663296,
          "server1.nic0.rx": 50331648,
          "rank4.rx": 25165824,
          "server0.nic1.tx": 50331648,
          "server1.nic1.rx": 50331648,
          "rank4.tx": 25165824,
          "server1.nic0.tx": 50331648,
          "server1.egress": 100663296,
          "cut.1->0": 100663296,
          "server0.ingress": 100663296,
          "server0.nic0.rx": 50331648,
          "rank1.rx": 25165824,
          "server1.nic1.tx": 50331648,
          "server0.nic1.rx": 50331648,
          "rank1.tx": 25165824,
          "rank5.rx": 25165824,
          "rank5.tx": 25165824,
          "rank2.rx": 25165824,
          "rank2.tx": 25165824,
          "rank6.rx": 25165824,
          "rank6.tx": 25165824,
          "rank3.rx": 25165824,
          "rank3.tx": 25165824,
          "rank7.rx": 25165824,
          "rank7.tx": 25165824,
          "rank0.rx": 25165824
        },
        "resource_lower_seconds": 0.0025165824,
        "barrier_lower_with_startup_seconds": 0.0025185824
      },
      {
        "round": 9,
        "phase": "all_gather",
        "resource_bytes": {
          "rank0.tx": 25165824,
          "server0.nic0.tx": 50331648,
          "server0.egress": 100663296,
          "cut.0->1": 100663296,
          "shared_cut.bidirectional": 201326592,
          "server1.ingress": 100663296,
          "server1.nic0.rx": 50331648,
          "rank4.rx": 25165824,
          "server0.nic1.tx": 50331648,
          "server1.nic1.rx": 50331648,
          "rank4.tx": 25165824,
          "server1.nic0.tx": 50331648,
          "server1.egress": 100663296,
          "cut.1->0": 100663296,
          "server0.ingress": 100663296,
          "server0.nic0.rx": 50331648,
          "rank1.rx": 25165824,
          "server1.nic1.tx": 50331648,
          "server0.nic1.rx": 50331648,
          "rank1.tx": 25165824,
          "rank5.rx": 25165824,
          "rank5.tx": 25165824,
          "rank2.rx": 25165824,
          "rank2.tx": 25165824,
          "rank6.rx": 25165824,
          "rank6.tx": 25165824,
          "rank3.rx": 25165824,
          "rank3.tx": 25165824,
          "rank7.rx": 25165824,
          "rank7.tx": 25165824,
          "rank0.rx": 25165824
        },
        "resource_lower_seconds": 0.0025165824,
        "barrier_lower_with_startup_seconds": 0.0025185824
      },
      {
        "round": 10,
        "phase": "all_gather",
        "resource_bytes": {
          "rank0.tx": 25165824,
          "server0.nic0.tx": 50331648,
          "server0.egress": 100663296,
          "cut.0->1": 100663296,
          "shared_cut.bidirectional": 201326592,
          "server1.ingress": 100663296,
          "server1.nic0.rx": 50331648,
          "rank4.rx": 25165824,
          "server0.nic1.tx": 50331648,
          "server1.nic1.rx": 50331648,
          "rank4.tx": 25165824,
          "server1.nic0.tx": 50331648,
          "server1.egress": 100663296,
          "cut.1->0": 100663296,
          "server0.ingress": 100663296,
          "server0.nic0.rx": 50331648,
          "rank1.rx": 25165824,
          "server1.nic1.tx": 50331648,
          "server0.nic1.rx": 50331648,
          "rank1.tx": 25165824,
          "rank5.rx": 25165824,
          "rank5.tx": 25165824,
          "rank2.rx": 25165824,
          "rank2.tx": 25165824,
          "rank6.rx": 25165824,
          "rank6.tx": 25165824,
          "rank3.rx": 25165824,
          "rank3.tx": 25165824,
          "rank7.rx": 25165824,
          "rank7.tx": 25165824,
          "rank0.rx": 25165824
        },
        "resource_lower_seconds": 0.0025165824,
        "barrier_lower_with_startup_seconds": 0.0025185824
      },
      {
        "round": 11,
        "phase": "all_gather",
        "resource_bytes": {
          "rank0.tx": 25165824,
          "server0.nic0.tx": 50331648,
          "server0.egress": 100663296,
          "cut.0->1": 100663296,
          "shared_cut.bidirectional": 201326592,
          "server1.ingress": 100663296,
          "server1.nic0.rx": 50331648,
          "rank4.rx": 25165824,
          "server0.nic1.tx": 50331648,
          "server1.nic1.rx": 50331648,
          "rank4.tx": 25165824,
          "server1.nic0.tx": 50331648,
          "server1.egress": 100663296,
          "cut.1->0": 100663296,
          "server0.ingress": 100663296,
          "server0.nic0.rx": 50331648,
          "rank1.rx": 25165824,
          "server1.nic1.tx": 50331648,
          "server0.nic1.rx": 50331648,
          "rank1.tx": 25165824,
          "rank5.rx": 25165824,
          "rank5.tx": 25165824,
          "rank2.rx": 25165824,
          "rank2.tx": 25165824,
          "rank6.rx": 25165824,
          "rank6.tx": 25165824,
          "rank3.rx": 25165824,
          "rank3.tx": 25165824,
          "rank7.rx": 25165824,
          "rank7.tx": 25165824,
          "rank0.rx": 25165824
        },
        "resource_lower_seconds": 0.0025165824,
        "barrier_lower_with_startup_seconds": 0.0025185824
      },
      {
        "round": 12,
        "phase": "all_gather",
        "resource_bytes": {
          "rank0.tx": 25165824,
          "server0.nic0.tx": 50331648,
          "server0.egress": 100663296,
          "cut.0->1": 100663296,
          "shared_cut.bidirectional": 201326592,
          "server1.ingress": 100663296,
          "server1.nic0.rx": 50331648,
          "rank4.rx": 25165824,
          "server0.nic1.tx": 50331648,
          "server1.nic1.rx": 50331648,
          "rank4.tx": 25165824,
          "server1.nic0.tx": 50331648,
          "server1.egress": 100663296,
          "cut.1->0": 100663296,
          "server0.ingress": 100663296,
          "server0.nic0.rx": 50331648,
          "rank1.rx": 25165824,
          "server1.nic1.tx": 50331648,
          "server0.nic1.rx": 50331648,
          "rank1.tx": 25165824,
          "rank5.rx": 25165824,
          "rank5.tx": 25165824,
          "rank2.rx": 25165824,
          "rank2.tx": 25165824,
          "rank6.rx": 25165824,
          "rank6.tx": 25165824,
          "rank3.rx": 25165824,
          "rank3.tx": 25165824,
          "rank7.rx": 25165824,
          "rank7.tx": 25165824,
          "rank0.rx": 25165824
        },
        "resource_lower_seconds": 0.0025165824,
        "barrier_lower_with_startup_seconds": 0.0025185824
      },
      {
        "round": 13,
        "phase": "all_gather",
        "resource_bytes": {
          "rank0.tx": 25165824,
          "server0.nic0.tx": 50331648,
          "server0.egress": 100663296,
          "cut.0->1": 100663296,
          "shared_cut.bidirectional": 201326592,
          "server1.ingress": 100663296,
          "server1.nic0.rx": 50331648,
          "rank4.rx": 25165824,
          "server0.nic1.tx": 50331648,
          "server1.nic1.rx": 50331648,
          "rank4.tx": 25165824,
          "server1.nic0.tx": 50331648,
          "server1.egress": 100663296,
          "cut.1->0": 100663296,
          "server0.ingress": 100663296,
          "server0.nic0.rx": 50331648,
          "rank1.rx": 25165824,
          "server1.nic1.tx": 50331648,
          "server0.nic1.rx": 50331648,
          "rank1.tx": 25165824,
          "rank5.rx": 25165824,
          "rank5.tx": 25165824,
          "rank2.rx": 25165824,
          "rank2.tx": 25165824,
          "rank6.rx": 25165824,
          "rank6.tx": 25165824,
          "rank3.rx": 25165824,
          "rank3.tx": 25165824,
          "rank7.rx": 25165824,
          "rank7.tx": 25165824,
          "rank0.rx": 25165824
        },
        "resource_lower_seconds": 0.0025165824,
        "barrier_lower_with_startup_seconds": 0.0025185824
      }
    ],
    "aggregate_resource_lower_seconds": 0.0352321536,
    "sum_round_resource_lower_seconds": 0.035232153599999996,
    "barrier_lower_with_startup_seconds": 0.0352601536
  },
  "summary": {
    "network_send_bytes": 2818572288,
    "local_send_bytes": 0,
    "remote_send_bytes": 2818572288,
    "reduction_scalar_adds": 352321536,
    "final_gradient_bytes_per_rank": [
      201326592,
      201326592,
      201326592,
      201326592,
      201326592,
      201326592,
      201326592,
      201326592
    ],
    "rounds": 14,
    "aggregate_resource_lower_seconds_exact": "344064/9765625",
    "largest_aggregate_resources": [
      "cut.0->1",
      "cut.1->0",
      "server0.egress",
      "server0.ingress",
      "server1.egress",
      "server1.ingress",
      "shared_cut.bidirectional"
    ],
    "serial_barrier_lower_seconds_exact": "5509399/156250000",
    "necessary_budget_not_excluded": true,
    "actual_training_deadline_feasible": null,
    "measured_seconds": null
  },
  "assumptions": [
    "One real first-layer gate parameter gradient per rank; each rank contributes different sample data to the same coordinates. Not activations, whole-model gradients, or framework buckets.",
    "FP32/BF16 are declared gradient wire/operand widths. Rank contribution identities prove algebraic sum coverage, not floating-point reassociation equivalence or backend accumulation precision.",
    "Two servers each own four fixed ranks. Hierarchy executes local RS, corresponding-owner two-rank AR, local AG with stage/round barriers; no overlapping stages or unmodeled algorithm substitutions.",
    "Remote messages stripe disjoint whole-element intervals over one/two NICs, never duplicate payload. Each source/destination NIC, shared egress/ingress and shared bidirectional cut has its own declared rate; shared40GB/s server edges do not grow with NIC count.",
    "All rates and startup are teaching inputs. Each round bound is max(resource bytes/rate)+startup; serialized barrier bounds omit reduction work, propagation, buffering, topology latency and interference. They are not executable timing or deadline guarantees.",
    "Logical network sends count payload once. Endpoint receive, NIC, ingress and cut counters represent distinct resource demands; their sum is not additional gradient payload or HBM traffic.",
    "No padding is introduced. Missing paths/resources or invalid rates reject. Budget pass only means this communication lower bound has not excluded the candidate; real training feasibility remains unknown."
  ]
}
```
