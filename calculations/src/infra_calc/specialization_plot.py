"""Optional Matplotlib figure derived from verified specialization results."""
import hashlib
import json
from fractions import Fraction
from pathlib import Path
from .paths import PROJECT


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    manifest_path=PROJECT/'figures/specialization/manifest.json'
    if not manifest_path.exists():
        return dict(verified_figures=0)
    manifest=json.loads(manifest_path.read_text())
    for entry in manifest['inputs']+manifest['artifacts']:
        if digest(PROJECT/entry['file'])!=entry['sha256']:
            raise ValueError('Specialization figure stale: '+entry['file']+'; run plot-specialization')
    return dict(verified_figures=len(manifest['artifacts']))


def render():
    from .reproduce import verify_results
    verify_results(include_figures=False)
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ValueError('Plotting requires the optional plot dependency; install calculations[plot]') from exc
    source=PROJECT/'results/specialization-medium.json'
    result=json.loads(source.read_text())
    rows=result['specialization_policies']
    output=PROJECT/'figures/specialization';output.mkdir(parents=True,exist_ok=True)
    samples=[]
    for n in range(151):
        totals={row['policy']:Fraction(row['prepare_ns'])+n*Fraction(row['cohort_execution_exact_ns']) for row in rows}
        samples.append(dict(repetitions=n,total_exact_ns={k:str(v) for k,v in totals.items()},
                            minimum=min(totals,key=totals.get)))
    data=dict(source=str(source.relative_to(PROJECT)),scope='Teaching single-layer FFN serial costs',
              samples=samples,crossings=result['specialization_crossings'])
    (output/'data.json').write_text(json.dumps(data,indent=2)+'\n')
    # Fixed metadata and SVG ids make rerendering deterministic in the same environment.
    plt.rcParams.update({'svg.hashsalt':'infra-calc-specialization','font.family':'DejaVu Sans','font.size':11})
    fig,ax=plt.subplots(figsize=(10,6),layout='constrained')
    colors={'generic':'#3156A6','bucket':'#C16C13','specialized':'#24856B'}
    labels={'generic':'Generic','bucket':'Bucketed','specialized':'Exact shapes'}
    for row in rows:
        name=row['policy']
        y=[float(Fraction(sample['total_exact_ns'][name])/10**9) for sample in samples]
        ax.plot(range(151),y,label=labels[name],color=colors[name],linewidth=2.4)
    for cross in result['specialization_crossings']:
        raw=cross['equality_repetitions_exact']
        if raw is None:continue
        x=Fraction(raw)
        if not 0<x<150:continue
        a=next(row for row in rows if row['policy']==cross['policy_a'])
        y=(a['prepare_ns']+x*Fraction(a['cohort_execution_exact_ns']))/10**9
        ax.scatter([float(x)],[float(y)],s=28,color='#333333',zorder=4)
        ax.annotate(f'{float(x):.2f}',(float(x),float(y)),xytext=(7,8),textcoords='offset points',fontsize=9)
    ax.set(xlim=(0,150),ylim=(0,None),xlabel='Repeated workload groups (10 calls per group)',
           ylabel='Preparation + execution time (seconds)',title='Qwen3-8B: when shape preparation pays off')
    ax.grid(alpha=.18);ax.legend(loc='upper left')
    fig.supxlabel('Teaching rates and preparation costs; one FFN layer. Zero shows the preparation intercept.',fontsize=9)
    fig.savefig(output/'figure.svg',metadata={'Date':None})
    fig.savefig(output/'figure.png',dpi=160,metadata={'Software':'infra-calc'})
    plt.close(fig)
    inputs=[source,Path(__file__),PROJECT/'pyproject.toml']
    artifacts=[output/name for name in ('figure.svg','figure.png','data.json')]
    manifest=dict(matplotlib_version=matplotlib.__version__,
                  inputs=[dict(file=str(p.relative_to(PROJECT)),sha256=digest(p)) for p in inputs],
                  artifacts=[dict(file=str(p.relative_to(PROJECT)),sha256=digest(p)) for p in artifacts])
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return dict(directory=str(output),**verify())
