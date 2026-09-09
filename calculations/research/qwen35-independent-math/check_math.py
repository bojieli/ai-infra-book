"""Independent short-list DeltaNet algebra and frozen-ledger invariants."""
import math,json,hashlib,types,sys,importlib.util
from pathlib import Path
O=Path(__file__).resolve().parent

def transpose(a):return [list(x) for x in zip(*a)]
def mm(a,b):return [[sum(x*y for x,y in zip(row,col)) for col in zip(*b)] for row in a]
def add(a,b):return [[x+y for x,y in zip(ar,br)] for ar,br in zip(a,b)]
def sub(a,b):return [[x-y for x,y in zip(ar,br)] for ar,br in zip(a,b)]
def scale(a,x):return [[v*x for v in row] for row in a]
def solve_unit_lower(a,b):
 out=[]
 for i,row in enumerate(b):out.append([row[j]-sum(a[i][k]*out[k][j] for k in range(i)) for j in range(len(row))])
 return out

def recurrent(q,k,v,g,beta,state):
 out=[]
 for qi,ki,vi,gi,bi in zip(q,k,v,g,beta):
  state=scale(state,math.exp(gi));prediction=mm([ki],state)[0];delta=[(x-y)*bi for x,y in zip(vi,prediction)]
  state=add(state,[[x*y for y in delta] for x in ki]);out.append(mm([qi],state)[0])
 return out,state

def chunk(q,k,v,g,beta,state,C):
 out=[];kd=len(k[0]);vd=len(v[0]);T=len(q)
 pad=(-T)%C
 q=q+[[0.]*kd for _ in range(pad)];k=k+[[0.]*kd for _ in range(pad)];v=v+[[0.]*vd for _ in range(pad)];g=g+[0.]*pad;beta=beta+[0.]*pad
 for start in range(0,T+pad,C):
  qc,kc,vc=q[start:start+C],k[start:start+C],v[start:start+C];bc=beta[start:start+C];gc=g[start:start+C];cum=[]
  for x in gc:cum.append(x+(cum[-1] if cum else 0))
  decay=[[math.exp(cum[i]-cum[j]) if j<=i else 0 for j in range(C)] for i in range(C)]
  kb=[[x*b for x in r] for r,b in zip(kc,bc)];vb=[[x*b for x in r] for r,b in zip(vc,bc)]
  ut=[[x*y for x,y in zip(r,dr)] for r,dr in zip(mm(kb,transpose(kc)),decay)]
  intra=[[x*y for x,y in zip(r,dr)] for r,dr in zip(mm(qc,transpose(kc)),decay)]
  decayed_kb=[[x*math.exp(g) for x in r] for r,g in zip(kb,cum)]
  new=solve_unit_lower(ut,vb);kread=solve_unit_lower(ut,decayed_kb)
  vn=sub(new,mm(kread,state));qq=[[x*math.exp(g) for x in r] for r,g in zip(qc,cum)]
  out.extend(add(mm(qq,state),mm(intra,vn)))
  kk=[[x*math.exp(cum[-1]-g) for x in r] for r,g in zip(kc,cum)]
  state=add(scale(state,math.exp(cum[-1])),mm(transpose(kk),vn))
 return out[:T],state

def err(a,b):return max(abs(x-y) for r,s in zip(a,b) for x,y in zip(r,s))
results=[]
for T in [1,2,3,4,5,9]:
 for C in [2,4,64]:
  for nonzero in [False,True]:
   q=[[math.sin((i+1)*(j+1))*.2 for j in range(3)] for i in range(T)]
   k=[[math.cos((i+2)*(j+1))*.15 for j in range(3)] for i in range(T)]
   v=[[math.sin(i+j+.7) for j in range(2)] for i in range(T)];g=[-.05*(i%3+1) for i in range(T)];beta=[.3+.1*(i%4) for i in range(T)]
   state=[[.03*(i-j) if nonzero else 0. for j in range(2)] for i in range(3)]
   a,sa=recurrent(q,k,v,g,beta,state);b,sb=chunk(q,k,v,g,beta,state,C)
   e=max(err(a,b),err(sa,sb));assert e<1e-12
   results.append({'tokens':T,'chunk_size':C,'nonzero_initial_state':nonzero,'max_abs_error':e})
# Import both frozen modules, never read a concurrently edited author helper.
helper=types.ModuleType('reference_steps');exec(compile((O/'reference_steps.snapshot.py').read_text(),'reference_steps.snapshot.py','exec'),helper.__dict__);sys.modules['reference_steps']=helper
spec=importlib.util.spec_from_file_location('qwen35_frozen',O/'qwen35_forward.snapshot.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
checks=[]
for T,S,B in [(1,0,1),(1,3,1),(3,7,2),(65,0,1)]:
 r=mod.calculate(batch=B,tokens=T,history=S,output_head='none');ops=r['operators'];mat=lambda pred:sum(x['matrix_flops']*x['repeats'] for x in ops if pred(x['name']))
 if S>0 and T==1:expected=45*6*B*64*128*128;actual=mat(lambda n:n.startswith('linear.recurrent.'))
 else:
  groups=B*64*((T+63)//64);expected=45*groups*(6*64*128*128+6*64*64*128);actual=mat(lambda n:n.startswith('linear.chunk.'))
  solve=next(x for x in ops if x['name']=='linear.chunk.two_triangular_solves');assert solve['scalar_flops']*solve['repeats']==45*groups*64*63*256
 assert actual==expected
 assert r['state']['linear_recurrent_fp32_bytes']==45*B*64*128*128*4
 assert r['state']['linear_conv_slot_bytes']==45*B*12288*4*2
 assert mat(lambda n:n.startswith('moe.expert'))==60*6*(B*T*10)*4096*1024
 assert mat(lambda n:n=='moe.router')==60*2*B*T*4096*512
 assert sum(r['execution']['expert_histogram'])==B*T*10
 checks.append({'batch':B,'tokens':T,'history':S,'core_matrix_flops':actual,'closed_form_match':True})
# Demonstrate the record_past copy discrepancy against the source branch: cache assignment, not last4 copy.
record=helper.supplement(1,2,0,[1]*20+[0]*492,True)
copyrow=next(x for x in record['steps'] if x['name']=='conv.cache_copy_last4')
assert copyrow['tensor_output_bytes']==2*12288*4
report={'snapshot_sha256':hashlib.sha256((O/'qwen35_forward.snapshot.py').read_bytes()).hexdigest(),'helper_snapshot_sha256':hashlib.sha256((O/'reference_steps.snapshot.py').read_bytes()).hexdigest(),'short_sequence_algebra_cases':results,'maximum_error':max(x['max_abs_error'] for x in results),'ledger_closed_form_cases':checks,'record_past_issue':{'history':0,'tokens':2,'record_past':True,'snapshot_claimed_last4_copy_bytes_per_layer':copyrow['tensor_output_bytes'],'source_last4_copy_bytes_per_layer':0,'reason':'Source cache_utils.update_conv_state uses assignment in record_past branch; no copy_ last4.'},'boundaries':['Pure Python float short matrices, not GPU or actual model payload test.','FMA=2 convention retained; independent algebra proves chunk recurrence equivalence for selected scan, not a torch solver backend operation count.','Snapshot has gaps/full_forward_exact=False; audit does not turn interface subtotal into HBM or memory peak.']}
(O/'results.json').write_text(json.dumps(report,indent=2)+'\n');print('numeric cases',len(results),'maxerror',report['maximum_error'],'ledger cases',len(checks))
