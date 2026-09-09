"""Actual persisted KV file bytes versus reusable tokens after a clean restart."""
import hashlib
import json
from pathlib import Path
from ..paths import PROJECT
from ..models import forward
from ..schema import Scenario
from .state import calculate as state_calculate


def calculate():
    lock=json.loads((PROJECT/'configs/cache-restart.lock.json').read_text());sources=[];raw={}
    for entry in lock['files']:
        data=(PROJECT/entry['file']).read_bytes()
        if hashlib.sha256(data).hexdigest()!=entry['sha256']:raise ValueError('Restart source SHA mismatch')
        name=entry['file'].split('sources/cache-restart/',1)[1]
        raw[name]=data
        # The manifest lists the 65 payload hashes; report metadata sources concisely.
        if not name.startswith('storage-v3/'):
            sources.append(dict(file=entry['file'],url='../../'+entry['origin'],sha256=entry['sha256']))
    documents={phase:json.loads(raw[f'results/{phase}-v6/raw.json']) for phase in ('producer','consumer')}
    config=documents['producer']['config']
    if config!=documents['consumer']['config'] or config['page_size']!=16 or config['dtype']!='bfloat16' or not config['model_path'].endswith('b968826d9c46dd6066d109eabc6255188de91218'):
        raise ValueError('Incompatible restart configurations')
    unit=state_calculate('qwen3-8b',1024)['summary']['kv_bytes_per_token_per_request']
    files={entry['path']:entry for entry in documents['producer']['storage_files']}
    if files!={entry['path']:entry for entry in documents['consumer']['storage_files']} or len(files)!=65:
        raise ValueError('Persisted inventory changed')
    for name,entry in files.items():
        data=raw['storage-v3/'+name]
        if len(data)!=entry['bytes'] or len(data)!=16*unit or hashlib.sha256(data).hexdigest()!=entry['sha256']:
            raise ValueError('KV payload geometry/hash mismatch')
    requests=[];trace_stats=[];pids={};reference=None
    for phase,document in documents.items():
        for name,sha in document['source_hashes'].items():
            if hashlib.sha256(raw[name]).hexdigest()!=sha:raise ValueError('Execution source mismatch')
        if len(document['requests'])!=3:raise ValueError('Expected three requests per process')
        for index,request in enumerate(document['requests']):
            meta=request['response']['meta_info'];output=request['response']['output_ids'];hit=meta['cached_tokens']
            if meta['prompt_tokens']!=1024 or meta['completion_tokens']!=16 or meta['num_retractions']!=0 or len(output)!=16:
                raise ValueError('Request workload mismatch')
            if reference is not None and output!=reference:raise ValueError('Restart output differs')
            reference=output
            if request['end_s']<request['start_s']:raise ValueError('Invalid request clock')
            expected=0 if phase=='producer' and index==0 else 1008
            if hit!=expected:raise ValueError('Unexpected reusable token count')
            detail=meta['cached_tokens_details']
            if phase=='consumer' and index==0:
                if detail!=dict(device=0,host=0,storage=1008,storage_backend='HiCacheFile'):raise ValueError('No verified storage hit')
            elif hit and detail['device']!=1008:raise ValueError('Expected local device reuse')
            full=forward('qwen3-8b',Scenario(tokens=1024,output_head='last'))
            actual=forward('qwen3-8b',Scenario(tokens=1024-hit,history=hit,output_head='last'))
            requests.append(dict(phase=phase,index=index,cached_tokens=hit,cache_details=detail,
                                 client_seconds=request['end_s']-request['start_s'],
                                 reusable_kv_bytes=hit*unit,prefill_saved_matrix_flops=full['summary']['matrix_flops']-actual['summary']['matrix_flops']))
        trace=[json.loads(line) for line in raw[f'results/{phase}-v6/storage.jsonl'].decode().splitlines()]
        if not all(row['success'] for row in trace):raise ValueError('Failed storage call')
        pids[phase]={row['pid'] for row in trace}
        for method in ('get','set'):
            events=[row for row in trace if row['method']==method]
            for event in events:
                name=Path(event['file']).name
                if name not in files or event['bytes']!=files[name]['bytes'] or event['end_s']<event['start_s']:
                    raise ValueError('Storage call payload mismatch')
            if phase=='consumer' and method=='get':
                first=document['requests'][0]
                if len(events)!=64 or len({event['key'] for event in events})!=64:raise ValueError('Incomplete storage reads')
                if not all(first['start_s']<=event['start_s']<=event['end_s']<=first['end_s'] for event in events):raise ValueError('Read outside consumer first request')
            trace_stats.append(dict(phase=phase,method=method,calls=len(events),
                                   file_bytes_named=sum(row['bytes'] for row in events),
                                   wall_span_seconds=max(row['end_s'] for row in events)-min(row['start_s'] for row in events) if events else 0))
    if pids['producer']&pids['consumer']:raise ValueError('Producer and consumer are not distinct processes')
    observed={(row['phase'],row['method']):row['calls'] for row in trace_stats}
    if observed!={('producer','get'):0,('producer','set'):65,('consumer','get'):64,('consumer','set'):1}:raise ValueError('Unexpected call counts')
    return dict(schema_version=1,calculation='cache-restart',scenario=dict(experiment='9-8 clean restart'),
                sources=sources+full['sources'],summary=dict(verified_payload_files=65,kv_page_tokens=16,
                    kv_page_bytes=16*unit,stored_payload_bytes=sum(entry['bytes'] for entry in files.values()),
                    consumer_get_calls=64,consumer_read_file_bytes=64*16*unit,
                    consumer_read_page_tokens=1024,consumer_reusable_tokens=1008,
                    consumer_reusable_bytes=1008*unit,read_but_not_reused_token_equivalent_bytes=16*unit,
                    requests=6,outputs_match=True),restart_requests=requests,restart_storage_calls=trace_stats,
                assumptions=[
                    '封存9-8 producer-v6/consumer-v6原件和65份实际KV文件全部SHA核验，模型BF16/16token页/配置相同，六次16token输出一致；未重跑服务或清页缓存。',
                    '每页bytes按官方Qwen36层GQA计算。读取64页对应1024token，但引擎可复用1008；多读16token等价量单列，不称全部读取都避免重算。',
                    '文件bytes和成功get/set调用不等于物理磁盘IO；set遇到已有文件可能直接成功。消费者一次set不计成新增持久化文件；两进程文件库存与哈希相同。',
                    '首个producer请求含JIT，单次正常重启不作速度比或恢复p95。fromfile/tofile路径不证明fsync、断电持久性、损坏检测或崩溃一致性。',
                    '矩阵仅计prompt首token前的完整／命中逻辑prefill，不含之后15次decode、真实访存或编译。强制相同16输出不等于任务质量或KV逐位与重算一致。',
                ])
