"""Download pinned source index into a NEW output directory; never overwrite archive."""
from pathlib import Path
import argparse,json,urllib.request,hashlib
p=argparse.ArgumentParser();p.add_argument('output');a=p.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
for item in json.loads((Path(__file__).parent/'sources/index.json').read_text()):
 data=urllib.request.urlopen(item['url'],timeout=60).read()
 if hashlib.sha256(data).hexdigest()!=item['sha256']:raise SystemExit('Source has changed: '+item['file']+'; frozen archive remains authoritative')
 (out/item['file']).write_bytes(data)
