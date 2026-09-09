"""Recount real vLLM block snapshots, preemption and cancellation release."""
import hashlib
import json
from ..paths import PROJECT
from ..sources import provenance
from .state import calculate as state_calculate


def read_records():
    records={};sources=[]
    for entry in json.loads((PROJECT/'configs/kv-traces.lock.json').read_text())['files']:
        path=PROJECT/entry['file'];raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=entry['sha256']:raise ValueError('KV trace hash mismatch')
        name=entry['file'].split('sources/kv-traces/')[1]
        if path.suffix=='.jsonl':records[name]=[json.loads(line) for line in raw.decode().splitlines()]
        elif path.suffix=='.json':records[name]=json.loads(raw)
        sources.append(dict(file=entry['file'],url='../../'+entry['origin'],sha256=entry['sha256']))
    return records,sources


def recount(blocks,per_token):
    first=blocks[0];reserved=first['total_blocks']-first['free_blocks']
    if reserved!=1:raise ValueError('Expected one reserved null block')
    rows=[];previous={};preemptions=[];scheduled=0
    for index,snapshot in enumerate(blocks):
        owned={};counts={}
        if snapshot['total_blocks']!=first['total_blocks'] or snapshot['block_size']!=16:
            raise ValueError('Pool geometry changed')
        for request in snapshot['requests']:
            if len(request['blocks'])!=1:raise ValueError('Expected one KV block group')
            ids=[]
            for block in request['blocks'][0]:
                if block['id'] in owned or block['refs']!=1:raise ValueError('Unexpected sharing or duplicate block')
                if not 0<=block['id']<first['total_blocks']:raise ValueError('Block outside pool')
                owned[block['id']]=request['id'];ids.append(block['id'])
            counts[request['id']]=len(ids)
            if request['status']=='PREEMPTED' and previous.get(request['id'])!='PREEMPTED':
                if request['computed']!=0 or ids:raise ValueError('Preemption did not reset computed state')
                preemptions.append(dict(time_s=snapshot['time_s'],id=request['id'],preserved_output_tokens=request['output_tokens']))
        if snapshot['free_blocks']+len(owned)+reserved!=first['total_blocks']:
            raise ValueError('Block pool conservation failed')
        if snapshot['event']=='schedule':scheduled+=sum(snapshot['scheduled_tokens'].values())
        previous={request['id']:request['status'] for request in snapshot['requests']}
        rows.append(dict(snapshot=index,time_s=snapshot['time_s'],event=snapshot['event'],
                         free_blocks=snapshot['free_blocks'],request_blocks=len(owned),
                         request_block_counts=counts,request_payload_capacity_bytes=len(owned)*16*per_token))
    if blocks[-1]['requests'] or blocks[-1]['free_blocks']!=first['free_blocks']:
        raise ValueError('Request blocks not fully returned')
    return dict(total_blocks=first['total_blocks'],reserved_blocks=reserved,
                block_bytes=16*per_token,peak_request_blocks=max(row['request_blocks'] for row in rows),
                scheduled_token_positions=scheduled,preemptions=preemptions,timeline=rows,
                all_request_blocks_released=True)


def calculate(run='small'):
    if run not in ('small','large','cancel'):raise ValueError('Unknown recorded run')
    records,sources=read_records()
    state=state_calculate('qwen3-8b',length=1);per_token=state['summary']['kv_bytes_per_token_per_request']
    results={};outputs={};configs={}
    for name in ('small','large','cancel'):
        prefix='results/'+name+'/'
        env=records[prefix+'environment.json'];config=env['config'];configs[name]=config
        if (config['dtype']!='bfloat16' or config['enable_prefix_caching'] or
            not config['model'].endswith('b968826d9c46dd6066d109eabc6255188de91218')):
            raise ValueError('Recorded model revision, dtype or APC differs')
        results[name]=recount(records[prefix+'blocks.jsonl'],per_token)
        if results[name]['total_blocks']!=config['kv_cache_memory_bytes']//(16*per_token):
            raise ValueError('Official KV geometry disagrees with pool size')
        requests=records[prefix+'requests.jsonl']
        outputs[name]={row['id']:row['output_ids'] for row in requests}
        if len(outputs[name])!=4:raise ValueError('Expected four requests')
        results[name]['output_token_counts']={key:len(value) for key,value in outputs[name].items()}
    if dict(configs['small'],kv_cache_memory_bytes=2*1024**3)!=configs['large'] or configs['small']!=configs['cancel']:
        raise ValueError('Unexpected configuration differences')
    blocks=records['results/cancel/blocks.jsonl'];actions=records['results/cancel/actions.jsonl']
    if len(actions)!=1:raise ValueError('Expected one cancellation action')
    before=next(row for row in blocks if row['event']=='finish_before' and row.get('finish_ids'))
    after=next(row for row in blocks if row['event']=='finish_after' and row.get('finish_ids'))
    released=after['free_blocks']-before['free_blocks']
    cancelled=set(before['finish_ids'])
    expected=sum(len(q['blocks'][0]) for q in before['requests'] if q['id'] in cancelled)
    if released!=expected or any(q['id'] in cancelled for q in after['requests']):
        raise ValueError('Cancel release mismatch')
    cancel=dict(released_blocks=released,released_payload_capacity_bytes=released*16*per_token,
                api_returned_s=actions[0]['returned_s'],release_observed_s=after['time_s'],
                return_to_observed_release_s=after['time_s']-actions[0]['returned_s'])
    comparison=dict(small_large_outputs_match=outputs['small']==outputs['large'],
                    cancel_survivors_match=all(outputs['cancel'][key]==outputs['large'][key] for key in ('r0','r1','r2')),
                    extra_scheduled_positions=results['small']['scheduled_token_positions']-results['large']['scheduled_token_positions'])
    selected=results[run]
    return dict(schema_version=1,calculation='kv-trace',scenario=dict(run=run),
                sources=provenance('qwen3-8b')+sources,kv_trace_timeline=selected['timeline'],
                kv_trace_runs={name:{key:value for key,value in result.items() if key!='timeline'} for name,result in results.items()},
                cancellation=cancel,comparison=comparison,
                summary=dict(run=run,total_blocks=selected['total_blocks'],reserved_blocks=selected['reserved_blocks'],
                             block_bytes=selected['block_bytes'],peak_request_blocks=selected['peak_request_blocks'],
                             peak_request_payload_capacity_bytes=selected['peak_request_blocks']*selected['block_bytes'],
                             snapshots=len(selected['timeline']),preemption_count=len(selected['preemptions']),
                             scheduled_token_positions=selected['scheduled_token_positions'],
                             extra_small_run_scheduled_positions=comparison['extra_scheduled_positions'],
                             cancel_released_blocks=released,cancel_release_after_return_s=cancel['return_to_observed_release_s'],
                             all_request_blocks_released=True,**{k:v for k,v in comparison.items() if k!='extra_scheduled_positions'}),
                assumptions=[
                    '实验8-3真实RTX PRO 6000／vLLM0.23.0／Qwen3-8B BF16固定revision，四条1536-token输入、强制512输出，APC关闭、eager、同步调度，设备有其它服务。每条件单次新引擎，不是统计性能结论。',
                    '原始21文件封存SHA校验，官方KV几何每token144KiB、16-token块2.25MiB；池包含一个null保留块，不属于请求。APC关闭时逐快照核对free+owned+reserved=total、块不重复、引用为1。',
                    '记录调度token位置与输出token分别计量。抢占保留输出历史、computed清零并归还块；small相对large多调度位置不能叫额外输出，也不能按相同成本位置直接变成FLOPs或时间。',
                    '取消API返回与scheduler finish_after观察时刻分开，释放按前后空闲差与被取消请求拥有块核对；观察有同步trace开销，时间不代表无观测实现的精确取消延迟。',
                    '块容量不等于全部有效KV字节，尾块可能未满。本模型不从瞬间tokens字段推断执行完成的KV长度；APC共享、缓存空闲块与copy-on-write未在此实验中测量。',
                ])
