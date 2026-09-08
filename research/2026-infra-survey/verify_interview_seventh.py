#!/usr/bin/env python3
"""Verify primary post attribution, timestamps and explicitly limited adoption."""
from datetime import datetime, timezone, timedelta
from pathlib import Path
import hashlib
import json
import re
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / 'references/interviews/2026-09-09/seventh-pass'


def verify():
    sources = {r['id']: r for r in json.loads((DEST / 'sources.json').read_text())}
    proof = json.loads((DEST / 'reading-proof.json').read_text())
    authors = set()
    for r in proof['posts']:
        source = sources[r['source_id']]
        for item in [source, r['main']]:
            data = (ROOT / item['file']).read_bytes()
            assert len(data) == item['bytes'] and hashlib.sha256(data).hexdigest() == item['sha256']
        soup = BeautifulSoup((ROOT / source['file']).read_text(), 'html.parser')
        script = next(s.get_text() for s in soup.find_all('script') if 'window.__INITIAL_STATE__=' in s.get_text())
        initial, _ = json.JSONDecoder().raw_decode(script.split('window.__INITIAL_STATE__=', 1)[1])
        main = initial['prefetchData']['2']['ssrCommonData']['contentData']
        assert main == json.loads((ROOT / r['main']['file']).read_text())
        assert main['uuid'] == r['uuid'] and main['userBrief']['nickname'] == r['author']
        authors.add(r['author'])
        for field, key in [('createdAt', 'published_at'), ('editTime', 'edited_at')]:
            assert datetime.fromtimestamp(main[field] / 1000, timezone(timedelta(hours=8))).isoformat() == r[key]
        assert r['interview_date'] is None
        if not r['adopted_direction']:
            assert main['content'] == '面壁智能rl infra二面' and not main['imgMoment'] and not main['title']
    assert len(authors) == proof['distinct_authors'] == 1
    assert sum(p['adopted_direction'] for p in proof['posts']) == 2
    assert proof['new_numbered_questions'] == 0
    questions = (ROOT / 'research/2026-infra-survey/interview-directions.md').read_text()
    assert re.findall(r'^\| (I\d+) ', questions, re.M) == [f'I{i:02}' for i in range(1, 22)]
    return dict(status='passed', verified_at=datetime.now(timezone.utc).isoformat(),
                source_responses=3, posts_with_question_directions=2,
                distinct_authors=1, title_only_posts=1,
                new_numbered_questions=0, questions=21, errors=[])


if __name__ == '__main__':
    result = verify()
    (Path(__file__).parent / 'interview-seventh-audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
