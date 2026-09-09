import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parent;P=ROOT/'results/run-v1'
order=json.loads((P/'order.json').read_text());assert len(order)==15
reports=[];states=[]
for item in order:
    r=json.loads((P/item['path']/'raw.json').read_text());assert r['status']=='passed'
    assert r['source_sha256']==hashlib.sha256((ROOT/'run.py').read_bytes()).hexdigest()
    assert r['mode']==item['mode'] and r['trial']==item['trial']
    assert len(r['steps'])==20 and [s['step'] for s in r['steps']]==list(range(4,24))
    e={v['event']:v['t_s'] for v in r['events']}
    assert e['window_start']<=e['training_start']<e['training_end']<=e['window_end']
    if r['mode']!='none':
        assert r['restored_snapshot']==r['expected_snapshot']
        assert e['write_start']<=e['write_end']<=e['commit_start']<=e['commit_end']<=e['window_end']
    if r['mode']=='async':assert e['stage_start']<=e['stage_end']<=e['save_return']<=e['training_start']
    for f in r['checkpoint_files']:
        p=P/item['path']/f['path'];assert p.stat().st_size==f['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==f['sha256']
    states.append(r['final_state'])
    reports.append(dict(**item,window_s=e['window_end']-e['window_start'],training_s=e['training_end']-e['training_start'],api_s=e.get('save_return',0)-e.get('save_call',0),stage_s=e.get('stage_end',0)-e.get('stage_start',0),write_s=e.get('write_end',0)-e.get('write_start',0),post_training_wait_s=e['window_end']-e['training_end'],checkpoint_bytes=sum(f['bytes'] for f in r['checkpoint_files']),rss_highwater_increase_kib=r['ru_maxrss_after_kib']-r['ru_maxrss_before_kib']))
assert all(s==states[0] for s in states)
assert {(r['trial'],r['mode']) for r in reports}=={(t,m) for t in range(5) for m in ['none','sync','async']}
summary={m:{key:statistics.median(r[key] for r in reports if r['mode']==m) for key in ['window_s','training_s','api_s','stage_s','write_s','post_training_wait_s','checkpoint_bytes','rss_highwater_increase_kib']} for m in ['none','sync','async']}
result=dict(status='passed',runs=reports,medians=summary,all_final_states_equal=True,scope='Actual CPU single-thread DCP experiment; fresh files, filesystem cache uncontrolled, process highwater is not staging-only memory. No artificial delay or failure gate. Same20 training steps and final state.')
(ROOT/'results/summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(summary,indent=2))
