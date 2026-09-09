# 增长KV：远端历史、追加副本与提交epoch

## 场景

```json
{
  "model": "qwen3-8b",
  "batch": 1,
  "prompt": 8192,
  "steps": 128,
  "copies": 2,
  "placement": "remote_all",
  "bandwidth_bytes_per_second": 40000000000,
  "startup_ns": 5000,
  "local_tail_budget_bytes": 1073741824
}
```

| 汇总 | 值 |
|---|---:|
| full_attention_qk_pv_flops | 623344877568 |
| initial_copy_network_bytes | 2415919104 |
| prior_history_logical_read_bytes | 155817345024 |
| remote_prior_read_bytes | 155817345024 |
| local_prior_read_bytes | 0 |
| current_kv_operand_bytes | 18874368 |
| append_replica_network_bytes | 37748736 |
| total_network_bytes | 158271012864 |
| remote_final_bytes_per_replica | 1226833920 |
| remote_physical_final_bytes | 2453667840 |
| local_tail_final_bytes | 0 |
| local_fixed_state_bytes | 0 |
| local_current_append_buffer_bytes | 147456 |
| final_unique_history_bytes | 1226833920 |
| local_tail_budget_fits | True |
| communication_skeleton_seconds_exact | 1237095413/312500000 |
| initial_copy_seconds_exact | 18877493/312500000 |
| token_communication_seconds_exact | 7613862/1953125 |
| actual_decode_seconds | None |
| actual_task_feasible | None |

| 步 | 所需远端epoch | 远端旧历史bytes | 本地旧历史bytes | 当前KVbytes | 副本写bytes | 提交秒 | 本地tailbytes |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 | 8192 | 1207959552 | 0 | 147456 | 294912 | 0.090629339 | 0 |
| 1 | 8193 | 1208107008 | 0 | 147456 | 294912 | 0.120854387 | 0 |
| 2 | 8194 | 1208254464 | 0 | 147456 | 294912 | 0.151083122 | 0 |
| 3 | 8195 | 1208401920 | 0 | 147456 | 294912 | 0.181315542 | 0 |
| 4 | 8196 | 1208549376 | 0 | 147456 | 294912 | 0.211551650 | 0 |
| 5 | 8197 | 1208696832 | 0 | 147456 | 294912 | 0.241791443 | 0 |
| 6 | 8198 | 1208844288 | 0 | 147456 | 294912 | 0.272034923 | 0 |
| 7 | 8199 | 1208991744 | 0 | 147456 | 294912 | 0.302282090 | 0 |
| 8 | 8200 | 1209139200 | 0 | 147456 | 294912 | 0.332532942 | 0 |
| 9 | 8201 | 1209286656 | 0 | 147456 | 294912 | 0.362787482 | 0 |
| 10 | 8202 | 1209434112 | 0 | 147456 | 294912 | 0.393045707 | 0 |
| 11 | 8203 | 1209581568 | 0 | 147456 | 294912 | 0.423307619 | 0 |
| 12 | 8204 | 1209729024 | 0 | 147456 | 294912 | 0.453573218 | 0 |
| 13 | 8205 | 1209876480 | 0 | 147456 | 294912 | 0.483842502 | 0 |
| 14 | 8206 | 1210023936 | 0 | 147456 | 294912 | 0.514115474 | 0 |
| 15 | 8207 | 1210171392 | 0 | 147456 | 294912 | 0.544392131 | 0 |
| 16 | 8208 | 1210318848 | 0 | 147456 | 294912 | 0.574672475 | 0 |
| 17 | 8209 | 1210466304 | 0 | 147456 | 294912 | 0.604956506 | 0 |
| 18 | 8210 | 1210613760 | 0 | 147456 | 294912 | 0.635244222 | 0 |
| 19 | 8211 | 1210761216 | 0 | 147456 | 294912 | 0.665535626 | 0 |
| 20 | 8212 | 1210908672 | 0 | 147456 | 294912 | 0.695830715 | 0 |
| 21 | 8213 | 1211056128 | 0 | 147456 | 294912 | 0.726129491 | 0 |
| 22 | 8214 | 1211203584 | 0 | 147456 | 294912 | 0.756431954 | 0 |
| 23 | 8215 | 1211351040 | 0 | 147456 | 294912 | 0.786738102 | 0 |
| 24 | 8216 | 1211498496 | 0 | 147456 | 294912 | 0.817047938 | 0 |
| 25 | 8217 | 1211645952 | 0 | 147456 | 294912 | 0.847361459 | 0 |
| 26 | 8218 | 1211793408 | 0 | 147456 | 294912 | 0.877678667 | 0 |
| 27 | 8219 | 1211940864 | 0 | 147456 | 294912 | 0.907999562 | 0 |
| 28 | 8220 | 1212088320 | 0 | 147456 | 294912 | 0.938324142 | 0 |
| 29 | 8221 | 1212235776 | 0 | 147456 | 294912 | 0.968652410 | 0 |
| 30 | 8222 | 1212383232 | 0 | 147456 | 294912 | 0.998984363 | 0 |
| 31 | 8223 | 1212530688 | 0 | 147456 | 294912 | 1.029320003 | 0 |
| 32 | 8224 | 1212678144 | 0 | 147456 | 294912 | 1.059659330 | 0 |
| 33 | 8225 | 1212825600 | 0 | 147456 | 294912 | 1.090002342 | 0 |
| 34 | 8226 | 1212973056 | 0 | 147456 | 294912 | 1.120349042 | 0 |
| 35 | 8227 | 1213120512 | 0 | 147456 | 294912 | 1.150699427 | 0 |
| 36 | 8228 | 1213267968 | 0 | 147456 | 294912 | 1.181053499 | 0 |
| 37 | 8229 | 1213415424 | 0 | 147456 | 294912 | 1.211411258 | 0 |
| 38 | 8230 | 1213562880 | 0 | 147456 | 294912 | 1.241772702 | 0 |
| 39 | 8231 | 1213710336 | 0 | 147456 | 294912 | 1.272137834 | 0 |
| 40 | 8232 | 1213857792 | 0 | 147456 | 294912 | 1.302506651 | 0 |
| 41 | 8233 | 1214005248 | 0 | 147456 | 294912 | 1.332879155 | 0 |
| 42 | 8234 | 1214152704 | 0 | 147456 | 294912 | 1.363255346 | 0 |
| 43 | 8235 | 1214300160 | 0 | 147456 | 294912 | 1.393635222 | 0 |
| 44 | 8236 | 1214447616 | 0 | 147456 | 294912 | 1.424018786 | 0 |
| 45 | 8237 | 1214595072 | 0 | 147456 | 294912 | 1.454406035 | 0 |
| 46 | 8238 | 1214742528 | 0 | 147456 | 294912 | 1.484796971 | 0 |
| 47 | 8239 | 1214889984 | 0 | 147456 | 294912 | 1.515191594 | 0 |
| 48 | 8240 | 1215037440 | 0 | 147456 | 294912 | 1.545589902 | 0 |
| 49 | 8241 | 1215184896 | 0 | 147456 | 294912 | 1.575991898 | 0 |
| 50 | 8242 | 1215332352 | 0 | 147456 | 294912 | 1.606397579 | 0 |
| 51 | 8243 | 1215479808 | 0 | 147456 | 294912 | 1.636806947 | 0 |
| 52 | 8244 | 1215627264 | 0 | 147456 | 294912 | 1.667220002 | 0 |
| 53 | 8245 | 1215774720 | 0 | 147456 | 294912 | 1.697636742 | 0 |
| 54 | 8246 | 1215922176 | 0 | 147456 | 294912 | 1.728057170 | 0 |
| 55 | 8247 | 1216069632 | 0 | 147456 | 294912 | 1.758481283 | 0 |
| 56 | 8248 | 1216217088 | 0 | 147456 | 294912 | 1.788909083 | 0 |
| 57 | 8249 | 1216364544 | 0 | 147456 | 294912 | 1.819340570 | 0 |
| 58 | 8250 | 1216512000 | 0 | 147456 | 294912 | 1.849775742 | 0 |
| 59 | 8251 | 1216659456 | 0 | 147456 | 294912 | 1.880214602 | 0 |
| 60 | 8252 | 1216806912 | 0 | 147456 | 294912 | 1.910657147 | 0 |
| 61 | 8253 | 1216954368 | 0 | 147456 | 294912 | 1.941103379 | 0 |
| 62 | 8254 | 1217101824 | 0 | 147456 | 294912 | 1.971553298 | 0 |
| 63 | 8255 | 1217249280 | 0 | 147456 | 294912 | 2.002006902 | 0 |
| 64 | 8256 | 1217396736 | 0 | 147456 | 294912 | 2.032464194 | 0 |
| 65 | 8257 | 1217544192 | 0 | 147456 | 294912 | 2.062925171 | 0 |
| 66 | 8258 | 1217691648 | 0 | 147456 | 294912 | 2.093389835 | 0 |
| 67 | 8259 | 1217839104 | 0 | 147456 | 294912 | 2.123858186 | 0 |
| 68 | 8260 | 1217986560 | 0 | 147456 | 294912 | 2.154330222 | 0 |
| 69 | 8261 | 1218134016 | 0 | 147456 | 294912 | 2.184805946 | 0 |
| 70 | 8262 | 1218281472 | 0 | 147456 | 294912 | 2.215285355 | 0 |
| 71 | 8263 | 1218428928 | 0 | 147456 | 294912 | 2.245768451 | 0 |
| 72 | 8264 | 1218576384 | 0 | 147456 | 294912 | 2.276255234 | 0 |
| 73 | 8265 | 1218723840 | 0 | 147456 | 294912 | 2.306745702 | 0 |
| 74 | 8266 | 1218871296 | 0 | 147456 | 294912 | 2.337239858 | 0 |
| 75 | 8267 | 1219018752 | 0 | 147456 | 294912 | 2.367737699 | 0 |
| 76 | 8268 | 1219166208 | 0 | 147456 | 294912 | 2.398239227 | 0 |
| 77 | 8269 | 1219313664 | 0 | 147456 | 294912 | 2.428744442 | 0 |
| 78 | 8270 | 1219461120 | 0 | 147456 | 294912 | 2.459253342 | 0 |
| 79 | 8271 | 1219608576 | 0 | 147456 | 294912 | 2.489765930 | 0 |
| 80 | 8272 | 1219756032 | 0 | 147456 | 294912 | 2.520282203 | 0 |
| 81 | 8273 | 1219903488 | 0 | 147456 | 294912 | 2.550802163 | 0 |
| 82 | 8274 | 1220050944 | 0 | 147456 | 294912 | 2.581325810 | 0 |
| 83 | 8275 | 1220198400 | 0 | 147456 | 294912 | 2.611853142 | 0 |
| 84 | 8276 | 1220345856 | 0 | 147456 | 294912 | 2.642384162 | 0 |
| 85 | 8277 | 1220493312 | 0 | 147456 | 294912 | 2.672918867 | 0 |
| 86 | 8278 | 1220640768 | 0 | 147456 | 294912 | 2.703457259 | 0 |
| 87 | 8279 | 1220788224 | 0 | 147456 | 294912 | 2.733999338 | 0 |
| 88 | 8280 | 1220935680 | 0 | 147456 | 294912 | 2.764545102 | 0 |
| 89 | 8281 | 1221083136 | 0 | 147456 | 294912 | 2.795094554 | 0 |
| 90 | 8282 | 1221230592 | 0 | 147456 | 294912 | 2.825647691 | 0 |
| 91 | 8283 | 1221378048 | 0 | 147456 | 294912 | 2.856204515 | 0 |
| 92 | 8284 | 1221525504 | 0 | 147456 | 294912 | 2.886765026 | 0 |
| 93 | 8285 | 1221672960 | 0 | 147456 | 294912 | 2.917329222 | 0 |
| 94 | 8286 | 1221820416 | 0 | 147456 | 294912 | 2.947897106 | 0 |
| 95 | 8287 | 1221967872 | 0 | 147456 | 294912 | 2.978468675 | 0 |
| 96 | 8288 | 1222115328 | 0 | 147456 | 294912 | 3.009043931 | 0 |
| 97 | 8289 | 1222262784 | 0 | 147456 | 294912 | 3.039622874 | 0 |
| 98 | 8290 | 1222410240 | 0 | 147456 | 294912 | 3.070205502 | 0 |
| 99 | 8291 | 1222557696 | 0 | 147456 | 294912 | 3.100791818 | 0 |
| 100 | 8292 | 1222705152 | 0 | 147456 | 294912 | 3.131381819 | 0 |
| 101 | 8293 | 1222852608 | 0 | 147456 | 294912 | 3.161975507 | 0 |
| 102 | 8294 | 1223000064 | 0 | 147456 | 294912 | 3.192572882 | 0 |
| 103 | 8295 | 1223147520 | 0 | 147456 | 294912 | 3.223173942 | 0 |
| 104 | 8296 | 1223294976 | 0 | 147456 | 294912 | 3.253778690 | 0 |
| 105 | 8297 | 1223442432 | 0 | 147456 | 294912 | 3.284387123 | 0 |
| 106 | 8298 | 1223589888 | 0 | 147456 | 294912 | 3.314999243 | 0 |
| 107 | 8299 | 1223737344 | 0 | 147456 | 294912 | 3.345615050 | 0 |
| 108 | 8300 | 1223884800 | 0 | 147456 | 294912 | 3.376234542 | 0 |
| 109 | 8301 | 1224032256 | 0 | 147456 | 294912 | 3.406857722 | 0 |
| 110 | 8302 | 1224179712 | 0 | 147456 | 294912 | 3.437484587 | 0 |
| 111 | 8303 | 1224327168 | 0 | 147456 | 294912 | 3.468115139 | 0 |
| 112 | 8304 | 1224474624 | 0 | 147456 | 294912 | 3.498749378 | 0 |
| 113 | 8305 | 1224622080 | 0 | 147456 | 294912 | 3.529387302 | 0 |
| 114 | 8306 | 1224769536 | 0 | 147456 | 294912 | 3.560028914 | 0 |
| 115 | 8307 | 1224916992 | 0 | 147456 | 294912 | 3.590674211 | 0 |
| 116 | 8308 | 1225064448 | 0 | 147456 | 294912 | 3.621323195 | 0 |
| 117 | 8309 | 1225211904 | 0 | 147456 | 294912 | 3.651975866 | 0 |
| 118 | 8310 | 1225359360 | 0 | 147456 | 294912 | 3.682632222 | 0 |
| 119 | 8311 | 1225506816 | 0 | 147456 | 294912 | 3.713292266 | 0 |
| 120 | 8312 | 1225654272 | 0 | 147456 | 294912 | 3.743955995 | 0 |
| 121 | 8313 | 1225801728 | 0 | 147456 | 294912 | 3.774623411 | 0 |
| 122 | 8314 | 1225949184 | 0 | 147456 | 294912 | 3.805294514 | 0 |
| 123 | 8315 | 1226096640 | 0 | 147456 | 294912 | 3.835969302 | 0 |
| 124 | 8316 | 1226244096 | 0 | 147456 | 294912 | 3.866647778 | 0 |
| 125 | 8317 | 1226391552 | 0 | 147456 | 294912 | 3.897329939 | 0 |
| 126 | 8318 | 1226539008 | 0 | 147456 | 294912 | 3.928015787 | 0 |
| 127 | 8319 | 1226686464 | 0 | 147456 | 294912 | 3.958705322 | 0 |

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
    "copies": 2,
    "placement": "remote_all",
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
    },
    {
      "replica": 1,
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
      "read_start_seconds_exact": "18877493/312500000",
      "read_finish_seconds_exact": "56632479/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8192,
          "bytes": 147456,
          "start_seconds_exact": "56632479/625000000",
          "commit_seconds_exact": "14159477/156250000"
        },
        {
          "replica": 1,
          "position": 8192,
          "bytes": 147456,
          "start_seconds_exact": "14159477/156250000",
          "commit_seconds_exact": "56643337/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "56643337/625000000",
      "remote_lengths_after": [
        8193,
        8193
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1208107008
    },
    {
      "step": 1,
      "required_remote_epoch": 8193,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1208107008,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4833017856,
      "read_start_seconds_exact": "56643337/625000000",
      "read_finish_seconds_exact": "37761567/312500000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8193,
          "bytes": 147456,
          "start_seconds_exact": "37761567/312500000",
          "commit_seconds_exact": "75528563/625000000"
        },
        {
          "replica": 1,
          "position": 8193,
          "bytes": 147456,
          "start_seconds_exact": "75528563/625000000",
          "commit_seconds_exact": "9441749/78125000"
        }
      ],
      "all_replica_commit_seconds_exact": "9441749/78125000",
      "remote_lengths_after": [
        8194,
        8194
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1208254464
    },
    {
      "step": 2,
      "required_remote_epoch": 8194,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1208254464,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4833607680,
      "read_start_seconds_exact": "9441749/78125000",
      "read_finish_seconds_exact": "94416093/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8194,
          "bytes": 147456,
          "start_seconds_exact": "94416093/625000000",
          "commit_seconds_exact": "47210761/312500000"
        },
        {
          "replica": 1,
          "position": 8194,
          "bytes": 147456,
          "start_seconds_exact": "47210761/312500000",
          "commit_seconds_exact": "94426951/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "94426951/625000000",
      "remote_lengths_after": [
        8195,
        8195
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1208401920
    },
    {
      "step": 3,
      "required_remote_epoch": 8195,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1208401920,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4834197504,
      "read_start_seconds_exact": "94426951/625000000",
      "read_finish_seconds_exact": "28327839/156250000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8195,
          "bytes": 147456,
          "start_seconds_exact": "28327839/156250000",
          "commit_seconds_exact": "22663357/125000000"
        },
        {
          "replica": 1,
          "position": 8195,
          "bytes": 147456,
          "start_seconds_exact": "22663357/125000000",
          "commit_seconds_exact": "56661107/312500000"
        }
      ],
      "all_replica_commit_seconds_exact": "56661107/312500000",
      "remote_lengths_after": [
        8196,
        8196
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1208549376
    },
    {
      "step": 4,
      "required_remote_epoch": 8196,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1208549376,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4834787328,
      "read_start_seconds_exact": "56661107/312500000",
      "read_finish_seconds_exact": "132208923/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8196,
          "bytes": 147456,
          "start_seconds_exact": "132208923/625000000",
          "commit_seconds_exact": "8263397/39062500"
        },
        {
          "replica": 1,
          "position": 8196,
          "bytes": 147456,
          "start_seconds_exact": "8263397/39062500",
          "commit_seconds_exact": "132219781/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "132219781/625000000",
      "remote_lengths_after": [
        8197,
        8197
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1208696832
    },
    {
      "step": 5,
      "required_remote_epoch": 8197,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1208696832,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4835377152,
      "read_start_seconds_exact": "132219781/625000000",
      "read_finish_seconds_exact": "75554397/312500000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8197,
          "bytes": 147456,
          "start_seconds_exact": "75554397/312500000",
          "commit_seconds_exact": "151114223/625000000"
        },
        {
          "replica": 1,
          "position": 8197,
          "bytes": 147456,
          "start_seconds_exact": "151114223/625000000",
          "commit_seconds_exact": "37779913/156250000"
        }
      ],
      "all_replica_commit_seconds_exact": "37779913/156250000",
      "remote_lengths_after": [
        8198,
        8198
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1208844288
    },
    {
      "step": 6,
      "required_remote_epoch": 8198,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1208844288,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4835966976,
      "read_start_seconds_exact": "37779913/156250000",
      "read_finish_seconds_exact": "170010969/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8198,
          "bytes": 147456,
          "start_seconds_exact": "170010969/625000000",
          "commit_seconds_exact": "85008199/312500000"
        },
        {
          "replica": 1,
          "position": 8198,
          "bytes": 147456,
          "start_seconds_exact": "85008199/312500000",
          "commit_seconds_exact": "170021827/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "170021827/625000000",
      "remote_lengths_after": [
        8199,
        8199
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1208991744
    },
    {
      "step": 7,
      "required_remote_epoch": 8199,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1208991744,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4836556800,
      "read_start_seconds_exact": "170021827/625000000",
      "read_finish_seconds_exact": "23614431/78125000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8199,
          "bytes": 147456,
          "start_seconds_exact": "23614431/78125000",
          "commit_seconds_exact": "188920877/625000000"
        },
        {
          "replica": 1,
          "position": 8199,
          "bytes": 147456,
          "start_seconds_exact": "188920877/625000000",
          "commit_seconds_exact": "94463153/312500000"
        }
      ],
      "all_replica_commit_seconds_exact": "94463153/312500000",
      "remote_lengths_after": [
        8200,
        8200
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1209139200
    },
    {
      "step": 8,
      "required_remote_epoch": 8200,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1209139200,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4837146624,
      "read_start_seconds_exact": "94463153/312500000",
      "read_finish_seconds_exact": "207822231/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8200,
          "bytes": 147456,
          "start_seconds_exact": "207822231/625000000",
          "commit_seconds_exact": "10391383/31250000"
        },
        {
          "replica": 1,
          "position": 8200,
          "bytes": 147456,
          "start_seconds_exact": "10391383/31250000",
          "commit_seconds_exact": "207833089/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "207833089/625000000",
      "remote_lengths_after": [
        8201,
        8201
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1209286656
    },
    {
      "step": 9,
      "required_remote_epoch": 8201,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1209286656,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4837736448,
      "read_start_seconds_exact": "207833089/625000000",
      "read_finish_seconds_exact": "113365659/312500000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8201,
          "bytes": 147456,
          "start_seconds_exact": "113365659/312500000",
          "commit_seconds_exact": "226736747/625000000"
        },
        {
          "replica": 1,
          "position": 8201,
          "bytes": 147456,
          "start_seconds_exact": "226736747/625000000",
          "commit_seconds_exact": "7085693/19531250"
        }
      ],
      "all_replica_commit_seconds_exact": "7085693/19531250",
      "remote_lengths_after": [
        8202,
        8202
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1209434112
    },
    {
      "step": 10,
      "required_remote_epoch": 8202,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1209434112,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4838326272,
      "read_start_seconds_exact": "7085693/19531250",
      "read_finish_seconds_exact": "245642709/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8202,
          "bytes": 147456,
          "start_seconds_exact": "245642709/625000000",
          "commit_seconds_exact": "122824069/312500000"
        },
        {
          "replica": 1,
          "position": 8202,
          "bytes": 147456,
          "start_seconds_exact": "122824069/312500000",
          "commit_seconds_exact": "245653567/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "245653567/625000000",
      "remote_lengths_after": [
        8203,
        8203
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1209581568
    },
    {
      "step": 11,
      "required_remote_epoch": 8203,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1209581568,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4838916096,
      "read_start_seconds_exact": "245653567/625000000",
      "read_finish_seconds_exact": "66139101/156250000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8203,
          "bytes": 147456,
          "start_seconds_exact": "66139101/156250000",
          "commit_seconds_exact": "264561833/625000000"
        },
        {
          "replica": 1,
          "position": 8203,
          "bytes": 147456,
          "start_seconds_exact": "264561833/625000000",
          "commit_seconds_exact": "132283631/312500000"
        }
      ],
      "all_replica_commit_seconds_exact": "132283631/312500000",
      "remote_lengths_after": [
        8204,
        8204
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1209729024
    },
    {
      "step": 12,
      "required_remote_epoch": 8204,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1209729024,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4839505920,
      "read_start_seconds_exact": "132283631/312500000",
      "read_finish_seconds_exact": "283472403/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8204,
          "bytes": 147456,
          "start_seconds_exact": "283472403/625000000",
          "commit_seconds_exact": "35434729/78125000"
        },
        {
          "replica": 1,
          "position": 8204,
          "bytes": 147456,
          "start_seconds_exact": "35434729/78125000",
          "commit_seconds_exact": "283483261/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "283483261/625000000",
      "remote_lengths_after": [
        8205,
        8205
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1209876480
    },
    {
      "step": 13,
      "required_remote_epoch": 8205,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1209876480,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4840095744,
      "read_start_seconds_exact": "283483261/625000000",
      "read_finish_seconds_exact": "151195353/312500000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8205,
          "bytes": 147456,
          "start_seconds_exact": "151195353/312500000",
          "commit_seconds_exact": "60479227/125000000"
        },
        {
          "replica": 1,
          "position": 8205,
          "bytes": 147456,
          "start_seconds_exact": "60479227/125000000",
          "commit_seconds_exact": "75600391/156250000"
        }
      ],
      "all_replica_commit_seconds_exact": "75600391/156250000",
      "remote_lengths_after": [
        8206,
        8206
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1210023936
    },
    {
      "step": 14,
      "required_remote_epoch": 8206,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1210023936,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4840685568,
      "read_start_seconds_exact": "75600391/156250000",
      "read_finish_seconds_exact": "321311313/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8206,
          "bytes": 147456,
          "start_seconds_exact": "321311313/625000000",
          "commit_seconds_exact": "160658371/312500000"
        },
        {
          "replica": 1,
          "position": 8206,
          "bytes": 147456,
          "start_seconds_exact": "160658371/312500000",
          "commit_seconds_exact": "321322171/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "321322171/625000000",
      "remote_lengths_after": [
        8207,
        8207
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1210171392
    },
    {
      "step": 15,
      "required_remote_epoch": 8207,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1210171392,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4841275392,
      "read_start_seconds_exact": "321322171/625000000",
      "read_finish_seconds_exact": "21264639/39062500",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8207,
          "bytes": 147456,
          "start_seconds_exact": "21264639/39062500",
          "commit_seconds_exact": "340239653/625000000"
        },
        {
          "replica": 1,
          "position": 8207,
          "bytes": 147456,
          "start_seconds_exact": "340239653/625000000",
          "commit_seconds_exact": "170122541/312500000"
        }
      ],
      "all_replica_commit_seconds_exact": "170122541/312500000",
      "remote_lengths_after": [
        8208,
        8208
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1210318848
    },
    {
      "step": 16,
      "required_remote_epoch": 8208,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1210318848,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4841865216,
      "read_start_seconds_exact": "170122541/312500000",
      "read_finish_seconds_exact": "359159439/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8208,
          "bytes": 147456,
          "start_seconds_exact": "359159439/625000000",
          "commit_seconds_exact": "89791217/156250000"
        },
        {
          "replica": 1,
          "position": 8208,
          "bytes": 147456,
          "start_seconds_exact": "89791217/156250000",
          "commit_seconds_exact": "359170297/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "359170297/625000000",
      "remote_lengths_after": [
        8209,
        8209
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1210466304
    },
    {
      "step": 17,
      "required_remote_epoch": 8209,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1210466304,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4842455040,
      "read_start_seconds_exact": "359170297/625000000",
      "read_finish_seconds_exact": "189043479/312500000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8209,
          "bytes": 147456,
          "start_seconds_exact": "189043479/312500000",
          "commit_seconds_exact": "378092387/625000000"
        },
        {
          "replica": 1,
          "position": 8209,
          "bytes": 147456,
          "start_seconds_exact": "378092387/625000000",
          "commit_seconds_exact": "47262227/78125000"
        }
      ],
      "all_replica_commit_seconds_exact": "47262227/78125000",
      "remote_lengths_after": [
        8210,
        8210
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1210613760
    },
    {
      "step": 18,
      "required_remote_epoch": 8210,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1210613760,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4843044864,
      "read_start_seconds_exact": "47262227/78125000",
      "read_finish_seconds_exact": "397016781/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8210,
          "bytes": 147456,
          "start_seconds_exact": "397016781/625000000",
          "commit_seconds_exact": "39702221/62500000"
        },
        {
          "replica": 1,
          "position": 8210,
          "bytes": 147456,
          "start_seconds_exact": "39702221/62500000",
          "commit_seconds_exact": "397027639/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "397027639/625000000",
      "remote_lengths_after": [
        8211,
        8211
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1210761216
    },
    {
      "step": 19,
      "required_remote_epoch": 8211,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1210761216,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4843634688,
      "read_start_seconds_exact": "397027639/625000000",
      "read_finish_seconds_exact": "103987227/156250000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8211,
          "bytes": 147456,
          "start_seconds_exact": "103987227/156250000",
          "commit_seconds_exact": "415954337/625000000"
        },
        {
          "replica": 1,
          "position": 8211,
          "bytes": 147456,
          "start_seconds_exact": "415954337/625000000",
          "commit_seconds_exact": "207979883/312500000"
        }
      ],
      "all_replica_commit_seconds_exact": "207979883/312500000",
      "remote_lengths_after": [
        8212,
        8212
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1210908672
    },
    {
      "step": 20,
      "required_remote_epoch": 8212,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1210908672,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4844224512,
      "read_start_seconds_exact": "207979883/312500000",
      "read_finish_seconds_exact": "434883339/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8212,
          "bytes": 147456,
          "start_seconds_exact": "434883339/625000000",
          "commit_seconds_exact": "6795137/9765625"
        },
        {
          "replica": 1,
          "position": 8212,
          "bytes": 147456,
          "start_seconds_exact": "6795137/9765625",
          "commit_seconds_exact": "434894197/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "434894197/625000000",
      "remote_lengths_after": [
        8213,
        8213
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1211056128
    },
    {
      "step": 21,
      "required_remote_epoch": 8213,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1211056128,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4844814336,
      "read_start_seconds_exact": "434894197/625000000",
      "read_finish_seconds_exact": "226910037/312500000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8213,
          "bytes": 147456,
          "start_seconds_exact": "226910037/312500000",
          "commit_seconds_exact": "453825503/625000000"
        },
        {
          "replica": 1,
          "position": 8213,
          "bytes": 147456,
          "start_seconds_exact": "453825503/625000000",
          "commit_seconds_exact": "113457733/156250000"
        }
      ],
      "all_replica_commit_seconds_exact": "113457733/156250000",
      "remote_lengths_after": [
        8214,
        8214
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1211203584
    },
    {
      "step": 22,
      "required_remote_epoch": 8214,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1211203584,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4845404160,
      "read_start_seconds_exact": "113457733/156250000",
      "read_finish_seconds_exact": "472759113/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8214,
          "bytes": 147456,
          "start_seconds_exact": "472759113/625000000",
          "commit_seconds_exact": "236382271/312500000"
        },
        {
          "replica": 1,
          "position": 8214,
          "bytes": 147456,
          "start_seconds_exact": "236382271/312500000",
          "commit_seconds_exact": "472769971/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "472769971/625000000",
      "remote_lengths_after": [
        8215,
        8215
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1211351040
    },
    {
      "step": 23,
      "required_remote_epoch": 8215,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1211351040,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4845993984,
      "read_start_seconds_exact": "472769971/625000000",
      "read_finish_seconds_exact": "61462557/78125000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8215,
          "bytes": 147456,
          "start_seconds_exact": "61462557/78125000",
          "commit_seconds_exact": "98341177/125000000"
        },
        {
          "replica": 1,
          "position": 8215,
          "bytes": 147456,
          "start_seconds_exact": "98341177/125000000",
          "commit_seconds_exact": "245855657/312500000"
        }
      ],
      "all_replica_commit_seconds_exact": "245855657/312500000",
      "remote_lengths_after": [
        8216,
        8216
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1211498496
    },
    {
      "step": 24,
      "required_remote_epoch": 8216,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1211498496,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4846583808,
      "read_start_seconds_exact": "245855657/312500000",
      "read_finish_seconds_exact": "510644103/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8216,
          "bytes": 147456,
          "start_seconds_exact": "510644103/625000000",
          "commit_seconds_exact": "127662383/156250000"
        },
        {
          "replica": 1,
          "position": 8216,
          "bytes": 147456,
          "start_seconds_exact": "127662383/156250000",
          "commit_seconds_exact": "510654961/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "510654961/625000000",
      "remote_lengths_after": [
        8217,
        8217
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1211645952
    },
    {
      "step": 25,
      "required_remote_epoch": 8217,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1211645952,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4847173632,
      "read_start_seconds_exact": "510654961/625000000",
      "read_finish_seconds_exact": "264795027/312500000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8217,
          "bytes": 147456,
          "start_seconds_exact": "264795027/312500000",
          "commit_seconds_exact": "529595483/625000000"
        },
        {
          "replica": 1,
          "position": 8217,
          "bytes": 147456,
          "start_seconds_exact": "529595483/625000000",
          "commit_seconds_exact": "33100057/39062500"
        }
      ],
      "all_replica_commit_seconds_exact": "33100057/39062500",
      "remote_lengths_after": [
        8218,
        8218
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1211793408
    },
    {
      "step": 26,
      "required_remote_epoch": 8218,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1211793408,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4847763456,
      "read_start_seconds_exact": "33100057/39062500",
      "read_finish_seconds_exact": "548538309/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8218,
          "bytes": 147456,
          "start_seconds_exact": "548538309/625000000",
          "commit_seconds_exact": "274271869/312500000"
        },
        {
          "replica": 1,
          "position": 8218,
          "bytes": 147456,
          "start_seconds_exact": "274271869/312500000",
          "commit_seconds_exact": "548549167/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "548549167/625000000",
      "remote_lengths_after": [
        8219,
        8219
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1211940864
    },
    {
      "step": 27,
      "required_remote_epoch": 8219,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1211940864,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4848353280,
      "read_start_seconds_exact": "548549167/625000000",
      "read_finish_seconds_exact": "141872217/156250000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8219,
          "bytes": 147456,
          "start_seconds_exact": "141872217/156250000",
          "commit_seconds_exact": "567494297/625000000"
        },
        {
          "replica": 1,
          "position": 8219,
          "bytes": 147456,
          "start_seconds_exact": "567494297/625000000",
          "commit_seconds_exact": "283749863/312500000"
        }
      ],
      "all_replica_commit_seconds_exact": "283749863/312500000",
      "remote_lengths_after": [
        8220,
        8220
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1212088320
    },
    {
      "step": 28,
      "required_remote_epoch": 8220,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1212088320,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4848943104,
      "read_start_seconds_exact": "283749863/312500000",
      "read_finish_seconds_exact": "586441731/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8220,
          "bytes": 147456,
          "start_seconds_exact": "586441731/625000000",
          "commit_seconds_exact": "14661179/15625000"
        },
        {
          "replica": 1,
          "position": 8220,
          "bytes": 147456,
          "start_seconds_exact": "14661179/15625000",
          "commit_seconds_exact": "586452589/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "586452589/625000000",
      "remote_lengths_after": [
        8221,
        8221
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1212235776
    },
    {
      "step": 29,
      "required_remote_epoch": 8221,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1212235776,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4849532928,
      "read_start_seconds_exact": "586452589/625000000",
      "read_finish_seconds_exact": "302698449/312500000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8221,
          "bytes": 147456,
          "start_seconds_exact": "302698449/312500000",
          "commit_seconds_exact": "605402327/625000000"
        },
        {
          "replica": 1,
          "position": 8221,
          "bytes": 147456,
          "start_seconds_exact": "605402327/625000000",
          "commit_seconds_exact": "151351939/156250000"
        }
      ],
      "all_replica_commit_seconds_exact": "151351939/156250000",
      "remote_lengths_after": [
        8222,
        8222
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1212383232
    },
    {
      "step": 30,
      "required_remote_epoch": 8222,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1212383232,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4850122752,
      "read_start_seconds_exact": "151351939/156250000",
      "read_finish_seconds_exact": "624354369/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8222,
          "bytes": 147456,
          "start_seconds_exact": "624354369/625000000",
          "commit_seconds_exact": "312179899/312500000"
        },
        {
          "replica": 1,
          "position": 8222,
          "bytes": 147456,
          "start_seconds_exact": "312179899/312500000",
          "commit_seconds_exact": "624365227/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "624365227/625000000",
      "remote_lengths_after": [
        8223,
        8223
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1212530688
    },
    {
      "step": 31,
      "required_remote_epoch": 8223,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1212530688,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4850712576,
      "read_start_seconds_exact": "624365227/625000000",
      "read_finish_seconds_exact": "20103567/19531250",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8223,
          "bytes": 147456,
          "start_seconds_exact": "20103567/19531250",
          "commit_seconds_exact": "643319573/625000000"
        },
        {
          "replica": 1,
          "position": 8223,
          "bytes": 147456,
          "start_seconds_exact": "643319573/625000000",
          "commit_seconds_exact": "321662501/312500000"
        }
      ],
      "all_replica_commit_seconds_exact": "321662501/312500000",
      "remote_lengths_after": [
        8224,
        8224
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1212678144
    },
    {
      "step": 32,
      "required_remote_epoch": 8224,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1212678144,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4851302400,
      "read_start_seconds_exact": "321662501/312500000",
      "read_finish_seconds_exact": "662276223/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8224,
          "bytes": 147456,
          "start_seconds_exact": "662276223/625000000",
          "commit_seconds_exact": "165570413/156250000"
        },
        {
          "replica": 1,
          "position": 8224,
          "bytes": 147456,
          "start_seconds_exact": "165570413/156250000",
          "commit_seconds_exact": "662287081/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "662287081/625000000",
      "remote_lengths_after": [
        8225,
        8225
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1212825600
    },
    {
      "step": 33,
      "required_remote_epoch": 8225,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1212825600,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4851892224,
      "read_start_seconds_exact": "662287081/625000000",
      "read_finish_seconds_exact": "340620303/312500000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8225,
          "bytes": 147456,
          "start_seconds_exact": "340620303/312500000",
          "commit_seconds_exact": "136249207/125000000"
        },
        {
          "replica": 1,
          "position": 8225,
          "bytes": 147456,
          "start_seconds_exact": "136249207/125000000",
          "commit_seconds_exact": "85156433/78125000"
        }
      ],
      "all_replica_commit_seconds_exact": "85156433/78125000",
      "remote_lengths_after": [
        8226,
        8226
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1212973056
    },
    {
      "step": 34,
      "required_remote_epoch": 8226,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1212973056,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4852482048,
      "read_start_seconds_exact": "85156433/78125000",
      "read_finish_seconds_exact": "700207293/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8226,
          "bytes": 147456,
          "start_seconds_exact": "700207293/625000000",
          "commit_seconds_exact": "350106361/312500000"
        },
        {
          "replica": 1,
          "position": 8226,
          "bytes": 147456,
          "start_seconds_exact": "350106361/312500000",
          "commit_seconds_exact": "700218151/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "700218151/625000000",
      "remote_lengths_after": [
        8227,
        8227
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1213120512
    },
    {
      "step": 35,
      "required_remote_epoch": 8227,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1213120512,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4853071872,
      "read_start_seconds_exact": "700218151/625000000",
      "read_finish_seconds_exact": "179794071/156250000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8227,
          "bytes": 147456,
          "start_seconds_exact": "179794071/156250000",
          "commit_seconds_exact": "719181713/625000000"
        },
        {
          "replica": 1,
          "position": 8227,
          "bytes": 147456,
          "start_seconds_exact": "719181713/625000000",
          "commit_seconds_exact": "359593571/312500000"
        }
      ],
      "all_replica_commit_seconds_exact": "359593571/312500000",
      "remote_lengths_after": [
        8228,
        8228
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1213267968
    },
    {
      "step": 36,
      "required_remote_epoch": 8228,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1213267968,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4853661696,
      "read_start_seconds_exact": "359593571/312500000",
      "read_finish_seconds_exact": "738147579/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8228,
          "bytes": 147456,
          "start_seconds_exact": "738147579/625000000",
          "commit_seconds_exact": "46134563/39062500"
        },
        {
          "replica": 1,
          "position": 8228,
          "bytes": 147456,
          "start_seconds_exact": "46134563/39062500",
          "commit_seconds_exact": "738158437/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "738158437/625000000",
      "remote_lengths_after": [
        8229,
        8229
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1213415424
    },
    {
      "step": 37,
      "required_remote_epoch": 8229,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1213415424,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4854251520,
      "read_start_seconds_exact": "738158437/625000000",
      "read_finish_seconds_exact": "378560589/312500000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8229,
          "bytes": 147456,
          "start_seconds_exact": "378560589/312500000",
          "commit_seconds_exact": "757126607/625000000"
        },
        {
          "replica": 1,
          "position": 8229,
          "bytes": 147456,
          "start_seconds_exact": "757126607/625000000",
          "commit_seconds_exact": "189283009/156250000"
        }
      ],
      "all_replica_commit_seconds_exact": "189283009/156250000",
      "remote_lengths_after": [
        8230,
        8230
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1213562880
    },
    {
      "step": 38,
      "required_remote_epoch": 8230,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1213562880,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4854841344,
      "read_start_seconds_exact": "189283009/156250000",
      "read_finish_seconds_exact": "776097081/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8230,
          "bytes": 147456,
          "start_seconds_exact": "776097081/625000000",
          "commit_seconds_exact": "77610251/62500000"
        },
        {
          "replica": 1,
          "position": 8230,
          "bytes": 147456,
          "start_seconds_exact": "77610251/62500000",
          "commit_seconds_exact": "776107939/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "776107939/625000000",
      "remote_lengths_after": [
        8231,
        8231
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1213710336
    },
    {
      "step": 39,
      "required_remote_epoch": 8231,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1213710336,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4855431168,
      "read_start_seconds_exact": "776107939/625000000",
      "read_finish_seconds_exact": "99384411/78125000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8231,
          "bytes": 147456,
          "start_seconds_exact": "99384411/78125000",
          "commit_seconds_exact": "795080717/625000000"
        },
        {
          "replica": 1,
          "position": 8231,
          "bytes": 147456,
          "start_seconds_exact": "795080717/625000000",
          "commit_seconds_exact": "397543073/312500000"
        }
      ],
      "all_replica_commit_seconds_exact": "397543073/312500000",
      "remote_lengths_after": [
        8232,
        8232
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1213857792
    },
    {
      "step": 40,
      "required_remote_epoch": 8232,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1213857792,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4856020992,
      "read_start_seconds_exact": "397543073/312500000",
      "read_finish_seconds_exact": "814055799/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8232,
          "bytes": 147456,
          "start_seconds_exact": "814055799/625000000",
          "commit_seconds_exact": "203515307/156250000"
        },
        {
          "replica": 1,
          "position": 8232,
          "bytes": 147456,
          "start_seconds_exact": "203515307/156250000",
          "commit_seconds_exact": "814066657/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "814066657/625000000",
      "remote_lengths_after": [
        8233,
        8233
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1214005248
    },
    {
      "step": 41,
      "required_remote_epoch": 8233,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1214005248,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4856610816,
      "read_start_seconds_exact": "814066657/625000000",
      "read_finish_seconds_exact": "416519307/312500000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8233,
          "bytes": 147456,
          "start_seconds_exact": "416519307/312500000",
          "commit_seconds_exact": "833044043/625000000"
        },
        {
          "replica": 1,
          "position": 8233,
          "bytes": 147456,
          "start_seconds_exact": "833044043/625000000",
          "commit_seconds_exact": "13016398/9765625"
        }
      ],
      "all_replica_commit_seconds_exact": "13016398/9765625",
      "remote_lengths_after": [
        8234,
        8234
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1214152704
    },
    {
      "step": 42,
      "required_remote_epoch": 8234,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1214152704,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4857200640,
      "read_start_seconds_exact": "13016398/9765625",
      "read_finish_seconds_exact": "852023733/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8234,
          "bytes": 147456,
          "start_seconds_exact": "852023733/625000000",
          "commit_seconds_exact": "426014581/312500000"
        },
        {
          "replica": 1,
          "position": 8234,
          "bytes": 147456,
          "start_seconds_exact": "426014581/312500000",
          "commit_seconds_exact": "852034591/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "852034591/625000000",
      "remote_lengths_after": [
        8235,
        8235
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1214300160
    },
    {
      "step": 43,
      "required_remote_epoch": 8235,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1214300160,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4857790464,
      "read_start_seconds_exact": "852034591/625000000",
      "read_finish_seconds_exact": "217752789/156250000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8235,
          "bytes": 147456,
          "start_seconds_exact": "217752789/156250000",
          "commit_seconds_exact": "174203317/125000000"
        },
        {
          "replica": 1,
          "position": 8235,
          "bytes": 147456,
          "start_seconds_exact": "174203317/125000000",
          "commit_seconds_exact": "435511007/312500000"
        }
      ],
      "all_replica_commit_seconds_exact": "435511007/312500000",
      "remote_lengths_after": [
        8236,
        8236
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1214447616
    },
    {
      "step": 44,
      "required_remote_epoch": 8236,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1214447616,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4858380288,
      "read_start_seconds_exact": "435511007/312500000",
      "read_finish_seconds_exact": "890000883/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8236,
          "bytes": 147456,
          "start_seconds_exact": "890000883/625000000",
          "commit_seconds_exact": "111250789/78125000"
        },
        {
          "replica": 1,
          "position": 8236,
          "bytes": 147456,
          "start_seconds_exact": "111250789/78125000",
          "commit_seconds_exact": "890011741/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "890011741/625000000",
      "remote_lengths_after": [
        8237,
        8237
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1214595072
    },
    {
      "step": 45,
      "required_remote_epoch": 8237,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1214595072,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4858970112,
      "read_start_seconds_exact": "890011741/625000000",
      "read_finish_seconds_exact": "454496457/312500000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8237,
          "bytes": 147456,
          "start_seconds_exact": "454496457/312500000",
          "commit_seconds_exact": "908998343/625000000"
        },
        {
          "replica": 1,
          "position": 8237,
          "bytes": 147456,
          "start_seconds_exact": "908998343/625000000",
          "commit_seconds_exact": "227250943/156250000"
        }
      ],
      "all_replica_commit_seconds_exact": "227250943/156250000",
      "remote_lengths_after": [
        8238,
        8238
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1214742528
    },
    {
      "step": 46,
      "required_remote_epoch": 8238,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1214742528,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4859559936,
      "read_start_seconds_exact": "227250943/156250000",
      "read_finish_seconds_exact": "927987249/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8238,
          "bytes": 147456,
          "start_seconds_exact": "927987249/625000000",
          "commit_seconds_exact": "463996339/312500000"
        },
        {
          "replica": 1,
          "position": 8238,
          "bytes": 147456,
          "start_seconds_exact": "463996339/312500000",
          "commit_seconds_exact": "927998107/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "927998107/625000000",
      "remote_lengths_after": [
        8239,
        8239
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1214889984
    },
    {
      "step": 47,
      "required_remote_epoch": 8239,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1214889984,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4860149760,
      "read_start_seconds_exact": "927998107/625000000",
      "read_finish_seconds_exact": "59186493/39062500",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8239,
          "bytes": 147456,
          "start_seconds_exact": "59186493/39062500",
          "commit_seconds_exact": "946989317/625000000"
        },
        {
          "replica": 1,
          "position": 8239,
          "bytes": 147456,
          "start_seconds_exact": "946989317/625000000",
          "commit_seconds_exact": "473497373/312500000"
        }
      ],
      "all_replica_commit_seconds_exact": "473497373/312500000",
      "remote_lengths_after": [
        8240,
        8240
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1215037440
    },
    {
      "step": 48,
      "required_remote_epoch": 8240,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1215037440,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4860739584,
      "read_start_seconds_exact": "473497373/312500000",
      "read_finish_seconds_exact": "965982831/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8240,
          "bytes": 147456,
          "start_seconds_exact": "965982831/625000000",
          "commit_seconds_exact": "48299413/31250000"
        },
        {
          "replica": 1,
          "position": 8240,
          "bytes": 147456,
          "start_seconds_exact": "48299413/31250000",
          "commit_seconds_exact": "965993689/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "965993689/625000000",
      "remote_lengths_after": [
        8241,
        8241
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1215184896
    },
    {
      "step": 49,
      "required_remote_epoch": 8241,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1215184896,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4861329408,
      "read_start_seconds_exact": "965993689/625000000",
      "read_finish_seconds_exact": "492492039/312500000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8241,
          "bytes": 147456,
          "start_seconds_exact": "492492039/312500000",
          "commit_seconds_exact": "984989507/625000000"
        },
        {
          "replica": 1,
          "position": 8241,
          "bytes": 147456,
          "start_seconds_exact": "984989507/625000000",
          "commit_seconds_exact": "123124367/78125000"
        }
      ],
      "all_replica_commit_seconds_exact": "123124367/78125000",
      "remote_lengths_after": [
        8242,
        8242
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1215332352
    },
    {
      "step": 50,
      "required_remote_epoch": 8242,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1215332352,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4861919232,
      "read_start_seconds_exact": "123124367/78125000",
      "read_finish_seconds_exact": "1003987629/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8242,
          "bytes": 147456,
          "start_seconds_exact": "1003987629/625000000",
          "commit_seconds_exact": "501996529/312500000"
        },
        {
          "replica": 1,
          "position": 8242,
          "bytes": 147456,
          "start_seconds_exact": "501996529/312500000",
          "commit_seconds_exact": "1003998487/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "1003998487/625000000",
      "remote_lengths_after": [
        8243,
        8243
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1215479808
    },
    {
      "step": 51,
      "required_remote_epoch": 8243,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1215479808,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4862509056,
      "read_start_seconds_exact": "1003998487/625000000",
      "read_finish_seconds_exact": "255748371/156250000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8243,
          "bytes": 147456,
          "start_seconds_exact": "255748371/156250000",
          "commit_seconds_exact": "1022998913/625000000"
        },
        {
          "replica": 1,
          "position": 8243,
          "bytes": 147456,
          "start_seconds_exact": "1022998913/625000000",
          "commit_seconds_exact": "511502171/312500000"
        }
      ],
      "all_replica_commit_seconds_exact": "511502171/312500000",
      "remote_lengths_after": [
        8244,
        8244
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1215627264
    },
    {
      "step": 52,
      "required_remote_epoch": 8244,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1215627264,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4863098880,
      "read_start_seconds_exact": "511502171/312500000",
      "read_finish_seconds_exact": "1042001643/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8244,
          "bytes": 147456,
          "start_seconds_exact": "1042001643/625000000",
          "commit_seconds_exact": "32562721/19531250"
        },
        {
          "replica": 1,
          "position": 8244,
          "bytes": 147456,
          "start_seconds_exact": "32562721/19531250",
          "commit_seconds_exact": "1042012501/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "1042012501/625000000",
      "remote_lengths_after": [
        8245,
        8245
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1215774720
    },
    {
      "step": 53,
      "required_remote_epoch": 8245,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1215774720,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4863688704,
      "read_start_seconds_exact": "1042012501/625000000",
      "read_finish_seconds_exact": "530506053/312500000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8245,
          "bytes": 147456,
          "start_seconds_exact": "530506053/312500000",
          "commit_seconds_exact": "212203507/125000000"
        },
        {
          "replica": 1,
          "position": 8245,
          "bytes": 147456,
          "start_seconds_exact": "212203507/125000000",
          "commit_seconds_exact": "265255741/156250000"
        }
      ],
      "all_replica_commit_seconds_exact": "265255741/156250000",
      "remote_lengths_after": [
        8246,
        8246
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1215922176
    },
    {
      "step": 54,
      "required_remote_epoch": 8246,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1215922176,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4864278528,
      "read_start_seconds_exact": "265255741/156250000",
      "read_finish_seconds_exact": "1080024873/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8246,
          "bytes": 147456,
          "start_seconds_exact": "1080024873/625000000",
          "commit_seconds_exact": "540015151/312500000"
        },
        {
          "replica": 1,
          "position": 8246,
          "bytes": 147456,
          "start_seconds_exact": "540015151/312500000",
          "commit_seconds_exact": "1080035731/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "1080035731/625000000",
      "remote_lengths_after": [
        8247,
        8247
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1216069632
    },
    {
      "step": 55,
      "required_remote_epoch": 8247,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1216069632,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4864868352,
      "read_start_seconds_exact": "1080035731/625000000",
      "read_finish_seconds_exact": "137379993/78125000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8247,
          "bytes": 147456,
          "start_seconds_exact": "137379993/78125000",
          "commit_seconds_exact": "1099045373/625000000"
        },
        {
          "replica": 1,
          "position": 8247,
          "bytes": 147456,
          "start_seconds_exact": "1099045373/625000000",
          "commit_seconds_exact": "549525401/312500000"
        }
      ],
      "all_replica_commit_seconds_exact": "549525401/312500000",
      "remote_lengths_after": [
        8248,
        8248
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1216217088
    },
    {
      "step": 56,
      "required_remote_epoch": 8248,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1216217088,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4865458176,
      "read_start_seconds_exact": "549525401/312500000",
      "read_finish_seconds_exact": "1118057319/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8248,
          "bytes": 147456,
          "start_seconds_exact": "1118057319/625000000",
          "commit_seconds_exact": "279515687/156250000"
        },
        {
          "replica": 1,
          "position": 8248,
          "bytes": 147456,
          "start_seconds_exact": "279515687/156250000",
          "commit_seconds_exact": "1118068177/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "1118068177/625000000",
      "remote_lengths_after": [
        8249,
        8249
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1216364544
    },
    {
      "step": 57,
      "required_remote_epoch": 8249,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1216364544,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4866048000,
      "read_start_seconds_exact": "1118068177/625000000",
      "read_finish_seconds_exact": "568538499/312500000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8249,
          "bytes": 147456,
          "start_seconds_exact": "568538499/312500000",
          "commit_seconds_exact": "1137082427/625000000"
        },
        {
          "replica": 1,
          "position": 8249,
          "bytes": 147456,
          "start_seconds_exact": "1137082427/625000000",
          "commit_seconds_exact": "71067991/39062500"
        }
      ],
      "all_replica_commit_seconds_exact": "71067991/39062500",
      "remote_lengths_after": [
        8250,
        8250
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1216512000
    },
    {
      "step": 58,
      "required_remote_epoch": 8250,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1216512000,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4866637824,
      "read_start_seconds_exact": "71067991/39062500",
      "read_finish_seconds_exact": "1156098981/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8250,
          "bytes": 147456,
          "start_seconds_exact": "1156098981/625000000",
          "commit_seconds_exact": "115610441/62500000"
        },
        {
          "replica": 1,
          "position": 8250,
          "bytes": 147456,
          "start_seconds_exact": "115610441/62500000",
          "commit_seconds_exact": "1156109839/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "1156109839/625000000",
      "remote_lengths_after": [
        8251,
        8251
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1216659456
    },
    {
      "step": 59,
      "required_remote_epoch": 8251,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1216659456,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4867227648,
      "read_start_seconds_exact": "1156109839/625000000",
      "read_finish_seconds_exact": "293780817/156250000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8251,
          "bytes": 147456,
          "start_seconds_exact": "293780817/156250000",
          "commit_seconds_exact": "1175128697/625000000"
        },
        {
          "replica": 1,
          "position": 8251,
          "bytes": 147456,
          "start_seconds_exact": "1175128697/625000000",
          "commit_seconds_exact": "587567063/312500000"
        }
      ],
      "all_replica_commit_seconds_exact": "587567063/312500000",
      "remote_lengths_after": [
        8252,
        8252
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1216806912
    },
    {
      "step": 60,
      "required_remote_epoch": 8252,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1216806912,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4867817472,
      "read_start_seconds_exact": "587567063/312500000",
      "read_finish_seconds_exact": "1194149859/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8252,
          "bytes": 147456,
          "start_seconds_exact": "1194149859/625000000",
          "commit_seconds_exact": "149269411/78125000"
        },
        {
          "replica": 1,
          "position": 8252,
          "bytes": 147456,
          "start_seconds_exact": "149269411/78125000",
          "commit_seconds_exact": "1194160717/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "1194160717/625000000",
      "remote_lengths_after": [
        8253,
        8253
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1216954368
    },
    {
      "step": 61,
      "required_remote_epoch": 8253,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1216954368,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4868407296,
      "read_start_seconds_exact": "1194160717/625000000",
      "read_finish_seconds_exact": "606589377/312500000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8253,
          "bytes": 147456,
          "start_seconds_exact": "606589377/312500000",
          "commit_seconds_exact": "1213184183/625000000"
        },
        {
          "replica": 1,
          "position": 8253,
          "bytes": 147456,
          "start_seconds_exact": "1213184183/625000000",
          "commit_seconds_exact": "303297403/156250000"
        }
      ],
      "all_replica_commit_seconds_exact": "303297403/156250000",
      "remote_lengths_after": [
        8254,
        8254
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1217101824
    },
    {
      "step": 62,
      "required_remote_epoch": 8254,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1217101824,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4868997120,
      "read_start_seconds_exact": "303297403/156250000",
      "read_finish_seconds_exact": "1232209953/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8254,
          "bytes": 147456,
          "start_seconds_exact": "1232209953/625000000",
          "commit_seconds_exact": "616107691/312500000"
        },
        {
          "replica": 1,
          "position": 8254,
          "bytes": 147456,
          "start_seconds_exact": "616107691/312500000",
          "commit_seconds_exact": "1232220811/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "1232220811/625000000",
      "remote_lengths_after": [
        8255,
        8255
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1217249280
    },
    {
      "step": 63,
      "required_remote_epoch": 8255,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1217249280,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4869586944,
      "read_start_seconds_exact": "1232220811/625000000",
      "read_finish_seconds_exact": "19550679/9765625",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8255,
          "bytes": 147456,
          "start_seconds_exact": "19550679/9765625",
          "commit_seconds_exact": "250249777/125000000"
        },
        {
          "replica": 1,
          "position": 8255,
          "bytes": 147456,
          "start_seconds_exact": "250249777/125000000",
          "commit_seconds_exact": "625627157/312500000"
        }
      ],
      "all_replica_commit_seconds_exact": "625627157/312500000",
      "remote_lengths_after": [
        8256,
        8256
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1217396736
    },
    {
      "step": 64,
      "required_remote_epoch": 8256,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1217396736,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4870176768,
      "read_start_seconds_exact": "625627157/312500000",
      "read_finish_seconds_exact": "1270279263/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8256,
          "bytes": 147456,
          "start_seconds_exact": "1270279263/625000000",
          "commit_seconds_exact": "317571173/156250000"
        },
        {
          "replica": 1,
          "position": 8256,
          "bytes": 147456,
          "start_seconds_exact": "317571173/156250000",
          "commit_seconds_exact": "1270290121/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "1270290121/625000000",
      "remote_lengths_after": [
        8257,
        8257
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1217544192
    },
    {
      "step": 65,
      "required_remote_epoch": 8257,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1217544192,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4870766592,
      "read_start_seconds_exact": "1270290121/625000000",
      "read_finish_seconds_exact": "644658687/312500000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8257,
          "bytes": 147456,
          "start_seconds_exact": "644658687/312500000",
          "commit_seconds_exact": "1289322803/625000000"
        },
        {
          "replica": 1,
          "position": 8257,
          "bytes": 147456,
          "start_seconds_exact": "1289322803/625000000",
          "commit_seconds_exact": "161166029/78125000"
        }
      ],
      "all_replica_commit_seconds_exact": "161166029/78125000",
      "remote_lengths_after": [
        8258,
        8258
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1217691648
    },
    {
      "step": 66,
      "required_remote_epoch": 8258,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1217691648,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4871356416,
      "read_start_seconds_exact": "161166029/78125000",
      "read_finish_seconds_exact": "1308357789/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8258,
          "bytes": 147456,
          "start_seconds_exact": "1308357789/625000000",
          "commit_seconds_exact": "654181609/312500000"
        },
        {
          "replica": 1,
          "position": 8258,
          "bytes": 147456,
          "start_seconds_exact": "654181609/312500000",
          "commit_seconds_exact": "1308368647/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "1308368647/625000000",
      "remote_lengths_after": [
        8259,
        8259
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1217839104
    },
    {
      "step": 67,
      "required_remote_epoch": 8259,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1217839104,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4871946240,
      "read_start_seconds_exact": "1308368647/625000000",
      "read_finish_seconds_exact": "331850127/156250000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8259,
          "bytes": 147456,
          "start_seconds_exact": "331850127/156250000",
          "commit_seconds_exact": "1327405937/625000000"
        },
        {
          "replica": 1,
          "position": 8259,
          "bytes": 147456,
          "start_seconds_exact": "1327405937/625000000",
          "commit_seconds_exact": "663705683/312500000"
        }
      ],
      "all_replica_commit_seconds_exact": "663705683/312500000",
      "remote_lengths_after": [
        8260,
        8260
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1217986560
    },
    {
      "step": 68,
      "required_remote_epoch": 8260,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1217986560,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4872536064,
      "read_start_seconds_exact": "663705683/312500000",
      "read_finish_seconds_exact": "1346445531/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8260,
          "bytes": 147456,
          "start_seconds_exact": "1346445531/625000000",
          "commit_seconds_exact": "16830637/7812500"
        },
        {
          "replica": 1,
          "position": 8260,
          "bytes": 147456,
          "start_seconds_exact": "16830637/7812500",
          "commit_seconds_exact": "1346456389/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "1346456389/625000000",
      "remote_lengths_after": [
        8261,
        8261
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1218134016
    },
    {
      "step": 69,
      "required_remote_epoch": 8261,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1218134016,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4873125888,
      "read_start_seconds_exact": "1346456389/625000000",
      "read_finish_seconds_exact": "682746429/312500000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8261,
          "bytes": 147456,
          "start_seconds_exact": "682746429/312500000",
          "commit_seconds_exact": "1365498287/625000000"
        },
        {
          "replica": 1,
          "position": 8261,
          "bytes": 147456,
          "start_seconds_exact": "1365498287/625000000",
          "commit_seconds_exact": "341375929/156250000"
        }
      ],
      "all_replica_commit_seconds_exact": "341375929/156250000",
      "remote_lengths_after": [
        8262,
        8262
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1218281472
    },
    {
      "step": 70,
      "required_remote_epoch": 8262,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1218281472,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4873715712,
      "read_start_seconds_exact": "341375929/156250000",
      "read_finish_seconds_exact": "1384542489/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8262,
          "bytes": 147456,
          "start_seconds_exact": "1384542489/625000000",
          "commit_seconds_exact": "692273959/312500000"
        },
        {
          "replica": 1,
          "position": 8262,
          "bytes": 147456,
          "start_seconds_exact": "692273959/312500000",
          "commit_seconds_exact": "1384553347/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "1384553347/625000000",
      "remote_lengths_after": [
        8263,
        8263
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1218428928
    },
    {
      "step": 71,
      "required_remote_epoch": 8263,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1218428928,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4874305536,
      "read_start_seconds_exact": "1384553347/625000000",
      "read_finish_seconds_exact": "175449303/78125000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8263,
          "bytes": 147456,
          "start_seconds_exact": "175449303/78125000",
          "commit_seconds_exact": "1403599853/625000000"
        },
        {
          "replica": 1,
          "position": 8263,
          "bytes": 147456,
          "start_seconds_exact": "1403599853/625000000",
          "commit_seconds_exact": "701802641/312500000"
        }
      ],
      "all_replica_commit_seconds_exact": "701802641/312500000",
      "remote_lengths_after": [
        8264,
        8264
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1218576384
    },
    {
      "step": 72,
      "required_remote_epoch": 8264,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1218576384,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4874895360,
      "read_start_seconds_exact": "701802641/312500000",
      "read_finish_seconds_exact": "1422648663/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8264,
          "bytes": 147456,
          "start_seconds_exact": "1422648663/625000000",
          "commit_seconds_exact": "355663523/156250000"
        },
        {
          "replica": 1,
          "position": 8264,
          "bytes": 147456,
          "start_seconds_exact": "355663523/156250000",
          "commit_seconds_exact": "1422659521/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "1422659521/625000000",
      "remote_lengths_after": [
        8265,
        8265
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1218723840
    },
    {
      "step": 73,
      "required_remote_epoch": 8265,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1218723840,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4875485184,
      "read_start_seconds_exact": "1422659521/625000000",
      "read_finish_seconds_exact": "720852603/312500000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8265,
          "bytes": 147456,
          "start_seconds_exact": "720852603/312500000",
          "commit_seconds_exact": "288342127/125000000"
        },
        {
          "replica": 1,
          "position": 8265,
          "bytes": 147456,
          "start_seconds_exact": "288342127/125000000",
          "commit_seconds_exact": "45053627/19531250"
        }
      ],
      "all_replica_commit_seconds_exact": "45053627/19531250",
      "remote_lengths_after": [
        8266,
        8266
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1218871296
    },
    {
      "step": 74,
      "required_remote_epoch": 8266,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1218871296,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4876075008,
      "read_start_seconds_exact": "45053627/19531250",
      "read_finish_seconds_exact": "1460764053/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8266,
          "bytes": 147456,
          "start_seconds_exact": "1460764053/625000000",
          "commit_seconds_exact": "730384741/312500000"
        },
        {
          "replica": 1,
          "position": 8266,
          "bytes": 147456,
          "start_seconds_exact": "730384741/312500000",
          "commit_seconds_exact": "1460774911/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "1460774911/625000000",
      "remote_lengths_after": [
        8267,
        8267
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1219018752
    },
    {
      "step": 75,
      "required_remote_epoch": 8267,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1219018752,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4876664832,
      "read_start_seconds_exact": "1460774911/625000000",
      "read_finish_seconds_exact": "369956301/156250000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8267,
          "bytes": 147456,
          "start_seconds_exact": "369956301/156250000",
          "commit_seconds_exact": "1479830633/625000000"
        },
        {
          "replica": 1,
          "position": 8267,
          "bytes": 147456,
          "start_seconds_exact": "1479830633/625000000",
          "commit_seconds_exact": "739918031/312500000"
        }
      ],
      "all_replica_commit_seconds_exact": "739918031/312500000",
      "remote_lengths_after": [
        8268,
        8268
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1219166208
    },
    {
      "step": 76,
      "required_remote_epoch": 8268,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1219166208,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4877254656,
      "read_start_seconds_exact": "739918031/312500000",
      "read_finish_seconds_exact": "1498888659/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8268,
          "bytes": 147456,
          "start_seconds_exact": "1498888659/625000000",
          "commit_seconds_exact": "187361761/78125000"
        },
        {
          "replica": 1,
          "position": 8268,
          "bytes": 147456,
          "start_seconds_exact": "187361761/78125000",
          "commit_seconds_exact": "1498899517/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "1498899517/625000000",
      "remote_lengths_after": [
        8269,
        8269
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1219313664
    },
    {
      "step": 77,
      "required_remote_epoch": 8269,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1219313664,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4877844480,
      "read_start_seconds_exact": "1498899517/625000000",
      "read_finish_seconds_exact": "758977209/312500000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8269,
          "bytes": 147456,
          "start_seconds_exact": "758977209/312500000",
          "commit_seconds_exact": "1517959847/625000000"
        },
        {
          "replica": 1,
          "position": 8269,
          "bytes": 147456,
          "start_seconds_exact": "1517959847/625000000",
          "commit_seconds_exact": "379491319/156250000"
        }
      ],
      "all_replica_commit_seconds_exact": "379491319/156250000",
      "remote_lengths_after": [
        8270,
        8270
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1219461120
    },
    {
      "step": 78,
      "required_remote_epoch": 8270,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1219461120,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4878434304,
      "read_start_seconds_exact": "379491319/156250000",
      "read_finish_seconds_exact": "1537022481/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8270,
          "bytes": 147456,
          "start_seconds_exact": "1537022481/625000000",
          "commit_seconds_exact": "153702791/62500000"
        },
        {
          "replica": 1,
          "position": 8270,
          "bytes": 147456,
          "start_seconds_exact": "153702791/62500000",
          "commit_seconds_exact": "1537033339/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "1537033339/625000000",
      "remote_lengths_after": [
        8271,
        8271
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1219608576
    },
    {
      "step": 79,
      "required_remote_epoch": 8271,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1219608576,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4879024128,
      "read_start_seconds_exact": "1537033339/625000000",
      "read_finish_seconds_exact": "97255803/39062500",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8271,
          "bytes": 147456,
          "start_seconds_exact": "97255803/39062500",
          "commit_seconds_exact": "1556098277/625000000"
        },
        {
          "replica": 1,
          "position": 8271,
          "bytes": 147456,
          "start_seconds_exact": "1556098277/625000000",
          "commit_seconds_exact": "778051853/312500000"
        }
      ],
      "all_replica_commit_seconds_exact": "778051853/312500000",
      "remote_lengths_after": [
        8272,
        8272
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1219756032
    },
    {
      "step": 80,
      "required_remote_epoch": 8272,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1219756032,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4879613952,
      "read_start_seconds_exact": "778051853/312500000",
      "read_finish_seconds_exact": "1575165519/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8272,
          "bytes": 147456,
          "start_seconds_exact": "1575165519/625000000",
          "commit_seconds_exact": "393792737/156250000"
        },
        {
          "replica": 1,
          "position": 8272,
          "bytes": 147456,
          "start_seconds_exact": "393792737/156250000",
          "commit_seconds_exact": "1575176377/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "1575176377/625000000",
      "remote_lengths_after": [
        8273,
        8273
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1219903488
    },
    {
      "step": 81,
      "required_remote_epoch": 8273,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1219903488,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4880203776,
      "read_start_seconds_exact": "1575176377/625000000",
      "read_finish_seconds_exact": "797120247/312500000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8273,
          "bytes": 147456,
          "start_seconds_exact": "797120247/312500000",
          "commit_seconds_exact": "1594245923/625000000"
        },
        {
          "replica": 1,
          "position": 8273,
          "bytes": 147456,
          "start_seconds_exact": "1594245923/625000000",
          "commit_seconds_exact": "199281419/78125000"
        }
      ],
      "all_replica_commit_seconds_exact": "199281419/78125000",
      "remote_lengths_after": [
        8274,
        8274
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1220050944
    },
    {
      "step": 82,
      "required_remote_epoch": 8274,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1220050944,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4880793600,
      "read_start_seconds_exact": "199281419/78125000",
      "read_finish_seconds_exact": "1613317773/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8274,
          "bytes": 147456,
          "start_seconds_exact": "1613317773/625000000",
          "commit_seconds_exact": "806661601/312500000"
        },
        {
          "replica": 1,
          "position": 8274,
          "bytes": 147456,
          "start_seconds_exact": "806661601/312500000",
          "commit_seconds_exact": "1613328631/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "1613328631/625000000",
      "remote_lengths_after": [
        8275,
        8275
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1220198400
    },
    {
      "step": 83,
      "required_remote_epoch": 8275,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1220198400,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4881383424,
      "read_start_seconds_exact": "1613328631/625000000",
      "read_finish_seconds_exact": "408099339/156250000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8275,
          "bytes": 147456,
          "start_seconds_exact": "408099339/156250000",
          "commit_seconds_exact": "326480557/125000000"
        },
        {
          "replica": 1,
          "position": 8275,
          "bytes": 147456,
          "start_seconds_exact": "326480557/125000000",
          "commit_seconds_exact": "816204107/312500000"
        }
      ],
      "all_replica_commit_seconds_exact": "816204107/312500000",
      "remote_lengths_after": [
        8276,
        8276
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1220345856
    },
    {
      "step": 84,
      "required_remote_epoch": 8276,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1220345856,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4881973248,
      "read_start_seconds_exact": "816204107/312500000",
      "read_finish_seconds_exact": "1651479243/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8276,
          "bytes": 147456,
          "start_seconds_exact": "1651479243/625000000",
          "commit_seconds_exact": "25804448/9765625"
        },
        {
          "replica": 1,
          "position": 8276,
          "bytes": 147456,
          "start_seconds_exact": "25804448/9765625",
          "commit_seconds_exact": "1651490101/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "1651490101/625000000",
      "remote_lengths_after": [
        8277,
        8277
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1220493312
    },
    {
      "step": 85,
      "required_remote_epoch": 8277,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1220493312,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4882563072,
      "read_start_seconds_exact": "1651490101/625000000",
      "read_finish_seconds_exact": "835281717/312500000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8277,
          "bytes": 147456,
          "start_seconds_exact": "835281717/312500000",
          "commit_seconds_exact": "1670568863/625000000"
        },
        {
          "replica": 1,
          "position": 8277,
          "bytes": 147456,
          "start_seconds_exact": "1670568863/625000000",
          "commit_seconds_exact": "417643573/156250000"
        }
      ],
      "all_replica_commit_seconds_exact": "417643573/156250000",
      "remote_lengths_after": [
        8278,
        8278
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1220640768
    },
    {
      "step": 86,
      "required_remote_epoch": 8278,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1220640768,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4883152896,
      "read_start_seconds_exact": "417643573/156250000",
      "read_finish_seconds_exact": "1689649929/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8278,
          "bytes": 147456,
          "start_seconds_exact": "1689649929/625000000",
          "commit_seconds_exact": "844827679/312500000"
        },
        {
          "replica": 1,
          "position": 8278,
          "bytes": 147456,
          "start_seconds_exact": "844827679/312500000",
          "commit_seconds_exact": "1689660787/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "1689660787/625000000",
      "remote_lengths_after": [
        8279,
        8279
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1220788224
    },
    {
      "step": 87,
      "required_remote_epoch": 8279,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1220788224,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4883742720,
      "read_start_seconds_exact": "1689660787/625000000",
      "read_finish_seconds_exact": "213592341/78125000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8279,
          "bytes": 147456,
          "start_seconds_exact": "213592341/78125000",
          "commit_seconds_exact": "1708744157/625000000"
        },
        {
          "replica": 1,
          "position": 8279,
          "bytes": 147456,
          "start_seconds_exact": "1708744157/625000000",
          "commit_seconds_exact": "854374793/312500000"
        }
      ],
      "all_replica_commit_seconds_exact": "854374793/312500000",
      "remote_lengths_after": [
        8280,
        8280
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1220935680
    },
    {
      "step": 88,
      "required_remote_epoch": 8280,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1220935680,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4884332544,
      "read_start_seconds_exact": "854374793/312500000",
      "read_finish_seconds_exact": "1727829831/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8280,
          "bytes": 147456,
          "start_seconds_exact": "1727829831/625000000",
          "commit_seconds_exact": "86391763/31250000"
        },
        {
          "replica": 1,
          "position": 8280,
          "bytes": 147456,
          "start_seconds_exact": "86391763/31250000",
          "commit_seconds_exact": "1727840689/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "1727840689/625000000",
      "remote_lengths_after": [
        8281,
        8281
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1221083136
    },
    {
      "step": 89,
      "required_remote_epoch": 8281,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1221083136,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4884922368,
      "read_start_seconds_exact": "1727840689/625000000",
      "read_finish_seconds_exact": "873461619/312500000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8281,
          "bytes": 147456,
          "start_seconds_exact": "873461619/312500000",
          "commit_seconds_exact": "1746928667/625000000"
        },
        {
          "replica": 1,
          "position": 8281,
          "bytes": 147456,
          "start_seconds_exact": "1746928667/625000000",
          "commit_seconds_exact": "109183381/39062500"
        }
      ],
      "all_replica_commit_seconds_exact": "109183381/39062500",
      "remote_lengths_after": [
        8282,
        8282
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1221230592
    },
    {
      "step": 90,
      "required_remote_epoch": 8282,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1221230592,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4885512192,
      "read_start_seconds_exact": "109183381/39062500",
      "read_finish_seconds_exact": "1766018949/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8282,
          "bytes": 147456,
          "start_seconds_exact": "1766018949/625000000",
          "commit_seconds_exact": "883012189/312500000"
        },
        {
          "replica": 1,
          "position": 8282,
          "bytes": 147456,
          "start_seconds_exact": "883012189/312500000",
          "commit_seconds_exact": "1766029807/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "1766029807/625000000",
      "remote_lengths_after": [
        8283,
        8283
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1221378048
    },
    {
      "step": 91,
      "required_remote_epoch": 8283,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1221378048,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4886102016,
      "read_start_seconds_exact": "1766029807/625000000",
      "read_finish_seconds_exact": "446279241/156250000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8283,
          "bytes": 147456,
          "start_seconds_exact": "446279241/156250000",
          "commit_seconds_exact": "1785122393/625000000"
        },
        {
          "replica": 1,
          "position": 8283,
          "bytes": 147456,
          "start_seconds_exact": "1785122393/625000000",
          "commit_seconds_exact": "892563911/312500000"
        }
      ],
      "all_replica_commit_seconds_exact": "892563911/312500000",
      "remote_lengths_after": [
        8284,
        8284
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1221525504
    },
    {
      "step": 92,
      "required_remote_epoch": 8284,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1221525504,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4886691840,
      "read_start_seconds_exact": "892563911/312500000",
      "read_finish_seconds_exact": "1804217283/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8284,
          "bytes": 147456,
          "start_seconds_exact": "1804217283/625000000",
          "commit_seconds_exact": "225527839/78125000"
        },
        {
          "replica": 1,
          "position": 8284,
          "bytes": 147456,
          "start_seconds_exact": "225527839/78125000",
          "commit_seconds_exact": "1804228141/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "1804228141/625000000",
      "remote_lengths_after": [
        8285,
        8285
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1221672960
    },
    {
      "step": 93,
      "required_remote_epoch": 8285,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1221672960,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4887281664,
      "read_start_seconds_exact": "1804228141/625000000",
      "read_finish_seconds_exact": "911659953/312500000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8285,
          "bytes": 147456,
          "start_seconds_exact": "911659953/312500000",
          "commit_seconds_exact": "364665067/125000000"
        },
        {
          "replica": 1,
          "position": 8285,
          "bytes": 147456,
          "start_seconds_exact": "364665067/125000000",
          "commit_seconds_exact": "455832691/156250000"
        }
      ],
      "all_replica_commit_seconds_exact": "455832691/156250000",
      "remote_lengths_after": [
        8286,
        8286
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1221820416
    },
    {
      "step": 94,
      "required_remote_epoch": 8286,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1221820416,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4887871488,
      "read_start_seconds_exact": "455832691/156250000",
      "read_finish_seconds_exact": "1842424833/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8286,
          "bytes": 147456,
          "start_seconds_exact": "1842424833/625000000",
          "commit_seconds_exact": "921215131/312500000"
        },
        {
          "replica": 1,
          "position": 8286,
          "bytes": 147456,
          "start_seconds_exact": "921215131/312500000",
          "commit_seconds_exact": "1842435691/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "1842435691/625000000",
      "remote_lengths_after": [
        8287,
        8287
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1221967872
    },
    {
      "step": 95,
      "required_remote_epoch": 8287,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1221967872,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4888461312,
      "read_start_seconds_exact": "1842435691/625000000",
      "read_finish_seconds_exact": "58172877/19531250",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8287,
          "bytes": 147456,
          "start_seconds_exact": "58172877/19531250",
          "commit_seconds_exact": "1861537493/625000000"
        },
        {
          "replica": 1,
          "position": 8287,
          "bytes": 147456,
          "start_seconds_exact": "1861537493/625000000",
          "commit_seconds_exact": "930771461/312500000"
        }
      ],
      "all_replica_commit_seconds_exact": "930771461/312500000",
      "remote_lengths_after": [
        8288,
        8288
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1222115328
    },
    {
      "step": 96,
      "required_remote_epoch": 8288,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1222115328,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4889051136,
      "read_start_seconds_exact": "930771461/312500000",
      "read_finish_seconds_exact": "1880641599/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8288,
          "bytes": 147456,
          "start_seconds_exact": "1880641599/625000000",
          "commit_seconds_exact": "470161757/156250000"
        },
        {
          "replica": 1,
          "position": 8288,
          "bytes": 147456,
          "start_seconds_exact": "470161757/156250000",
          "commit_seconds_exact": "1880652457/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "1880652457/625000000",
      "remote_lengths_after": [
        8289,
        8289
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1222262784
    },
    {
      "step": 97,
      "required_remote_epoch": 8289,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1222262784,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4889640960,
      "read_start_seconds_exact": "1880652457/625000000",
      "read_finish_seconds_exact": "949876719/312500000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8289,
          "bytes": 147456,
          "start_seconds_exact": "949876719/312500000",
          "commit_seconds_exact": "1899758867/625000000"
        },
        {
          "replica": 1,
          "position": 8289,
          "bytes": 147456,
          "start_seconds_exact": "1899758867/625000000",
          "commit_seconds_exact": "237470537/78125000"
        }
      ],
      "all_replica_commit_seconds_exact": "237470537/78125000",
      "remote_lengths_after": [
        8290,
        8290
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1222410240
    },
    {
      "step": 98,
      "required_remote_epoch": 8290,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1222410240,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4890230784,
      "read_start_seconds_exact": "237470537/78125000",
      "read_finish_seconds_exact": "1918867581/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8290,
          "bytes": 147456,
          "start_seconds_exact": "1918867581/625000000",
          "commit_seconds_exact": "191887301/62500000"
        },
        {
          "replica": 1,
          "position": 8290,
          "bytes": 147456,
          "start_seconds_exact": "191887301/62500000",
          "commit_seconds_exact": "1918878439/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "1918878439/625000000",
      "remote_lengths_after": [
        8291,
        8291
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1222557696
    },
    {
      "step": 99,
      "required_remote_epoch": 8291,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1222557696,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4890820608,
      "read_start_seconds_exact": "1918878439/625000000",
      "read_finish_seconds_exact": "484496007/156250000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8291,
          "bytes": 147456,
          "start_seconds_exact": "484496007/156250000",
          "commit_seconds_exact": "1937989457/625000000"
        },
        {
          "replica": 1,
          "position": 8291,
          "bytes": 147456,
          "start_seconds_exact": "1937989457/625000000",
          "commit_seconds_exact": "968997443/312500000"
        }
      ],
      "all_replica_commit_seconds_exact": "968997443/312500000",
      "remote_lengths_after": [
        8292,
        8292
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1222705152
    },
    {
      "step": 100,
      "required_remote_epoch": 8292,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1222705152,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4891410432,
      "read_start_seconds_exact": "968997443/312500000",
      "read_finish_seconds_exact": "1957102779/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8292,
          "bytes": 147456,
          "start_seconds_exact": "1957102779/625000000",
          "commit_seconds_exact": "122319263/39062500"
        },
        {
          "replica": 1,
          "position": 8292,
          "bytes": 147456,
          "start_seconds_exact": "122319263/39062500",
          "commit_seconds_exact": "1957113637/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "1957113637/625000000",
      "remote_lengths_after": [
        8293,
        8293
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1222852608
    },
    {
      "step": 101,
      "required_remote_epoch": 8293,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1222852608,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4892000256,
      "read_start_seconds_exact": "1957113637/625000000",
      "read_finish_seconds_exact": "988111917/312500000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8293,
          "bytes": 147456,
          "start_seconds_exact": "988111917/312500000",
          "commit_seconds_exact": "1976229263/625000000"
        },
        {
          "replica": 1,
          "position": 8293,
          "bytes": 147456,
          "start_seconds_exact": "1976229263/625000000",
          "commit_seconds_exact": "494058673/156250000"
        }
      ],
      "all_replica_commit_seconds_exact": "494058673/156250000",
      "remote_lengths_after": [
        8294,
        8294
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1223000064
    },
    {
      "step": 102,
      "required_remote_epoch": 8294,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1223000064,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4892590080,
      "read_start_seconds_exact": "494058673/156250000",
      "read_finish_seconds_exact": "1995347193/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8294,
          "bytes": 147456,
          "start_seconds_exact": "1995347193/625000000",
          "commit_seconds_exact": "997676311/312500000"
        },
        {
          "replica": 1,
          "position": 8294,
          "bytes": 147456,
          "start_seconds_exact": "997676311/312500000",
          "commit_seconds_exact": "1995358051/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "1995358051/625000000",
      "remote_lengths_after": [
        8295,
        8295
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1223147520
    },
    {
      "step": 103,
      "required_remote_epoch": 8295,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1223147520,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4893179904,
      "read_start_seconds_exact": "1995358051/625000000",
      "read_finish_seconds_exact": "251809107/78125000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8295,
          "bytes": 147456,
          "start_seconds_exact": "251809107/78125000",
          "commit_seconds_exact": "402895657/125000000"
        },
        {
          "replica": 1,
          "position": 8295,
          "bytes": 147456,
          "start_seconds_exact": "402895657/125000000",
          "commit_seconds_exact": "1007241857/312500000"
        }
      ],
      "all_replica_commit_seconds_exact": "1007241857/312500000",
      "remote_lengths_after": [
        8296,
        8296
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1223294976
    },
    {
      "step": 104,
      "required_remote_epoch": 8296,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1223294976,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4893769728,
      "read_start_seconds_exact": "1007241857/312500000",
      "read_finish_seconds_exact": "2033600823/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8296,
          "bytes": 147456,
          "start_seconds_exact": "2033600823/625000000",
          "commit_seconds_exact": "508401563/156250000"
        },
        {
          "replica": 1,
          "position": 8296,
          "bytes": 147456,
          "start_seconds_exact": "508401563/156250000",
          "commit_seconds_exact": "2033611681/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "2033611681/625000000",
      "remote_lengths_after": [
        8297,
        8297
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1223442432
    },
    {
      "step": 105,
      "required_remote_epoch": 8297,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1223442432,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4894359552,
      "read_start_seconds_exact": "2033611681/625000000",
      "read_finish_seconds_exact": "1026365547/312500000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8297,
          "bytes": 147456,
          "start_seconds_exact": "1026365547/312500000",
          "commit_seconds_exact": "2052736523/625000000"
        },
        {
          "replica": 1,
          "position": 8297,
          "bytes": 147456,
          "start_seconds_exact": "2052736523/625000000",
          "commit_seconds_exact": "32074093/9765625"
        }
      ],
      "all_replica_commit_seconds_exact": "32074093/9765625",
      "remote_lengths_after": [
        8298,
        8298
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1223589888
    },
    {
      "step": 106,
      "required_remote_epoch": 8298,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1223589888,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4894949376,
      "read_start_seconds_exact": "32074093/9765625",
      "read_finish_seconds_exact": "2071863669/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8298,
          "bytes": 147456,
          "start_seconds_exact": "2071863669/625000000",
          "commit_seconds_exact": "1035934549/312500000"
        },
        {
          "replica": 1,
          "position": 8298,
          "bytes": 147456,
          "start_seconds_exact": "1035934549/312500000",
          "commit_seconds_exact": "2071874527/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "2071874527/625000000",
      "remote_lengths_after": [
        8299,
        8299
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1223737344
    },
    {
      "step": 107,
      "required_remote_epoch": 8299,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1223737344,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4895539200,
      "read_start_seconds_exact": "2071874527/625000000",
      "read_finish_seconds_exact": "522749637/156250000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8299,
          "bytes": 147456,
          "start_seconds_exact": "522749637/156250000",
          "commit_seconds_exact": "2091003977/625000000"
        },
        {
          "replica": 1,
          "position": 8299,
          "bytes": 147456,
          "start_seconds_exact": "2091003977/625000000",
          "commit_seconds_exact": "1045504703/312500000"
        }
      ],
      "all_replica_commit_seconds_exact": "1045504703/312500000",
      "remote_lengths_after": [
        8300,
        8300
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1223884800
    },
    {
      "step": 108,
      "required_remote_epoch": 8300,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1223884800,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4896129024,
      "read_start_seconds_exact": "1045504703/312500000",
      "read_finish_seconds_exact": "2110135731/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8300,
          "bytes": 147456,
          "start_seconds_exact": "2110135731/625000000",
          "commit_seconds_exact": "52753529/15625000"
        },
        {
          "replica": 1,
          "position": 8300,
          "bytes": 147456,
          "start_seconds_exact": "52753529/15625000",
          "commit_seconds_exact": "2110146589/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "2110146589/625000000",
      "remote_lengths_after": [
        8301,
        8301
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1224032256
    },
    {
      "step": 109,
      "required_remote_epoch": 8301,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1224032256,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4896718848,
      "read_start_seconds_exact": "2110146589/625000000",
      "read_finish_seconds_exact": "1064637609/312500000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8301,
          "bytes": 147456,
          "start_seconds_exact": "1064637609/312500000",
          "commit_seconds_exact": "2129280647/625000000"
        },
        {
          "replica": 1,
          "position": 8301,
          "bytes": 147456,
          "start_seconds_exact": "2129280647/625000000",
          "commit_seconds_exact": "532321519/156250000"
        }
      ],
      "all_replica_commit_seconds_exact": "532321519/156250000",
      "remote_lengths_after": [
        8302,
        8302
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1224179712
    },
    {
      "step": 110,
      "required_remote_epoch": 8302,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1224179712,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4897308672,
      "read_start_seconds_exact": "532321519/156250000",
      "read_finish_seconds_exact": "2148417009/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8302,
          "bytes": 147456,
          "start_seconds_exact": "2148417009/625000000",
          "commit_seconds_exact": "1074211219/312500000"
        },
        {
          "replica": 1,
          "position": 8302,
          "bytes": 147456,
          "start_seconds_exact": "1074211219/312500000",
          "commit_seconds_exact": "2148427867/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "2148427867/625000000",
      "remote_lengths_after": [
        8303,
        8303
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1224327168
    },
    {
      "step": 111,
      "required_remote_epoch": 8303,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1224327168,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4897898496,
      "read_start_seconds_exact": "2148427867/625000000",
      "read_finish_seconds_exact": "135472569/39062500",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8303,
          "bytes": 147456,
          "start_seconds_exact": "135472569/39062500",
          "commit_seconds_exact": "2167566533/625000000"
        },
        {
          "replica": 1,
          "position": 8303,
          "bytes": 147456,
          "start_seconds_exact": "2167566533/625000000",
          "commit_seconds_exact": "1083785981/312500000"
        }
      ],
      "all_replica_commit_seconds_exact": "1083785981/312500000",
      "remote_lengths_after": [
        8304,
        8304
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1224474624
    },
    {
      "step": 112,
      "required_remote_epoch": 8304,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1224474624,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4898488320,
      "read_start_seconds_exact": "1083785981/312500000",
      "read_finish_seconds_exact": "2186707503/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8304,
          "bytes": 147456,
          "start_seconds_exact": "2186707503/625000000",
          "commit_seconds_exact": "546678233/156250000"
        },
        {
          "replica": 1,
          "position": 8304,
          "bytes": 147456,
          "start_seconds_exact": "546678233/156250000",
          "commit_seconds_exact": "2186718361/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "2186718361/625000000",
      "remote_lengths_after": [
        8305,
        8305
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1224622080
    },
    {
      "step": 113,
      "required_remote_epoch": 8305,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1224622080,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4899078144,
      "read_start_seconds_exact": "2186718361/625000000",
      "read_finish_seconds_exact": "1102928103/312500000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8305,
          "bytes": 147456,
          "start_seconds_exact": "1102928103/312500000",
          "commit_seconds_exact": "441172327/125000000"
        },
        {
          "replica": 1,
          "position": 8305,
          "bytes": 147456,
          "start_seconds_exact": "441172327/125000000",
          "commit_seconds_exact": "275733383/78125000"
        }
      ],
      "all_replica_commit_seconds_exact": "275733383/78125000",
      "remote_lengths_after": [
        8306,
        8306
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1224769536
    },
    {
      "step": 114,
      "required_remote_epoch": 8306,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1224769536,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4899667968,
      "read_start_seconds_exact": "275733383/78125000",
      "read_finish_seconds_exact": "2225007213/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8306,
          "bytes": 147456,
          "start_seconds_exact": "2225007213/625000000",
          "commit_seconds_exact": "1112506321/312500000"
        },
        {
          "replica": 1,
          "position": 8306,
          "bytes": 147456,
          "start_seconds_exact": "1112506321/312500000",
          "commit_seconds_exact": "2225018071/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "2225018071/625000000",
      "remote_lengths_after": [
        8307,
        8307
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1224916992
    },
    {
      "step": 115,
      "required_remote_epoch": 8307,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1224916992,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4900257792,
      "read_start_seconds_exact": "2225018071/625000000",
      "read_finish_seconds_exact": "561040131/156250000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8307,
          "bytes": 147456,
          "start_seconds_exact": "561040131/156250000",
          "commit_seconds_exact": "2244165953/625000000"
        },
        {
          "replica": 1,
          "position": 8307,
          "bytes": 147456,
          "start_seconds_exact": "2244165953/625000000",
          "commit_seconds_exact": "1122085691/312500000"
        }
      ],
      "all_replica_commit_seconds_exact": "1122085691/312500000",
      "remote_lengths_after": [
        8308,
        8308
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1225064448
    },
    {
      "step": 116,
      "required_remote_epoch": 8308,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1225064448,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4900847616,
      "read_start_seconds_exact": "1122085691/312500000",
      "read_finish_seconds_exact": "2263316139/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8308,
          "bytes": 147456,
          "start_seconds_exact": "2263316139/625000000",
          "commit_seconds_exact": "70728799/19531250"
        },
        {
          "replica": 1,
          "position": 8308,
          "bytes": 147456,
          "start_seconds_exact": "70728799/19531250",
          "commit_seconds_exact": "2263326997/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "2263326997/625000000",
      "remote_lengths_after": [
        8309,
        8309
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1225211904
    },
    {
      "step": 117,
      "required_remote_epoch": 8309,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1225211904,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4901437440,
      "read_start_seconds_exact": "2263326997/625000000",
      "read_finish_seconds_exact": "1141237029/312500000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8309,
          "bytes": 147456,
          "start_seconds_exact": "1141237029/312500000",
          "commit_seconds_exact": "2282479487/625000000"
        },
        {
          "replica": 1,
          "position": 8309,
          "bytes": 147456,
          "start_seconds_exact": "2282479487/625000000",
          "commit_seconds_exact": "570621229/156250000"
        }
      ],
      "all_replica_commit_seconds_exact": "570621229/156250000",
      "remote_lengths_after": [
        8310,
        8310
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1225359360
    },
    {
      "step": 118,
      "required_remote_epoch": 8310,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1225359360,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4902027264,
      "read_start_seconds_exact": "570621229/156250000",
      "read_finish_seconds_exact": "2301634281/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8310,
          "bytes": 147456,
          "start_seconds_exact": "2301634281/625000000",
          "commit_seconds_exact": "230163971/62500000"
        },
        {
          "replica": 1,
          "position": 8310,
          "bytes": 147456,
          "start_seconds_exact": "230163971/62500000",
          "commit_seconds_exact": "2301645139/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "2301645139/625000000",
      "remote_lengths_after": [
        8311,
        8311
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1225506816
    },
    {
      "step": 119,
      "required_remote_epoch": 8311,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1225506816,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4902617088,
      "read_start_seconds_exact": "2301645139/625000000",
      "read_finish_seconds_exact": "290099601/78125000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8311,
          "bytes": 147456,
          "start_seconds_exact": "290099601/78125000",
          "commit_seconds_exact": "2320802237/625000000"
        },
        {
          "replica": 1,
          "position": 8311,
          "bytes": 147456,
          "start_seconds_exact": "2320802237/625000000",
          "commit_seconds_exact": "1160403833/312500000"
        }
      ],
      "all_replica_commit_seconds_exact": "1160403833/312500000",
      "remote_lengths_after": [
        8312,
        8312
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1225654272
    },
    {
      "step": 120,
      "required_remote_epoch": 8312,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1225654272,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4903206912,
      "read_start_seconds_exact": "1160403833/312500000",
      "read_finish_seconds_exact": "2339961639/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8312,
          "bytes": 147456,
          "start_seconds_exact": "2339961639/625000000",
          "commit_seconds_exact": "584991767/156250000"
        },
        {
          "replica": 1,
          "position": 8312,
          "bytes": 147456,
          "start_seconds_exact": "584991767/156250000",
          "commit_seconds_exact": "2339972497/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "2339972497/625000000",
      "remote_lengths_after": [
        8313,
        8313
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1225801728
    },
    {
      "step": 121,
      "required_remote_epoch": 8313,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1225801728,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4903796736,
      "read_start_seconds_exact": "2339972497/625000000",
      "read_finish_seconds_exact": "1179564387/312500000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8313,
          "bytes": 147456,
          "start_seconds_exact": "1179564387/312500000",
          "commit_seconds_exact": "2359134203/625000000"
        },
        {
          "replica": 1,
          "position": 8313,
          "bytes": 147456,
          "start_seconds_exact": "2359134203/625000000",
          "commit_seconds_exact": "147446227/39062500"
        }
      ],
      "all_replica_commit_seconds_exact": "147446227/39062500",
      "remote_lengths_after": [
        8314,
        8314
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1225949184
    },
    {
      "step": 122,
      "required_remote_epoch": 8314,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1225949184,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4904386560,
      "read_start_seconds_exact": "147446227/39062500",
      "read_finish_seconds_exact": "2378298213/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8314,
          "bytes": 147456,
          "start_seconds_exact": "2378298213/625000000",
          "commit_seconds_exact": "1189151821/312500000"
        },
        {
          "replica": 1,
          "position": 8314,
          "bytes": 147456,
          "start_seconds_exact": "1189151821/312500000",
          "commit_seconds_exact": "2378309071/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "2378309071/625000000",
      "remote_lengths_after": [
        8315,
        8315
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1226096640
    },
    {
      "step": 123,
      "required_remote_epoch": 8315,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1226096640,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4904976384,
      "read_start_seconds_exact": "2378309071/625000000",
      "read_finish_seconds_exact": "599367489/156250000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8315,
          "bytes": 147456,
          "start_seconds_exact": "599367489/156250000",
          "commit_seconds_exact": "479495077/125000000"
        },
        {
          "replica": 1,
          "position": 8315,
          "bytes": 147456,
          "start_seconds_exact": "479495077/125000000",
          "commit_seconds_exact": "1198740407/312500000"
        }
      ],
      "all_replica_commit_seconds_exact": "1198740407/312500000",
      "remote_lengths_after": [
        8316,
        8316
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1226244096
    },
    {
      "step": 124,
      "required_remote_epoch": 8316,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1226244096,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4905566208,
      "read_start_seconds_exact": "1198740407/312500000",
      "read_finish_seconds_exact": "2416644003/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8316,
          "bytes": 147456,
          "start_seconds_exact": "2416644003/625000000",
          "commit_seconds_exact": "302081179/78125000"
        },
        {
          "replica": 1,
          "position": 8316,
          "bytes": 147456,
          "start_seconds_exact": "302081179/78125000",
          "commit_seconds_exact": "2416654861/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "2416654861/625000000",
      "remote_lengths_after": [
        8317,
        8317
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1226391552
    },
    {
      "step": 125,
      "required_remote_epoch": 8317,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1226391552,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4906156032,
      "read_start_seconds_exact": "2416654861/625000000",
      "read_finish_seconds_exact": "1217910177/312500000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8317,
          "bytes": 147456,
          "start_seconds_exact": "1217910177/312500000",
          "commit_seconds_exact": "2435825783/625000000"
        },
        {
          "replica": 1,
          "position": 8317,
          "bytes": 147456,
          "start_seconds_exact": "2435825783/625000000",
          "commit_seconds_exact": "608957803/156250000"
        }
      ],
      "all_replica_commit_seconds_exact": "608957803/156250000",
      "remote_lengths_after": [
        8318,
        8318
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1226539008
    },
    {
      "step": 126,
      "required_remote_epoch": 8318,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1226539008,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4906745856,
      "read_start_seconds_exact": "608957803/156250000",
      "read_finish_seconds_exact": "2454999009/625000000",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8318,
          "bytes": 147456,
          "start_seconds_exact": "2454999009/625000000",
          "commit_seconds_exact": "1227502219/312500000"
        },
        {
          "replica": 1,
          "position": 8318,
          "bytes": 147456,
          "start_seconds_exact": "1227502219/312500000",
          "commit_seconds_exact": "2455009867/625000000"
        }
      ],
      "all_replica_commit_seconds_exact": "2455009867/625000000",
      "remote_lengths_after": [
        8319,
        8319
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1226686464
    },
    {
      "step": 127,
      "required_remote_epoch": 8319,
      "selected_read_replica": 0,
      "remote_prior_read_bytes": 1226686464,
      "local_prior_read_bytes": 0,
      "current_kv_operand_bytes": 147456,
      "full_attention_qk_pv_flops": 4907335680,
      "read_start_seconds_exact": "2455009867/625000000",
      "read_finish_seconds_exact": "38659062/9765625",
      "replica_writes": [
        {
          "replica": 0,
          "position": 8319,
          "bytes": 147456,
          "start_seconds_exact": "38659062/9765625",
          "commit_seconds_exact": "2474185397/625000000"
        },
        {
          "replica": 1,
          "position": 8319,
          "bytes": 147456,
          "start_seconds_exact": "2474185397/625000000",
          "commit_seconds_exact": "1237095413/312500000"
        }
      ],
      "all_replica_commit_seconds_exact": "1237095413/312500000",
      "remote_lengths_after": [
        8320,
        8320
      ],
      "local_tail_bytes_after": 0,
      "logical_full_history_bytes_after": 1226833920
    }
  ],
  "summary": {
    "full_attention_qk_pv_flops": 623344877568,
    "initial_copy_network_bytes": 2415919104,
    "prior_history_logical_read_bytes": 155817345024,
    "remote_prior_read_bytes": 155817345024,
    "local_prior_read_bytes": 0,
    "current_kv_operand_bytes": 18874368,
    "append_replica_network_bytes": 37748736,
    "total_network_bytes": 158271012864,
    "remote_final_bytes_per_replica": 1226833920,
    "remote_physical_final_bytes": 2453667840,
    "local_tail_final_bytes": 0,
    "local_fixed_state_bytes": 0,
    "local_current_append_buffer_bytes": 147456,
    "final_unique_history_bytes": 1226833920,
    "local_tail_budget_fits": true,
    "communication_skeleton_seconds_exact": "1237095413/312500000",
    "initial_copy_seconds_exact": "18877493/312500000",
    "token_communication_seconds_exact": "7613862/1953125",
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
