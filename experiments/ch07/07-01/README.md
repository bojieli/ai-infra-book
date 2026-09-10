# 实验 7-1：八卡服务器之间的模型切分

对应正文 7.1。为 V4-Pro 和 Kimi K3 先求容量下界，再比较服务器内 TP／EP、服务器间 PP，以及跨服务器 TP／EP 的候选；用固定 InfiniBand 或以太网配置分别计算 prefill 与 decode，说明什么延迟目标下跨服务器推理仍然可行。

## 独立运行

```bash
python3 run.py    # 现场调用 calculations/calc.py state|v4-forward|k3-forward
```

只需 Python 3.8+ 标准库。每卡 80 GB、每机 8 卡；通信模型 `每次交接 = α + 载荷/有效带宽`，α 与有效带宽是声明输入。

## 容量下界：单机方案直接出局

| 模型 | 统一 BF16 权重 | decode 状态 | 最少卡数 | 最少服务器 |
| --- | ---: | ---: | ---: | ---: |
| DeepSeek-V4-Pro | 3,146 GB | 6.87 GB | **40** | **5** |
| Kimi K3 | 5,559 GB | 43.58 GB | **71** | **9** |

两个模型都装不进一台八卡服务器——V4-Pro 至少要 5 台，K3 至少要 9 台。**"服务器内 TP／EP"这个候选在容量上就不成立**，讨论只在 B（服务器间 PP）与 C（跨服务器 TP／EP）之间进行。

## 通信预算

| 模型 | 阶段 | 互联 | 方案 | 每次载荷 | 交接次数 | 通信时间 |
| --- | --- | --- | --- | ---: | ---: | ---: |
| V4-Pro | prefill 8192 | InfiniBand | **B：PP** | 112 MiB | 4 | **9.42 ms** |
| V4-Pro | prefill 8192 | InfiniBand | C：跨机 TP | 112 MiB | 61 | **143.58 ms** |
| V4-Pro | prefill 8192 | 以太网 | C：跨机 TP | 112 MiB | 61 | 287.77 ms |
| V4-Pro | decode b64 | InfiniBand | B：PP | 0.88 MiB | 4 | 0.09 ms |
| V4-Pro | decode b64 | InfiniBand | C：跨机 TP | 0.88 MiB | 61 | 1.42 ms |
| V4-Pro | decode b64 | 以太网 | C：跨机 TP | 0.88 MiB | 61 | 3.46 ms |
| K3 | prefill 8192 | InfiniBand | C：跨机 TP | 112 MiB | 93 | 218.90 ms |
| K3 | decode b64 | 以太网 | C：跨机 TP | 0.88 MiB | 93 | 5.27 ms |

三条判断：

1. **prefill 和 decode 的答案完全不同**。prefill 的每次载荷是 112 MiB，跨机 TP 要 61／93 次，通信就吃掉 144–439 ms；PP 只交接 4／8 次，降到 9–38 ms，**15 倍以上**。decode 的载荷只有 0.88 MiB，跨机 TP 也只要 1.42–5.27 ms。**prefill 必须用 PP 跨机，decode 用什么都可以。**
2. **以太网与 InfiniBand 的差距在 decode 上被 α 主导**。decode 跨机 TP 从 1.42 涨到 3.46 ms（2.4 倍），而两者带宽差 2 倍、α 差 4 倍——小消息下 α 是主要项。prefill 上差距是 2 倍（143.6→287.8 ms），由带宽主导。
3. **跨服务器推理可行的延迟目标**：以 V4-Pro decode 为例，跨机 TP 在 InfiniBand 上每步加 1.42 ms、以太网上加 3.46 ms。若逐 token 延迟目标是 50 ms，这分别占 2.8% 与 6.9%，**可行**；若目标是 10 ms（高速生成场景，见实验 8-6），以太网方案的通信就占 35%，只能改用 PP 或缩小跨机范围。prefill 侧则相反：TTFT 目标若是 1 s，PP 的 9.4 ms 可忽略，跨机 TP 的 143.6 ms 已占 14%，以太网的 287.8 ms 占 29%——**TTFT 目标在 1 s 以内时跨服务器 TP 不可取**。

完整数值见 [results/split.md](results/split.md)。

## 限制

- 权重按统一 BF16 口径，不是 V4／K3 实际混合量化格式的存储；实际部署会小很多，但卡数下界的结论方向不变。
- 通信只算集合交接的载荷与次数，不含拥塞、重叠与集合通信库的算法选择（见实验 6-4）。
- 只比较三类候选的通信项，未加入计算与访存；完整步时下界见实验 7-2。
- α 与有效带宽是声明输入，需要实测校正（实测的远程调用分解见实验 7-4）。
