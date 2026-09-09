"""Check bounded parallel-agent reading, source identity and own arithmetic."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
D=ROOT/'references/framework-history/2026-09-09/spindle-wavefront'


def verify():
    inventory=json.loads((D/'inventory.json').read_text())
    for f in inventory['files']:
        b=(D/f['file']).read_bytes()
        assert len(b)==f['bytes'] and hashlib.sha256(b).hexdigest()==f['sha256']
    sources=json.loads((D/'sources.json').read_text())
    assert len(sources)==9
    for s in sources:
        b=(D/s['file']).read_bytes()
        assert s['status']==200 and len(b)==s['bytes'] and hashlib.sha256(b).hexdigest()==s['sha256']
    reading=json.loads((D/'reading.json').read_text())
    assert len(reading['source_reading'])==5
    for r in reading['source_reading']:
        b=(D/r['file']).read_bytes();lines=b.decode().splitlines(keepends=True)
        assert hashlib.sha256(b).hexdigest()==r['sha256'] and len(lines)==r['total_lines']
        assert len(r['line_ranges'])==len(r['range_sha256'])
        for (lo,hi),proof in zip(r['line_ranges'],r['range_sha256']):
            assert 1<=lo<=hi<=len(lines)
            assert proof['first']==lo and proof['last']==hi
            assert hashlib.sha256(''.join(lines[lo-1:hi]).encode()).hexdigest()==proof['sha256']
    commit=json.loads((D/'sources/spindle-commit.json').read_text())
    assert commit['sha']=='1c03a149c3aabcf3eac9585d44dd5cec8933edff'
    assert commit['commit']['committer']['date'].startswith('2025-03-19')
    assert (D/'spindle-reading.json').read_bytes()==(ROOT/'references/proceedings/ASPLOS/2025/spindle-reading.json').read_bytes()
    before=(D/'arithmetic.json').read_bytes()
    subprocess.run([sys.executable,str(D/'arithmetic.py')],check=True,stdout=subprocess.PIPE)
    assert (D/'arithmetic.json').read_bytes()==before
    a=json.loads(before)
    assert a['incremental_handoff_break_even_ms']==1
    assert a['restart_teaching_budget']['strictly_profitable_steps']==1201
    result=dict(verified_at=datetime.now(timezone.utc).isoformat(),status='passed',raw_responses=9,
                source_scopes=5,selected_body_pages=15,body_page_views=8,
                scope='Selected paper/source ranges and independent teaching arithmetic; no full runtime or GPU reproduction.')
    (ROOT/'research/2026-infra-survey/qa/spindle-phase.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result


if __name__=='__main__':
    print(json.dumps(verify(),ensure_ascii=False))
