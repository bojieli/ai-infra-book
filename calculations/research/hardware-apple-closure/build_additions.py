"""Emit reviewed official GPU-bin/memory combinations, not arbitrary cross products."""
import json
import hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
hw=json.loads((ROOT/'configs/hardware.json').read_text())
locks=json.loads((ROOT/'configs/sources.lock.json').read_text())['sources']+json.loads((OUT/'additional-sources.lock.json').read_text())['sources']
sources={r['id']:r for r in locks if 'id' in r}
# Family, GPU bin, explicitly permitted capacities, bandwidth GB/s, source.
specs=[
 ('m1',7,[8,16],None,'apple-m1-base-specs'),('m1',8,[8,16],None,'apple-m1-base-specs'),
 ('m1-pro',14,[16,32],200,'apple-m1-pro-14-specs'),('m1-pro',16,[16,32],200,'apple-m1-pro-14-specs'),
 ('m1-max',24,[32,64],400,'apple-m1-studio-specs'),('m1-max',32,[32,64],400,'apple-m1-studio-specs'),
 ('m1-ultra',48,[64,128],800,'apple-m1-studio-specs'),('m1-ultra',64,[64,128],800,'apple-m1-studio-specs'),
 ('m2',8,[8,16,24],100,'apple-m2-base-specs'),('m2',10,[8,16,24],100,'apple-m2-base-specs'),
 ('m2-pro',16,[16,32],200,'apple-m2-pro-max-14-specs'),('m2-pro',19,[16,32],200,'apple-m2-pro-max-14-specs'),
 ('m2-max',30,[32,64],400,'apple-m2-pro-max-14-specs'),('m2-max',38,[32,64,96],400,'apple-m2-pro-max-14-specs'),
 ('m2-ultra',60,[64,128,192],800,'apple-m2-studio-specs'),('m2-ultra',76,[64,128,192],800,'apple-m2-studio-specs'),
 ('m3',8,[8,16,24],100,'apple-m3-base-specs'),('m3',10,[8,16,24],100,'apple-m3-base-specs'),
 ('m3-pro',14,[18,36],150,'apple-m3-pro-max-14-specs'),('m3-pro',18,[18,36],150,'apple-m3-pro-max-14-specs'),
 ('m3-max',30,[36,96],300,'apple-m3-pro-max-specs'),('m3-max',40,[48,64,128],400,'apple-m3-pro-max-specs'),
 ('m3-ultra',60,[96,256],819,'apple-m3-ultra-specs'),('m3-ultra',80,[96,256],819,'apple-m3-ultra-specs'),
 ('m3-ultra',80,[512],819,'apple-m3-ultra-power-config'),
 ('m4',8,[16,24,32],120,'apple-m4-base-specs'),('m4',10,[16,24,32],120,'apple-m4-base-specs'),
 ('m4-pro',16,[24,48,64],273,'apple-m4-mini-specs'),('m4-pro',20,[24,48,64],273,'apple-m4-mini-specs'),
 ('m4-max',32,[36],410,'apple-m4-pro-max-specs'),('m4-max',40,[48,64,128],546,'apple-m4-pro-max-specs'),
 ('m5',8,[16,24,32],153,'apple-m5-air-specs'),('m5',10,[16,24,32],153,'apple-m5-air-specs'),
 ('m5-pro',16,[24,48],307,'apple-m5-pro-max-14-specs'),
 ('m5-pro',16,[64],307,'apple-macmini-current-specs'),
 ('m5-pro',20,[24,48,64],307,'apple-m5-pro-max-specs'),
 ('m5-max',32,[36],460,'apple-m5-pro-max-specs'),('m5-max',40,[48,64,128],614,'apple-m5-pro-max-specs'),
 ('m5-ultra',64,[96,256],1200,'apple-macstudio-current-specs'),('m5-ultra',80,[96,256,512],1200,'apple-macstudio-current-specs'),
 ('m6',12,[16],153,'apple-macmini-current-specs'),('m6',12,[24,32],170,'apple-macmini-current-specs'),
]
def key(d):
 import re
 f=re.match(r'm[1-6](?:-pro|-max|-ultra)?',d['id']).group()
 return f,d.get('gpu_cores',d.get('core_counts',{}).get('gpu')),d['memory']['nominal_capacity']
old={key(d):d['id'] for d in hw['devices'] if d['vendor']=='Apple'}
new=[];catalog=[]
for fam,gpu,caps,bw,source in specs:
 r=sources[source];data=(ROOT/r['file']).read_bytes();assert hashlib.sha256(data).hexdigest()==r['sha256']
 for cap in caps:
  k=fam,gpu,cap
  id=f'{fam}-{gpu}gpu-{cap}gb'
  catalog.append(dict(family=fam,gpu_cores=gpu,memory_gb=cap,bandwidth_gb_per_second=bw,source_id=source,device_id=old.get(k,id),already_present=k in old))
  if k in old:continue
  ids=[source];notes=['官方GPU档位与其允许内存组合，非芯片最高内存对所有GPU档位的笛卡尔积。',
    '仅枚举Mac GPU/容量组合；同组合在不同整机/CPU/SSD中的复用不代表相同功耗、持续频率或可用内存。',
    '所引官方来源未提供输入精度/累加精度/稀疏口径完整的GPU峰值，保持未知；Neural Engine与GPU Neural Accelerator不合并。']
  availability=dict(status='official_configuration_documented',as_of='2026-09-09',current_retail_availability='not_verified',source_id=source)
  if fam=='m3-ultra' and cap==512:
   ids+=['apple-m3-ultra-specs','apple-h04-m3-ultra-launch']
   availability['status']='historical_configuration_documented'
   notes+=['官方功耗文档明确测试配置为32 CPU/80 GPU/512GB；只引用其配置身份，不将整机墙上270W用作GPU TDP。819GB/s来自同型号技术规格；当前支持页只列96/256GB不抹去历史512GB。']
  if fam=='m5-ultra':
   ids+=['apple-h04-m5-ultra-product-launch']
   availability=dict(status='announced_not_yet_available',as_of='2026-09-09',announced_date='2026-08-25',available_from='2026-09-22' if cap!=512 else None,available_window='late October 2026' if cap==512 else None,source_id='apple-h04-m5-ultra-product-launch')
  if fam=='m5-pro' and gpu==16 and cap==64:notes+=['64GB来自Mac mini，14英寸MacBook Pro技术页只允许此16GPU档至48GB；不可混同整机选项。']
  peak=[]
  if fam=='m1' and gpu==8:
   peak=next(d for d in hw['devices'] if d['id']=='m1-8gpu-16gb')['peak_rates'];ids+=['apple-m1-launch']
  new.append(dict(id=id,name=f'Apple {fam.upper().replace("-"," ")} {gpu}-core GPU / {cap}GB',vendor='Apple',architecture=fam.upper().replace('-',' '),form_factor='Mac SoC / shared unified memory',spec_scope='single_device',source_ids=ids,memory=dict(nominal_capacity=cap,capacity_unit='GB',bandwidth_bytes_per_second=None if bw is None else bw*10**9,source_id='apple-m3-ultra-specs' if fam=='m3-ultra' and cap==512 else source,locator='Chip / Memory / Configure to Order; historical 512GB identity also in official power-test configuration',capacity_note='厂商容量标签；CPU/GPU/OS共享，不是GPU专用可分配容量。',shared_with_cpu=True),gpu_cores=gpu,power_watts=None,peak_rates=peak,availability=availability,notes=notes))
assert len({(x['family'],x['gpu_cores'],x['memory_gb']) for x in catalog})==len(catalog)
assert len({d['id'] for d in new})==len(new)
assert all(set(d['source_ids'])<=sources.keys() for d in new)
(OUT/'additional-devices.json').write_text(json.dumps(dict(schema_version=1,as_of='2026-09-09',devices=new),ensure_ascii=False,indent=2)+'\n')
(OUT/'gpu-memory-combinations.json').write_text(json.dumps(dict(as_of='2026-09-09',combinations=catalog),ensure_ascii=False,indent=2)+'\n')
patches=[]
for id,window,date in [('m5-ultra-64gpu-256gb',None,'2026-09-22'),('m5-ultra-80gpu-512gb','late October 2026',None)]:
 patches.append(dict(device_id=id,merge_fields=dict(availability=dict(status='announced_not_yet_available',as_of='2026-09-09',announced_date='2026-08-25',available_from=date,available_window=window,source_id='apple-h04-m5-ultra-product-launch')),append_source_ids=['apple-h04-m5-ultra-product-launch']))
(OUT/'availability-patches.json').write_text(json.dumps(dict(patches=patches),indent=2)+'\n')
print('new',len(new),'catalog',len(catalog),'already present',len(catalog)-len(new))
