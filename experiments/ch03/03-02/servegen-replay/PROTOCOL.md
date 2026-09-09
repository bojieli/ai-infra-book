# ServeGen实际回放预定方案

Two sequential120s cases: original ServeGen window337800 seed302 and permutation seed303 of intact input/output-length pairs over the exact same timestamps.480 each. Synthetic valid token adapter, unique leading token per task; no production content or prefix identity. Greedy forced output, APC off; open loop then drain. Fixed order is a limitation, not replicated performance evidence.

比较实际发送偏差、TTFT、初次排队、完成延迟、等待/KV采样和输出一致性。每个任务相同输入和强制输出长度，保留原始全部token和事件。不以一次固定顺序测量宣称稳定胜负，不用合成内容评价质量。协议在GPU执行前保存。
