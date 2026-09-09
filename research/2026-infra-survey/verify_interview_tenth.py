"""Verify archived public posts and attribution boundaries from parallel reading."""
from pathlib import Path
import contextlib
import io
import json
import re
import runpy

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'references/interviews/2026-09-09/tenth-pass'


def verify():
    # Locally authored evidence checker, inspected before use; no downloaded code execution.
    with contextlib.redirect_stdout(io.StringIO()):
        result=runpy.run_path(str(BASE/'verify.py'))['result']
    questions=(ROOT/'research/2026-infra-survey/interview-directions.md').read_text()
    assert len(re.findall(r'^\| I\d+ ',questions,re.M))==21
    proof=json.loads((BASE/'reading-proof.json').read_text())
    assert proof['posts'][-1]['kind']=='commercial_column_lead'
    assert not proof['posts'][-1]['adopted_direction']
    result['curated_questions']=21
    result['scope']='Declared public post text/date/identity only; self-reports not independently authenticated, commercial column not a new RL interview sample.'
    (ROOT/'research/2026-infra-survey/interview-tenth-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result


if __name__=='__main__':
    print(json.dumps(verify(),ensure_ascii=False))
