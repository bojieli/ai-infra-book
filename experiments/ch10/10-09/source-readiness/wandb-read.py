"""Read-only public shared-report GraphQL transport; no account credentials."""
import datetime,hashlib,json,pathlib,re,sys,urllib.parse,urllib.request,urllib.error
B=pathlib.Path(__file__).resolve().parent
name=sys.argv[1];query=sys.stdin.read();u=json.loads(re.search(r'replace\((".*?")\)',(B/'wandb/report.html').read_text()).group(1));token=urllib.parse.parse_qs(urllib.parse.urlparse(u).query)['accessToken'][0]
raw=json.dumps({'query':query}).encode();req=urllib.request.Request('https://api.wandb.ai/graphql',data=raw,headers={'Content-Type':'application/json','access-token':token,'report-view':'true'})
try:
 with urllib.request.urlopen(req,timeout=45) as r:body=r.read(10*1024*1024+1);status=r.status
except urllib.error.HTTPError as e:body=e.read();status=e.code
assert len(body)<=10*1024*1024
p=B/'wandb'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(body);p.with_suffix(p.suffix+'.query.json').write_bytes(raw);p.with_suffix(p.suffix+'.source.json').write_text(json.dumps(dict(url=req.full_url,method='POST',status=status,scope='Public report share-token via official client headers; read-only query; no personal credentials',bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),retrieved_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()),indent=2)+'\n');print(name,status,len(body));j=json.loads(body);print('errors',j.get('errors'))
