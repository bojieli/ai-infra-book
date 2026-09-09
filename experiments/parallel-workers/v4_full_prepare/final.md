完整 V4 实验已经完成实际运行；最终交付见 [实验 README](/Users/boj/book/ai-infra-book/experiments/ch02/02-05/full-model-run/README.md) 和 [交接说明](HANDOFF.md)。

最终只保留 `cpu110-bias-alias-004`：43原层、48分片、8题正常结束且答案精确匹配，653文件封存并完成两端核验。使用110GiB CPU offload及私有 bias 别名适配；配置、资源实测和复现方式以实验目录为准。M8严格数值门槛尚未放行，不作广义质量结论。

本目录原准备阶段的验证记录仅作准备证据。旧启动指令已移除，被成功结果替代的调试事件已清理，正式科学负结果完整保留。
