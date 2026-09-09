"""Archived Agent APC hits with official full/suffix matrix work accounting."""
import hashlib
import json
from fractions import Fraction
from statistics import median
from ..paths import PROJECT
from ..models import forward
from ..schema import Scenario
from ..sources import provenance


RUNS=('cache6','gap6','pressure1','pressure6','nocache6')


def read_records():
    records={};sources=[]
    for entry in json.loads((PROJECT/'configs/apc-traces.lock.json').read_text())['files']:
        path=PROJECT/entry['file'];raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=entry['sha256']:raise ValueError('APC trace hash mismatch')
        name=entry['file'].split('sources/apc-traces/')[1]
        if path.suffix=='.jsonl':records[name]=[json.loads(line) for line in raw.decode().splitlines()]
        elif path.suffix=='.json':records[name]=json.loads(raw)
        sources.append(dict(file=entry['file'],url='../../'+entry['origin'],sha256=entry['sha256']))
    return records,sources


def calculate(run='cache6'):
    if run not in RUNS:raise ValueError('Unknown APC run')
    records,sources=read_records();inputs=records['inputs/agent-prompts.json']['requests']
    outputs=[];pressure_inputs={}
    for name in RUNS:
        rows=records['results/'+name+'/requests.jsonl']
        env=records['results/'+name+'/environment.json'];config=env['config']
        if config['dtype']!='bfloat16' or not config['model'].endswith('b968826d9c46dd6066d109eabc6255188de91218'):
            raise ValueError('APC model mismatch')
        expected=dict(records['results/cache6/environment.json']['config'])
        if name=='pressure1':expected['kv_cache_memory_bytes']=1024**3
        if name=='nocache6':expected['enable_prefix_caching']=False
        if config!=expected or env['gap_s']!=(0.2 if name=='gap6' else 0):
            raise ValueError('Unexpected APC configuration or gap')
        if env['pressure_requests']!=(3 if name.startswith('pressure') else 0):
            raise ValueError('Unexpected interference count')
        agents=[row for row in rows if row['kind']=='agent']
        pressure=[row for row in rows if row['kind']=='pressure']
        if len(agents)!=len(inputs) or len(agents)!=12 or len(pressure)!=11*env['pressure_requests']:
            raise ValueError('Unexpected request counts')
        for row,inp in zip(agents,inputs):
            ids=inp['prompt_token_ids']
            if row['prompt_tokens']!=len(ids) or row['prompt_sha256']!=hashlib.sha256(json.dumps(ids).encode()).hexdigest():
                raise ValueError('Frozen prompt mismatch')
            if not 0<=row['cached_tokens']<row['prompt_tokens'] or len(row['output_ids'])!=1:
                raise ValueError('Expected nonempty suffix and one output token')
            if row['metrics']['is_corrupted']:raise ValueError('Corrupt engine result')
        if name=='nocache6' and any(row['cached_tokens'] for row in agents):
            raise ValueError('Disabled cache reported hits')
        outputs.append([row['output_ids'] for row in agents])
        pressure_inputs[name]=[(row['id'],row['prompt_sha256']) for row in pressure]
    if any(output!=outputs[0] for output in outputs) or pressure_inputs['pressure1']!=pressure_inputs['pressure6']:
        raise ValueError('Outputs or pressure inputs differ')
    raw=records['results/'+run+'/requests.jsonl'];rows=[]
    for request in (row for row in raw if row['kind']=='agent'):
        length=request['prompt_tokens'];cached=request['cached_tokens']
        full=forward('qwen3-8b',Scenario(tokens=length,output_head='last'))['summary']
        hit=forward('qwen3-8b',Scenario(tokens=length-cached,history=cached,output_head='last'))['summary']
        rows.append(dict(id=request['id'],prompt_tokens=length,cached_tokens=cached,
                         uncached_tokens=length-cached,full_matrix_flops=full['matrix_flops'],
                         hit_matrix_flops=hit['matrix_flops'],saved_matrix_flops=full['matrix_flops']-hit['matrix_flops'],
                         reused_kv_logical_bytes=cached*full['kv_bytes_per_token_per_request'],
                         delivery_ttft_s=request['delivery_ttft_s'],request_wall_s=request['end_s']-request['start_s']))
    total=sum(row['prompt_tokens'] for row in rows);cached=sum(row['cached_tokens'] for row in rows)
    full=sum(row['full_matrix_flops'] for row in rows);hit=sum(row['hit_matrix_flops'] for row in rows)
    agent_time=sum(row['request_wall_s'] for row in rows)
    pressure_time=sum(row['end_s']-row['start_s'] for row in raw if row['kind']=='pressure')
    elapsed=raw[-1]['end_s']-raw[0]['start_s']
    return dict(schema_version=1,calculation='apc-trace',scenario=dict(run=run),
                sources=provenance('qwen3-8b')+sources,apc_rounds=rows,
                summary=dict(agent_requests=len(rows),input_tokens=total,cached_tokens=cached,
                             requests_with_hit=sum(row['cached_tokens']>0 for row in rows),
                             request_hit_fraction_exact=str(Fraction(sum(row['cached_tokens']>0 for row in rows),len(rows))),
                             token_weighted_hit_fraction_exact=str(Fraction(cached,total)),
                             mean_per_request_cached_fraction_exact=str(sum(Fraction(row['cached_tokens'],row['prompt_tokens']) for row in rows)/len(rows)),
                             full_matrix_flops=full,hit_matrix_flops=hit,saved_matrix_flops=full-hit,
                             matrix_work_saved_fraction_exact=str(Fraction(full-hit,full)),
                             cumulative_reused_kv_logical_bytes=sum(row['reused_kv_logical_bytes'] for row in rows),
                             agent_request_wall_s=agent_time,pressure_request_wall_s=pressure_time,
                             replay_elapsed_s=elapsed,between_requests_s=elapsed-agent_time-pressure_time,
                             median_delivery_ttft_s=median(row['delivery_ttft_s'] for row in rows),
                             all_five_run_output_tokens_match=True,pressure_inputs_match=True),
                assumptions=[
                    '实验8-4固定12轮真实Agent输入，各轮仅生成一个token，不重跑工具或继续真实多token Agent任务。RTX共享GPU／vLLM0.23.0、Qwen3-8B BF16、eager、分块预算512、每条件单次串行回放。',
                    '命中数来自引擎记录，核对冻结prompt ID哈希、所有配置输出相同及两组干扰输入相同。请求命中率指cached>0的请求占比；token加权命中与每请求缓存比例平均分列。',
                    '矩阵工作为官方full前向减history=cached的suffix前向，保留suffix对命中历史的注意力与末token logits；数学工作不包括chunk额外启动、实际HBM和查找成本。命中工作节省不直接转换为实测加速。',
                    '累计复用KV逻辑字节按每轮相加，不是缓存驻留峰值或唯一物理页数。同一历史可能多轮重复命中，缺少块寿命记录不能推出容量占用时间。',
                    'Agent请求墙钟、干扰请求墙钟和整段回放时间分开；between_requests含显式间隔与主机开销，不能把整段时间都归因于Agent推理。',
                    '6GiB与1GiB干扰条件、0.2秒间隔及关闭APC分别对照；单次共享GPU回放不证明通用TTL、显著性能收益或混合排队效果。',
                ])
