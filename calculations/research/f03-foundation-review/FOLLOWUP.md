# F03 五文件合入后有限复查

`Path`归一化`./`和重复斜线，但当前代码比较原字符串与`as_posix()`，所以当前POSIX项目中的非规范路径会被拒绝，无需修改。

实际剩余反例是manifest只列README即可通过。最小增量 `manifest-completeness.patch` 只要求reproduce无条件生成的四个core文件：README、hardware.md、hardware-audit.json、hardware-audit.md。保留已有非空/唯一/规范路径/合法SHA及逐产物哈希验证；不使用目录glob作为产物清单。

这是对公共清单结构的F03验收，不是所有章节/场景产物覆盖的证明，后者另行审查。显式artifacts数组是当前reproduce拥有的产物集合。合法删除一个scene后，reproduce会从空artifacts列表重新收集剩余场景输出并重写manifest，但旧场景文件可能仍在目录；这些未被新manifest引用的旧文件不应使新结果验证失败，也不要求用户手动清理。

公共测试已规范格式。清单回归先验证含旧场景的5项清单，再模拟删除scene后重建的4项core清单，旧场景文件留在磁盘仍通过；README-only、空清单、重复项、错误路径/哈希、已列文件损坏都拒绝。这一小型回归直接验证reproduce的显式ownership协议，没有宣称再次执行全部章节复现。当前16项隔离契约回归全部通过。

`manifest-completeness-guard.json`给出当前共享reproduce.py的before与增量after SHA。共享源码未修改。对PLAN F03其他契约复查未发现新的实际必阻断反例；单位/形状/逻辑读写记录、数值输出、配置来源、CLI、离线哈希和受限重取维持已验收候选边界。主线完成core-only增量与全量复现后可进入F03正式验收，不扩大到未实现模型/全部运行时/全书计算覆盖。
