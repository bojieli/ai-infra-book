"""Archived distributions and explicitly hypothetical KV retention."""
from pathlib import Path
import sys,json,hashlib
P=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(P/'src'))
from infra_calc.topics import agent_trace,trace_resource_bridge


def calculate():
    raw,lock=agent_trace.read_trace('thinking-on')
    bridge=trace_resource_bridge.calculate()
    account=agent_trace.calculate('thinking-on')
    if len(raw['rounds.jsonl']) != len(account['agent_rounds']):
        raise ValueError('Agent row count mismatch')
    rows=[]
    for r,a in zip(raw['rounds.jsonl'],account['agent_rounds']):
        if r['turn'] != a['turn']:
            raise ValueError('Agent turn identity mismatch')
        ids=r['output_token_ids'];marker=r['reasoning_end_token_id']
        boundary=ids.index(marker)+1 if marker in ids else None
        event=next((x['t_s'] for x in r['output_events'] if boundary is not None and x['token_count']>=boundary),None)
        rows.append(dict(turn=r['turn'],input_tokens=len(r['prompt_token_ids']),output_tokens=len(ids),cached_tokens=r['cached_tokens'],
            reasoning_boundary_count=boundary,reasoning_boundary_observed_seconds=event,
            finish_reason=r['finish_reason'],model_start=r['model_start_s'],model_end=r['model_end_s'],
            tool_start=r['tool_start_s'],tool_end=r['tool_end_s'],
            hypothetical_retained_kv_bytes=a['retained_logical_kv_bytes']))
    return dict(agent=rows,chat=[dict(request=x['request'],input_tokens=x['recorded']['input_tokens'],output_tokens=x['recorded']['returned_id_tokens'],cached_tokens=x['recorded']['cached_tokens']) for x in bridge['calls']],sources=account['sources'],chat_sources=bridge['trace_sources'],
        scope='Reasoning marker count includes the delimiter; event time is first observed stream event reaching it, not GPU phase time. Missing marker stays unknown. KV bars assume final logical state retained during tool wait; no observed block lifetime.')


def render(output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    d=calculate();output.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'svg.hashsalt':'infra-chat-agent','font.family':'DejaVu Sans'})
    fig,axes=plt.subplots(3,2,figsize=(13,11),layout='constrained')
    for ax,key in zip(axes[0],('chat','agent')):
        rows=d[key];x=list(range(len(rows)))
        for metric,offset,color in [('input_tokens',-.25,'#426b9a'),('cached_tokens',0,'#3f927d'),('output_tokens',.25,'#de9852')]:
            ax.bar([i+offset for i in x],[r[metric] for r in rows],.23,label=metric,color=color)
        ax.set(title=key.title()+': all captured calls',xlabel='Call / round',ylabel='Token IDs',xticks=x)
        ax.legend(fontsize=8)
    ax=axes[1,0]
    for r in d['agent']:
        i=r['turn'];ax.barh(i,r['model_end']-r['model_start'],left=r['model_start'],color='#426b9a')
        ax.plot([r['tool_start'],r['tool_end']],[i,i],color='#bd493b',lw=4)
        if r['reasoning_boundary_observed_seconds'] is not None:ax.scatter(r['reasoning_boundary_observed_seconds'],i,marker='|',s=180,color='black')
    ax.set(title='Agent: recorded application intervals',xlabel='Seconds from run start',ylabel='Round',yticks=range(4))
    ax.text(.02,.98,'Blue: model call; red: tool; black: marker event',transform=ax.transAxes,va='top',fontsize=8)
    ax=axes[1,1]
    for r in d['agent']:
        i=r['turn'];boundary=r['reasoning_boundary_count']
        if boundary is None:
            ax.barh(i,r['output_tokens'],color='#b9bec7',hatch='///');ax.text(r['output_tokens']/2,i,'boundary not observed',ha='center',va='center',fontsize=8)
        else:
            ax.barh(i,boundary,color='#8b79ae');ax.barh(i,r['output_tokens']-boundary,left=boundary,color='#de9852')
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color='#8b79ae',label='Through marker'),Patch(color='#de9852',label='After marker'),Patch(facecolor='#b9bec7',hatch='///',label='Boundary unknown')],fontsize=8,loc='upper right')
    ax.set(title='Returned IDs: through marker / after marker',xlabel='Token IDs (delimiter included)',ylabel='Round',yticks=range(4))
    ax=axes[2,0]
    values=[1000*(r['tool_end']-r['tool_start']) for r in d['agent']]
    ax.bar(range(4),values,color='#bd493b')
    for i,v in enumerate(values):ax.annotate(f'{v:.3f}',(i,v),xytext=(0,4),textcoords='offset points',ha='center',fontsize=9)
    ax.set(title='Tool waits on a separate scale',xlabel='Round',ylabel='Recorded milliseconds',xticks=range(4));ax.margins(y=.2)
    ax=axes[2,1]
    ax.bar(range(4),[r['hypothetical_retained_kv_bytes']/2**20 for r in d['agent']],color='#3f927d',hatch='//')
    ax.set(title='Declared KV retained during each tool wait',xlabel='Round',ylabel='Logical BF16 MiB; not measured residency',xticks=range(4))
    fig.suptitle('Chat and Agent: lengths, reuse and state\nCaptured calls, observed tool intervals, conditional KV policy',fontsize=15)
    for fmt in ('png','svg','pdf'):
        metadata={'Date':None} if fmt=='svg' else {'CreationDate':None,'ModDate':None} if fmt=='pdf' else {'Software':'infra-calc'}
        fig.savefig(output/('figure.'+fmt),dpi=160,metadata=metadata)
    plt.close(fig)
    (output/'data.json').write_text(json.dumps(d,indent=2)+'\n')
    inputs={x['file'] for x in d['sources']}
    inputs.update('sources/trace-resource-bridge/'+x['file'] for x in d['chat_sources'])
    inputs.update(['configs/agent-traces.lock.json','sources/trace-resource-bridge/sources.lock.json'])
    inputs.update(str(x.relative_to(P)) for x in (P/'src/infra_calc').rglob('*.py'))
    inputs.add(str(Path(__file__).relative_to(P)))
    def record(path):
        return dict(file=str(path.relative_to(P)),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    manifest=dict(inputs=[record(P/x) for x in sorted(inputs)],artifacts=[record(output/name) for name in ('figure.png','figure.svg','figure.pdf','data.json')])
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return d

if __name__=='__main__':render(Path(__file__).resolve().parent/'figure')
