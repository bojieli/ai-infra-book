"""Reuse archived natural Qwen8 trials; no invented second-model results."""
from pathlib import Path
from collections import Counter
import json,sys,hashlib
P=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(P/'src'))
from infra_calc.topics import kv_quality,trace_resource_bridge


def calculate():
    verified=kv_quality.calculate('bf16')
    data,_=kv_quality.read_records()
    tasks={x['id']:x for x in data['results/bf16/inputs.json']['tasks']}
    raw={x['id']:x for x in data['results/bf16/requests.jsonl']}
    calls=[];work={}
    for row in verified['kv_quality_requests']:
        if row['mode']!='natural':continue
        record=raw[row['id']];task=tasks[row['task_id']]
        correct=kv_quality.strict_answer(record['text'],task['expected'])
        if correct!=row['correct']:raise ValueError('Re-scoring differs')
        n=len(task['prompt_token_ids']);g=len(record['output_ids'])
        key=(n,g)
        if key not in work:
            # Deliberately logical cold-request policy, not observed cache events
            # or proof that the archived scheduler used these forward calls.
            work[key]=trace_resource_bridge.logical_call(0,n,g)
        ledger=work[key]
        calls.append(dict(request_id=row['id'],task_id=row['task_id'],trial=row['trial'],concurrency=row['concurrency'],correct=correct,
            input_tokens=n,returned_ids=g,recorded_latency_seconds=row['latency_s'],
            declared_cold_serial_matrix_flops=ledger['complete_logical_totals']['matrix_flops'],
            declared_final_kv_bytes=ledger['final_state_bytes'],observed_model_calls=None))
    counts=Counter(x['task_id'] for x in calls)
    return dict(calculation='paired-model-quality-baseline',model='qwen3-8b',sources=verified['sources'],distinct_tasks=len(counts),natural_executions=len(calls),correct_executions=sum(x['correct'] for x in calls),calls=calls,
        per_task=[dict(task_id=key,trials=counts[key],correct=sum(x['correct'] for x in calls if x['task_id']==key)) for key in sorted(counts)],
        paired_second_model=None,quality_equivalence=None,economic_winner=None,
        scope=['Existing eight retrieval tasks and natural-output runs only; calibration and forced-length timing excluded.',
               'Repeated/concurrent runs are not additional independent tasks. Full original scorer and provenance checks run before this export.',
               'Cold serial resource policy is explicit: no cached prefix, one prefill and G-1 decode calls; last returned ID has no extra KV append. Recorded latency is not derived from these FLOPs.',
               'A second model must run identical messages/scoring/budgets; tokenizer-specific IDs and lengths are recorded separately. No quality replacement or economic claim without paired evidence.'])

if __name__=='__main__':print(json.dumps(calculate(),indent=2))
