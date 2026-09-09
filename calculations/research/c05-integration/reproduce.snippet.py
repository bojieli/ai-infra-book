# Add ub_scope to .topics imports in reproduce.py.
# Add the following to input_hashes()'s paths list, matching existing external historical locks:
# *(PROJECT / row['file'] for row in json.loads((PROJECT / 'configs/ub-scope.lock.json').read_text())),
# In run(), after save() has been declared:
ub_rows = []
for row in scenarios.get('ub_scope', []):
    result = ub_scope.calculate(**{key:value for key,value in row.items() if key != 'id'})
    save(row['id'], result)
    ub_rows.append((row['id'], result))
# In generated results/README.md construction:
lines.extend(['', 'UB 协作范围：当代 Qwen 教学载荷，非历史参数复原；容量与串行通信预算分列。', '',
              '| 场景 | 单机TP8容量通过 | 双机TP4×PP2容量通过 | 仅通信偏好 |', '|---|---|---|---|'])
for name, result in ub_rows:
    a,b=result['scope_candidates']
    lines.append(f"| [{name}]({name}.md) | {a['summary']['all_cards_fit']} | {b['summary']['all_cards_fit']} | {result['scope_crossover']['communication_only_preference']} |")
# Add 'ub_scope_scenarios': len(ub_rows) to run() return counts.
# No CSV is needed for a matrix-operator table: this module's complete messages/cards
# are already in JSON and the dedicated Markdown renderer. Do not label messages FLOPs.
