# Sealed Chat trace to Qwen8 resources

Actual recorded lengths; explicitly conditional model-step mapping.

```json
{
  "schema": "trace-resource-bridge-v1",
  "scenario": {
    "generation_policy": "unknown_steps"
  },
  "trace_sources": [
    {
      "file": "sources/chat/capture.jsonl",
      "origin": "experiments/ch02/02-08/sources/chat/capture.jsonl",
      "sha256": "d7bdd31d5f48144e9fb69a0dcdc318badb63ffc585b85d75da06c4878d1a0a5d",
      "bytes": 14337,
      "copied_at": "2026-09-09T00:47:35.822203+00:00"
    },
    {
      "file": "sources/chat/requests.jsonl",
      "origin": "experiments/ch02/02-08/sources/chat/requests.jsonl",
      "sha256": "0a461aa67a00a2fbd5ddd9427b1a64b4708a3ab5ce22ce4a324188f3a6698dde",
      "bytes": 18359,
      "copied_at": "2026-09-09T00:47:35.822203+00:00"
    },
    {
      "file": "sources/chat/prompts.json",
      "origin": "experiments/ch02/02-08/sources/chat/prompts.json",
      "sha256": "14879849525db78f61756638fc8de6e5695a9c7b6cd27c4fce0429368e820d5d",
      "bytes": 16509,
      "copied_at": "2026-09-09T00:47:35.822203+00:00"
    },
    {
      "file": "sources/chat/execution.json",
      "origin": "experiments/ch02/02-08/sources/chat/execution.json",
      "sha256": "f442be80190335da25adb63c90202c875118b43e9df64483435e361ca9fcf465",
      "bytes": 5962,
      "copied_at": "2026-09-09T00:47:35.822203+00:00"
    },
    {
      "file": "sources/chat/worker0-requests/ubuntu_0.log",
      "origin": "experiments/ch02/02-08/sources/chat/worker0-requests/ubuntu_0.log",
      "sha256": "234e15cd7fe5d59c5223b16e37aa132b0ca3866514f828c8655658e4d7c9e118",
      "bytes": 78523,
      "copied_at": "2026-09-09T00:47:35.822203+00:00"
    },
    {
      "file": "sources/chat/worker1-requests/ubuntu_0.log",
      "origin": "experiments/ch02/02-08/sources/chat/worker1-requests/ubuntu_0.log",
      "sha256": "ed2da4c34b78ec8b2d133d3d2f877e8403eaa2e188d917d32846dcf3c94788f2",
      "bytes": 65533,
      "copied_at": "2026-09-09T00:47:35.822203+00:00"
    },
    {
      "file": "sources/chat/run.py",
      "origin": "experiments/ch02/02-08/sources/chat/run.py",
      "sha256": "5aa95974984f02f93fca817f5f7537c6a943d85231dc3358cf1f230f08491d9d",
      "bytes": 5912,
      "copied_at": "2026-09-09T00:47:35.822203+00:00"
    },
    {
      "file": "sources/tokenizer_config.json",
      "origin": "experiments/ch02/02-08/sources/tokenizer_config.json",
      "sha256": "d5d09f07b48c3086c508b30d1c9114bd1189145b74e982a265350c923acd8101",
      "bytes": 9732,
      "copied_at": "2026-09-09T00:47:35.822203+00:00"
    },
    {
      "file": "summary.json",
      "origin": "experiments/ch02/02-08/summary.json",
      "sha256": "43ada8e6e7b59088afc9f54fc353a1f0677975b000a714e9cb282ad0b037cd30",
      "bytes": 35269,
      "scope": "existing derived/identity evidence, not new model execution"
    },
    {
      "file": "analyze.py",
      "origin": "experiments/ch02/02-08/analyze.py",
      "sha256": "7bbd65c5635bcd1783860d574dceae23f16117e8dbfe65bb3cf859f8e72db961",
      "bytes": 6711,
      "scope": "existing derived/identity evidence, not new model execution"
    },
    {
      "file": "source-index.json",
      "origin": "experiments/ch02/02-08/source-index.json",
      "sha256": "fa89a24405fccb0072a9874a8b3959e09e2060a5dfffe015bc28625cb51ff1cd",
      "bytes": 4578,
      "scope": "existing derived/identity evidence, not new model execution"
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
  "calls": [
    {
      "request": 0,
      "application_request_id": "book909chat-capture-0",
      "recorded": {
        "input_tokens": 116,
        "cached_tokens": 0,
        "returned_id_tokens": 29,
        "engine_completion_tokens": 29,
        "output_parts": {
          "reasoning": 0,
          "nonreasoning": 28,
          "delimiter": 0,
          "termination": 1,
          "unknown": 0
        },
        "finish_reason": {
          "type": "stop",
          "matched": 151645
        },
        "worker": "worker0-requests",
        "application_wall_seconds": 0.30805450887419283,
        "engine_e2e_seconds": 0.3061568280681968,
        "tool_wait_seconds": null,
        "previous_same_worker_completion_gap_seconds": null
      },
      "mapping": {
        "prefix_tokens": 0,
        "new_tokens": 116,
        "batch": 1,
        "output_head": "last",
        "sampled_steps": null,
        "decode_forward_calls": null,
        "observed_model_forward_calls": null
      },
      "resources": {
        "prefill": {
          "logical_forward_calls": 1,
          "totals": {
            "matrix_flops": 1616665247744,
            "accounted_scalar_flops": 559195284,
            "special_ops": {
              "sin": 14848,
              "cos": 14848,
              "rsqrt": 175508,
              "negate": 62005248,
              "exp": 59132160,
              "compare_max": 7683840,
              "mask_decisions": 15501312
            },
            "known_interfaces": {
              "weight_read_once_per_operator_bytes": 15137761280,
              "activation_operand_read_bytes": 999458880,
              "activation_operand_write_bytes": 827575040,
              "kv_existing_history_unique_payload_bytes": 0,
              "kv_new_write_bytes": 17104896
            }
          },
          "source_ledger": {
            "schema_version": 1,
            "calculation": "qwen3-dense-forward",
            "model": "qwen3-8b",
            "scenario": {
              "batch": 1,
              "history": 0,
              "tokens": 116,
              "output_head": "last",
              "weight_bytes": 2,
              "activation_bytes": 2,
              "kv_bytes": 2,
              "score_bytes": 4
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
            "dimensions": {
              "num_hidden_layers": 36,
              "hidden_size": 4096,
              "intermediate_size": 12288,
              "num_attention_heads": 32,
              "num_key_value_heads": 8,
              "head_dim": 128,
              "vocab_size": 151936,
              "tie_word_embeddings": false
            },
            "assumptions": [
              "\u6240\u6709\u8bf7\u6c42\u7b49\u957f\u3001\u76f8\u540c\u4f4d\u7f6e ID\u3001\u65e0\u8de8\u8bf7\u6c42\u524d\u7f00\u5171\u4eab\uff0c\u65e0 TP/PP\uff1bdropout=0 \u63a8\u7406\u3002",
              "\u5168\u6a21\u578b\u6743\u91cd\u7edf\u4e00 weight_bytes \u7684\u6559\u5b66\u683c\u5f0f\uff1b\u4e0d\u7531 torch_dtype \u63a8\u65ad\u5b9e\u9645\u91cf\u5316\u683c\u5f0f\u3002",
              "\u6bcf\u884c operator \u6210\u672c\u4e3a\u4e00\u6b21\u51fa\u73b0\uff0crepeats \u662f\u5c42\u6570\uff1b\u5e03\u5c40\u89c6\u56fe\u4e0e GQA repeat \u4e0d\u989d\u5916\u7269\u5316\u3002",
              "FMA=2\uff1bmatrix_flops \u662f\u6709\u6548\u56e0\u679c\u77e9\u9635\u5de5\u4f5c\uff0cscalar_flops \u662f\u58f0\u660e\u7b97\u6cd5\u7684\u666e\u901a\u7b97\u672f\uff1b\u7279\u6b8a\u51fd\u6570\u53e6\u5217\u3002",
              "operator \u8bfb\u5199\u662f\u72ec\u7acb\u7b97\u5b50\u64cd\u4f5c\u6570\u8f7d\u8377\uff0c\u5206\u6570\uff0f\u6982\u7387\u77e9\u5f62\u7269\u5316\uff1b\u4e0d\u662f\u5b9e\u6d4b HBM\u3001\u4e0d\u662f\u5168\u56fe\u6d41\u91cf\u4e0b\u754c\u3002",
              "\u6807\u91cf\u884c\u5185\u4e2d\u95f4\u91cf\u89c6\u4e3a\u7247\u4e0a\uff1b\u77e9\u5f62\u6ce8\u610f\u529b\u540c\u65f6\u62a5\u544a\uff0cFlashAttention/tile/\u7f13\u5b58\u6d41\u91cf\u7531\u6267\u884c\u4e13\u9898\u53e6\u7b97\u3002",
              "\u4e0d\u8ba1\u91c7\u6837\u3001tokenizer\u3001kernel launch\u3001\u5206\u914d\u5668\u3001KV \u7ba1\u7406\u7d22\u5f15\u53ca\u540e\u7aef\u5de5\u4f5c\u533a\uff1b\u4e0d\u636e\u6b64\u58f0\u79f0\u5b8c\u6574 token \u65f6\u95f4\u3002"
            ],
            "weights": [
              {
                "name": "model.embed_tokens.weight",
                "shape": [
                  151936,
                  4096
                ],
                "copies": 1,
                "note": "",
                "parameters": 622329856,
                "resident_bytes": 1244659712
              },
              {
                "name": "model.layers.{layer}.self_attn.q_proj.weight",
                "shape": [
                  4096,
                  4096
                ],
                "copies": 36,
                "note": "",
                "parameters": 603979776,
                "resident_bytes": 1207959552
              },
              {
                "name": "model.layers.{layer}.self_attn.k_proj.weight",
                "shape": [
                  1024,
                  4096
                ],
                "copies": 36,
                "note": "",
                "parameters": 150994944,
                "resident_bytes": 301989888
              },
              {
                "name": "model.layers.{layer}.self_attn.v_proj.weight",
                "shape": [
                  1024,
                  4096
                ],
                "copies": 36,
                "note": "",
                "parameters": 150994944,
                "resident_bytes": 301989888
              },
              {
                "name": "model.layers.{layer}.self_attn.o_proj.weight",
                "shape": [
                  4096,
                  4096
                ],
                "copies": 36,
                "note": "",
                "parameters": 603979776,
                "resident_bytes": 1207959552
              },
              {
                "name": "model.layers.{layer}.self_attn.q_norm.weight",
                "shape": [
                  128
                ],
                "copies": 36,
                "note": "",
                "parameters": 4608,
                "resident_bytes": 9216
              },
              {
                "name": "model.layers.{layer}.self_attn.k_norm.weight",
                "shape": [
                  128
                ],
                "copies": 36,
                "note": "",
                "parameters": 4608,
                "resident_bytes": 9216
              },
              {
                "name": "model.layers.{layer}.input_layernorm.weight",
                "shape": [
                  4096
                ],
                "copies": 36,
                "note": "",
                "parameters": 147456,
                "resident_bytes": 294912
              },
              {
                "name": "model.layers.{layer}.post_attention_layernorm.weight",
                "shape": [
                  4096
                ],
                "copies": 36,
                "note": "",
                "parameters": 147456,
                "resident_bytes": 294912
              },
              {
                "name": "model.norm.weight",
                "shape": [
                  4096
                ],
                "copies": 1,
                "note": "",
                "parameters": 4096,
                "resident_bytes": 8192
              },
              {
                "name": "lm_head.weight",
                "shape": [
                  151936,
                  4096
                ],
                "copies": 1,
                "note": "",
                "parameters": 622329856,
                "resident_bytes": 1244659712
              },
              {
                "name": "model.layers.{layer}.mlp.gate_proj.weight",
                "shape": [
                  12288,
                  4096
                ],
                "copies": 36,
                "note": "",
                "parameters": 1811939328,
                "resident_bytes": 3623878656
              },
              {
                "name": "model.layers.{layer}.mlp.up_proj.weight",
                "shape": [
                  12288,
                  4096
                ],
                "copies": 36,
                "note": "",
                "parameters": 1811939328,
                "resident_bytes": 3623878656
              },
              {
                "name": "model.layers.{layer}.mlp.down_proj.weight",
                "shape": [
                  4096,
                  12288
                ],
                "copies": 36,
                "note": "",
                "parameters": 1811939328,
                "resident_bytes": 3623878656
              }
            ],
            "operators": [
              {
                "name": "embedding",
                "category": "embedding",
                "shapes": {
                  "indices": [
                    1,
                    116
                  ],
                  "table": [
                    151936,
                    4096
                  ],
                  "output": [
                    116,
                    4096
                  ]
                },
                "repeats": 1,
                "matrix_flops": 0,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 950272,
                "activation_read_bytes": 928,
                "activation_write_bytes": 950272,
                "notes": "\u6bcf token \u4e00\u6b21\u884c\u67e5\u627e\uff0c\u4e0d\u8bfb\u53d6\u6574\u4e2a\u8bcd\u8868\uff1b\u91cd\u590d token \u662f\u5426\u7f13\u5b58\u672a\u5047\u5b9a\u3002int64 \u8f93\u5165\u7d22\u5f15\u3002"
              },
              {
                "name": "rope_table",
                "category": "position",
                "shapes": {
                  "frequencies": [
                    116,
                    64
                  ],
                  "cos_sin_each": [
                    116,
                    128
                  ]
                },
                "repeats": 1,
                "matrix_flops": 0,
                "scalar_flops": 7424,
                "special_ops": {
                  "sin": 14848,
                  "cos": 14848
                },
                "weight_read_bytes": 0,
                "activation_read_bytes": 1184,
                "activation_write_bytes": 59392,
                "notes": "\u540c\u4f4d\u7f6e ID \u6279\u5171\u4eab\uff0c\u6240\u6709\u5c42\u590d\u7528\uff1binv_freq \u56fa\u5b9a\u4e0d\u8ba1\u521d\u59cb\u5316\u3002\u53c2\u8003\u8def\u5f84\u590d\u5236\u9891\u7387\u540e\u6c42 sin/cos\uff1b\u8f6c\u6362\u53e6\u8ba1\u3002"
              },
              {
                "name": "input_layernorm",
                "category": "normalization",
                "shapes": {
                  "input": [
                    116,
                    4096
                  ],
                  "weight": [
                    4096
                  ],
                  "output": [
                    116,
                    4096
                  ]
                },
                "repeats": 36,
                "matrix_flops": 0,
                "scalar_flops": 1900660,
                "special_ops": {
                  "rsqrt": 116
                },
                "weight_read_bytes": 8192,
                "activation_read_bytes": 950272,
                "activation_write_bytes": 950272,
                "notes": "\u6309 FP32 \u884c\u5185\u5f52\u7ea6\u7684\u4ee3\u6570\u8ba1\u6570\uff1brsqrt\u3001\u7c7b\u578b\u8f6c\u6362\u4e0e\u4e34\u65f6 FP32 \u5f20\u91cf\u5206\u5217\uff0f\u4e0d\u63a8\u65ad HBM spill\u3002"
              },
              {
                "name": "q_proj",
                "category": "linear",
                "shapes": {
                  "input": [
                    116,
                    4096
                  ],
                  "weight_math": [
                    4096,
                    4096
                  ],
                  "weight_storage": [
                    4096,
                    4096
                  ],
                  "output": [
                    116,
                    4096
                  ]
                },
                "repeats": 36,
                "matrix_flops": 3892314112,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 33554432,
                "activation_read_bytes": 950272,
                "activation_write_bytes": 950272,
                "notes": "\u72ec\u7acb GEMM\uff1a\u6743\u91cd\u4e0e\u8f93\u5165\u5404\u8bfb\u4e00\u6b21\u3001\u8f93\u51fa\u5199\u4e00\u6b21\u7684\u64cd\u4f5c\u6570\u8f7d\u8377\uff1b\u4e0d\u9884\u6d4b tile \u91cd\u8bfb\u3002"
              },
              {
                "name": "k_proj",
                "category": "linear",
                "shapes": {
                  "input": [
                    116,
                    4096
                  ],
                  "weight_math": [
                    4096,
                    1024
                  ],
                  "weight_storage": [
                    1024,
                    4096
                  ],
                  "output": [
                    116,
                    1024
                  ]
                },
                "repeats": 36,
                "matrix_flops": 973078528,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 8388608,
                "activation_read_bytes": 950272,
                "activation_write_bytes": 237568,
                "notes": "\u72ec\u7acb GEMM\uff1a\u6743\u91cd\u4e0e\u8f93\u5165\u5404\u8bfb\u4e00\u6b21\u3001\u8f93\u51fa\u5199\u4e00\u6b21\u7684\u64cd\u4f5c\u6570\u8f7d\u8377\uff1b\u4e0d\u9884\u6d4b tile \u91cd\u8bfb\u3002"
              },
              {
                "name": "v_proj",
                "category": "linear",
                "shapes": {
                  "input": [
                    116,
                    4096
                  ],
                  "weight_math": [
                    4096,
                    1024
                  ],
                  "weight_storage": [
                    1024,
                    4096
                  ],
                  "output": [
                    116,
                    1024
                  ]
                },
                "repeats": 36,
                "matrix_flops": 973078528,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 8388608,
                "activation_read_bytes": 950272,
                "activation_write_bytes": 237568,
                "notes": "\u72ec\u7acb GEMM\uff1a\u6743\u91cd\u4e0e\u8f93\u5165\u5404\u8bfb\u4e00\u6b21\u3001\u8f93\u51fa\u5199\u4e00\u6b21\u7684\u64cd\u4f5c\u6570\u8f7d\u8377\uff1b\u4e0d\u9884\u6d4b tile \u91cd\u8bfb\u3002"
              },
              {
                "name": "q_norm",
                "category": "normalization",
                "shapes": {
                  "input": [
                    3712,
                    128
                  ],
                  "weight": [
                    128
                  ],
                  "output": [
                    3712,
                    128
                  ]
                },
                "repeats": 36,
                "matrix_flops": 0,
                "scalar_flops": 1904256,
                "special_ops": {
                  "rsqrt": 3712
                },
                "weight_read_bytes": 256,
                "activation_read_bytes": 950272,
                "activation_write_bytes": 950272,
                "notes": "\u6309 FP32 \u884c\u5185\u5f52\u7ea6\u7684\u4ee3\u6570\u8ba1\u6570\uff1brsqrt\u3001\u7c7b\u578b\u8f6c\u6362\u4e0e\u4e34\u65f6 FP32 \u5f20\u91cf\u5206\u5217\uff0f\u4e0d\u63a8\u65ad HBM spill\u3002"
              },
              {
                "name": "k_norm",
                "category": "normalization",
                "shapes": {
                  "input": [
                    928,
                    128
                  ],
                  "weight": [
                    128
                  ],
                  "output": [
                    928,
                    128
                  ]
                },
                "repeats": 36,
                "matrix_flops": 0,
                "scalar_flops": 476064,
                "special_ops": {
                  "rsqrt": 928
                },
                "weight_read_bytes": 256,
                "activation_read_bytes": 237568,
                "activation_write_bytes": 237568,
                "notes": "\u6309 FP32 \u884c\u5185\u5f52\u7ea6\u7684\u4ee3\u6570\u8ba1\u6570\uff1brsqrt\u3001\u7c7b\u578b\u8f6c\u6362\u4e0e\u4e34\u65f6 FP32 \u5f20\u91cf\u5206\u5217\uff0f\u4e0d\u63a8\u65ad HBM spill\u3002"
              },
              {
                "name": "apply_rope",
                "category": "position",
                "shapes": {
                  "Q": [
                    1,
                    32,
                    116,
                    128
                  ],
                  "K": [
                    1,
                    8,
                    116,
                    128
                  ]
                },
                "repeats": 36,
                "matrix_flops": 0,
                "scalar_flops": 1781760,
                "special_ops": {
                  "negate": 296960
                },
                "weight_read_bytes": 0,
                "activation_read_bytes": 1247232,
                "activation_write_bytes": 1187840,
                "notes": "2 multiply + 1 add/\u5143\u7d20\uff0crotate_half \u7b26\u53f7\u7ffb\u8f6c\u5206\u5217\uff1b\u8868\u6309\u6279\uff0f\u5934\u7406\u60f3\u590d\u7528\u3002"
              },
              {
                "name": "kv_append",
                "category": "state",
                "shapes": {
                  "new_K_and_V_each": [
                    1,
                    8,
                    116,
                    128
                  ]
                },
                "repeats": 36,
                "matrix_flops": 0,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 0,
                "activation_read_bytes": 475136,
                "activation_write_bytes": 475136,
                "notes": "\u539f\u4f4d\uff0f\u5206\u9875 append \u8f7d\u8377\uff1b\u4e0d\u5047\u5b9a\u52a8\u6001 torch.cat \u5bf9\u65e7\u7f13\u5b58\u6574\u6bb5\u590d\u5236\u3002"
              },
              {
                "name": "qk",
                "category": "attention",
                "shapes": {
                  "Q": [
                    1,
                    32,
                    116,
                    128
                  ],
                  "K_shared": [
                    1,
                    8,
                    116,
                    128
                  ],
                  "scores_rectangular": [
                    1,
                    32,
                    116,
                    116
                  ]
                },
                "repeats": 36,
                "matrix_flops": 55590912,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 0,
                "activation_read_bytes": 1187840,
                "activation_write_bytes": 1722368,
                "notes": "FLOPs \u4ec5\u6709\u6548\u56e0\u679c\u4f4d\u7f6e\uff1b\u8f7d\u8377\u662f\u5047\u5b9a Q/K \u5404\u8bfb\u4e00\u6b21\u3001GQA \u5934\u5171\u4eab\uff0c\u5b8c\u6574\u5206\u6570\u77e9\u9635\u7269\u5316\u3002"
              },
              {
                "name": "score_scale_mask_softmax",
                "category": "softmax",
                "shapes": {
                  "scores": [
                    1,
                    32,
                    116,
                    116
                  ]
                },
                "repeats": 36,
                "matrix_flops": 0,
                "scalar_flops": 864896,
                "special_ops": {
                  "exp": 217152,
                  "compare_max": 213440,
                  "mask_decisions": 430592
                },
                "weight_read_bytes": 0,
                "activation_read_bytes": 1722368,
                "activation_write_bytes": 1722368,
                "notes": "\u9009\u62e9\u7684\u878d\u5408 scale/mask/softmax \u4ee3\u6570\u5de5\u4f5c\uff1b\u5c4f\u853d\u70b9\u4e0d\u8ba1 exp\u3002\u7269\u5316 FP32 \u9ed8\u8ba4\u6982\u7387\uff1b\u975e\u5177\u4f53 eager trace\u3002"
              },
              {
                "name": "pv",
                "category": "attention",
                "shapes": {
                  "P": [
                    1,
                    32,
                    116,
                    116
                  ],
                  "V_shared": [
                    1,
                    8,
                    116,
                    128
                  ],
                  "output": [
                    1,
                    32,
                    116,
                    128
                  ]
                },
                "repeats": 36,
                "matrix_flops": 55590912,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 0,
                "activation_read_bytes": 1959936,
                "activation_write_bytes": 950272,
                "notes": "PV/AV\uff1a\u5404 Q \u5934\u4ecd\u8ba1\u7b97\uff1bV \u5bb9\u91cf\u4e0d\u4e58 GQA \u590d\u5236\u6570\u3002\u8f7d\u8377\u5047\u5b9a V \u5728\u5934\uff0f\u67e5\u8be2\u4e4b\u95f4\u7406\u60f3\u590d\u7528\u3002"
              },
              {
                "name": "o_proj",
                "category": "linear",
                "shapes": {
                  "input": [
                    116,
                    4096
                  ],
                  "weight_math": [
                    4096,
                    4096
                  ],
                  "weight_storage": [
                    4096,
                    4096
                  ],
                  "output": [
                    116,
                    4096
                  ]
                },
                "repeats": 36,
                "matrix_flops": 3892314112,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 33554432,
                "activation_read_bytes": 950272,
                "activation_write_bytes": 950272,
                "notes": "\u72ec\u7acb GEMM\uff1a\u6743\u91cd\u4e0e\u8f93\u5165\u5404\u8bfb\u4e00\u6b21\u3001\u8f93\u51fa\u5199\u4e00\u6b21\u7684\u64cd\u4f5c\u6570\u8f7d\u8377\uff1b\u4e0d\u9884\u6d4b tile \u91cd\u8bfb\u3002"
              },
              {
                "name": "attention_residual",
                "category": "residual",
                "shapes": {
                  "inputs_each": [
                    116,
                    4096
                  ],
                  "output": [
                    116,
                    4096
                  ]
                },
                "repeats": 36,
                "matrix_flops": 0,
                "scalar_flops": 475136,
                "special_ops": {},
                "weight_read_bytes": 0,
                "activation_read_bytes": 1900544,
                "activation_write_bytes": 950272,
                "notes": ""
              },
              {
                "name": "post_attention_layernorm",
                "category": "normalization",
                "shapes": {
                  "input": [
                    116,
                    4096
                  ],
                  "weight": [
                    4096
                  ],
                  "output": [
                    116,
                    4096
                  ]
                },
                "repeats": 36,
                "matrix_flops": 0,
                "scalar_flops": 1900660,
                "special_ops": {
                  "rsqrt": 116
                },
                "weight_read_bytes": 8192,
                "activation_read_bytes": 950272,
                "activation_write_bytes": 950272,
                "notes": "\u6309 FP32 \u884c\u5185\u5f52\u7ea6\u7684\u4ee3\u6570\u8ba1\u6570\uff1brsqrt\u3001\u7c7b\u578b\u8f6c\u6362\u4e0e\u4e34\u65f6 FP32 \u5f20\u91cf\u5206\u5217\uff0f\u4e0d\u63a8\u65ad HBM spill\u3002"
              },
              {
                "name": "gate_proj",
                "category": "linear",
                "shapes": {
                  "input": [
                    116,
                    4096
                  ],
                  "weight_math": [
                    4096,
                    12288
                  ],
                  "weight_storage": [
                    12288,
                    4096
                  ],
                  "output": [
                    116,
                    12288
                  ]
                },
                "repeats": 36,
                "matrix_flops": 11676942336,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 100663296,
                "activation_read_bytes": 950272,
                "activation_write_bytes": 2850816,
                "notes": "\u72ec\u7acb GEMM\uff1a\u6743\u91cd\u4e0e\u8f93\u5165\u5404\u8bfb\u4e00\u6b21\u3001\u8f93\u51fa\u5199\u4e00\u6b21\u7684\u64cd\u4f5c\u6570\u8f7d\u8377\uff1b\u4e0d\u9884\u6d4b tile \u91cd\u8bfb\u3002"
              },
              {
                "name": "up_proj",
                "category": "linear",
                "shapes": {
                  "input": [
                    116,
                    4096
                  ],
                  "weight_math": [
                    4096,
                    12288
                  ],
                  "weight_storage": [
                    12288,
                    4096
                  ],
                  "output": [
                    116,
                    12288
                  ]
                },
                "repeats": 36,
                "matrix_flops": 11676942336,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 100663296,
                "activation_read_bytes": 950272,
                "activation_write_bytes": 2850816,
                "notes": "\u72ec\u7acb GEMM\uff1a\u6743\u91cd\u4e0e\u8f93\u5165\u5404\u8bfb\u4e00\u6b21\u3001\u8f93\u51fa\u5199\u4e00\u6b21\u7684\u64cd\u4f5c\u6570\u8f7d\u8377\uff1b\u4e0d\u9884\u6d4b tile \u91cd\u8bfb\u3002"
              },
              {
                "name": "silu_mul",
                "category": "activation",
                "shapes": {
                  "gate": [
                    116,
                    12288
                  ],
                  "up": [
                    116,
                    12288
                  ],
                  "output": [
                    116,
                    12288
                  ]
                },
                "repeats": 36,
                "matrix_flops": 0,
                "scalar_flops": 5701632,
                "special_ops": {
                  "exp": 1425408,
                  "negate": 1425408
                },
                "weight_read_bytes": 0,
                "activation_read_bytes": 5701632,
                "activation_write_bytes": 2850816,
                "notes": "sigmoid: exp(-x), +1, reciprocal\uff1b\u518d\u4e58 x \u548c up\u3002exp \u4e0e\u53d6\u8d1f\u5206\u5217\u3002"
              },
              {
                "name": "down_proj",
                "category": "linear",
                "shapes": {
                  "input": [
                    116,
                    12288
                  ],
                  "weight_math": [
                    12288,
                    4096
                  ],
                  "weight_storage": [
                    4096,
                    12288
                  ],
                  "output": [
                    116,
                    4096
                  ]
                },
                "repeats": 36,
                "matrix_flops": 11676942336,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 100663296,
                "activation_read_bytes": 2850816,
                "activation_write_bytes": 950272,
                "notes": "\u72ec\u7acb GEMM\uff1a\u6743\u91cd\u4e0e\u8f93\u5165\u5404\u8bfb\u4e00\u6b21\u3001\u8f93\u51fa\u5199\u4e00\u6b21\u7684\u64cd\u4f5c\u6570\u8f7d\u8377\uff1b\u4e0d\u9884\u6d4b tile \u91cd\u8bfb\u3002"
              },
              {
                "name": "ffn_residual",
                "category": "residual",
                "shapes": {
                  "inputs_each": [
                    116,
                    4096
                  ],
                  "output": [
                    116,
                    4096
                  ]
                },
                "repeats": 36,
                "matrix_flops": 0,
                "scalar_flops": 475136,
                "special_ops": {},
                "weight_read_bytes": 0,
                "activation_read_bytes": 1900544,
                "activation_write_bytes": 950272,
                "notes": ""
              },
              {
                "name": "final_norm",
                "category": "normalization",
                "shapes": {
                  "input": [
                    116,
                    4096
                  ],
                  "weight": [
                    4096
                  ],
                  "output": [
                    116,
                    4096
                  ]
                },
                "repeats": 1,
                "matrix_flops": 0,
                "scalar_flops": 1900660,
                "special_ops": {
                  "rsqrt": 116
                },
                "weight_read_bytes": 8192,
                "activation_read_bytes": 950272,
                "activation_write_bytes": 950272,
                "notes": "\u6309 FP32 \u884c\u5185\u5f52\u7ea6\u7684\u4ee3\u6570\u8ba1\u6570\uff1brsqrt\u3001\u7c7b\u578b\u8f6c\u6362\u4e0e\u4e34\u65f6 FP32 \u5f20\u91cf\u5206\u5217\uff0f\u4e0d\u63a8\u65ad HBM spill\u3002"
              },
              {
                "name": "lm_head",
                "category": "linear",
                "shapes": {
                  "input": [
                    1,
                    4096
                  ],
                  "weight_math": [
                    4096,
                    151936
                  ],
                  "weight_storage": [
                    151936,
                    4096
                  ],
                  "output": [
                    1,
                    151936
                  ]
                },
                "repeats": 1,
                "matrix_flops": 1244659712,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 1244659712,
                "activation_read_bytes": 8192,
                "activation_write_bytes": 303872,
                "notes": "\u72ec\u7acb GEMM\uff1a\u6743\u91cd\u4e0e\u8f93\u5165\u5404\u8bfb\u4e00\u6b21\u3001\u8f93\u51fa\u5199\u4e00\u6b21\u7684\u64cd\u4f5c\u6570\u8f7d\u8377\uff1b\u4e0d\u9884\u6d4b tile \u91cd\u8bfb\u3002"
              }
            ],
            "summary": {
              "parameters": 8190735360,
              "weight_resident_bytes": 16381470720,
              "backbone_projection_ffn_flops": 1611418042368,
              "causal_attention_matrix_flops": 4002545664,
              "rectangular_attention_matrix_flops": 7936671744,
              "matrix_flops": 1616665247744,
              "scalar_flops": 559195284,
              "special_ops": {
                "sin": 14848,
                "cos": 14848,
                "rsqrt": 175508,
                "negate": 62005248,
                "exp": 59132160,
                "compare_max": 7683840,
                "mask_decisions": 15501312
              },
              "weight_read_once_per_operator_bytes": 15137761280,
              "activation_operand_read_bytes": 999458880,
              "activation_operand_write_bytes": 827575040,
              "kv_bytes_per_token_per_request": 147456,
              "kv_resident_before_bytes": 0,
              "kv_resident_after_bytes": 17104896,
              "kv_new_write_bytes": 17104896,
              "kv_existing_history_unique_payload_bytes": 0,
              "kv_attention_unique_payload_bytes": 17104896,
              "kv_logical_query_head_operand_bytes": 4002545664,
              "attention_score_tensor_per_layer_bytes": 1722368,
              "materialized_scores_probabilities_io_all_layers_bytes": 248020992,
              "minimum_required_weight_and_kv_bytes": 16398575616
            }
          },
          "state_after_bytes": 17104896
        },
        "decode": null,
        "complete_logical_totals": null,
        "final_state_bytes": null
      }
    },
    {
      "request": 1,
      "application_request_id": "book909chat-capture-1",
      "recorded": {
        "input_tokens": 168,
        "cached_tokens": 112,
        "returned_id_tokens": 16,
        "engine_completion_tokens": 16,
        "output_parts": {
          "reasoning": 0,
          "nonreasoning": 15,
          "delimiter": 0,
          "termination": 1,
          "unknown": 0
        },
        "finish_reason": {
          "type": "stop",
          "matched": 151645
        },
        "worker": "worker0-requests",
        "application_wall_seconds": 0.17865554196760058,
        "engine_e2e_seconds": 0.1771900539752096,
        "tool_wait_seconds": null,
        "previous_same_worker_completion_gap_seconds": 0.0010008979588747025
      },
      "mapping": {
        "prefix_tokens": 112,
        "new_tokens": 56,
        "batch": 1,
        "output_head": "last",
        "sampled_steps": null,
        "decode_forward_calls": null,
        "observed_model_forward_calls": null
      },
      "resources": {
        "prefill": {
          "logical_forward_calls": 1,
          "totals": {
            "matrix_flops": 783811346432,
            "accounted_scalar_flops": 291116280,
            "special_ops": {
              "sin": 7168,
              "cos": 7168,
              "rsqrt": 84728,
              "negate": 29933568,
              "exp": 33836544,
              "compare_max": 8999424,
              "mask_decisions": 10838016
            },
            "known_interfaces": {
              "weight_read_once_per_operator_bytes": 15137269760,
              "activation_operand_read_bytes": 525853824,
              "activation_operand_write_bytes": 426513152,
              "kv_existing_history_unique_payload_bytes": 16515072,
              "kv_new_write_bytes": 8257536
            }
          },
          "source_ledger": {
            "schema_version": 1,
            "calculation": "qwen3-dense-forward",
            "model": "qwen3-8b",
            "scenario": {
              "batch": 1,
              "history": 112,
              "tokens": 56,
              "output_head": "last",
              "weight_bytes": 2,
              "activation_bytes": 2,
              "kv_bytes": 2,
              "score_bytes": 4
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
            "dimensions": {
              "num_hidden_layers": 36,
              "hidden_size": 4096,
              "intermediate_size": 12288,
              "num_attention_heads": 32,
              "num_key_value_heads": 8,
              "head_dim": 128,
              "vocab_size": 151936,
              "tie_word_embeddings": false
            },
            "assumptions": [
              "\u6240\u6709\u8bf7\u6c42\u7b49\u957f\u3001\u76f8\u540c\u4f4d\u7f6e ID\u3001\u65e0\u8de8\u8bf7\u6c42\u524d\u7f00\u5171\u4eab\uff0c\u65e0 TP/PP\uff1bdropout=0 \u63a8\u7406\u3002",
              "\u5168\u6a21\u578b\u6743\u91cd\u7edf\u4e00 weight_bytes \u7684\u6559\u5b66\u683c\u5f0f\uff1b\u4e0d\u7531 torch_dtype \u63a8\u65ad\u5b9e\u9645\u91cf\u5316\u683c\u5f0f\u3002",
              "\u6bcf\u884c operator \u6210\u672c\u4e3a\u4e00\u6b21\u51fa\u73b0\uff0crepeats \u662f\u5c42\u6570\uff1b\u5e03\u5c40\u89c6\u56fe\u4e0e GQA repeat \u4e0d\u989d\u5916\u7269\u5316\u3002",
              "FMA=2\uff1bmatrix_flops \u662f\u6709\u6548\u56e0\u679c\u77e9\u9635\u5de5\u4f5c\uff0cscalar_flops \u662f\u58f0\u660e\u7b97\u6cd5\u7684\u666e\u901a\u7b97\u672f\uff1b\u7279\u6b8a\u51fd\u6570\u53e6\u5217\u3002",
              "operator \u8bfb\u5199\u662f\u72ec\u7acb\u7b97\u5b50\u64cd\u4f5c\u6570\u8f7d\u8377\uff0c\u5206\u6570\uff0f\u6982\u7387\u77e9\u5f62\u7269\u5316\uff1b\u4e0d\u662f\u5b9e\u6d4b HBM\u3001\u4e0d\u662f\u5168\u56fe\u6d41\u91cf\u4e0b\u754c\u3002",
              "\u6807\u91cf\u884c\u5185\u4e2d\u95f4\u91cf\u89c6\u4e3a\u7247\u4e0a\uff1b\u77e9\u5f62\u6ce8\u610f\u529b\u540c\u65f6\u62a5\u544a\uff0cFlashAttention/tile/\u7f13\u5b58\u6d41\u91cf\u7531\u6267\u884c\u4e13\u9898\u53e6\u7b97\u3002",
              "\u4e0d\u8ba1\u91c7\u6837\u3001tokenizer\u3001kernel launch\u3001\u5206\u914d\u5668\u3001KV \u7ba1\u7406\u7d22\u5f15\u53ca\u540e\u7aef\u5de5\u4f5c\u533a\uff1b\u4e0d\u636e\u6b64\u58f0\u79f0\u5b8c\u6574 token \u65f6\u95f4\u3002"
            ],
            "weights": [
              {
                "name": "model.embed_tokens.weight",
                "shape": [
                  151936,
                  4096
                ],
                "copies": 1,
                "note": "",
                "parameters": 622329856,
                "resident_bytes": 1244659712
              },
              {
                "name": "model.layers.{layer}.self_attn.q_proj.weight",
                "shape": [
                  4096,
                  4096
                ],
                "copies": 36,
                "note": "",
                "parameters": 603979776,
                "resident_bytes": 1207959552
              },
              {
                "name": "model.layers.{layer}.self_attn.k_proj.weight",
                "shape": [
                  1024,
                  4096
                ],
                "copies": 36,
                "note": "",
                "parameters": 150994944,
                "resident_bytes": 301989888
              },
              {
                "name": "model.layers.{layer}.self_attn.v_proj.weight",
                "shape": [
                  1024,
                  4096
                ],
                "copies": 36,
                "note": "",
                "parameters": 150994944,
                "resident_bytes": 301989888
              },
              {
                "name": "model.layers.{layer}.self_attn.o_proj.weight",
                "shape": [
                  4096,
                  4096
                ],
                "copies": 36,
                "note": "",
                "parameters": 603979776,
                "resident_bytes": 1207959552
              },
              {
                "name": "model.layers.{layer}.self_attn.q_norm.weight",
                "shape": [
                  128
                ],
                "copies": 36,
                "note": "",
                "parameters": 4608,
                "resident_bytes": 9216
              },
              {
                "name": "model.layers.{layer}.self_attn.k_norm.weight",
                "shape": [
                  128
                ],
                "copies": 36,
                "note": "",
                "parameters": 4608,
                "resident_bytes": 9216
              },
              {
                "name": "model.layers.{layer}.input_layernorm.weight",
                "shape": [
                  4096
                ],
                "copies": 36,
                "note": "",
                "parameters": 147456,
                "resident_bytes": 294912
              },
              {
                "name": "model.layers.{layer}.post_attention_layernorm.weight",
                "shape": [
                  4096
                ],
                "copies": 36,
                "note": "",
                "parameters": 147456,
                "resident_bytes": 294912
              },
              {
                "name": "model.norm.weight",
                "shape": [
                  4096
                ],
                "copies": 1,
                "note": "",
                "parameters": 4096,
                "resident_bytes": 8192
              },
              {
                "name": "lm_head.weight",
                "shape": [
                  151936,
                  4096
                ],
                "copies": 1,
                "note": "",
                "parameters": 622329856,
                "resident_bytes": 1244659712
              },
              {
                "name": "model.layers.{layer}.mlp.gate_proj.weight",
                "shape": [
                  12288,
                  4096
                ],
                "copies": 36,
                "note": "",
                "parameters": 1811939328,
                "resident_bytes": 3623878656
              },
              {
                "name": "model.layers.{layer}.mlp.up_proj.weight",
                "shape": [
                  12288,
                  4096
                ],
                "copies": 36,
                "note": "",
                "parameters": 1811939328,
                "resident_bytes": 3623878656
              },
              {
                "name": "model.layers.{layer}.mlp.down_proj.weight",
                "shape": [
                  4096,
                  12288
                ],
                "copies": 36,
                "note": "",
                "parameters": 1811939328,
                "resident_bytes": 3623878656
              }
            ],
            "operators": [
              {
                "name": "embedding",
                "category": "embedding",
                "shapes": {
                  "indices": [
                    1,
                    56
                  ],
                  "table": [
                    151936,
                    4096
                  ],
                  "output": [
                    56,
                    4096
                  ]
                },
                "repeats": 1,
                "matrix_flops": 0,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 458752,
                "activation_read_bytes": 448,
                "activation_write_bytes": 458752,
                "notes": "\u6bcf token \u4e00\u6b21\u884c\u67e5\u627e\uff0c\u4e0d\u8bfb\u53d6\u6574\u4e2a\u8bcd\u8868\uff1b\u91cd\u590d token \u662f\u5426\u7f13\u5b58\u672a\u5047\u5b9a\u3002int64 \u8f93\u5165\u7d22\u5f15\u3002"
              },
              {
                "name": "rope_table",
                "category": "position",
                "shapes": {
                  "frequencies": [
                    56,
                    64
                  ],
                  "cos_sin_each": [
                    56,
                    128
                  ]
                },
                "repeats": 1,
                "matrix_flops": 0,
                "scalar_flops": 3584,
                "special_ops": {
                  "sin": 7168,
                  "cos": 7168
                },
                "weight_read_bytes": 0,
                "activation_read_bytes": 704,
                "activation_write_bytes": 28672,
                "notes": "\u540c\u4f4d\u7f6e ID \u6279\u5171\u4eab\uff0c\u6240\u6709\u5c42\u590d\u7528\uff1binv_freq \u56fa\u5b9a\u4e0d\u8ba1\u521d\u59cb\u5316\u3002\u53c2\u8003\u8def\u5f84\u590d\u5236\u9891\u7387\u540e\u6c42 sin/cos\uff1b\u8f6c\u6362\u53e6\u8ba1\u3002"
              },
              {
                "name": "input_layernorm",
                "category": "normalization",
                "shapes": {
                  "input": [
                    56,
                    4096
                  ],
                  "weight": [
                    4096
                  ],
                  "output": [
                    56,
                    4096
                  ]
                },
                "repeats": 36,
                "matrix_flops": 0,
                "scalar_flops": 917560,
                "special_ops": {
                  "rsqrt": 56
                },
                "weight_read_bytes": 8192,
                "activation_read_bytes": 458752,
                "activation_write_bytes": 458752,
                "notes": "\u6309 FP32 \u884c\u5185\u5f52\u7ea6\u7684\u4ee3\u6570\u8ba1\u6570\uff1brsqrt\u3001\u7c7b\u578b\u8f6c\u6362\u4e0e\u4e34\u65f6 FP32 \u5f20\u91cf\u5206\u5217\uff0f\u4e0d\u63a8\u65ad HBM spill\u3002"
              },
              {
                "name": "q_proj",
                "category": "linear",
                "shapes": {
                  "input": [
                    56,
                    4096
                  ],
                  "weight_math": [
                    4096,
                    4096
                  ],
                  "weight_storage": [
                    4096,
                    4096
                  ],
                  "output": [
                    56,
                    4096
                  ]
                },
                "repeats": 36,
                "matrix_flops": 1879048192,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 33554432,
                "activation_read_bytes": 458752,
                "activation_write_bytes": 458752,
                "notes": "\u72ec\u7acb GEMM\uff1a\u6743\u91cd\u4e0e\u8f93\u5165\u5404\u8bfb\u4e00\u6b21\u3001\u8f93\u51fa\u5199\u4e00\u6b21\u7684\u64cd\u4f5c\u6570\u8f7d\u8377\uff1b\u4e0d\u9884\u6d4b tile \u91cd\u8bfb\u3002"
              },
              {
                "name": "k_proj",
                "category": "linear",
                "shapes": {
                  "input": [
                    56,
                    4096
                  ],
                  "weight_math": [
                    4096,
                    1024
                  ],
                  "weight_storage": [
                    1024,
                    4096
                  ],
                  "output": [
                    56,
                    1024
                  ]
                },
                "repeats": 36,
                "matrix_flops": 469762048,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 8388608,
                "activation_read_bytes": 458752,
                "activation_write_bytes": 114688,
                "notes": "\u72ec\u7acb GEMM\uff1a\u6743\u91cd\u4e0e\u8f93\u5165\u5404\u8bfb\u4e00\u6b21\u3001\u8f93\u51fa\u5199\u4e00\u6b21\u7684\u64cd\u4f5c\u6570\u8f7d\u8377\uff1b\u4e0d\u9884\u6d4b tile \u91cd\u8bfb\u3002"
              },
              {
                "name": "v_proj",
                "category": "linear",
                "shapes": {
                  "input": [
                    56,
                    4096
                  ],
                  "weight_math": [
                    4096,
                    1024
                  ],
                  "weight_storage": [
                    1024,
                    4096
                  ],
                  "output": [
                    56,
                    1024
                  ]
                },
                "repeats": 36,
                "matrix_flops": 469762048,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 8388608,
                "activation_read_bytes": 458752,
                "activation_write_bytes": 114688,
                "notes": "\u72ec\u7acb GEMM\uff1a\u6743\u91cd\u4e0e\u8f93\u5165\u5404\u8bfb\u4e00\u6b21\u3001\u8f93\u51fa\u5199\u4e00\u6b21\u7684\u64cd\u4f5c\u6570\u8f7d\u8377\uff1b\u4e0d\u9884\u6d4b tile \u91cd\u8bfb\u3002"
              },
              {
                "name": "q_norm",
                "category": "normalization",
                "shapes": {
                  "input": [
                    1792,
                    128
                  ],
                  "weight": [
                    128
                  ],
                  "output": [
                    1792,
                    128
                  ]
                },
                "repeats": 36,
                "matrix_flops": 0,
                "scalar_flops": 919296,
                "special_ops": {
                  "rsqrt": 1792
                },
                "weight_read_bytes": 256,
                "activation_read_bytes": 458752,
                "activation_write_bytes": 458752,
                "notes": "\u6309 FP32 \u884c\u5185\u5f52\u7ea6\u7684\u4ee3\u6570\u8ba1\u6570\uff1brsqrt\u3001\u7c7b\u578b\u8f6c\u6362\u4e0e\u4e34\u65f6 FP32 \u5f20\u91cf\u5206\u5217\uff0f\u4e0d\u63a8\u65ad HBM spill\u3002"
              },
              {
                "name": "k_norm",
                "category": "normalization",
                "shapes": {
                  "input": [
                    448,
                    128
                  ],
                  "weight": [
                    128
                  ],
                  "output": [
                    448,
                    128
                  ]
                },
                "repeats": 36,
                "matrix_flops": 0,
                "scalar_flops": 229824,
                "special_ops": {
                  "rsqrt": 448
                },
                "weight_read_bytes": 256,
                "activation_read_bytes": 114688,
                "activation_write_bytes": 114688,
                "notes": "\u6309 FP32 \u884c\u5185\u5f52\u7ea6\u7684\u4ee3\u6570\u8ba1\u6570\uff1brsqrt\u3001\u7c7b\u578b\u8f6c\u6362\u4e0e\u4e34\u65f6 FP32 \u5f20\u91cf\u5206\u5217\uff0f\u4e0d\u63a8\u65ad HBM spill\u3002"
              },
              {
                "name": "apply_rope",
                "category": "position",
                "shapes": {
                  "Q": [
                    1,
                    32,
                    56,
                    128
                  ],
                  "K": [
                    1,
                    8,
                    56,
                    128
                  ]
                },
                "repeats": 36,
                "matrix_flops": 0,
                "scalar_flops": 860160,
                "special_ops": {
                  "negate": 143360
                },
                "weight_read_bytes": 0,
                "activation_read_bytes": 602112,
                "activation_write_bytes": 573440,
                "notes": "2 multiply + 1 add/\u5143\u7d20\uff0crotate_half \u7b26\u53f7\u7ffb\u8f6c\u5206\u5217\uff1b\u8868\u6309\u6279\uff0f\u5934\u7406\u60f3\u590d\u7528\u3002"
              },
              {
                "name": "kv_append",
                "category": "state",
                "shapes": {
                  "new_K_and_V_each": [
                    1,
                    8,
                    56,
                    128
                  ]
                },
                "repeats": 36,
                "matrix_flops": 0,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 0,
                "activation_read_bytes": 229376,
                "activation_write_bytes": 229376,
                "notes": "\u539f\u4f4d\uff0f\u5206\u9875 append \u8f7d\u8377\uff1b\u4e0d\u5047\u5b9a\u52a8\u6001 torch.cat \u5bf9\u65e7\u7f13\u5b58\u6574\u6bb5\u590d\u5236\u3002"
              },
              {
                "name": "qk",
                "category": "attention",
                "shapes": {
                  "Q": [
                    1,
                    32,
                    56,
                    128
                  ],
                  "K_shared": [
                    1,
                    8,
                    168,
                    128
                  ],
                  "scores_rectangular": [
                    1,
                    32,
                    56,
                    168
                  ]
                },
                "repeats": 36,
                "matrix_flops": 64454656,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 0,
                "activation_read_bytes": 802816,
                "activation_write_bytes": 1204224,
                "notes": "FLOPs \u4ec5\u6709\u6548\u56e0\u679c\u4f4d\u7f6e\uff1b\u8f7d\u8377\u662f\u5047\u5b9a Q/K \u5404\u8bfb\u4e00\u6b21\u3001GQA \u5934\u5171\u4eab\uff0c\u5b8c\u6574\u5206\u6570\u77e9\u9635\u7269\u5316\u3002"
              },
              {
                "name": "score_scale_mask_softmax",
                "category": "softmax",
                "shapes": {
                  "scores": [
                    1,
                    32,
                    56,
                    168
                  ]
                },
                "repeats": 36,
                "matrix_flops": 0,
                "scalar_flops": 1005312,
                "special_ops": {
                  "exp": 251776,
                  "compare_max": 249984,
                  "mask_decisions": 301056
                },
                "weight_read_bytes": 0,
                "activation_read_bytes": 1204224,
                "activation_write_bytes": 1204224,
                "notes": "\u9009\u62e9\u7684\u878d\u5408 scale/mask/softmax \u4ee3\u6570\u5de5\u4f5c\uff1b\u5c4f\u853d\u70b9\u4e0d\u8ba1 exp\u3002\u7269\u5316 FP32 \u9ed8\u8ba4\u6982\u7387\uff1b\u975e\u5177\u4f53 eager trace\u3002"
              },
              {
                "name": "pv",
                "category": "attention",
                "shapes": {
                  "P": [
                    1,
                    32,
                    56,
                    168
                  ],
                  "V_shared": [
                    1,
                    8,
                    168,
                    128
                  ],
                  "output": [
                    1,
                    32,
                    56,
                    128
                  ]
                },
                "repeats": 36,
                "matrix_flops": 64454656,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 0,
                "activation_read_bytes": 1548288,
                "activation_write_bytes": 458752,
                "notes": "PV/AV\uff1a\u5404 Q \u5934\u4ecd\u8ba1\u7b97\uff1bV \u5bb9\u91cf\u4e0d\u4e58 GQA \u590d\u5236\u6570\u3002\u8f7d\u8377\u5047\u5b9a V \u5728\u5934\uff0f\u67e5\u8be2\u4e4b\u95f4\u7406\u60f3\u590d\u7528\u3002"
              },
              {
                "name": "o_proj",
                "category": "linear",
                "shapes": {
                  "input": [
                    56,
                    4096
                  ],
                  "weight_math": [
                    4096,
                    4096
                  ],
                  "weight_storage": [
                    4096,
                    4096
                  ],
                  "output": [
                    56,
                    4096
                  ]
                },
                "repeats": 36,
                "matrix_flops": 1879048192,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 33554432,
                "activation_read_bytes": 458752,
                "activation_write_bytes": 458752,
                "notes": "\u72ec\u7acb GEMM\uff1a\u6743\u91cd\u4e0e\u8f93\u5165\u5404\u8bfb\u4e00\u6b21\u3001\u8f93\u51fa\u5199\u4e00\u6b21\u7684\u64cd\u4f5c\u6570\u8f7d\u8377\uff1b\u4e0d\u9884\u6d4b tile \u91cd\u8bfb\u3002"
              },
              {
                "name": "attention_residual",
                "category": "residual",
                "shapes": {
                  "inputs_each": [
                    56,
                    4096
                  ],
                  "output": [
                    56,
                    4096
                  ]
                },
                "repeats": 36,
                "matrix_flops": 0,
                "scalar_flops": 229376,
                "special_ops": {},
                "weight_read_bytes": 0,
                "activation_read_bytes": 917504,
                "activation_write_bytes": 458752,
                "notes": ""
              },
              {
                "name": "post_attention_layernorm",
                "category": "normalization",
                "shapes": {
                  "input": [
                    56,
                    4096
                  ],
                  "weight": [
                    4096
                  ],
                  "output": [
                    56,
                    4096
                  ]
                },
                "repeats": 36,
                "matrix_flops": 0,
                "scalar_flops": 917560,
                "special_ops": {
                  "rsqrt": 56
                },
                "weight_read_bytes": 8192,
                "activation_read_bytes": 458752,
                "activation_write_bytes": 458752,
                "notes": "\u6309 FP32 \u884c\u5185\u5f52\u7ea6\u7684\u4ee3\u6570\u8ba1\u6570\uff1brsqrt\u3001\u7c7b\u578b\u8f6c\u6362\u4e0e\u4e34\u65f6 FP32 \u5f20\u91cf\u5206\u5217\uff0f\u4e0d\u63a8\u65ad HBM spill\u3002"
              },
              {
                "name": "gate_proj",
                "category": "linear",
                "shapes": {
                  "input": [
                    56,
                    4096
                  ],
                  "weight_math": [
                    4096,
                    12288
                  ],
                  "weight_storage": [
                    12288,
                    4096
                  ],
                  "output": [
                    56,
                    12288
                  ]
                },
                "repeats": 36,
                "matrix_flops": 5637144576,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 100663296,
                "activation_read_bytes": 458752,
                "activation_write_bytes": 1376256,
                "notes": "\u72ec\u7acb GEMM\uff1a\u6743\u91cd\u4e0e\u8f93\u5165\u5404\u8bfb\u4e00\u6b21\u3001\u8f93\u51fa\u5199\u4e00\u6b21\u7684\u64cd\u4f5c\u6570\u8f7d\u8377\uff1b\u4e0d\u9884\u6d4b tile \u91cd\u8bfb\u3002"
              },
              {
                "name": "up_proj",
                "category": "linear",
                "shapes": {
                  "input": [
                    56,
                    4096
                  ],
                  "weight_math": [
                    4096,
                    12288
                  ],
                  "weight_storage": [
                    12288,
                    4096
                  ],
                  "output": [
                    56,
                    12288
                  ]
                },
                "repeats": 36,
                "matrix_flops": 5637144576,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 100663296,
                "activation_read_bytes": 458752,
                "activation_write_bytes": 1376256,
                "notes": "\u72ec\u7acb GEMM\uff1a\u6743\u91cd\u4e0e\u8f93\u5165\u5404\u8bfb\u4e00\u6b21\u3001\u8f93\u51fa\u5199\u4e00\u6b21\u7684\u64cd\u4f5c\u6570\u8f7d\u8377\uff1b\u4e0d\u9884\u6d4b tile \u91cd\u8bfb\u3002"
              },
              {
                "name": "silu_mul",
                "category": "activation",
                "shapes": {
                  "gate": [
                    56,
                    12288
                  ],
                  "up": [
                    56,
                    12288
                  ],
                  "output": [
                    56,
                    12288
                  ]
                },
                "repeats": 36,
                "matrix_flops": 0,
                "scalar_flops": 2752512,
                "special_ops": {
                  "exp": 688128,
                  "negate": 688128
                },
                "weight_read_bytes": 0,
                "activation_read_bytes": 2752512,
                "activation_write_bytes": 1376256,
                "notes": "sigmoid: exp(-x), +1, reciprocal\uff1b\u518d\u4e58 x \u548c up\u3002exp \u4e0e\u53d6\u8d1f\u5206\u5217\u3002"
              },
              {
                "name": "down_proj",
                "category": "linear",
                "shapes": {
                  "input": [
                    56,
                    12288
                  ],
                  "weight_math": [
                    12288,
                    4096
                  ],
                  "weight_storage": [
                    4096,
                    12288
                  ],
                  "output": [
                    56,
                    4096
                  ]
                },
                "repeats": 36,
                "matrix_flops": 5637144576,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 100663296,
                "activation_read_bytes": 1376256,
                "activation_write_bytes": 458752,
                "notes": "\u72ec\u7acb GEMM\uff1a\u6743\u91cd\u4e0e\u8f93\u5165\u5404\u8bfb\u4e00\u6b21\u3001\u8f93\u51fa\u5199\u4e00\u6b21\u7684\u64cd\u4f5c\u6570\u8f7d\u8377\uff1b\u4e0d\u9884\u6d4b tile \u91cd\u8bfb\u3002"
              },
              {
                "name": "ffn_residual",
                "category": "residual",
                "shapes": {
                  "inputs_each": [
                    56,
                    4096
                  ],
                  "output": [
                    56,
                    4096
                  ]
                },
                "repeats": 36,
                "matrix_flops": 0,
                "scalar_flops": 229376,
                "special_ops": {},
                "weight_read_bytes": 0,
                "activation_read_bytes": 917504,
                "activation_write_bytes": 458752,
                "notes": ""
              },
              {
                "name": "final_norm",
                "category": "normalization",
                "shapes": {
                  "input": [
                    56,
                    4096
                  ],
                  "weight": [
                    4096
                  ],
                  "output": [
                    56,
                    4096
                  ]
                },
                "repeats": 1,
                "matrix_flops": 0,
                "scalar_flops": 917560,
                "special_ops": {
                  "rsqrt": 56
                },
                "weight_read_bytes": 8192,
                "activation_read_bytes": 458752,
                "activation_write_bytes": 458752,
                "notes": "\u6309 FP32 \u884c\u5185\u5f52\u7ea6\u7684\u4ee3\u6570\u8ba1\u6570\uff1brsqrt\u3001\u7c7b\u578b\u8f6c\u6362\u4e0e\u4e34\u65f6 FP32 \u5f20\u91cf\u5206\u5217\uff0f\u4e0d\u63a8\u65ad HBM spill\u3002"
              },
              {
                "name": "lm_head",
                "category": "linear",
                "shapes": {
                  "input": [
                    1,
                    4096
                  ],
                  "weight_math": [
                    4096,
                    151936
                  ],
                  "weight_storage": [
                    151936,
                    4096
                  ],
                  "output": [
                    1,
                    151936
                  ]
                },
                "repeats": 1,
                "matrix_flops": 1244659712,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 1244659712,
                "activation_read_bytes": 8192,
                "activation_write_bytes": 303872,
                "notes": "\u72ec\u7acb GEMM\uff1a\u6743\u91cd\u4e0e\u8f93\u5165\u5404\u8bfb\u4e00\u6b21\u3001\u8f93\u51fa\u5199\u4e00\u6b21\u7684\u64cd\u4f5c\u6570\u8f7d\u8377\uff1b\u4e0d\u9884\u6d4b tile \u91cd\u8bfb\u3002"
              }
            ],
            "summary": {
              "parameters": 8190735360,
              "weight_resident_bytes": 16381470720,
              "backbone_projection_ffn_flops": 777925951488,
              "causal_attention_matrix_flops": 4640735232,
              "rectangular_attention_matrix_flops": 5549064192,
              "matrix_flops": 783811346432,
              "scalar_flops": 291116280,
              "special_ops": {
                "sin": 7168,
                "cos": 7168,
                "rsqrt": 84728,
                "negate": 29933568,
                "exp": 33836544,
                "compare_max": 8999424,
                "mask_decisions": 10838016
              },
              "weight_read_once_per_operator_bytes": 15137269760,
              "activation_operand_read_bytes": 525853824,
              "activation_operand_write_bytes": 426513152,
              "kv_bytes_per_token_per_request": 147456,
              "kv_resident_before_bytes": 16515072,
              "kv_resident_after_bytes": 24772608,
              "kv_new_write_bytes": 8257536,
              "kv_existing_history_unique_payload_bytes": 16515072,
              "kv_attention_unique_payload_bytes": 24772608,
              "kv_logical_query_head_operand_bytes": 4640735232,
              "attention_score_tensor_per_layer_bytes": 1204224,
              "materialized_scores_probabilities_io_all_layers_bytes": 173408256,
              "minimum_required_weight_and_kv_bytes": 16406243328
            }
          },
          "state_after_bytes": 24772608
        },
        "decode": null,
        "complete_logical_totals": null,
        "final_state_bytes": null
      }
    },
    {
      "request": 2,
      "application_request_id": "book909chat-capture-2",
      "recorded": {
        "input_tokens": 217,
        "cached_tokens": 164,
        "returned_id_tokens": 8,
        "engine_completion_tokens": 8,
        "output_parts": {
          "reasoning": 0,
          "nonreasoning": 7,
          "delimiter": 0,
          "termination": 1,
          "unknown": 0
        },
        "finish_reason": {
          "type": "stop",
          "matched": 151645
        },
        "worker": "worker0-requests",
        "application_wall_seconds": 0.09583428199402988,
        "engine_e2e_seconds": 0.09449789416976273,
        "tool_wait_seconds": null,
        "previous_same_worker_completion_gap_seconds": 0.00071111717261374
      },
      "mapping": {
        "prefix_tokens": 164,
        "new_tokens": 53,
        "batch": 1,
        "output_head": "last",
        "sampled_steps": null,
        "decode_forward_calls": null,
        "observed_model_forward_calls": null
      },
      "resources": {
        "prefill": {
          "logical_forward_calls": 1,
          "totals": {
            "matrix_flops": 743466795008,
            "accounted_scalar_flops": 287854077,
            "special_ops": {
              "sin": 6784,
              "cos": 6784,
              "rsqrt": 80189,
              "negate": 28329984,
              "exp": 35107200,
              "compare_max": 11600640,
              "mask_decisions": 13249152
            },
            "known_interfaces": {
              "weight_read_once_per_operator_bytes": 15137245184,
              "activation_operand_read_bytes": 530169936,
              "activation_operand_write_bytes": 427614464,
              "kv_existing_history_unique_payload_bytes": 24182784,
              "kv_new_write_bytes": 7815168
            }
          },
          "source_ledger": {
            "schema_version": 1,
            "calculation": "qwen3-dense-forward",
            "model": "qwen3-8b",
            "scenario": {
              "batch": 1,
              "history": 164,
              "tokens": 53,
              "output_head": "last",
              "weight_bytes": 2,
              "activation_bytes": 2,
              "kv_bytes": 2,
              "score_bytes": 4
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
            "dimensions": {
              "num_hidden_layers": 36,
              "hidden_size": 4096,
              "intermediate_size": 12288,
              "num_attention_heads": 32,
              "num_key_value_heads": 8,
              "head_dim": 128,
              "vocab_size": 151936,
              "tie_word_embeddings": false
            },
            "assumptions": [
              "\u6240\u6709\u8bf7\u6c42\u7b49\u957f\u3001\u76f8\u540c\u4f4d\u7f6e ID\u3001\u65e0\u8de8\u8bf7\u6c42\u524d\u7f00\u5171\u4eab\uff0c\u65e0 TP/PP\uff1bdropout=0 \u63a8\u7406\u3002",
              "\u5168\u6a21\u578b\u6743\u91cd\u7edf\u4e00 weight_bytes \u7684\u6559\u5b66\u683c\u5f0f\uff1b\u4e0d\u7531 torch_dtype \u63a8\u65ad\u5b9e\u9645\u91cf\u5316\u683c\u5f0f\u3002",
              "\u6bcf\u884c operator \u6210\u672c\u4e3a\u4e00\u6b21\u51fa\u73b0\uff0crepeats \u662f\u5c42\u6570\uff1b\u5e03\u5c40\u89c6\u56fe\u4e0e GQA repeat \u4e0d\u989d\u5916\u7269\u5316\u3002",
              "FMA=2\uff1bmatrix_flops \u662f\u6709\u6548\u56e0\u679c\u77e9\u9635\u5de5\u4f5c\uff0cscalar_flops \u662f\u58f0\u660e\u7b97\u6cd5\u7684\u666e\u901a\u7b97\u672f\uff1b\u7279\u6b8a\u51fd\u6570\u53e6\u5217\u3002",
              "operator \u8bfb\u5199\u662f\u72ec\u7acb\u7b97\u5b50\u64cd\u4f5c\u6570\u8f7d\u8377\uff0c\u5206\u6570\uff0f\u6982\u7387\u77e9\u5f62\u7269\u5316\uff1b\u4e0d\u662f\u5b9e\u6d4b HBM\u3001\u4e0d\u662f\u5168\u56fe\u6d41\u91cf\u4e0b\u754c\u3002",
              "\u6807\u91cf\u884c\u5185\u4e2d\u95f4\u91cf\u89c6\u4e3a\u7247\u4e0a\uff1b\u77e9\u5f62\u6ce8\u610f\u529b\u540c\u65f6\u62a5\u544a\uff0cFlashAttention/tile/\u7f13\u5b58\u6d41\u91cf\u7531\u6267\u884c\u4e13\u9898\u53e6\u7b97\u3002",
              "\u4e0d\u8ba1\u91c7\u6837\u3001tokenizer\u3001kernel launch\u3001\u5206\u914d\u5668\u3001KV \u7ba1\u7406\u7d22\u5f15\u53ca\u540e\u7aef\u5de5\u4f5c\u533a\uff1b\u4e0d\u636e\u6b64\u58f0\u79f0\u5b8c\u6574 token \u65f6\u95f4\u3002"
            ],
            "weights": [
              {
                "name": "model.embed_tokens.weight",
                "shape": [
                  151936,
                  4096
                ],
                "copies": 1,
                "note": "",
                "parameters": 622329856,
                "resident_bytes": 1244659712
              },
              {
                "name": "model.layers.{layer}.self_attn.q_proj.weight",
                "shape": [
                  4096,
                  4096
                ],
                "copies": 36,
                "note": "",
                "parameters": 603979776,
                "resident_bytes": 1207959552
              },
              {
                "name": "model.layers.{layer}.self_attn.k_proj.weight",
                "shape": [
                  1024,
                  4096
                ],
                "copies": 36,
                "note": "",
                "parameters": 150994944,
                "resident_bytes": 301989888
              },
              {
                "name": "model.layers.{layer}.self_attn.v_proj.weight",
                "shape": [
                  1024,
                  4096
                ],
                "copies": 36,
                "note": "",
                "parameters": 150994944,
                "resident_bytes": 301989888
              },
              {
                "name": "model.layers.{layer}.self_attn.o_proj.weight",
                "shape": [
                  4096,
                  4096
                ],
                "copies": 36,
                "note": "",
                "parameters": 603979776,
                "resident_bytes": 1207959552
              },
              {
                "name": "model.layers.{layer}.self_attn.q_norm.weight",
                "shape": [
                  128
                ],
                "copies": 36,
                "note": "",
                "parameters": 4608,
                "resident_bytes": 9216
              },
              {
                "name": "model.layers.{layer}.self_attn.k_norm.weight",
                "shape": [
                  128
                ],
                "copies": 36,
                "note": "",
                "parameters": 4608,
                "resident_bytes": 9216
              },
              {
                "name": "model.layers.{layer}.input_layernorm.weight",
                "shape": [
                  4096
                ],
                "copies": 36,
                "note": "",
                "parameters": 147456,
                "resident_bytes": 294912
              },
              {
                "name": "model.layers.{layer}.post_attention_layernorm.weight",
                "shape": [
                  4096
                ],
                "copies": 36,
                "note": "",
                "parameters": 147456,
                "resident_bytes": 294912
              },
              {
                "name": "model.norm.weight",
                "shape": [
                  4096
                ],
                "copies": 1,
                "note": "",
                "parameters": 4096,
                "resident_bytes": 8192
              },
              {
                "name": "lm_head.weight",
                "shape": [
                  151936,
                  4096
                ],
                "copies": 1,
                "note": "",
                "parameters": 622329856,
                "resident_bytes": 1244659712
              },
              {
                "name": "model.layers.{layer}.mlp.gate_proj.weight",
                "shape": [
                  12288,
                  4096
                ],
                "copies": 36,
                "note": "",
                "parameters": 1811939328,
                "resident_bytes": 3623878656
              },
              {
                "name": "model.layers.{layer}.mlp.up_proj.weight",
                "shape": [
                  12288,
                  4096
                ],
                "copies": 36,
                "note": "",
                "parameters": 1811939328,
                "resident_bytes": 3623878656
              },
              {
                "name": "model.layers.{layer}.mlp.down_proj.weight",
                "shape": [
                  4096,
                  12288
                ],
                "copies": 36,
                "note": "",
                "parameters": 1811939328,
                "resident_bytes": 3623878656
              }
            ],
            "operators": [
              {
                "name": "embedding",
                "category": "embedding",
                "shapes": {
                  "indices": [
                    1,
                    53
                  ],
                  "table": [
                    151936,
                    4096
                  ],
                  "output": [
                    53,
                    4096
                  ]
                },
                "repeats": 1,
                "matrix_flops": 0,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 434176,
                "activation_read_bytes": 424,
                "activation_write_bytes": 434176,
                "notes": "\u6bcf token \u4e00\u6b21\u884c\u67e5\u627e\uff0c\u4e0d\u8bfb\u53d6\u6574\u4e2a\u8bcd\u8868\uff1b\u91cd\u590d token \u662f\u5426\u7f13\u5b58\u672a\u5047\u5b9a\u3002int64 \u8f93\u5165\u7d22\u5f15\u3002"
              },
              {
                "name": "rope_table",
                "category": "position",
                "shapes": {
                  "frequencies": [
                    53,
                    64
                  ],
                  "cos_sin_each": [
                    53,
                    128
                  ]
                },
                "repeats": 1,
                "matrix_flops": 0,
                "scalar_flops": 3392,
                "special_ops": {
                  "sin": 6784,
                  "cos": 6784
                },
                "weight_read_bytes": 0,
                "activation_read_bytes": 680,
                "activation_write_bytes": 27136,
                "notes": "\u540c\u4f4d\u7f6e ID \u6279\u5171\u4eab\uff0c\u6240\u6709\u5c42\u590d\u7528\uff1binv_freq \u56fa\u5b9a\u4e0d\u8ba1\u521d\u59cb\u5316\u3002\u53c2\u8003\u8def\u5f84\u590d\u5236\u9891\u7387\u540e\u6c42 sin/cos\uff1b\u8f6c\u6362\u53e6\u8ba1\u3002"
              },
              {
                "name": "input_layernorm",
                "category": "normalization",
                "shapes": {
                  "input": [
                    53,
                    4096
                  ],
                  "weight": [
                    4096
                  ],
                  "output": [
                    53,
                    4096
                  ]
                },
                "repeats": 36,
                "matrix_flops": 0,
                "scalar_flops": 868405,
                "special_ops": {
                  "rsqrt": 53
                },
                "weight_read_bytes": 8192,
                "activation_read_bytes": 434176,
                "activation_write_bytes": 434176,
                "notes": "\u6309 FP32 \u884c\u5185\u5f52\u7ea6\u7684\u4ee3\u6570\u8ba1\u6570\uff1brsqrt\u3001\u7c7b\u578b\u8f6c\u6362\u4e0e\u4e34\u65f6 FP32 \u5f20\u91cf\u5206\u5217\uff0f\u4e0d\u63a8\u65ad HBM spill\u3002"
              },
              {
                "name": "q_proj",
                "category": "linear",
                "shapes": {
                  "input": [
                    53,
                    4096
                  ],
                  "weight_math": [
                    4096,
                    4096
                  ],
                  "weight_storage": [
                    4096,
                    4096
                  ],
                  "output": [
                    53,
                    4096
                  ]
                },
                "repeats": 36,
                "matrix_flops": 1778384896,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 33554432,
                "activation_read_bytes": 434176,
                "activation_write_bytes": 434176,
                "notes": "\u72ec\u7acb GEMM\uff1a\u6743\u91cd\u4e0e\u8f93\u5165\u5404\u8bfb\u4e00\u6b21\u3001\u8f93\u51fa\u5199\u4e00\u6b21\u7684\u64cd\u4f5c\u6570\u8f7d\u8377\uff1b\u4e0d\u9884\u6d4b tile \u91cd\u8bfb\u3002"
              },
              {
                "name": "k_proj",
                "category": "linear",
                "shapes": {
                  "input": [
                    53,
                    4096
                  ],
                  "weight_math": [
                    4096,
                    1024
                  ],
                  "weight_storage": [
                    1024,
                    4096
                  ],
                  "output": [
                    53,
                    1024
                  ]
                },
                "repeats": 36,
                "matrix_flops": 444596224,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 8388608,
                "activation_read_bytes": 434176,
                "activation_write_bytes": 108544,
                "notes": "\u72ec\u7acb GEMM\uff1a\u6743\u91cd\u4e0e\u8f93\u5165\u5404\u8bfb\u4e00\u6b21\u3001\u8f93\u51fa\u5199\u4e00\u6b21\u7684\u64cd\u4f5c\u6570\u8f7d\u8377\uff1b\u4e0d\u9884\u6d4b tile \u91cd\u8bfb\u3002"
              },
              {
                "name": "v_proj",
                "category": "linear",
                "shapes": {
                  "input": [
                    53,
                    4096
                  ],
                  "weight_math": [
                    4096,
                    1024
                  ],
                  "weight_storage": [
                    1024,
                    4096
                  ],
                  "output": [
                    53,
                    1024
                  ]
                },
                "repeats": 36,
                "matrix_flops": 444596224,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 8388608,
                "activation_read_bytes": 434176,
                "activation_write_bytes": 108544,
                "notes": "\u72ec\u7acb GEMM\uff1a\u6743\u91cd\u4e0e\u8f93\u5165\u5404\u8bfb\u4e00\u6b21\u3001\u8f93\u51fa\u5199\u4e00\u6b21\u7684\u64cd\u4f5c\u6570\u8f7d\u8377\uff1b\u4e0d\u9884\u6d4b tile \u91cd\u8bfb\u3002"
              },
              {
                "name": "q_norm",
                "category": "normalization",
                "shapes": {
                  "input": [
                    1696,
                    128
                  ],
                  "weight": [
                    128
                  ],
                  "output": [
                    1696,
                    128
                  ]
                },
                "repeats": 36,
                "matrix_flops": 0,
                "scalar_flops": 870048,
                "special_ops": {
                  "rsqrt": 1696
                },
                "weight_read_bytes": 256,
                "activation_read_bytes": 434176,
                "activation_write_bytes": 434176,
                "notes": "\u6309 FP32 \u884c\u5185\u5f52\u7ea6\u7684\u4ee3\u6570\u8ba1\u6570\uff1brsqrt\u3001\u7c7b\u578b\u8f6c\u6362\u4e0e\u4e34\u65f6 FP32 \u5f20\u91cf\u5206\u5217\uff0f\u4e0d\u63a8\u65ad HBM spill\u3002"
              },
              {
                "name": "k_norm",
                "category": "normalization",
                "shapes": {
                  "input": [
                    424,
                    128
                  ],
                  "weight": [
                    128
                  ],
                  "output": [
                    424,
                    128
                  ]
                },
                "repeats": 36,
                "matrix_flops": 0,
                "scalar_flops": 217512,
                "special_ops": {
                  "rsqrt": 424
                },
                "weight_read_bytes": 256,
                "activation_read_bytes": 108544,
                "activation_write_bytes": 108544,
                "notes": "\u6309 FP32 \u884c\u5185\u5f52\u7ea6\u7684\u4ee3\u6570\u8ba1\u6570\uff1brsqrt\u3001\u7c7b\u578b\u8f6c\u6362\u4e0e\u4e34\u65f6 FP32 \u5f20\u91cf\u5206\u5217\uff0f\u4e0d\u63a8\u65ad HBM spill\u3002"
              },
              {
                "name": "apply_rope",
                "category": "position",
                "shapes": {
                  "Q": [
                    1,
                    32,
                    53,
                    128
                  ],
                  "K": [
                    1,
                    8,
                    53,
                    128
                  ]
                },
                "repeats": 36,
                "matrix_flops": 0,
                "scalar_flops": 814080,
                "special_ops": {
                  "negate": 135680
                },
                "weight_read_bytes": 0,
                "activation_read_bytes": 569856,
                "activation_write_bytes": 542720,
                "notes": "2 multiply + 1 add/\u5143\u7d20\uff0crotate_half \u7b26\u53f7\u7ffb\u8f6c\u5206\u5217\uff1b\u8868\u6309\u6279\uff0f\u5934\u7406\u60f3\u590d\u7528\u3002"
              },
              {
                "name": "kv_append",
                "category": "state",
                "shapes": {
                  "new_K_and_V_each": [
                    1,
                    8,
                    53,
                    128
                  ]
                },
                "repeats": 36,
                "matrix_flops": 0,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 0,
                "activation_read_bytes": 217088,
                "activation_write_bytes": 217088,
                "notes": "\u539f\u4f4d\uff0f\u5206\u9875 append \u8f7d\u8377\uff1b\u4e0d\u5047\u5b9a\u52a8\u6001 torch.cat \u5bf9\u65e7\u7f13\u5b58\u6574\u6bb5\u590d\u5236\u3002"
              },
              {
                "name": "qk",
                "category": "attention",
                "shapes": {
                  "Q": [
                    1,
                    32,
                    53,
                    128
                  ],
                  "K_shared": [
                    1,
                    8,
                    217,
                    128
                  ],
                  "scores_rectangular": [
                    1,
                    32,
                    53,
                    217
                  ]
                },
                "repeats": 36,
                "matrix_flops": 82927616,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 0,
                "activation_read_bytes": 878592,
                "activation_write_bytes": 1472128,
                "notes": "FLOPs \u4ec5\u6709\u6548\u56e0\u679c\u4f4d\u7f6e\uff1b\u8f7d\u8377\u662f\u5047\u5b9a Q/K \u5404\u8bfb\u4e00\u6b21\u3001GQA \u5934\u5171\u4eab\uff0c\u5b8c\u6574\u5206\u6570\u77e9\u9635\u7269\u5316\u3002"
              },
              {
                "name": "score_scale_mask_softmax",
                "category": "softmax",
                "shapes": {
                  "scores": [
                    1,
                    32,
                    53,
                    217
                  ]
                },
                "repeats": 36,
                "matrix_flops": 0,
                "scalar_flops": 1294048,
                "special_ops": {
                  "exp": 323936,
                  "compare_max": 322240,
                  "mask_decisions": 368032
                },
                "weight_read_bytes": 0,
                "activation_read_bytes": 1472128,
                "activation_write_bytes": 1472128,
                "notes": "\u9009\u62e9\u7684\u878d\u5408 scale/mask/softmax \u4ee3\u6570\u5de5\u4f5c\uff1b\u5c4f\u853d\u70b9\u4e0d\u8ba1 exp\u3002\u7269\u5316 FP32 \u9ed8\u8ba4\u6982\u7387\uff1b\u975e\u5177\u4f53 eager trace\u3002"
              },
              {
                "name": "pv",
                "category": "attention",
                "shapes": {
                  "P": [
                    1,
                    32,
                    53,
                    217
                  ],
                  "V_shared": [
                    1,
                    8,
                    217,
                    128
                  ],
                  "output": [
                    1,
                    32,
                    53,
                    128
                  ]
                },
                "repeats": 36,
                "matrix_flops": 82927616,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 0,
                "activation_read_bytes": 1916544,
                "activation_write_bytes": 434176,
                "notes": "PV/AV\uff1a\u5404 Q \u5934\u4ecd\u8ba1\u7b97\uff1bV \u5bb9\u91cf\u4e0d\u4e58 GQA \u590d\u5236\u6570\u3002\u8f7d\u8377\u5047\u5b9a V \u5728\u5934\uff0f\u67e5\u8be2\u4e4b\u95f4\u7406\u60f3\u590d\u7528\u3002"
              },
              {
                "name": "o_proj",
                "category": "linear",
                "shapes": {
                  "input": [
                    53,
                    4096
                  ],
                  "weight_math": [
                    4096,
                    4096
                  ],
                  "weight_storage": [
                    4096,
                    4096
                  ],
                  "output": [
                    53,
                    4096
                  ]
                },
                "repeats": 36,
                "matrix_flops": 1778384896,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 33554432,
                "activation_read_bytes": 434176,
                "activation_write_bytes": 434176,
                "notes": "\u72ec\u7acb GEMM\uff1a\u6743\u91cd\u4e0e\u8f93\u5165\u5404\u8bfb\u4e00\u6b21\u3001\u8f93\u51fa\u5199\u4e00\u6b21\u7684\u64cd\u4f5c\u6570\u8f7d\u8377\uff1b\u4e0d\u9884\u6d4b tile \u91cd\u8bfb\u3002"
              },
              {
                "name": "attention_residual",
                "category": "residual",
                "shapes": {
                  "inputs_each": [
                    53,
                    4096
                  ],
                  "output": [
                    53,
                    4096
                  ]
                },
                "repeats": 36,
                "matrix_flops": 0,
                "scalar_flops": 217088,
                "special_ops": {},
                "weight_read_bytes": 0,
                "activation_read_bytes": 868352,
                "activation_write_bytes": 434176,
                "notes": ""
              },
              {
                "name": "post_attention_layernorm",
                "category": "normalization",
                "shapes": {
                  "input": [
                    53,
                    4096
                  ],
                  "weight": [
                    4096
                  ],
                  "output": [
                    53,
                    4096
                  ]
                },
                "repeats": 36,
                "matrix_flops": 0,
                "scalar_flops": 868405,
                "special_ops": {
                  "rsqrt": 53
                },
                "weight_read_bytes": 8192,
                "activation_read_bytes": 434176,
                "activation_write_bytes": 434176,
                "notes": "\u6309 FP32 \u884c\u5185\u5f52\u7ea6\u7684\u4ee3\u6570\u8ba1\u6570\uff1brsqrt\u3001\u7c7b\u578b\u8f6c\u6362\u4e0e\u4e34\u65f6 FP32 \u5f20\u91cf\u5206\u5217\uff0f\u4e0d\u63a8\u65ad HBM spill\u3002"
              },
              {
                "name": "gate_proj",
                "category": "linear",
                "shapes": {
                  "input": [
                    53,
                    4096
                  ],
                  "weight_math": [
                    4096,
                    12288
                  ],
                  "weight_storage": [
                    12288,
                    4096
                  ],
                  "output": [
                    53,
                    12288
                  ]
                },
                "repeats": 36,
                "matrix_flops": 5335154688,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 100663296,
                "activation_read_bytes": 434176,
                "activation_write_bytes": 1302528,
                "notes": "\u72ec\u7acb GEMM\uff1a\u6743\u91cd\u4e0e\u8f93\u5165\u5404\u8bfb\u4e00\u6b21\u3001\u8f93\u51fa\u5199\u4e00\u6b21\u7684\u64cd\u4f5c\u6570\u8f7d\u8377\uff1b\u4e0d\u9884\u6d4b tile \u91cd\u8bfb\u3002"
              },
              {
                "name": "up_proj",
                "category": "linear",
                "shapes": {
                  "input": [
                    53,
                    4096
                  ],
                  "weight_math": [
                    4096,
                    12288
                  ],
                  "weight_storage": [
                    12288,
                    4096
                  ],
                  "output": [
                    53,
                    12288
                  ]
                },
                "repeats": 36,
                "matrix_flops": 5335154688,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 100663296,
                "activation_read_bytes": 434176,
                "activation_write_bytes": 1302528,
                "notes": "\u72ec\u7acb GEMM\uff1a\u6743\u91cd\u4e0e\u8f93\u5165\u5404\u8bfb\u4e00\u6b21\u3001\u8f93\u51fa\u5199\u4e00\u6b21\u7684\u64cd\u4f5c\u6570\u8f7d\u8377\uff1b\u4e0d\u9884\u6d4b tile \u91cd\u8bfb\u3002"
              },
              {
                "name": "silu_mul",
                "category": "activation",
                "shapes": {
                  "gate": [
                    53,
                    12288
                  ],
                  "up": [
                    53,
                    12288
                  ],
                  "output": [
                    53,
                    12288
                  ]
                },
                "repeats": 36,
                "matrix_flops": 0,
                "scalar_flops": 2605056,
                "special_ops": {
                  "exp": 651264,
                  "negate": 651264
                },
                "weight_read_bytes": 0,
                "activation_read_bytes": 2605056,
                "activation_write_bytes": 1302528,
                "notes": "sigmoid: exp(-x), +1, reciprocal\uff1b\u518d\u4e58 x \u548c up\u3002exp \u4e0e\u53d6\u8d1f\u5206\u5217\u3002"
              },
              {
                "name": "down_proj",
                "category": "linear",
                "shapes": {
                  "input": [
                    53,
                    12288
                  ],
                  "weight_math": [
                    12288,
                    4096
                  ],
                  "weight_storage": [
                    4096,
                    12288
                  ],
                  "output": [
                    53,
                    4096
                  ]
                },
                "repeats": 36,
                "matrix_flops": 5335154688,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 100663296,
                "activation_read_bytes": 1302528,
                "activation_write_bytes": 434176,
                "notes": "\u72ec\u7acb GEMM\uff1a\u6743\u91cd\u4e0e\u8f93\u5165\u5404\u8bfb\u4e00\u6b21\u3001\u8f93\u51fa\u5199\u4e00\u6b21\u7684\u64cd\u4f5c\u6570\u8f7d\u8377\uff1b\u4e0d\u9884\u6d4b tile \u91cd\u8bfb\u3002"
              },
              {
                "name": "ffn_residual",
                "category": "residual",
                "shapes": {
                  "inputs_each": [
                    53,
                    4096
                  ],
                  "output": [
                    53,
                    4096
                  ]
                },
                "repeats": 36,
                "matrix_flops": 0,
                "scalar_flops": 217088,
                "special_ops": {},
                "weight_read_bytes": 0,
                "activation_read_bytes": 868352,
                "activation_write_bytes": 434176,
                "notes": ""
              },
              {
                "name": "final_norm",
                "category": "normalization",
                "shapes": {
                  "input": [
                    53,
                    4096
                  ],
                  "weight": [
                    4096
                  ],
                  "output": [
                    53,
                    4096
                  ]
                },
                "repeats": 1,
                "matrix_flops": 0,
                "scalar_flops": 868405,
                "special_ops": {
                  "rsqrt": 53
                },
                "weight_read_bytes": 8192,
                "activation_read_bytes": 434176,
                "activation_write_bytes": 434176,
                "notes": "\u6309 FP32 \u884c\u5185\u5f52\u7ea6\u7684\u4ee3\u6570\u8ba1\u6570\uff1brsqrt\u3001\u7c7b\u578b\u8f6c\u6362\u4e0e\u4e34\u65f6 FP32 \u5f20\u91cf\u5206\u5217\uff0f\u4e0d\u63a8\u65ad HBM spill\u3002"
              },
              {
                "name": "lm_head",
                "category": "linear",
                "shapes": {
                  "input": [
                    1,
                    4096
                  ],
                  "weight_math": [
                    4096,
                    151936
                  ],
                  "weight_storage": [
                    151936,
                    4096
                  ],
                  "output": [
                    1,
                    151936
                  ]
                },
                "repeats": 1,
                "matrix_flops": 1244659712,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 1244659712,
                "activation_read_bytes": 8192,
                "activation_write_bytes": 303872,
                "notes": "\u72ec\u7acb GEMM\uff1a\u6743\u91cd\u4e0e\u8f93\u5165\u5404\u8bfb\u4e00\u6b21\u3001\u8f93\u51fa\u5199\u4e00\u6b21\u7684\u64cd\u4f5c\u6570\u8f7d\u8377\uff1b\u4e0d\u9884\u6d4b tile \u91cd\u8bfb\u3002"
              }
            ],
            "summary": {
              "parameters": 8190735360,
              "weight_resident_bytes": 16381470720,
              "backbone_projection_ffn_flops": 736251346944,
              "causal_attention_matrix_flops": 5970788352,
              "rectangular_attention_matrix_flops": 6783565824,
              "matrix_flops": 743466795008,
              "scalar_flops": 287854077,
              "special_ops": {
                "sin": 6784,
                "cos": 6784,
                "rsqrt": 80189,
                "negate": 28329984,
                "exp": 35107200,
                "compare_max": 11600640,
                "mask_decisions": 13249152
              },
              "weight_read_once_per_operator_bytes": 15137245184,
              "activation_operand_read_bytes": 530169936,
              "activation_operand_write_bytes": 427614464,
              "kv_bytes_per_token_per_request": 147456,
              "kv_resident_before_bytes": 24182784,
              "kv_resident_after_bytes": 31997952,
              "kv_new_write_bytes": 7815168,
              "kv_existing_history_unique_payload_bytes": 24182784,
              "kv_attention_unique_payload_bytes": 31997952,
              "kv_logical_query_head_operand_bytes": 5970788352,
              "attention_score_tensor_per_layer_bytes": 1472128,
              "materialized_scores_probabilities_io_all_layers_bytes": 211986432,
              "minimum_required_weight_and_kv_bytes": 16413468672
            }
          },
          "state_after_bytes": 31997952
        },
        "decode": null,
        "complete_logical_totals": null,
        "final_state_bytes": null
      }
    },
    {
      "request": 3,
      "application_request_id": "book909chat-capture-3",
      "recorded": {
        "input_tokens": 252,
        "cached_tokens": 213,
        "returned_id_tokens": 26,
        "engine_completion_tokens": 26,
        "output_parts": {
          "reasoning": 0,
          "nonreasoning": 25,
          "delimiter": 0,
          "termination": 1,
          "unknown": 0
        },
        "finish_reason": {
          "type": "stop",
          "matched": 151645
        },
        "worker": "worker0-requests",
        "application_wall_seconds": 0.28321623313240707,
        "engine_e2e_seconds": 0.2816207760479301,
        "tool_wait_seconds": null,
        "previous_same_worker_completion_gap_seconds": 0.0007473889272660017
      },
      "mapping": {
        "prefix_tokens": 213,
        "new_tokens": 39,
        "batch": 1,
        "output_head": "last",
        "sampled_steps": null,
        "decode_forward_calls": null,
        "observed_model_forward_calls": null
      },
      "resources": {
        "prefill": {
          "logical_forward_calls": 1,
          "totals": {
            "matrix_flops": 548374249472,
            "accounted_scalar_flops": 219365055,
            "special_ops": {
              "sin": 4992,
              "cos": 4992,
              "rsqrt": 59007,
              "negate": 20846592,
              "exp": 27720576,
              "compare_max": 10423296,
              "mask_decisions": 11321856
            },
            "known_interfaces": {
              "weight_read_once_per_operator_bytes": 15137130496,
              "activation_operand_read_bytes": 416320368,
              "activation_operand_write_bytes": 327319808,
              "kv_existing_history_unique_payload_bytes": 31408128,
              "kv_new_write_bytes": 5750784
            }
          },
          "source_ledger": {
            "schema_version": 1,
            "calculation": "qwen3-dense-forward",
            "model": "qwen3-8b",
            "scenario": {
              "batch": 1,
              "history": 213,
              "tokens": 39,
              "output_head": "last",
              "weight_bytes": 2,
              "activation_bytes": 2,
              "kv_bytes": 2,
              "score_bytes": 4
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
            "dimensions": {
              "num_hidden_layers": 36,
              "hidden_size": 4096,
              "intermediate_size": 12288,
              "num_attention_heads": 32,
              "num_key_value_heads": 8,
              "head_dim": 128,
              "vocab_size": 151936,
              "tie_word_embeddings": false
            },
            "assumptions": [
              "\u6240\u6709\u8bf7\u6c42\u7b49\u957f\u3001\u76f8\u540c\u4f4d\u7f6e ID\u3001\u65e0\u8de8\u8bf7\u6c42\u524d\u7f00\u5171\u4eab\uff0c\u65e0 TP/PP\uff1bdropout=0 \u63a8\u7406\u3002",
              "\u5168\u6a21\u578b\u6743\u91cd\u7edf\u4e00 weight_bytes \u7684\u6559\u5b66\u683c\u5f0f\uff1b\u4e0d\u7531 torch_dtype \u63a8\u65ad\u5b9e\u9645\u91cf\u5316\u683c\u5f0f\u3002",
              "\u6bcf\u884c operator \u6210\u672c\u4e3a\u4e00\u6b21\u51fa\u73b0\uff0crepeats \u662f\u5c42\u6570\uff1b\u5e03\u5c40\u89c6\u56fe\u4e0e GQA repeat \u4e0d\u989d\u5916\u7269\u5316\u3002",
              "FMA=2\uff1bmatrix_flops \u662f\u6709\u6548\u56e0\u679c\u77e9\u9635\u5de5\u4f5c\uff0cscalar_flops \u662f\u58f0\u660e\u7b97\u6cd5\u7684\u666e\u901a\u7b97\u672f\uff1b\u7279\u6b8a\u51fd\u6570\u53e6\u5217\u3002",
              "operator \u8bfb\u5199\u662f\u72ec\u7acb\u7b97\u5b50\u64cd\u4f5c\u6570\u8f7d\u8377\uff0c\u5206\u6570\uff0f\u6982\u7387\u77e9\u5f62\u7269\u5316\uff1b\u4e0d\u662f\u5b9e\u6d4b HBM\u3001\u4e0d\u662f\u5168\u56fe\u6d41\u91cf\u4e0b\u754c\u3002",
              "\u6807\u91cf\u884c\u5185\u4e2d\u95f4\u91cf\u89c6\u4e3a\u7247\u4e0a\uff1b\u77e9\u5f62\u6ce8\u610f\u529b\u540c\u65f6\u62a5\u544a\uff0cFlashAttention/tile/\u7f13\u5b58\u6d41\u91cf\u7531\u6267\u884c\u4e13\u9898\u53e6\u7b97\u3002",
              "\u4e0d\u8ba1\u91c7\u6837\u3001tokenizer\u3001kernel launch\u3001\u5206\u914d\u5668\u3001KV \u7ba1\u7406\u7d22\u5f15\u53ca\u540e\u7aef\u5de5\u4f5c\u533a\uff1b\u4e0d\u636e\u6b64\u58f0\u79f0\u5b8c\u6574 token \u65f6\u95f4\u3002"
            ],
            "weights": [
              {
                "name": "model.embed_tokens.weight",
                "shape": [
                  151936,
                  4096
                ],
                "copies": 1,
                "note": "",
                "parameters": 622329856,
                "resident_bytes": 1244659712
              },
              {
                "name": "model.layers.{layer}.self_attn.q_proj.weight",
                "shape": [
                  4096,
                  4096
                ],
                "copies": 36,
                "note": "",
                "parameters": 603979776,
                "resident_bytes": 1207959552
              },
              {
                "name": "model.layers.{layer}.self_attn.k_proj.weight",
                "shape": [
                  1024,
                  4096
                ],
                "copies": 36,
                "note": "",
                "parameters": 150994944,
                "resident_bytes": 301989888
              },
              {
                "name": "model.layers.{layer}.self_attn.v_proj.weight",
                "shape": [
                  1024,
                  4096
                ],
                "copies": 36,
                "note": "",
                "parameters": 150994944,
                "resident_bytes": 301989888
              },
              {
                "name": "model.layers.{layer}.self_attn.o_proj.weight",
                "shape": [
                  4096,
                  4096
                ],
                "copies": 36,
                "note": "",
                "parameters": 603979776,
                "resident_bytes": 1207959552
              },
              {
                "name": "model.layers.{layer}.self_attn.q_norm.weight",
                "shape": [
                  128
                ],
                "copies": 36,
                "note": "",
                "parameters": 4608,
                "resident_bytes": 9216
              },
              {
                "name": "model.layers.{layer}.self_attn.k_norm.weight",
                "shape": [
                  128
                ],
                "copies": 36,
                "note": "",
                "parameters": 4608,
                "resident_bytes": 9216
              },
              {
                "name": "model.layers.{layer}.input_layernorm.weight",
                "shape": [
                  4096
                ],
                "copies": 36,
                "note": "",
                "parameters": 147456,
                "resident_bytes": 294912
              },
              {
                "name": "model.layers.{layer}.post_attention_layernorm.weight",
                "shape": [
                  4096
                ],
                "copies": 36,
                "note": "",
                "parameters": 147456,
                "resident_bytes": 294912
              },
              {
                "name": "model.norm.weight",
                "shape": [
                  4096
                ],
                "copies": 1,
                "note": "",
                "parameters": 4096,
                "resident_bytes": 8192
              },
              {
                "name": "lm_head.weight",
                "shape": [
                  151936,
                  4096
                ],
                "copies": 1,
                "note": "",
                "parameters": 622329856,
                "resident_bytes": 1244659712
              },
              {
                "name": "model.layers.{layer}.mlp.gate_proj.weight",
                "shape": [
                  12288,
                  4096
                ],
                "copies": 36,
                "note": "",
                "parameters": 1811939328,
                "resident_bytes": 3623878656
              },
              {
                "name": "model.layers.{layer}.mlp.up_proj.weight",
                "shape": [
                  12288,
                  4096
                ],
                "copies": 36,
                "note": "",
                "parameters": 1811939328,
                "resident_bytes": 3623878656
              },
              {
                "name": "model.layers.{layer}.mlp.down_proj.weight",
                "shape": [
                  4096,
                  12288
                ],
                "copies": 36,
                "note": "",
                "parameters": 1811939328,
                "resident_bytes": 3623878656
              }
            ],
            "operators": [
              {
                "name": "embedding",
                "category": "embedding",
                "shapes": {
                  "indices": [
                    1,
                    39
                  ],
                  "table": [
                    151936,
                    4096
                  ],
                  "output": [
                    39,
                    4096
                  ]
                },
                "repeats": 1,
                "matrix_flops": 0,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 319488,
                "activation_read_bytes": 312,
                "activation_write_bytes": 319488,
                "notes": "\u6bcf token \u4e00\u6b21\u884c\u67e5\u627e\uff0c\u4e0d\u8bfb\u53d6\u6574\u4e2a\u8bcd\u8868\uff1b\u91cd\u590d token \u662f\u5426\u7f13\u5b58\u672a\u5047\u5b9a\u3002int64 \u8f93\u5165\u7d22\u5f15\u3002"
              },
              {
                "name": "rope_table",
                "category": "position",
                "shapes": {
                  "frequencies": [
                    39,
                    64
                  ],
                  "cos_sin_each": [
                    39,
                    128
                  ]
                },
                "repeats": 1,
                "matrix_flops": 0,
                "scalar_flops": 2496,
                "special_ops": {
                  "sin": 4992,
                  "cos": 4992
                },
                "weight_read_bytes": 0,
                "activation_read_bytes": 568,
                "activation_write_bytes": 19968,
                "notes": "\u540c\u4f4d\u7f6e ID \u6279\u5171\u4eab\uff0c\u6240\u6709\u5c42\u590d\u7528\uff1binv_freq \u56fa\u5b9a\u4e0d\u8ba1\u521d\u59cb\u5316\u3002\u53c2\u8003\u8def\u5f84\u590d\u5236\u9891\u7387\u540e\u6c42 sin/cos\uff1b\u8f6c\u6362\u53e6\u8ba1\u3002"
              },
              {
                "name": "input_layernorm",
                "category": "normalization",
                "shapes": {
                  "input": [
                    39,
                    4096
                  ],
                  "weight": [
                    4096
                  ],
                  "output": [
                    39,
                    4096
                  ]
                },
                "repeats": 36,
                "matrix_flops": 0,
                "scalar_flops": 639015,
                "special_ops": {
                  "rsqrt": 39
                },
                "weight_read_bytes": 8192,
                "activation_read_bytes": 319488,
                "activation_write_bytes": 319488,
                "notes": "\u6309 FP32 \u884c\u5185\u5f52\u7ea6\u7684\u4ee3\u6570\u8ba1\u6570\uff1brsqrt\u3001\u7c7b\u578b\u8f6c\u6362\u4e0e\u4e34\u65f6 FP32 \u5f20\u91cf\u5206\u5217\uff0f\u4e0d\u63a8\u65ad HBM spill\u3002"
              },
              {
                "name": "q_proj",
                "category": "linear",
                "shapes": {
                  "input": [
                    39,
                    4096
                  ],
                  "weight_math": [
                    4096,
                    4096
                  ],
                  "weight_storage": [
                    4096,
                    4096
                  ],
                  "output": [
                    39,
                    4096
                  ]
                },
                "repeats": 36,
                "matrix_flops": 1308622848,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 33554432,
                "activation_read_bytes": 319488,
                "activation_write_bytes": 319488,
                "notes": "\u72ec\u7acb GEMM\uff1a\u6743\u91cd\u4e0e\u8f93\u5165\u5404\u8bfb\u4e00\u6b21\u3001\u8f93\u51fa\u5199\u4e00\u6b21\u7684\u64cd\u4f5c\u6570\u8f7d\u8377\uff1b\u4e0d\u9884\u6d4b tile \u91cd\u8bfb\u3002"
              },
              {
                "name": "k_proj",
                "category": "linear",
                "shapes": {
                  "input": [
                    39,
                    4096
                  ],
                  "weight_math": [
                    4096,
                    1024
                  ],
                  "weight_storage": [
                    1024,
                    4096
                  ],
                  "output": [
                    39,
                    1024
                  ]
                },
                "repeats": 36,
                "matrix_flops": 327155712,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 8388608,
                "activation_read_bytes": 319488,
                "activation_write_bytes": 79872,
                "notes": "\u72ec\u7acb GEMM\uff1a\u6743\u91cd\u4e0e\u8f93\u5165\u5404\u8bfb\u4e00\u6b21\u3001\u8f93\u51fa\u5199\u4e00\u6b21\u7684\u64cd\u4f5c\u6570\u8f7d\u8377\uff1b\u4e0d\u9884\u6d4b tile \u91cd\u8bfb\u3002"
              },
              {
                "name": "v_proj",
                "category": "linear",
                "shapes": {
                  "input": [
                    39,
                    4096
                  ],
                  "weight_math": [
                    4096,
                    1024
                  ],
                  "weight_storage": [
                    1024,
                    4096
                  ],
                  "output": [
                    39,
                    1024
                  ]
                },
                "repeats": 36,
                "matrix_flops": 327155712,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 8388608,
                "activation_read_bytes": 319488,
                "activation_write_bytes": 79872,
                "notes": "\u72ec\u7acb GEMM\uff1a\u6743\u91cd\u4e0e\u8f93\u5165\u5404\u8bfb\u4e00\u6b21\u3001\u8f93\u51fa\u5199\u4e00\u6b21\u7684\u64cd\u4f5c\u6570\u8f7d\u8377\uff1b\u4e0d\u9884\u6d4b tile \u91cd\u8bfb\u3002"
              },
              {
                "name": "q_norm",
                "category": "normalization",
                "shapes": {
                  "input": [
                    1248,
                    128
                  ],
                  "weight": [
                    128
                  ],
                  "output": [
                    1248,
                    128
                  ]
                },
                "repeats": 36,
                "matrix_flops": 0,
                "scalar_flops": 640224,
                "special_ops": {
                  "rsqrt": 1248
                },
                "weight_read_bytes": 256,
                "activation_read_bytes": 319488,
                "activation_write_bytes": 319488,
                "notes": "\u6309 FP32 \u884c\u5185\u5f52\u7ea6\u7684\u4ee3\u6570\u8ba1\u6570\uff1brsqrt\u3001\u7c7b\u578b\u8f6c\u6362\u4e0e\u4e34\u65f6 FP32 \u5f20\u91cf\u5206\u5217\uff0f\u4e0d\u63a8\u65ad HBM spill\u3002"
              },
              {
                "name": "k_norm",
                "category": "normalization",
                "shapes": {
                  "input": [
                    312,
                    128
                  ],
                  "weight": [
                    128
                  ],
                  "output": [
                    312,
                    128
                  ]
                },
                "repeats": 36,
                "matrix_flops": 0,
                "scalar_flops": 160056,
                "special_ops": {
                  "rsqrt": 312
                },
                "weight_read_bytes": 256,
                "activation_read_bytes": 79872,
                "activation_write_bytes": 79872,
                "notes": "\u6309 FP32 \u884c\u5185\u5f52\u7ea6\u7684\u4ee3\u6570\u8ba1\u6570\uff1brsqrt\u3001\u7c7b\u578b\u8f6c\u6362\u4e0e\u4e34\u65f6 FP32 \u5f20\u91cf\u5206\u5217\uff0f\u4e0d\u63a8\u65ad HBM spill\u3002"
              },
              {
                "name": "apply_rope",
                "category": "position",
                "shapes": {
                  "Q": [
                    1,
                    32,
                    39,
                    128
                  ],
                  "K": [
                    1,
                    8,
                    39,
                    128
                  ]
                },
                "repeats": 36,
                "matrix_flops": 0,
                "scalar_flops": 599040,
                "special_ops": {
                  "negate": 99840
                },
                "weight_read_bytes": 0,
                "activation_read_bytes": 419328,
                "activation_write_bytes": 399360,
                "notes": "2 multiply + 1 add/\u5143\u7d20\uff0crotate_half \u7b26\u53f7\u7ffb\u8f6c\u5206\u5217\uff1b\u8868\u6309\u6279\uff0f\u5934\u7406\u60f3\u590d\u7528\u3002"
              },
              {
                "name": "kv_append",
                "category": "state",
                "shapes": {
                  "new_K_and_V_each": [
                    1,
                    8,
                    39,
                    128
                  ]
                },
                "repeats": 36,
                "matrix_flops": 0,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 0,
                "activation_read_bytes": 159744,
                "activation_write_bytes": 159744,
                "notes": "\u539f\u4f4d\uff0f\u5206\u9875 append \u8f7d\u8377\uff1b\u4e0d\u5047\u5b9a\u52a8\u6001 torch.cat \u5bf9\u65e7\u7f13\u5b58\u6574\u6bb5\u590d\u5236\u3002"
              },
              {
                "name": "qk",
                "category": "attention",
                "shapes": {
                  "Q": [
                    1,
                    32,
                    39,
                    128
                  ],
                  "K_shared": [
                    1,
                    8,
                    252,
                    128
                  ],
                  "scores_rectangular": [
                    1,
                    32,
                    39,
                    252
                  ]
                },
                "repeats": 36,
                "matrix_flops": 74440704,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 0,
                "activation_read_bytes": 835584,
                "activation_write_bytes": 1257984,
                "notes": "FLOPs \u4ec5\u6709\u6548\u56e0\u679c\u4f4d\u7f6e\uff1b\u8f7d\u8377\u662f\u5047\u5b9a Q/K \u5404\u8bfb\u4e00\u6b21\u3001GQA \u5934\u5171\u4eab\uff0c\u5b8c\u6574\u5206\u6570\u77e9\u9635\u7269\u5316\u3002"
              },
              {
                "name": "score_scale_mask_softmax",
                "category": "softmax",
                "shapes": {
                  "scores": [
                    1,
                    32,
                    39,
                    252
                  ]
                },
                "repeats": 36,
                "matrix_flops": 0,
                "scalar_flops": 1161888,
                "special_ops": {
                  "exp": 290784,
                  "compare_max": 289536,
                  "mask_decisions": 314496
                },
                "weight_read_bytes": 0,
                "activation_read_bytes": 1257984,
                "activation_write_bytes": 1257984,
                "notes": "\u9009\u62e9\u7684\u878d\u5408 scale/mask/softmax \u4ee3\u6570\u5de5\u4f5c\uff1b\u5c4f\u853d\u70b9\u4e0d\u8ba1 exp\u3002\u7269\u5316 FP32 \u9ed8\u8ba4\u6982\u7387\uff1b\u975e\u5177\u4f53 eager trace\u3002"
              },
              {
                "name": "pv",
                "category": "attention",
                "shapes": {
                  "P": [
                    1,
                    32,
                    39,
                    252
                  ],
                  "V_shared": [
                    1,
                    8,
                    252,
                    128
                  ],
                  "output": [
                    1,
                    32,
                    39,
                    128
                  ]
                },
                "repeats": 36,
                "matrix_flops": 74440704,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 0,
                "activation_read_bytes": 1774080,
                "activation_write_bytes": 319488,
                "notes": "PV/AV\uff1a\u5404 Q \u5934\u4ecd\u8ba1\u7b97\uff1bV \u5bb9\u91cf\u4e0d\u4e58 GQA \u590d\u5236\u6570\u3002\u8f7d\u8377\u5047\u5b9a V \u5728\u5934\uff0f\u67e5\u8be2\u4e4b\u95f4\u7406\u60f3\u590d\u7528\u3002"
              },
              {
                "name": "o_proj",
                "category": "linear",
                "shapes": {
                  "input": [
                    39,
                    4096
                  ],
                  "weight_math": [
                    4096,
                    4096
                  ],
                  "weight_storage": [
                    4096,
                    4096
                  ],
                  "output": [
                    39,
                    4096
                  ]
                },
                "repeats": 36,
                "matrix_flops": 1308622848,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 33554432,
                "activation_read_bytes": 319488,
                "activation_write_bytes": 319488,
                "notes": "\u72ec\u7acb GEMM\uff1a\u6743\u91cd\u4e0e\u8f93\u5165\u5404\u8bfb\u4e00\u6b21\u3001\u8f93\u51fa\u5199\u4e00\u6b21\u7684\u64cd\u4f5c\u6570\u8f7d\u8377\uff1b\u4e0d\u9884\u6d4b tile \u91cd\u8bfb\u3002"
              },
              {
                "name": "attention_residual",
                "category": "residual",
                "shapes": {
                  "inputs_each": [
                    39,
                    4096
                  ],
                  "output": [
                    39,
                    4096
                  ]
                },
                "repeats": 36,
                "matrix_flops": 0,
                "scalar_flops": 159744,
                "special_ops": {},
                "weight_read_bytes": 0,
                "activation_read_bytes": 638976,
                "activation_write_bytes": 319488,
                "notes": ""
              },
              {
                "name": "post_attention_layernorm",
                "category": "normalization",
                "shapes": {
                  "input": [
                    39,
                    4096
                  ],
                  "weight": [
                    4096
                  ],
                  "output": [
                    39,
                    4096
                  ]
                },
                "repeats": 36,
                "matrix_flops": 0,
                "scalar_flops": 639015,
                "special_ops": {
                  "rsqrt": 39
                },
                "weight_read_bytes": 8192,
                "activation_read_bytes": 319488,
                "activation_write_bytes": 319488,
                "notes": "\u6309 FP32 \u884c\u5185\u5f52\u7ea6\u7684\u4ee3\u6570\u8ba1\u6570\uff1brsqrt\u3001\u7c7b\u578b\u8f6c\u6362\u4e0e\u4e34\u65f6 FP32 \u5f20\u91cf\u5206\u5217\uff0f\u4e0d\u63a8\u65ad HBM spill\u3002"
              },
              {
                "name": "gate_proj",
                "category": "linear",
                "shapes": {
                  "input": [
                    39,
                    4096
                  ],
                  "weight_math": [
                    4096,
                    12288
                  ],
                  "weight_storage": [
                    12288,
                    4096
                  ],
                  "output": [
                    39,
                    12288
                  ]
                },
                "repeats": 36,
                "matrix_flops": 3925868544,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 100663296,
                "activation_read_bytes": 319488,
                "activation_write_bytes": 958464,
                "notes": "\u72ec\u7acb GEMM\uff1a\u6743\u91cd\u4e0e\u8f93\u5165\u5404\u8bfb\u4e00\u6b21\u3001\u8f93\u51fa\u5199\u4e00\u6b21\u7684\u64cd\u4f5c\u6570\u8f7d\u8377\uff1b\u4e0d\u9884\u6d4b tile \u91cd\u8bfb\u3002"
              },
              {
                "name": "up_proj",
                "category": "linear",
                "shapes": {
                  "input": [
                    39,
                    4096
                  ],
                  "weight_math": [
                    4096,
                    12288
                  ],
                  "weight_storage": [
                    12288,
                    4096
                  ],
                  "output": [
                    39,
                    12288
                  ]
                },
                "repeats": 36,
                "matrix_flops": 3925868544,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 100663296,
                "activation_read_bytes": 319488,
                "activation_write_bytes": 958464,
                "notes": "\u72ec\u7acb GEMM\uff1a\u6743\u91cd\u4e0e\u8f93\u5165\u5404\u8bfb\u4e00\u6b21\u3001\u8f93\u51fa\u5199\u4e00\u6b21\u7684\u64cd\u4f5c\u6570\u8f7d\u8377\uff1b\u4e0d\u9884\u6d4b tile \u91cd\u8bfb\u3002"
              },
              {
                "name": "silu_mul",
                "category": "activation",
                "shapes": {
                  "gate": [
                    39,
                    12288
                  ],
                  "up": [
                    39,
                    12288
                  ],
                  "output": [
                    39,
                    12288
                  ]
                },
                "repeats": 36,
                "matrix_flops": 0,
                "scalar_flops": 1916928,
                "special_ops": {
                  "exp": 479232,
                  "negate": 479232
                },
                "weight_read_bytes": 0,
                "activation_read_bytes": 1916928,
                "activation_write_bytes": 958464,
                "notes": "sigmoid: exp(-x), +1, reciprocal\uff1b\u518d\u4e58 x \u548c up\u3002exp \u4e0e\u53d6\u8d1f\u5206\u5217\u3002"
              },
              {
                "name": "down_proj",
                "category": "linear",
                "shapes": {
                  "input": [
                    39,
                    12288
                  ],
                  "weight_math": [
                    12288,
                    4096
                  ],
                  "weight_storage": [
                    4096,
                    12288
                  ],
                  "output": [
                    39,
                    4096
                  ]
                },
                "repeats": 36,
                "matrix_flops": 3925868544,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 100663296,
                "activation_read_bytes": 958464,
                "activation_write_bytes": 319488,
                "notes": "\u72ec\u7acb GEMM\uff1a\u6743\u91cd\u4e0e\u8f93\u5165\u5404\u8bfb\u4e00\u6b21\u3001\u8f93\u51fa\u5199\u4e00\u6b21\u7684\u64cd\u4f5c\u6570\u8f7d\u8377\uff1b\u4e0d\u9884\u6d4b tile \u91cd\u8bfb\u3002"
              },
              {
                "name": "ffn_residual",
                "category": "residual",
                "shapes": {
                  "inputs_each": [
                    39,
                    4096
                  ],
                  "output": [
                    39,
                    4096
                  ]
                },
                "repeats": 36,
                "matrix_flops": 0,
                "scalar_flops": 159744,
                "special_ops": {},
                "weight_read_bytes": 0,
                "activation_read_bytes": 638976,
                "activation_write_bytes": 319488,
                "notes": ""
              },
              {
                "name": "final_norm",
                "category": "normalization",
                "shapes": {
                  "input": [
                    39,
                    4096
                  ],
                  "weight": [
                    4096
                  ],
                  "output": [
                    39,
                    4096
                  ]
                },
                "repeats": 1,
                "matrix_flops": 0,
                "scalar_flops": 639015,
                "special_ops": {
                  "rsqrt": 39
                },
                "weight_read_bytes": 8192,
                "activation_read_bytes": 319488,
                "activation_write_bytes": 319488,
                "notes": "\u6309 FP32 \u884c\u5185\u5f52\u7ea6\u7684\u4ee3\u6570\u8ba1\u6570\uff1brsqrt\u3001\u7c7b\u578b\u8f6c\u6362\u4e0e\u4e34\u65f6 FP32 \u5f20\u91cf\u5206\u5217\uff0f\u4e0d\u63a8\u65ad HBM spill\u3002"
              },
              {
                "name": "lm_head",
                "category": "linear",
                "shapes": {
                  "input": [
                    1,
                    4096
                  ],
                  "weight_math": [
                    4096,
                    151936
                  ],
                  "weight_storage": [
                    151936,
                    4096
                  ],
                  "output": [
                    1,
                    151936
                  ]
                },
                "repeats": 1,
                "matrix_flops": 1244659712,
                "scalar_flops": 0,
                "special_ops": {},
                "weight_read_bytes": 1244659712,
                "activation_read_bytes": 8192,
                "activation_write_bytes": 303872,
                "notes": "\u72ec\u7acb GEMM\uff1a\u6743\u91cd\u4e0e\u8f93\u5165\u5404\u8bfb\u4e00\u6b21\u3001\u8f93\u51fa\u5199\u4e00\u6b21\u7684\u64cd\u4f5c\u6570\u8f7d\u8377\uff1b\u4e0d\u9884\u6d4b tile \u91cd\u8bfb\u3002"
              }
            ],
            "summary": {
              "parameters": 8190735360,
              "weight_resident_bytes": 16381470720,
              "backbone_projection_ffn_flops": 541769859072,
              "causal_attention_matrix_flops": 5359730688,
              "rectangular_attention_matrix_flops": 5796790272,
              "matrix_flops": 548374249472,
              "scalar_flops": 219365055,
              "special_ops": {
                "sin": 4992,
                "cos": 4992,
                "rsqrt": 59007,
                "negate": 20846592,
                "exp": 27720576,
                "compare_max": 10423296,
                "mask_decisions": 11321856
              },
              "weight_read_once_per_operator_bytes": 15137130496,
              "activation_operand_read_bytes": 416320368,
              "activation_operand_write_bytes": 327319808,
              "kv_bytes_per_token_per_request": 147456,
              "kv_resident_before_bytes": 31408128,
              "kv_resident_after_bytes": 37158912,
              "kv_new_write_bytes": 5750784,
              "kv_existing_history_unique_payload_bytes": 31408128,
              "kv_attention_unique_payload_bytes": 37158912,
              "kv_logical_query_head_operand_bytes": 5359730688,
              "attention_score_tensor_per_layer_bytes": 1257984,
              "materialized_scores_probabilities_io_all_layers_bytes": 181149696,
              "minimum_required_weight_and_kv_bytes": 16418629632
            }
          },
          "state_after_bytes": 37158912
        },
        "decode": null,
        "complete_logical_totals": null,
        "final_state_bytes": null
      }
    }
  ],
  "summary": {
    "recorded_application_calls": 4,
    "recorded_input_tokens": 753,
    "recorded_cached_tokens": 489,
    "recorded_returned_ids": 79,
    "logical_prefill_totals": {
      "matrix_flops": 3692317638656,
      "accounted_scalar_flops": 1357530696,
      "special_ops": {
        "sin": 33792,
        "cos": 33792,
        "rsqrt": 399432,
        "negate": 141115392,
        "exp": 155796480,
        "compare_max": 38707200,
        "mask_decisions": 50910336
      },
      "known_interfaces": {
        "weight_read_once_per_operator_bytes": 60549406720,
        "activation_operand_read_bytes": 2471803008,
        "activation_operand_write_bytes": 2009022464,
        "kv_existing_history_unique_payload_bytes": 72105984,
        "kv_new_write_bytes": 38928384
      }
    },
    "conditional_complete_logical_totals": null,
    "observed_model_forward_calls": null,
    "conditional_serial_forward_calls": null,
    "recorded_application_wall_sum_seconds": 0.8657605659682304,
    "tool_wait_sum_seconds": null,
    "simultaneous_kv_peak_bytes": null,
    "actual_hbm_bytes": null,
    "actual_gpu_runtime_seconds": null
  },
  "scope": [
    "Four original sealed Chat captures only. No routing replay is a new natural request, and no model execution occurred during this calculation.",
    "S is recorded cached-token count interpreted as a logical retained prefix, P=N-S. This does not prove KV page identity, actual prefill chunks or backend matrix scheduling. Original model snapshot and BF16 arguments are checked.",
    "Returned IDs and completion counters include EOS. unknown_steps preserves sampled/model-step counts as null. returned_ids_serial_policy explicitly assumes one serial sampled step per returned ID, G outputs from one logical prefill and G-1 single-token decodes.",
    "Last-position generation head is explicit in every forward. The final emitted ID has no additional forward/KV append. EOS is not subtracted from sampled steps in the conditional policy.",
    "Operator interfaces and scalar/special work retain public Qwen8 logical assumptions, not measured HBM or instruction counts. State is per-call endpoint, not summed into a simultaneous residency peak.",
    "Recorded request and engine walls remain separate from resources and tool nulls. Completion-to-send gaps are not per-block reuse distance or human think time. No throughput or GPU latency is derived.",
    "To reconstruct observed model calls, log admitted prefix/pages, each scheduled forward input, prefill chunks, sampled/accepted/retracted IDs, speculative/beam mode, logits rows, final-ID processing, and KV lifetime. The archived application records alone do not provide that trace."
  ]
}
```
