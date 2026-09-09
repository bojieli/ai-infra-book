"""Figure12-1: declared file request budget and exact bandwidth curves."""
from pathlib import Path
from fractions import Fraction
import hashlib
import json
from .paths import PROJECT

DIRECTORY = PROJECT / 'figures/image-request'


def input_paths():
    import json
    rows=json.loads((PROJECT/'scenarios/book.json').read_text())['image_request_budget']
    return [Path(__file__), PROJECT/'src/infra_calc/topics/image_request_budget.py',
            *[PROJECT/'results'/(row['id']+'.json') for row in rows]]


def hashes(paths):
    return [{'file':str(p.relative_to(PROJECT)), 'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]


def verify():
    manifest=json.loads((DIRECTORY/'manifest.json').read_text())
    expected_inputs={str(p.relative_to(PROJECT)) for p in input_paths()}
    expected_artifacts={str((DIRECTORY/name).relative_to(PROJECT)) for name in ('figure.png','figure.svg','curve-data.json')}
    for key,expected in [('inputs',expected_inputs),('artifacts',expected_artifacts)]:
        rows=manifest.get(key)
        if not isinstance(rows,list) or any(not isinstance(row,dict) for row in rows):
            raise ValueError('Malformed image request figure manifest')
        names=[row.get('file') for row in rows]
        if len(names)!=len(expected) or set(names)!=expected:
            raise ValueError('Incomplete or duplicate image request figure manifest')
        for row in rows:
            if hashlib.sha256((PROJECT/row['file']).read_bytes()).hexdigest()!=row['sha256']:
                raise ValueError('Stale image request figure input/artifact: '+row['file'])
    return {'verified_figures':2}



def render():
    from .reproduce import verify_results
    verify_results(include_figures=False)
    from .topics import image_request_budget as module
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    HERE=DIRECTORY
    HERE.mkdir(parents=True,exist_ok=True)
    archived=json.loads((PROJECT/'results/image-request-original.json').read_text())
    baseline = module.calculate()
    assert baseline == archived
    assert baseline['variants'][0]['complete_final_image_seconds_exact'] == '64/5'
    compression = dict(transmitted_bytes=15_000_000, extra_encode_seconds='1/5',
        extra_decode_seconds='1/10', comparison_authorized=True,
        quality_contract='same original information and same final-image requirement')
    points = []
    for mbps in range(10, 801):
        rate = mbps*1_000_000
        ordinary = module.calculate(upload_bits_per_second=rate, local_seconds='5', compression=compression)
        faster = module.calculate(upload_bits_per_second=rate, model_seconds='3/100', local_seconds='5')
        original, compressed = ordinary['variants']
        accelerated = faster['variants'][0]
        row = dict(upload_bits_per_second=rate,
            original_seconds_exact=original['complete_final_image_seconds_exact'],
            compressed_seconds_exact=compressed['complete_final_image_seconds_exact'],
            faster_model_seconds_exact=accelerated['complete_final_image_seconds_exact'],
            local_seconds_exact='5', preview_ready_seconds=None)
        # Independent closed-form check; Mb/s and MB retain decimal units.
        assert Fraction(row['original_seconds_exact']) == Fraction(4,5)+Fraction(240,mbps)
        assert Fraction(row['compressed_seconds_exact']) == Fraction(11,10)+Fraction(120,mbps)
        assert Fraction(row['faster_model_seconds_exact']) == Fraction(53,100)+Fraction(240,mbps)
        points.append(row)
    data = dict(figure='12-1', metadata_kind='declared_teaching',
        comparison_endpoint='usable complete final image; preview unknown',
        baseline=baseline['variants'][0], quality_contract=baseline['scenario']['quality_contract'],
        compressed_quality_authorization='caller assertion, not a codec or quality measurement',
        compression=compression, sample_points=points,
        formulas_seconds=dict(original='4/5 + 240000000/upload_bits_per_second',
            compressed='11/10 + 120000000/upload_bits_per_second',
            faster_model='53/100 + 240000000/upload_bits_per_second', local='5'),
        interpretation='RTT is an additive residual request budget, not placement before upload on an observed timeline.')
    (HERE/'curve-data.json').write_text(json.dumps(data, indent=2)+'\n')
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,
        'axes.spines.top':False,'axes.spines.right':False,'svg.hashsalt':'image-request-budget-figure12-1-v1',
        'svg.fonttype':'none','figure.facecolor':'white','axes.facecolor':'white'})
    fig = plt.figure(figsize=(12, 8.4))
    ax = fig.add_axes([.08,.64,.88,.14])
    curve = fig.add_axes([.08,.18,.88,.34])
    fig.text(.08,.95,'Figure 12-1  |  Image request: data, budget and upload rate', fontsize=18, weight='bold')
    fig.text(.08,.915,'Declared teaching inputs • Complete usable final image • No codec or network execution', fontsize=10, color='#555555')
    fig.text(.08,.86,'30 MB RAW  →  full upload  →  model  →  final encode  →  5 MB JPEG download  →  usable image', fontsize=11)
    fig.text(.08,.825,'A. At 20 Mb/s upload and 100 Mb/s download: 12.8 s complete-image budget', fontsize=12, weight='bold')
    palette={'upload':'#2166ac','model':'#1b9e77','download':'#e6ab02','request_round_trip':'#8856a7'}
    # This is an additive budget composition, deliberately not an event timeline.
    left=0
    display_order=['upload','model','download','request_round_trip']
    durations={r['stage']:Fraction(r['duration_seconds_exact']) for r in data['baseline']['stages']}
    for name in display_order:
        seconds=float(durations[name]);ax.barh(0, seconds, left=left, height=.47, color=palette[name], edgecolor='white', linewidth=.8)
        left+=seconds
    ax.text(6,0,'Upload: 12.0 s',ha='center',va='center',color='white',fontsize=12,weight='bold')
    ax.annotate('12.8 s',xy=(12.8,0),xytext=(13.0,0),va='center',fontsize=12,weight='bold')
    ax.set_xlim(0,14);ax.set_ylim(-.65,.65);ax.set_yticks([])
    ax.set_xlabel('Additive seconds — budget composition, not chronological placement of RTT')
    ax.spines['left'].set_visible(False);ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=palette[k],label=label) for k,label in [
        ('upload','Upload 12.0 s'),('model','Model 0.3 s'),('download','Download 0.4 s'),('request_round_trip','Residual RTT budget 0.1 s')]],
        loc='upper left',bbox_to_anchor=(0,1.12),ncol=4,frameon=False,fontsize=9)
    fig.text(.08,.55,'B. Complete-image time vs upload rate; download fixed at 100 Mb/s',fontsize=12,weight='bold')
    x=[r['upload_bits_per_second']/1e6 for r in points]
    specs=[('original_seconds_exact','#2166ac','-','Original 30 MB; model 0.30 s'),
           ('compressed_seconds_exact','#d95f02','-','Compressed 15 MB; extra codec 0.30 s'),
           ('faster_model_seconds_exact','#1b9e77','--','Original 30 MB; faster model 0.03 s'),
           ('local_seconds_exact','#555555',':','Local complete-image time: 5 s')]
    for key,color,style,label in specs:
        curve.plot(x,[float(Fraction(r[key])) for r in points],color=color,linestyle=style,lw=2,label=label)
    curve.set_xscale('log');curve.set_xlim(10,800);curve.set_ylim(0,26)
    curve.set_xticks([10,20,50,100,200,400,800]);curve.set_xticklabels(['10','20','50','100','200','400','800'])
    curve.set_xlabel('Upload rate (Mb/s, decimal)');curve.set_ylabel('Complete final image (s)')
    curve.grid(which='major',alpha=.18);curve.legend(loc='upper right',frameon=False,fontsize=9)
    curve.scatter([20,20],[12.8,7.1],s=30,c=['#2166ac','#d95f02'],zorder=5)
    curve.annotate('20 Mb/s: 12.8 s original\n12.53 s with faster model',xy=(20,12.8),xytext=(30,15),
                   arrowprops={'arrowstyle':'-','color':'#666666'},fontsize=9)
    curve.annotate('20 Mb/s: 7.1 s compressed',xy=(20,7.1),xytext=(12,9.4),
                   arrowprops={'arrowstyle':'-','color':'#666666'},fontsize=9)
    fig.text(.08,.10,'Same final-image requirement is asserted for compression and local comparison; quality is not measured.',fontsize=9,color='#444444')
    fig.text(.08,.074,'Connection, queue, preparation, final encoding and output-use terms are declared zero here. Preview readiness is unknown.',fontsize=9,color='#444444')
    fig.text(.08,.048,'RTT is charged once as a residual control/propagation budget. Curves are exact serial budgets, not measured service times.',fontsize=9,color='#444444')
    fig.savefig(HERE/'figure.svg',metadata={'Date':None,'Creator':'image-request-budget plot.py'})
    fig.savefig(HERE/'figure.png',dpi=160,metadata={'Software':'image-request-budget plot.py'})
    plt.close(fig)
    manifest={'inputs':hashes(input_paths()),
              'artifacts':hashes([HERE/name for name in ('figure.png','figure.svg','curve-data.json')]),
              'scope':'Declared complete-image budgets; no preview or measured quality/runtime claim'}
    (HERE/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return {'directory':str(HERE.relative_to(PROJECT)), **verify()}
