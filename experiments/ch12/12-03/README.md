# 12-3：真实视觉编码与完整 EC 传输（有界部分实测）

2026-09-09，在 RTX 主机的 **CPU** 上，以缓存中的 **Qwen3-VL-8B-Instruct** 完成 3 张程序生成 PNG 的官方预处理、真实训练权重视觉前向及独立进程 TCP 传输。8 次交付全部验证通过；原图传输后重编码与完整 EC 直接传输的各张量形状、dtype、原始字节 SHA-256 一致。此处完成的是视觉边界实测，**不是全实验 12-3 完成**。

## 正文候选（供主 agent 统一回填）

> 真实 Qwen3-VL-8B CPU 视觉实测中，256×256 图像产生最终投影和三组 DeepStack，各为 BF16 `[64,4096]`；完整 EC 加 grid 的 safetensors 文件为 2,097,584 B，两个 PNG 原件分别仅 3,443 / 3,545 B。320×256 图像各组为 `[80,4096]`，EC 文件 2,621,872 B、PNG 3,708 B。独立 TCP 发送/接收进程的 8 次交付均逐位校验通过，原图远传后重编码与 EC 直接交付一致；重复图像可复用，同尺寸内容变化则失效。该结果来自 CPU、同机 loopback 和小型合成夹具，不证明端设备/WAN 性能、任务质量或语言 KV 可迁移。

## 固定模型与真实执行

- Snapshot：`0c351dd01ed87e9c1b53cbc748cba10e6187ff3b`；远端缓存 `/home/ubuntu/.cache/huggingface/hub/models--Qwen--Qwen3-VL-8B-Instruct/snapshots/…`。4 个既有分片合计 **17,534,339,512 B**，未下载、未回传权重。
- 官方 `Qwen3VLVisionModel`，27 层、hidden 1152、投影 4096、DeepStack block 索引 **8/16/24**。从 safetensors 按 `model.visual.*` 读取 **351 个 key、576,388,336 个参数**。先验证期望/实际 key 集合及形状相等，`strict=True, assign=True` 加载，再逐一验证已加载张量 dtype/shape/原始字节 hash 与读取权重相等。普通 CPU 构造时产生的初始化参数全部被训练权重覆盖；无缺失参数替代。
- `AutoProcessor` 实例为官方 `Qwen3VLProcessor`，调用其 `image_processor`，实际类为 `Qwen2VLImageProcessor`；没有文本请求，因此不运行 tokenizer/chat template。原始配置的旧 Fast 类名称与本版本解析后的实际类分开记录，未自写预处理。
- 现有 SG Python 3.10 环境实际加载 **Transformers 5.8.1 / Torch 2.10.0+cu128**，Torch 来自用户 site-packages，而非任务预期的 2.11。完整路径和版本见 [source-addendum.json](results/source-addendum.json)、[environment.json](results/environment.json)。未修改共享环境、未安装依赖。
- 官方 eager attention、BF16 参数与输入；processor 输出 FP32，输入 cast 单独计时。无 autocast、模型源码补丁、GPU/MPS、语言主干加载。`CUDA_VISIBLE_DEVICES=''`，四核 affinity，intra-op=4、inter-op=1；模型分阶段驻留，发送器不加载模型。
- 监督进程每 100 ms 检查本实验子进程聚合 RSS，阈值 11 GiB。采样峰值 **4,344,258,560 B（约 4.05 GiB）**；该值不包括监督器自身小额 RSS，也不是硬件级峰值。prepare/receiver/sender 均退出 0。未操作已有服务或 GPU。

## 输入、完整 EC 与语言 KV 的边界

[fixtures](fixtures/) 包含 `a-v1` / `a-v2`（256×256，同尺寸改变色块及版本文字）和 `b-v1`（320×256）。程序生成算法、PNG 压缩等级固定；2026-09-09 已逐张视觉 QA，版本文字、色块变化与宽度变化可辨，图像可正常解码。它们是确定性夹具，不是实拍任务或质量评测。

| 夹具 | PNG B | processor pixel_values | grid | 每组最终/DeepStack | EC 文件 B | 基准 encoder s |
|---|---:|---|---|---|---:|---:|
| a-v1 | 3,443 | FP32 [256,1536] | [1,16,16] | BF16 [64,4096] ×4 | 2,097,584 | 6.0426 |
| a-v2 | 3,545 | FP32 [256,1536] | [1,16,16] | BF16 [64,4096] ×4 | 2,097,584 | 5.7660 |
| b-v1 | 3,708 | FP32 [320,1536] | [1,16,20] | BF16 [80,4096] ×4 | 2,621,872 | 7.9719 |

EC 文件含 `pooler_output`、`deepstack_0/1/2` 与 INT64 `image_grid_thw`。256² 的四组特征原始字节共 2,097,152 B，grid 24 B；文件另含 safetensors header。所有官方返回的 `last_hidden_state` 也保存在 `vision-all.safetensors`，但它不是该官方语言入口消费的视觉特征，因此不放入传输 EC。原图重编码路径同样核验并保存它。

依据封存的官方 [modeling_qwen3_vl.py](results/sources/modeling_qwen3_vl.py)：`get_image_features` 获取投影并按 grid 分图；`Qwen3VLModel.forward` 用投影替换图片 placeholder，并将三组 DeepStack 交给语言层。grid 用于视觉位置准备。**EC 足以保存本例的视觉编码边界，不等于完整语言请求**：文本 input IDs、图片顺序、placeholder/mask、位置与语言模型仍需由下游准备。本次没有构建或运行这些语言输入，更没有生成/迁移语言 KV。EC 不包含 KV，也不证明更换问题后语言 KV 可以复用。

原章节和案例的 4B/640² 数值仅用于理解对象边界，不作为本次 8B 的测量。未访问或执行 calculations；本文表格来自实际存档张量和日志。

## 真实协议与缓存验证

`prepare` 进程先编码三张图并退出；新的 `receiver` 进程独立加载同一视觉模型，第三个 `sender` 进程只读取 PNG/EC 文件。两端通过 `127.0.0.1` 的真实 TCP socket 通信，不是共享队列模拟。单连接顺序为 `a-v1 → a-v1 → a-v2 → b-v1`，每轮先 raw、再 EC，共 8 个请求；真实 PID、端口、退出与计时在 [supervisor.jsonl](results/supervisor.jsonl)、[sender.jsonl](results/sender.jsonl)、[receiver.jsonl](results/receiver.jsonl)。

协议 `vision-ec-v1`：12 B 大端 `uint32 JSON长度 + uint64 payload长度`，随后 UTF-8 JSON 和原样 PNG 或 safetensors payload。JSON 带 seq/name/mode/protocol/payload SHA-256。接收端收齐并验证后发同结构空 payload ACK，JSON 中携带验证状态、字节和耗时。日志中的 wire bytes 是**应用层 framing 字节**，不含 TCP/IP、链路头或重传。请求总计 8,929,959 B，ACK 总计 2,151 B。

接收 raw 时，以 `SHA256(PNG bytes + canonical identity JSON)` 为缓存键。identity 固定 snapshot、config hash、processor 配置、源码 hash、Torch/Transformers 版本、dtype、attention 和协议。命中序列为 **miss / hit / miss / miss**；`a-v2` 与 `a-v1` 的尺寸相同，但 key 及四组特征 hash 均不同，不能以尺寸复用。该 key 对不同 PNG 编码但相同像素也会保守失效。本次只实测内容变化失效，未另外测模型/预处理版本切换。

每次 EC 请求都真的发送完整文件，包括重复帧；EC 直接路径不运行 encoder。每个 raw miss 独立重编码，并与基准的 processor、全部视觉返回值核验一致；raw hit 取回已有完整 EC 后重新做 hash 验证。这里不宣称跨后端数值一致，也未测外部缓存服务、并发/驱逐/故障恢复。

## 计时口径

原始浮点秒与 monotonic 时间戳均保留，只有表格显示值做舍入。单次小样本、固定顺序、没有单独预热，不作性能置信区间或因果比较。

- `model_ready.seconds`：类构造、逐 key 权重提取/核验、加载及 processor 准备；不计入 encoder。
- `png_decode_s`：Pillow 打开并 `load()`；`processor_s`：官方 image processor；`input_cast_s`：FP32→BF16；`encoder_s`：实际同步 CPU 前向，含模型内部的投影和 DeepStack。基准 processor 分别 3.617 / 0.865 / 21.532 ms，非纯 resize 性能。
- `serialize_s`：内存中将完整 EC 转为 safetensors bytes，约 0.403–0.494 ms；不包括落盘、processor 输出及全返回张量的存档。
- `sendall_s`：包含 JSON 序列化、协议头构造与全部 `sendall` 调用；完成只说明数据交给 socket，不表示对端已验证。EC 为 1.093–1.567 ms。
- `send_to_verified_ack_s`：开始发请求至收齐验证 ACK，包含接收端工作和日志开销。三个 raw miss 分别 **6.0350 / 5.7293 / 7.4546 s**，raw hit **1.114 ms**；四个 EC 请求 **4.551–5.607 ms**。它不是单向网络延迟，也没有将发送前已完成的编码算入 EC 路径。判断端侧编码端到端收益必须加回该成本。
- receiver 的 `recv_wait_and_read_s` 包含等待下一请求的空闲时间；不能当作纯传输时间。`decode_or_reencode_and_verify_s` 含反序列化或 PNG 编码路径、缓存、tensor hash，以及 miss 时存档等工作；encoder 自身另列。TCP 首次连接发生在上述请求计时之前，未计入。

全部测量为同一 CPU 主机、loopback。没有 WAN、端设备、GPU、传输限速或丢包仿真；共存服务和 CPU 竞争未受控。PNG 高度可压缩，不能把本表放大为真实截图的比率。

## 证据与复跑

- [run.py](run.py)：夹具、严格权重加载、官方编码、独立 sender/receiver。
- [launch.py](launch.py)：四核限制、聚合 RSS 监督、子进程与退出记录。
- [analyze.py](analyze.py)：Mac CPU 上用 Python 标准库独立解析 safetensors 文件，复核 shape/dtype/原始 bytes hash、内容版本失效、8 条两端日志及退出。不加载模型，也不依赖 Torch。
- [summary.json](results/summary.json)、[weights-manifest.json](results/weights-manifest.json)、[manifest.json](manifest.json)：结果与文件级校验。每张图的目录中保存 processor 张量、完整返回值、EC 和接收端副本。
- 最终使用普通官方 CPU 构造，初始化非持久 inv_freq buffer，再严格加载训练权重，无模型源码 patch。prepare/receiver/sender 均退出0，8次交付逐位一致；官方 buffer 定义见 [source-addendum.json](results/source-addendum.json)。

只复核现有证据：

```sh
python3 experiments/ch12/12-03/analyze.py
```

远端复跑需在本实验目录下新建一个空子目录，将 `run.py`、`launch.py` 复制进去，再运行 `/home/ubuntu/sglang-venv/bin/python launch.py`，避免覆盖封存结果。脚本将离线读取固定缓存，CPU 模型驻留、权重核验和全部传输均重新执行；若环境已改变，版本与结果也必须重新归档。不得复制权重或在其他实验目录执行。`analyze.py` 放入同一复跑目录可复核新结果。

未完成：完整模型答案/任务成功率、语言 prefill/decode 与 KV 迁移、真实跨设备/WAN 传输、物理功耗、完整助手动作闭环、SGLang/vLLM 实际 connector。无需 GPU 失败交接，本例官方 CPU 路径已成功；这些未执行项仍留待主 agent 决定后续工作。
