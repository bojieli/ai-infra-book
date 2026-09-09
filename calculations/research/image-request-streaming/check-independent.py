"""Independent task-DAG earliest-start scheduler for the streaming candidate."""
from fractions import Fraction as F
from pathlib import Path
import importlib.util,json

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('stream_candidate',HERE/'calculate.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def independently_schedule(s):
    tasks={}
    def add(name,resource,duration,deps,priority=0):
        tasks[name]=dict(resource=resource,duration=F(duration),deps=deps,priority=priority,index=len(tasks))
    chunks=s['chunks'];preview=s['preview'];whole=s['mode']=='whole_image'
    add('prepare','client',s['preparation_seconds'],[])
    add('connect','client',s['connection_seconds'],['prepare'])
    for i,c in enumerate(chunks):
        add(f'upload.{i}','uplink',F(8*c['input_bytes'])/F(s['upload_bits_per_second']),['connect'] if i==0 else [f'upload.{i-1}'])
        add(f'input_arrival.{i}',None,s['forward_propagation_seconds'],[f'upload.{i}'])
    previous=None
    for i,c in enumerate(chunks):
        deps=[f'input_arrival.{j}' for j in (range(len(chunks)) if whole else c['required_inputs'])]
        if previous is not None:deps.append(previous)
        add(f'process.{i}','server',c['process_seconds'],deps)
        add(f'encode.{i}','server',c['encode_seconds'],[f'process.{i}'])
        previous=f'encode.{i}'
        if preview is not None and preview['after_processed_chunk']==i:
            add('preview_encode','server',preview['encode_seconds'],[previous]+[f'process.{j}' for j in range(i+1)])
            previous='preview_encode'
    for i,c in enumerate(chunks):
        deps=[f'encode.{j}' for j in range(len(chunks))] if whole else [f'encode.{i}']
        add(f'download.final.{i}','downlink',F(8*c['output_bytes'])/F(s['download_bits_per_second']),deps,2+i)
        add(f'arrival.final.{i}',None,s['reverse_propagation_seconds'],[f'download.final.{i}'])
    if preview is not None:
        add('download.preview','downlink',F(8*preview['bytes'])/F(s['download_bits_per_second']),['preview_encode'],1)
        add('arrival.preview',None,s['reverse_propagation_seconds'],['download.preview'])
    add('final_usable','client',s['final_assembly_seconds'],[f'arrival.final.{i}' for i in range(len(chunks))])
    done={};free={};pending=dict(tasks)
    while pending:
        ready=[]
        for name,t in pending.items():
            if all(d in done for d in t['deps']):
                release=max((done[d][1] for d in t['deps']),default=F(0))
                begin=max(release,free.get(t['resource'],F(0))) if t['resource'] else release
                # Downlink is FIFO by release, preview wins only equal releases.
                ready.append((begin,0 if t['resource']!='downlink' else 1,
                              release,t['priority'],t['index'],name))
        assert ready,'DAG cycle'
        *_,name=min(ready);t=pending.pop(name)
        release=max((done[d][1] for d in t['deps']),default=F(0))
        begin=max(release,free.get(t['resource'],F(0))) if t['resource'] else release
        finish=begin+t['duration'];done[name]=(begin,finish)
        if t['resource']:free[t['resource']]=finish
    return done

cases=[]
for mode in ('whole_image','independent_blocks'):
 for up,down in ((20_000_000,100_000_000),(800_000_000,8_000_000)):
  for boundary in (None,0,2):
   for propagation in (('1/20','1/20'),('3/4','5/4')):
    preview=None if boundary is None else dict(after_processed_chunk=boundary,bytes=2_000_000,encode_seconds='3/20',quality_contract='partial-preview quality, not final')
    cases.append(dict(mode=mode,independent_blocks_authorized=mode=='independent_blocks',
       upload_bits_per_second=up,download_bits_per_second=down,
       forward_propagation_seconds=propagation[0],reverse_propagation_seconds=propagation[1],
       preparation_seconds='1/10',connection_seconds='1/5',final_assembly_seconds='1/8',preview=preview))
# Zero-duration encode/processing tests release ties and preview priority.
for mode in ('whole_image','independent_blocks'):
 cases.append(dict(mode=mode,independent_blocks_authorized=mode=='independent_blocks',
    chunks=[dict(input_bytes=1,output_bytes=1,process_seconds='0',encode_seconds='0',required_inputs=[i]) for i in range(3)],
    upload_bits_per_second=8,download_bits_per_second=8,forward_propagation_seconds='0',reverse_propagation_seconds='0',
    preview=dict(after_processed_chunk=0,bytes=1,encode_seconds='0',quality_contract='preview only')))
results=[]
for args in cases:
    r=m.calculate(**args);expected=independently_schedule(r['scenario'])
    observed={e['id']:e for e in r['events']}
    assert set(expected)==set(observed)
    for name,(start,end) in expected.items():
        e=observed[name]
        assert (F(e['start_seconds_exact']),F(e['end_seconds_exact']))==(start,end),(args,name,(start,end),e)
        assert F(e['duration_seconds_exact'])==end-start
        assert all(F(observed[d]['end_seconds_exact'])<=start for d in e['dependencies'])
    for resource in ('client','uplink','server','downlink'):
        intervals=sorted((F(e['start_seconds_exact']),F(e['end_seconds_exact'])) for e in observed.values() if e['resource']==resource and F(e['duration_seconds_exact']))
        assert all(a[1]<=b[0] for a,b in zip(intervals,intervals[1:])),resource
    summary=r['summary'];preview=r['scenario']['preview']
    assert F(summary['complete_final_image_seconds_exact'])==expected['final_usable'][1]
    assert summary['preview_ready_seconds_exact']==(None if preview is None else str(expected['arrival.preview'][1]))
    assert sum(e.get('bytes',0) for e in observed.values() if e['resource']=='uplink')==summary['input_file_bytes']
    assert sum(e.get('bytes',0) for e in observed.values() if e['resource']=='downlink')==summary['total_downlink_bytes']
    assert summary['total_downlink_bytes']==summary['final_file_bytes']+summary['additional_preview_bytes']
    assert summary['measured_seconds'] is None and not summary['preview_is_complete_final_image']
    results.append(dict(scenario=args,summary=summary))
# Defaults preserve serial budget and reveal overlap only after authorization.
a=m.calculate();b=m.calculate(mode='independent_blocks',independent_blocks_authorized=True)
assert a['summary']['complete_final_image_seconds_exact']=='64/5'
assert b['summary']['complete_final_image_seconds_exact']=='309/25'
for field in ('input_file_bytes','final_file_bytes'):assert a['summary'][field]==b['summary'][field]
for resource in ('uplink','server','downlink'):
 assert sum(F(e['duration_seconds_exact']) for e in a['events'] if e['resource']==resource)==sum(F(e['duration_seconds_exact']) for e in b['events'] if e['resource']==resource)
preview=dict(after_processed_chunk=0,bytes=500_000,encode_seconds='1/20',quality_contract='partial preview')
p=m.calculate(preview=preview)
assert p['summary']['complete_final_image_seconds_exact']=='257/20' # +0.05s server work
p2=m.calculate(mode='independent_blocks',independent_blocks_authorized=True,preview=preview)
assert p2['summary']['complete_final_image_seconds_exact']==b['summary']['complete_final_image_seconds_exact']
# Large preview can occupy a shared downlink and delay final delivery.
no=m.calculate(upload_bits_per_second=800_000_000,download_bits_per_second=8_000_000)
yes=m.calculate(upload_bits_per_second=800_000_000,download_bits_per_second=8_000_000,
    preview=dict(after_processed_chunk=0,bytes=10_000_000,encode_seconds='0',quality_contract='partial preview'))
assert F(yes['summary']['complete_final_image_seconds_exact'])>F(no['summary']['complete_final_image_seconds_exact'])
invalid=[dict(mode='independent_blocks'),dict(quality_contract=''),dict(upload_bits_per_second=0),
 dict(forward_propagation_seconds=True),dict(reverse_propagation_seconds='-1')]
for deps in ([0,1],[1]):
 chunks=m.default_chunks();chunks[0]['required_inputs']=deps
 invalid.append(dict(mode='independent_blocks',independent_blocks_authorized=True,chunks=chunks))
for args in invalid:
 try:m.calculate(**args)
 except ValueError:pass
 else:raise AssertionError(args)
(HERE/'check-independent.json').write_text(json.dumps(dict(status='passed',dag_scenarios=len(results),
 invalid_cases=len(invalid),default_serial='64/5',default_independent='309/25',
 preview_serial='257/20',preview_independent='309/25',cases=results),indent=2)+'\n')
print(f'PASS: {len(results)} independent DAG/resource scenarios;7 invalid cases; equal-work modes; preview delay/no-delay cases.')
