已完成这次有界真实测量，产物保存在 [README](/Users/boj/book/ai-infra-book/experiments/ch12/12-03/README.md)，独占 [status](/Users/boj/book/ai-infra-book/experiments/parallel-workers/vision/status.md) 已更新。指定远端归档的 **66 个文件、37,111,092 B** 已通过 manifest 校验，不含模型权重。

- 固定既有 Qwen3-VL-8B-Instruct snapshot，完整加载并逐项核验 **351 个视觉权重 key、576,388,336 个参数**。
- 官方 processor 与真实 CPU BF16 视觉编码成功，保存最终投影、**三组 DeepStack**、grid、processor 张量和完整视觉返回。
- 独立发送/接收进程完成 **8 次真实 TCP 交付**，形状、dtype、字节 hash 全部一致；原图传输后重编码与 EC 直接传输一致。
- 重复原图命中缓存；同尺寸内容变化正确失效。三个正式进程均退出 0，采样聚合峰值 RSS 约 **4.05 GiB**。
- 首轮 meta buffer 导致的真实失败完整保留；改用官方普通 CPU 构造后成功，没有修改模型源码或用随机参数替代缺失权重。

README 已包含简洁正文候选、计时边界与复跑说明。**完整语言答案、语言 KV 迁移、物理功耗、真实跨设备/WAN 和任务质量仍未执行，不宣称全 12-3 完成。** 全程未使用 GPU/MPS、修改共享环境、操作既有服务或接触 calculations 工作。