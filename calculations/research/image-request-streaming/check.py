"""Independent hand substitution, DAG and resource conservation checks."""
from fractions import Fraction as F
from pathlib import Path
import json
import calculate as candidate

checks=0

def require(condition):
    global checks
    assert condition
    checks+=1


def audit(result):
    events=result['events'];by_id={e['id']:e for e in events}
    require(len(events)==len(by_id))
    resources={}
    for e in events:
        start,end,duration=(F(e[k]) for k in ('start_seconds_exact','end_seconds_exact','duration_seconds_exact'))
        require(end-start==duration and start>=0 and duration>=0)
        for name in e['dependencies']:require(start>=F(by_id[name]['end_seconds_exact']))
        if e['resource'] is not None:resources.setdefault(e['resource'],[]).append((start,end))
    for intervals in resources.values():
        for previous,current in zip(sorted(intervals),sorted(intervals)[1:]):require(previous[1]<=current[0])
    summary=result['summary'];scenario=result['scenario'];chunks=scenario['chunks']
    require(sum(e.get('bytes',0) for e in events if e['resource']=='uplink')==sum(c['input_bytes'] for c in chunks)==summary['input_file_bytes'])
    require(sum(e.get('bytes',0) for e in events if e['resource']=='downlink')==summary['total_downlink_bytes'])
    for i,c in enumerate(chunks):
        require(F(by_id[f'upload.{i}']['duration_seconds_exact'])==F(8*c['input_bytes'],F(scenario['upload_bits_per_second'])))
        require(F(by_id[f'input_arrival.{i}']['end_seconds_exact'])-F(by_id[f'upload.{i}']['end_seconds_exact'])==F(scenario['forward_propagation_seconds']))
    for e in events:
        if e['id'].startswith('arrival.'):
            require(F(e['duration_seconds_exact'])==F(scenario['reverse_propagation_seconds']))
    if scenario['mode']=='whole_image':
        uploaded=max(F(by_id[f'input_arrival.{i}']['end_seconds_exact']) for i in range(len(chunks)))
        encoded=max(F(by_id[f'encode.{i}']['end_seconds_exact']) for i in range(len(chunks)))
        require(all(F(by_id[f'process.{i}']['start_seconds_exact'])>=uploaded for i in range(len(chunks))))
        require(all(F(by_id[f'download.final.{i}']['start_seconds_exact'])>=encoded for i in range(len(chunks))))
    require(F(summary['complete_final_image_seconds_exact'])==max(F(by_id[f'arrival.final.{i}']['end_seconds_exact']) for i in range(len(chunks)))+F(scenario['final_assembly_seconds']))
    if scenario['preview'] is None:require(summary['preview_ready_seconds_exact'] is None)
    else:require(summary['preview_ready_seconds_exact']==by_id['arrival.preview']['end_seconds_exact'])
    require(summary['preview_is_complete_final_image'] is False)

results=candidate.build_results()
expected={'whole_image-without-preview':('64/5',None),'whole_image-with-preview':('257/20','1229/100'),
          'independent_blocks-without-preview':('309/25',None),'independent_blocks-with-preview':('309/25','108/25')}
for name,result in results.items():
    audit(result);final,preview=expected[name]
    require(result['summary']['complete_final_image_seconds_exact']==final)
    require(result['summary']['preview_ready_seconds_exact']==preview)
# Tiny independent hand schedule: uploads[0,1],[1,2], processes[1,2],[2,3].
# No preview: two 2-byte downloads[2,4],[4,6]. Preview3 bytes at t2
# wins ready-time tie, downloads[2,5]; final blocks[5,7],[7,9].
chunks=[dict(input_bytes=1,output_bytes=2,process_seconds='1',encode_seconds='0',required_inputs=[i]) for i in range(2)]
args=dict(chunks=chunks,mode='independent_blocks',independent_blocks_authorized=True,upload_bits_per_second=8,download_bits_per_second=8,forward_propagation_seconds='0',reverse_propagation_seconds='0')
p=dict(after_processed_chunk=0,bytes=3,encode_seconds='0',quality_contract='partial preview')
a=candidate.calculate(**args);b=candidate.calculate(**args,preview=p)
audit(a);audit(b)
require(a['summary']['complete_final_image_seconds_exact']=='6')
require(b['summary']['complete_final_image_seconds_exact']=='9')
require(b['summary']['preview_ready_seconds_exact']=='5')
# Single-block modes are equal; one forward/reverse delay regardless of block
# count is on the last dependency path, not serialized into link resource use.
for forward,reverse in (('0','0'),('1/3','2/3'),('5','7')):
    one=[chunks[0]]
    for mode in ('whole_image','independent_blocks'):
        r=candidate.calculate(**{**args,'chunks':one,'mode':mode,'forward_propagation_seconds':forward,'reverse_propagation_seconds':reverse})
        audit(r);require(F(r['summary']['complete_final_image_seconds_exact'])==4+F(forward)+F(reverse))
# Exhaustively recompute final completion from an independent scalar recurrence
# for 3 blocks, no preview. Includes upload/server/downlink bottlenecks.
for up in (8,16,80):
 for down in (8,16,80):
  for work in ('0','1/2','5'):
   cs=[dict(input_bytes=i+1,output_bytes=3-i,process_seconds=work,encode_seconds='1/7',required_inputs=[i]) for i in range(3)]
   for mode in ('whole_image','independent_blocks'):
    r=candidate.calculate(chunks=cs,mode=mode,independent_blocks_authorized=True,upload_bits_per_second=up,download_bits_per_second=down,forward_propagation_seconds='1/3',reverse_propagation_seconds='2/3')
    audit(r)
    arrivals=[F(8*sum(c['input_bytes'] for c in cs[:i+1]),up)+F(1,3) for i in range(3)]
    finish=[];server=F(0)
    for i in range(3):
        server=max(server,max(arrivals) if mode=='whole_image' else arrivals[i])+F(work)+F(1,7);finish.append(server)
    link=F(0)
    for i in range(3):link=max(link,max(finish) if mode=='whole_image' else finish[i])+F(8*cs[i]['output_bytes'],down)
    require(F(r['summary']['complete_final_image_seconds_exact'])==link+F(2,3))
invalid=[dict(mode='independent_blocks'),dict(mode='other'),dict(chunks=[]),dict(upload_bits_per_second=0),dict(reverse_propagation_seconds=-1),dict(quality_contract=''),dict(preview={}),dict(preview={**p,'after_processed_chunk':3}),dict(preview={**p,'bytes':0}),dict(preview={**p,'quality_contract':''}),dict(mode='independent_blocks',independent_blocks_authorized=True,chunks=[{**chunks[0],'required_inputs':[0,1]},chunks[1]])]
for args_bad in invalid:
    try:candidate.calculate(**args_bad)
    except ValueError:checks+=1
    else:raise AssertionError(args_bad)
report=dict(status='pass',checks=checks,independent_grid_cases=54,invalid_inputs_rejected=len(invalid),
    evidence=['Exact default hand values','DAG dependencies and serial resource nonoverlap','Byte conservation including additional preview','Tiny preview contention increases final6s to9s','Single-block equivalence and asymmetric one-way propagation','Independent max-plus recurrence across uplink/server/downlink bottlenecks'],limitations=['Algebraic scheduling checks only; independence and quality are supplied assertions, not model or codec tests.'])
Path(__file__).with_name('check-result.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
