"""Actual missing prefix pages: fallback work and BF16 tensor differences."""
from array import array
import hashlib
import json
import struct
import sys
from pathlib import Path
from ..paths import PROJECT
from ..models import forward
from ..schema import Scenario


def compare_bf16(original,restored,layers=36,page_tokens=16,heads=8,head_dim=128):
    size=2*layers*page_tokens*heads*head_dim
    if len(original)!=size*2 or len(restored)!=size*2:raise ValueError('Incorrect BF16 layer_first page size')
    a=array('H');a.frombytes(original);b=array('H');b.frombytes(restored)
    if sys.byteorder!='little':a.byteswap();b.byteswap()
    rows=[dict(layer=i,different_elements=0,max_abs_difference=0.0) for i in range(layers)]
    stride=page_tokens*heads*head_dim
    for index,(x,y) in enumerate(zip(a,b)):
        if (x&0x7f80)==0x7f80 or (y&0x7f80)==0x7f80:raise ValueError('Nonfinite BF16 KV')
        if x!=y:
            row=rows[(index//stride)%layers];row['different_elements']+=1
            xf=struct.unpack('<f',struct.pack('<I',x<<16))[0]
            yf=struct.unpack('<f',struct.pack('<I',y<<16))[0]
            row['max_abs_difference']=max(row['max_abs_difference'],abs(xf-yf))
    return dict(elements=size,different_elements=sum(r['different_elements'] for r in rows),
                max_abs_difference=max(r['max_abs_difference'] for r in rows),layers=rows)


def calculate():
    lock=json.loads((PROJECT/'configs/cache-missing.lock.json').read_text());raw={};sources=[]
    for entry in lock['files']:
        data=(PROJECT/entry['file']).read_bytes()
        if hashlib.sha256(data).hexdigest()!=entry['sha256']:raise ValueError('Missing-page source SHA mismatch')
        name=entry['file'].split('sources/cache-missing/',1)[1];raw[name]=data
        sources.append(dict(file=entry['file'],url='../../'+entry['origin'],sha256=entry['sha256']))
    prep=json.loads(raw['preparation.json']);reference=json.loads(raw['reference-output.json'])
    rows=[];requests=[];layer_rows=[]
    for case in prep['cases']:
        name=case['case'];missing=case['missing_page_index'];before=case['before_files']
        doc=json.loads(raw[f'results/{name}/raw.json'])
        if len(before)!=64 or case['omitted'] in before or any(prep['source_files'][k]!=v for k,v in before.items()):raise ValueError('Invalid missing-page preparation')
        config=doc['config']
        if config['hicache_mem_layout']!='layer_first' or config['page_size']!=16 or config['dtype']!='bfloat16' or not config['model_path'].endswith('b968826d9c46dd6066d109eabc6255188de91218'):raise ValueError('Unexpected KV layout/model')
        for file,sha in doc['source_hashes'].items():
            if hashlib.sha256(raw[file]).hexdigest()!=sha:raise ValueError('Execution source mismatch')
        after={entry['path']:entry for entry in doc['storage_files']}
        if len(after)!=65 or any(after[k]['sha256']!=v for k,v in before.items()):raise ValueError('Unrelated file metadata changed')
        original=(PROJECT/'sources/cache-restart/storage-v3'/case['omitted']).read_bytes()
        restored=raw[f'restored-{name}.bin']
        if hashlib.sha256(original).hexdigest()!=prep['source_files'][case['omitted']] or hashlib.sha256(restored).hexdigest()!=after[case['omitted']]['sha256']:raise ValueError('Original/restored payload mismatch')
        compared=compare_bf16(original,restored)
        layer_rows.extend(dict(case=name,**row) for row in compared['layers'])
        trace=[json.loads(line) for line in raw[f'results/{name}/storage.jsonl'].decode().splitlines()]
        gets=[event for event in trace if event['method']=='get']
        if len(gets)!=missing or not all(event['success'] for event in trace):raise ValueError('Unexpected storage reads')
        if any(Path(event['file']).name not in before or event['bytes']!=2359296 for event in gets):raise ValueError('Invalid get payload')
        if len(doc['requests'])!=3:raise ValueError('Expected three requests')
        for index,request in enumerate(doc['requests']):
            meta=request['response']['meta_info'];hit=meta['cached_tokens']
            if request['response']['output_ids']!=reference or meta['prompt_tokens']!=1024 or meta['completion_tokens']!=16 or meta['num_retractions']!=0:raise ValueError('Request identity mismatch')
            expected=missing*16 if index==0 else 1008
            if hit!=expected:raise ValueError('Unexpected reusable prefix')
            if index and meta['cached_tokens_details']['device']!=1008:raise ValueError('Expected subsequent device hit')
            if name=='middle' and index==0 and meta['cached_tokens_details']['storage']!=512:raise ValueError('Expected partial storage hit')
            work=forward('qwen3-8b',Scenario(history=hit,tokens=1024-hit,output_head='last'))
            requests.append(dict(case=name,index=index,cached_tokens=hit,remaining_prefill_tokens=1024-hit,
                                 prefill_matrix_flops=work['summary']['matrix_flops'],client_seconds=request['end_s']-request['start_s']))
        rows.append(dict(case=name,missing_page_index=missing,successful_get_calls=len(gets),
                         get_file_bytes=sum(event['bytes'] for event in gets),first_reused_tokens=missing*16,
                         first_recomputed_tokens=1024-missing*16,restored_page_bytes=len(restored),
                         bf16_elements=compared['elements'],different_bf16_elements=compared['different_elements'],
                         max_abs_difference=compared['max_abs_difference'],other_files_reported_unchanged=True))
    # The device control creates exactly 512 prefix tokens with one output;
    # the earlier 16-output attempt had a different 528-token cache boundary.
    control=json.loads(raw['results/device-prefix-v2/raw.json'])
    if control['config']!=config:raise ValueError('Device control configuration differs')
    for file,sha in control['source_hashes'].items():
        if hashlib.sha256(raw[file]).hexdigest()!=sha:raise ValueError('Device control source mismatch')
    prefix=control['prefix_response']['meta_info']
    if prefix['prompt_tokens']!=512 or prefix['completion_tokens']!=1 or prefix['cached_tokens']!=0:
        raise ValueError('Device control must prepare exactly 512 tokens')
    if len(control['requests'])!=3:raise ValueError('Expected three full device-control requests')
    control_requests=[]
    for index,request in enumerate(control['requests']):
        meta=request['response']['meta_info']
        if meta['prompt_tokens']!=1024 or meta['completion_tokens']!=16 or request['response']['output_ids']!=reference:
            raise ValueError('Device-control full request mismatch')
        expected=512 if index==0 else 1008
        detail=meta['cached_tokens_details']
        if meta['cached_tokens']!=expected or detail!=dict(device=expected,host=0,storage=0,storage_backend='HiCacheFile'):
            raise ValueError('Device control did not reuse the required local prefix')
        control_requests.append(dict(index=index,cached_tokens=expected,cache_details=detail))
    middle=next(case for case in prep['cases'] if case['case']=='middle')
    original=(PROJECT/'sources/cache-restart/storage-v3'/middle['omitted']).read_bytes()
    device=raw['device-prefix-v2-page32.bin']
    expected_hash={entry['path']:entry['sha256'] for entry in control['storage_files']}[middle['omitted']]
    if hashlib.sha256(device).hexdigest()!=expected_hash:raise ValueError('Device-control page SHA mismatch')
    comparisons=[]
    for label,left,right in [('full_vs_device',original,device),
                             ('storage_vs_device',raw['restored-middle.bin'],device)]:
        result=compare_bf16(left,right)
        comparisons.append(dict(comparison=label,**result))
    return dict(schema_version=1,calculation='cache-missing',scenario=dict(experiment='9-8 missing pages'),
                sources=sources+work['sources'],summary=dict(cases=len(rows),requests=len(requests),device_control_full_requests=3,device_control_prefix_requests=1,outputs_match_reference=True),
                missing_page_cases=rows,missing_page_requests=requests,missing_page_layers=layer_rows,
                device_control_requests=control_requests,device_control_comparisons=comparisons,
                assumptions=[
                    '封存缺页0／32两个独立恢复实例，原页复用cache-restart已归档载荷；恢复页实际bytes与SHA核验。其余64页未改变的结论来自前后文件清单，未再复制两份完整目录。',
                    '实际layer_first BF16页[2,36,16,8,128]，按两字节字模式比较，再转FP32计算绝对差；全部元素有限，逐层合并K/V统计。',
                    'get止于缺口之前，后续文件仍存在不等于可复用连续前缀。首请求缺页0重算1024token、缺页32重算512token，后两次均device命中1008。',
                    '六次16token输出等于参考，不证明KV逐位一致。分段执行、形状和数值路径未完全隔离，不能将差异唯一归因于存储损坏或舍入；显存分段控制v2已核对512输入／1输出的前置请求及后续实际device命中512，排除旧528边界尝试；该控制仍未完全隔离所有形状与执行因素。',
                    '首条件含独立JIT，只有每条件一次重启，不作速度比或p95。矩阵只计实际剩余prefill，文件bytes不是物理磁盘IO，故障策略和长期持久性另计。',
                ])
