"""Archived matched CPU training windows: no save, synchronous DCP, async DCP."""
import hashlib
import json
from statistics import median

from ..sources import PROJECT


MODES = ('none', 'sync', 'async')


def read_records():
    lock = json.loads((PROJECT/'configs/checkpoint-baseline.lock.json').read_text())
    raw = {}
    for entry in lock['files']:
        data = (PROJECT/entry['file']).read_bytes()
        if len(data) != entry['bytes'] or hashlib.sha256(data).hexdigest() != entry['sha256']:
            raise ValueError(f"Archived checkpoint evidence changed: {entry['file']}")
        raw[entry['file'].split('sources/checkpoint-baseline/',1)[1]] = data
    sources = [dict(file=e['file'],url='../../'+e['origin'],sha256=e['sha256']) for e in lock['files']
               if e['file'].endswith(('run.py','PROTOCOL.md','order.json','original-manifest.json'))]
    return raw, sources


def calculate():
    raw,sources = read_records()
    prefix='results/run-v1/'
    order=json.loads(raw[prefix+'order.json'])
    if len(order)!=15 or {(x['trial'],x['mode']) for x in order}!={(t,m) for t in range(5) for m in MODES}:
        raise ValueError('Expected five matched trials and three modes')
    source_hash=hashlib.sha256(raw['run.py']).hexdigest()
    rows=[];states=[];snapshots=[];losses=[]
    for position,item in enumerate(order):
        record=json.loads(raw[prefix+item['path']+'/raw.json'])
        mode=record['mode']
        if (record['trial'],mode)!=(item['trial'],item['mode']) or record['status']!='passed':
            raise ValueError('Trial identity/status mismatch')
        if record['source_sha256']!=source_hash or (record['device'],record['threads'],record['torch'])!=('cpu',1,'2.10.0+cu128'):
            raise ValueError('Fixed execution source or environment mismatch')
        events={e['event']:e['t_s'] for e in record['events']}
        if len(events)!=len(record['events']):raise ValueError('Duplicate lifecycle events')
        a,b,c,d=(events[k] for k in ('window_start','training_start','training_end','window_end'))
        if not a<=b<c<=d:raise ValueError('Training/window ordering mismatch')
        steps=record['steps']
        if [s['step'] for s in steps]!=list(range(4,24)):raise ValueError('Same twenty training steps required')
        previous=b
        for step in steps:
            if not previous<=step['start_s']<step['end_s']<=c:raise ValueError('Step outside training window')
            previous=step['end_s']
        states.append(record['final_state']);snapshots.append(record['expected_snapshot']);losses.append([s['loss'] for s in steps])
        api=stage=write=commit_latency=overlap=exposed=None
        if mode=='none':
            if record['checkpoint_files'] or record['restored_snapshot'] is not None or 'save_call' in events:
                raise ValueError('No-save control unexpectedly saved')
        else:
            if record['restored_snapshot']!=record['expected_snapshot']:raise ValueError('Restored snapshot hash mismatch')
            if not a<=events['save_call']<events['save_return']<=b:raise ValueError('Save API ordering mismatch')
            if not events['save_call']<=events['write_start']<events['write_end']<=events['commit_start']<=events['commit_end']<=d:
                raise ValueError('Writer commit ordering mismatch')
            api=events['save_return']-events['save_call']
            write=events['write_end']-events['write_start']
            commit_latency=events['commit_end']-events['save_call']
            overlap=max(0,min(c,events['write_end'])-max(b,events['write_start']))
            exposed=max(0,events['commit_end']-c)
            if mode=='sync' and events['commit_end']>events['save_return']:raise ValueError('Sync return before commit')
            if mode=='async':
                if not events['save_call']<=events['stage_start']<events['stage_end']<=events['save_return']:
                    raise ValueError('Async staging ordering mismatch')
                if not max(c,events['commit_end'])<=events['future_observed_complete']<=d:
                    raise ValueError('Future observation ordering mismatch')
                stage=events['stage_end']-events['stage_start']
        for file in record['checkpoint_files']:
            data=raw[prefix+item['path']+'/'+file['path']]
            if len(data)!=file['bytes'] or hashlib.sha256(data).hexdigest()!=file['sha256']:
                raise ValueError('Actual checkpoint file differs from raw report')
        rows.append(dict(trial=item['trial'],mode=mode,execution_order=position,
                         window_seconds=d-a,training_seconds=c-b,api_seconds=api,stage_seconds=stage,
                         writer_seconds=write,commit_from_call_seconds=commit_latency,
                         writer_training_overlap_seconds=overlap,commit_after_training_seconds=exposed,
                         window_tail_after_training_seconds=d-c,
                         checkpoint_file_bytes=sum(f['bytes'] for f in record['checkpoint_files']),
                         process_rss_highwater_delta_kib=record['ru_maxrss_after_kib']-record['ru_maxrss_before_kib']))
    if not all(s==states[0] for s in states) or not all(s==snapshots[0] for s in snapshots) or not all(x==losses[0] for x in losses):
        raise ValueError('Matched final state, snapshot or per-step loss changed')
    pairs=[]
    for trial in range(5):
        group={r['mode']:r for r in rows if r['trial']==trial}
        pairs.append(dict(trial=trial,
                          async_minus_none_window_seconds=group['async']['window_seconds']-group['none']['window_seconds'],
                          sync_minus_none_window_seconds=group['sync']['window_seconds']-group['none']['window_seconds'],
                          async_minus_none_training_seconds=group['async']['training_seconds']-group['none']['training_seconds'],
                          sync_minus_async_window_seconds=group['sync']['window_seconds']-group['async']['window_seconds']))
    metrics=['window_seconds','training_seconds','api_seconds','stage_seconds','writer_seconds','commit_from_call_seconds','writer_training_overlap_seconds','commit_after_training_seconds']
    summaries=[]
    for mode in MODES:
        group=[r for r in rows if r['mode']==mode]
        summaries.append(dict(mode=mode,**{key:median(r[key] for r in group) if all(r[key] is not None for r in group) else None for key in metrics}))
    return dict(schema_version=1,calculation='checkpoint-baseline',scenario=dict(experiment='ch10/10-07/save-baseline',trials=5,training_steps=20),sources=sources,
                checkpoint_baseline_runs=rows,checkpoint_baseline_modes=summaries,checkpoint_baseline_pairs=pairs,
                summary=dict(runs=15,restored_checkpoints=10,archived_evidence_files=len(raw),
                             all_reported_final_states_equal=True,all_reported_snapshots_equal=True,all_per_step_losses_equal=True,
                             median_paired_async_minus_none_window_seconds=median(p['async_minus_none_window_seconds'] for p in pairs),
                             median_paired_async_minus_none_training_seconds=median(p['async_minus_none_training_seconds'] for p in pairs),
                             median_paired_sync_minus_async_window_seconds=median(p['sync_minus_async_window_seconds'] for p in pairs)),
                assumptions=[
                    '真实CPU单线程PyTorch2.10.0+cu128 DCP，1024×1024 Linear/Tanh/Dropout与AdamW，合成16行输入。非Qwen、非GPU训练性能；每模式五个独立进程，轮内顺序预定随机化。',
                    '核验执行源码、原始计时、十份实际检查点文件SHA与报告载荷；本计算未调用torch重新加载，恢复正确及全状态哈希来自封存运行的实际加载记录，不能冒充本轮重新执行训练。',
                    '三模式同20步、逐步loss及第23步参数/Adam/RNG/游标哈希相同。窗口从保存前到训练与保存均结束，初始化、前3步、哈希与恢复校验在窗口之外。',
                    'API暂停、训练、writer区间与完整窗口分别报告，重叠量是同进程时钟交集，不能将这些区间相加。future_observed_complete只是主线程观察，不是后台真实就绪时间；提交使用writer commit_end。',
                    'none的API/stage等为null，sync未经过stage钩子也为null，不把未测当零。每轮差值后取中位数，与两组中位数相减分开。五次样本不推出p95、显著性或独立优化收益。',
                    'sync_files=True、缓存未清除；不把文件字节除writer区间当物理磁盘带宽。进程RSS高水位差包括训练/库分配，不是独立staging峰值；未隔离首次准备、CPU争用及文件系统缓存因素。',
                ])
