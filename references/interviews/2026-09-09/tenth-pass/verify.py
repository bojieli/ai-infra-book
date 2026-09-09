from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json
from bs4 import BeautifulSoup
D=Path(__file__).resolve().parent
sources=json.loads((D/'sources.json').read_text());proof=json.loads((D/'reading-proof.json').read_text());by_id={r['id']:r for r in sources}
assert len(by_id)==len(sources)==proof['source_responses']==8
for r in sources:
 data=(D/r['file']).read_bytes();assert len(data)==r['bytes'];assert hashlib.sha256(data).hexdigest()==r['sha256'];assert r['status']==200
for r in proof['posts']:
 source=by_id[r['source_id']];soup=BeautifulSoup((D/source['file']).read_bytes(),'html.parser');script=next(s.get_text() for s in soup.find_all('script') if 'window.__INITIAL_STATE__=' in s.get_text());state,_=json.JSONDecoder().raw_decode(script.split('window.__INITIAL_STATE__=',1)[1]);main=state
 for part in r['main_object_path']:main=main[part]
 for item in [r['main'],r['text']]:
  data=(D/item['file']).read_bytes();assert len(data)==item['bytes'];assert hashlib.sha256(data).hexdigest()==item['sha256']
 assert main==json.loads((D/r['main']['file']).read_text());assert main['uuid']==r['uuid'];assert main['userBrief']['nickname']==r['author'];assert main['userBrief']['userId']==r['user_id'];assert main['title']==r['title']
 assert datetime.fromtimestamp(main[r['time_field']]/1000,timezone(timedelta(hours=8))).isoformat()==r['published_at'];assert r['published_at'].startswith('2026-')
 assert datetime.fromtimestamp(main['editTime']/1000,timezone(timedelta(hours=8))).isoformat()==r['edited_at']
 text=BeautifulSoup(main.get('content',''),'html.parser').get_text('\n',strip=True)+'\n';assert text==(D/r['text']['file']).read_text();assert r['body_read_lines']==[1,len(text.splitlines())]
 if r['images_viewed']:
  assert [x['src'] for x in main['imgMoment']]==[by_id[x]['url'] for x in r['images_viewed']]
assert len({p['user_id'] for p in proof['posts'] if p['adopted_direction']})==3
assert sum(p['kind']=='unverified_first_person' and p['company_scope']=='foundation_model_company' for p in proof['posts'])==2
for sid in proof['shell_sources']:
 assert 'window.__INITIAL_STATE__=' not in (D/by_id[sid]['file']).read_text()
assert proof['new_numbered_questions']==0 and proof['questions_proposed_to_remain']==21
result=dict(status='passed',verified_at=datetime.now(timezone.utc).isoformat(),source_responses=len(sources),main_posts_read=len(proof['posts']),foundation_company_unverified_personal_reports=2,related_cloud_platform_unverified_personal_reports=1,commercial_column_leads=1,new_numbered_questions=0,errors=[])
(D/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
