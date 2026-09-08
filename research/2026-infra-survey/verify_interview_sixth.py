#!/usr/bin/env python3
"""Verify archived identities and the synthetic routing ledger, without network access."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
from fractions import Fraction as F
import hashlib
import json
import math
import re
from urllib.parse import unquote, urlsplit
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / 'references/interviews/2026-09-08/sixth-pass'


def verify():
    def check_file(rec):
        b = (ROOT / rec['file']).read_bytes()
        assert len(b) == rec['bytes'] and hashlib.sha256(b).hexdigest() == rec['sha256'], rec['file']

    sources = json.loads((D / 'sources.json').read_text())
    assert len({r['id'] for r in sources}) == len(sources) == 8
    for r in sources:
        check_file(r)
    assert sum(r['status_code'] == 403 for r in sources) == 1
    assert sum(r.get('retrieval_kind') == 'web_tool_text_extract' for r in sources) == 2
    proof = json.loads((D / 'reading-proof.json').read_text())
    step = proof['stepfun']
    check_file(step['parent']); check_file(step['image'])
    post = json.loads((ROOT / step['parent']['file']).read_text())
    assert post['uuid'] == step['uuid']
    assert post['imgMoment'][0]['src'] == sources[0]['url']
    assert [post['imgMoment'][0][k] for k in ['width', 'height']] == step['image_size']
    assert step['viewed'] and step['role'] is None and step['interview_date'] is None
    for r in proof['nowcoder']:
        check_file(r['main'])
        soup = BeautifulSoup((D / (r['stem'] + '.html')).read_text(), 'html.parser')
        script = next(s.get_text() for s in soup.find_all('script') if 'window.__INITIAL_STATE__=' in s.get_text())
        initial, _ = json.JSONDecoder().raw_decode(script.split('window.__INITIAL_STATE__=', 1)[1])
        main = initial['prefetchData']['2']['ssrCommonData']['contentData']
        assert main == json.loads((ROOT / r['main']['file']).read_text())
        assert main['uuid'] == r['uuid'] and main['userBrief']['nickname'] == r['author']
        assert datetime.fromtimestamp(main['createTime']/1000, timezone(timedelta(hours=8))).isoformat() == r['published_at']
    for r in proof['web_reports']:
        check_file(r['source'])
        t = (ROOT / r['source']['file']).read_text()
        assert 'Curated and edited by PracHub' in t
        assert r['original_candidate_identity'] is None
    check_file(proof['roundup']['selected'])
    assert len(proof['roundup']['headings']) == 5
    check_file(proof['minimax']['article'])
    for r in proof['billing_reused_sources']:
        check_file(r['source']); check_file(r['selected'])

    # Independently accumulate full task ledgers, including unsuccessful calls.
    a = json.loads((ROOT / 'research/2026-infra-survey/routing-cost-arithmetic.json').read_text())
    assert a['tasks_per_candidate'] == 1000 and a['a_quality_successes'] == 800
    a_total = F(1000 * (1000 * 1 + 19000 * F(1, 10) + 2000 * 4), 10**6)
    b_hit_total = F(1000 * (1000 * 2 + 19000 * F(1, 5) + 300 * 8), 10**6)
    b_miss_total = F(1000 * (20000 * 2 + 300 * 8), 10**6)
    assert a_total == F(109, 10) and b_hit_total == F(82, 10) and b_miss_total == F(424, 10)
    assert a['a_total_cost'] == float(a_total)
    assert a['a_cost_per_quality_success'] == float(a_total / 800)
    for s in a['b_scenarios']:
        h = s['hit_fraction']
        ledger = h * float(b_hit_total) + (1-h) * float(b_miss_total)
        assert math.isclose(ledger, s['total_cost'])
        assert s['quality_successes'] == 980
        assert math.isclose(ledger / 980, s['cost_per_quality_success'])
    h = F(a['cost_break_even_exact'])
    assert h == F(1291, 1520)
    assert (h*b_hit_total + (1-h)*b_miss_total) / 980 == a_total / 800
    assert math.isclose(a['latency_followup']['b_min_hit_fraction'], 900/980)
    assert 900/980 > float(h)

    questions = (ROOT / 'research/2026-infra-survey/interview-directions.md').read_text()
    assert re.findall(r'^\| (I\d+) ', questions, re.M) == [f'I{i:02}' for i in range(1, 22)]
    assert '\n\n| I21' not in questions
    catalog = json.loads((ROOT / 'outlines/chapters.json').read_text())
    assert [x['title'] for x in catalog[7:12]] == ['单实例推理','分布式推理','训练系统','资源调度与运行环境','端边云协同']
    chapter = ROOT / 'outlines' / catalog[10]['file']
    c = chapter.read_text()
    assert '### 11.4.5 ' in c and '84.93%' in c
    assert len(re.findall(r'^> \*\*实验 .*〔核心〕', c, re.M)) == 3
    files = [D/'README.md', ROOT/'case-studies/routing-cost-and-completion.md', ROOT/'research/2026-infra-survey/interview-directions.md']
    links = 0
    for p in files:
        for target in re.findall(r'\]\(([^)]+)\)', p.read_text()):
            u = urlsplit(target)
            if u.scheme or not u.path:
                continue
            assert (p.parent / unquote(u.path)).resolve().is_file(), (p, target)
            links += 1
    return dict(status='passed', verified_at=datetime.now(timezone.utc).isoformat(),
                source_records=8, direct_new_candidate_posts=1, completed_existing_image=1,
                commercial_reports=2, questions=21, current_location='11.4.3–11.4.5 / experiment 11-8 / figure 11-7',
                routing_ledger='passed', local_links_checked=links,
                scope='This phase only; no full conference archive recheck or model/API experiment.', errors=[])


if __name__ == '__main__':
    result = verify()
    (Path(__file__).parent / 'qa/interview-sixth-verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
