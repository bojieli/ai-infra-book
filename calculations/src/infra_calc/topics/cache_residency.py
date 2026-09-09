"""Immutable prefix-page residency: same-tier unions and cross-tier copies."""
from fractions import Fraction
from ..sources import model_config,provenance
from ..units import positive_int
from .state import calculate as state_calculate


def calculate(model='qwen3-8b',page_tokens=16,intervals=None,capacities=None):
    positive_int(page_tokens,'page_tokens')
    config=model_config(model)
    if config['model_type'] not in ('qwen3','qwen3_moe'):
        raise ValueError('Immutable full GQA pages required; hybrid states need another identity model')
    unit=state_calculate(model,page_tokens)['summary']['kv_bytes_per_token_per_request']
    capacities=dict(HBM=512*1024**2,DRAM=1024**3,SSD=4*1024**3) if capacities is None else capacities
    if not isinstance(capacities,dict) or not capacities:raise ValueError('Supply tier capacity budgets')
    for tier,size in capacities.items():
        if not isinstance(tier,str) or not tier:raise ValueError('Tier names must be nonempty strings')
        positive_int(size,'tier capacity',allow_zero=True)
    intervals=([
        dict(id='a-short',tier='HBM',prefix_identity='A',tokens=1024,start_ns=0,end_ns=10*10**9),
        dict(id='a-long',tier='HBM',prefix_identity='A',tokens=2048,start_ns=5*10**9,end_ns=15*10**9),
        dict(id='b',tier='HBM',prefix_identity='B',tokens=512,start_ns=2*10**9,end_ns=6*10**9),
        dict(id='a-host',tier='DRAM',prefix_identity='A',tokens=2048,start_ns=8*10**9,end_ns=30*10**9),
        dict(id='a-disk',tier='SSD',prefix_identity='A',tokens=2048,start_ns=12*10**9,end_ns=60*10**9),
    ] if intervals is None else intervals)
    if not isinstance(intervals,list) or not intervals:raise ValueError('Supply nonempty residency intervals')
    ids=set();boundaries=set()
    for row in intervals:
        if set(row)!={'id','tier','prefix_identity','tokens','start_ns','end_ns'}:raise ValueError('Unexpected interval fields')
        if not isinstance(row['id'],str) or not row['id'] or row['id'] in ids:raise ValueError('Distinct nonempty interval IDs required')
        ids.add(row['id'])
        if row['tier'] not in capacities or not isinstance(row['prefix_identity'],str) or not row['prefix_identity']:raise ValueError('Unknown tier or empty prefix identity')
        for name in ('tokens','start_ns','end_ns'):positive_int(row[name],name,allow_zero=name!='tokens')
        if row['end_ns']<=row['start_ns'] or row['tokens']%page_tokens:raise ValueError('Positive half-open lifetime and complete pages required')
        state_calculate(model,row['tokens'])
        boundaries.update((row['start_ns'],row['end_ns']))
    points=sorted(boundaries);segments=[]
    totals={tier:dict(tier=tier,capacity_bytes=capacity,peak_bytes=0,physical_byte_nanoseconds=0,
                      logical_byte_nanoseconds=0,over_capacity_nanoseconds=0)
            for tier,capacity in capacities.items()}
    unique_area=0;physical_area=0;peak_all=0
    for start,end in zip(points,points[1:]):
        active=[row for row in intervals if row['start_ns']<=start<row['end_ns']]
        global_prefix={};tier_bytes={};logical_bytes={}
        for tier in capacities:
            prefix={};logical=0
            for row in active:
                if row['tier']!=tier:continue
                identity=row['prefix_identity'];n=row['tokens']
                prefix[identity]=max(prefix.get(identity,0),n)
                global_prefix[identity]=max(global_prefix.get(identity,0),n)
                logical+=n*unit
            physical=sum(prefix.values())*unit
            tier_bytes[tier]=physical;logical_bytes[tier]=logical
            result=totals[tier];duration=end-start
            result['peak_bytes']=max(result['peak_bytes'],physical)
            result['physical_byte_nanoseconds']+=physical*duration
            result['logical_byte_nanoseconds']+=logical*duration
            if physical>result['capacity_bytes']:result['over_capacity_nanoseconds']+=duration
        all_physical=sum(tier_bytes.values());global_unique=sum(global_prefix.values())*unit
        unique_area+=global_unique*(end-start);physical_area+=all_physical*(end-start)
        peak_all=max(peak_all,all_physical)
        segments.append(dict(start_ns=start,end_ns=end,tier_physical_bytes=tier_bytes,
                             tier_logical_bytes=logical_bytes,all_tier_physical_bytes=all_physical,
                             globally_unique_page_bytes=global_unique))
    rows=[]
    for value in totals.values():
        rows.append(dict(**value,physical_byte_seconds_exact=str(Fraction(value['physical_byte_nanoseconds'],10**9)),
                         logical_byte_seconds_exact=str(Fraction(value['logical_byte_nanoseconds'],10**9)),
                         shared_byte_seconds_saved_exact=str(Fraction(value['logical_byte_nanoseconds']-value['physical_byte_nanoseconds'],10**9))))
    return dict(schema_version=1,calculation='cache-residency',scenario=dict(model=model,page_tokens=page_tokens,intervals=intervals,capacities=capacities),sources=provenance(model),
                summary=dict(kv_bytes_per_token=unit,kv_page_bytes=unit*page_tokens,
                             all_tier_peak_physical_bytes=peak_all,
                             all_tier_physical_byte_seconds_exact=str(Fraction(physical_area,10**9)),
                             globally_unique_byte_seconds_exact=str(Fraction(unique_area,10**9)),
                             cross_tier_copy_byte_seconds_exact=str(Fraction(physical_area-unique_area,10**9)),
                             all_tiers_capacity_feasible=all(row['over_capacity_nanoseconds']==0 for row in rows)),
                residency_tiers=rows,residency_segments=segments,
                assumptions=[
                    '官方完整GQA BF16页容量，interval从驻留已完成到最后释放，[start,end)端点释放先于分配。只接纳完整页，部分页写入／COW及混合递推状态未模拟。',
                    'prefix_identity声明同一不可变物理页序列及相同模型版本／adapter／格式／执行状态身份，长度较长者共享原完整页。同token文本并不足以证明KV逐位相同，身份必须由调用方确认；不同identity不猜测共享祖先。',
                    '同tier同identity的同时驻留按最大前缀长度取并集，跨tier各保留一份实体，不能跨HBM/DRAM/SSD消除物理副本；全局唯一量仅为比较基准。',
                    '区间与净容量为教学输入，不是实际缓存事件。超容量时保留需求并标记超预算时长，不隐式驱逐或声称部署可运行；未计metadata、allocator、文件padding或备份副本。',
                    'byte-seconds对实际声明驻留积分，空闲间隔不计。没有写入／迁移事件，不从容量变化推断写入字节、磁盘IO、命中率或取回性能。',
                ])
