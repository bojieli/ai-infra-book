"""Independent coefficient, accounting and source-integrity checks."""
from pathlib import Path
import sys,json,hashlib,math,unittest
import numpy as np
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'calculations/research/vision-preprocess';OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE));import vision_preprocess as m
checks=0
def check(value,label):
 global checks
 checks+=1
 if not value:raise AssertionError(label)
for old,new in [(1,256),(3,32),(7,11),(11,7),(32,256),(256,32),(385,384),(257,256),(4608,4096),(200,1024)]:
 actual=m.axis_weights(old,new); scale=old/new; radius=2*max(scale,1);K=2*math.ceil(radius)+1
 floats=[];sizes=[];starts=[]
 for i in range(new):
  center=(i+.5)*scale;lo=max(int(center-radius+.5),0);hi=min(int(center+radius+.5),old);n=max(0,min(hi-lo,K))
  distance=np.abs((np.arange(lo,lo+n,dtype=np.float64)-center+.5)/max(scale,1))
  w=np.zeros(n)
  a=distance<1;b=(distance>=1)&(distance<2)
  w[a]=1-2.5*distance[a]**2+1.5*distance[a]**3
  w[b]=2-4*distance[b]+2.5*distance[b]**2-.5*distance[b]**3
  w/=sum(w)
  floats.append(np.pad(w,(0,K-n)));sizes.append(n);starts.append(lo)
 peak=max(max(w) for w in floats);bits=next((b for b in range(22) if int(.5+peak*2**(b+1))>=32768),22)
 check(actual['weights_precision_bits']==bits,'coefficient precision')
 for row,w,n,lo in zip(actual['ranges'],floats,sizes,starts):
  quant=np.trunc(w*2**bits+np.where(w<0,-.5,.5)).astype(int).tolist()
  check(row['start']==lo and row['count']==n,'support')
  check(row['int16_weights']==quant,'independent polynomial coefficient')
for H,W in [(640,640),(257,385),(32,32),(4608,4608),(256,32)]:
 for dtype in ['bf16','fp32']:
  d=m.calculate(H,W,encoder_dtype=dtype); stages=d['stages']; by={s['stage']:s for s in stages}
  for axis in d['resize_axes']:
   label=axis['axis']; mult=3*H if label=='width' else 3*d['summary']['resized_width']
   conv=by[label+'_uint8_separable_convolution'];mac=mult*sum(x['count'] for x in axis['ranges'])
   check(conv['operations']['int32_multiply']==mac,'integer multiplies')
   check(conv['semantic_read_bytes']==3*mac,'pixel and int16 operand bytes')
  check(all(s['semantic_read_bytes']>=0 and s['semantic_write_bytes']>=0 for s in stages),'nonnegative interfaces')
for row in json.loads((BASE/'sources.lock.json').read_text()):
 data=(BASE/row['file']).read_bytes();check(len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'],'official source hash')
r=unittest.TextTestRunner().run(unittest.defaultTestLoader.discover(str(BASE),pattern='test_vision_preprocess.py'));check(r.wasSuccessful() and not r.skipped,'author accounting tests')
(OUT/'results.json').write_text(json.dumps({'checks':checks,'author_tests':r.testsRun,'skipped':len(r.skipped)},indent=2)+'\n');print('Independent checks:',checks)
# Execute the existing selected-official numerical oracle, redirecting only evidence output.
script=(BASE/'numeric_check.py').read_text().replace('(HERE / "numeric-verification.json")','(Path('+repr(str(OUT)) + ') / "numeric-replay.json")')
exec(compile(script,str(BASE/'numeric_check.py'),'exec'),{'__name__':'__main__','__file__':str(BASE/'numeric_check.py')})
