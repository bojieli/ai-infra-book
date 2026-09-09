"""Deterministic iteration scheduler with official per-request matrix/KV work."""
from functools import lru_cache
from ..models import forward,qwen3
from ..sources import model_config,provenance
from ..schema import Scenario
from ..units import positive_int


POLICIES=('fixed','continuous','chunked')
DEFAULT_REQUESTS=[dict(id='r0',arrival_ns=0,prompt_tokens=16,output_tokens=8),
                  dict(id='r1',arrival_ns=0,prompt_tokens=16,output_tokens=2),
                  dict(id='r2',arrival_ns=20000,prompt_tokens=128,output_tokens=2),
                  dict(id='r3',arrival_ns=30000,prompt_tokens=16,output_tokens=4)]


def calculate(model='qwen3-8b',policy='chunked',requests=None,max_sequences=2,token_budget=32,
              chunk_tokens=16,step_base_ns=10000,per_new_token_ns=1000,per_causal_pair_ns=1,
              kv_capacity_bytes=None):
    if policy not in POLICIES:raise ValueError('Unknown batching policy')
    for name,value in [('max_sequences',max_sequences),('token_budget',token_budget),('chunk_tokens',chunk_tokens),
                       ('step_base_ns',step_base_ns),('per_new_token_ns',per_new_token_ns),('per_causal_pair_ns',per_causal_pair_ns)]:
        positive_int(value,name,allow_zero=name in ('per_new_token_ns','per_causal_pair_ns'))
    if token_budget<max_sequences:raise ValueError('Token budget must fit every possible decode request')
    if kv_capacity_bytes is not None:positive_int(kv_capacity_bytes,'kv_capacity_bytes')
    config=model_config(model);qwen3.validate(config)
    unit=4*config['num_hidden_layers']*config['num_key_value_heads']*config['head_dim']
    requests=DEFAULT_REQUESTS if requests is None else requests
    if not isinstance(requests,list) or not requests or len(requests)>64:raise ValueError('Supply 1..64 requests')
    rows=[]
    for request in requests:
        if set(request)!={'id','arrival_ns','prompt_tokens','output_tokens'}:raise ValueError('Unexpected request fields')
        if not isinstance(request['id'],str) or not request['id'] or any(r['id']==request['id'] for r in rows):raise ValueError('Duplicate or invalid request ID')
        for name in ('arrival_ns','prompt_tokens','output_tokens'):positive_int(request[name],name,allow_zero=name=='arrival_ns')
        tokens=request['prompt_tokens']+request['output_tokens']-1
        if tokens>config['max_position_embeddings']:raise ValueError('Request exceeds official context')
        reserve=tokens*unit
        if kv_capacity_bytes is not None and reserve>kv_capacity_bytes:raise ValueError('Request cannot fit KV capacity alone')
        rows.append(dict(**request,computed=0,delivered=0,reserved_bytes=reserve,admitted_ns=None,delivery_ns=[],matrix_flops=0))
    if sum(r['prompt_tokens']+r['output_tokens'] for r in rows)>65536:raise ValueError('Teaching replay limited to 65536 tokens')
    waiting=sorted(range(len(rows)),key=lambda i:(rows[i]['arrival_ns'],i));active=[]
    now=0;steps=[];peak=0;reserved_peak=0;area=0
    @lru_cache(maxsize=None)
    def work(history,tokens,head):
        return forward(model,Scenario(history=history,tokens=tokens,output_head=head))['summary']['matrix_flops']
    while waiting or active:
        if not active and waiting:now=max(now,rows[waiting[0]]['arrival_ns'])
        if policy!='fixed' or not active:
            while waiting and len(active)<max_sequences and rows[waiting[0]]['arrival_ns']<=now:
                i=waiting[0]
                reserve=sum(rows[j]['reserved_bytes'] for j in active)+rows[i]['reserved_bytes']
                if kv_capacity_bytes is not None and reserve>kv_capacity_bytes:break
                waiting.pop(0);active.append(i);rows[i]['admitted_ns']=now
        reserved_peak=max(reserved_peak,sum(rows[i]['reserved_bytes'] for i in active))
        plans=[];budget=token_budget
        # Existing decode requests go first; FIFO prefill takes remaining budget.
        ordered=sorted(active,key=lambda i:rows[i]['delivered']==0)
        for i in ordered:
            r=rows[i];prefill=r['delivered']==0
            new=r['prompt_tokens']-r['computed'] if prefill else 1
            if policy=='chunked':new=min(new,budget,chunk_tokens if prefill else 1)
            if not new:continue
            emits=not prefill or r['computed']+new==r['prompt_tokens']
            pairs=new*r['computed']+new*(new+1)//2
            flops=work(r['computed'],new,'last' if emits else 'none')
            plans.append(dict(request=r['id'],index=i,phase='prefill' if prefill else 'decode',
                              history_tokens=r['computed'],new_tokens=new,causal_pairs=pairs,
                              emits_token=emits,matrix_flops=flops))
            budget-=new
        if not plans:raise ValueError('Scheduler made no progress')
        tokens=sum(p['new_tokens'] for p in plans);pairs=sum(p['causal_pairs'] for p in plans)
        duration=step_base_ns+tokens*per_new_token_ns+pairs*per_causal_pair_ns
        live=(sum(rows[i]['computed'] for i in active)+tokens)*unit
        peak=max(peak,live);area+=live*duration
        if kv_capacity_bytes is not None and live>kv_capacity_bytes:raise ValueError('Live KV exceeded reservation')
        end=now+duration
        for p in plans:
            r=rows[p.pop('index')];r['computed']+=p['new_tokens'];r['matrix_flops']+=p['matrix_flops']
            if p['emits_token']:r['delivered']+=1;r['delivery_ns'].append(end)
        steps.append(dict(start_ns=now,end_ns=end,duration_ns=duration,new_tokens=tokens,
                          causal_pairs=pairs,live_kv_bytes_during_step=live,plans=plans))
        active=[i for i in active if rows[i]['delivered']<rows[i]['output_tokens']]
        now=end
    for r in rows:
        times=r['delivery_ns'];r['waiting_ns']=r['admitted_ns']-r['arrival_ns']
        r['ttft_ns']=times[0]-r['arrival_ns'];r['finish_ns']=times[-1]
        r['latency_ns']=times[-1]-r['arrival_ns'];r['max_itl_ns']=max((b-a for a,b in zip(times,times[1:])),default=None)
    return dict(schema_version=1,calculation='iteration-batching',scenario=dict(model=model,policy=policy,requests=requests,
                max_sequences=max_sequences,token_budget=token_budget,chunk_tokens=chunk_tokens,step_base_ns=step_base_ns,
                per_new_token_ns=per_new_token_ns,per_causal_pair_ns=per_causal_pair_ns,kv_capacity_bytes=kv_capacity_bytes),
                sources=provenance(model),batching_steps=steps,batching_requests=rows,
                summary=dict(requests=len(rows),iterations=len(steps),finish_ns=now,
                             total_output_tokens=sum(r['delivered'] for r in rows),
                             total_scheduled_tokens=sum(s['new_tokens'] for s in steps),
                             total_matrix_flops=sum(r['matrix_flops'] for r in rows),
                             peak_live_kv_bytes=peak,peak_reserved_kv_bytes=reserved_peak,live_kv_byte_ns=area,
                             max_waiting_ns=max(r['waiting_ns'] for r in rows),max_ttft_ns=max(r['ttft_ns'] for r in rows),
                             max_itl_ns=max((r['max_itl_ns'] for r in rows if r['max_itl_ns'] is not None),default=None)),
                assumptions=[
                    '同一教学请求流：固定批次只在整组退出后补位，连续批处理每个迭代边界补位，两者prefill一次处理完整prompt；chunked在相同连续补位上按decode优先、FIFO prefill分配token预算与单请求块上限。',
                    '只在迭代边界接纳已到达请求；固定批次不额外等待凑满。每个请求先完成prefill产生首输出，后续输出各消耗一个pending token。最新输出尚未写入KV，最终计算长度为prompt+output-1。',
                    '每步时长为base+new_tokens*per_new_token_ns+有效因果配对*per_causal_pair_ns，全部显式教学成本，跨请求相加后一次base；它不是实测拟合或硬件峰值预测。官方矩阵另计，非末prefill块不做输出头。',
                    'KV准入按声明最大输出长度预留，严格FIFO不绕过队首；逻辑KV按每步开始分配该步全部新增行、步末完成请求释放。只计KV池，不含权重、页碎片或工作区；无抢占、共享前缀或动态EOS。',
                    '时间戳是调度模型交付时刻，不模拟HTTP或流式聚合；相同输出数量不证明生成内容或质量一致。maxITL仅对至少两输出请求定义。',
                ])
