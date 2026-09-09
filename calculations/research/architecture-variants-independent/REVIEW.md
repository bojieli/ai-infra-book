# Architecture variants independent review

结论：冻结候选核心数学通过，可按声明的未训练结构比较范围集成。无参数、TP状态或切换区间计算阻塞。check.py、results.json及快照绑定候选；未修改作者或共享文件。

## 参数守恒与对齐

独立计算 `P=2VH+H+L(2HQD+2HKD+3HF+2H+2D)`，包含两个词表、每层两个hidden norm与共享于所有头的Q/K norm各D。不是每个query/KV head另复制D个norm参数。

默认严格等参例：KV8→2释放每层`2×4096×6×128=6,291,456`参数；FFN12288→12800增加`3×4096×512=6,291,456`。因此两者都8,190,735,360参数。query heads保持32、hidden4096，所以QK/PV不变；所有token线性矩阵参数也相等，整个矩阵FLOPs保持相等。KV逐token从147456B降为36864B。scalar和质量不因此相等。

独立核7种alignment×6变体=42项，按理想有理数F检查左右相邻对齐候选，误差不超过3LH×alignment/2；另外192在128步长的平局选256。baseline维持真实12288，即便alignment不整除baseline也不改变模型身份。

非阻塞展示提醒：`exact_budget_less_kv_more_ffn`这个内部名称只在默认128等兼容alignment下严格等参；alignment1024时其实际FFN会变成13312，`exact_equal_parameters=false`及非零delta已正确输出。公共报告应使用这两个实际字段判断等参，不能把名称直接翻译成所有输入都“严格等参”。

## TP、状态、工作

独立逐rank矩阵尺寸枚举检查norm复制及词表/FFN/Q/K完整轴切分，非使用总参数除TP。全变体家族只有TP1/2满足共同完整头约束；TP3/4/8/16明确拒绝，不能把此例宣传为支持任意8卡架构。拒绝原因已声明为本比较不提供KV复制回退，不暗示这些架构不能部署。

三个请求形状分别decode、带history多token、prefill，共18个变体检查矩阵闭式与实际因果对枚举。权重复制/每rankKV、历史与新增状态均匹配。max_equal_length_requests基于单请求KV和固定per-rank workspace，正确独立于当前batch；batch_fits再以batch比较。它不是吞吐上界或计算所得完整workspace。

## 切换点

每个变体与baseline的声明存活预算分别a,b：只有较小者可容纳的整数容量区间为 `[min(a,b),max(a,b)-1]`。独立检查每区间起点前1、起点、终点、终点后1，满足0/1/1/2种结构可容纳。未把负headroom或“0请求”当装得下。

ring每rank发送线字节为 `2(TP−1)/TP × (B×tokens×H×2) × (2L)`；这里wire定义是发送字节，不能再把收发双向相加后保持同一带宽分母。TP1明确零调用和零线字节。独立以两个精确R、a值验证直接相减和`Δbytes/R+ΔN×a`一致。该式只属于每层两次output allreduce子路径，不是完整请求临界时间或质量胜负。

## 身份与集成边界

baseline来自固定公开Qwen3-8B。变体明确未训练，不保证原checkpoint可加载、相同输出或质量。公开报告须继续展示signed parameter delta/exact flag、TP限制、固定workspace、未含embedding/head通信及重叠边界。

候选7项原测试重跑通过。公共迁移测试需将研究目录动态import改成正常topic import；作者README已指出这一迁移步骤。CLI/report尚不是本候选已实现功能，不把研究测试通过说成公共再生通过。

运行：`PYTHONDONTWRITEBYTECODE=1 python3 calculations/research/architecture-variants-independent/check.py`。独立检查42对齐项、18请求变体及全部对应容量/ring边界；results.json绑定源SHA，SHA身份与语义核算分开。
