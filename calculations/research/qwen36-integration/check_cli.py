"""Exercise actual public commands and check CSV accounting, not only imports."""
from pathlib import Path
import csv
import io
import json
import subprocess
import sys
import tempfile

project = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project / 'src'))
from infra_calc.topics import qwen36_forward, qwen36_capacity
from infra_calc import report

book = json.loads((project / 'scenarios/book.json').read_text())
checks = []
with tempfile.TemporaryDirectory(prefix='qwen36-cli-') as directory:
    inputs = Path(directory)/'inputs.json'
    for group, command, module in [('qwen36_forward', 'qwen36-forward', qwen36_forward),
                                   ('qwen36_capacity', 'qwen36-capacity', qwen36_capacity)]:
        for scene in book[group]:
            inputs.write_text(json.dumps(scene['inputs']))
            result = module.calculate(**scene['inputs'])
            formats = ['json', 'md', 'csv'] if group == 'qwen36_forward' else ['json', 'md']
            for format_name in formats:
                args = [sys.executable, str(project/'calc.py'), command, '--inputs', str(inputs), '--format', format_name]
                output = subprocess.check_output(args, text=True)
                if format_name == 'json':
                    assert json.loads(output) == result
                elif format_name == 'md':
                    assert output.strip() == report.markdown(result).strip()
                    assert str(result['summary'].get('base_text_parameters', result['summary'].get('necessary_budget_bytes'))) in output
                else:
                    rows = list(csv.DictReader(io.StringIO(output)))
                    for metric in ['matrix_flops', 'scalar_flops', 'weight_read_bytes', 'activation_read_bytes', 'activation_write_bytes']:
                        assert sum(int(row[metric])*int(row['repeats']) for row in rows) == result['summary'][metric]
                checks.append({'scenario':scene['id'], 'format':format_name, 'passed':True})
(project/'research/qwen36-integration/cli-check.json').write_text(json.dumps({'status':'passed','actual_invocations':len(checks),'checks':checks},indent=2)+'\n')
print(f'{len(checks)} actual CLI output checks passed')
