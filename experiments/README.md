# 全书实验

十二章共 106 项实验与计算。**每一项都有自己的目录**（`chXX/XX-YY/`），各自包含输入、可独立运行的程序、README 和运行结果，不依赖相邻实验的运行产物。正文在每个实验块之后回填一段简洁结果与链接；完整条件、原始记录与限制留在各实验目录的 README 中。

## 目录约定

```
experiments/chXX/XX-YY/
├── run.py        # 独立运行入口，只依赖 Python 3.8+ 标准库（实跑项另注依赖）
├── README.md     # 题目、固定输入、结果、判断与限制
├── results/      # JSON 与 Markdown 结果，必要时含 SVG
└── verify.py     # 可选：与 calculations/ 的独立实现交叉核对
```

正文编号与目录编号在第 8、11 章有历史错位（如正文实验 8-5 对应目录 `ch08/08-07`），各目录 README 首行已注明映射，路径作为稳定证据地址保留。原第 13 章的案例已并入前十二章，`ch13/` 保留为封存证据地址。

## 两类实验

- **计算类**：直接复用 [`calculations/`](../calculations/README.md) 已复算的结果，或由 `run.py` 现场调用其 CLI 生成；本目录**不重复实现公式**，只做本题需要的组织、对照、判断与绘图。每个 README 都注明数字的来源命令与固定输入。
- **实跑类**：在本地 Apple M2 Max 或 `rtx-pro`（NVIDIA RTX PRO 6000 Blackwell Workstation Edition，96 GB，SM120，PyTorch 2.10/2.11，共享设备）上实际执行，保留完整原始记录、哈希与失败尝试。GPU 上有其他常驻服务，测量保留共享设备条件，不声称整卡独占。

## 运行

```bash
cd experiments/ch04/04-05 && python3 run.py      # 任取一项，独立运行
```

计算类实验需要仓库中的 `calculations/`（同一仓库内，无需额外安装）。实跑类实验的环境与依赖锁文件在各自目录中说明。

## 状态

`inventory.json` 保存正文题目、目录、证据与状态：

- `delivered`（92 项）：目录、程序、结果与正文回填齐备。
- `delivered_with_documented_gaps`（18 项）：主路径已交付，`remaining` 字段逐项写明仍未覆盖的部分（如无 E2B 凭据、公开记录中不存在同条件训练原始数据、后端拒绝某项配置、Agent 未产出可用新内核等）。**负结果与失败尝试按原协议完整保留，不改写成成功。**

记录保留规则：成功重跑后删除被替代的启动与配置调试失败产物，只交付最终成功运行及复现所需文件；正式实验的配对重复、预设故障注入、数值与质量负结果完整报告。

详细分工与验证记录见 [PROGRESS.md](PROGRESS.md) 与 [SCOPE-REVIEW.md](SCOPE-REVIEW.md)。
