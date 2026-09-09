# 完整模型资源快照

本目录保留最终 `probe.py` 和一次成功的只读资源观测，结果不是完整模型容量或推理通过的证明。`results/observation.json` 中记录脚本 SHA256、采样时间和资源信息；`results/meminfo.txt`、`gpu.txt`、`gpu-processes.txt` 保留实际原始快照。

观测时 CPU MemAvailable 为 77,525,276 KiB（约73.93 GiB）；RTX PRO 6000 Blackwell 总显存97,887 MiB、已用60,956 MiB、空闲36,294 MiB。它们是当时共享主机的快照，不代表当前空闲量，也未通过实际完整模型加载测定容量。

**110 GiB CPU offload 仅为候选配置，不是最低需求证明。** 候选来源记录于 observation.json；没有由该快照得出完整模型可运行、不可运行或最低资源需求的结论。相邻 native-layer-probe 的成功仅限截断四层、两次合成请求，不构成完整模型或质量通过。

`probe.py --out <全新结果目录>` 可在原主机采集新的只读资源快照；本次清理未重新采样、运行模型或操作现有进程。最终脚本和四个资源记录均纳入 `raw-transfer-manifest.json`，本目录交付文件由 `manifest.json` 封存（manifest 自身除外）。
