# checkpoint-resume — 

输入：`{"experiment": "ch10/10-06", "load_worlds": [2, 3, 1], "save_world": 2}`

来自封存DCP重分片恢复与下一步实际训练记录，非GPU性能。

| 结果 | 值 |
| --- | ---: |
| archived_evidence_files | 15 |
| logical_state_tensors | 19 |
| unique_logical_state_bytes | 463,688 |
| actual_checkpoint_file_bytes | 518,512 |
| metadata_bytes | 6,393 |
| actual_minus_logical_bytes | 54,824 |
| restored_ranks | 6 |
| next_loss | 1.3159840106964111 |
| all_reported_next_states_match | `true` |
| all_reported_adam_negative_controls_detected | `true` |

| 操作 | world | axis | 最大rank API s | 全组局部状态 bytes | 第一权重各rank形状 |
| --- | ---: | ---: | ---: | ---: | --- |
| save | 2 | 0 | 0.29678282095119357 | 473824 | [[129, 129], [128, 129]] |
| load | 2 | 0 | 0.04859711299650371 | 473824 | [[129, 129], [128, 129]] |
| load | 3 | 1 | 0.06458290317095816 | 483960 | [[257, 43], [257, 43], [257, 43]] |
| load | 1 | 0 | 0.04960532812401652 | 463688 | [[257, 129]] |

| 状态张量 | 全局shape | dtype | 唯一逻辑 bytes | 保存chunk数 |
| --- | --- | --- | ---: | ---: |
| model.0.weight | [257, 129] | torch.float32 | 132612 | 2 |
| model.0.bias | [257] | torch.float32 | 1028 | 2 |
| model.3.weight | [17, 257] | torch.float32 | 17476 | 2 |
| model.3.bias | [17] | torch.float32 | 68 | 2 |
| optim.0.exp_avg | [257, 129] | torch.float32 | 132612 | 2 |
| optim.0.exp_avg_sq | [257, 129] | torch.float32 | 132612 | 2 |
| optim.1.exp_avg | [257] | torch.float32 | 1028 | 2 |
| optim.1.exp_avg_sq | [257] | torch.float32 | 1028 | 2 |
| optim.2.exp_avg | [17, 257] | torch.float32 | 17476 | 2 |
| optim.2.exp_avg_sq | [17, 257] | torch.float32 | 17476 | 2 |
| optim.3.exp_avg | [17] | torch.float32 | 68 | 2 |
| optim.3.exp_avg_sq | [17] | torch.float32 | 68 | 2 |
| optim.0.step | [] | torch.float32 | 4 | 1 |
| optim.1.step | [] | torch.float32 | 4 | 1 |
| optim.2.step | [] | torch.float32 | 4 | 1 |
| optim.3.step | [] | torch.float32 | 4 | 1 |
| rng | [5056] | torch.uint8 | 5056 | 1 |
| data_rng | [5056] | torch.uint8 | 5056 | 1 |
| cursor | [] | torch.int64 | 8 | 1 |

计量条件：

- 实际CPU/Gloo PyTorch2.10.0+cu128小模型，2进程行保存→2行/3列/1完整恢复，非Qwen或多机GPU训练。模型Linear129→257→17含tanh/Dropout，FP32 AdamW，先更新4步保存，再核验第5步。
- 文件SHA逐一核验，19逻辑状态形状与chunk坐标来自已封存inspect_checkpoint对实际metadata的提取；本CLI不重新反序列化metadata或执行torch恢复。恢复和下一步相同来源为封存实际加载/训练记录。
- 矩形chunk先检查边界、两两无交集，再以总体积证明完整覆盖；标量体积为1。局部shape按固定源码DTensor placement核对，RNG和标量复制；全组局部字节可因复制大于唯一逻辑状态。
- 数据容器与metadata总文件字节、唯一逻辑载荷分开；差额可能含序列化、对齐和复制等，不单独归因为某种开销，不把该差额或API时间当磁盘吞吐。
- 每rank API在barrier后计时，只取各路径最大rank，不相加，也没有共同起止全局墙钟。未含torchrun启动、DTensor构造、加载后full_tensor聚合与下一步训练；每路径一次不排名布局性能。
- 恢复目标先置零；恢复后聚合成完整张量，再走相同单进程数学路径，故不证明不同分布式归约能逐位相同。全部6恢复rank检出清空Adam动量负对照；真实DataLoader队列、packing残留和大模型完整恢复仍待。

固定来源：

- [sources/checkpoint-resume/run.py](../../experiments/ch10/10-06/run.py)，SHA256 `e48837d6ec9d8fdbf8c4bbee1c23036bb7323c33d07958150ffe35e0e85e5121`。
- [sources/checkpoint-resume/inspect_checkpoint.py](../../experiments/ch10/10-06/inspect_checkpoint.py)，SHA256 `547c9d8be88b1984305b7681b88b71f699771794945709e819d6db63fe447435`。
- [sources/checkpoint-resume/results/checkpoint-manifest.json](../../experiments/ch10/10-06/results/checkpoint-manifest.json)，SHA256 `25c72373c9c31c0b1fa99c9cfcea191e098394501637ebfbde286528ba1941f5`。
- [sources/checkpoint-resume/results/reference.json](../../experiments/ch10/10-06/results/reference.json)，SHA256 `5d67bd31b9e9174771e23d9ecefb2e0a61f2921fdfcb0c24a0e075976f788013`。
