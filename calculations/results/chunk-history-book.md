# chunk-history — 

输入：`{"input_tokens": 8192, "model": "qwen3-8b", "new_tokens_per_chunk": 512, "trials": 11}`

CUDA event区间来自封存逐块实测；有效配对和backbone矩阵工作按官方配置独立复算。

| 结果 | 值 |
| --- | ---: |
| requests | 11 |
| prefill_chunks | 176 |
| empty_execute_calls | 11 |
| first_median_ms | 25.300640106201172 |
| last_median_ms | 35.07001495361328 |
| paired_last_first_median | 1.3884246512899991 |
| ratio_of_medians | 1.3861315289417377 |
| first_causal_pairs | 131,328 |
| last_causal_pairs | 4,063,488 |
| causal_pair_ratio_exact | `"5291/171"` |
| first_backbone_matrix_flops | 7,189,926,248,448 |
| last_backbone_matrix_flops | 9,509,208,588,288 |
| backbone_matrix_ratio_exact | `"62977/47617"` |
| full_prefill_backbone_matrix_flops | 133,593,078,693,888 |

| 历史token | 新token | 有效因果配对 | backbone矩阵FLOPs | 区间中位ms | 最小ms | 最大ms |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 512 | 131328 | 7189926248448 | 25.300640106201172 | 25.020479202270508 | 25.560224533081055 |
| 512 | 512 | 393472 | 7344545071104 | 25.217824935913086 | 25.02521514892578 | 25.525983810424805 |
| 1024 | 512 | 655616 | 7499163893760 | 25.92140769958496 | 25.57734489440918 | 26.181663513183594 |
| 1536 | 512 | 917760 | 7653782716416 | 26.73129653930664 | 26.593568801879883 | 27.058271408081055 |
| 2048 | 512 | 1179904 | 7808401539072 | 27.89651107788086 | 27.62995147705078 | 28.218687057495117 |
| 2560 | 512 | 1442048 | 7963020361728 | 28.655296325683594 | 28.424320220947266 | 29.19500732421875 |
| 3072 | 512 | 1704192 | 8117639184384 | 29.30441665649414 | 29.168672561645508 | 29.57801628112793 |
| 3584 | 512 | 1966336 | 8272258007040 | 29.800479888916016 | 29.688608169555664 | 30.066560745239258 |
| 4096 | 512 | 2228480 | 8426876829696 | 30.495967864990234 | 30.389631271362305 | 30.6713924407959 |
| 4608 | 512 | 2490624 | 8581495652352 | 31.13030433654785 | 30.96463966369629 | 31.4532470703125 |
| 5120 | 512 | 2752768 | 8736114475008 | 31.837919235229492 | 31.662559509277344 | 32.14195251464844 |
| 5632 | 512 | 3014912 | 8890733297664 | 32.50624084472656 | 32.18268966674805 | 32.65427017211914 |
| 6144 | 512 | 3277056 | 9045352120320 | 33.20947265625 | 32.82921600341797 | 33.3746223449707 |
| 6656 | 512 | 3539200 | 9199970942976 | 33.80691146850586 | 33.48771286010742 | 34.08195114135742 |
| 7168 | 512 | 3801344 | 9354589765632 | 34.45951843261719 | 34.177345275878906 | 34.74943923950195 |
| 7680 | 512 | 4063488 | 9509208588288 | 35.07001495361328 | 34.85785675048828 | 35.341854095458984 |

计量条件：

- 导入实验8-2 chunk-history的15个封存文件，核对SHA、配置、请求ID、连续history、输出一致与零APC；不重跑GPU。11个正式请求各16块，空execute调用单列。
- RTX PRO 6000、vLLM0.23、BF16、eager、单活跃请求、512预算，同引擎重复；其他GPU服务保留。输入为固定合成token，不能当作生产轨迹或答案质量验证。
- event_ms为execute_model前后CUDA event区间，包含完整模型路径和可能的主机提交间隙；外部logits／采样不在区间内，官方工作采用output_head=none并仅计矩阵FLOPs。
- 注意力有效配对、完整backbone矩阵工作和实测时间分别列；配对比例不能当作整体算力、HBM访问或时间倍率。位置、内容、末块处理及执行顺序共同变化，不识别独立因果贡献。
- 配对末／首比例的中位数与两个位置中位数之比单独报告；11次样本保留，不生成置信区间或饱和服务SLO结论。

固定来源：

- [sources/chunk-history/PROTOCOL.md](../../experiments/ch08/08-02/chunk-history/PROTOCOL.md)，SHA256 `5e7c25c3bb800193650cfb17ced5ef538537d11e5742e8261ea9f40d9d4e8852`。
- [sources/chunk-history/README.md](../../experiments/ch08/08-02/chunk-history/README.md)，SHA256 `ddc495b8f94b212e8398d731577b027cbd6358c783b141068a7ecccecd894e90`。
- [sources/chunk-history/analyze.py](../../experiments/ch08/08-02/chunk-history/analyze.py)，SHA256 `f16d38b61e02e14a0c146b3daeb5f6eaaac94d66e3f52cd7591a02f47643404b`。
- [sources/chunk-history/engine-config.json](../../experiments/ch08/08-02/chunk-history/engine-config.json)，SHA256 `0ed4ce3eceb19e14244aee664b96a921d02ef53fc5d5759d53664a5db32bc391`。
- [sources/chunk-history/input-provenance.json](../../experiments/ch08/08-02/chunk-history/input-provenance.json)，SHA256 `515476e3c6dd7c9a4774ae24757b3dc926bf426c67997b02f6ae9bfd8aae075c`。
- [sources/chunk-history/inputs.json](../../experiments/ch08/08-02/chunk-history/inputs.json)，SHA256 `cc01544fe8eaf45e5bfcfc030184076814ec7b1daa592e534ddf95cd350c7fc1`。
- [sources/chunk-history/plot.py](../../experiments/ch08/08-02/chunk-history/plot.py)，SHA256 `fdb2824cb67ec579e5d2cde7848f33b40b40cdad013c12a8ab275f15b8d28f1a`。
- [sources/chunk-history/results/history.png](../../experiments/ch08/08-02/chunk-history/results/history.png)，SHA256 `7d1d85f63051a671f0c460b3250f791f2ff62ceac869f5e17326b8724ba9f52b`。
- [sources/chunk-history/results/history.svg](../../experiments/ch08/08-02/chunk-history/results/history.svg)，SHA256 `0f2cc10ccf35ae6a9b68f81686d7aa18d26ac6b1f236ae084ddb8d74a6a1d0ab`。
- [sources/chunk-history/results/run-v1/raw.json](../../experiments/ch08/08-02/chunk-history/results/run-v1/raw.json)，SHA256 `2fd5e42b90159566bd3ef3fc4180c84fbc48acc56b846d3f1b42633aa6900879`。
- [sources/chunk-history/results/summary.json](../../experiments/ch08/08-02/chunk-history/results/summary.json)，SHA256 `b7e561051b6d1ba41cc5a0a7473c08c29b976e2c593a4f542e1b179a6e1f05f8`。
- [sources/chunk-history/run.log](../../experiments/ch08/08-02/chunk-history/run.log)，SHA256 `2a8dd7253750b400a1b59baf69b7b8968cd9d310a0fecc4d9351a7ea05638fa4`。
- [sources/chunk-history/run.py](../../experiments/ch08/08-02/chunk-history/run.py)，SHA256 `0c2b7d25b3402b80fef604afa42a72abd54e923ffeb8740e64fb495be06a164d`。
- [sources/chunk-history/step_worker.py](../../experiments/ch08/08-02/chunk-history/step_worker.py)，SHA256 `b97a54d2f0ad6de710fdc9edaaa78106cf01cb15a889db86c28545cc801deff2`。
- [sources/chunk-history/manifest.json](../../experiments/ch08/08-02/chunk-history/manifest.json)，SHA256 `5ca4f338233965341ac4edd14887a75bf2a3325af9a18f179820a46806966f4b`。
- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
