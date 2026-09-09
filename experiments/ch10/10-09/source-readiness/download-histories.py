import concurrent.futures,json,pathlib,subprocess,sys
B=pathlib.Path(__file__).resolve().parent;runs=json.loads((B/'wandb/runs.json').read_text())['data']['project']['runs']['edges']
selected=[e['node']['name'] for e in runs if any(e['node']['name'].startswith('gate3-v'+v+'-r3') for v in ['1','2','6','7'])]
def get(name):
 out='histories/'+name+'.json';query='query { project(name:"R3-Effectiveness-0609",entityName:"nvidia-nemo-fw-public"){run(name:'+json.dumps(name)+'){name state history(samples:1000) files(first:100){edges{node{name url sizeBytes}} pageInfo{hasNextPage endCursor}}}}}'
 p=subprocess.run([sys.executable,'-B',str(B/'wandb-read.py'),out],input=query,text=True,capture_output=True);assert p.returncode==0,(name,p.stderr);return p.stdout.strip()
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 for x in pool.map(get,selected):print(x)
