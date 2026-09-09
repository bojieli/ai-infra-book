"""Bounded public author-linked W&B config and token-loss retrieval; no weights."""
import concurrent.futures,json,pathlib,urllib.request,hashlib
ROOT=pathlib.Path(__file__).resolve().parent
GROUPS={'160m':'Pythia 125M_1mpgqyzx','1b':'800M Pythia_1zw5etef','1.4b':'Pythia 1.3B_lepj8rtx','2.8b':'2.7B New_36751euw'}
def query(q,path):
 payload={'query':q};raw=urllib.request.urlopen(urllib.request.Request('https://api.wandb.ai/graphql',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'}),timeout=45).read();path.write_bytes(raw);path.with_suffix('.request.json').write_text(json.dumps(payload,indent=2)+'\n');return json.loads(raw)
def get(item):
 name,group=item;f=json.dumps({'group':group});d=query('query { project(name:"pythia", entityName:"eleutherai") { runs(first:100, filters:'+json.dumps(f)+') { edges { node { name displayName group config summaryMetrics } } } } }',ROOT/f'{name}-runs.json');out=[]
 for edge in d['data']['project']['runs']['edges']:
  n=edge['node'];summary=json.loads(n['summaryMetrics'])
  if 'validation/lm_loss' not in summary:continue
  spec=json.dumps({'keys':['_step','validation/lm_loss','validation/lm_loss_ppl'],'samples':10000})
  h=query('query { project(name:"pythia", entityName:"eleutherai") { run(name:'+json.dumps(n['name'])+') { sampledHistory(specs:['+json.dumps(spec)+']) } } }',ROOT/f"{name}-{n['name']}-loss.json")
  out.append((name,n['name'],h))
 return out
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  for out in pool.map(get,GROUPS.items()):print(out)
