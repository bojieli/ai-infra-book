# cachebranch 状态：有界实验完成，待主agent统一复核回填

交付：[README](../../ch09/09-10/branch-observation/README.md)、[summary](../../ch09/09-10/branch-observation/summary.json)、[请求事件链](../../ch09/09-10/branch-observation/request-chains.json)、[首完成索引](../../ch09/09-10/branch-observation/REQUEST-EVIDENCE.md)。远端同名目录 /home/ubuntu/ai-infra-book-experiments/ch09/09-10/branch-observation。

4组18请求完成；全部输出ID及text精确等于固定参考。单请求两轮first native-0 cached1008；8请求波两轮first native-4 cached0。20325条真实事件完整保留。

实际分支：native-0..3通过rate检查，占用0/1024/2048/3072；native-4..7 occupied4096>=limit3289被限额。前四请求progress先False；native-4无ongoing，progress源码1361行直接True，pop0，真实prefill prefix/host/storage=0，首完成API id精确关联。actual host pool8208、device/runtime pool4096。预取前四请求后续completed1024、host matched1024、loaded0；不再推测所有树节点创建者。单请求completed1024/matched0/loaded1024，prefill有效host1008，API storage1008。

GPU严格等待主agent释放JSON后，独立核实2490395/2531457的/proc及GPU均无记录才启动。worker4个exit0、controller/launcher SSH exit0、下载上传exit0。采样峰值17290MiB<24576MiB。所有自有/proc PID最终不存在，GPU仅原五服务；四组cleanup为空。子进程无Python atexit记录，独立报告缺失，不声称子进程exit0；实际退出由/proc与显存释放证明。分析器额外atexit假设失败版本/原因保留，未复跑。

固定SG0.5.13.post1五份sources及前后hash一致；未改共享源码。模块顶层observer进入spawn，实际事件PID与安装/proc所有权对应。CPU检查exit0，仅作仪器校验。实际ServerInfo双字段4096、固定config逐项验证；原9-8输出ID另直接比较。77份原始结果本地/远端hash一致；最终manifest121文件71652376字节，本地远端verify_manifest均exit0，数据低于1GiB。图最终rsvg渲染目视QA通过，Quick Look裁切失败另保留。

仅写新branch-observation与本状态；旧封存实验、正文、inventory/PROGRESS/references/research未动，calculations不执行不改不复制；未联系session、未派生agent、未git提交。此结论仅本批受观察开销影响的固定条件路径，不作性能比较、跨session审计或全9-10完成声明。
