# 增长KV：远端历史、追加副本与提交epoch

## 场景

```json
{
  "model": "qwen3.6-35b-a3b",
  "batch": 1,
  "prompt": 8192,
  "steps": 128,
  "copies": 1,
  "placement": "remote_prefix_local_tail",
  "bandwidth_bytes_per_second": 40000000000,
  "startup_ns": 5000,
  "local_tail_budget_bytes": 1048576
}
```

| 汇总 | 值 |
|---|---:|
| full_attention_qk_pv_flops | 173151354880 |
| initial_copy_network_bytes | 167772160 |
| prior_history_logical_read_bytes | 21641297920 |
| remote_prior_read_bytes | 21474836480 |
| local_prior_read_bytes | 166461440 |
| current_kv_operand_bytes | 2621440 |
| append_replica_network_bytes | 0 |
| total_network_bytes | 21642608640 |
| remote_final_bytes_per_replica | 167772160 |
| remote_physical_final_bytes | 167772160 |
| local_tail_final_bytes | 2621440 |
| local_fixed_state_bytes | 64880640 |
| local_current_append_buffer_bytes | 20480 |
| final_unique_history_bytes | 170393600 |
| local_tail_budget_fits | False |
| communication_skeleton_seconds_exact | 67713777/125000000 |
| initial_copy_seconds_exact | 524913/125000000 |
| token_communication_seconds_exact | 1049826/1953125 |
| actual_decode_seconds | None |
| actual_task_feasible | None |

| 步 | 所需远端epoch | 远端旧历史bytes | 本地旧历史bytes | 当前KVbytes | 副本写bytes | 提交秒 | 本地tailbytes |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 | 8192 | 167772160 | 0 | 20480 | 0 | 0.008398608 | 20480 |
| 1 | 8192 | 167772160 | 20480 | 20480 | 0 | 0.012597912 | 40960 |
| 2 | 8192 | 167772160 | 40960 | 20480 | 0 | 0.016797216 | 61440 |
| 3 | 8192 | 167772160 | 61440 | 20480 | 0 | 0.020996520 | 81920 |
| 4 | 8192 | 167772160 | 81920 | 20480 | 0 | 0.025195824 | 102400 |
| 5 | 8192 | 167772160 | 102400 | 20480 | 0 | 0.029395128 | 122880 |
| 6 | 8192 | 167772160 | 122880 | 20480 | 0 | 0.033594432 | 143360 |
| 7 | 8192 | 167772160 | 143360 | 20480 | 0 | 0.037793736 | 163840 |
| 8 | 8192 | 167772160 | 163840 | 20480 | 0 | 0.041993040 | 184320 |
| 9 | 8192 | 167772160 | 184320 | 20480 | 0 | 0.046192344 | 204800 |
| 10 | 8192 | 167772160 | 204800 | 20480 | 0 | 0.050391648 | 225280 |
| 11 | 8192 | 167772160 | 225280 | 20480 | 0 | 0.054590952 | 245760 |
| 12 | 8192 | 167772160 | 245760 | 20480 | 0 | 0.058790256 | 266240 |
| 13 | 8192 | 167772160 | 266240 | 20480 | 0 | 0.062989560 | 286720 |
| 14 | 8192 | 167772160 | 286720 | 20480 | 0 | 0.067188864 | 307200 |
| 15 | 8192 | 167772160 | 307200 | 20480 | 0 | 0.071388168 | 327680 |
| 16 | 8192 | 167772160 | 327680 | 20480 | 0 | 0.075587472 | 348160 |
| 17 | 8192 | 167772160 | 348160 | 20480 | 0 | 0.079786776 | 368640 |
| 18 | 8192 | 167772160 | 368640 | 20480 | 0 | 0.083986080 | 389120 |
| 19 | 8192 | 167772160 | 389120 | 20480 | 0 | 0.088185384 | 409600 |
| 20 | 8192 | 167772160 | 409600 | 20480 | 0 | 0.092384688 | 430080 |
| 21 | 8192 | 167772160 | 430080 | 20480 | 0 | 0.096583992 | 450560 |
| 22 | 8192 | 167772160 | 450560 | 20480 | 0 | 0.100783296 | 471040 |
| 23 | 8192 | 167772160 | 471040 | 20480 | 0 | 0.104982600 | 491520 |
| 24 | 8192 | 167772160 | 491520 | 20480 | 0 | 0.109181904 | 512000 |
| 25 | 8192 | 167772160 | 512000 | 20480 | 0 | 0.113381208 | 532480 |
| 26 | 8192 | 167772160 | 532480 | 20480 | 0 | 0.117580512 | 552960 |
| 27 | 8192 | 167772160 | 552960 | 20480 | 0 | 0.121779816 | 573440 |
| 28 | 8192 | 167772160 | 573440 | 20480 | 0 | 0.125979120 | 593920 |
| 29 | 8192 | 167772160 | 593920 | 20480 | 0 | 0.130178424 | 614400 |
| 30 | 8192 | 167772160 | 614400 | 20480 | 0 | 0.134377728 | 634880 |
| 31 | 8192 | 167772160 | 634880 | 20480 | 0 | 0.138577032 | 655360 |
| 32 | 8192 | 167772160 | 655360 | 20480 | 0 | 0.142776336 | 675840 |
| 33 | 8192 | 167772160 | 675840 | 20480 | 0 | 0.146975640 | 696320 |
| 34 | 8192 | 167772160 | 696320 | 20480 | 0 | 0.151174944 | 716800 |
| 35 | 8192 | 167772160 | 716800 | 20480 | 0 | 0.155374248 | 737280 |
| 36 | 8192 | 167772160 | 737280 | 20480 | 0 | 0.159573552 | 757760 |
| 37 | 8192 | 167772160 | 757760 | 20480 | 0 | 0.163772856 | 778240 |
| 38 | 8192 | 167772160 | 778240 | 20480 | 0 | 0.167972160 | 798720 |
| 39 | 8192 | 167772160 | 798720 | 20480 | 0 | 0.172171464 | 819200 |
| 40 | 8192 | 167772160 | 819200 | 20480 | 0 | 0.176370768 | 839680 |
| 41 | 8192 | 167772160 | 839680 | 20480 | 0 | 0.180570072 | 860160 |
| 42 | 8192 | 167772160 | 860160 | 20480 | 0 | 0.184769376 | 880640 |
| 43 | 8192 | 167772160 | 880640 | 20480 | 0 | 0.188968680 | 901120 |
| 44 | 8192 | 167772160 | 901120 | 20480 | 0 | 0.193167984 | 921600 |
| 45 | 8192 | 167772160 | 921600 | 20480 | 0 | 0.197367288 | 942080 |
| 46 | 8192 | 167772160 | 942080 | 20480 | 0 | 0.201566592 | 962560 |
| 47 | 8192 | 167772160 | 962560 | 20480 | 0 | 0.205765896 | 983040 |
| 48 | 8192 | 167772160 | 983040 | 20480 | 0 | 0.209965200 | 1003520 |
| 49 | 8192 | 167772160 | 1003520 | 20480 | 0 | 0.214164504 | 1024000 |
| 50 | 8192 | 167772160 | 1024000 | 20480 | 0 | 0.218363808 | 1044480 |
| 51 | 8192 | 167772160 | 1044480 | 20480 | 0 | 0.222563112 | 1064960 |
| 52 | 8192 | 167772160 | 1064960 | 20480 | 0 | 0.226762416 | 1085440 |
| 53 | 8192 | 167772160 | 1085440 | 20480 | 0 | 0.230961720 | 1105920 |
| 54 | 8192 | 167772160 | 1105920 | 20480 | 0 | 0.235161024 | 1126400 |
| 55 | 8192 | 167772160 | 1126400 | 20480 | 0 | 0.239360328 | 1146880 |
| 56 | 8192 | 167772160 | 1146880 | 20480 | 0 | 0.243559632 | 1167360 |
| 57 | 8192 | 167772160 | 1167360 | 20480 | 0 | 0.247758936 | 1187840 |
| 58 | 8192 | 167772160 | 1187840 | 20480 | 0 | 0.251958240 | 1208320 |
| 59 | 8192 | 167772160 | 1208320 | 20480 | 0 | 0.256157544 | 1228800 |
| 60 | 8192 | 167772160 | 1228800 | 20480 | 0 | 0.260356848 | 1249280 |
| 61 | 8192 | 167772160 | 1249280 | 20480 | 0 | 0.264556152 | 1269760 |
| 62 | 8192 | 167772160 | 1269760 | 20480 | 0 | 0.268755456 | 1290240 |
| 63 | 8192 | 167772160 | 1290240 | 20480 | 0 | 0.272954760 | 1310720 |
| 64 | 8192 | 167772160 | 1310720 | 20480 | 0 | 0.277154064 | 1331200 |
| 65 | 8192 | 167772160 | 1331200 | 20480 | 0 | 0.281353368 | 1351680 |
| 66 | 8192 | 167772160 | 1351680 | 20480 | 0 | 0.285552672 | 1372160 |
| 67 | 8192 | 167772160 | 1372160 | 20480 | 0 | 0.289751976 | 1392640 |
| 68 | 8192 | 167772160 | 1392640 | 20480 | 0 | 0.293951280 | 1413120 |
| 69 | 8192 | 167772160 | 1413120 | 20480 | 0 | 0.298150584 | 1433600 |
| 70 | 8192 | 167772160 | 1433600 | 20480 | 0 | 0.302349888 | 1454080 |
| 71 | 8192 | 167772160 | 1454080 | 20480 | 0 | 0.306549192 | 1474560 |
| 72 | 8192 | 167772160 | 1474560 | 20480 | 0 | 0.310748496 | 1495040 |
| 73 | 8192 | 167772160 | 1495040 | 20480 | 0 | 0.314947800 | 1515520 |
| 74 | 8192 | 167772160 | 1515520 | 20480 | 0 | 0.319147104 | 1536000 |
| 75 | 8192 | 167772160 | 1536000 | 20480 | 0 | 0.323346408 | 1556480 |
| 76 | 8192 | 167772160 | 1556480 | 20480 | 0 | 0.327545712 | 1576960 |
| 77 | 8192 | 167772160 | 1576960 | 20480 | 0 | 0.331745016 | 1597440 |
| 78 | 8192 | 167772160 | 1597440 | 20480 | 0 | 0.335944320 | 1617920 |
| 79 | 8192 | 167772160 | 1617920 | 20480 | 0 | 0.340143624 | 1638400 |
| 80 | 8192 | 167772160 | 1638400 | 20480 | 0 | 0.344342928 | 1658880 |
| 81 | 8192 | 167772160 | 1658880 | 20480 | 0 | 0.348542232 | 1679360 |
| 82 | 8192 | 167772160 | 1679360 | 20480 | 0 | 0.352741536 | 1699840 |
| 83 | 8192 | 167772160 | 1699840 | 20480 | 0 | 0.356940840 | 1720320 |
| 84 | 8192 | 167772160 | 1720320 | 20480 | 0 | 0.361140144 | 1740800 |
| 85 | 8192 | 167772160 | 1740800 | 20480 | 0 | 0.365339448 | 1761280 |
| 86 | 8192 | 167772160 | 1761280 | 20480 | 0 | 0.369538752 | 1781760 |
| 87 | 8192 | 167772160 | 1781760 | 20480 | 0 | 0.373738056 | 1802240 |
| 88 | 8192 | 167772160 | 1802240 | 20480 | 0 | 0.377937360 | 1822720 |
| 89 | 8192 | 167772160 | 1822720 | 20480 | 0 | 0.382136664 | 1843200 |
| 90 | 8192 | 167772160 | 1843200 | 20480 | 0 | 0.386335968 | 1863680 |
| 91 | 8192 | 167772160 | 1863680 | 20480 | 0 | 0.390535272 | 1884160 |
| 92 | 8192 | 167772160 | 1884160 | 20480 | 0 | 0.394734576 | 1904640 |
| 93 | 8192 | 167772160 | 1904640 | 20480 | 0 | 0.398933880 | 1925120 |
| 94 | 8192 | 167772160 | 1925120 | 20480 | 0 | 0.403133184 | 1945600 |
| 95 | 8192 | 167772160 | 1945600 | 20480 | 0 | 0.407332488 | 1966080 |
| 96 | 8192 | 167772160 | 1966080 | 20480 | 0 | 0.411531792 | 1986560 |
| 97 | 8192 | 167772160 | 1986560 | 20480 | 0 | 0.415731096 | 2007040 |
| 98 | 8192 | 167772160 | 2007040 | 20480 | 0 | 0.419930400 | 2027520 |
| 99 | 8192 | 167772160 | 2027520 | 20480 | 0 | 0.424129704 | 2048000 |
| 100 | 8192 | 167772160 | 2048000 | 20480 | 0 | 0.428329008 | 2068480 |
| 101 | 8192 | 167772160 | 2068480 | 20480 | 0 | 0.432528312 | 2088960 |
| 102 | 8192 | 167772160 | 2088960 | 20480 | 0 | 0.436727616 | 2109440 |
| 103 | 8192 | 167772160 | 2109440 | 20480 | 0 | 0.440926920 | 2129920 |
| 104 | 8192 | 167772160 | 2129920 | 20480 | 0 | 0.445126224 | 2150400 |
| 105 | 8192 | 167772160 | 2150400 | 20480 | 0 | 0.449325528 | 2170880 |
| 106 | 8192 | 167772160 | 2170880 | 20480 | 0 | 0.453524832 | 2191360 |
| 107 | 8192 | 167772160 | 2191360 | 20480 | 0 | 0.457724136 | 2211840 |
| 108 | 8192 | 167772160 | 2211840 | 20480 | 0 | 0.461923440 | 2232320 |
| 109 | 8192 | 167772160 | 2232320 | 20480 | 0 | 0.466122744 | 2252800 |
| 110 | 8192 | 167772160 | 2252800 | 20480 | 0 | 0.470322048 | 2273280 |
| 111 | 8192 | 167772160 | 2273280 | 20480 | 0 | 0.474521352 | 2293760 |
| 112 | 8192 | 167772160 | 2293760 | 20480 | 0 | 0.478720656 | 2314240 |
| 113 | 8192 | 167772160 | 2314240 | 20480 | 0 | 0.482919960 | 2334720 |
| 114 | 8192 | 167772160 | 2334720 | 20480 | 0 | 0.487119264 | 2355200 |
| 115 | 8192 | 167772160 | 2355200 | 20480 | 0 | 0.491318568 | 2375680 |
| 116 | 8192 | 167772160 | 2375680 | 20480 | 0 | 0.495517872 | 2396160 |
| 117 | 8192 | 167772160 | 2396160 | 20480 | 0 | 0.499717176 | 2416640 |
| 118 | 8192 | 167772160 | 2416640 | 20480 | 0 | 0.503916480 | 2437120 |
| 119 | 8192 | 167772160 | 2437120 | 20480 | 0 | 0.508115784 | 2457600 |
| 120 | 8192 | 167772160 | 2457600 | 20480 | 0 | 0.512315088 | 2478080 |
| 121 | 8192 | 167772160 | 2478080 | 20480 | 0 | 0.516514392 | 2498560 |
| 122 | 8192 | 167772160 | 2498560 | 20480 | 0 | 0.520713696 | 2519040 |
| 123 | 8192 | 167772160 | 2519040 | 20480 | 0 | 0.524913000 | 2539520 |
| 124 | 8192 | 167772160 | 2539520 | 20480 | 0 | 0.529112304 | 2560000 |
| 125 | 8192 | 167772160 | 2560000 | 20480 | 0 | 0.533311608 | 2580480 |
| 126 | 8192 | 167772160 | 2580480 | 20480 | 0 | 0.537510912 | 2600960 |
| 127 | 8192 | 167772160 | 2600960 | 20480 | 0 | 0.541710216 | 2621440 |

所有配置/实现原件校验后使用；BF16完整attention KV按层/头计，Qwen3.6仅10层保存全历史KV，30层FP32递推和BF16卷积槽留在计算节点，不传成历史序列。
prompt是已产生的KV位置数；steps是追加单token forward次数。输入token/输出token移位明确，当前位置操作数不混入远端旧历史读取。给出的QK/PV仅完整attention子账，不含投影/专家/DeltaNet等全部计算。
remote_all复制完整prompt，逐步读一个副本的所有旧位置，再将新位置发给每个副本；共享发送接口串行写入，全副本提交屏障保证下一步所有可选副本都达到要求epoch。没有实现真实一致性协议或原子性证明。
remote_prefix_local_tail保持远端prompt不变，新增位置留本地；每步远端prefix和本地tail各读一次。全部模型层仍需要本地递推/卷积等状态，尾部预算只检查新增完整attention KV，不是整机容量。
初始化和每消息startup+bytes/B均为声明串行传输模型。当前KV生成完成后才可追加，但计算时长和与网络重叠未知；时间轴只列通信骨架，不能视为真实decode latency或吞吐。
新KV在本地先产生，current append buffer另列，不和已增长tail盲目相加为内存峰值。远端读缓存/临时buffer/控制消息/ACK/重试/故障检测及恢复未计，不推测厂商能力。
初始拷贝计从外部已产出的prompt向各副本的发送；原始prompt源是否释放另由上层所有权协议决定，不计成已释放容量。副本只增加存储/写入与静态冗余，不自动增加读带宽。

```json
{
  "calculation": "growing-remote-kv",
  "scenario": {
    "model": "qwen3.6-35b-a3b",
    "batch": 1,
    "prompt": 8192,
    "steps": 128,
    "copies": 1,
    "placement": "remote_prefix_local_tail",
    "bandwidth_bytes_per_second": 40000000000,
    "startup_ns": 5000,
    "local_tail_budget_bytes": 1048576
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
    }
  ],
  "geometry": {
    "model": "qwen3.6-35b-a3b",
    "full_attention_layers": 10,
    "linear_layers": 30,
    "kv_bytes_per_position": 20480,
    "qk_pv_flops_per_position_pair": 163840,
    "local_recurrent_bytes_per_request": 62914560,
    "local_convolution_bytes_per_request": 1966080,
    "max_positions": 262144
  },
  "initial_copy_messages": [
    {
      "replica": 0,
      "bytes": 167772160
    }
  ],
  "steps": [
    {
      "step": 0,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1342341120,
      "read_start_seconds_exact": "524913/125000000",
      "read_finish_seconds_exact": "524913/62500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "524913/62500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 20480,
      "logical_full_history_bytes_after": 167792640
    },
    {
      "step": 1,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 20480,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1342504960,
      "read_start_seconds_exact": "524913/62500000",
      "read_finish_seconds_exact": "1574739/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "1574739/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 40960,
      "logical_full_history_bytes_after": 167813120
    },
    {
      "step": 2,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 40960,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1342668800,
      "read_start_seconds_exact": "1574739/125000000",
      "read_finish_seconds_exact": "524913/31250000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "524913/31250000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 61440,
      "logical_full_history_bytes_after": 167833600
    },
    {
      "step": 3,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 61440,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1342832640,
      "read_start_seconds_exact": "524913/31250000",
      "read_finish_seconds_exact": "524913/25000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "524913/25000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 81920,
      "logical_full_history_bytes_after": 167854080
    },
    {
      "step": 4,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 81920,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1342996480,
      "read_start_seconds_exact": "524913/25000000",
      "read_finish_seconds_exact": "1574739/62500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "1574739/62500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 102400,
      "logical_full_history_bytes_after": 167874560
    },
    {
      "step": 5,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 102400,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1343160320,
      "read_start_seconds_exact": "1574739/62500000",
      "read_finish_seconds_exact": "3674391/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "3674391/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 122880,
      "logical_full_history_bytes_after": 167895040
    },
    {
      "step": 6,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 122880,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1343324160,
      "read_start_seconds_exact": "3674391/125000000",
      "read_finish_seconds_exact": "524913/15625000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "524913/15625000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 143360,
      "logical_full_history_bytes_after": 167915520
    },
    {
      "step": 7,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 143360,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1343488000,
      "read_start_seconds_exact": "524913/15625000",
      "read_finish_seconds_exact": "4724217/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "4724217/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 163840,
      "logical_full_history_bytes_after": 167936000
    },
    {
      "step": 8,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 163840,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1343651840,
      "read_start_seconds_exact": "4724217/125000000",
      "read_finish_seconds_exact": "524913/12500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "524913/12500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 184320,
      "logical_full_history_bytes_after": 167956480
    },
    {
      "step": 9,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 184320,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1343815680,
      "read_start_seconds_exact": "524913/12500000",
      "read_finish_seconds_exact": "5774043/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "5774043/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 204800,
      "logical_full_history_bytes_after": 167976960
    },
    {
      "step": 10,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 204800,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1343979520,
      "read_start_seconds_exact": "5774043/125000000",
      "read_finish_seconds_exact": "1574739/31250000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "1574739/31250000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 225280,
      "logical_full_history_bytes_after": 167997440
    },
    {
      "step": 11,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 225280,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1344143360,
      "read_start_seconds_exact": "1574739/31250000",
      "read_finish_seconds_exact": "6823869/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "6823869/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 245760,
      "logical_full_history_bytes_after": 168017920
    },
    {
      "step": 12,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 245760,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1344307200,
      "read_start_seconds_exact": "6823869/125000000",
      "read_finish_seconds_exact": "3674391/62500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "3674391/62500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 266240,
      "logical_full_history_bytes_after": 168038400
    },
    {
      "step": 13,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 266240,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1344471040,
      "read_start_seconds_exact": "3674391/62500000",
      "read_finish_seconds_exact": "1574739/25000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "1574739/25000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 286720,
      "logical_full_history_bytes_after": 168058880
    },
    {
      "step": 14,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 286720,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1344634880,
      "read_start_seconds_exact": "1574739/25000000",
      "read_finish_seconds_exact": "524913/7812500",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "524913/7812500",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 307200,
      "logical_full_history_bytes_after": 168079360
    },
    {
      "step": 15,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 307200,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1344798720,
      "read_start_seconds_exact": "524913/7812500",
      "read_finish_seconds_exact": "8923521/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "8923521/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 327680,
      "logical_full_history_bytes_after": 168099840
    },
    {
      "step": 16,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 327680,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1344962560,
      "read_start_seconds_exact": "8923521/125000000",
      "read_finish_seconds_exact": "4724217/62500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "4724217/62500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 348160,
      "logical_full_history_bytes_after": 168120320
    },
    {
      "step": 17,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 348160,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1345126400,
      "read_start_seconds_exact": "4724217/62500000",
      "read_finish_seconds_exact": "9973347/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "9973347/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 368640,
      "logical_full_history_bytes_after": 168140800
    },
    {
      "step": 18,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 368640,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1345290240,
      "read_start_seconds_exact": "9973347/125000000",
      "read_finish_seconds_exact": "524913/6250000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "524913/6250000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 389120,
      "logical_full_history_bytes_after": 168161280
    },
    {
      "step": 19,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 389120,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1345454080,
      "read_start_seconds_exact": "524913/6250000",
      "read_finish_seconds_exact": "11023173/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "11023173/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 409600,
      "logical_full_history_bytes_after": 168181760
    },
    {
      "step": 20,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 409600,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1345617920,
      "read_start_seconds_exact": "11023173/125000000",
      "read_finish_seconds_exact": "5774043/62500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "5774043/62500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 430080,
      "logical_full_history_bytes_after": 168202240
    },
    {
      "step": 21,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 430080,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1345781760,
      "read_start_seconds_exact": "5774043/62500000",
      "read_finish_seconds_exact": "12072999/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "12072999/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 450560,
      "logical_full_history_bytes_after": 168222720
    },
    {
      "step": 22,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 450560,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1345945600,
      "read_start_seconds_exact": "12072999/125000000",
      "read_finish_seconds_exact": "1574739/15625000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "1574739/15625000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 471040,
      "logical_full_history_bytes_after": 168243200
    },
    {
      "step": 23,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 471040,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1346109440,
      "read_start_seconds_exact": "1574739/15625000",
      "read_finish_seconds_exact": "524913/5000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "524913/5000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 491520,
      "logical_full_history_bytes_after": 168263680
    },
    {
      "step": 24,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 491520,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1346273280,
      "read_start_seconds_exact": "524913/5000000",
      "read_finish_seconds_exact": "6823869/62500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "6823869/62500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 512000,
      "logical_full_history_bytes_after": 168284160
    },
    {
      "step": 25,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 512000,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1346437120,
      "read_start_seconds_exact": "6823869/62500000",
      "read_finish_seconds_exact": "14172651/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "14172651/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 532480,
      "logical_full_history_bytes_after": 168304640
    },
    {
      "step": 26,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 532480,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1346600960,
      "read_start_seconds_exact": "14172651/125000000",
      "read_finish_seconds_exact": "3674391/31250000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "3674391/31250000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 552960,
      "logical_full_history_bytes_after": 168325120
    },
    {
      "step": 27,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 552960,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1346764800,
      "read_start_seconds_exact": "3674391/31250000",
      "read_finish_seconds_exact": "15222477/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "15222477/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 573440,
      "logical_full_history_bytes_after": 168345600
    },
    {
      "step": 28,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 573440,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1346928640,
      "read_start_seconds_exact": "15222477/125000000",
      "read_finish_seconds_exact": "1574739/12500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "1574739/12500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 593920,
      "logical_full_history_bytes_after": 168366080
    },
    {
      "step": 29,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 593920,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1347092480,
      "read_start_seconds_exact": "1574739/12500000",
      "read_finish_seconds_exact": "16272303/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "16272303/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 614400,
      "logical_full_history_bytes_after": 168386560
    },
    {
      "step": 30,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 614400,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1347256320,
      "read_start_seconds_exact": "16272303/125000000",
      "read_finish_seconds_exact": "524913/3906250",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "524913/3906250",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 634880,
      "logical_full_history_bytes_after": 168407040
    },
    {
      "step": 31,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 634880,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1347420160,
      "read_start_seconds_exact": "524913/3906250",
      "read_finish_seconds_exact": "17322129/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "17322129/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 655360,
      "logical_full_history_bytes_after": 168427520
    },
    {
      "step": 32,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 655360,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1347584000,
      "read_start_seconds_exact": "17322129/125000000",
      "read_finish_seconds_exact": "8923521/62500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "8923521/62500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 675840,
      "logical_full_history_bytes_after": 168448000
    },
    {
      "step": 33,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 675840,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1347747840,
      "read_start_seconds_exact": "8923521/62500000",
      "read_finish_seconds_exact": "3674391/25000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "3674391/25000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 696320,
      "logical_full_history_bytes_after": 168468480
    },
    {
      "step": 34,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 696320,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1347911680,
      "read_start_seconds_exact": "3674391/25000000",
      "read_finish_seconds_exact": "4724217/31250000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "4724217/31250000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 716800,
      "logical_full_history_bytes_after": 168488960
    },
    {
      "step": 35,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 716800,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1348075520,
      "read_start_seconds_exact": "4724217/31250000",
      "read_finish_seconds_exact": "19421781/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "19421781/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 737280,
      "logical_full_history_bytes_after": 168509440
    },
    {
      "step": 36,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 737280,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1348239360,
      "read_start_seconds_exact": "19421781/125000000",
      "read_finish_seconds_exact": "9973347/62500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "9973347/62500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 757760,
      "logical_full_history_bytes_after": 168529920
    },
    {
      "step": 37,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 757760,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1348403200,
      "read_start_seconds_exact": "9973347/62500000",
      "read_finish_seconds_exact": "20471607/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "20471607/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 778240,
      "logical_full_history_bytes_after": 168550400
    },
    {
      "step": 38,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 778240,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1348567040,
      "read_start_seconds_exact": "20471607/125000000",
      "read_finish_seconds_exact": "524913/3125000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "524913/3125000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 798720,
      "logical_full_history_bytes_after": 168570880
    },
    {
      "step": 39,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 798720,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1348730880,
      "read_start_seconds_exact": "524913/3125000",
      "read_finish_seconds_exact": "21521433/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "21521433/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 819200,
      "logical_full_history_bytes_after": 168591360
    },
    {
      "step": 40,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 819200,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1348894720,
      "read_start_seconds_exact": "21521433/125000000",
      "read_finish_seconds_exact": "11023173/62500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "11023173/62500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 839680,
      "logical_full_history_bytes_after": 168611840
    },
    {
      "step": 41,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 839680,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1349058560,
      "read_start_seconds_exact": "11023173/62500000",
      "read_finish_seconds_exact": "22571259/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "22571259/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 860160,
      "logical_full_history_bytes_after": 168632320
    },
    {
      "step": 42,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 860160,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1349222400,
      "read_start_seconds_exact": "22571259/125000000",
      "read_finish_seconds_exact": "5774043/31250000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "5774043/31250000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 880640,
      "logical_full_history_bytes_after": 168652800
    },
    {
      "step": 43,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 880640,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1349386240,
      "read_start_seconds_exact": "5774043/31250000",
      "read_finish_seconds_exact": "4724217/25000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "4724217/25000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 901120,
      "logical_full_history_bytes_after": 168673280
    },
    {
      "step": 44,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 901120,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1349550080,
      "read_start_seconds_exact": "4724217/25000000",
      "read_finish_seconds_exact": "12072999/62500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "12072999/62500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 921600,
      "logical_full_history_bytes_after": 168693760
    },
    {
      "step": 45,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 921600,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1349713920,
      "read_start_seconds_exact": "12072999/62500000",
      "read_finish_seconds_exact": "24670911/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "24670911/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 942080,
      "logical_full_history_bytes_after": 168714240
    },
    {
      "step": 46,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 942080,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1349877760,
      "read_start_seconds_exact": "24670911/125000000",
      "read_finish_seconds_exact": "1574739/7812500",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "1574739/7812500",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 962560,
      "logical_full_history_bytes_after": 168734720
    },
    {
      "step": 47,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 962560,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1350041600,
      "read_start_seconds_exact": "1574739/7812500",
      "read_finish_seconds_exact": "25720737/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "25720737/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 983040,
      "logical_full_history_bytes_after": 168755200
    },
    {
      "step": 48,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 983040,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1350205440,
      "read_start_seconds_exact": "25720737/125000000",
      "read_finish_seconds_exact": "524913/2500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "524913/2500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1003520,
      "logical_full_history_bytes_after": 168775680
    },
    {
      "step": 49,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1003520,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1350369280,
      "read_start_seconds_exact": "524913/2500000",
      "read_finish_seconds_exact": "26770563/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "26770563/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1024000,
      "logical_full_history_bytes_after": 168796160
    },
    {
      "step": 50,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1024000,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1350533120,
      "read_start_seconds_exact": "26770563/125000000",
      "read_finish_seconds_exact": "6823869/31250000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "6823869/31250000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1044480,
      "logical_full_history_bytes_after": 168816640
    },
    {
      "step": 51,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1044480,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1350696960,
      "read_start_seconds_exact": "6823869/31250000",
      "read_finish_seconds_exact": "27820389/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "27820389/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1064960,
      "logical_full_history_bytes_after": 168837120
    },
    {
      "step": 52,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1064960,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1350860800,
      "read_start_seconds_exact": "27820389/125000000",
      "read_finish_seconds_exact": "14172651/62500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "14172651/62500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1085440,
      "logical_full_history_bytes_after": 168857600
    },
    {
      "step": 53,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1085440,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1351024640,
      "read_start_seconds_exact": "14172651/62500000",
      "read_finish_seconds_exact": "5774043/25000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "5774043/25000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1105920,
      "logical_full_history_bytes_after": 168878080
    },
    {
      "step": 54,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1105920,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1351188480,
      "read_start_seconds_exact": "5774043/25000000",
      "read_finish_seconds_exact": "3674391/15625000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "3674391/15625000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1126400,
      "logical_full_history_bytes_after": 168898560
    },
    {
      "step": 55,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1126400,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1351352320,
      "read_start_seconds_exact": "3674391/15625000",
      "read_finish_seconds_exact": "29920041/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "29920041/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1146880,
      "logical_full_history_bytes_after": 168919040
    },
    {
      "step": 56,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1146880,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1351516160,
      "read_start_seconds_exact": "29920041/125000000",
      "read_finish_seconds_exact": "15222477/62500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "15222477/62500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1167360,
      "logical_full_history_bytes_after": 168939520
    },
    {
      "step": 57,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1167360,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1351680000,
      "read_start_seconds_exact": "15222477/62500000",
      "read_finish_seconds_exact": "30969867/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "30969867/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1187840,
      "logical_full_history_bytes_after": 168960000
    },
    {
      "step": 58,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1187840,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1351843840,
      "read_start_seconds_exact": "30969867/125000000",
      "read_finish_seconds_exact": "1574739/6250000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "1574739/6250000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1208320,
      "logical_full_history_bytes_after": 168980480
    },
    {
      "step": 59,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1208320,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1352007680,
      "read_start_seconds_exact": "1574739/6250000",
      "read_finish_seconds_exact": "32019693/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "32019693/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1228800,
      "logical_full_history_bytes_after": 169000960
    },
    {
      "step": 60,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1228800,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1352171520,
      "read_start_seconds_exact": "32019693/125000000",
      "read_finish_seconds_exact": "16272303/62500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "16272303/62500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1249280,
      "logical_full_history_bytes_after": 169021440
    },
    {
      "step": 61,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1249280,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1352335360,
      "read_start_seconds_exact": "16272303/62500000",
      "read_finish_seconds_exact": "33069519/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "33069519/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1269760,
      "logical_full_history_bytes_after": 169041920
    },
    {
      "step": 62,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1269760,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1352499200,
      "read_start_seconds_exact": "33069519/125000000",
      "read_finish_seconds_exact": "524913/1953125",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "524913/1953125",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1290240,
      "logical_full_history_bytes_after": 169062400
    },
    {
      "step": 63,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1290240,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1352663040,
      "read_start_seconds_exact": "524913/1953125",
      "read_finish_seconds_exact": "6823869/25000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "6823869/25000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1310720,
      "logical_full_history_bytes_after": 169082880
    },
    {
      "step": 64,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1310720,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1352826880,
      "read_start_seconds_exact": "6823869/25000000",
      "read_finish_seconds_exact": "17322129/62500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "17322129/62500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1331200,
      "logical_full_history_bytes_after": 169103360
    },
    {
      "step": 65,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1331200,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1352990720,
      "read_start_seconds_exact": "17322129/62500000",
      "read_finish_seconds_exact": "35169171/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "35169171/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1351680,
      "logical_full_history_bytes_after": 169123840
    },
    {
      "step": 66,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1351680,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1353154560,
      "read_start_seconds_exact": "35169171/125000000",
      "read_finish_seconds_exact": "8923521/31250000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "8923521/31250000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1372160,
      "logical_full_history_bytes_after": 169144320
    },
    {
      "step": 67,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1372160,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1353318400,
      "read_start_seconds_exact": "8923521/31250000",
      "read_finish_seconds_exact": "36218997/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "36218997/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1392640,
      "logical_full_history_bytes_after": 169164800
    },
    {
      "step": 68,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1392640,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1353482240,
      "read_start_seconds_exact": "36218997/125000000",
      "read_finish_seconds_exact": "3674391/12500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "3674391/12500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1413120,
      "logical_full_history_bytes_after": 169185280
    },
    {
      "step": 69,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1413120,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1353646080,
      "read_start_seconds_exact": "3674391/12500000",
      "read_finish_seconds_exact": "37268823/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "37268823/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1433600,
      "logical_full_history_bytes_after": 169205760
    },
    {
      "step": 70,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1433600,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1353809920,
      "read_start_seconds_exact": "37268823/125000000",
      "read_finish_seconds_exact": "4724217/15625000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "4724217/15625000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1454080,
      "logical_full_history_bytes_after": 169226240
    },
    {
      "step": 71,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1454080,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1353973760,
      "read_start_seconds_exact": "4724217/15625000",
      "read_finish_seconds_exact": "38318649/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "38318649/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1474560,
      "logical_full_history_bytes_after": 169246720
    },
    {
      "step": 72,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1474560,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1354137600,
      "read_start_seconds_exact": "38318649/125000000",
      "read_finish_seconds_exact": "19421781/62500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "19421781/62500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1495040,
      "logical_full_history_bytes_after": 169267200
    },
    {
      "step": 73,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1495040,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1354301440,
      "read_start_seconds_exact": "19421781/62500000",
      "read_finish_seconds_exact": "1574739/5000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "1574739/5000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1515520,
      "logical_full_history_bytes_after": 169287680
    },
    {
      "step": 74,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1515520,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1354465280,
      "read_start_seconds_exact": "1574739/5000000",
      "read_finish_seconds_exact": "9973347/31250000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "9973347/31250000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1536000,
      "logical_full_history_bytes_after": 169308160
    },
    {
      "step": 75,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1536000,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1354629120,
      "read_start_seconds_exact": "9973347/31250000",
      "read_finish_seconds_exact": "40418301/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "40418301/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1556480,
      "logical_full_history_bytes_after": 169328640
    },
    {
      "step": 76,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1556480,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1354792960,
      "read_start_seconds_exact": "40418301/125000000",
      "read_finish_seconds_exact": "20471607/62500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "20471607/62500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1576960,
      "logical_full_history_bytes_after": 169349120
    },
    {
      "step": 77,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1576960,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1354956800,
      "read_start_seconds_exact": "20471607/62500000",
      "read_finish_seconds_exact": "41468127/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "41468127/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1597440,
      "logical_full_history_bytes_after": 169369600
    },
    {
      "step": 78,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1597440,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1355120640,
      "read_start_seconds_exact": "41468127/125000000",
      "read_finish_seconds_exact": "524913/1562500",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "524913/1562500",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1617920,
      "logical_full_history_bytes_after": 169390080
    },
    {
      "step": 79,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1617920,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1355284480,
      "read_start_seconds_exact": "524913/1562500",
      "read_finish_seconds_exact": "42517953/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "42517953/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1638400,
      "logical_full_history_bytes_after": 169410560
    },
    {
      "step": 80,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1638400,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1355448320,
      "read_start_seconds_exact": "42517953/125000000",
      "read_finish_seconds_exact": "21521433/62500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "21521433/62500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1658880,
      "logical_full_history_bytes_after": 169431040
    },
    {
      "step": 81,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1658880,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1355612160,
      "read_start_seconds_exact": "21521433/62500000",
      "read_finish_seconds_exact": "43567779/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "43567779/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1679360,
      "logical_full_history_bytes_after": 169451520
    },
    {
      "step": 82,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1679360,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1355776000,
      "read_start_seconds_exact": "43567779/125000000",
      "read_finish_seconds_exact": "11023173/31250000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "11023173/31250000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1699840,
      "logical_full_history_bytes_after": 169472000
    },
    {
      "step": 83,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1699840,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1355939840,
      "read_start_seconds_exact": "11023173/31250000",
      "read_finish_seconds_exact": "8923521/25000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "8923521/25000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1720320,
      "logical_full_history_bytes_after": 169492480
    },
    {
      "step": 84,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1720320,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1356103680,
      "read_start_seconds_exact": "8923521/25000000",
      "read_finish_seconds_exact": "22571259/62500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "22571259/62500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1740800,
      "logical_full_history_bytes_after": 169512960
    },
    {
      "step": 85,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1740800,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1356267520,
      "read_start_seconds_exact": "22571259/62500000",
      "read_finish_seconds_exact": "45667431/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "45667431/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1761280,
      "logical_full_history_bytes_after": 169533440
    },
    {
      "step": 86,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1761280,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1356431360,
      "read_start_seconds_exact": "45667431/125000000",
      "read_finish_seconds_exact": "5774043/15625000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "5774043/15625000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1781760,
      "logical_full_history_bytes_after": 169553920
    },
    {
      "step": 87,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1781760,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1356595200,
      "read_start_seconds_exact": "5774043/15625000",
      "read_finish_seconds_exact": "46717257/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "46717257/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1802240,
      "logical_full_history_bytes_after": 169574400
    },
    {
      "step": 88,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1802240,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1356759040,
      "read_start_seconds_exact": "46717257/125000000",
      "read_finish_seconds_exact": "4724217/12500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "4724217/12500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1822720,
      "logical_full_history_bytes_after": 169594880
    },
    {
      "step": 89,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1822720,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1356922880,
      "read_start_seconds_exact": "4724217/12500000",
      "read_finish_seconds_exact": "47767083/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "47767083/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1843200,
      "logical_full_history_bytes_after": 169615360
    },
    {
      "step": 90,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1843200,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1357086720,
      "read_start_seconds_exact": "47767083/125000000",
      "read_finish_seconds_exact": "12072999/31250000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "12072999/31250000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1863680,
      "logical_full_history_bytes_after": 169635840
    },
    {
      "step": 91,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1863680,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1357250560,
      "read_start_seconds_exact": "12072999/31250000",
      "read_finish_seconds_exact": "48816909/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "48816909/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1884160,
      "logical_full_history_bytes_after": 169656320
    },
    {
      "step": 92,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1884160,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1357414400,
      "read_start_seconds_exact": "48816909/125000000",
      "read_finish_seconds_exact": "24670911/62500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "24670911/62500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1904640,
      "logical_full_history_bytes_after": 169676800
    },
    {
      "step": 93,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1904640,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1357578240,
      "read_start_seconds_exact": "24670911/62500000",
      "read_finish_seconds_exact": "9973347/25000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "9973347/25000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1925120,
      "logical_full_history_bytes_after": 169697280
    },
    {
      "step": 94,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1925120,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1357742080,
      "read_start_seconds_exact": "9973347/25000000",
      "read_finish_seconds_exact": "1574739/3906250",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "1574739/3906250",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1945600,
      "logical_full_history_bytes_after": 169717760
    },
    {
      "step": 95,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1945600,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1357905920,
      "read_start_seconds_exact": "1574739/3906250",
      "read_finish_seconds_exact": "50916561/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "50916561/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1966080,
      "logical_full_history_bytes_after": 169738240
    },
    {
      "step": 96,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1966080,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1358069760,
      "read_start_seconds_exact": "50916561/125000000",
      "read_finish_seconds_exact": "25720737/62500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "25720737/62500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1986560,
      "logical_full_history_bytes_after": 169758720
    },
    {
      "step": 97,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 1986560,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1358233600,
      "read_start_seconds_exact": "25720737/62500000",
      "read_finish_seconds_exact": "51966387/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "51966387/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 2007040,
      "logical_full_history_bytes_after": 169779200
    },
    {
      "step": 98,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 2007040,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1358397440,
      "read_start_seconds_exact": "51966387/125000000",
      "read_finish_seconds_exact": "524913/1250000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "524913/1250000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 2027520,
      "logical_full_history_bytes_after": 169799680
    },
    {
      "step": 99,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 2027520,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1358561280,
      "read_start_seconds_exact": "524913/1250000",
      "read_finish_seconds_exact": "53016213/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "53016213/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 2048000,
      "logical_full_history_bytes_after": 169820160
    },
    {
      "step": 100,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 2048000,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1358725120,
      "read_start_seconds_exact": "53016213/125000000",
      "read_finish_seconds_exact": "26770563/62500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "26770563/62500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 2068480,
      "logical_full_history_bytes_after": 169840640
    },
    {
      "step": 101,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 2068480,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1358888960,
      "read_start_seconds_exact": "26770563/62500000",
      "read_finish_seconds_exact": "54066039/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "54066039/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 2088960,
      "logical_full_history_bytes_after": 169861120
    },
    {
      "step": 102,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 2088960,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1359052800,
      "read_start_seconds_exact": "54066039/125000000",
      "read_finish_seconds_exact": "6823869/15625000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "6823869/15625000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 2109440,
      "logical_full_history_bytes_after": 169881600
    },
    {
      "step": 103,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 2109440,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1359216640,
      "read_start_seconds_exact": "6823869/15625000",
      "read_finish_seconds_exact": "11023173/25000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "11023173/25000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 2129920,
      "logical_full_history_bytes_after": 169902080
    },
    {
      "step": 104,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 2129920,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1359380480,
      "read_start_seconds_exact": "11023173/25000000",
      "read_finish_seconds_exact": "27820389/62500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "27820389/62500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 2150400,
      "logical_full_history_bytes_after": 169922560
    },
    {
      "step": 105,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 2150400,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1359544320,
      "read_start_seconds_exact": "27820389/62500000",
      "read_finish_seconds_exact": "56165691/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "56165691/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 2170880,
      "logical_full_history_bytes_after": 169943040
    },
    {
      "step": 106,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 2170880,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1359708160,
      "read_start_seconds_exact": "56165691/125000000",
      "read_finish_seconds_exact": "14172651/31250000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "14172651/31250000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 2191360,
      "logical_full_history_bytes_after": 169963520
    },
    {
      "step": 107,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 2191360,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1359872000,
      "read_start_seconds_exact": "14172651/31250000",
      "read_finish_seconds_exact": "57215517/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "57215517/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 2211840,
      "logical_full_history_bytes_after": 169984000
    },
    {
      "step": 108,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 2211840,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1360035840,
      "read_start_seconds_exact": "57215517/125000000",
      "read_finish_seconds_exact": "5774043/12500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "5774043/12500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 2232320,
      "logical_full_history_bytes_after": 170004480
    },
    {
      "step": 109,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 2232320,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1360199680,
      "read_start_seconds_exact": "5774043/12500000",
      "read_finish_seconds_exact": "58265343/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "58265343/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 2252800,
      "logical_full_history_bytes_after": 170024960
    },
    {
      "step": 110,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 2252800,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1360363520,
      "read_start_seconds_exact": "58265343/125000000",
      "read_finish_seconds_exact": "3674391/7812500",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "3674391/7812500",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 2273280,
      "logical_full_history_bytes_after": 170045440
    },
    {
      "step": 111,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 2273280,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1360527360,
      "read_start_seconds_exact": "3674391/7812500",
      "read_finish_seconds_exact": "59315169/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "59315169/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 2293760,
      "logical_full_history_bytes_after": 170065920
    },
    {
      "step": 112,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 2293760,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1360691200,
      "read_start_seconds_exact": "59315169/125000000",
      "read_finish_seconds_exact": "29920041/62500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "29920041/62500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 2314240,
      "logical_full_history_bytes_after": 170086400
    },
    {
      "step": 113,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 2314240,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1360855040,
      "read_start_seconds_exact": "29920041/62500000",
      "read_finish_seconds_exact": "12072999/25000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "12072999/25000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 2334720,
      "logical_full_history_bytes_after": 170106880
    },
    {
      "step": 114,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 2334720,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1361018880,
      "read_start_seconds_exact": "12072999/25000000",
      "read_finish_seconds_exact": "15222477/31250000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "15222477/31250000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 2355200,
      "logical_full_history_bytes_after": 170127360
    },
    {
      "step": 115,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 2355200,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1361182720,
      "read_start_seconds_exact": "15222477/31250000",
      "read_finish_seconds_exact": "61414821/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "61414821/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 2375680,
      "logical_full_history_bytes_after": 170147840
    },
    {
      "step": 116,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 2375680,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1361346560,
      "read_start_seconds_exact": "61414821/125000000",
      "read_finish_seconds_exact": "30969867/62500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "30969867/62500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 2396160,
      "logical_full_history_bytes_after": 170168320
    },
    {
      "step": 117,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 2396160,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1361510400,
      "read_start_seconds_exact": "30969867/62500000",
      "read_finish_seconds_exact": "62464647/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "62464647/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 2416640,
      "logical_full_history_bytes_after": 170188800
    },
    {
      "step": 118,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 2416640,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1361674240,
      "read_start_seconds_exact": "62464647/125000000",
      "read_finish_seconds_exact": "1574739/3125000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "1574739/3125000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 2437120,
      "logical_full_history_bytes_after": 170209280
    },
    {
      "step": 119,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 2437120,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1361838080,
      "read_start_seconds_exact": "1574739/3125000",
      "read_finish_seconds_exact": "63514473/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "63514473/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 2457600,
      "logical_full_history_bytes_after": 170229760
    },
    {
      "step": 120,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 2457600,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1362001920,
      "read_start_seconds_exact": "63514473/125000000",
      "read_finish_seconds_exact": "32019693/62500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "32019693/62500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 2478080,
      "logical_full_history_bytes_after": 170250240
    },
    {
      "step": 121,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 2478080,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1362165760,
      "read_start_seconds_exact": "32019693/62500000",
      "read_finish_seconds_exact": "64564299/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "64564299/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 2498560,
      "logical_full_history_bytes_after": 170270720
    },
    {
      "step": 122,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 2498560,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1362329600,
      "read_start_seconds_exact": "64564299/125000000",
      "read_finish_seconds_exact": "16272303/31250000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "16272303/31250000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 2519040,
      "logical_full_history_bytes_after": 170291200
    },
    {
      "step": 123,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 2519040,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1362493440,
      "read_start_seconds_exact": "16272303/31250000",
      "read_finish_seconds_exact": "524913/1000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "524913/1000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 2539520,
      "logical_full_history_bytes_after": 170311680
    },
    {
      "step": 124,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 2539520,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1362657280,
      "read_start_seconds_exact": "524913/1000000",
      "read_finish_seconds_exact": "33069519/62500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "33069519/62500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 2560000,
      "logical_full_history_bytes_after": 170332160
    },
    {
      "step": 125,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 2560000,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1362821120,
      "read_start_seconds_exact": "33069519/62500000",
      "read_finish_seconds_exact": "66663951/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "66663951/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 2580480,
      "logical_full_history_bytes_after": 170352640
    },
    {
      "step": 126,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 2580480,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1362984960,
      "read_start_seconds_exact": "66663951/125000000",
      "read_finish_seconds_exact": "1049826/1953125",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "1049826/1953125",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 2600960,
      "logical_full_history_bytes_after": 170373120
    },
    {
      "step": 127,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 167772160,
      "local_prior_read_bytes": 2600960,
      "current_kv_operand_bytes": 20480,
      "full_attention_qk_pv_flops": 1363148800,
      "read_start_seconds_exact": "1049826/1953125",
      "read_finish_seconds_exact": "67713777/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "67713777/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 2621440,
      "logical_full_history_bytes_after": 170393600
    }
  ],
  "summary": {
    "full_attention_qk_pv_flops": 173151354880,
    "initial_copy_network_bytes": 167772160,
    "prior_history_logical_read_bytes": 21641297920,
    "remote_prior_read_bytes": 21474836480,
    "local_prior_read_bytes": 166461440,
    "current_kv_operand_bytes": 2621440,
    "append_replica_network_bytes": 0,
    "total_network_bytes": 21642608640,
    "remote_final_bytes_per_replica": 167772160,
    "remote_physical_final_bytes": 167772160,
    "local_tail_final_bytes": 2621440,
    "local_fixed_state_bytes": 64880640,
    "local_current_append_buffer_bytes": 20480,
    "final_unique_history_bytes": 170393600,
    "local_tail_budget_fits": false,
    "communication_skeleton_seconds_exact": "67713777/125000000",
    "initial_copy_seconds_exact": "524913/125000000",
    "token_communication_seconds_exact": "1049826/1953125",
    "actual_decode_seconds": null,
    "actual_task_feasible": null
  },
  "assumptions": [
    "所有配置/实现原件校验后使用；BF16完整attention KV按层/头计，Qwen3.6仅10层保存全历史KV，30层FP32递推和BF16卷积槽留在计算节点，不传成历史序列。",
    "prompt是已产生的KV位置数；steps是追加单token forward次数。输入token/输出token移位明确，当前位置操作数不混入远端旧历史读取。给出的QK/PV仅完整attention子账，不含投影/专家/DeltaNet等全部计算。",
    "remote_all复制完整prompt，逐步读一个副本的所有旧位置，再将新位置发给每个副本；共享发送接口串行写入，全副本提交屏障保证下一步所有可选副本都达到要求epoch。没有实现真实一致性协议或原子性证明。",
    "remote_prefix_local_tail保持远端prompt不变，新增位置留本地；每步远端prefix和本地tail各读一次。全部模型层仍需要本地递推/卷积等状态，尾部预算只检查新增完整attention KV，不是整机容量。",
    "初始化和每消息startup+bytes/B均为声明串行传输模型。当前KV生成完成后才可追加，但计算时长和与网络重叠未知；时间轴只列通信骨架，不能视为真实decode latency或吞吐。",
    "新KV在本地先产生，current append buffer另列，不和已增长tail盲目相加为内存峰值。远端读缓存/临时buffer/控制消息/ACK/重试/故障检测及恢复未计，不推测厂商能力。",
    "初始拷贝计从外部已产出的prompt向各副本的发送；原始prompt源是否释放另由上层所有权协议决定，不计成已释放容量。副本只增加存储/写入与静态冗余，不自动增加读带宽。"
  ]
}
```
