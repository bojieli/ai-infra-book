"""Check observed ordering and summarize API/staging/write completion times."""
import hashlib
import json
from pathlib import Path

root=Path(__file__).parent/'results'
outcomes=json.loads((root/'outcomes.json').read_text())
assert outcomes['source_sha256']==hashlib.sha256((root.parent/'run.py').read_bytes()).hexdigest()
rows=[]
for case in ['normal','fault']:
    events=[json.loads(line) for line in (root/case/'events.jsonl').read_text().splitlines()]
    for number in [1,2]:
        label=f'checkpoint-{number}'
        e={v['event']:v for v in events if v.get('checkpoint')==label}
        ts={k:v['monotonic_s'] for k,v in e.items()}
        assert ts['api_call']<=ts['stage_start']<=ts['stage_complete']<=ts['api_return']
        assert ts['write_start']<=ts['data_write_complete']<=ts['metadata_commit_enter']
        assert e['training_complete']['steps']==20
        row=dict(case=case,checkpoint=label,api_ms=1000*(ts['api_return']-ts['api_call']),
                 staging_ms=1000*(ts['stage_complete']-ts['stage_start']),
                 data_write_ms=1000*(ts['data_write_complete']-ts['write_start']),
                 api_return_future_done=e['api_return']['future_done'],
                 training_20_steps_ms=e['training_complete']['seconds']*1000)
        if case=='fault' and number==2:
            assert 'metadata_commit_complete' not in e and 'future_complete' not in e
            assert ts['api_return']<outcomes['fault']['sigkill_monotonic_s']
            assert ts['metadata_commit_enter']<outcomes['fault']['sigkill_monotonic_s']
            assert ts['training_complete']<outcomes['fault']['sigkill_monotonic_s']
            assert not (root/case/label/'.metadata').exists()
        else:
            assert ts['metadata_commit_enter']<=ts['metadata_commit_complete']<=ts['future_complete']
            assert (root/case/label/'.metadata').is_file()
            row['commit_from_call_ms']=1000*(ts['metadata_commit_complete']-ts['api_call'])
            # Future was awaited after 20 steps. This timestamp is observation,
            # not the instant at which the future internally became ready.
            row['await_observed_from_call_ms']=1000*(ts['future_complete']-ts['api_call'])
        rows.append(row)
assert outcomes['fault']['returncode']==-9
assert outcomes['fault']['recovered_cursor']==3
assert outcomes['fault']['incomplete_data_files']
assert outcomes['fault']['incomplete_load_error']['type']=='CheckpointException'
expected=json.loads((root/'fault/expected.json').read_text())
assert outcomes['fault']['recovered_hashes']==expected['checkpoint-1']
normal=json.loads((root/'normal/recovered.json').read_text())
expected=json.loads((root/'normal/expected.json').read_text())
for label,cursor in [('checkpoint-1',3),('checkpoint-2',23)]:
    assert normal[label]['hashes']==expected[label]
    assert normal[label]['cursor']==cursor
(root/'summary.json').write_text(json.dumps(dict(rows=rows,
    limitation='Injected metadata gate is not measured bandwidth; no power-loss durability or throughput baseline claimed.'),indent=2)+'\n')
for row in rows:print(json.dumps(row))
