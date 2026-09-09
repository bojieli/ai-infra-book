"""Small reference-counted KV page allocator with explicit fork/append/cancel."""
from collections import Counter
from ..sources import model_config, provenance
from ..units import positive_int
from .state import calculate as state_calculate


def calculate(model='qwen3-8b',page_tokens=16,reservation_tokens=64,events=None,capacity_bytes=None):
    positive_int(page_tokens,'page_tokens');positive_int(reservation_tokens,'reservation_tokens')
    config=model_config(model)
    if config['model_type'] not in ('qwen3','qwen3_moe'):
        raise ValueError('Full-history Qwen GQA page geometry required')
    per_token=state_calculate(model,length=1)['summary']['kv_bytes_per_token_per_request']
    page_bytes=page_tokens*per_token
    if capacity_bytes is not None:
        positive_int(capacity_bytes,'capacity_bytes',allow_zero=True)
    capacity_pages=None if capacity_bytes is None else capacity_bytes//page_bytes
    if events is None:
        events=[dict(op='create',id='a',tokens=17),dict(op='fork',parent='a',id='b'),
                dict(op='fork',parent='a',id='c'),dict(op='append',id='a',tokens=1),
                dict(op='append',id='b',tokens=16),dict(op='cancel',id='c')]
    if not isinstance(events,list) or not events:raise ValueError('Nonempty event list required')
    requests={};pages={};next_page=0;rows=[];copied=0
    def allocate(used=0):
        nonlocal next_page
        page=next_page;next_page+=1;pages[page]=used
        return page
    def refs():return Counter(page for table in requests.values() for page in table)
    def append(name,count):
        nonlocal copied
        table=requests[name]
        while count:
            if not table or pages[table[-1]]==page_tokens:
                table.append(allocate())
            tail=table[-1]
            if refs()[tail]>1:
                copied+=pages[tail]*per_token
                tail=allocate(pages[tail]);table[-1]=tail
            take=min(count,page_tokens-pages[tail]);pages[tail]+=take;count-=take
    for index,event in enumerate(events):
        op=event['op'];name=event['id']
        if not isinstance(name,str) or not name:raise ValueError('Nonempty request ID required')
        before_pages=set(pages);before_copy=copied
        if op in ('create','fork') and name in requests:raise ValueError('Request already exists')
        if op in ('append','cancel') and name not in requests:raise ValueError('Unknown request')
        additional_pages=0
        if op in ('create','append'):
            positive_int(event['tokens'],'tokens',allow_zero=True)
            count=event['tokens']
            table=requests.get(name,[])
            current=sum(pages[p] for p in table)
            if current+count>reservation_tokens:raise ValueError('Sequence exceeds declared reservation maximum')
            if count:
                room=page_tokens-pages[table[-1]] if table else 0
                additional_pages=(max(0,count-room)+page_tokens-1)//page_tokens
                if room and refs()[table[-1]]>1:additional_pages+=1
        accepted=capacity_pages is None or len(pages)+additional_pages<=capacity_pages
        if not accepted:
            pass  # Admission fails before any page, length or reference mutation.
        elif op in ('create','append'):
            positive_int(event['tokens'],'tokens',allow_zero=True)
            current=sum(pages[p] for p in requests.get(name,[]))
            if current+event['tokens']>reservation_tokens:raise ValueError('Sequence exceeds declared reservation maximum')
            if op=='create':requests[name]=[]
            append(name,event['tokens'])
        elif op=='fork':
            if event['parent'] not in requests:raise ValueError('Unknown parent')
            requests[name]=list(requests[event['parent']])
        elif op=='cancel':
            del requests[name]
        else:raise ValueError('Unknown allocator operation')
        references=refs()
        for page in set(pages)-set(references):del pages[page]
        lengths={key:sum(pages[p] for p in table) for key,table in requests.items()}
        logical=sum(lengths.values())*per_token
        unique=sum(pages.values())*per_token
        allocated=len(pages)*page_tokens*per_token
        private_pages=sum((length+page_tokens-1)//page_tokens for length in lengths.values())
        rows.append(dict(event=index,operation=event,accepted=accepted,
                         additional_pages_required=additional_pages,
                         rejection_reason=None if accepted else 'insufficient_page_capacity',
                         request_lengths=lengths,
                         page_tables={key:list(table) for key,table in requests.items()},
                         pages=[dict(id=p,used_tokens=pages[p],references=references[p]) for p in sorted(pages)],
                         active_requests=len(requests),logical_request_bytes=logical,
                         unique_live_bytes=unique,allocated_page_bytes=allocated,
                         unused_page_bytes=allocated-unique,
                         private_paged_bytes=private_pages*page_tokens*per_token,
                         fixed_reservation_bytes=len(requests)*reservation_tokens*per_token,
                         copied_valid_bytes=copied-before_copy,
                         freed_page_ids=sorted(before_pages-set(pages))))
    last=rows[-1]
    return dict(schema_version=1,calculation='kv-pages',
                scenario=dict(model=model,page_tokens=page_tokens,reservation_tokens=reservation_tokens,events=events,capacity_bytes=capacity_bytes),
                sources=provenance(model),kv_page_events=rows,
                summary=dict(kv_bytes_per_token=per_token,page_bytes=page_tokens*per_token,
                             capacity_pages=capacity_pages,
                             unusable_capacity_bytes=None if capacity_bytes is None else capacity_bytes%page_bytes,
                             rejected_events=sum(not row['accepted'] for row in rows),
                             peak_allocated_page_bytes=max(row['allocated_page_bytes'] for row in rows),
                             final_allocated_page_bytes=last['allocated_page_bytes'],
                             final_logical_request_bytes=last['logical_request_bytes'],
                             final_unique_live_bytes=last['unique_live_bytes'],
                             final_unused_page_bytes=last['unused_page_bytes'],
                             final_private_paged_bytes=last['private_paged_bytes'],
                             final_fixed_reservation_bytes=last['fixed_reservation_bytes'],
                             total_copied_valid_bytes=copied),
                assumptions=[
                    '官方Qwen BF16完整GQA每token跨全层KV字节；一个逻辑页聚合各层相同token范围，实际引擎可能分层分配。本例不含权重、工作区、块表与引用计数元数据。',
                    'create建立独立序列，fork共享父序列全部页；append只修改尾部。共享未满尾页写前复制，满页后追加新页；只复制有效旧token字节，未初始化空位不复制。真实kernel可能搬整个块，需另核。',
                    'cancel在安全点立即移除该请求引用，只释放引用计数归零页；不是实际异步取消API完成保证。事件之间无在途读写，不需额外延迟回收。',
                    '逻辑请求字节对每请求分别求和，unique_live去除物理共享，allocated按完整页计，unused=allocated-unique_live。共享节省与尾块碎片分开，不用allocated-logical作为碎片。',
                    'fixed_reservation按每活跃请求显式最大长度预留，private_paged按各请求当前长度分页但不共享；三者在相同事件点比较。最大长度是输入约束，不预测真实生成长度或可接纳吞吐。',
                    '可选capacity_bytes按完整页取整；create/append在修改前计算新页与共享尾页COW所需页，容量不足整项拒绝，不改变长度、页表、引用或复制账。fork本身无需新KV页，但后续写入仍可能拒绝；不预留未来增长、不自动抢占或排队重试。',
                    'fork假设相同token及计算状态，可共享KV；不同adapter/权重/位置语义不能仅凭文字前缀相同复用。未模拟换出、重算、缓存淘汰或实际vLLM块记录。',
                ])
