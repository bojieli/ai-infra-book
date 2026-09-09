# 12-03 vision worker

状态：**有界真实视觉实测完成；全 12-3 仍为部分完成**。2026-09-09。

交付：`experiments/ch12/12-03/README.md`（含简洁正文候选）、独立 `run.py` / `launch.py` / `analyze.py`、3 PNG、processor/grid 张量、完整 vision 返回、完整 EC、接收端副本、351 key 权重 manifest、固定 config/源码及 hash、原始计时/传输/退出日志、首轮失败原件、summary 与文件 manifest。指定远端同路径归档。本地约 39 MB，无权重。

真实结果：Qwen3-VL-8B-Instruct snapshot `0c351dd01ed87e9c1b53cbc748cba10e6187ff3b`，4 分片 17534339512 B 全为既有缓存。按 key 读取 351 组/576388336 参数，严格匹配并逐项验证加载后 hash。官方 Qwen3VLVisionModel / AutoProcessor，27 层视觉、4096 投影、DeepStack 8/16/24，CPU BF16 eager。现有环境实际 Transformers 5.8.1 / Torch 2.10.0+cu128（用户 site），没有改环境。

3 张夹具实际编码成功。256² 的最终投影+3 DeepStack 各 [64,4096]，完整 EC safetensors 含 grid 为 2097584 B，PNG 3443/3545 B；320×256 为各 [80,4096]，EC 2621872 B，PNG 3708 B。独立 TCP sender/receiver 8 次交付均逐位一致；原图传输后重编码的 processor 与全部 vision 返回也一致。重复/变化序列 raw cache 为 miss/hit/miss/miss，同尺寸变化的四组输出 hash 均不同。

资源/验收：仅 RTX 主机 CPU 四核 affinity，intra-op4/inter-op1，CUDA不可见，无 GPU/MPS 或语言模型加载，无服务操作。监督子进程聚合 RSS 100ms 采样峰 4344258560 B，11 GiB 阈值；prepare/receiver/sender 均 exit0。Mac CPU 标准库独立解析 safetensors 与两端日志通过，PNG 已逐张视觉 QA。

真实失败保留：首轮 meta 构造的非持久 RoPE inv_freq buffer 未被 state_dict 覆盖，真实前向失败 exit1。`attempts/meta-buffer-failure/` 含原代码/traceback。改为官方普通 CPU 构造，全部参数严格覆盖训练权重后成功；未 patch 模型源码，没有随机参数替代缺失权重。

边界：原始 CPU 编码约 5.7–8.0s；loopback 的 EC send-to-verified-ACK 约4.55–5.61ms，不能当 WAN/端设备/GPU 性能，也不含预先完成的编码。小夹具不评任务质量。完整语言答案、语言KV迁移、物理功耗、WAN/真实跨设备、完整动作闭环和生产 connector 均未完成。

纪律：仅写用户授权两个本地位置及对应远端实验目录；未访问/执行/修改/复制 calculations 工作，未联系其 session/作者；未修改正文、总进展、inventory、references 或其他实验；无 git 提交，无 agent/Codex 派生，无跨 session 最终复核。
