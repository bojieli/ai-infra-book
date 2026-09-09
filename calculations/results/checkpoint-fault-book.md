# checkpoint-fault — 

输入：`{"experiment": "ch10/10-07", "fault_processes": 1, "normal_processes": 1}`

来自封存DCP元数据提交前终止实验，未完成提交不填时间。

| 结果 | 值 |
| --- | ---: |
| archived_evidence_files | 20 |
| completed_commits | 3 |
| incomplete_commits | 1 |
| incomplete_load_error_type | `"CheckpointException"` |
| incomplete_data_bytes | 12,622,659 |
| fallback_recovered_cursor | 3 |
| last_completed_training_cursor | 43 |
| completed_updates_after_recovery_point | 40 |

| 分支 | 快照 | API s | stage s | writer s | 调用到commit s | 未完成观察 s | 数据 bytes | metadata bytes | 实际加载成功 |
| --- | --- | ---: | ---: | ---: | --- | --- | ---: | ---: | --- |
| normal | checkpoint-1 | 0.011327265994623303 | 0.009255638113245368 | 0.05705438717268407 | 0.07616994017735124 | None | 12622659 | 2526 | True |
| normal | checkpoint-2 | 0.00725071388296783 | 0.002600746927782893 | 0.03698247903957963 | 0.04829886695370078 | None | 12622659 | 2526 | True |
| fault | checkpoint-1 | 0.009852709947153926 | 0.004717637086287141 | 0.050992392003536224 | 0.06261501298286021 | None | 12622659 | 2525 | True |
| fault | checkpoint-2 | 0.009479633066803217 | 0.00457123015075922 | 0.030256371945142746 | None | 0.24184582196176052 | 12622659 | 0 | False |

计量条件：

- 真实CPU单线程PyTorch2.10.0+cu128 DCP，1024×1024 Linear/Tanh/Dropout与AdamW，快照cursor3/23后各训练20步。非Qwen/GPU性能；正常与故障各一进程，不能推出故障率或p95。
- 故障在第二份数据写完、metadata提交之前人为设置屏障，父进程等API返回和20步训练完成再SIGKILL。此阻塞区间不是慢存储或带宽测量，不估算有效写入带宽。
- 实际数据文件与metadata逐文件SHA核验；三份加载成功及一份拒绝来自封存实际torch加载记录，本CLI不反序列化或重新训练。只有正常分支记录完整环境，故障执行源码由同一监督器哈希及运行结构绑定。
- 未完成提交时间保留null，kill减api_call仅是未完成观察长度；future_complete是主线程等待后的观察，不当内部就绪时刻。文件已有字节不证明已提交，更不证明断电或远端复制持久性。
- 源程序固定前3步、两轮各20步，故障前完成cursor43、回到3需重做40次更新；没有下一步恢复训练或重新执行这40步的时间证据，不推ETTR。进程终止不代表断电、多rank或磁盘故障。

固定来源：

- [sources/checkpoint-fault/run.py](../../experiments/ch10/10-07/run.py)，SHA256 `2dd21009f42a8b5ca4d582c8be608db0684800f225eddb59fb54ee9886a3ef8a`。
- [sources/checkpoint-fault/results/raw-manifest.json](../../experiments/ch10/10-07/results/raw-manifest.json)，SHA256 `53c5cfd4944e914f1269e226f52500d7007224be02ad7fb9ab9a1a5d3d768094`。
- [sources/checkpoint-fault/results/normal/environment.json](../../experiments/ch10/10-07/results/normal/environment.json)，SHA256 `83c7c74ac7f888305bab1d9d1912c597c1ffc5d840e6567dde9d79412386be62`。
- [sources/checkpoint-fault/results/outcomes.json](../../experiments/ch10/10-07/results/outcomes.json)，SHA256 `d09d50953ca85723d10d654d62bf37fcab16104c78a5b3f35ba5890ec3f20f11`。
