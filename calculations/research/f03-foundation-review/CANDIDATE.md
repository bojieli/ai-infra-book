# F03 可合入候选（共享文件未改）

合入入口为 `final-foundation.patch`，五文件分别为units/schema/sources/cli/reproduce。`merge-guards.json`提供每个共享原文件SHA、候选SHA及patchSHA，应用前逐项guard，应用后核候选SHA。新回归文件 `test_foundation_contract.py` 可复制到公共tests目录。

候选已在临时隔离计算包中验证：**15项独立契约回归、109项现有test_accounting全部通过**。新回归最后又单独运行，包含构造后修改Operator为NaN/负字节/bool的拒绝。日志分别为candidate-tests.log及existing-accounting-tests.log；未复制或下载权重，数据仅从已有路径只读。

Weight的每个驻留shape维度必须为正整数；标量空tuple仍表示一个参数。linear允许rows=0，拒绝负数/bool；Operator次数/工作/字节为非负整数，构造和record边界均校验，shapes保留零/符号/嵌套描述能力。大正整数不会因math.isfinite内部转float溢出而错误拒绝。

所有HTTP请求均以锁bytes+1为读取上限，校验实际长度和SHA。Range必须是固定起止，区间长度等于锁bytes；响应完整数值Content-Range匹配、total大于end。Content-Length可缺省，存在时必须是正确整数长度。错误响应不会替换旧文件；成功内容用同目录唯一临时文件原子替换，写入/替换失败清理临时文件。fetch帮助明确精确来源组、不自动扩张依赖。

CLI和reproduce的结果JSON拒绝NaN/Infinity。input_hashes加入calc.py；manifest要求非空、唯一、规范相对results路径、合法SHA及README索引，再逐产物验证内容哈希。没有宣称这种manifest可抵抗同时改写manifest与产物的攻击，也没有要求完成全部模型执行图。

主线合入并完成约定全量复现后再做F03最终验收；目前交付的是通过独立和现有基础回归的候选，不伪称公共部署已完成。
