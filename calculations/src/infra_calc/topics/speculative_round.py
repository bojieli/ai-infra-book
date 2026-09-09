"""Observed accepted-length histogram, canonical KV rollback and round ledger."""
from fractions import Fraction
from ..models import forward
from ..schema import Scenario
from ..units import positive_int


def calculate(model='qwen3-8b',history=1024,draft_tokens=4,accepted_counts=None,
              draft_ns=40000,verify_ns=100000,commit_ns=10000,
              baseline_token_ns=50000,remaining_output_tokens=None):
    inputs=locals().copy()
    for name,value in inputs.items():
        if name in ('model','accepted_counts','remaining_output_tokens'):continue
        positive_int(value,name,allow_zero=name in ('history','draft_ns','commit_ns'))
    if remaining_output_tokens is not None:positive_int(remaining_output_tokens,'remaining_output_tokens')
    counts=[2,1,1,2,4] if accepted_counts is None and draft_tokens==4 else accepted_counts
    if counts is None:raise ValueError('Explicit accepted_counts required for this draft length')
    if not isinstance(counts,list) or len(counts)!=draft_tokens+1:raise ValueError('Counts must cover accepted lengths 0..draft_tokens')
    for count in counts:positive_int(count,'count',allow_zero=True)
    if not sum(counts):raise ValueError('At least one observed round required')
    verification=forward(model,Scenario(tokens=draft_tokens+1,history=history,output_head='all'))
    per_token=verification['summary']['kv_bytes_per_token_per_request']
    round_time=draft_ns+verify_ns+commit_ns
    rows=[]
    for accepted,count in enumerate(counts):
        if not count:continue
        produced=accepted+1
        delivered=produced if remaining_output_tokens is None else min(produced,remaining_output_tokens)
        serial_work=sum(forward(model,Scenario(tokens=1,history=history+i,output_head='last'))['summary']['matrix_flops'] for i in range(delivered))
        rows.append(dict(accepted_drafts=accepted,count=count,produced_before_limit=produced,
                         delivered_tokens=delivered,clipped_tokens=produced-delivered,
                         baseline_matrix_flops=serial_work,baseline_ns=delivered*baseline_token_ns,
                         round_ns=round_time,
                         target_new_kv_kept_bytes=delivered*per_token,
                         target_new_kv_discarded_bytes=(draft_tokens+1-delivered)*per_token,
                         target_final_kv_bytes=(history+delivered)*per_token))
    rounds=sum(counts);accepted=sum(row['accepted_drafts']*row['count'] for row in rows)
    delivered=sum(row['delivered_tokens']*row['count'] for row in rows)
    total_time=rounds*round_time;baseline_time=delivered*baseline_token_ns
    inputs['accepted_counts']=counts
    return dict(schema_version=1,calculation='speculative-round',scenario=inputs,
                sources=verification['sources'],speculative_outcomes=rows,
                summary=dict(rounds=rounds,total_drafted_tokens=rounds*draft_tokens,
                             accepted_draft_tokens=accepted,
                             draft_acceptance_fraction_exact=str(Fraction(accepted,rounds*draft_tokens)),
                             mean_accepted_drafts_exact=str(Fraction(accepted,rounds)),
                             mean_delivered_tokens_exact=str(Fraction(delivered,rounds)),
                             delivered_tokens=delivered,total_speculative_ns=total_time,
                             matched_baseline_ns=baseline_time,
                             time_per_delivered_token_exact_ns=str(Fraction(total_time,delivered)),
                             unweighted_round_time_per_token_exact_ns=str(sum(Fraction(row['round_ns'],row['delivered_tokens'])*row['count'] for row in rows)/rounds),
                             matched_time_speedup_exact=str(Fraction(baseline_time,total_time)),
                             target_verify_rows=draft_tokens+1,
                             target_verify_matrix_flops_per_round=verification['summary']['matrix_flops'],
                             target_verify_matrix_flops_total=verification['summary']['matrix_flops']*rounds,
                             matched_serial_matrix_flops_total=sum(row['baseline_matrix_flops']*row['count'] for row in rows),
                             target_peak_kv_bytes=(history+draft_tokens+1)*per_token,
                             target_verify_new_kv_bytes=(draft_tokens+1)*per_token,
                             total_discarded_target_kv_bytes=sum(row['target_new_kv_discarded_bytes']*row['count'] for row in rows)),
                assumptions=[
                    '计量一个固定起点history的轮次分布，accepted_counts[a]是连续接受a个草稿的观察次数／教学次数，不由独立位置接受概率推断，也不是顺次增长历史的完整请求回放。',
                    '目标验证输入为一个待处理token加k个草稿，共k+1行，并为所有行计算logits。每轮产出a个接受草稿及一个补偿／额外token，尚未考虑EOS时为a+1；显式remaining_output_tokens只截断交付，验证工作仍已执行。',
                    '规范化回滚约定：起点history条已缓存，最后输出token待处理；提交m个新输出后只保留m条新增输入KV，最新输出仍待处理。验证分配k+1条，保留m条、丢弃k+1-m条。引擎可能采用其它预分配／提交布局，需另核。',
                    'baseline比较交付相同m个token的逐次目标decode，逐步增长history计算矩阵工作；验证块使用因果配对，不能把其工作当成m次单token简单相乘。',
                    'draft/verify/commit和baseline_token_ns均为独立教学时长，按串行相加；草稿模型形状／状态、运行时重叠与真实检查点不在本例。目标矩阵工作来自官方Qwen配置，不能从计数推出草稿准确率。',
                    '总体每token时间为总时间/总交付，不是各轮time/tokens等权平均；接受率只数草稿，平均交付包含额外token。这里验证收支，不实现拒绝采样或证明目标采样分布一致。',
                ])
