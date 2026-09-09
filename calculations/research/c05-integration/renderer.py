"""Copy ub_scope_markdown into report.py; dispatch before generic summary access."""
from fractions import Fraction
import json


def ub_scope_markdown(result):
    lines=['# UB 协作范围：当代 Qwen 教学计算','',
           '此结果是声明容量与串行通信路径预算，不是历史UB负载复原或端到端性能预测。','',
           '输入：`'+json.dumps(result['scenario'],ensure_ascii=False,sort_keys=True)+'`','',
           '| 候选 | 每机卡数×服务器 | 末步KV位置 | 最大逐卡bytes | 全卡容量通过 | 通信预算每前向ms | 全部前向ms |',
           '|---|---|---:|---:|---|---:|---:|']
    for c in result['scope_candidates']:
        s=c['summary'];lines.append(f"| {c['name']} | {c['cards_per_server']}×{c['servers']} | {s['final_cache_positions']} | {s['maximum_card_resident_bytes']} | {s['all_cards_fit']} | {float(Fraction(s['serial_communication_seconds_per_forward_exact']))*1000:.9f} | {float(Fraction(s['serial_communication_seconds_all_forwards_exact']))*1000:.9f} |")
    lines+=['','## 容量先于选择','',
            '比较标签只针对通信；任何逐卡容量不通过的候选不得据此选择。工作区是声明预留，尚非完整运行时峰值。','',
            '| 量 | 精确值 |','|---|---|']
    for k,v in result['scope_crossover'].items():lines.append(f'| {k} | `{v}` |')
    for c in result['scope_candidates']:
        lines+=['',f"## {c['name']}：逐卡与循环",'',
                '| server/card | PP/TP | 权重bytes | KV bytes | workspace bytes | resident bytes | fit |',
                '|---|---|---:|---:|---:|---:|---|']
        for d in c['placement_cards']:
            lines.append(f"| {d['server']}/{d['physical_card']} | {d['stage']}/{d['tp_rank']} | {d['weight_bytes']} | {d['kv_bytes']} | {d['workspace_bytes']} | {d['resident_bytes']} | {d['fits_declared_budget']} |")
        lines+=['','| 操作 | 层/阶段 | 服务接口 | 前向次数 | 每次启动轮 | 每次计费bytes | 所有前向秒（精确） |',
                '|---|---|---|---:|---:|---:|---|']
        for o in c['handoff_operations']:
            lines.append(f"| {o['name']} | {o['layer']}/{o['stage']} | {o['interface']} | {o['forward_evaluations']} | {o['startup_rounds_per_forward']} | {o['charged_resource_bytes_per_forward']} | {o['modeled_seconds_all_forwards_exact']} |")
    lines+=['','## 条件与来源','']+[f'- {s}' for s in result['assumptions']]
    lines+=['','历史材料仅证明时间线：']+[f"- [{s['file']}]({s['url']}) SHA-256 `{s['sha256']}`" for s in result['historical_sources']]
    lines+=['','模型固定来源：']+[f"- [{s['file']}]({s['url']}) SHA-256 `{s['sha256']}`" for s in result['sources']]
    return '\n'.join(lines)+'\n'
