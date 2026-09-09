from pathlib import Path
import hashlib
import json
import sys

HERE = Path(__file__).resolve().parent
P = HERE.parent/'omni-audio-preprocess'
sys.path.insert(0,str(P))
import omni_audio_preprocess as m
new = (P/'omni_audio_preprocess.py').read_text()
old = new.replace('        12 * batch * filters,\n','        4 * batch * filters,\n').replace('        12 * batch,\n','        4 * batch,\n')
old = '\n'.join(line for line in old.split('\n') if not line.strip().startswith('index_output_bytes=') and 'note="Dimensional max produces int64 indices' not in line)
assert hashlib.sha256(old.encode()).hexdigest() == '077bc4ec20010b21df644573f55d1e249919b777287d1d2ce0ca6250b5d6d331'
namespace = {'__file__':str(P/'omni_audio_preprocess.py')}
exec(compile(old,'verified_original','exec'),namespace)
records=[]
for path in sorted((P/'results').glob('*.json')):
    new_result=json.loads(path.read_text())
    old_result=namespace['calculate'](**new_result['scenario'])
    b=len(new_result['scenario']['sample_lengths'])
    assert new_result['summary']['source_operand_write_bytes']-old_result['summary']['source_operand_write_bytes']==1032*b
    for key in old_result:
        if key not in ('summary','stages'):assert old_result[key]==new_result[key]
    for key in old_result['summary']:
        if key!='source_operand_write_bytes':assert old_result['summary'][key]==new_result['summary'][key]
    for x,y in zip(old_result['stages'],new_result['stages']):
        y=y.copy()
        if x['id'] in ('per_audio_time_max','per_audio_mel_max'):
            extra=y.pop('index_output_bytes');y.pop('note');y['write_bytes']-=extra
        assert x==y
    records.append({'scenario':path.name,'write_delta':1032*b,'all_other_fields_equal':True})
(HERE/'fix-verification.json').write_text(json.dumps({'reverse_patch_matches_original_sha':True,'new_sha':hashlib.sha256(new.encode()).hexdigest(),'scenarios':records},indent=2)+'\n')
