import os,pathlib,json
P=pathlib.Path(__file__).resolve().parents[1]
os.environ['MPLCONFIGDIR']=str(P/'plot-cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
rows=json.loads((P/'results/steps.json').read_text())
fig,axs=plt.subplots(2,1,figsize=(12,7),layout='constrained')
for ax,mode in zip(axs,['dflash-7','dflash-15']):
 r=[x for x in rows if x['mode']==mode and 'short_math' in x['request_id']]
 k=int(mode.split('-')[1]); xx=list(range(len(r)))
 a=[x['accepted_draft_length'] for x in r]; rejected=[len(x['actual_draft_tokens'])-x['accepted_draft_length'] for x in r]
 ax.bar(xx,a,color='#167a70',label='Accepted draft positions')
 ax.bar(xx,rejected,bottom=a,color='#d66545',label='Rejected draft positions')
 ax.bar(xx,[1]*len(r),bottom=[a+b for a,b in zip(a,rejected)],color='#8296ae',label='One additional verification row')
 ax.set_xticks(xx,[str(x['step']) for x in r]);ax.set_ylim(0,k+4);ax.set_yticks(range(0,k+2,2));ax.set_ylabel('Actual verification rows');ax.set_xlabel('Observed engine step');ax.set_title(f'{mode}: short_math, concurrency 2; quality FAIL retained',loc='left')
 ax.legend(ncol=3,loc='upper right',fontsize=8)
fig.suptitle('Real per-request verification rows and acceptance\nInstrumented observation batch; no speed ranking',fontsize=14)
fig.savefig(P/'results/verification-rows.png',dpi=160);fig.savefig(P/'results/verification-rows.svg');plt.close(fig)
# Actual GPU execution intervals, preserving CPU submission gaps; per-batch only.
t=json.loads((P/'raw/dflash-7/trace.json').read_text())['traceEvents']
ranges=[x for x in t if x.get('ph')=='X' and x.get('name','').startswith('stage/') and '/step=2' in x['name']]
outer=next(x for x in ranges if 'execute_model/' in x['name']);start=outer['ts']
rt={x.get('args',{}).get('correlation'):x for x in t if x.get('cat') in ['cuda_runtime','cuda_driver'] and 'correlation' in x.get('args',{})}
allranges=[x for x in t if x.get('ph')=='X' and (x.get('name','').startswith('stage/') or x.get('name','').startswith('obs.readback'))]
lanes=['Target forward','Rejection sampling','Effective-context prep','Draft propose','Other original stages','Observation readback']; colors=['#386cb0','#d66545','#b7950b','#167a70','#777777','#b88bc4'];intervals=[[] for _ in lanes]
for x in t:
 if x.get('cat') not in ['kernel','gpu_memcpy','gpu_memset']:continue
 call=rt.get(x.get('args',{}).get('correlation'))
 if call is None:continue
 rr=[r for r in allranges if r['tid']==call['tid'] and r['ts']<=call['ts']<=r['ts']+r['dur']]
 ss=[r for r in rr if '/step=2' in r['name'] and r['name'].endswith('=2')]
 if not ss:continue
 obs=[r for r in rr if r['name'].startswith('obs.')]
 name=min(obs or rr,key=lambda r:r['dur'])['name']
 i=5 if obs else 0 if '_model_forward' in name else 1 if 'rejection_sample' in name or 'RejectionSampler' in name else 2 if 'prepare_inputs' in name or 'set_inputs_first_pass' in name else 3 if '.propose' in name else 4
 intervals[i].append(((x['ts']-start)/1000,x['dur']/1000))
fig,ax=plt.subplots(figsize=(12,4),layout='constrained')
for i,(label,color,vals) in enumerate(zip(lanes,colors,intervals)):
 ax.broken_barh(vals,(i-.32,.64),facecolors=color)
ax.set_yticks(range(len(lanes)),[f'{label}\n{len(vals)} activities; {sum(d for _,d in vals)*1000:.1f} us' for label,vals in zip(lanes,intervals)]);ax.invert_yaxis();ax.set_xlabel('Actual GPU interval relative to CPU execute_model start (ms)')
ax.set_title('K7 observed step 2: GPU kernels/copies/memsets, linked by CUDA correlation\nShared GPU; gaps retained; batch attribution only; profiler/readbacks perturb timing')
ax.grid(axis='x',alpha=.2);fig.savefig(P/'results/gpu-timeline.png',dpi=160);fig.savefig(P/'results/gpu-timeline.svg')
