"""Independent post-run checks, never included in the agent's tool workspace."""
import copy
import itertools
import json
from pathlib import Path
import random
import subprocess
import sys
from fixture import validate_code,limits


def oracle(intervals):
    # Connected components of the overlap graph; independent of sorted folding.
    remaining=set(range(len(intervals)));result=[]
    while remaining:
        pending=[remaining.pop()];component=[]
        while pending:
            i=pending.pop();component.append(i)
            linked={j for j in remaining if max(intervals[i][0],intervals[j][0])<=min(intervals[i][1],intervals[j][1])}
            remaining.difference_update(linked);pending.extend(linked)
        result.append([min(intervals[i][0] for i in component),max(intervals[i][1] for i in component)])
    return sorted(result)


def check(path):
    code=path.read_text();validate_code(code)
    namespace={};exec(compile(code,str(path),'exec'),namespace)
    f=namespace['merge_intervals']
    intervals=[[a,b] for a in range(-3,4) for b in range(a,4)]
    cases=[[]]+[[x] for x in intervals]+[list(xs) for xs in itertools.product(intervals,repeat=2)]
    rng=random.Random(304)
    cases += [[rng.choice(intervals) for _ in range(rng.randrange(3,8))] for _ in range(200)]
    failures=[];value_and_input_passed=0;alias_failures=0
    for original in cases:
        arg=copy.deepcopy(original);expected=oracle(original)
        try:
            actual=f(arg)
            passed=actual==expected and arg==original
            value_and_input_passed+=int(passed)
            if actual:
                actual[0][0]-=100
                aliases=arg!=original
                if passed and aliases:alias_failures+=1
                passed=passed and not aliases  # Additional result-isolation check.
            if not passed:failures.append(dict(input=original,expected=expected))
        except Exception as e:failures.append(dict(input=original,error=repr(e)))
    return dict(cases=len(cases),passed=len(cases)-len(failures),failures=failures,
                value_and_input_passed=value_and_input_passed,additional_alias_failures=alias_failures,
                criteria='Value equality and input unchanged immediately after call; separately mutate first output pair to detect aliasing.')


if __name__=='__main__':
    if '--child' in sys.argv:print(json.dumps(check(Path(sys.argv[1]))))
    else:
        root=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).parent/'results'
        result=subprocess.run([sys.executable,__file__,str(root/'workspace/intervals.py'),'--child'],
                              capture_output=True,text=True,timeout=5,preexec_fn=limits)
        assert result.returncode==0,result.stderr
        data=json.loads(result.stdout)
        (root/'independent-checks-v2.json').write_text(json.dumps(data,indent=2)+'\n')
        print(json.dumps({k:v for k,v in data.items() if k!='failures'}))
