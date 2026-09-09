"""Sealed same-size prefill chunks: measured intervals and official work."""
import hashlib
import json
from fractions import Fraction
from statistics import median
from ..paths import PROJECT
from ..models import forward
from ..schema import Scenario


def read_records():
    records={};sources=[]
    for entry in json.loads((PROJECT/'configs/chunk-history.lock.json').read_text())['files']:
        data=(PROJECT/entry['file']).read_bytes()
        if hashlib.sha256(data).hexdigest()!=entry['sha256']:
            raise ValueError('Chunk-history source checksum mismatch')
        name=entry['file'].split('sources/chunk-history/')[1]
        if name.endswith('.json'):records[name]=json.loads(data)
        sources.append(dict(file=entry['file'],url='../../'+entry['origin'],sha256=entry['sha256']))
    return records,sources


def recount(raw):
    if raw['status']!='passed' or len(raw['records'])!=11:
        raise ValueError('Expected 11 completed measured requests')
    blocks={h:[] for h in range(0,8192,512)};ratios=[];outputs=[];empty=0
    trials=set()
    for record in raw['records']:
        if record['trial'] in trials or len(record['steps'])!=1:raise ValueError('Duplicate trial or worker layout')
        trials.add(record['trial']);active=[];ids=set();histories=[]
        for step in record['steps'][0]:
            if not step['total_scheduled_tokens']:
                empty+=1
                continue
            mapping=step['per_request_scheduled_tokens']
            if step['total_scheduled_tokens']!=512 or len(mapping)!=1:raise ValueError('Not a single 512-token chunk')
            rid=next(iter(mapping));ids.add(rid)
            if not rid.startswith(f"trial-{record['trial']}-") or mapping[rid]!=512:raise ValueError('Request identity mismatch')
            if set(step['prior_scheduled_tokens'])!={rid}:raise ValueError('Prior request identity mismatch')
            history=step['prior_scheduled_tokens'][rid];histories.append(history)
            if history not in blocks or step['event_ms']<=0:raise ValueError('Invalid history/time')
            blocks[history].append(step['event_ms']);active.append(step)
        if histories!=list(blocks) or len(ids)!=1:raise ValueError('Incomplete or reordered prefill history')
        output=record['output']
        if len(output['output_ids'])!=1 or output['cached_tokens'] not in (None,0):raise ValueError('Output or APC mismatch')
        outputs.append(output['output_ids']);ratios.append(active[-1]['event_ms']/active[0]['event_ms'])
    if any(o!=outputs[0] for o in outputs):raise ValueError('Output tokens differ')
    return blocks,ratios,empty


def calculate():
    records,sources=read_records();raw=records['results/run-v1/raw.json'];config=records['engine-config.json']
    for name,expected in raw['source_hashes'].items():
        if hashlib.sha256((PROJECT/'sources/chunk-history'/name).read_bytes()).hexdigest()!=expected:
            raise ValueError('Raw measurement source identity mismatch')
    if raw['config']!={**config,'worker_extension_cls':'step_worker.StepWorker'}:
        raise ValueError('Execution configuration mismatch')
    if not config['model'].endswith('b968826d9c46dd6066d109eabc6255188de91218') or config['dtype']!='bfloat16':
        raise ValueError('Unexpected target model')
    if config['max_num_seqs']!=1 or config['max_num_batched_tokens']!=512 or config['enable_prefix_caching'] or not config['enforce_eager'] or not config['enable_chunked_prefill']:
        raise ValueError('Unexpected batching/cache/graph conditions')
    if len(records['inputs.json'])!=8192:raise ValueError('Unexpected input length')
    blocks,ratios,empty=recount(raw);rows=[]
    for history,samples in blocks.items():
        work=forward('qwen3-8b',Scenario(tokens=512,history=history,output_head='none'))
        rows.append(dict(history_tokens=history,new_tokens=512,causal_pairs=512*history+512*513//2,
                         backbone_matrix_flops=work['summary']['matrix_flops'],
                         kv_after_bytes=work['summary']['kv_resident_after_bytes'],
                         samples_ms=samples,median_ms=median(samples),min_ms=min(samples),max_ms=max(samples)))
    sources+=work['sources'];first=rows[0];last=rows[-1]
    full=forward('qwen3-8b',Scenario(tokens=8192,output_head='none'))['summary']['matrix_flops']
    if sum(row['backbone_matrix_flops'] for row in rows)!=full:raise ValueError('Chunked/full work conservation failed')
    return dict(schema_version=1,calculation='chunk-history',scenario=dict(model='qwen3-8b',new_tokens_per_chunk=512,input_tokens=8192,trials=11),
                sources=sources,chunk_history_rows=rows,
                summary=dict(requests=11,prefill_chunks=176,empty_execute_calls=empty,
                             first_median_ms=first['median_ms'],last_median_ms=last['median_ms'],
                             paired_last_first_median=median(ratios),ratio_of_medians=last['median_ms']/first['median_ms'],
                             first_causal_pairs=first['causal_pairs'],last_causal_pairs=last['causal_pairs'],
                             causal_pair_ratio_exact=str(Fraction(last['causal_pairs'],first['causal_pairs'])),
                             first_backbone_matrix_flops=first['backbone_matrix_flops'],last_backbone_matrix_flops=last['backbone_matrix_flops'],
                             backbone_matrix_ratio_exact=str(Fraction(last['backbone_matrix_flops'],first['backbone_matrix_flops'])),
                             full_prefill_backbone_matrix_flops=full),
                paired_last_first_ratios=ratios,versions=raw['versions'],
                assumptions=[
                    '导入实验8-2 chunk-history的15个封存文件，核对SHA、配置、请求ID、连续history、输出一致与零APC；不重跑GPU。11个正式请求各16块，空execute调用单列。',
                    'RTX PRO 6000、vLLM0.23、BF16、eager、单活跃请求、512预算，同引擎重复；其他GPU服务保留。输入为固定合成token，不能当作生产轨迹或答案质量验证。',
                    'event_ms为execute_model前后CUDA event区间，包含完整模型路径和可能的主机提交间隙；外部logits／采样不在区间内，官方工作采用output_head=none并仅计矩阵FLOPs。',
                    '注意力有效配对、完整backbone矩阵工作和实测时间分别列；配对比例不能当作整体算力、HBM访问或时间倍率。位置、内容、末块处理及执行顺序共同变化，不识别独立因果贡献。',
                    '配对末／首比例的中位数与两个位置中位数之比单独报告；11次样本保留，不生成置信区间或饱和服务SLO结论。',
                ])
