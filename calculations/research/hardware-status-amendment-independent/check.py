"""Read-only catalog amendment and C22 scenario replay; outputs local evidence only."""
from pathlib import Path
import json,hashlib,sys,copy
HERE=Path(__file__).resolve().parent
CALC=HERE.parents[1]
sys.path.insert(0,str(CALC/'src'))
from infra_calc import topics
CAND=CALC/'research/stage-resource-bounds/public'
topics.__path__.insert(0,str(CAND/'src/infra_calc/topics'))
from infra_calc.topics import stage_resource_bounds as module
sha=lambda raw:hashlib.sha256(raw).hexdigest()
patch=json.loads((CALC/'research/vision-preprocess/hardware-prose.patch.json').read_text())
raw=(CALC/'configs/hardware.json').read_bytes();current=json.loads(raw);old=copy.deepcopy(current)
for row in patch['replacements']:
    keys=row['path'].strip('/').split('/');node=old
    for key in keys[:-1]:node=node[int(key)] if isinstance(node,list) else node[key]
    key=int(keys[-1]) if isinstance(node,list) else keys[-1]
    assert node[key]==row['new'],row['path']
    node[key]=row['old']
# Reconstruct the exact original serialization, not just equality to a claimed old object.
oldraw=(json.dumps(old,ensure_ascii=False,indent=2)+'\n').encode()
assert sha(oldraw)==patch['expected_sha256'],sha(oldraw)
claimed=json.loads((CALC/'research/hardware-status-cleanup/verification.json').read_text())
assert sha(raw)==claimed['current_sha256']
assert sha(oldraw)==claimed['previous_sha256']
assert old['devices'][45]['id']=='a800-40gb-active'
results=[]
for scene in json.loads((CAND/'book.append.json').read_text()):
    expected_path=CAND/'results'/(scene['id']+'.json')
    expected=json.loads(expected_path.read_text())
    observed=module.calculate(**{k:v for k,v in scene.items() if k!='id'})
    assert observed==expected,scene['id']
    results.append({'id':scene['id'],'full_result_exactly_equal':True,'frozen_result_sha256':sha(expected_path.read_bytes())})
from infra_calc.sources import records
source_rows=sorted([r for r in records() if r.get('model')=='hardware'],key=lambda r:(r['id'],r['file']))
source_hash=sha(json.dumps(source_rows,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())
acceptance=json.loads((CALC/'inventory/h07-source-review.json').read_text())
assert source_hash==acceptance['binding']['hardware_sources_subset_sha256']
assert sha(oldraw)==acceptance['binding']['hardware_sha256']
output={'hardware_source_rows':len(source_rows),'hardware_sources_subset_sha256':source_hash,'historical_H07_binding_retained':True,'old_catalog_sha256':sha(oldraw),'current_catalog_sha256':sha(raw),'reverse_three_prose_fields_reconstructs_original_bytes':True,'all_other_fields_and_sources_unchanged':True,'changed_paths':[r['path'] for r in patch['replacements']],'c22_module_sha256':sha(Path(module.__file__).read_bytes()),'scenarios':len(results),'exact_equal_scenarios':len(results),'results':results}
(HERE/'verification.json').write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps({k:v for k,v in output.items() if k!='results'},indent=2))
