# Qwen3.6-35B-A3B 必要容量筛选

| 组成 | bytes |
|---|---:|
| selected_checkpoint_weight_bytes | 69321221376 |
| full_attention_kv_bytes | 671088640 |
| recurrent_fp32_bytes | 62914560 |
| convolution_bf16_bytes | 1966080 |
| declared_reserve_bytes | 2147483648 |

| 设备 | 名义 bytes | 必要预算通过 | 剩余 bytes |
|---|---:|---|---:|
| rtx4090 | 24000000000 | False | -48204674304 |
| rtx5090 | 32000000000 | False | -40204674304 |
| h100-sxm | 80000000000 | True | 7795325696 |
| rtx-pro6000-blackwell-ws | 96000000000 | True | 23795325696 |
| m2-max-38gpu-96gb | 96000000000 | True | 23795325696 |

全部路由专家常驻；A3B不是驻留权重大小。默认仅基础文本权重，选项可保留视觉/MTP文件中的全部权重，但不会凭此假装已计它们的执行状态。
所有原始张量为BF16存储；线性递推状态按声明参考路径FP32，卷积槽与完整attention KV按BF16。运行时权重重排、转换、分配器和临时峰值未测。
length是追加后的完整attention历史长度；递推状态与卷积槽不随历史线性增长。B个请求独立，不假定前缀共享。
reserve_bytes为明确的额外预算假设，默认2GiB，并非测得workspace。官方名义GB按十进制计，不能等同可分配空间；Mac还与CPU/OS共享。
超过预算即可在这些假设下排除；通过必要容量筛选不证明能加载、达到延迟目标或满足质量。此处没有低位量化、卸载或多卡切分。

```json
{
  "schema_version": 1,
  "calculation": "qwen36-capacity",
  "model": "qwen3.6-35b-a3b",
  "scenario": {
    "batch": 1,
    "length": 32768,
    "reserve_bytes": 2147483648,
    "include_auxiliary_weights": false
  },
  "sources": [
    {
      "file": "sources/qwen3.6-35b-a3b/headers/model-00001-of-00026.safetensors.json",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00001-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "69c3b8c645af1e7abc1cd7b02224c7e68571e10e2c15d3b638173d42aa407995"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/headers/model-00002-of-00026.safetensors.json",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00002-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "88769fdfc34f169920bc4130ef6b601399c05c3a5931a5248a6be39750f208b5"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/headers/model-00003-of-00026.safetensors.json",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00003-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "6c01d14e2c844939e3dbc5bee19bd28d92386ad31ac8cdc3ad4df41bc90c2c98"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/headers/model-00004-of-00026.safetensors.json",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00004-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "ffab4a1a75b0153c17b484834fd6ea40f80676647747b912e2510c03ecb98efe"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/headers/model-00005-of-00026.safetensors.json",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00005-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "aaf0d94d73352c5a48c09e90b8e99c5195c45f12c8940d7c837b4983ec39b38f"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/headers/model-00006-of-00026.safetensors.json",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00006-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "77a2eb60895810cb154288dfbbf0298fc99a3ca3e4b7e22c4390a4496609ccd2"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/headers/model-00007-of-00026.safetensors.json",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00007-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "9bacee631f1fafe58cea09187ea5c3e9ae085f5f78707527045bfce64c9ef6cb"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/headers/model-00008-of-00026.safetensors.json",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00008-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "4e58096750bf0150cd80e780de88fb080389cc95fafe057da009555c3a9a0c1d"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/headers/model-00009-of-00026.safetensors.json",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00009-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "06e29dde0121e46d9fe0530baf4871e926d834b9a2efecc746f8c8c20cc4e7ef"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/headers/model-00010-of-00026.safetensors.json",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00010-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "116723a5280f4507573ea64a68604c7846fc4a555d93a8c99cffc2625db8847a"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/headers/model-00011-of-00026.safetensors.json",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00011-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "ca75540855f6f3af531033c80d2912bb2e17d5546e3c264a850a7ddfbcce2e43"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/headers/model-00012-of-00026.safetensors.json",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00012-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "aac84bea9971f30e92c21adbd44cf742fbfc2352817e8cc3ab5749c8a3da55d5"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/headers/model-00013-of-00026.safetensors.json",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00013-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "9503e8cb9c3de395ab148a23f40590d96a75f07853609c69b18e304cbfb02115"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/headers/model-00014-of-00026.safetensors.json",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00014-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "80f55eaac4fc6cbb9ed41a26e8fa54e7177eae6ee71cce8f5132d41a072ef35b"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/headers/model-00015-of-00026.safetensors.json",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00015-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "89cad0602536b1fad60d504f0f99ab269270a0fa3f0f5e4003b2fc9ec3e70c49"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/headers/model-00016-of-00026.safetensors.json",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00016-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "8fd865ef18ecb362fa5592f9a4297e1036090a0277737dcf4b231849874bc145"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/headers/model-00017-of-00026.safetensors.json",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00017-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "ab99b3f6f9e5cd5fe5f8a017ab6c5078da087db3d73ec7cb1321dbf4d18e5293"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/headers/model-00018-of-00026.safetensors.json",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00018-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "d8b3d32008271cc91f2e5511b22a67f39f82ad26d7c984e929daf3702c39179e"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/headers/model-00019-of-00026.safetensors.json",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00019-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "b56714b8357f44802a2bef55e08c4392b19cca45a73777f3f10257a14e51a81b"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/headers/model-00020-of-00026.safetensors.json",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00020-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "87878657f90f825b71f580755dbd0bd5826cf535255c97e01338e37b9a88f73d"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/headers/model-00021-of-00026.safetensors.json",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00021-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "24cbcb695d13a3f6d697b60a754efe2b8272f05b9a86634c04af6093027cfc47"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/headers/model-00022-of-00026.safetensors.json",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00022-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "9cf268df8fab5b4cf19e3a218d7cc775307d5a660df8af646f9aeb7a6110229e"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/headers/model-00023-of-00026.safetensors.json",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00023-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "60709d278824f306799b8a00555932403a226cf493d9fcc713310210c7eccae8"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/headers/model-00024-of-00026.safetensors.json",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00024-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "e2407bcbb1772cbed34cfff2f5c6154479034b80f5bad1d8ed979cfab857e342"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/headers/model-00025-of-00026.safetensors.json",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00025-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "a1213b03752357c4ef03c1fb806bc445f5230de6e4c70fe252328ad707322d39"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/headers/model-00026-of-00026.safetensors.json",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00026-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "6f2afede1820106eca9e38a4c24f8da679a79dc841a94a30d90ab32a16f402ec"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/model/LICENSE",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/LICENSE",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "50cbab8a892c5f2993b8c7351a99182507472def3b1374558308605d99b86b32"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/model/README.md",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/README.md",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "c4ddaa065649ff6352648f64747a16eda31726f3e34add94ce04abb461c77b75"
    },
    {
      "file": "configs/models/qwen3.6-35b-a3b/config.json",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/config.json",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "93a4693fa9d8392fbfccd4b3c9873f4bfdcb14fdede978b123d07d19675efe99"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/model/generation_config.json",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/generation_config.json",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "e70c136c1b78ddc1fb0905bac8e733a4dc448d4f852a5dd75143fffc70be550e"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/model/model.safetensors.index.json",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model.safetensors.index.json",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "41b9356101ebf8e7519e150dc811f80c4226e727301fbb032b890f006ed0be83"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/model/preprocessor_config.json",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/preprocessor_config.json",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "27225450ac9c6529872ee1924fcb0962ff5634834f817040f444118116f4e516"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/model/tokenizer_config.json",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/tokenizer_config.json",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "5186f0defcd7f232382c7f0aebcd2252d073bb921ab240e407b7ae8745d2b29b"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/model/video_preprocessor_config.json",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/video_preprocessor_config.json",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "7768af27c1fafa9cc9011c1dc20067e03f8915e03b63504550e11d5066986d13"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/prefixes/model-00001-of-00026.safetensors.length",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00001-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "446c0f1fb415466ced0c7ef638d55ede3501d50fa0864f9a656e8ac9f3d02f86"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/prefixes/model-00002-of-00026.safetensors.length",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00002-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "f532133eefa22cd8d607e207e598921a3a3c856318e4441012ba330d412ca051"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/prefixes/model-00003-of-00026.safetensors.length",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00003-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "1efe4258121a8103faf852bced0d4b614742bb5e22fcf90f5187b12fc60761f2"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/prefixes/model-00004-of-00026.safetensors.length",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00004-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "81232e6fc122c8559e3603438f029923d93444c8db238764978ed84827a9bb81"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/prefixes/model-00005-of-00026.safetensors.length",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00005-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "1efe4258121a8103faf852bced0d4b614742bb5e22fcf90f5187b12fc60761f2"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/prefixes/model-00006-of-00026.safetensors.length",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00006-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "e39295bf82392aaccb5f571e53c4d02639f122af1adc3ee450fb2b2777e4fd7d"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/prefixes/model-00007-of-00026.safetensors.length",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00007-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "14e2502d0b04c63c56fb849cbd57c722876c1f8e025e252ecefbb0e0381f1fbe"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/prefixes/model-00008-of-00026.safetensors.length",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00008-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "6ce9601c6e5b9102802c840fbd354a967f5a0ee35616a8a47730cacd27dbce1c"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/prefixes/model-00009-of-00026.safetensors.length",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00009-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "5cf4e36e55b7e978342b4da5afb35f9b5bda5db08cee6abdf7333660f4688cc5"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/prefixes/model-00010-of-00026.safetensors.length",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00010-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "e39295bf82392aaccb5f571e53c4d02639f122af1adc3ee450fb2b2777e4fd7d"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/prefixes/model-00011-of-00026.safetensors.length",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00011-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "d5716ff5ad4dbe6b61258a23d71b8b14f77c816dbcec6e059a8fb359998ca03d"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/prefixes/model-00012-of-00026.safetensors.length",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00012-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "e39295bf82392aaccb5f571e53c4d02639f122af1adc3ee450fb2b2777e4fd7d"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/prefixes/model-00013-of-00026.safetensors.length",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00013-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "d5716ff5ad4dbe6b61258a23d71b8b14f77c816dbcec6e059a8fb359998ca03d"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/prefixes/model-00014-of-00026.safetensors.length",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00014-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "7e3e6caf3f95b6efd9f2abd90a46fc57b26b3dcc10753c359d716ae5f2bd8030"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/prefixes/model-00015-of-00026.safetensors.length",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00015-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "0c7919cd26fdfbba492bfa0eaf2ff77aa349c2175d0f1ca7025a2182549fdb52"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/prefixes/model-00016-of-00026.safetensors.length",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00016-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "bcc0e7d554bfb67e6dfaa82a25ef2a617173bede4c2416a211eb9600a67e9e82"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/prefixes/model-00017-of-00026.safetensors.length",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00017-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "320b0991dca4866e2b5119bf56d78eaf905d0486d48a9fb628b5706aaff30c72"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/prefixes/model-00018-of-00026.safetensors.length",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00018-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "e39295bf82392aaccb5f571e53c4d02639f122af1adc3ee450fb2b2777e4fd7d"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/prefixes/model-00019-of-00026.safetensors.length",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00019-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "f41eca22268832e0ea934317cd48cbb7b12583b482191eda46808fda402b57d3"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/prefixes/model-00020-of-00026.safetensors.length",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00020-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "1da0ac8751a276da403b2b8205fb4a04633ce8cfa428ac738af3ccbb8f37feff"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/prefixes/model-00021-of-00026.safetensors.length",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00021-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "fcc5388b428e87f8472244907f55aecb1422b707abfd961e204c981ca68fcd45"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/prefixes/model-00022-of-00026.safetensors.length",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00022-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "f25627ac25cfe3995df9d19c5873d0b5aa39c58cd1969746e4777158bd485eb9"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/prefixes/model-00023-of-00026.safetensors.length",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00023-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "6ec0f1032522ad00595cc34a92037af62d006b04dccf4c7de4cd1798bf9af605"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/prefixes/model-00024-of-00026.safetensors.length",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00024-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "f25627ac25cfe3995df9d19c5873d0b5aa39c58cd1969746e4777158bd485eb9"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/prefixes/model-00025-of-00026.safetensors.length",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00025-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "2f686e9145e9adc55a483eba50fcd2e3e903cfe03edef06dc03f14eecae24657"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/prefixes/model-00026-of-00026.safetensors.length",
      "url": "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model-00026-of-00026.safetensors",
      "revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
      "sha256": "fd284465e9f27cbe96ea41fd0c3c6833c4221b3074f992f784dfd5f298f8fd78"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/transformers/src/transformers/cache_utils.py",
      "url": "https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/src/transformers/cache_utils.py",
      "revision": "cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55",
      "sha256": "702144bb44553f6339ea1bf23c8205a708bb5f8c7c09cb3a2db484182646743c"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/transformers/src/transformers/masking_utils.py",
      "url": "https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/src/transformers/masking_utils.py",
      "revision": "cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55",
      "sha256": "50a737f63d8c778a5597fa34ac139049af921f44958205e3e1c29fe2bae77254"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/transformers/src/transformers/modeling_rope_utils.py",
      "url": "https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/src/transformers/modeling_rope_utils.py",
      "revision": "cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55",
      "sha256": "60438ad10eceddc1809b35256eb8de4492f759888bd929d9f3ae971fa255c60f"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/transformers/src/transformers/models/qwen3_5_moe/__init__.py",
      "url": "https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/src/transformers/models/qwen3_5_moe/__init__.py",
      "revision": "cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55",
      "sha256": "bbad751c2169cb9cc52cd13d53401ed0171a4f980e8dad48c3f6fb339ecab30d"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/transformers/src/transformers/models/qwen3_5_moe/configuration_qwen3_5_moe.py",
      "url": "https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/src/transformers/models/qwen3_5_moe/configuration_qwen3_5_moe.py",
      "revision": "cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55",
      "sha256": "9f68bcddc54b4e512802e18ec8a242514d7f746795b28373805d3e05a981f573"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/transformers/src/transformers/models/qwen3_5_moe/modeling_qwen3_5_moe.py",
      "url": "https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/src/transformers/models/qwen3_5_moe/modeling_qwen3_5_moe.py",
      "revision": "cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55",
      "sha256": "3f89026abe4e89ee42797fcf01a29dafaa961533e279fcb193d02999ef5251ca"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/transformers/src/transformers/models/qwen3_5_moe/modular_qwen3_5_moe.py",
      "url": "https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/src/transformers/models/qwen3_5_moe/modular_qwen3_5_moe.py",
      "revision": "cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55",
      "sha256": "20c4291118bb4d2ab967d91470033d5250447d7c4cdda3fdd3f44d3de9fd47ab"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/transformers/src/transformers/vision_utils.py",
      "url": "https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/src/transformers/vision_utils.py",
      "revision": "cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55",
      "sha256": "bcecd5a92b3266b9926272a549d2b1a0f1fe7646c698c0fa19bd96f976085356"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/transformers/tests/models/qwen3_5_moe/__init__.py",
      "url": "https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/tests/models/qwen3_5_moe/__init__.py",
      "revision": "cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55",
      "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    },
    {
      "file": "sources/qwen3.6-35b-a3b/transformers/tests/models/qwen3_5_moe/test_modeling_qwen3_5_moe.py",
      "url": "https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/tests/models/qwen3_5_moe/test_modeling_qwen3_5_moe.py",
      "revision": "cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55",
      "sha256": "693d82ca256b39e9f9267d12a6a557bd09c3bca299304d3f5ba7fc6342c86f1a"
    },
    {
      "file": "sources/hardware/nvidia-h100-page.html",
      "url": "https://www.nvidia.com/en-us/data-center/h100/",
      "revision": "snapshot-2026-09-08",
      "sha256": "8fe697dfa96dceeeed6e7a16517294e15d9100cc0e9f1e6e5edbce78699b4681"
    },
    {
      "file": "sources/hardware/nvidia-rtx-blackwell-whitepaper.pdf",
      "url": "https://images.nvidia.com/aem-dam/Solutions/geforce/blackwell/nvidia-rtx-blackwell-gpu-architecture.pdf",
      "revision": "snapshot-2026-09-08",
      "sha256": "906ff2a409d7a7e4cbc56f5d3a179d574120d19aaba99520670e1a0c064595fa"
    },
    {
      "file": "../references/files/specs/nvidia-h100.pdf",
      "url": "https://dam-cdn.nvd.orangelogic.com/AssetLink/705n6ur546g0uk43w0117r17n8042d73.pdf",
      "revision": "book-official-archive-2026-09-06",
      "sha256": "3641614979809a027a8aabdc2e77639efb8fcd0f8dc7873a22ba2125489f5a27"
    },
    {
      "file": "../references/files/specs/nvidia-rtx-blackwell-pro.pdf",
      "url": "https://www.nvidia.com/content/dam/en-zz/Solutions/design-visualization/quadro-product-literature/NVIDIA-RTX-Blackwell-PRO-GPU-Architecture-v1.0.pdf",
      "revision": "book-official-archive-2026-09-06",
      "sha256": "ad6727c2875d1272aaa15cfeb3fd51b8e6666fc5625742fd1bd3bb076ed119d6"
    },
    {
      "file": "../references/files/specs/apple-m2-pro-max.html",
      "url": "https://www.apple.com/newsroom/2023/01/apple-unveils-m2-pro-and-m2-max-next-generation-chips-for-next-level-workflows/",
      "revision": "book-official-archive-2026-09-06",
      "sha256": "cd25f2f6f04f6be4eec9d75868c5379c396862a4426ce5f9961b9e8241150ea7"
    },
    {
      "file": "sources/hardware/nvidia-ptx-isa-9-3.html",
      "url": "https://docs.nvidia.com/cuda/parallel-thread-execution/index.html",
      "revision": "snapshot-2026-09-08",
      "sha256": "940cc68f858cefdf82425b47ee3bac3afde447c8a85b95f43d7d6fb1f46b4413"
    },
    {
      "file": "research/hardware-nvidia-closure/rtx4090.html",
      "url": "https://www.nvidia.com/en-us/geforce/graphics-cards/40-series/rtx-4090/",
      "revision": "official-closure-snapshot-2026-09-09",
      "sha256": "2b315d1402135bfe273c3fbde57aa31ca482522ee8928b92af96cab8088906f8"
    },
    {
      "file": "research/hardware-nvidia-closure/rtx5090.html",
      "url": "https://www.nvidia.com/en-us/geforce/graphics-cards/50-series/rtx-5090/",
      "revision": "official-closure-snapshot-2026-09-09",
      "sha256": "33715ee8c890c82dda0615a28b9bf2d6879965b7a85ec6ae7e3e4c4497835df7"
    },
    {
      "file": "research/hardware-nvidia-closure/rtx-pro-ws-datasheet.pdf",
      "url": "https://www.nvidia.com/content/dam/en-zz/Solutions/data-center/rtx-pro-6000-blackwell-workstation-edition/workstation-blackwell-rtx-pro-6000-workstation-edition-nvidia-us-3519208-web.pdf",
      "revision": "official-closure-snapshot-2026-09-09",
      "sha256": "a19daec7b413bcbc2abc3893de5b97d4cfefef59cf1cb0f6121c3414037a9ddf"
    },
    {
      "file": "research/h05-next-review/cuda-programming-guide-12.8.1.html",
      "url": "https://docs.nvidia.com/cuda/archive/12.8.1/cuda-c-programming-guide/index.html",
      "revision": "CUDA12.8.1 archive",
      "sha256": "cdc49d93372b4e03e94d56f24345373f82ad76b8663c745073463263009637ce"
    }
  ],
  "summary": {
    "base_text_checkpoint_bytes": 69321221376,
    "entire_checkpoint_bytes": 71903645408,
    "auxiliary_checkpoint_bytes": 2582424032,
    "budget_components_bytes": {
      "selected_checkpoint_weight_bytes": 69321221376,
      "full_attention_kv_bytes": 671088640,
      "recurrent_fp32_bytes": 62914560,
      "convolution_bf16_bytes": 1966080,
      "declared_reserve_bytes": 2147483648
    },
    "necessary_budget_bytes": 72204674304
  },
  "devices": [
    {
      "device": "rtx4090",
      "nominal_capacity_bytes": 24000000000,
      "memory_evidence": {
        "nominal_capacity": 24,
        "capacity_unit": "GB",
        "bandwidth_bytes_per_second": 1008000000000.0,
        "source_id": "nvidia-rtx-blackwell-whitepaper",
        "locator": "Appendix A, Table 3, physical pages 46–48; footnotes 1 and 2",
        "capacity_note": "厂商 GB 标签；不是运行时可分配 bytes。统一内存还由 CPU/OS 共享。"
      },
      "necessary_budget_fits": false,
      "headroom_after_declared_budget_bytes": -48204674304,
      "runtime_feasibility": null,
      "tokens_per_second": null
    },
    {
      "device": "rtx5090",
      "nominal_capacity_bytes": 32000000000,
      "memory_evidence": {
        "nominal_capacity": 32,
        "capacity_unit": "GB",
        "bandwidth_bytes_per_second": 1792000000000.0,
        "source_id": "nvidia-rtx-blackwell-whitepaper",
        "locator": "Appendix A, Table 3, physical pages 46–48; footnotes 1 and 2",
        "capacity_note": "厂商 GB 标签；不是运行时可分配 bytes。统一内存还由 CPU/OS 共享。"
      },
      "necessary_budget_fits": false,
      "headroom_after_declared_budget_bytes": -40204674304,
      "runtime_feasibility": null,
      "tokens_per_second": null
    },
    {
      "device": "h100-sxm",
      "nominal_capacity_bytes": 80000000000,
      "memory_evidence": {
        "nominal_capacity": 80,
        "capacity_unit": "GB",
        "bandwidth_bytes_per_second": 3350000000000.0,
        "source_id": "nvidia-h100-page",
        "locator": "Product Specifications, H100 SXM",
        "capacity_note": "厂商 GB 标签；不是运行时可分配 bytes。统一内存还由 CPU/OS 共享。"
      },
      "necessary_budget_fits": true,
      "headroom_after_declared_budget_bytes": 7795325696,
      "runtime_feasibility": null,
      "tokens_per_second": null
    },
    {
      "device": "rtx-pro6000-blackwell-ws",
      "nominal_capacity_bytes": 96000000000,
      "memory_evidence": {
        "nominal_capacity": 96,
        "capacity_unit": "GB",
        "bandwidth_bytes_per_second": 1792000000000.0,
        "source_id": "nvidia-rtx-blackwell-pro",
        "locator": "Appendix A, Table 4, physical pages 45–47; footnotes 1 and 2",
        "capacity_note": "厂商 GB 标签；不是运行时可分配 bytes。统一内存还由 CPU/OS 共享。"
      },
      "necessary_budget_fits": true,
      "headroom_after_declared_budget_bytes": 23795325696,
      "runtime_feasibility": null,
      "tokens_per_second": null
    },
    {
      "device": "m2-max-38gpu-96gb",
      "nominal_capacity_bytes": 96000000000,
      "memory_evidence": {
        "nominal_capacity": 96,
        "capacity_unit": "GB",
        "bandwidth_bytes_per_second": 400000000000.0,
        "source_id": "apple-m2-pro-max",
        "locator": "M2 Max section; 38-core GPU / up to 96GB",
        "capacity_note": "厂商 GB 标签；不是运行时可分配 bytes。统一内存还由 CPU/OS 共享。",
        "shared_with_cpu": true
      },
      "necessary_budget_fits": true,
      "headroom_after_declared_budget_bytes": 23795325696,
      "runtime_feasibility": null,
      "tokens_per_second": null
    }
  ],
  "assumptions": [
    "全部路由专家常驻；A3B不是驻留权重大小。默认仅基础文本权重，选项可保留视觉/MTP文件中的全部权重，但不会凭此假装已计它们的执行状态。",
    "所有原始张量为BF16存储；线性递推状态按声明参考路径FP32，卷积槽与完整attention KV按BF16。运行时权重重排、转换、分配器和临时峰值未测。",
    "length是追加后的完整attention历史长度；递推状态与卷积槽不随历史线性增长。B个请求独立，不假定前缀共享。",
    "reserve_bytes为明确的额外预算假设，默认2GiB，并非测得workspace。官方名义GB按十进制计，不能等同可分配空间；Mac还与CPU/OS共享。",
    "超过预算即可在这些假设下排除；通过必要容量筛选不证明能加载、达到延迟目标或满足质量。此处没有低位量化、卸载或多卡切分。"
  ]
}
```
