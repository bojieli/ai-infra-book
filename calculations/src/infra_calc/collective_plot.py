"""Six-panel directed-link loads from the verified 16-node path enumeration."""
import json
import math
from pathlib import Path
from .paths import PROJECT
from .specialization_plot import digest


def verify():
    path=PROJECT/'figures/collective-paths/manifest.json'
    if not path.exists():return dict(verified_figures=0)
    manifest=json.loads(path.read_text())
    for entry in manifest['inputs']+manifest['artifacts']:
        if digest(PROJECT/entry['file'])!=entry['sha256']:
            raise ValueError('Collective path figure stale: '+entry['file']+'; run plot-collective-paths')
    return dict(verified_figures=len(manifest['artifacts']))


def panels(result):
    """Keep the full directed-edge table, including zero-load directions."""
    output=[]
    for pattern in result['collective_path_patterns']:
        for row in pattern['rounds']:
            edges=[dict(sender=a,receiver=(a+d)%16,bytes=row['directed_link_bytes'].get(f'{a}->{(a+d)%16}',0))
                   for a in range(16) for d in (-1,1)]
            route=next(route for route in row['routes'] if route['sender']==0)
            output.append(dict(pattern=pattern['pattern'],round=row['round'],edges=edges,
                               message_bytes=row['message_bytes'],physical_link_bytes=row['physical_link_bytes'],
                               peak_link_bytes=row['peak_link_bytes'],peak_link_messages=row['peak_link_messages'],
                               rank_zero_path=[0]+[b for a,b in route['path']]))
    return output


def render():
    from .reproduce import verify_results
    verify_results(include_figures=False)
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib.patches import FancyArrowPatch
        from matplotlib.colors import Normalize
        from matplotlib.cm import ScalarMappable
    except ImportError as exc:
        raise ValueError('Install the optional calculations[plot] dependency') from exc
    source=PROJECT/'results/collective-paths-book.json'
    result=json.loads(source.read_text());data=panels(result)
    if len(data)!=6:raise ValueError('Figure requires the verified three-round, two-pattern case')
    output=PROJECT/'figures/collective-paths';output.mkdir(parents=True,exist_ok=True)
    (output/'data.json').write_text(json.dumps(dict(source=str(source.relative_to(PROJECT)),panels=data),indent=2)+'\n')
    plt.rcParams.update({'svg.hashsalt':'infra-calc-directed-ring','font.family':'DejaVu Sans','font.size':10})
    fig,axes=plt.subplots(2,3,figsize=(13,9),layout='constrained')
    maximum=max(edge['bytes'] for panel in data for edge in panel['edges'])/2**20
    norm=Normalize(0,maximum);cmap=plt.get_cmap('viridis')
    def point(node,radius):
        angle=math.pi/2-2*math.pi*node/16
        return radius*math.cos(angle),radius*math.sin(angle)
    for ax,panel in zip(axes.flat,data):
        for edge in panel['edges']:
            a,b=edge['sender'],edge['receiver'];value=edge['bytes']/2**20
            radius=.90 if (b-a)%16==1 else 1.14
            x0,y0=point(a,radius);x1,y1=point(b,radius)
            # Two radii separate opposite directions; arrowheads preserve orientation.
            start=(x0+.14*(x1-x0),y0+.14*(y1-y0))
            end=(x0+.86*(x1-x0),y0+.86*(y1-y0))
            arrow=FancyArrowPatch(start,end,arrowstyle='-|>',mutation_scale=9,
                                  linewidth=.6+2.5*value/maximum,
                                  color=cmap(norm(value)) if value else '#D8D8D8')
            ax.add_patch(arrow)
        for node in range(16):
            x,y=point(node,1.36)
            ax.text(x,y,str(node),ha='center',va='center',fontsize=8)
        ax.text(0,.19,f"Peak: {panel['peak_link_bytes']/2**20:g} MiB/link",ha='center',fontsize=10)
        ax.text(0,-.04,f"{panel['peak_link_messages']} message{'s' if panel['peak_link_messages'] != 1 else ''} on busiest link",ha='center',fontsize=8)
        ax.text(0,-.28,f"All links: {panel['physical_link_bytes']/2**20:g} MiB",ha='center',fontsize=9)
        ax.set_title(f"{panel['pattern'].capitalize()} · round {panel['round']}\n{panel['message_bytes']/2**20:g} MiB per message",fontsize=11)
        ax.text(.5,-.03,'Rank 0 route: '+' → '.join(map(str,panel['rank_zero_path'])),transform=ax.transAxes,ha='center',fontsize=8)
        ax.set(xlim=(-1.6,1.6),ylim=(-1.6,1.6),aspect='equal');ax.axis('off')
    colorbar=fig.colorbar(ScalarMappable(norm=norm,cmap=cmap),ax=axes,shrink=.70,pad=.02)
    colorbar.set_label('Bytes per directed link per round (MiB)')
    fig.suptitle('Same logical messages, different physical link loads',fontsize=17)
    fig.supxlabel('Inner arrows clockwise; outer counterclockwise; gray = no traffic · all 16 senders counted\nFirst three reduce-scatter rounds only; not full all-reduce performance.',fontsize=10)
    fig.savefig(output/'figure.svg',metadata={'Date':None})
    fig.savefig(output/'figure.png',dpi=160,metadata={'Software':'infra-calc'})
    plt.close(fig)
    inputs=[source,Path(__file__),Path(__file__).with_name('specialization_plot.py'),PROJECT/'pyproject.toml']
    artifacts=[output/name for name in ('figure.svg','figure.png','data.json')]
    manifest=dict(matplotlib_version=matplotlib.__version__,
                  inputs=[dict(file=str(p.relative_to(PROJECT)),sha256=digest(p)) for p in inputs],
                  artifacts=[dict(file=str(p.relative_to(PROJECT)),sha256=digest(p)) for p in artifacts])
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return dict(directory=str(output),**verify())
