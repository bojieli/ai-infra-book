"""Sealed two-worker router replay: observed hits and official matrix accounting."""
import hashlib
import json
from statistics import median
from ..paths import PROJECT
from ..models import forward
from ..schema import Scenario

POLICIES=('round_robin','cache_aware','power_of_two')


def read_records():
    lock=json.loads((PROJECT/'configs/router-trace.lock.json').read_text())
    raw={}
    for entry in lock['files']:
        data=(PROJECT/entry['file']).read_bytes()
        if hashlib.sha256(data).hexdigest()!=entry['sha256']:raise ValueError('Router raw SHA mismatch')
        raw[entry['file'].split('sources/router-trace/',1)[1]]=data.decode()
    return raw,[dict(file=entry['file'],sha256=entry['sha256'],url='../../'+entry['origin']) for entry in lock['files']]


def calculate(policy='cache_aware'):
    if policy not in POLICIES:raise ValueError('Unknown archived router policy')
    raw,sources=read_records()
    execution=json.loads(raw['results/execution.json'])
    for name,sha in execution['source_hashes'].items():
        if hashlib.sha256(raw[name].encode()).hexdigest()!=sha:raise ValueError('Execution source mismatch')
    worker_commands=[cmd for cmd in execution['commands'] if 'sglang.launch_server' in cmd]
    if len(worker_commands)!=2:raise ValueError('Expected two workers')
    for cmd in worker_commands:
        if not cmd[cmd.index('--model-path')+1].endswith('b968826d9c46dd6066d109eabc6255188de91218') or cmd[cmd.index('--dtype')+1]!='bfloat16':
            raise ValueError('Unexpected worker model or precision')
    prompts=json.loads(raw['results/prompts.json'])
    requests=[json.loads(line) for line in raw['results/requests.jsonl'].splitlines()]
    if len(prompts)!=12 or len(requests)!=36:raise ValueError('Incomplete router record')
    locations={}
    for worker in range(2):
        for line in raw[f'results/worker{worker}-requests/ubuntu_0.log'].splitlines():
            if '{' not in line:continue
            record=json.loads(line[line.index('{'):])
            if record.get('event')=='request.received' and record['rid'].startswith('book909-'):
                if record['rid'] in locations:raise ValueError('Duplicate worker request identity')
                locations[record['rid']]=worker
    if set(locations)!={r['rid'] for r in requests}:raise ValueError('Worker identities do not match requests')
    totals=[];details={};outputs={}
    for name in POLICIES:
        registration=json.loads(raw[f'results/registration-{name}.jsonl'].splitlines()[-1])
        if len(registration['workers'])!=2 or not all(w['is_healthy'] for w in registration['workers']):
            raise ValueError('Workers not registered healthy')
        rows=[r for r in requests if r['policy']==name]
        if [r['prompt_id'] for r in rows]!=list(range(12)):raise ValueError('Unexpected replay order')
        history={0:[],1:[]};parsed=[];previous_end=None
        for row in rows:
            meta=row['response']['meta_info'];ids=prompts[row['prompt_id']]['input_ids']
            n=len(ids);hit=meta['cached_tokens'];worker=locations[row['rid']]
            if meta['id']!=row['rid'] or meta['prompt_tokens']!=n or meta['completion_tokens']!=1 or meta['num_retractions']!=0:
                raise ValueError('Request metadata mismatch')
            if not isinstance(hit,int) or not 0<=hit<n:raise ValueError('Invalid cached token count')
            if row['end_s']<row['start_s'] or (previous_end is not None and row['start_s']<previous_end):
                raise ValueError('Replay is not serial')
            previous_end=row['end_s']
            # An observed hit cannot exceed any previously completed local prefix.
            matches=[]
            for old in history[worker]:
                length=0
                for a,b in zip(old,ids):
                    if a!=b:break
                    length+=1
                matches.append(length)
            if hit>max(matches,default=0):raise ValueError('Hit exceeds completed same-worker prefix')
            history[worker].append(ids)
            cache_detail=meta['cached_tokens_details']
            if cache_detail is not None and (cache_detail['host']!=0 or cache_detail['device']!=hit):
                raise ValueError('Unexpected remote/host cache')
            full=forward('qwen3-8b',Scenario(tokens=n,output_head='last'))
            warm=forward('qwen3-8b',Scenario(tokens=n-hit,history=hit,output_head='last'))
            output=row['response']['output_ids']
            if len(output)!=1:raise ValueError('Expected one forced output token')
            outputs.setdefault(row['prompt_id'],[]).append(output)
            parsed.append(dict(prompt_id=row['prompt_id'],rid=row['rid'],worker=worker,
                               prompt_tokens=n,cached_tokens=hit,client_elapsed_s=row['end_s']-row['start_s'],
                               full_matrix_flops=full['summary']['matrix_flops'],
                               executed_logical_matrix_flops=warm['summary']['matrix_flops']))
        total=sum(r['prompt_tokens'] for r in parsed);hits=sum(r['cached_tokens'] for r in parsed)
        totals.append(dict(policy=name,requests=12,prompt_tokens=total,cached_tokens=hits,
                           token_weighted_hit_rate=hits/total,hit_requests=sum(r['cached_tokens']>0 for r in parsed),
                           client_median_s=median(r['client_elapsed_s'] for r in parsed),
                           replay_window_s=rows[-1]['end_s']-rows[0]['start_s'],
                           saved_matrix_flops=sum(r['full_matrix_flops']-r['executed_logical_matrix_flops'] for r in parsed)))
        details[name]=parsed
    if any(len(values)!=3 or values[0]!=values[1] or values[0]!=values[2] for values in outputs.values()):
        raise ValueError('Outputs differ across policies')
    return dict(schema_version=1,calculation='router-trace',scenario=dict(policy=policy),sources=sources+full['sources'],
                summary=next(r for r in totals if r['policy']==policy),router_policy_rows=totals,router_request_rows=details[policy],
                assumptions=[
                    '导入实验9-9正式run-v3封存36请求及两worker原生日志；失败v1/v2不计。每策略同12轮Agent输入，串行一轮、固定策略顺序，两个BF16 worker共用一GPU，非跨机扩展。',
                    '命中来自模型响应cached_tokens，去向来自worker request.received日志；已核对健康注册、prompt长度、同worker已完成前缀上界及三策略逐请求相同输出。未以router预计命中代替实际命中。',
                    '真实无host命中或远端KV，复算矩阵是官方Qwen逻辑工作，非实际HBM、tile、融合后issued FLOPs。命中前缀累计节省不是唯一驻留容量。',
                    '客户端end-start为完整单token请求耗时，不是独立引擎TTFT或远端取回时间。每策略12点、单轮与共享GPU不支持细微性能排名或生产SLO结论。',
                    '输入源为原始失败Agent轨迹，本次只重放输入，未重跑工具；强制一个输出token及相同输出不证明任务质量。实际部分prefill图仍被捕获，不能称为全程eager。',
                    '此记录没有事件缺口恢复或持续排队压力，不能据串行缓存亲和行为宣称缓存事件索引已得到验证。',
                ])
