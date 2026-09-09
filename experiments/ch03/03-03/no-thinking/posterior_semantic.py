"""Post hoc semantic diagnosis only; never replaces registered strict JSON scoring."""
import json
import re
from pathlib import Path
from tasks import TASKS,answer,dp
R=Path(__file__).resolve().parent

def extract(text):
 text=text.rstrip()
 if text.rfind('<think>')>text.rfind('</think>'):
  return None,'unclosed_thinking_region'
 def unique_object(pairs):
  result={}
  for key,value in pairs:
   if key in result:raise ValueError('duplicate_json_keys')
   result[key]=value
  return result
 decoder=json.JSONDecoder(object_pairs_hook=unique_object)
 found=[];duplicate_keys=False
 for i,char in enumerate(text):
  if char!='{':continue
  try:
   obj,length=decoder.raw_decode(text[i:])
   if isinstance(obj,dict):found.append((i,i+length,obj))
  except json.JSONDecodeError:pass
  except ValueError:duplicate_keys=True
 if duplicate_keys:return None,'duplicate_json_keys'
 # Nested objects are part of their containing object, not independent answers.
 maximal=[item for item in found if not any(other[0]<item[0] and other[1]>=item[1] for other in found)]
 if len(maximal)!=1:return None,'no_complete_json_object' if not maximal else 'multiple_json_objects'
 start,end,obj=maximal[0]
 if set(obj)!={'count'} or type(obj['count']) is not int:return None,'not_exact_integer_count_object'
 tail=text[end:]
 if not tail.strip():return obj['count'],'accepted_bare_terminal_object'
 # Entire final fenced block must be exactly this object, with optional whitespace.
 for match in re.finditer(r'```(?:json)?[ \t]*\n(.*?)\n```',text,re.S):
  if match.end()!=len(text):continue
  body=match.group(1)
  if body.strip()==text[start:end]:
   return obj['count'],'accepted_terminal_json_fence'
 return None,'trailing_content_or_nonstandard_fence'

def main():
 raw=[json.loads(s) for s in (R/'results/raw.jsonl').read_text().splitlines()]
 assert len(raw)==24
 truth={t['id']:answer(t) for t in TASKS};assert all(dp(t)==truth[t['id']] for t in TASKS)
 rows=[];groups=[];summary={}
 for group in raw:
  values=[]
  for c in group['candidates']:
   value,reason=extract(c['text'])
   if value is not None:values.append(value)
   rows.append(dict(group=group['group'],trial=group['trial'],task=group['task'],policy=group['policy'],candidate=c['index'],extracted=value,reason=reason,numerically_correct=value==truth[group['task']] if value is not None else None,primary_format_compliant=c['value'] is not None,primary_value=c['value'],finish_reason=c['finish_reason']))
  selected=max(values,key=lambda v:values.count(v)) if values else None
  correct=selected==truth[group['task']]
  groups.append(dict(group=group['group'],policy=group['policy'],task=group['task'],trial=group['trial'],selected=selected,numerically_correct=correct,primary_selected=group['selected'],primary_correct=group['correct']))
  s=summary.setdefault(group['policy'],dict(groups=0,numerically_correct_groups=0,primary_correct_groups=0,extractable_candidates=0))
  s['groups']+=1;s['numerically_correct_groups']+=int(correct);s['primary_correct_groups']+=int(group['correct']);s['extractable_candidates']+=len(values)
 output=dict(label='POST HOC semantic diagnosis; not the preregistered score or success cost',rule='Exactly one complete maximal JSON object in the entire text; terminal bare object or one terminal standard json/untagged fenced block; only integer count; multiple objects and ambiguity rejected. Same majority/first-tie selection; truth used only for scoring.',summary=summary,candidates=rows,groups=groups)
 (R/'posterior-semantic.json').write_text(json.dumps(output,indent=2)+'\n')
 print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
