"""Actual DCP tensor coverage, changed shard axes and next-update verification."""
import hashlib
import json
from itertools import combinations
from math import prod
from ..sources import PROJECT


WIDTHS={'torch.float32':4,'torch.uint8':1,'torch.int64':8}


def coverage(shape,chunks):
    """Rectangles within bounds, pairwise disjoint, and equal total volume."""
    for c in chunks:
        if len(c['offsets'])!=len(shape) or len(c['sizes'])!=len(shape):raise ValueError('Chunk rank mismatch')
        if any(not isinstance(x,int) or isinstance(x,bool) for x in c['offsets']+c['sizes']):raise ValueError('Integer coordinates required')
        if any(o<0 or n<=0 or o+n>s for o,n,s in zip(c['offsets'],c['sizes'],shape)):raise ValueError('Chunk out of bounds')
    for a,b in combinations(chunks,2):
        if all(max(x,y)<min(x+n,y+m) for x,n,y,m in zip(a['offsets'],a['sizes'],b['offsets'],b['sizes'])):
            raise ValueError('Overlapping chunks')
    if sum(prod(c['sizes']) for c in chunks)!=prod(shape):raise ValueError('Missing tensor volume')


def read_records():
    lock=json.loads((PROJECT/'configs/checkpoint-resume.lock.json').read_text());raw={}
    for e in lock['files']:
        data=(PROJECT/e['file']).read_bytes()
        if len(data)!=e['bytes'] or hashlib.sha256(data).hexdigest()!=e['sha256']:raise ValueError('Resume evidence changed')
        raw[e['file'].split('sources/checkpoint-resume/',1)[1]]=data
    sources=[dict(file=e['file'],url='../../'+e['origin'],sha256=e['sha256']) for e in lock['files']
             if e['file'].endswith(('run.py','inspect_checkpoint.py','checkpoint-manifest.json','reference.json'))]
    return raw,sources


def calculate():
    raw,sources=read_records();manifest=json.loads(raw['results/checkpoint-manifest.json']);reference=json.loads(raw['results/reference.json'])
    run_hash=hashlib.sha256(raw['run.py']).hexdigest();tensor_rows=[]
    if set(manifest['tensors'])!=set(reference['before']) or set(reference['before'])!=set(reference['after']):
        raise ValueError('State field identity mismatch')
    for name,tensor in manifest['tensors'].items():
        coverage(tensor['shape'],tensor['chunks'])
        width=WIDTHS[tensor['dtype']]
        tensor_rows.append(dict(name=name,shape=tensor['shape'],dtype=tensor['dtype'],logical_bytes=prod(tensor['shape'])*width,
                                saved_chunks=tensor['chunks'],chunk_count=len(tensor['chunks'])))
    for name,e in manifest['files'].items():
        data=raw['results/checkpoint/'+name]
        if len(data)!=e['bytes'] or hashlib.sha256(data).hexdigest()!=e['sha256']:raise ValueError('Checkpoint container hash mismatch')
    groups=[];ranks=[]
    for mode,world,axis in [('save',2,0),('load',2,0),('load',3,1),('load',1,0)]:
        group=[]
        for rank in range(world):
            r=json.loads(raw[f'results/{mode}-w{world}-axis{axis}-rank{rank}.json'])
            if (r['mode'],r['world_size'],r['axis'],r['rank'])!=(mode,world,axis,rank) or r['source_sha256']!=run_hash:
                raise ValueError('Executed source or rank identity mismatch')
            if (r['torch'],r['backend'],r['device'])!=('2.10.0+cu128','gloo','cpu'):raise ValueError('Execution environment mismatch')
            if set(r['local_shapes'])!=set(manifest['tensors']):raise ValueError('Missing local state')
            local_bytes=0
            for name,t in manifest['tensors'].items():
                shape=list(t['shape'])
                if shape and not name.endswith('rng'):
                    dim=min(axis,len(shape)-1);chunk=(shape[dim]+world-1)//world
                    shape[dim]=max(0,min(chunk,shape[dim]-rank*chunk))
                if r['local_shapes'][name]!=shape:raise ValueError('Actual local shape differs from declared DTensor placement')
                local_bytes+=prod(shape)*WIDTHS[t['dtype']]
            if mode=='load':
                if r['restored_hashes']!=reference['before'] or r['next_state_hashes']!=reference['after'] or r['next_loss']!=reference['next_loss']:
                    raise ValueError('Actual next update or recovered state mismatch')
                if r['optimizer_loss_negative_control_detected'] is not True:raise ValueError('Missing Adam negative control')
            row=dict(mode=mode,world=world,axis=axis,rank=rank,api_seconds=r['api_seconds'],
                     local_logical_state_bytes=local_bytes,first_weight_shape=r['local_shapes']['model.0.weight'],
                     restored_and_next_update_match=True if mode=='load' else None)
            group.append(row);ranks.append(row)
        groups.append(dict(mode=mode,world=world,axis=axis,max_rank_api_seconds=max(x['api_seconds'] for x in group),
                           sum_rank_local_logical_bytes=sum(x['local_logical_state_bytes'] for x in group),
                           first_weight_local_shapes=[x['first_weight_shape'] for x in group]))
    logical=sum(t['logical_bytes'] for t in tensor_rows)
    actual=sum(e['bytes'] for e in manifest['files'].values())
    return dict(schema_version=1,calculation='checkpoint-resume',scenario=dict(experiment='ch10/10-06',save_world=2,load_worlds=[2,3,1]),sources=sources,
                checkpoint_resume_tensors=tensor_rows,checkpoint_resume_ranks=ranks,checkpoint_resume_groups=groups,
                summary=dict(archived_evidence_files=len(raw),logical_state_tensors=len(tensor_rows),unique_logical_state_bytes=logical,
                             actual_checkpoint_file_bytes=actual,metadata_bytes=manifest['files']['.metadata']['bytes'],
                             actual_minus_logical_bytes=actual-logical,restored_ranks=6,next_loss=reference['next_loss'],
                             all_reported_next_states_match=True,all_reported_adam_negative_controls_detected=True),
                assumptions=[
                    '实际CPU/Gloo PyTorch2.10.0+cu128小模型，2进程行保存→2行/3列/1完整恢复，非Qwen或多机GPU训练。模型Linear129→257→17含tanh/Dropout，FP32 AdamW，先更新4步保存，再核验第5步。',
                    '文件SHA逐一核验，19逻辑状态形状与chunk坐标来自已封存inspect_checkpoint对实际metadata的提取；本CLI不重新反序列化metadata或执行torch恢复。恢复和下一步相同来源为封存实际加载/训练记录。',
                    '矩形chunk先检查边界、两两无交集，再以总体积证明完整覆盖；标量体积为1。局部shape按固定源码DTensor placement核对，RNG和标量复制；全组局部字节可因复制大于唯一逻辑状态。',
                    '数据容器与metadata总文件字节、唯一逻辑载荷分开；差额可能含序列化、对齐和复制等，不单独归因为某种开销，不把该差额或API时间当磁盘吞吐。',
                    '每rank API在barrier后计时，只取各路径最大rank，不相加，也没有共同起止全局墙钟。未含torchrun启动、DTensor构造、加载后full_tensor聚合与下一步训练；每路径一次不排名布局性能。',
                    '恢复目标先置零；恢复后聚合成完整张量，再走相同单进程数学路径，故不证明不同分布式归约能逐位相同。全部6恢复rank检出清空Adam动量负对照；真实DataLoader队列、packing残留和大模型完整恢复仍待。',
                ])
