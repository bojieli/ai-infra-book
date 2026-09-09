"""Actual DCP metadata-gated process failure; incomplete commit stays unknown."""
import hashlib
import json
from ..sources import PROJECT


def read_records():
    lock=json.loads((PROJECT/'configs/checkpoint-fault.lock.json').read_text())
    raw={}
    for e in lock['files']:
        data=(PROJECT/e['file']).read_bytes()
        if len(data)!=e['bytes'] or hashlib.sha256(data).hexdigest()!=e['sha256']:
            raise ValueError('Checkpoint fault evidence hash mismatch')
        raw[e['file'].split('sources/checkpoint-fault/',1)[1]]=data
    sources=[dict(file=e['file'],url='../../'+e['origin'],sha256=e['sha256']) for e in lock['files']
             if e['file'].endswith(('run.py','raw-manifest.json','outcomes.json','environment.json'))]
    return raw,sources


def calculate():
    raw,sources=read_records()
    outcomes=json.loads(raw['results/outcomes.json'])
    source_hash=hashlib.sha256(raw['run.py']).hexdigest()
    environment=json.loads(raw['results/normal/environment.json'])
    if outcomes['source_sha256']!=source_hash or environment['source_sha256']!=source_hash:
        raise ValueError('Executed source differs from archived source')
    if (environment['torch'],environment['device'],environment['threads'])!=('2.10.0+cu128','cpu',1):
        raise ValueError('Unexpected actual environment')
    fault=outcomes['fault'];kill=fault['sigkill_monotonic_s']
    if outcomes['normal']['returncode']!=0 or fault['returncode']!=-9:
        raise ValueError('Unexpected process outcome')
    if fault['incomplete_load_error']['type']!='CheckpointException' or 'metadata is None' not in fault['incomplete_load_error']['message']:
        raise ValueError('Expected actual incomplete-load error')
    rows=[]
    for case in ('normal','fault'):
        events=[json.loads(line) for line in raw[f'results/{case}/events.jsonl'].splitlines()]
        expected=json.loads(raw[f'results/{case}/expected.json'])
        recovered=json.loads(raw['results/normal/recovered.json']) if case=='normal' else None
        for number,cursor in ((1,3),(2,23)):
            label=f'checkpoint-{number}'
            selected=[e for e in events if e.get('checkpoint')==label]
            e={x['event']:x for x in selected}
            if len(e)!=len(selected):raise ValueError('Duplicate lifecycle events')
            t={name:x['monotonic_s'] for name,x in e.items()}
            if not t['api_call']<=t['stage_start']<t['stage_complete']<=t['api_return']<t['training_complete']:
                raise ValueError('Snapshot/compute order mismatch')
            if not t['stage_complete']<=t['write_start']<t['data_write_complete']<=t['metadata_commit_enter']:
                raise ValueError('Writer ordering mismatch')
            if e['api_return']['future_done'] is not False or e['training_complete']['steps']!=20:
                raise ValueError('Expected unfinished API future and twenty completed steps')
            directory=f'results/{case}/{label}/'
            files={path[len(directory):]:data for path,data in raw.items() if path.startswith(directory)}
            incomplete=case=='fault' and number==2
            if incomplete:
                if '.metadata' in files or 'metadata_commit_complete' in e or 'future_complete' in e:
                    raise ValueError('Injected incomplete save unexpectedly committed')
                if not max(t['metadata_commit_enter'],t['training_complete'],t['api_return'])<kill:
                    raise ValueError('Kill must follow fault barrier and training')
                if sorted(files)!=sorted(fault['incomplete_data_files']):raise ValueError('Incomplete file inventory differs')
            else:
                if '.metadata' not in files or not t['metadata_commit_enter']<=t['metadata_commit_complete']<=t['future_complete']:
                    raise ValueError('Completed checkpoint lacks commit evidence')
                if case=='normal':
                    if recovered[label]['hashes']!=expected[label] or recovered[label]['cursor']!=cursor:
                        raise ValueError('Actual restored normal snapshot mismatch')
                elif fault['recovered_hashes']!=expected[label] or fault['recovered_cursor']!=cursor:
                    raise ValueError('Actual fallback restored snapshot mismatch')
            rows.append(dict(case=case,checkpoint=label,snapshot_cursor=cursor,completed_post_snapshot_steps=20,
                             api_seconds=t['api_return']-t['api_call'],stage_seconds=t['stage_complete']-t['stage_start'],
                             writer_seconds=t['data_write_complete']-t['write_start'],
                             commit_from_call_seconds=None if incomplete else t['metadata_commit_complete']-t['api_call'],
                             future_observed_from_call_seconds=None if incomplete else t['future_complete']-t['api_call'],
                             unfinished_observation_seconds=kill-t['api_call'] if incomplete else None,
                             training_seconds=e['training_complete']['seconds'],
                             metadata_present='.metadata' in files,data_file_bytes=sum(len(v) for k,v in files.items() if k!='.metadata'),
                             metadata_bytes=len(files.get('.metadata',b'')),actual_load_succeeded=not incomplete))
    return dict(schema_version=1,calculation='checkpoint-fault',scenario=dict(experiment='ch10/10-07',normal_processes=1,fault_processes=1),sources=sources,
                checkpoint_fault_rows=rows,
                summary=dict(archived_evidence_files=len(raw),completed_commits=3,incomplete_commits=1,
                             incomplete_load_error_type=fault['incomplete_load_error']['type'],
                             incomplete_data_bytes=rows[-1]['data_file_bytes'],fallback_recovered_cursor=fault['recovered_cursor'],
                             last_completed_training_cursor=43,completed_updates_after_recovery_point=40),
                assumptions=[
                    '真实CPU单线程PyTorch2.10.0+cu128 DCP，1024×1024 Linear/Tanh/Dropout与AdamW，快照cursor3/23后各训练20步。非Qwen/GPU性能；正常与故障各一进程，不能推出故障率或p95。',
                    '故障在第二份数据写完、metadata提交之前人为设置屏障，父进程等API返回和20步训练完成再SIGKILL。此阻塞区间不是慢存储或带宽测量，不估算有效写入带宽。',
                    '实际数据文件与metadata逐文件SHA核验；三份加载成功及一份拒绝来自封存实际torch加载记录，本CLI不反序列化或重新训练。只有正常分支记录完整环境，故障执行源码由同一监督器哈希及运行结构绑定。',
                    '未完成提交时间保留null，kill减api_call仅是未完成观察长度；future_complete是主线程等待后的观察，不当内部就绪时刻。文件已有字节不证明已提交，更不证明断电或远端复制持久性。',
                    '源程序固定前3步、两轮各20步，故障前完成cursor43、回到3需重做40次更新；没有下一步恢复训练或重新执行这40步的时间证据，不推ETTR。进程终止不代表断电、多rank或磁盘故障。',
                ])
