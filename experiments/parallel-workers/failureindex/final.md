已交付审查清单：

- [candidates.json](/Users/boj/book/ai-infra-book/experiments/parallel-workers/failureindex/candidates.json)：25 组、93 个精确文件，包含失败证据、最终成功替代记录，以及 README、analyzer、manifest 的联动项。
- [final.md](/Users/boj/book/ai-infra-book/experiments/parallel-workers/failureindex/final.md)：逐组审查说明及必须保留／暂缓清理的记录。

重点确认了 08-05 的三次启动/预热失败、10-01 的缺包与编译配置失败、12-03 的 meta buffer 初始化失败。成功安装日志、数值不匹配、质量失败、故障注入及含有效请求的混合批次未列为删除候选。

仅写入上述两个文件，未删除或修改其他文件，未运行模型、测试或实验分析器；已排除指定目录，未读写 calculations。这是供主 agent 按成功依据清理的交接清单，不代表全部实验完成。