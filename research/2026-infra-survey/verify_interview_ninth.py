"""Check public-source attribution and independent three-batch arithmetic only."""
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from urllib.parse import unquote, urlsplit
import hashlib
import json
import re
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'references/interviews/2026-09-09/ninth-pass'


def check_file(meta):
    data = (ROOT / meta['file']).read_bytes()
    assert len(data) == meta['bytes']
    assert hashlib.sha256(data).hexdigest() == meta['sha256']


def public_post(name):
    soup = BeautifulSoup((BASE / name).read_bytes(), 'html.parser')
    script = next(s.get_text() for s in soup.find_all('script')
                  if s.get_text().startswith('window.__INITIAL_STATE__='))
    state = json.JSONDecoder().raw_decode(script.split('=', 1)[1])[0]
    return state['prefetchData']['2']['ssrCommonData']['contentData']


def calculate():
    # Explicit intervals; no framework or general scheduling simulator is run.
    plans = {
        'admit_immediately': [('S0', 0, 100, 1), ('S1', 90, 190, 1), ('L', 190, 290, 8)],
        'reserve_group': [('S0', 0, 100, 1), ('L', 100, 200, 8), ('S1', 200, 300, 1)],
        'short_backfill': [('S0', 0, 100, 1), ('S1', 90, 100, 1), ('L', 100, 200, 8)],
    }
    results = {}
    for name, plan in plans.items():
        for task, start, end, width in plan:
            assert start >= (90 if task == 'S1' else 0) and end > start
            assert end - start == (10 if name == 'short_backfill' and task == 'S1' else 100)
            assert width == (8 if task == 'L' else 1)
        # Every event interval must fit all eight GPUs, including simultaneous ends/starts.
        points = sorted({x for _, a, b, _ in plan for x in (a, b)})
        for a, b in zip(points, points[1:]):
            assert sum(w for _, s, e, w in plan if s < b and e > a) <= 8
        completion = {task: end for task, _, end, _ in plan}
        work = sum((end - start) * width for _, start, end, width in plan)
        results[name] = dict(intervals=plan, completion_ms=completion,
                             gpu_ms=work, large_deadline_met=completion['L'] <= 200,
                             small_deadline_met=completion['S1'] <= 350)
    assert results['admit_immediately']['gpu_ms'] == results['reserve_group']['gpu_ms'] == 1000
    assert not results['admit_immediately']['large_deadline_met']
    assert all(results[p]['large_deadline_met'] for p in ['reserve_group', 'short_backfill'])
    assert 100 + 40 + 100 == 240 > 200
    return dict(plans=results, fixed_observation_ms=300,
                work_fraction=str(Fraction(1000, 8 * 300)),
                work_percent=float(Fraction(1000, 8 * 300) * 100),
                restore_lower_bound_ms=240,
                scope='Book-authored finite intervals with zero switching, plus separate nonoverlappable 40 ms recovery. Not model timings or a stability proof.')


def verify():
    sources = json.loads((BASE / 'sources.json').read_text())
    proof = json.loads((BASE / 'reading-proof.json').read_text())
    assert len(sources) == len(proof['records']) == 6
    for meta in sources + proof['web_extracts'] + proof['reused_inputs']:
        check_file(meta)
    assert {x['id'] for x in sources} == {x['source_id'] for x in proof['records']}
    assert sum(x['new_primary_interview_sample'] for x in proof['records']) == proof['new_primary_interview_samples'] == 1
    assert proof['new_numbered_questions'] == 0
    for record in proof['records']:
        if record.get('mode') != 'public_main_content':
            continue
        d = public_post(record['source_id'])
        assert d['uuid'] == record['uuid'] and d['title'] == record['title']
        assert d['userBrief']['nickname'] == record['author']
        assert d[record['publication_timestamp_field']] == record['publication_timestamp_ms']
        assert datetime.fromtimestamp(record['publication_timestamp_ms'] / 1000, timezone.utc) == datetime.fromisoformat(record['published_at'])
        derived = (BeautifulSoup(d['content'], 'html.parser').get_text('\n', strip=True) + '\n').encode()
        assert derived == (ROOT / record['text_file']).read_bytes()
        assert len(derived) == record['text_bytes'] and hashlib.sha256(derived).hexdigest() == record['text_sha256']
    assert '剩余60%内容' in (BASE / 'deepseek-lead.html').read_text()
    soup = BeautifulSoup((BASE / 'anthropic-swe-index.html').read_bytes(), 'html.parser')
    text = soup.find('main').get_text('\n', strip=True)
    card = text.split('Staff Software Engineer, Infrastructure', 1)[1].split('Unlock all interview experiences', 1)[0]
    assert 'September 2025' in card and 'Submitted Apr 13, 2026' in card
    current = BeautifulSoup((BASE / 'anthropic-staff.html').read_bytes(), 'html.parser')
    assert 'Share your experience to unlock' in current.find('main').get_text(' ', strip=True)
    questions = (ROOT / 'research/2026-infra-survey/interview-directions.md').read_text()
    assert len(re.findall(r'^\| I\d+ ', questions, re.M)) == 21
    docs = [BASE / 'README.md', ROOT / 'case-studies/resource-sharing-and-placement.md',
            ROOT / 'outlines/extensions/11-资源调度与运行环境.md',
            ROOT / 'research/2026-infra-survey/interview-directions.md']
    links = 0
    for path in docs:
        for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
            target = urlsplit(target)
            if target.scheme or not target.path:
                continue
            dest = (path.parent / unquote(target.path)).resolve()
            # This report is written after these checks.
            assert dest.exists() or dest == ROOT / 'research/2026-infra-survey/interview-ninth-audit.json', dest
            links += 1
    report = dict(verified_at=datetime.now(timezone.utc).isoformat(), status='passed',
                  source_responses=6, web_extracts=2, reused_inputs=3,
                  new_primary_interview_samples=1, new_numbered_questions=0,
                  curated_questions=21, documents_checked=4, local_links_checked=links,
                  arithmetic=calculate(),
                  scope='Declared public readings, date/extraction checks and independent arithmetic; no company authentication or model/framework execution.')
    (ROOT / 'research/2026-infra-survey/interview-ninth-audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    return report


if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False, indent=2))
