"""Archived natural retrieval quality, fixed-output timing and actual KV pools."""
import hashlib
import json
import re
import math
from statistics import median
from ..paths import PROJECT
from ..sources import model_config,provenance


RUNS=('bf16','fp8','fp8_qbf16')


def strict_answer(text,expected):
    def unique(pairs):
        result={}
        for key,value in pairs:
            if key in result:raise ValueError('Duplicate JSON answer key')
            result[key]=value
        return result
    try:return json.loads(text,object_pairs_hook=unique)==expected
    except (ValueError,TypeError):return False


def read_records():
    records={};sources=[]
    for entry in json.loads((PROJECT/'configs/kv-quality.lock.json').read_text())['files']:
        data=(PROJECT/entry['file']).read_bytes()
        if hashlib.sha256(data).hexdigest()!=entry['sha256']:raise ValueError('KV quality hash mismatch')
        name=entry['file'].split('sources/kv-quality/')[1]
        if name.endswith('.json'):records[name]=json.loads(data)
        elif name.endswith('.jsonl'):records[name]=[json.loads(line) for line in data.decode().splitlines()]
        sources.append(dict(file=entry['file'],url='../../'+entry['origin'],sha256=entry['sha256']))
    return records,sources


def calculate(run='bf16'):
    if run not in RUNS:raise ValueError('Unknown KV quality run')
    data,sources=read_records();c=model_config('qwen3-8b');layers=c['num_hidden_layers'];heads=c['num_key_value_heads'];dim=c['head_dim']
    base=data['results/bf16/environment.json'];all_rows={};pools={};scales={}
    for name in RUNS:
        prefix=f'results/{name}/';env=data[prefix+'environment.json'];config=dict(base['config'])
        if name!='bf16':config['kv_cache_dtype']='fp8_e4m3'
        if name=='fp8_qbf16':config['worker_extension_cls']='probe_qbf16.KVQBF16Probe'
        if env['config']!=config or env['input_sha256']!=base['input_sha256']:raise ValueError('Unexpected config/input difference')
        if env['vllm']!='0.23.0' or config['dtype']!='bfloat16' or not config['model'].endswith('b968826d9c46dd6066d109eabc6255188de91218'):raise ValueError('Unexpected model/runtime')
        for file,digest in env['hashes'].items():
            if hashlib.sha256((PROJECT/'sources/kv-quality'/file).read_bytes()).hexdigest()!=digest:raise ValueError('Runtime source identity mismatch')
        if hashlib.sha256((PROJECT/'sources/kv-quality'/prefix/'inputs.json').read_bytes()).hexdigest()!=env['input_sha256']:raise ValueError('Input file hash mismatch')
        tasks={t['id']:t for t in data[prefix+'inputs.json']['tasks']}
        if len(tasks)!=8:raise ValueError('Expected eight distinct retrieval tasks')
        for task in tasks.values():
            pairs=re.findall(r'^(k\d{4}) = (\d{6})$',task['messages'][1]['content'],re.MULTILINE)
            document=dict(pairs)
            if len(document)!=len(pairs) or len(document)!=task['rows'] or any(document[k]!=v for k,v in task['expected'].items()):raise ValueError('Answer key does not match document')
        snapshots=data[prefix+'kv-snapshots.json'];cal=snapshots['after_calibration'][0];after=snapshots['after'][0]
        scales[name]=cal['scales']
        if len(scales[name])!=layers or scales[name]!=after['scales']:raise ValueError('KV scales changed')
        if any(s['calculate'] or s['backend']!='TritonAttentionImpl' or any(not math.isfinite(s[k]) or s[k]<=0 for k in ('k','v')) for s in scales[name]):raise ValueError('Invalid frozen scale')
        element_bytes=2 if name=='bf16' else 1;blocks=5461 if name=='bf16' else 10922
        tensors=cal['kv_tensors'];expected_shape=[blocks,2,16,heads,dim]
        if len(tensors)!=layers or any(t['shape']!=expected_shape or t['dtype']!=('torch.bfloat16' if name=='bf16' else 'torch.uint8') or t['logical_bytes']!=math.prod(expected_shape)*element_bytes or t['storage_bytes']!=t['logical_bytes'] for t in tensors):raise ValueError('KV tensor geometry mismatch')
        pool=sum(t['storage_bytes'] for t in tensors)
        if pool!=cal['unique_kv_storage_bytes']:raise ValueError('Unique KV storage mismatch')
        pools[name]=dict(blocks=blocks,token_slots=blocks*16,storage_bytes=pool,bytes_per_token=2*layers*heads*dim*element_bytes)
        if name!='bf16' and (snapshots['armed_layers']!=[36] or scales[name]==snapshots['before'][0]['scales']):raise ValueError('Missing independent FP8 calibration')
        if name=='fp8_qbf16':
            if snapshots['q_override_layers']!=[36] or any(q['enabled'] for q in snapshots['after_q_override'][0]['query_quantization']):raise ValueError('Q override missing')
            observed=after['observed_query_dtypes']
            if len(observed)!=36 or set(observed.values())!={'torch.bfloat16'} or scales[name]!=scales['fp8']:raise ValueError('Q dtype or matched calibration mismatch')
        requests=data[prefix+'requests.jsonl'];batches=data[prefix+'batches.jsonl'];evaluated=[]
        if len(requests)!=97 or len(batches)!=24 or len({r['id'] for r in requests})!=97:raise ValueError('Unexpected invocation counts')
        for batch in batches:
            group=[r for r in requests if r['id'].startswith(batch['id']+'-')]
            if len(group)!=4 or len({r['task_id'] for r in group})!=4:raise ValueError('Incomplete batch')
            for r in group:
                task=tasks[r['task_id']];mode=r['mode'];count=len(r['output_ids'])
                if mode!=batch['mode'] or task['rows']!=batch['rows']:raise ValueError('Task condition mismatch')
                if mode=='fixed' and (count!=64 or r['finish_reason']!='length'):raise ValueError('Fixed output work changed')
                if not batch['start_s']<=r['start_s']<=r['end_s']<=batch['end_s']:raise ValueError('Request outside batch clock')
                if batch['trial']=='warm':continue
                evaluated.append(dict(id=r['id'],task_id=r['task_id'],mode=mode,trial=batch['trial'],rows=batch['rows'],concurrency=batch['concurrency'],
                                      output_tokens=count,finish_reason=r['finish_reason'],output_ids=r['output_ids'],
                                      correct=strict_answer(r['text'],task['expected']) if mode=='natural' else None,
                                      latency_s=r['end_s']-r['start_s']))
        if len(evaluated)!=64:raise ValueError('Expected64 formal requests')
        all_rows[name]=evaluated
    rows=all_rows[run];summaries=[]
    for document_rows in (128,512):
        for concurrency in (1,4):
            for mode in ('natural','fixed'):
                group=[r for r in rows if (r['rows'],r['concurrency'],r['mode'])==(document_rows,concurrency,mode)]
                batches=[b for b in data[f'results/{run}/batches.jsonl'] if b['trial']!='warm' and (b['rows'],b['concurrency'],b['mode'])==(document_rows,concurrency,mode)]
                if len(group)!=8 or len(batches)!=2:raise ValueError('Formal condition count mismatch')
                window=sum(b['end_s']-b['start_s'] for b in batches)
                summaries.append(dict(document_rows=document_rows,concurrency=concurrency,mode=mode,requests=8,
                                      correct=sum(r['correct'] for r in group) if mode=='natural' else None,
                                      natural_truncated=sum(r['finish_reason']=='length' for r in group) if mode=='natural' else None,
                                      output_tokens=sum(r['output_tokens'] for r in group),median_latency_s=median(r['latency_s'] for r in group),
                                      batch_window_s=window,output_tokens_per_s=sum(r['output_tokens'] for r in group)/window,
                                      failed_ids=[r['id'] for r in group if r['correct'] is False]))
    natural=[r for r in rows if r['mode']=='natural'];comparisons={}
    baseline={r['id']:r for r in all_rows['bf16']}
    for name,records in all_rows.items():
        if set(baseline)!={r['id'] for r in records}:raise ValueError('Cross-format request IDs differ')
        comparisons[name]=dict(natural_output_differences=sum(r['output_ids']!=baseline[r['id']]['output_ids'] for r in records if r['mode']=='natural'),
                               natural_correctness_changes=[r['id'] for r in records if r['mode']=='natural' and r['correct']!=baseline[r['id']]['correct']])
    return dict(schema_version=1,calculation='kv-quality',scenario=dict(run=run),sources=sources+provenance('qwen3-8b'),
                kv_quality_conditions=summaries,kv_quality_requests=rows,actual_kv_pools=pools,paired_against_bf16=comparisons,
                summary=dict(distinct_tasks=8,formal_requests=64,natural_executions=32,natural_correct=sum(r['correct'] for r in natural),
                             natural_output_lengths=sorted({r['output_tokens'] for r in natural}),natural_length_stops=sum(r['finish_reason']=='length' for r in natural),
                             natural_stop_reasons=sorted({r['finish_reason'] for r in natural}),**pools[run]),
                assumptions=[
                    '导入实验8-8三条件的原始manifest封存文件，核对配置、源码、输入文档与答案、实际KV张量、独立校准与冻结scale。没有重跑GPU或替换错误输出。',
                    '自然检索答案严格JSON判定，拒绝重复键／多余文字／错误值；固定64输出只计工作与时长，不以其后续文本评价自然答案。每格式32次自然执行仅八个不同任务，不能当作32个独立质量样本。',
                    'BF16／FP8／FP8+BF16 Q都保持BF16权重；原FP8引擎路径同时改变Q量化，后续控制组实际观察36层Q为BF16且KV scales匹配。不能将原两组差异全部归于KV位宽。',
                    '固定12GiB KV预算，BF165461块、FP810922块，唯一storage字节相同；较小元素换更多token槽，不是实际分配减半，也未实测最大可接纳并发或DRAM流量。',
                    '时间为同批次起止区间，统计自然和固定长度分开；格式顺序运行、共享GPU、仅两轮，Q观察控制组另有Python回调开销，不用于确定微小速度排名。没有重试，错误请求的时间不含修正答案成本。',
                ])
