# 增长KV：远端历史、追加副本与提交epoch

## 场景

```json
{
  "model": "qwen3-8b",
  "batch": 1,
  "prompt": 8192,
  "steps": 128,
  "copies": 1,
  "placement": "remote_prefix_local_tail",
  "bandwidth_bytes_per_second": 40000000000,
  "startup_ns": 5000,
  "local_tail_budget_bytes": 1073741824
}
```

| 汇总 | 值 |
|---|---:|
| full_attention_qk_pv_flops | 623344877568 |
| initial_copy_network_bytes | 1207959552 |
| prior_history_logical_read_bytes | 155817345024 |
| remote_prior_read_bytes | 154618822656 |
| local_prior_read_bytes | 1198522368 |
| current_kv_operand_bytes | 18874368 |
| append_replica_network_bytes | 0 |
| total_network_bytes | 155826782208 |
| remote_final_bytes_per_replica | 1207959552 |
| remote_physical_final_bytes | 1207959552 |
| local_tail_final_bytes | 18874368 |
| local_fixed_state_bytes | 0 |
| local_current_append_buffer_bytes | 147456 |
| final_unique_history_bytes | 1226833920 |
| local_tail_budget_fits | True |
| communication_skeleton_seconds_exact | 2435196597/625000000 |
| initial_copy_seconds_exact | 18877493/625000000 |
| token_communication_seconds_exact | 37754986/9765625 |
| actual_decode_seconds | None |
| actual_task_feasible | None |

| 步 | 所需远端epoch | 远端旧历史bytes | 本地旧历史bytes | 当前KVbytes | 副本写bytes | 提交秒 | 本地tailbytes |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 | 8192 | 1207959552 | 0 | 147456 | 0 | 0.060407978 | 147456 |
| 1 | 8192 | 1207959552 | 147456 | 147456 | 0 | 0.090611966 | 294912 |
| 2 | 8192 | 1207959552 | 294912 | 147456 | 0 | 0.120815955 | 442368 |
| 3 | 8192 | 1207959552 | 442368 | 147456 | 0 | 0.151019944 | 589824 |
| 4 | 8192 | 1207959552 | 589824 | 147456 | 0 | 0.181223933 | 737280 |
| 5 | 8192 | 1207959552 | 737280 | 147456 | 0 | 0.211427922 | 884736 |
| 6 | 8192 | 1207959552 | 884736 | 147456 | 0 | 0.241631910 | 1032192 |
| 7 | 8192 | 1207959552 | 1032192 | 147456 | 0 | 0.271835899 | 1179648 |
| 8 | 8192 | 1207959552 | 1179648 | 147456 | 0 | 0.302039888 | 1327104 |
| 9 | 8192 | 1207959552 | 1327104 | 147456 | 0 | 0.332243877 | 1474560 |
| 10 | 8192 | 1207959552 | 1474560 | 147456 | 0 | 0.362447866 | 1622016 |
| 11 | 8192 | 1207959552 | 1622016 | 147456 | 0 | 0.392651854 | 1769472 |
| 12 | 8192 | 1207959552 | 1769472 | 147456 | 0 | 0.422855843 | 1916928 |
| 13 | 8192 | 1207959552 | 1916928 | 147456 | 0 | 0.453059832 | 2064384 |
| 14 | 8192 | 1207959552 | 2064384 | 147456 | 0 | 0.483263821 | 2211840 |
| 15 | 8192 | 1207959552 | 2211840 | 147456 | 0 | 0.513467810 | 2359296 |
| 16 | 8192 | 1207959552 | 2359296 | 147456 | 0 | 0.543671798 | 2506752 |
| 17 | 8192 | 1207959552 | 2506752 | 147456 | 0 | 0.573875787 | 2654208 |
| 18 | 8192 | 1207959552 | 2654208 | 147456 | 0 | 0.604079776 | 2801664 |
| 19 | 8192 | 1207959552 | 2801664 | 147456 | 0 | 0.634283765 | 2949120 |
| 20 | 8192 | 1207959552 | 2949120 | 147456 | 0 | 0.664487754 | 3096576 |
| 21 | 8192 | 1207959552 | 3096576 | 147456 | 0 | 0.694691742 | 3244032 |
| 22 | 8192 | 1207959552 | 3244032 | 147456 | 0 | 0.724895731 | 3391488 |
| 23 | 8192 | 1207959552 | 3391488 | 147456 | 0 | 0.755099720 | 3538944 |
| 24 | 8192 | 1207959552 | 3538944 | 147456 | 0 | 0.785303709 | 3686400 |
| 25 | 8192 | 1207959552 | 3686400 | 147456 | 0 | 0.815507698 | 3833856 |
| 26 | 8192 | 1207959552 | 3833856 | 147456 | 0 | 0.845711686 | 3981312 |
| 27 | 8192 | 1207959552 | 3981312 | 147456 | 0 | 0.875915675 | 4128768 |
| 28 | 8192 | 1207959552 | 4128768 | 147456 | 0 | 0.906119664 | 4276224 |
| 29 | 8192 | 1207959552 | 4276224 | 147456 | 0 | 0.936323653 | 4423680 |
| 30 | 8192 | 1207959552 | 4423680 | 147456 | 0 | 0.966527642 | 4571136 |
| 31 | 8192 | 1207959552 | 4571136 | 147456 | 0 | 0.996731630 | 4718592 |
| 32 | 8192 | 1207959552 | 4718592 | 147456 | 0 | 1.026935619 | 4866048 |
| 33 | 8192 | 1207959552 | 4866048 | 147456 | 0 | 1.057139608 | 5013504 |
| 34 | 8192 | 1207959552 | 5013504 | 147456 | 0 | 1.087343597 | 5160960 |
| 35 | 8192 | 1207959552 | 5160960 | 147456 | 0 | 1.117547586 | 5308416 |
| 36 | 8192 | 1207959552 | 5308416 | 147456 | 0 | 1.147751574 | 5455872 |
| 37 | 8192 | 1207959552 | 5455872 | 147456 | 0 | 1.177955563 | 5603328 |
| 38 | 8192 | 1207959552 | 5603328 | 147456 | 0 | 1.208159552 | 5750784 |
| 39 | 8192 | 1207959552 | 5750784 | 147456 | 0 | 1.238363541 | 5898240 |
| 40 | 8192 | 1207959552 | 5898240 | 147456 | 0 | 1.268567530 | 6045696 |
| 41 | 8192 | 1207959552 | 6045696 | 147456 | 0 | 1.298771518 | 6193152 |
| 42 | 8192 | 1207959552 | 6193152 | 147456 | 0 | 1.328975507 | 6340608 |
| 43 | 8192 | 1207959552 | 6340608 | 147456 | 0 | 1.359179496 | 6488064 |
| 44 | 8192 | 1207959552 | 6488064 | 147456 | 0 | 1.389383485 | 6635520 |
| 45 | 8192 | 1207959552 | 6635520 | 147456 | 0 | 1.419587474 | 6782976 |
| 46 | 8192 | 1207959552 | 6782976 | 147456 | 0 | 1.449791462 | 6930432 |
| 47 | 8192 | 1207959552 | 6930432 | 147456 | 0 | 1.479995451 | 7077888 |
| 48 | 8192 | 1207959552 | 7077888 | 147456 | 0 | 1.510199440 | 7225344 |
| 49 | 8192 | 1207959552 | 7225344 | 147456 | 0 | 1.540403429 | 7372800 |
| 50 | 8192 | 1207959552 | 7372800 | 147456 | 0 | 1.570607418 | 7520256 |
| 51 | 8192 | 1207959552 | 7520256 | 147456 | 0 | 1.600811406 | 7667712 |
| 52 | 8192 | 1207959552 | 7667712 | 147456 | 0 | 1.631015395 | 7815168 |
| 53 | 8192 | 1207959552 | 7815168 | 147456 | 0 | 1.661219384 | 7962624 |
| 54 | 8192 | 1207959552 | 7962624 | 147456 | 0 | 1.691423373 | 8110080 |
| 55 | 8192 | 1207959552 | 8110080 | 147456 | 0 | 1.721627362 | 8257536 |
| 56 | 8192 | 1207959552 | 8257536 | 147456 | 0 | 1.751831350 | 8404992 |
| 57 | 8192 | 1207959552 | 8404992 | 147456 | 0 | 1.782035339 | 8552448 |
| 58 | 8192 | 1207959552 | 8552448 | 147456 | 0 | 1.812239328 | 8699904 |
| 59 | 8192 | 1207959552 | 8699904 | 147456 | 0 | 1.842443317 | 8847360 |
| 60 | 8192 | 1207959552 | 8847360 | 147456 | 0 | 1.872647306 | 8994816 |
| 61 | 8192 | 1207959552 | 8994816 | 147456 | 0 | 1.902851294 | 9142272 |
| 62 | 8192 | 1207959552 | 9142272 | 147456 | 0 | 1.933055283 | 9289728 |
| 63 | 8192 | 1207959552 | 9289728 | 147456 | 0 | 1.963259272 | 9437184 |
| 64 | 8192 | 1207959552 | 9437184 | 147456 | 0 | 1.993463261 | 9584640 |
| 65 | 8192 | 1207959552 | 9584640 | 147456 | 0 | 2.023667250 | 9732096 |
| 66 | 8192 | 1207959552 | 9732096 | 147456 | 0 | 2.053871238 | 9879552 |
| 67 | 8192 | 1207959552 | 9879552 | 147456 | 0 | 2.084075227 | 10027008 |
| 68 | 8192 | 1207959552 | 10027008 | 147456 | 0 | 2.114279216 | 10174464 |
| 69 | 8192 | 1207959552 | 10174464 | 147456 | 0 | 2.144483205 | 10321920 |
| 70 | 8192 | 1207959552 | 10321920 | 147456 | 0 | 2.174687194 | 10469376 |
| 71 | 8192 | 1207959552 | 10469376 | 147456 | 0 | 2.204891182 | 10616832 |
| 72 | 8192 | 1207959552 | 10616832 | 147456 | 0 | 2.235095171 | 10764288 |
| 73 | 8192 | 1207959552 | 10764288 | 147456 | 0 | 2.265299160 | 10911744 |
| 74 | 8192 | 1207959552 | 10911744 | 147456 | 0 | 2.295503149 | 11059200 |
| 75 | 8192 | 1207959552 | 11059200 | 147456 | 0 | 2.325707138 | 11206656 |
| 76 | 8192 | 1207959552 | 11206656 | 147456 | 0 | 2.355911126 | 11354112 |
| 77 | 8192 | 1207959552 | 11354112 | 147456 | 0 | 2.386115115 | 11501568 |
| 78 | 8192 | 1207959552 | 11501568 | 147456 | 0 | 2.416319104 | 11649024 |
| 79 | 8192 | 1207959552 | 11649024 | 147456 | 0 | 2.446523093 | 11796480 |
| 80 | 8192 | 1207959552 | 11796480 | 147456 | 0 | 2.476727082 | 11943936 |
| 81 | 8192 | 1207959552 | 11943936 | 147456 | 0 | 2.506931070 | 12091392 |
| 82 | 8192 | 1207959552 | 12091392 | 147456 | 0 | 2.537135059 | 12238848 |
| 83 | 8192 | 1207959552 | 12238848 | 147456 | 0 | 2.567339048 | 12386304 |
| 84 | 8192 | 1207959552 | 12386304 | 147456 | 0 | 2.597543037 | 12533760 |
| 85 | 8192 | 1207959552 | 12533760 | 147456 | 0 | 2.627747026 | 12681216 |
| 86 | 8192 | 1207959552 | 12681216 | 147456 | 0 | 2.657951014 | 12828672 |
| 87 | 8192 | 1207959552 | 12828672 | 147456 | 0 | 2.688155003 | 12976128 |
| 88 | 8192 | 1207959552 | 12976128 | 147456 | 0 | 2.718358992 | 13123584 |
| 89 | 8192 | 1207959552 | 13123584 | 147456 | 0 | 2.748562981 | 13271040 |
| 90 | 8192 | 1207959552 | 13271040 | 147456 | 0 | 2.778766970 | 13418496 |
| 91 | 8192 | 1207959552 | 13418496 | 147456 | 0 | 2.808970958 | 13565952 |
| 92 | 8192 | 1207959552 | 13565952 | 147456 | 0 | 2.839174947 | 13713408 |
| 93 | 8192 | 1207959552 | 13713408 | 147456 | 0 | 2.869378936 | 13860864 |
| 94 | 8192 | 1207959552 | 13860864 | 147456 | 0 | 2.899582925 | 14008320 |
| 95 | 8192 | 1207959552 | 14008320 | 147456 | 0 | 2.929786914 | 14155776 |
| 96 | 8192 | 1207959552 | 14155776 | 147456 | 0 | 2.959990902 | 14303232 |
| 97 | 8192 | 1207959552 | 14303232 | 147456 | 0 | 2.990194891 | 14450688 |
| 98 | 8192 | 1207959552 | 14450688 | 147456 | 0 | 3.020398880 | 14598144 |
| 99 | 8192 | 1207959552 | 14598144 | 147456 | 0 | 3.050602869 | 14745600 |
| 100 | 8192 | 1207959552 | 14745600 | 147456 | 0 | 3.080806858 | 14893056 |
| 101 | 8192 | 1207959552 | 14893056 | 147456 | 0 | 3.111010846 | 15040512 |
| 102 | 8192 | 1207959552 | 15040512 | 147456 | 0 | 3.141214835 | 15187968 |
| 103 | 8192 | 1207959552 | 15187968 | 147456 | 0 | 3.171418824 | 15335424 |
| 104 | 8192 | 1207959552 | 15335424 | 147456 | 0 | 3.201622813 | 15482880 |
| 105 | 8192 | 1207959552 | 15482880 | 147456 | 0 | 3.231826802 | 15630336 |
| 106 | 8192 | 1207959552 | 15630336 | 147456 | 0 | 3.262030790 | 15777792 |
| 107 | 8192 | 1207959552 | 15777792 | 147456 | 0 | 3.292234779 | 15925248 |
| 108 | 8192 | 1207959552 | 15925248 | 147456 | 0 | 3.322438768 | 16072704 |
| 109 | 8192 | 1207959552 | 16072704 | 147456 | 0 | 3.352642757 | 16220160 |
| 110 | 8192 | 1207959552 | 16220160 | 147456 | 0 | 3.382846746 | 16367616 |
| 111 | 8192 | 1207959552 | 16367616 | 147456 | 0 | 3.413050734 | 16515072 |
| 112 | 8192 | 1207959552 | 16515072 | 147456 | 0 | 3.443254723 | 16662528 |
| 113 | 8192 | 1207959552 | 16662528 | 147456 | 0 | 3.473458712 | 16809984 |
| 114 | 8192 | 1207959552 | 16809984 | 147456 | 0 | 3.503662701 | 16957440 |
| 115 | 8192 | 1207959552 | 16957440 | 147456 | 0 | 3.533866690 | 17104896 |
| 116 | 8192 | 1207959552 | 17104896 | 147456 | 0 | 3.564070678 | 17252352 |
| 117 | 8192 | 1207959552 | 17252352 | 147456 | 0 | 3.594274667 | 17399808 |
| 118 | 8192 | 1207959552 | 17399808 | 147456 | 0 | 3.624478656 | 17547264 |
| 119 | 8192 | 1207959552 | 17547264 | 147456 | 0 | 3.654682645 | 17694720 |
| 120 | 8192 | 1207959552 | 17694720 | 147456 | 0 | 3.684886634 | 17842176 |
| 121 | 8192 | 1207959552 | 17842176 | 147456 | 0 | 3.715090622 | 17989632 |
| 122 | 8192 | 1207959552 | 17989632 | 147456 | 0 | 3.745294611 | 18137088 |
| 123 | 8192 | 1207959552 | 18137088 | 147456 | 0 | 3.775498600 | 18284544 |
| 124 | 8192 | 1207959552 | 18284544 | 147456 | 0 | 3.805702589 | 18432000 |
| 125 | 8192 | 1207959552 | 18432000 | 147456 | 0 | 3.835906578 | 18579456 |
| 126 | 8192 | 1207959552 | 18579456 | 147456 | 0 | 3.866110566 | 18726912 |
| 127 | 8192 | 1207959552 | 18726912 | 147456 | 0 | 3.896314555 | 18874368 |

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
    "model": "qwen3-8b",
    "batch": 1,
    "prompt": 8192,
    "steps": 128,
    "copies": 1,
    "placement": "remote_prefix_local_tail",
    "bandwidth_bytes_per_second": 40000000000,
    "startup_ns": 5000,
    "local_tail_budget_bytes": 1073741824
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
  "geometry": {
    "model": "qwen3-8b",
    "full_attention_layers": 36,
    "linear_layers": 0,
    "kv_bytes_per_position": 147456,
    "qk_pv_flops_per_position_pair": 589824,
    "local_recurrent_bytes_per_request": 0,
    "local_convolution_bytes_per_request": 0,
    "max_positions": 40960
  },
  "initial_copy_messages": [
    {
      "replica": 0,
      "bytes": 1207959552
    }
  ],
  "steps": [
    {
      "step": 0,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4832428032,
      "read_start_seconds_exact": "18877493/625000000",
      "read_finish_seconds_exact": "18877493/312500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "18877493/312500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 147456,
      "logical_full_history_bytes_after": 1208107008
    },
    {
      "step": 1,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 147456,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4833017856,
      "read_start_seconds_exact": "18877493/312500000",
      "read_finish_seconds_exact": "56632479/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "56632479/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 294912,
      "logical_full_history_bytes_after": 1208254464
    },
    {
      "step": 2,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 294912,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4833607680,
      "read_start_seconds_exact": "56632479/625000000",
      "read_finish_seconds_exact": "18877493/156250000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "18877493/156250000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 442368,
      "logical_full_history_bytes_after": 1208401920
    },
    {
      "step": 3,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 442368,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4834197504,
      "read_start_seconds_exact": "18877493/156250000",
      "read_finish_seconds_exact": "18877493/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "18877493/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 589824,
      "logical_full_history_bytes_after": 1208549376
    },
    {
      "step": 4,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 589824,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4834787328,
      "read_start_seconds_exact": "18877493/125000000",
      "read_finish_seconds_exact": "56632479/312500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "56632479/312500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 737280,
      "logical_full_history_bytes_after": 1208696832
    },
    {
      "step": 5,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 737280,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4835377152,
      "read_start_seconds_exact": "56632479/312500000",
      "read_finish_seconds_exact": "132142451/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "132142451/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 884736,
      "logical_full_history_bytes_after": 1208844288
    },
    {
      "step": 6,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 884736,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4835966976,
      "read_start_seconds_exact": "132142451/625000000",
      "read_finish_seconds_exact": "18877493/78125000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "18877493/78125000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1032192,
      "logical_full_history_bytes_after": 1208991744
    },
    {
      "step": 7,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 1032192,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4836556800,
      "read_start_seconds_exact": "18877493/78125000",
      "read_finish_seconds_exact": "169897437/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "169897437/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1179648,
      "logical_full_history_bytes_after": 1209139200
    },
    {
      "step": 8,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 1179648,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4837146624,
      "read_start_seconds_exact": "169897437/625000000",
      "read_finish_seconds_exact": "18877493/62500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "18877493/62500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1327104,
      "logical_full_history_bytes_after": 1209286656
    },
    {
      "step": 9,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 1327104,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4837736448,
      "read_start_seconds_exact": "18877493/62500000",
      "read_finish_seconds_exact": "207652423/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "207652423/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1474560,
      "logical_full_history_bytes_after": 1209434112
    },
    {
      "step": 10,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 1474560,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4838326272,
      "read_start_seconds_exact": "207652423/625000000",
      "read_finish_seconds_exact": "56632479/156250000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "56632479/156250000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1622016,
      "logical_full_history_bytes_after": 1209581568
    },
    {
      "step": 11,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 1622016,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4838916096,
      "read_start_seconds_exact": "56632479/156250000",
      "read_finish_seconds_exact": "245407409/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "245407409/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1769472,
      "logical_full_history_bytes_after": 1209729024
    },
    {
      "step": 12,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 1769472,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4839505920,
      "read_start_seconds_exact": "245407409/625000000",
      "read_finish_seconds_exact": "132142451/312500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "132142451/312500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 1916928,
      "logical_full_history_bytes_after": 1209876480
    },
    {
      "step": 13,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 1916928,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4840095744,
      "read_start_seconds_exact": "132142451/312500000",
      "read_finish_seconds_exact": "56632479/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "56632479/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 2064384,
      "logical_full_history_bytes_after": 1210023936
    },
    {
      "step": 14,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 2064384,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4840685568,
      "read_start_seconds_exact": "56632479/125000000",
      "read_finish_seconds_exact": "18877493/39062500",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "18877493/39062500",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 2211840,
      "logical_full_history_bytes_after": 1210171392
    },
    {
      "step": 15,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 2211840,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4841275392,
      "read_start_seconds_exact": "18877493/39062500",
      "read_finish_seconds_exact": "320917381/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "320917381/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 2359296,
      "logical_full_history_bytes_after": 1210318848
    },
    {
      "step": 16,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 2359296,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4841865216,
      "read_start_seconds_exact": "320917381/625000000",
      "read_finish_seconds_exact": "169897437/312500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "169897437/312500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 2506752,
      "logical_full_history_bytes_after": 1210466304
    },
    {
      "step": 17,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 2506752,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4842455040,
      "read_start_seconds_exact": "169897437/312500000",
      "read_finish_seconds_exact": "358672367/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "358672367/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 2654208,
      "logical_full_history_bytes_after": 1210613760
    },
    {
      "step": 18,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 2654208,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4843044864,
      "read_start_seconds_exact": "358672367/625000000",
      "read_finish_seconds_exact": "18877493/31250000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "18877493/31250000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 2801664,
      "logical_full_history_bytes_after": 1210761216
    },
    {
      "step": 19,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 2801664,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4843634688,
      "read_start_seconds_exact": "18877493/31250000",
      "read_finish_seconds_exact": "396427353/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "396427353/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 2949120,
      "logical_full_history_bytes_after": 1210908672
    },
    {
      "step": 20,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 2949120,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4844224512,
      "read_start_seconds_exact": "396427353/625000000",
      "read_finish_seconds_exact": "207652423/312500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "207652423/312500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 3096576,
      "logical_full_history_bytes_after": 1211056128
    },
    {
      "step": 21,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 3096576,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4844814336,
      "read_start_seconds_exact": "207652423/312500000",
      "read_finish_seconds_exact": "434182339/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "434182339/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 3244032,
      "logical_full_history_bytes_after": 1211203584
    },
    {
      "step": 22,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 3244032,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4845404160,
      "read_start_seconds_exact": "434182339/625000000",
      "read_finish_seconds_exact": "56632479/78125000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "56632479/78125000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 3391488,
      "logical_full_history_bytes_after": 1211351040
    },
    {
      "step": 23,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 3391488,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4845993984,
      "read_start_seconds_exact": "56632479/78125000",
      "read_finish_seconds_exact": "18877493/25000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "18877493/25000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 3538944,
      "logical_full_history_bytes_after": 1211498496
    },
    {
      "step": 24,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 3538944,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4846583808,
      "read_start_seconds_exact": "18877493/25000000",
      "read_finish_seconds_exact": "245407409/312500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "245407409/312500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 3686400,
      "logical_full_history_bytes_after": 1211645952
    },
    {
      "step": 25,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 3686400,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4847173632,
      "read_start_seconds_exact": "245407409/312500000",
      "read_finish_seconds_exact": "509692311/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "509692311/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 3833856,
      "logical_full_history_bytes_after": 1211793408
    },
    {
      "step": 26,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 3833856,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4847763456,
      "read_start_seconds_exact": "509692311/625000000",
      "read_finish_seconds_exact": "132142451/156250000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "132142451/156250000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 3981312,
      "logical_full_history_bytes_after": 1211940864
    },
    {
      "step": 27,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 3981312,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4848353280,
      "read_start_seconds_exact": "132142451/156250000",
      "read_finish_seconds_exact": "547447297/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "547447297/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 4128768,
      "logical_full_history_bytes_after": 1212088320
    },
    {
      "step": 28,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 4128768,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4848943104,
      "read_start_seconds_exact": "547447297/625000000",
      "read_finish_seconds_exact": "56632479/62500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "56632479/62500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 4276224,
      "logical_full_history_bytes_after": 1212235776
    },
    {
      "step": 29,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 4276224,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4849532928,
      "read_start_seconds_exact": "56632479/62500000",
      "read_finish_seconds_exact": "585202283/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "585202283/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 4423680,
      "logical_full_history_bytes_after": 1212383232
    },
    {
      "step": 30,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 4423680,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4850122752,
      "read_start_seconds_exact": "585202283/625000000",
      "read_finish_seconds_exact": "18877493/19531250",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "18877493/19531250",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 4571136,
      "logical_full_history_bytes_after": 1212530688
    },
    {
      "step": 31,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 4571136,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4850712576,
      "read_start_seconds_exact": "18877493/19531250",
      "read_finish_seconds_exact": "622957269/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "622957269/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 4718592,
      "logical_full_history_bytes_after": 1212678144
    },
    {
      "step": 32,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 4718592,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4851302400,
      "read_start_seconds_exact": "622957269/625000000",
      "read_finish_seconds_exact": "320917381/312500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "320917381/312500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 4866048,
      "logical_full_history_bytes_after": 1212825600
    },
    {
      "step": 33,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 4866048,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4851892224,
      "read_start_seconds_exact": "320917381/312500000",
      "read_finish_seconds_exact": "132142451/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "132142451/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 5013504,
      "logical_full_history_bytes_after": 1212973056
    },
    {
      "step": 34,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 5013504,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4852482048,
      "read_start_seconds_exact": "132142451/125000000",
      "read_finish_seconds_exact": "169897437/156250000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "169897437/156250000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 5160960,
      "logical_full_history_bytes_after": 1213120512
    },
    {
      "step": 35,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 5160960,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4853071872,
      "read_start_seconds_exact": "169897437/156250000",
      "read_finish_seconds_exact": "698467241/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "698467241/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 5308416,
      "logical_full_history_bytes_after": 1213267968
    },
    {
      "step": 36,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 5308416,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4853661696,
      "read_start_seconds_exact": "698467241/625000000",
      "read_finish_seconds_exact": "358672367/312500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "358672367/312500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 5455872,
      "logical_full_history_bytes_after": 1213415424
    },
    {
      "step": 37,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 5455872,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4854251520,
      "read_start_seconds_exact": "358672367/312500000",
      "read_finish_seconds_exact": "736222227/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "736222227/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 5603328,
      "logical_full_history_bytes_after": 1213562880
    },
    {
      "step": 38,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 5603328,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4854841344,
      "read_start_seconds_exact": "736222227/625000000",
      "read_finish_seconds_exact": "18877493/15625000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "18877493/15625000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 5750784,
      "logical_full_history_bytes_after": 1213710336
    },
    {
      "step": 39,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 5750784,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4855431168,
      "read_start_seconds_exact": "18877493/15625000",
      "read_finish_seconds_exact": "773977213/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "773977213/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 5898240,
      "logical_full_history_bytes_after": 1213857792
    },
    {
      "step": 40,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 5898240,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4856020992,
      "read_start_seconds_exact": "773977213/625000000",
      "read_finish_seconds_exact": "396427353/312500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "396427353/312500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 6045696,
      "logical_full_history_bytes_after": 1214005248
    },
    {
      "step": 41,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 6045696,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4856610816,
      "read_start_seconds_exact": "396427353/312500000",
      "read_finish_seconds_exact": "811732199/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "811732199/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 6193152,
      "logical_full_history_bytes_after": 1214152704
    },
    {
      "step": 42,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 6193152,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4857200640,
      "read_start_seconds_exact": "811732199/625000000",
      "read_finish_seconds_exact": "207652423/156250000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "207652423/156250000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 6340608,
      "logical_full_history_bytes_after": 1214300160
    },
    {
      "step": 43,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 6340608,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4857790464,
      "read_start_seconds_exact": "207652423/156250000",
      "read_finish_seconds_exact": "169897437/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "169897437/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 6488064,
      "logical_full_history_bytes_after": 1214447616
    },
    {
      "step": 44,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 6488064,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4858380288,
      "read_start_seconds_exact": "169897437/125000000",
      "read_finish_seconds_exact": "434182339/312500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "434182339/312500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 6635520,
      "logical_full_history_bytes_after": 1214595072
    },
    {
      "step": 45,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 6635520,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4858970112,
      "read_start_seconds_exact": "434182339/312500000",
      "read_finish_seconds_exact": "887242171/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "887242171/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 6782976,
      "logical_full_history_bytes_after": 1214742528
    },
    {
      "step": 46,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 6782976,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4859559936,
      "read_start_seconds_exact": "887242171/625000000",
      "read_finish_seconds_exact": "56632479/39062500",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "56632479/39062500",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 6930432,
      "logical_full_history_bytes_after": 1214889984
    },
    {
      "step": 47,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 6930432,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4860149760,
      "read_start_seconds_exact": "56632479/39062500",
      "read_finish_seconds_exact": "924997157/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "924997157/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 7077888,
      "logical_full_history_bytes_after": 1215037440
    },
    {
      "step": 48,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 7077888,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4860739584,
      "read_start_seconds_exact": "924997157/625000000",
      "read_finish_seconds_exact": "18877493/12500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "18877493/12500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 7225344,
      "logical_full_history_bytes_after": 1215184896
    },
    {
      "step": 49,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 7225344,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4861329408,
      "read_start_seconds_exact": "18877493/12500000",
      "read_finish_seconds_exact": "962752143/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "962752143/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 7372800,
      "logical_full_history_bytes_after": 1215332352
    },
    {
      "step": 50,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 7372800,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4861919232,
      "read_start_seconds_exact": "962752143/625000000",
      "read_finish_seconds_exact": "245407409/156250000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "245407409/156250000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 7520256,
      "logical_full_history_bytes_after": 1215479808
    },
    {
      "step": 51,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 7520256,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4862509056,
      "read_start_seconds_exact": "245407409/156250000",
      "read_finish_seconds_exact": "1000507129/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "1000507129/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 7667712,
      "logical_full_history_bytes_after": 1215627264
    },
    {
      "step": 52,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 7667712,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4863098880,
      "read_start_seconds_exact": "1000507129/625000000",
      "read_finish_seconds_exact": "509692311/312500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "509692311/312500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 7815168,
      "logical_full_history_bytes_after": 1215774720
    },
    {
      "step": 53,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 7815168,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4863688704,
      "read_start_seconds_exact": "509692311/312500000",
      "read_finish_seconds_exact": "207652423/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "207652423/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 7962624,
      "logical_full_history_bytes_after": 1215922176
    },
    {
      "step": 54,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 7962624,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4864278528,
      "read_start_seconds_exact": "207652423/125000000",
      "read_finish_seconds_exact": "132142451/78125000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "132142451/78125000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 8110080,
      "logical_full_history_bytes_after": 1216069632
    },
    {
      "step": 55,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 8110080,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4864868352,
      "read_start_seconds_exact": "132142451/78125000",
      "read_finish_seconds_exact": "1076017101/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "1076017101/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 8257536,
      "logical_full_history_bytes_after": 1216217088
    },
    {
      "step": 56,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 8257536,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4865458176,
      "read_start_seconds_exact": "1076017101/625000000",
      "read_finish_seconds_exact": "547447297/312500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "547447297/312500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 8404992,
      "logical_full_history_bytes_after": 1216364544
    },
    {
      "step": 57,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 8404992,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4866048000,
      "read_start_seconds_exact": "547447297/312500000",
      "read_finish_seconds_exact": "1113772087/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "1113772087/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 8552448,
      "logical_full_history_bytes_after": 1216512000
    },
    {
      "step": 58,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 8552448,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4866637824,
      "read_start_seconds_exact": "1113772087/625000000",
      "read_finish_seconds_exact": "56632479/31250000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "56632479/31250000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 8699904,
      "logical_full_history_bytes_after": 1216659456
    },
    {
      "step": 59,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 8699904,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4867227648,
      "read_start_seconds_exact": "56632479/31250000",
      "read_finish_seconds_exact": "1151527073/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "1151527073/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 8847360,
      "logical_full_history_bytes_after": 1216806912
    },
    {
      "step": 60,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 8847360,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4867817472,
      "read_start_seconds_exact": "1151527073/625000000",
      "read_finish_seconds_exact": "585202283/312500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "585202283/312500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 8994816,
      "logical_full_history_bytes_after": 1216954368
    },
    {
      "step": 61,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 8994816,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4868407296,
      "read_start_seconds_exact": "585202283/312500000",
      "read_finish_seconds_exact": "1189282059/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "1189282059/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 9142272,
      "logical_full_history_bytes_after": 1217101824
    },
    {
      "step": 62,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 9142272,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4868997120,
      "read_start_seconds_exact": "1189282059/625000000",
      "read_finish_seconds_exact": "18877493/9765625",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "18877493/9765625",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 9289728,
      "logical_full_history_bytes_after": 1217249280
    },
    {
      "step": 63,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 9289728,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4869586944,
      "read_start_seconds_exact": "18877493/9765625",
      "read_finish_seconds_exact": "245407409/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "245407409/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 9437184,
      "logical_full_history_bytes_after": 1217396736
    },
    {
      "step": 64,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 9437184,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4870176768,
      "read_start_seconds_exact": "245407409/125000000",
      "read_finish_seconds_exact": "622957269/312500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "622957269/312500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 9584640,
      "logical_full_history_bytes_after": 1217544192
    },
    {
      "step": 65,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 9584640,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4870766592,
      "read_start_seconds_exact": "622957269/312500000",
      "read_finish_seconds_exact": "1264792031/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "1264792031/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 9732096,
      "logical_full_history_bytes_after": 1217691648
    },
    {
      "step": 66,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 9732096,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4871356416,
      "read_start_seconds_exact": "1264792031/625000000",
      "read_finish_seconds_exact": "320917381/156250000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "320917381/156250000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 9879552,
      "logical_full_history_bytes_after": 1217839104
    },
    {
      "step": 67,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 9879552,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4871946240,
      "read_start_seconds_exact": "320917381/156250000",
      "read_finish_seconds_exact": "1302547017/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "1302547017/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 10027008,
      "logical_full_history_bytes_after": 1217986560
    },
    {
      "step": 68,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 10027008,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4872536064,
      "read_start_seconds_exact": "1302547017/625000000",
      "read_finish_seconds_exact": "132142451/62500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "132142451/62500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 10174464,
      "logical_full_history_bytes_after": 1218134016
    },
    {
      "step": 69,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 10174464,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4873125888,
      "read_start_seconds_exact": "132142451/62500000",
      "read_finish_seconds_exact": "1340302003/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "1340302003/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 10321920,
      "logical_full_history_bytes_after": 1218281472
    },
    {
      "step": 70,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 10321920,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4873715712,
      "read_start_seconds_exact": "1340302003/625000000",
      "read_finish_seconds_exact": "169897437/78125000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "169897437/78125000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 10469376,
      "logical_full_history_bytes_after": 1218428928
    },
    {
      "step": 71,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 10469376,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4874305536,
      "read_start_seconds_exact": "169897437/78125000",
      "read_finish_seconds_exact": "1378056989/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "1378056989/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 10616832,
      "logical_full_history_bytes_after": 1218576384
    },
    {
      "step": 72,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 10616832,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4874895360,
      "read_start_seconds_exact": "1378056989/625000000",
      "read_finish_seconds_exact": "698467241/312500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "698467241/312500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 10764288,
      "logical_full_history_bytes_after": 1218723840
    },
    {
      "step": 73,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 10764288,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4875485184,
      "read_start_seconds_exact": "698467241/312500000",
      "read_finish_seconds_exact": "56632479/25000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "56632479/25000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 10911744,
      "logical_full_history_bytes_after": 1218871296
    },
    {
      "step": 74,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 10911744,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4876075008,
      "read_start_seconds_exact": "56632479/25000000",
      "read_finish_seconds_exact": "358672367/156250000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "358672367/156250000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 11059200,
      "logical_full_history_bytes_after": 1219018752
    },
    {
      "step": 75,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 11059200,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4876664832,
      "read_start_seconds_exact": "358672367/156250000",
      "read_finish_seconds_exact": "1453566961/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "1453566961/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 11206656,
      "logical_full_history_bytes_after": 1219166208
    },
    {
      "step": 76,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 11206656,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4877254656,
      "read_start_seconds_exact": "1453566961/625000000",
      "read_finish_seconds_exact": "736222227/312500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "736222227/312500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 11354112,
      "logical_full_history_bytes_after": 1219313664
    },
    {
      "step": 77,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 11354112,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4877844480,
      "read_start_seconds_exact": "736222227/312500000",
      "read_finish_seconds_exact": "1491321947/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "1491321947/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 11501568,
      "logical_full_history_bytes_after": 1219461120
    },
    {
      "step": 78,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 11501568,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4878434304,
      "read_start_seconds_exact": "1491321947/625000000",
      "read_finish_seconds_exact": "18877493/7812500",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "18877493/7812500",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 11649024,
      "logical_full_history_bytes_after": 1219608576
    },
    {
      "step": 79,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 11649024,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4879024128,
      "read_start_seconds_exact": "18877493/7812500",
      "read_finish_seconds_exact": "1529076933/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "1529076933/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 11796480,
      "logical_full_history_bytes_after": 1219756032
    },
    {
      "step": 80,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 11796480,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4879613952,
      "read_start_seconds_exact": "1529076933/625000000",
      "read_finish_seconds_exact": "773977213/312500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "773977213/312500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 11943936,
      "logical_full_history_bytes_after": 1219903488
    },
    {
      "step": 81,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 11943936,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4880203776,
      "read_start_seconds_exact": "773977213/312500000",
      "read_finish_seconds_exact": "1566831919/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "1566831919/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 12091392,
      "logical_full_history_bytes_after": 1220050944
    },
    {
      "step": 82,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 12091392,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4880793600,
      "read_start_seconds_exact": "1566831919/625000000",
      "read_finish_seconds_exact": "396427353/156250000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "396427353/156250000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 12238848,
      "logical_full_history_bytes_after": 1220198400
    },
    {
      "step": 83,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 12238848,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4881383424,
      "read_start_seconds_exact": "396427353/156250000",
      "read_finish_seconds_exact": "320917381/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "320917381/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 12386304,
      "logical_full_history_bytes_after": 1220345856
    },
    {
      "step": 84,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 12386304,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4881973248,
      "read_start_seconds_exact": "320917381/125000000",
      "read_finish_seconds_exact": "811732199/312500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "811732199/312500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 12533760,
      "logical_full_history_bytes_after": 1220493312
    },
    {
      "step": 85,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 12533760,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4882563072,
      "read_start_seconds_exact": "811732199/312500000",
      "read_finish_seconds_exact": "1642341891/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "1642341891/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 12681216,
      "logical_full_history_bytes_after": 1220640768
    },
    {
      "step": 86,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 12681216,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4883152896,
      "read_start_seconds_exact": "1642341891/625000000",
      "read_finish_seconds_exact": "207652423/78125000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "207652423/78125000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 12828672,
      "logical_full_history_bytes_after": 1220788224
    },
    {
      "step": 87,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 12828672,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4883742720,
      "read_start_seconds_exact": "207652423/78125000",
      "read_finish_seconds_exact": "1680096877/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "1680096877/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 12976128,
      "logical_full_history_bytes_after": 1220935680
    },
    {
      "step": 88,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 12976128,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4884332544,
      "read_start_seconds_exact": "1680096877/625000000",
      "read_finish_seconds_exact": "169897437/62500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "169897437/62500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 13123584,
      "logical_full_history_bytes_after": 1221083136
    },
    {
      "step": 89,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 13123584,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4884922368,
      "read_start_seconds_exact": "169897437/62500000",
      "read_finish_seconds_exact": "1717851863/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "1717851863/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 13271040,
      "logical_full_history_bytes_after": 1221230592
    },
    {
      "step": 90,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 13271040,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4885512192,
      "read_start_seconds_exact": "1717851863/625000000",
      "read_finish_seconds_exact": "434182339/156250000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "434182339/156250000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 13418496,
      "logical_full_history_bytes_after": 1221378048
    },
    {
      "step": 91,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 13418496,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4886102016,
      "read_start_seconds_exact": "434182339/156250000",
      "read_finish_seconds_exact": "1755606849/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "1755606849/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 13565952,
      "logical_full_history_bytes_after": 1221525504
    },
    {
      "step": 92,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 13565952,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4886691840,
      "read_start_seconds_exact": "1755606849/625000000",
      "read_finish_seconds_exact": "887242171/312500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "887242171/312500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 13713408,
      "logical_full_history_bytes_after": 1221672960
    },
    {
      "step": 93,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 13713408,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4887281664,
      "read_start_seconds_exact": "887242171/312500000",
      "read_finish_seconds_exact": "358672367/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "358672367/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 13860864,
      "logical_full_history_bytes_after": 1221820416
    },
    {
      "step": 94,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 13860864,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4887871488,
      "read_start_seconds_exact": "358672367/125000000",
      "read_finish_seconds_exact": "56632479/19531250",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "56632479/19531250",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 14008320,
      "logical_full_history_bytes_after": 1221967872
    },
    {
      "step": 95,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 14008320,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4888461312,
      "read_start_seconds_exact": "56632479/19531250",
      "read_finish_seconds_exact": "1831116821/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "1831116821/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 14155776,
      "logical_full_history_bytes_after": 1222115328
    },
    {
      "step": 96,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 14155776,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4889051136,
      "read_start_seconds_exact": "1831116821/625000000",
      "read_finish_seconds_exact": "924997157/312500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "924997157/312500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 14303232,
      "logical_full_history_bytes_after": 1222262784
    },
    {
      "step": 97,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 14303232,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4889640960,
      "read_start_seconds_exact": "924997157/312500000",
      "read_finish_seconds_exact": "1868871807/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "1868871807/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 14450688,
      "logical_full_history_bytes_after": 1222410240
    },
    {
      "step": 98,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 14450688,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4890230784,
      "read_start_seconds_exact": "1868871807/625000000",
      "read_finish_seconds_exact": "18877493/6250000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "18877493/6250000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 14598144,
      "logical_full_history_bytes_after": 1222557696
    },
    {
      "step": 99,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 14598144,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4890820608,
      "read_start_seconds_exact": "18877493/6250000",
      "read_finish_seconds_exact": "1906626793/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "1906626793/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 14745600,
      "logical_full_history_bytes_after": 1222705152
    },
    {
      "step": 100,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 14745600,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4891410432,
      "read_start_seconds_exact": "1906626793/625000000",
      "read_finish_seconds_exact": "962752143/312500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "962752143/312500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 14893056,
      "logical_full_history_bytes_after": 1222852608
    },
    {
      "step": 101,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 14893056,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4892000256,
      "read_start_seconds_exact": "962752143/312500000",
      "read_finish_seconds_exact": "1944381779/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "1944381779/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 15040512,
      "logical_full_history_bytes_after": 1223000064
    },
    {
      "step": 102,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 15040512,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4892590080,
      "read_start_seconds_exact": "1944381779/625000000",
      "read_finish_seconds_exact": "245407409/78125000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "245407409/78125000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 15187968,
      "logical_full_history_bytes_after": 1223147520
    },
    {
      "step": 103,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 15187968,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4893179904,
      "read_start_seconds_exact": "245407409/78125000",
      "read_finish_seconds_exact": "396427353/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "396427353/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 15335424,
      "logical_full_history_bytes_after": 1223294976
    },
    {
      "step": 104,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 15335424,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4893769728,
      "read_start_seconds_exact": "396427353/125000000",
      "read_finish_seconds_exact": "1000507129/312500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "1000507129/312500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 15482880,
      "logical_full_history_bytes_after": 1223442432
    },
    {
      "step": 105,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 15482880,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4894359552,
      "read_start_seconds_exact": "1000507129/312500000",
      "read_finish_seconds_exact": "2019891751/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "2019891751/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 15630336,
      "logical_full_history_bytes_after": 1223589888
    },
    {
      "step": 106,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 15630336,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4894949376,
      "read_start_seconds_exact": "2019891751/625000000",
      "read_finish_seconds_exact": "509692311/156250000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "509692311/156250000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 15777792,
      "logical_full_history_bytes_after": 1223737344
    },
    {
      "step": 107,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 15777792,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4895539200,
      "read_start_seconds_exact": "509692311/156250000",
      "read_finish_seconds_exact": "2057646737/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "2057646737/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 15925248,
      "logical_full_history_bytes_after": 1223884800
    },
    {
      "step": 108,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 15925248,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4896129024,
      "read_start_seconds_exact": "2057646737/625000000",
      "read_finish_seconds_exact": "207652423/62500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "207652423/62500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 16072704,
      "logical_full_history_bytes_after": 1224032256
    },
    {
      "step": 109,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 16072704,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4896718848,
      "read_start_seconds_exact": "207652423/62500000",
      "read_finish_seconds_exact": "2095401723/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "2095401723/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 16220160,
      "logical_full_history_bytes_after": 1224179712
    },
    {
      "step": 110,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 16220160,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4897308672,
      "read_start_seconds_exact": "2095401723/625000000",
      "read_finish_seconds_exact": "132142451/39062500",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "132142451/39062500",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 16367616,
      "logical_full_history_bytes_after": 1224327168
    },
    {
      "step": 111,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 16367616,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4897898496,
      "read_start_seconds_exact": "132142451/39062500",
      "read_finish_seconds_exact": "2133156709/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "2133156709/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 16515072,
      "logical_full_history_bytes_after": 1224474624
    },
    {
      "step": 112,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 16515072,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4898488320,
      "read_start_seconds_exact": "2133156709/625000000",
      "read_finish_seconds_exact": "1076017101/312500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "1076017101/312500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 16662528,
      "logical_full_history_bytes_after": 1224622080
    },
    {
      "step": 113,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 16662528,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4899078144,
      "read_start_seconds_exact": "1076017101/312500000",
      "read_finish_seconds_exact": "434182339/125000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "434182339/125000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 16809984,
      "logical_full_history_bytes_after": 1224769536
    },
    {
      "step": 114,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 16809984,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4899667968,
      "read_start_seconds_exact": "434182339/125000000",
      "read_finish_seconds_exact": "547447297/156250000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "547447297/156250000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 16957440,
      "logical_full_history_bytes_after": 1224916992
    },
    {
      "step": 115,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 16957440,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4900257792,
      "read_start_seconds_exact": "547447297/156250000",
      "read_finish_seconds_exact": "2208666681/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "2208666681/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 17104896,
      "logical_full_history_bytes_after": 1225064448
    },
    {
      "step": 116,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 17104896,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4900847616,
      "read_start_seconds_exact": "2208666681/625000000",
      "read_finish_seconds_exact": "1113772087/312500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "1113772087/312500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 17252352,
      "logical_full_history_bytes_after": 1225211904
    },
    {
      "step": 117,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 17252352,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4901437440,
      "read_start_seconds_exact": "1113772087/312500000",
      "read_finish_seconds_exact": "2246421667/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "2246421667/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 17399808,
      "logical_full_history_bytes_after": 1225359360
    },
    {
      "step": 118,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 17399808,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4902027264,
      "read_start_seconds_exact": "2246421667/625000000",
      "read_finish_seconds_exact": "56632479/15625000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "56632479/15625000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 17547264,
      "logical_full_history_bytes_after": 1225506816
    },
    {
      "step": 119,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 17547264,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4902617088,
      "read_start_seconds_exact": "56632479/15625000",
      "read_finish_seconds_exact": "2284176653/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "2284176653/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 17694720,
      "logical_full_history_bytes_after": 1225654272
    },
    {
      "step": 120,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 17694720,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4903206912,
      "read_start_seconds_exact": "2284176653/625000000",
      "read_finish_seconds_exact": "1151527073/312500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "1151527073/312500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 17842176,
      "logical_full_history_bytes_after": 1225801728
    },
    {
      "step": 121,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 17842176,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4903796736,
      "read_start_seconds_exact": "1151527073/312500000",
      "read_finish_seconds_exact": "2321931639/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "2321931639/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 17989632,
      "logical_full_history_bytes_after": 1225949184
    },
    {
      "step": 122,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 17989632,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4904386560,
      "read_start_seconds_exact": "2321931639/625000000",
      "read_finish_seconds_exact": "585202283/156250000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "585202283/156250000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 18137088,
      "logical_full_history_bytes_after": 1226096640
    },
    {
      "step": 123,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 18137088,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4904976384,
      "read_start_seconds_exact": "585202283/156250000",
      "read_finish_seconds_exact": "18877493/5000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "18877493/5000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 18284544,
      "logical_full_history_bytes_after": 1226244096
    },
    {
      "step": 124,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 18284544,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4905566208,
      "read_start_seconds_exact": "18877493/5000000",
      "read_finish_seconds_exact": "1189282059/312500000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "1189282059/312500000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 18432000,
      "logical_full_history_bytes_after": 1226391552
    },
    {
      "step": 125,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 18432000,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4906156032,
      "read_start_seconds_exact": "1189282059/312500000",
      "read_finish_seconds_exact": "2397441611/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "2397441611/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 18579456,
      "logical_full_history_bytes_after": 1226539008
    },
    {
      "step": 126,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 18579456,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4906745856,
      "read_start_seconds_exact": "2397441611/625000000",
      "read_finish_seconds_exact": "37754986/9765625",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "37754986/9765625",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 18726912,
      "logical_full_history_bytes_after": 1226686464
    },
    {
      "step": 127,
      "required_remote_epoch": 8192,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1207959552,
      "local_prior_read_bytes": 18726912,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4907335680,
      "read_start_seconds_exact": "37754986/9765625",
      "read_finish_seconds_exact": "2435196597/625000000",
      "replica_writes": [],
      "all_replica_commit_seconds_exact": "2435196597/625000000",
      "remote_lengths_after": [
        8192
      ],
      "local_tail_bytes_after": 18874368,
      "logical_full_history_bytes_after": 1226833920
    }
  ],
  "summary": {
    "full_attention_qk_pv_flops": 623344877568,
    "initial_copy_network_bytes": 1207959552,
    "prior_history_logical_read_bytes": 155817345024,
    "remote_prior_read_bytes": 154618822656,
    "local_prior_read_bytes": 1198522368,
    "current_kv_operand_bytes": 18874368,
    "append_replica_network_bytes": 0,
    "total_network_bytes": 155826782208,
    "remote_final_bytes_per_replica": 1207959552,
    "remote_physical_final_bytes": 1207959552,
    "local_tail_final_bytes": 18874368,
    "local_fixed_state_bytes": 0,
    "local_current_append_buffer_bytes": 147456,
    "final_unique_history_bytes": 1226833920,
    "local_tail_budget_fits": true,
    "communication_skeleton_seconds_exact": "2435196597/625000000",
    "initial_copy_seconds_exact": "18877493/625000000",
    "token_communication_seconds_exact": "37754986/9765625",
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
