"""Figure6-9: exact deadline staircases from verified cohort request traces."""
from pathlib import Path
from fractions import Fraction
import hashlib
import json
from .paths import PROJECT

DIRECTORY = PROJECT / 'figures/supernode-cost'


def scenario_names():
    return [f'{model}-n{requests}-d{deadline}-{profile}'
            for model in ('qwen3-8b','qwen3-32b') for requests in (1,4,8)
            for deadline in (80,250,600) for profile in ('healthy','short','long')]


def input_paths():
    return [Path(__file__), *[PROJECT/'results'/('supernode-'+name+'.json') for name in scenario_names()]]


def hashes(paths):
    return [{'file':str(p.relative_to(PROJECT)), 'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]


def verify():
    manifest=json.loads((DIRECTORY/'manifest.json').read_text())
    expected_inputs={str(p.relative_to(PROJECT)) for p in input_paths()}
    expected_artifacts={str((DIRECTORY/name).relative_to(PROJECT)) for name in ('figure.png','figure.svg','data.json')}
    for key,expected in [('inputs',expected_inputs),('artifacts',expected_artifacts)]:
        rows=manifest.get(key)
        if not isinstance(rows,list) or any(not isinstance(row,dict) for row in rows):
            raise ValueError('Malformed supernode figure manifest')
        names=[row.get('file') for row in rows]
        if len(names)!=len(expected) or set(names)!=expected:
            raise ValueError('Incomplete or duplicate supernode figure manifest')
        for row in rows:
            if hashlib.sha256((PROJECT/row['file']).read_bytes()).hexdigest()!=row['sha256']:
                raise ValueError('Stale supernode figure input/artifact: '+row['file'])
    return {'verified_figures':2}


def render():
    from .reproduce import verify_results
    verify_results(include_figures=False)
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams['svg.hashsalt']='ai-infra-book-supernode-cohort-v1'
    root=DIRECTORY
    root.mkdir(parents=True,exist_ok=True)
    results={name:json.loads((PROJECT/'results'/('supernode-'+name+'.json')).read_text()) for name in scenario_names()}
    fig,axes=plt.subplots(2,3,figsize=(15,8),sharex=True)
    colors={8:'#2166ac',4:'#e08214',2:'#198b5b'}
    curve_data=[]
    for row,model in enumerate(('qwen3-8b','qwen3-32b')):
        for col,count in enumerate((1,4,8)):
            ax=axes[row,col]
            for tag,style in [('healthy','-'),('long','--')]:
                result=results[f'{model}-n{count}-d600-{tag}']
                required=result['selection']['required_valid_requests']
                for candidate in result['candidates']:
                    if not candidate['capacity_fits']:
                        continue
                    cost=Fraction(candidate['cost']['full_declared_cost_exact'])
                    deadline=np.arange(1,1001)
                    values=[];records=[]
                    for limit in deadline:
                        valid=sum(r['latency_ms']<=int(limit) for r in candidate['schedule']['requests'])
                        exact=str(cost/valid) if valid>=required else None
                        values.append(float(Fraction(exact)) if exact is not None else np.nan)
                        records.append(dict(deadline_ms=int(limit),valid=valid,cost_per_valid_exact=exact))
                    ax.step(deadline,values,where='post',color=colors[candidate['tp']],linestyle=style,
                            label=f"TP{candidate['tp']} x {candidate['replicas']} replicas / {tag}")
                    curve_data.append(dict(model=model,requests=count,profile=tag,candidate=candidate['id'],points=records))
            ax.set_title(f'{model} | {count} simultaneous requests')
            ax.grid(alpha=.2);ax.set_xlim(0,1000)
            ax.set_xlabel('Completion deadline (ms)')
            if col==0:ax.set_ylabel('Declared credit / SLO-valid request')
    handles,labels=axes[0,0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='lower center',ncol=3,fontsize=9,bbox_to_anchor=(.5,.025))
    fig.suptitle('Figure 6-9: same eight cards, capacity + failure + SLO + cost',fontsize=15)
    fig.text(.5,.005,'Only >=75% valid completion is shown. Gaps mean ineligible. Solid: healthy; dashed: failure at50ms, recovery200ms +1 external credit. Teaching inputs.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.12,1,.95))
    for ext in ('png','svg'):
        fig.savefig(root/f'figure.{ext}',dpi=150,**({'metadata':{'Date':None}} if ext=='svg' else {}))
    (root/'data.json').write_text(json.dumps(curve_data,indent=2)+'\n')
    artifacts=[root/name for name in ('figure.png','figure.svg','data.json')]
    manifest={'scope':'Same eight cards; declared service, price and recovery assumptions; only >=75% SLO-valid shown',
              'inputs':hashes(input_paths()),'artifacts':hashes(artifacts)}
    (root/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    plt.close(fig)
    return {'directory':str(root.relative_to(PROJECT)), **verify()}
