# 3-3：关闭 thinking 的诊断协议（GPU 尚未运行）

先前 thinking 开启的 1024 与 4096 总输出预算两批均未产生合规最终答案。本批在看到这些结果后追加，关闭 thinking，仍保留每候选 4096 总输出上限。它同时改变聊天模板和解析：模板使用 enable_thinking=False，输出全段必须直接是仅含整数 count 字段的 JSON；不要求生成 </think>，不从思考文本或代码围栏中提取答案。因此不是仅改 token 预算的对照，也不是盲测。

四题、两轮、三策略、24 组 44 个候选，任务内容及独立枚举/动态规划真值交叉核对与 wide-budget 一致。APC 关闭、同 Qwen3-8B BF16、eager、2 序列、512 chunk、6 GiB KV、engine seed303；temperature .6、top_p .95、每候选seed30300+trial*10+index；顺序 seed303 不变。serial 两个独立候选，parallel 同引擎两个并发，adaptive 元素数≤8 一个、其余串行两个；它是固定长度规则，不使用生成后答案或真值调整预算。

严格有效整数答案多数投票，平票选先出现的候选。真值只用于最终评分，不挑候选、不补跑失败、不提前终止。全部输出 IDs、原文、消息、输入 IDs、停止原因、逐步交付事件、缓存和验证/选择/评分时间保留。额外保存实际 tokenizer 的 think/EOS ID，离线按显式标记分区输出；意外出现思考标记仍保留，严格 JSON 解析不能因此剥离它。未知真实语义不由文本猜测。

原 sealed 数据不修改。baseline.json 保存原 run/tasks 哈希及本批准备后的源码哈希。当前未执行；须由主 agent 或 remaining_execution 明确确认第 9-10 项释放 GPU 后才能启动。无独立 RTX 性能实验并发；不结束已有 GPU 服务，不操作 calculations。

执行目录须没有 results；远端使用 /home/ubuntu/vllm023-venv/bin/python run.py --model /home/ubuntu/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218，并保存完整 run.log 与退出状态。运行后 python3 analyze.py、Matplotlib 环境 python plot.py。实际正确任务数、输出 token、选择前验证耗时与总任务耗时均实报；无费用/能耗测量，不把低延迟错误结果当作成功任务收益。
