import datetime,hashlib,json,pathlib,re,urllib.parse,urllib.request,urllib.error
B=pathlib.Path(__file__).resolve().parent;u=json.loads(re.search(r'replace\((".*?")\)',(B/'wandb/report.html').read_text()).group(1));token=urllib.parse.parse_qs(urllib.parse.urlparse(u).query)['accessToken'][0];results=[]
for p in (B/'wandb/histories').glob('gate3-v1-*.json'):
 if '.query.' in p.name or '.source.' in p.name:continue
 r=json.loads(p.read_text())['data']['project']['run']
 for e in r['files']['edges']:
  f=e['node']
  if f['name'] not in ['output.log','requirements.txt','config.yaml']:continue
  req=urllib.request.Request(f['url'],headers={'access-token':token,'report-view':'true'})
  try:
   with urllib.request.urlopen(req,timeout=45) as response:body=response.read(5*1024*1024+1);status=response.status;resolved=response.url
  except urllib.error.HTTPError as err:
   results.append(dict(run=r['name'],name=f['name'],status=err.code,downloaded=False));continue
  assert len(body)<=5*1024*1024
  dst=B/'wandb/files'/r['name']/f['name'];dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(body);record=dict(run=r['name'],name=f['name'],status=status,downloaded=True,url=f['url'],resolved_url=resolved,bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),retrieved_utc=datetime.datetime.now(datetime.timezone.utc).isoformat());dst.with_suffix(dst.suffix+'.source.json').write_text(json.dumps(record,indent=2)+'\n');results.append(record)
(B/'wandb/file-access.json').write_text(json.dumps(results,indent=2)+'\n');print([(r['run'],r['name'],r['status'],r.get('bytes')) for r in results])
