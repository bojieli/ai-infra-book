"""QK -> materialized causal softmax -> PV, with explicit handoff paths.

Uses Qwen3 head width; this is a declared dense materialization schedule,
not a claimed implementation of FlashAttention or any vendor's direct path.
"""
from pathlib import Path
import sys,json,argparse
PROJECT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(PROJECT/'src'))
from infra_calc.sources import model_config,provenance
from infra_calc.units import positive_int
from infra_calc.topics.request_dag import schedule


def calculate(length=128,group_rows=32,slots=2,path='staged',matrix_flops_per_tick=8192,
              scalar_ops_per_tick=128,exp_ops_per_tick=16,div_ops_per_tick=16,
              comparison_ops_per_tick=128,link_bytes_per_tick=128,capacity_bytes=98304):
    args=locals().copy()
    for name,value in args.items():
        if name!='path':positive_int(value,name)
    if path not in ('staged','direct'):raise ValueError('Choose staged or direct path')
    c=model_config('qwen3-8b');d=c['head_dim']
    if length>c['max_position_embeddings'] or length%group_rows:
        raise ValueError('Aligned complete row groups within official context required')
    groups=length//group_rows
    score_bytes=4*group_rows*length;probability_bytes=2*group_rows*length
    slot_bytes=score_bytes+probability_bytes
    tasks=[];work=[]
    ceil=lambda n,r:(n+r-1)//r
    def add(name,duration,deps,resource):
        tasks.append(dict(id=name,duration_ns=duration,deps=deps,resource=resource))
    hops=2 if path=='staged' else 1
    for i in range(groups):
        prefix=f'g{i}'
        qk=2*group_rows*length*d
        scalar=3*group_rows*length-group_rows # scale, subtract, sum
        comparisons=group_rows*(length-1)
        exp=division=group_rows*length
        masked=sum(length-row-1 for row in range(i*group_rows,(i+1)*group_rows))
        # Complete each row's entire K contraction before publishing its scores.
        deps=[f'g{i-slots}.pv'] if i>=slots else []
        if i:deps.append(f'g{i-1}.qk')
        add(prefix+'.qk',ceil(qk,matrix_flops_per_tick),deps,'matrix')
        add(prefix+'.scores',ceil(hops*score_bytes,link_bytes_per_tick),[prefix+'.qk'],'handoff')
        # One declared vector server serially performs these classes. No shared
        # resource throughput is counted twice as independent parallel supply.
        vector=(ceil(scalar,scalar_ops_per_tick)+ceil(comparisons,comparison_ops_per_tick)
                +ceil(exp,exp_ops_per_tick)+ceil(division,div_ops_per_tick))
        add(prefix+'.softmax',vector,[prefix+'.scores'],'vector')
        add(prefix+'.probabilities',ceil(hops*probability_bytes,link_bytes_per_tick),[prefix+'.softmax'],'handoff')
        add(prefix+'.pv',ceil(qk,matrix_flops_per_tick),[prefix+'.probabilities'],'matrix')
        work.append(dict(group=i,row_start=i*group_rows,row_count=group_rows,
                         QK_shapes=[[group_rows,d],[d,length]],PV_shapes=[[group_rows,length],[length,d]],
                         qk_flops=qk,pv_flops=qk,basic_scalar_ops=scalar,
                         maximum_comparisons=comparisons,exponential_ops=exp,division_ops=division,
                         masked_score_elements=masked,score_handoff_bytes=score_bytes,
                         probability_handoff_bytes=probability_bytes,
                         served_handoff_bytes=hops*(score_bytes+probability_bytes)))
    raw=schedule(tasks)
    timeline=[{k.replace('_ns','_tick') if k in ('start_ns','end_ns') else ('duration_ticks' if k=='duration_ns' else k):v for k,v in t.items()} for t in raw['tasks']]
    by_id={t['id']:t for t in timeline}
    ownership=[dict(group=i,slot=i%slots,start_tick=by_id[f'g{i}.qk']['start_tick'],
                    release_tick=by_id[f'g{i}.pv']['end_tick']) for i in range(groups)]
    fits=slots*slot_bytes<=capacity_bytes
    return dict(calculation='qwen-matrix-vector-handoff',model='qwen3-8b',scenario=args,sources=provenance('qwen3-8b'),
                work=work,timeline=timeline,slot_ownership=ownership,
                summary=dict(groups=groups,fp32_score_bytes_per_slot=score_bytes,
                             bf16_probability_bytes_per_slot=probability_bytes,
                             reserved_handoff_bytes=slots*slot_bytes,passes_declared_handoff_capacity=fits,
                             total_matrix_flops=sum(w['qk_flops']+w['pv_flops'] for w in work),
                             crossing_payload_bytes=groups*(score_bytes+probability_bytes),
                             served_handoff_bytes=hops*groups*(score_bytes+probability_bytes),
                             finish_tick=raw['finish_ns'],capacity_qualified_finish_tick=raw['finish_ns'] if fits else None,
                             first_vector_start_tick=min(t['start_tick'] for t in timeline if t['resource']=='vector'),
                             measured_kernel_seconds=None,actual_instruction_count=None),
                assumptions=['One head, full causal score matrix materialized. Dense GEMMs include masked upper-triangle entries; softmax scale/subtract/exp/divide runs on the full rectangle, with masked values set to -infinity.',
                             'Each row group includes the complete key extent and head-dimension contraction. A K-partial accumulator is never published to softmax; row splitting alone permits earlier vector work.',
                             'Mask predicate creation and score-mask writes, final output store, operand loading, layout conversion and control instructions are excluded; this is a compute/handoff subaccount, not a complete attention forward.',
                             'FP32 scores and BF16 probabilities are separately reserved within each slot; the slot is acquired before QK and released only after PV. Other accumulators/inputs/workspaces are outside this declared capacity.',
                             'Staged path serves a write and a read for each crossing payload through one shared handoff server; direct path serves one transfer on that server. These are abstract path assumptions, not asserted NVIDIA/Ascend/Apple implementations.',
                             'All rates are declared work per teaching tick, not official hardware peak or measured effective service. Vector classes execute serially on one resource; QK and PV share one matrix server.',
                             'Scheduler uses earliest-ready nonpreemptive tasks with stable list order, including finite-slot release dependencies; reported ordering is one declared schedule, not a globally optimal scheduler.',
                             'Output probabilities are cast to BF16 as a declared representation; cast work and quality impact are not claimed absent or measured.'])


def cases():
    return {f'{path}-rows{rows}-slots{slots}':calculate(group_rows=rows,slots=slots,path=path)
            for path in ('staged','direct') for rows,slots in [(128,1),(32,1),(32,2),(32,4)]}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.write_text(json.dumps(cases(),indent=2)+'\n')
