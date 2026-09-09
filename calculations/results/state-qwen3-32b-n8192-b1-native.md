# model-state — qwen3-32b

输入：`{"batch": 1, "element_bytes": 2, "length": 8192, "mla_path": "compact", "recurrent_bytes": 4}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| resident_bytes | 2,147,483,648 |
| selected_history_payload_bytes | 2,147,483,648 |
| next_token_append_bytes | 262,144 |
| kv_bytes_per_token_per_request | 262,144 |

计量条件：

- N 为已处理 token 数；读取对应可见长度 N 的最后一条查询，append 对应第 N+1 个 token。
- 字节为未切分、无前缀共享的逻辑载荷；KV 各记录一次复用不代表实测 HBM。
- 不包含权重、attention 临时工作区、分配器对齐、并行复制、前缀检查点副本。

固定来源：

- [configs/models/qwen3-32b/config.json](https://huggingface.co/Qwen/Qwen3-32B/resolve/9216db5781bf21249d130ec9da846c4624c16137/config.json)，SHA256 `97e295b63283935788fac5e4f8860862a56d4089538cafc93f0431f2ebe483bb`。
- [sources/qwen3-32b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-32B/resolve/9216db5781bf21249d130ec9da846c4624c16137/model.safetensors.index.json)，SHA256 `bed42c6c55274bc08a1f616bceb3bcb84b3f02cb6584c573bd18c6519291ecd0`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
