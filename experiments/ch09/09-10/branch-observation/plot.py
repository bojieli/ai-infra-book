"""Generate an evidence flow diagram from analyzed actual events (not a latency plot)."""
import json,html
from pathlib import Path
R=Path(__file__).resolve().parent
chains=json.loads((R/'request-chains.json').read_text())
first=[c for c in chains if c['first_completed']]
assert len(first)==4
s=['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="590" viewBox="0 0 1200 590">','<rect width="1200" height="590" fill="#f5f7fb"/>','<style>text{font-family:Arial,sans-serif;fill:#172338}.title{font-size:26px;font-weight:700}.sub{font-size:15px}.label{font-size:17px;font-weight:700}.body{font-size:16px}.small{font-size:13px}</style>']
def text(x,y,txt,cls='body'):s.append(f'<text x="{x}" y="{y}" class="{cls}">{html.escape(str(txt))}</text>')
text(30,42,'HiCache: observed first-completed request path','title')
text(30,70,'2 trials per condition | exact request IDs | fixed SG 0.5.13.post1 | execution trace, not latency','sub')
for row,count in enumerate((1,8)):
 cs=[c for c in first if ('native-1' if count==1 else 'native-8') in c['group']];assert len(cs)==2
 c=cs[0];y=115+row*205
 text(30,y,f'{count} request'+('s' if count==8 else '')+f' / first: {c["rid"]} / repeated in both trials','label')
 rate=c['rate'][0];pop=c['pop'][0]['loaded'];pref=next(e for e in c['prefill'] if e['phase']=='call')['req']
 boxes=[('Rate limit',[f'occupied {rate["controller"]["prefetch_tokens_occupied"]}',f'capacity {rate["controller"]["prefetch_capacity_limit"]}',f'return {str(rate["limited"]).lower()}']),('Ongoing / progress',['registered' if count==1 else 'not registered','complete then true' if count==1 else 'absent -> true']),('Storage attribution',[f'pop loaded: {pop}', 'host matched: 0' if count==1 else 'no operation']),('Before prefill',[f'prefix: {pref["prefix_indices_len"]}',f'host: {pref["host_hit_length"]}',f'storage: {pref["storage_hit_length"]}']),('API first complete',[f'cached: {c["cached_tokens"]}','storage: 1008' if count==1 else 'details: null'])]
 for col,(label,lines) in enumerate(boxes):
  x=30+col*235
  s.append(f'<rect x="{x}" y="{y+18}" width="210" height="128" rx="9" fill="white" stroke="'+('#3a7c78' if count==1 else '#ba7044')+'" stroke-width="2"/>')
  text(x+13,y+45,label,'label')
  for j,line in enumerate(lines):text(x+13,y+73+j*22,line)
  if col<4:s.append(f'<path d="M {x+213} {y+82} h 17 m -5 -5 l 5 5 l -5 5" fill="none" stroke="#718096" stroke-width="2"/>')
text(30,535,'8-request wave: native-0..3 wait; native-4 passes the no-ongoing branch and enters with zero matched tokens.','sub')
text(30,563,'Device pool 4096; actual host pool 8208; limit 3289. Diagram spacing does not encode time.','sub')
s.append('</svg>');(R/'branch-flow.svg').write_text('\n'.join(s)+'\n')
