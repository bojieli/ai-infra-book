"""Independent prewritten integer oracles, checked against the frozen candidate."""
import hashlib
import importlib.util
import json
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('retry_candidate', ROOT / 'calculate.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def main():
    source_hash = hashlib.sha256((ROOT / 'calculate.py').read_bytes()).hexdigest()
    normal = json.loads((ROOT / 'root-normal-input.json').read_text())
    checks = []
    for name, expected in [('none', 10), ('hrr', 14), ('retry', 14), ('psk_unknown_fallback', 10)]:
        inputs = dict(normal, handshake_event=name, application_retry_authorized=False,
                      application_early_data_authorized=False)
        result = module.calculate(inputs)
        assert F(result['milestones']['complete_response']) == expected
        assert result['summary']['early_payload_sent_bytes'] == 0
        assert result['summary']['application_execution_count'] == 1
        checks.append(name + ': no-early first request needs no replay permission')
    early = json.loads((ROOT / 'root-early-retry-input.json').read_text())
    result = module.calculate(early)
    assert result['summary']['early_payload_sent_bytes'] == 8176
    assert result['summary']['accepted_unique_request_bytes'] == 4672
    assert F(result['milestones']['complete_response']) == 12
    packets = [p for p in result['transmissions'] if p['kind'] == 'request']
    assert [p['packet_number'] for p in packets] == list(range(7))
    assert [p['offset'] for p in packets] == [0, 1168, 2336, 0, 1168, 2336, 3504]
    checks.append('Retry reattempt remains early: new PN, same STREAM prefix')
    result = module.calculate(dict(early, handshake_event='selected_binder_invalid'))
    data = [p for p in result['transmissions'] if p['kind'] == 'request']
    close = [p for p in result['transmissions'] if p['kind'] == 'failure']
    assert len(close) == 1 and close[0]['packet_number_space'] == 'initial'
    assert F(close[0]['start']) == 2 and F(close[0]['arrival']) == 4
    assert [(F(p['start']), F(p['end'])) for p in data] == [(1, 2), (2, 3), (3, 4)]
    assert result['summary']['application_execution_count'] == 0
    assert result['summary']['accepted_unique_request_bytes'] == 0
    assert F(result['summary']['last_modeled_arrival']) == 5
    checks.append('Fatal notification propagates before client stops; in-flight packets remain')
    assert source_hash == hashlib.sha256((ROOT / 'calculate.py').read_bytes()).hexdigest()
    report = dict(status='passed', source_sha256=source_hash, checks=checks)
    (ROOT / 'root-check.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
