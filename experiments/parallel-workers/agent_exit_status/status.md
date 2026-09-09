已完成并封存：仅真实同服务 ABBA 工具退出语义子实验，待主agent独立复核。

42次真实HTTP请求，四次 baseline/proper-exit/proper-exit/baseline 分别12/12/9/9轮，六例2/2/6/6，finish否/否/是/是；两臂各一次合格、一次失败，不支持退出码改善质量结论。独立1013严格通过283/283/1013/1013，额外alias失败均0。16次非JSON严格拒绝，无length；全部正式结果保留，未追加或重跑。相同初始请求在干预之前已产生不同输出，不能忽略共享服务非确定性。

复用原RTX OpenRealtime服务，Qwen3-VL-30B-A3B-Instruct-FP8 revision d9748a51ae66354c4dad665aab2c71f26cf2c8cd，PID3613078/3614304运行前后一致；不启新GPU引擎、不reset APC、不改或停现有服务。模型阶段17.229603秒，本任务CPU树RSS采样峰值68,947,968 bytes，CPU8–11，正常退出无所属残留。服务显存只作背景、token IDs/内核调度时间/费用均不伪造。

交付 ../../ch11/11-09/exit-status/ 下 README.md、PROTOCOL.md、analysis.json、checks.json（663项通过）、manifest.json、standalone fixture/checker/controller、全部raw。远端同名目录 /home/ubuntu/ai-infra-book-experiments/ch11/11-09/exit-status/。

只写授权目录；未改calculations、正文、inventory、PROGRESS、共享模型/环境；未联系他人、提交git、扩展样本或宣布11-9/11-10整体完成。
