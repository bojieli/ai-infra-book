"""Audit rendered artists and sealed numerical inputs without author writes."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[1]
AUTHOR=PROJECT/'research/architecture-shapes'
sys.path.insert(0,str(PROJECT/'src'))
source=AUTHOR/'public/src/infra_calc/architecture_shape_plot.py'
spec=importlib.util.spec_from_file_location('review_shapes',source)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba


def main():
    data=m.calculate()
    assert data==json.loads((AUTHOR/'figures/data.json').read_text())
    assert len(data['inputs'])==4 and len(data['panels'])==6
    for row in data['inputs']:
        assert hashlib.sha256((PROJECT/row['file']).read_bytes()).hexdigest()==row['sha256']
    # Run original numerical assertions in-memory, removing only output-file mutation.
    original=(AUTHOR/'check.py').read_text()
    numerical=original[:original.index('files=[p,')]
    env={'__file__':str(AUTHOR/'check.py')}
    exec(compile(numerical,str(AUTHOR/'check.py'),'exec'),env)
    assert env['checks']==41
    with patch.object(plt,'close'):
        m.render(HERE/'rendered')
        fig=plt.gcf()
        rows=[]
        for i,panel in enumerate(data['panels']):
            axis=fig.axes[2*i if i<3 else 2*(i-3)+1]
            dense=panel['family']=='Dense'
            expected=panel['layers'] if dense else panel['experts']
            assert len(axis.patches)==expected
            width=.24*panel['hidden']/5120 if dense else .015*panel['intermediate']/3072
            assert all(abs(p.get_width()-width)<1e-14 for p in axis.patches)
            orange=[j for j,p in enumerate(axis.patches) if p.get_facecolor()==to_rgba('#D8672A')]
            assert orange==([] if dense else sorted(panel['first_recorded_route']['experts']))
            assert all(p.get_linewidth()==0 for p in axis.patches)
            texts=[x.get_text() for x in axis.texts]
            assert any('(released baseline)' in t for t in texts) if panel['released_baseline'] else any('(untrained)' in t for t in texts)
            assert any(f"{panel['total_parameters']:,}" in t for t in texts)
            assert any(f"{panel['parameter_delta']:+,}" in t for t in texts)
            rows.append(dict(name=panel['name'],family=panel['family'],patches=expected,width=width,orange_ids=orange,texts=texts))
    plt.close(fig)
    report={'status':'pass','author_numerical_checks_replayed_without_writes':41,'input_count':4,'panels':rows,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'original_png_sha256':hashlib.sha256((AUTHOR/'figures/figure.png').read_bytes()).hexdigest(),'visual_review':'Original PNG inspected: visible gaps; all six panels/titles/weight shapes/totals/deltas readable; no clipping or overlaps; orange row marker counts match source routes. Column scales differ explicitly.'}
    (HERE/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':'pass','panels':6,'patch_counts':[x['patches'] for x in rows]}))


if __name__=='__main__':main()
