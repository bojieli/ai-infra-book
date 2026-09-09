import json,pathlib,concurrent.futures
from fetch_loss import query,ROOT
RUNS=['32t0zbcs','3mvtbwii','12j05401','vd5ogsc6','2l7ymzlr','4x2lfblu','2j0vfxrj']
def get(run):
 spec=json.dumps({'keys':['_step','validation/lm_loss','validation/lm_loss_ppl'],'samples':10000})
 d=query('query { project(name:"pythia", entityName:"eleutherai") { run(name:'+json.dumps(run)+') { sampledHistory(specs:['+json.dumps(spec)+']) } } }',ROOT/f'v2-{run}-history.json')
 rows=d['data']['project']['run']['sampledHistory'][0];return run,len(rows),rows[:1],rows[-1:]
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as p:
  for x in p.map(get,RUNS):print(x)
