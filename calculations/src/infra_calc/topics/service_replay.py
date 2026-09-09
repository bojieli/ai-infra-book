"""Actual AsyncLLM delivery replay and explicitly defined joint timing SLO."""
import hashlib
import json
from statistics import median
from math import ceil
from ..paths import PROJECT
from ..units import positive_number


RUNS=('chunk512','chunk8192','nochunk8192','graph512')


def read_records():
    records={};sources=[]
    for entry in json.loads((PROJECT/'configs/service-replay.lock.json').read_text())['files']:
        data=(PROJECT/entry['file']).read_bytes()
        if hashlib.sha256(data).hexdigest()!=entry['sha256']:raise ValueError('Service replay hash mismatch')
        name=entry['file'].split('sources/service-replay/')[1]
        if name.endswith('.json'):records[name]=json.loads(data)
        elif name.endswith('.jsonl'):records[name]=[json.loads(line) for line in data.decode().splitlines()]
        else:records[name]=data
        sources.append(dict(file=entry['file'],url='../../'+entry['origin'],sha256=entry['sha256']))
    return records,sources


def delivery_rows(events,inputs):
    specs={r['id']:r for r in inputs};groups={}
    if len(specs)!=6:raise ValueError('Expected six fixed request shapes')
    for e in events:groups.setdefault((e['trial'],e['id']),[]).append(e)
    if set(groups)!={(trial,rid) for trial in range(3) for rid in specs}:raise ValueError('Missing or extra replay requests')
    rows=[]
    for (trial,rid),group in sorted(groups.items()):
        spec=specs[rid];last=group[-1]
        if not last['finished'] or last['finish_reason']!='length':raise ValueError('Incomplete request')
        total=0;times=[];tokens=[];merged=0
        submitted=group[0]['submitted_s']
        for e in group:
            if e['submitted_s']!=submitted or e['scheduled_s']!=spec['arrival_s']:raise ValueError('Request time identity changed')
            total+=len(e['new_token_ids'])
            if total!=e['cumulative_tokens']:raise ValueError('Cumulative output mismatch')
            if e['new_token_ids']:
                times.append(e['delivered_s']);tokens.extend(e['new_token_ids']);merged+=len(e['new_token_ids'])>1
        if total!=spec['max_tokens'] or times!=sorted(times) or times[0]<submitted:raise ValueError('Output count or clock ordering mismatch')
        m=last['engine_request_metrics']
        if m['is_corrupted'] or m['num_generation_tokens']!=total or not 0<m['queued_ts']<=m['scheduled_ts']<=m['first_token_ts']<=m['last_token_ts']:
            raise ValueError('Invalid engine request metrics')
        rows.append(dict(trial=trial,id=rid,submitted_s=submitted,last_delivery_s=times[-1],
                         output_tokens=total,output_token_ids=tokens,multi_token_events=merged,
                         delivered_ttft_ms=1000*(times[0]-submitted),delivered_e2e_ms=1000*(times[-1]-submitted),
                         delivered_mean_tpot_ms=1000*(times[-1]-times[0])/(total-1) if total>1 else None,
                         max_delivery_event_gap_ms=max((1000*(b-a) for a,b in zip(times,times[1:])),default=None),
                         engine_queue_ms=1000*(m['scheduled_ts']-m['queued_ts']),
                         engine_mean_tpot_ms=1000*(m['last_token_ts']-m['first_token_ts'])/(total-1) if total>1 else None))
    return rows


def calculate(run='chunk512',ttft_limit_ms=300,e2e_limit_ms=2000,mean_tpot_limit_ms=20):
    if run not in RUNS:raise ValueError('Unknown replay condition')
    for name,value in [('ttft_limit_ms',ttft_limit_ms),('e2e_limit_ms',e2e_limit_ms),('mean_tpot_limit_ms',mean_tpot_limit_ms)]:positive_number(value,name)
    records,sources=read_records();all_rows={};baseline=records['results/measured-chunk512/environment.json'];request_hash=baseline['requests_sha256']
    for name in RUNS:
        prefix=f'results/measured-{name}/';env=records[prefix+'environment.json']
        if env['completed_trials']!=3 or env['vllm']!='0.23.0' or env['run_sha256']!=hashlib.sha256(records['run.py']).hexdigest():raise ValueError('Replay environment mismatch')
        payload=(PROJECT/'sources/service-replay'/prefix/'requests.json').read_bytes()
        if hashlib.sha256(payload).hexdigest()!=env['requests_sha256'] or env['requests_sha256']!=request_hash:raise ValueError('Replay input mismatch')
        if any(env[key]!=baseline[key] for key in ('torch','VLLM_USE_FLASHINFER_SAMPLER')):raise ValueError('Runtime or sampler changed')
        expected=dict(baseline['config'])
        if name in ('chunk8192','nochunk8192'):expected['max_num_batched_tokens']=8192
        if name=='nochunk8192':expected['enable_chunked_prefill']=False
        if name=='graph512':expected.update(enforce_eager=False,compilation_config={'mode':0,'cudagraph_mode':'FULL_DECODE_ONLY'})
        if env['config']!=expected:raise ValueError('Unexpected configuration difference')
        if expected['dtype']!='bfloat16' or not expected['model'].endswith('b968826d9c46dd6066d109eabc6255188de91218') or expected['enable_prefix_caching']:raise ValueError('Target model/cache mismatch')
        all_rows[name]=delivery_rows(records[prefix+'events.jsonl'],records[prefix+'requests.json'])
    identities=[(r['trial'],r['id'],r['output_token_ids']) for r in all_rows[RUNS[0]]]
    for rows in all_rows.values():
        if identities!=[(r['trial'],r['id'],r['output_token_ids']) for r in rows]:raise ValueError('Output token sequences differ across conditions')
    rows=all_rows[run];trials=[]
    for r in rows:
        r['ttft_pass']=r['delivered_ttft_ms']<=ttft_limit_ms
        r['e2e_pass']=r['delivered_e2e_ms']<=e2e_limit_ms
        r['mean_tpot_pass']=r['delivered_mean_tpot_ms'] is None or r['delivered_mean_tpot_ms']<=mean_tpot_limit_ms
        r['joint_timing_pass']=r['ttft_pass'] and r['e2e_pass'] and r['mean_tpot_pass']
    for trial in range(3):
        group=[r for r in rows if r['trial']==trial]
        window=max(r['last_delivery_s'] for r in group)-min(r['submitted_s'] for r in group)
        passed=sum(r['joint_timing_pass'] for r in group)
        trials.append(dict(trial=trial,window_s=window,requests=len(group),timing_passed=passed,timing_goodput_requests_per_s=passed/window))
    window=sum(t['window_s'] for t in trials);passed=sum(r['joint_timing_pass'] for r in rows)
    stats={}
    for key in ('delivered_ttft_ms','delivered_e2e_ms','delivered_mean_tpot_ms','engine_queue_ms'):
        values=sorted(r[key] for r in rows if r[key] is not None)
        stats[key]=dict(median=median(values),p95=values[ceil(.95*len(values))-1],maximum=max(values))
    return dict(schema_version=1,calculation='service-replay',scenario=dict(run=run,ttft_limit_ms=ttft_limit_ms,e2e_limit_ms=e2e_limit_ms,mean_tpot_limit_ms=mean_tpot_limit_ms),
                sources=sources,service_requests=rows,service_trials=trials,request_statistics=stats,
                summary=dict(requests=18,output_tokens=sum(r['output_tokens'] for r in rows),
                             joint_timing_passed=passed,joint_timing_pass_fraction=passed/18,
                             ttft_passed=sum(r['ttft_pass'] for r in rows),e2e_passed=sum(r['e2e_pass'] for r in rows),mean_tpot_passed=sum(r['mean_tpot_pass'] for r in rows),
                             summed_observation_window_s=window,timing_goodput_requests_per_s=passed/window,
                             request_throughput_per_s=18/window,output_throughput_tokens_per_s=sum(r['output_tokens'] for r in rows)/window,
                             multi_token_delivery_events=sum(r['multi_token_events'] for r in rows)),
                assumptions=[
                    '固定实验8-2四配置各三轮六请求，共72请求核对相同输入／运行源码／输出token；本场景选其中18请求。RTX PRO6000、Qwen8 BF16、vLLM0.23，其他服务驻留、配置按固定顺序执行，未跨配置交错，不推断微小优势。',
                    '客户端TTFT、E2E与平均TPOT均从同一perf_counter基准交付时间计算；TPOT=(末次-首次交付)/(输出数-1)，合并交付事件使单事件间隔不能冒充逐token ITL。引擎队列与TPOT在自己的monotonic基准内相减，不跨时钟相减。',
                    '联合计时判据为同一请求TTFT、E2E和平均TPOT三者均不超过显式阈值，边界包含等号；单输出请求无后续间隔，平均TPOT判据不适用。平均TPOT达标不保证每个输出间隔达标。',
                    '每轮观测窗从最早实际提交到最后实际输出，三轮窗口相加，不拼接重置的时间戳，不含轮间休息／引擎启动。goodput=联合达标请求数/窗口总和，不是三轮goodput等权平均，也不是单项通过率相乘。',
                    '阈值是新增分析输入，结果只是timing goodput。相同输出token不证明答案质量、任务成功率或生产SLO；没有新运行GPU，没有给设备／到达率外推。',
                ])
