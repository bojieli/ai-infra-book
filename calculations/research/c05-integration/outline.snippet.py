# Inside outline refresh, before the existing historical subsection 1.6.2:
ub = result('ub-scope-qwen32-default')
one,two = ub['scope_candidates']
insert('01-初识 AI Infra.md', 'C05-modern-scope',
       '[当代Qwen教学计算](../calculations/results/ub-scope-qwen32-default.md)用同一Qwen3-32B、8卡与32次decode前向比较单机TP8和双机TP4×PP2。'
       f"末步KV为{one['summary']['final_cache_positions']}位置，最大逐卡预算占用分别{one['summary']['maximum_card_resident_bytes']}与{two['summary']['maximum_card_resident_bytes']}bytes，工作区为显式预留。"
       '教学本地50GB/s、2μs启动，跨机25GB/s、5μs启动；双机每次跨机发送4份hidden加token反馈，共40964bytes、2次启动。'
       '声明串行通信预算分别3.68886936和1.61838368ms/前向；不是端到端耗时。'
       '[带宽相等边界](../calculations/results/ub-scope-remote-tie.md)约19.769MB/s；[双机刚好可放](../calculations/results/ub-scope-capacity-dual-only.md)仍须先排除容量失败的单机候选。'
       '运行 `python3 calculations/calc.py ub-scope --format md` 复现。Qwen配置与服务条件是当代教学输入，不属于UB创立时已知事实；作者回忆仅支撑早于2020转折的时间线，原C05的当年容量/交接/选择翻转仍需历史输入，保持未完成。',
       '### 1.6.2 需求转折与未确定的未来')
