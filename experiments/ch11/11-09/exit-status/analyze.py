"""Offline integrity audit; never executes generated code or calls a model."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parent
RAW=R/'raw';ARMS=['baseline','proper-exit','proper-exit','baseline'];checks=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_text())
def ck(ok,label):
 assert ok,label
 checks.append(label)
for n,h in load(R/'run.lock.json').items():ck(sha((R/n).read_bytes())==h,'frozen '+n)
for n,h in load(R/'sources.lock.json').items():ck(sha((R/n).read_bytes())==h,'source '+n)
proof=load(RAW/'wrapper-proof.json');a=proof['baseline'];b=proof['proper_exit']
ck(a['stdout']==b['stdout'] and a['stderr']==b['stderr'] and a['returncode']==0 and b['returncode']==1,'real wrapper proof')
initial=load(R/'initial-messages.json');summary=[];requests=[]
# AST literal extraction avoids importing or executing fixture/generated code.
import ast
literals={n.targets[0].id:ast.literal_eval(n.value) for n in ast.parse((R/'fixture.py').read_text()).body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ['INITIAL','SPEC','CHECKER']}
for i,arm in enumerate(ARMS):
 d=RAW/f'{i}-{arm}';rows=[json.loads(x) for x in (d/'rounds.jsonl').read_text().splitlines()];messages=initial;code=literals['INITIAL'];finished=False;tokens=[0,0];tool_count=0
 ck(1<=len(rows)<=12,f'{i} round count')
 ck((d/'workspace/SPEC.txt').read_text()==literals['SPEC'] and (d/'workspace/test_intervals.py').read_text()==literals['CHECKER'],f'{i} fixture')
 for t,x in enumerate(rows):
  tag=f'{i}:{t}';reqraw=(d/f'request-{t:02}.json').read_bytes();respraw=(d/f'response-{t:02}.json').read_bytes();req=json.loads(reqraw);resp=json.loads(respraw)
  ck(x['turn']==t and x['arm']==arm and not finished,tag+' ordering')
  ck(x['request']==req and x['response']==resp and x['http_status']==200,tag+' raw HTTP')
  ck(sha(reqraw)==x['request_sha256'] and sha(respraw)==x['response_sha256'],tag+' HTTP hashes')
  ck(req==dict(model='qwen-fast',messages=messages,temperature=0,top_p=1,seed=304,max_tokens=1200,stream=False,chat_template_kwargs=dict(enable_thinking=False)),tag+' request parameters and messages')
  ck(x['messages']==messages and x['code_before']==code,tag+' chain')
  choice=resp['choices'][0];text=choice['message']['content'];ck(text==x['output_text'] and choice['finish_reason']==x['finish_reason'] and resp['usage']==x['usage'],tag+' output usage finish')
  for k in ['prompt_token_ids','output_token_ids','kernel_time','scheduling_time','cost']:ck(x[k] is None,tag+' null '+k)
  action=x['action'];reply=x['tool_result'];tool=action.get('tool')
  if tool!='invalid':ck(json.loads(text)==action and x['finish_reason']!='length',tag+' strict JSON')
  else:
   try:json.loads(text);parse_failed=False
   except (ValueError,TypeError):parse_failed=True
   ck(parse_failed or x['finish_reason']=='length',tag+' rejected actual non-JSON/length')
   ck('error' in reply,tag+' error feedback')
  if tool=='write_file':code=action['content'];ck(reply==dict(written_bytes=len(code.encode()),sha256=sha(code.encode())),tag+' write')
  elif tool=='read_file':
   contents={'intervals.py':code,'SPEC.txt':literals['SPEC'],'test_intervals.py':literals['CHECKER']};ck(reply=={'content':contents[action['path']]},tag+' read')
  elif tool=='run_tests':
   tool_count+=1;ck(set(reply)=={'returncode','stdout','stderr'},tag+' original fields')
   data=json.loads(reply['stdout']);ck(len(data['cases'])==6 and data['passed']==all(c['passed'] for c in data['cases']),tag+' six original cases')
   ck(reply['returncode']==(1 if arm=='proper-exit' and not data['passed'] else 0),tag+' actual exit mapping')
   ck(x['tool_audit']['argv'][-1]==arm and x['tool_audit']['limits']==dict(cpu_s=2,as_bytes=536870912,wall_s=5,file_bytes=1048576),tag+' subprocess invocation limits')
  elif tool=='finish':finished=True;ck(reply=={'answer':action.get('answer','')},tag+' finish')
  ck(x['code_after']==code and (d/f'code-{t:02}.py').read_text()==code and sha(code.encode())==x['file_sha256'],tag+' code')
  messages=messages+[dict(role='assistant',content=text),dict(role='user',content='Tool result: '+json.dumps(reply))]
  requests.append((x['client_start_unix'],x['client_end_unix']));tokens[0]+=x['usage']['prompt_tokens'];tokens[1]+=x['usage']['completion_tokens']
 f=load(d/'final.json');v=json.loads(f['validation']['stdout']);h=load(d/'independent-checks.json');hd=json.loads(h['result']['stdout'])
 ck(f['agent_finished']==finished and f['rounds']==len(rows) and f['final_code']==code and f['final_sha256']==sha(code.encode()) and (d/'workspace/intervals.py').read_text()==code,f'{i} final')
 ck(f['validation']['returncode']==0 and len(v['cases'])==6,f'{i} final validation')
 ck(h['result']['returncode']==0 and h['checker_sha256']==sha((R/'check_code.py').read_bytes()) and hd['cases']==1013 and hd['passed']==hd['value_and_input_passed']-hd['additional_alias_failures'],f'{i} holdout')
 ck(h['audit']['start_unix']>=load(RAW/'model-ended.json')['end_unix'],f'{i} holdout after all attempts')
 summary.append(dict(index=i,arm=arm,rounds=len(rows),run_tests=tool_count,agent_finished=finished,six_passed=sum(c['passed'] for c in v['cases']),qualified=finished and v['passed'],holdout_value_input_passed=hd['value_and_input_passed'],additional_alias_failures=hd['additional_alias_failures'],holdout_strict_passed=hd['passed'],prompt_tokens=tokens[0],completion_tokens=tokens[1],length_outputs=sum(x['finish_reason']=='length' for x in rows),invalid_outputs=sum(x['action']['tool']=='invalid' for x in rows),client_request_s=sum(x['client_end_unix']-x['client_start_unix'] for x in rows),final_sha256=f['final_sha256']))
ck(all(a<=b for a,b in requests) and all(requests[i][1]<=requests[i+1][0] for i in range(len(requests)-1)),'single in flight')
ck(load(RAW/'model-ended.json')['elapsed_s']<=1200,'model wall <=1200')
res=[json.loads(x) for x in (RAW/'resources.jsonl').read_text().splitlines()]
ck(all(x['rss_bytes']<=2*1024**3 for x in res),'sampled CPU tree RSS <=2GiB')
ck(all(p['affinity']==[8,9,10,11] for x in res for p in x['processes']),'CPU affinity')
ck(load(RAW/'exit.json')['returncode']==0 and load(RAW/'exit.json')['remaining_owned']==[],'clean exit')
before=load(RAW/'service-before.json');after=load(RAW/'service-after.json');ck(before['server_cmdline']==after['server_cmdline'],'same service command')
ck(before['engine_stat'].split()[21]==after['engine_stat'].split()[21],'same engine start ticks')
result=dict(attempts=summary,requests=len(requests),model_elapsed_s=load(RAW/'model-ended.json')['elapsed_s'],cpu_tree_rss_peak_bytes=max(x['rss_bytes'] for x in res),samples=len(res),max_sample_gap_s=max(b['time_unix']-a['time_unix'] for a,b in zip(res,res[1:])),cost=None,gpu_exclusive_bytes=None)
(R/'analysis.json').write_text(json.dumps(result,indent=2)+'\n');(R/'checks.json').write_text(json.dumps(dict(passed=len(checks),checks=checks),indent=2)+'\n');print(json.dumps(result,indent=2));print('checks',len(checks))
