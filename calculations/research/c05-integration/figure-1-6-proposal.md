# 图1-6草案：相同8卡与请求，不同组织

两图均是当代Qwen3-32B教学配置。每卡24×10⁹bytes、显式workspace2GiB，BF16权重/KV；每次只处理batch1的一个新token，重复32次。节点标通信事件数，不能当作时间比例图。

```mermaid
flowchart LR
 subgraph S0[单服务器：8卡 TP8]
 E[词表embedding规约 1次] --> L[64层：每层attention及FFN各规约1次]
 L --> H[末位置logits all-gather 1次]
 H --> B[采样未计时；token树广播1次]
 B -. 下一前向 .-> E
 end
 C[8张物理卡各自核容量；最大10608683008 bytes] --- S0
```

```mermaid
flowchart LR
 subgraph S1[服务器0：4卡 TP4 / PP0]
 A[embedding规约1次] --> L0[层0至31：64次规约]
 end
 subgraph S2[服务器1：4卡 TP4 / PP1]
 L1[层32至63：64次规约] --> Z[logits all-gather1次；采样未计时]
 end
 L0 -- 4份复制hidden：40960bytes --> L1
 Z -- token反馈：4bytes --> T[首stage token广播1次]
 T -. 下一前向 .-> A
 C[8张物理卡各自核容量；最大10608011264 bytes] --- S1
```

跨服务器hidden与token反馈串行使用一个声明共享出口，每前向2次启动、40964bytes。内部collective按独立有向环边预算；两个服务器仍处于同一条单微批依赖链。对应默认完整预算与逐层消息见ub-scope-qwen32-default.md。正式制图需遵循全书图形流程，本图稿尚非已验收图片。
