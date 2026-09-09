"""Read-only applied patch/checkbox/Omni paragraph reconciliation."""
from pathlib import Path
import ast,hashlib,json,re,sys
HERE=Path(__file__).resolve().parent;CALC=HERE.parents[1];BOOK=CALC.parent
proposal=json.loads((HERE/'suggested.patch.json').read_text());current=(CALC/'PLAN.md').read_text();reversed_text=current
followup=json.loads((HERE/'c77-public-followup.json').read_text())
assert reversed_text.count(followup['new'])==1
reversed_text=reversed_text.replace(followup['new'],followup['old'])
for row in proposal['replacements']:
 assert reversed_text.count(row['new'])==1
 reversed_text=reversed_text.replace(row['new'],row['old'])
sha=lambda s:hashlib.sha256(s.encode()).hexdigest()
original=None;appended=None
for pos in [len(reversed_text)]+[i+1 for i,c in enumerate(reversed_text) if c=='\n']:
 if sha(reversed_text[:pos])==proposal['expected_sha256']:original=reversed_text[:pos];appended=reversed_text[pos:];break
assert original is not None,'Reverse patch plus appended progress cannot reconstruct original'
pattern=r'^- \[([ x])\] ([HCF]\d+)\b'
oldboxes=re.findall(pattern,original,re.M);newboxes=re.findall(pattern,current,re.M);assert oldboxes==newboxes
assert appended.strip().startswith('C77前处理子进度：') and not re.search(pattern,appended,re.M)
module=ast.parse((CALC/'src/infra_calc/outline.py').read_text());calls=[]
for node in ast.walk(module):
 if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='insert' and len(node.args)>=4:
  try:args=[ast.literal_eval(a) for a in node.args[:4]]
  except (ValueError,TypeError):continue
  if args[1]=='C77-omni-pcm-preprocess':calls.append(args)
assert len(calls)==1
file,tag,paragraph,anchor=calls[0];outline=(BOOK/'outlines'/file).read_text();assert anchor=='> **实验 12-3' and outline.count(anchor)==1
frozen=json.loads((CALC/'research/omni-audio-preprocess/results/omni-pcm-1s.json').read_text())
sys.path.insert(0,str(CALC/'src'))
from infra_calc.topics import omni_audio_preprocess
public=omni_audio_preprocess.calculate();assert public['summary']==frozen['summary'] and public['geometry']==frozen['geometry']
expected={k:frozen['summary'][k] for k in ['matrix_flops','known_scalar_flops','source_operand_read_bytes','source_operand_write_bytes','encoder_input_bytes']}
for value in expected.values():assert f'{value:,}' in paragraph
assert '100个有效mel帧' in paragraph and '13个位置' in paragraph
assert paragraph in outline and outline.index(tag)<outline.index(anchor)
output=dict(c77_public_followup_verified=True,applied_replacements=len(proposal['replacements']),original_plan_exactly_recovered_sha256=sha(original),current_plan_sha256=sha(current),all_checkbox_states_exactly_preserved=True,checkbox_count=len(oldboxes),only_added_tail=appended.strip(),outline_file=file,anchor=anchor,anchor_line=outline[:outline.index(anchor)].count('\n')+1,one_second_values=expected,public_candidate_summary_and_geometry_equal=True,generated_paragraph_present=tag in outline,generator_paragraph_and_numeric_validation=True)
(HERE/'application-verification.json').write_text(json.dumps(output,indent=2,ensure_ascii=False)+'\n');print(json.dumps(output,indent=2,ensure_ascii=False))
