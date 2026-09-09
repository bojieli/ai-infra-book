import requests,pathlib,json,hashlib,datetime,concurrent.futures,sys
p=pathlib.Path(__file__).resolve().parent; jobs=json.loads(pathlib.Path(sys.argv[1]).read_text())
def get(j):
 try:
  r=requests.get(j['url'],timeout=45);b=r.content; ext='pdf' if b.startswith(b'%PDF') else 'html';f=p/(j['id']+'.'+ext);f.write_bytes(b)
  return {**j,'final_url':r.url,'status_code':r.status_code,'file':str(f),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'retrieved_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 except Exception as e:
  f=p/(j['id']+'.error.txt');f.write_text(str(e));b=f.read_bytes()
  return {**j,'status_code':None,'file':str(f),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'error':str(e),'retrieved_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex: out=list(ex.map(get,jobs))
pathlib.Path(sys.argv[1]+'.results.json').write_text(json.dumps(out,indent=2))
for x in out: print(x['id'],x['status_code'],x['bytes'],x['file'])
