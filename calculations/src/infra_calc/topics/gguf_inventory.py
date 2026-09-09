"""Pinned publisher GGUF shard inventory and explicit unified-memory budget.

File bytes are not decoded tensor residency. No quantization block layout is
inferred from a variant's display name.
"""
import hashlib
import json
import re
from ..paths import PROJECT
from ..topics import state
from ..units import positive_int


def inventory():
    lock=json.loads((PROJECT/'configs/gguf-qwen235.lock.json').read_text());sources=[];tree=None
    for record in lock['files']:
        data=(PROJECT/record['file']).read_bytes()
        if hashlib.sha256(data).hexdigest()!=record['sha256']:raise ValueError('GGUF inventory hash mismatch')
        if record['file'].endswith('/tree.json'):tree=json.loads(data)
        sources.append(record)
    groups={};seen=set()
    for entry in tree:
        path=entry['path']
        if path in seen:raise ValueError('Duplicate tree path')
        seen.add(path)
        if entry['type']!='file' or not path.endswith('.gguf'):continue
        match=re.fullmatch(r'([^/]+)/Qwen3-235B-A22B-(.+)-(\d{5})-of-(\d{5})\.gguf',path)
        if match is None or match[1]!=match[2]:raise ValueError('Unexpected GGUF shard naming')
        variant=match[1];index=int(match[3]);count=int(match[4]);lfs=entry.get('lfs',{})
        if entry['size']!=lfs.get('size') or not re.fullmatch('[0-9a-f]{64}',lfs.get('oid','')):raise ValueError('Missing or inconsistent LFS identity')
        groups.setdefault(variant,[]).append(dict(path=path,index=index,count=count,file_bytes=entry['size'],lfs_sha256=lfs['oid']))
    for shards in groups.values():
        shards.sort(key=lambda x:x['index']);count=shards[0]['count']
        if len(shards)!=count or [s['index'] for s in shards]!=list(range(1,count+1)) or any(s['count']!=count for s in shards):
            raise ValueError('Incomplete or inconsistent shard set')
    return groups,sources,lock


def calculate(context_tokens=8192,memory_budget_bytes=96*10**9,reserved_bytes=8*1024**3,
              variants=None):
    positive_int(context_tokens,'context_tokens')
    positive_int(memory_budget_bytes,'memory_budget_bytes')
    positive_int(reserved_bytes,'reserved_bytes',allow_zero=True)
    if reserved_bytes>memory_budget_bytes:raise ValueError('Reserved budget exceeds memory')
    groups,sources,lock=inventory()
    variants=['Q2_K','UD-Q2_K_XL','Q3_K_S','Q4_K_M','Q8_0','BF16'] if variants is None else variants
    if not isinstance(variants,list) or not variants or len(set(variants))!=len(variants) or any(v not in groups for v in variants):raise ValueError('Unknown or duplicate GGUF variant')
    kv=state.calculate(model='qwen3-235b-a22b',length=context_tokens)
    from ..sources import model_config
    config=model_config('qwen3-235b-a22b')
    if context_tokens>config['max_position_embeddings']:raise ValueError('Context exceeds official limit')
    per_token=4*config['num_hidden_layers']*config['num_key_value_heads']*config['head_dim']
    kv_bytes=kv['summary']['resident_bytes']
    if kv_bytes!=context_tokens*per_token:raise ValueError('Official KV geometry mismatch')
    available=memory_budget_bytes-reserved_bytes
    rows=[]
    for variant in variants:
        shards=groups[variant];size=sum(s['file_bytes'] for s in shards)
        remaining=available-size
        rows.append(dict(variant=variant,shards=len(shards),file_bytes=size,file_gib=size/1024**3,
                         budget_after_files_bytes=remaining,
                         max_independent_bf16_kv_requests=max(0,remaining//kv_bytes),
                         files_fit_budget=size<=available,
                         files_plus_one_kv_fit=size+kv_bytes<=available,
                         bytes_over_budget_with_one_kv=max(0,size+kv_bytes-available),
                         shard_files=shards))
    return dict(schema_version=1,calculation='gguf-inventory',scenario=dict(context_tokens=context_tokens,
                memory_budget_bytes=memory_budget_bytes,reserved_bytes=reserved_bytes,variants=variants),
                sources=sources+kv['sources'],gguf_variants=rows,
                summary=dict(repository=lock['repository'],revision=lock['revision'],
                             complete_variants_in_tree=len(groups),complete_gguf_files=sum(len(s) for s in groups.values()),
                             declared_available_bytes=available,bf16_kv_bytes_per_token=per_token,
                             bf16_kv_bytes_per_independent_request=kv_bytes,
                             all_variant_file_totals={k:sum(s['file_bytes'] for s in v) for k,v in sorted(groups.items())}),
                assumptions=[
                    '文件清单来自量化发布者unsloth的固定revision API，逐variant核对分片序号1..N完整、大小与LFS size一致，并保留发布LFS SHA256。这里只下载目录元数据，未下载或计算完整GGUF载荷哈希；发布哈希不是本地校验通过声明。',
                    'Q2_K、Q4_K_M等是文件变体名称，不将其当作所有张量位宽。总量逐分片求和包含文件头、tokenizer元数据、张量数据及对齐；尚未解析各张量类型，不能从总量差额单独识别量化元数据开销。',
                    '96×10^9总预算与8GiB预留是可修改的教学输入，对应96GB机器容量规划问题，不是本机实测可用内存。预留需覆盖系统、运行时、图和工作区；本模型没有证明8GiB足够。',
                    '容量情景假定整个文件字节都有一份内存预算，另加独立请求的官方Qwen235 BF16 GQA KV。文件大小不等于实际mmap驻留、解包／重打包或GPU分配，不能把此情景称为真实可运行并发。',
                    'KV取指定缓存位置数，每请求独立，无前缀共享／页碎片／KV量化；不根据MoE每token激活22B裁减235B完整权重文件。量化质量、冷加载、SSD／主存读取与生成速度未测。',
                ])
