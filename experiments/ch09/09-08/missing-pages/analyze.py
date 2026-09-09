import hashlib,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parent
prep=json.loads((ROOT/'preparation.json').read_text())
reference=json.loads((ROOT/'reference-output.json').read_text())
reports=[]
for c in prep['cases']:
 name=c['case'];d=json.loads((ROOT/f'results/{name}/raw.json').read_text())
 for f,sha in d['source_hashes'].items():assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==sha
 assert len(c['before_files'])==64 and c['omitted'] not in c['before_files']
 assert all(prep['source_files'][k]==v for k,v in c['before_files'].items())
 after={f['path']:f for f in d['storage_files']};assert len(after)==65
 assert c['omitted'] in after
 assert all(after[k]['sha256']==v for k,v in c['before_files'].items())
 t=[json.loads(l) for l in (ROOT/f'results/{name}/storage.jsonl').read_text().splitlines()]
 gets=[r for r in t if r['method']=='get'];assert all(x['success'] for x in t)
 assert len(gets)==c['missing_page_index']
 assert all(Path(x['file']).name in c['before_files'] for x in gets)
 records=[]
 for r in d['requests']:
  out=r['response'];assert out['output_ids']==reference
  m=out['meta_info'];assert m['num_retractions']==0 and m['prompt_tokens']==1024 and m['completion_tokens']==16
  records.append(dict(index=r['index'],elapsed_s=r['end_s']-r['start_s'],cached_tokens=m['cached_tokens'],details=m['cached_tokens_details']))
 assert records[0]['cached_tokens']==c['missing_page_index']*16
 if name=='middle':assert records[0]['details']['storage']==512
 assert all(r['details']['device']==1008 for r in records[1:])
 missing_file=ROOT/f'restored-{name}.bin'
 assert hashlib.sha256(missing_file.read_bytes()).hexdigest()==after[c['omitted']]['sha256']
 original=(ROOT.parent/'storage-v3'/c['omitted']).read_bytes();restored=missing_file.read_bytes()
 assert len(original)==len(restored)
 words_a=struct.unpack('<'+'H'*(len(original)//2),original);words_b=struct.unpack('<'+'H'*(len(restored)//2),restored)
 different=sum(a!=b for a,b in zip(words_a,words_b))
 delta=max(abs(struct.unpack('<f',struct.pack('<I',a<<16))[0]-struct.unpack('<f',struct.pack('<I',b<<16))[0]) for a,b in zip(words_a,words_b))
 reports.append(dict(bf16_different_elements=different,bf16_total_elements=len(words_a),bf16_max_abs_difference=delta,case=name,missing_page_index=c['missing_page_index'],requests=records,get_calls=len(gets),get_file_bytes=sum(g['bytes'] for g in gets),omitted_file_restored=True,restored_bitwise_matches_original=after[c['omitted']]['sha256']==prep['source_files'][c['omitted']],other_files_unchanged=True))
(ROOT/'summary.json').write_text(json.dumps(dict(status='passed',cases=reports),indent=2)+'\n')
print(json.dumps(reports))
