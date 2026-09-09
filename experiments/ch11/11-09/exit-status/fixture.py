import argparse

import asyncio

import ast

from dataclasses import asdict

import hashlib

import json

import os

from pathlib import Path

import resource

import subprocess

import sys

import time

import threading

INITIAL='''def merge_intervals(intervals):
    intervals.sort()
    result = []
    for start, end in intervals:
        if result and start < result[-1][1]:
            result[-1][1] = end
        else:
            result.append([start, end])
    return result
'''

SPEC='''Implement merge_intervals(intervals). Input: list of [start,end] integer pairs, start <= end.
Return new sorted pairs merging overlaps AND touching endpoints. Nested intervals must not shorten a merged end.
Do not mutate the input, including its nested lists. Empty input returns [].
'''

CHECKER='''import copy, json, runpy
f = runpy.run_path('intervals.py')['merge_intervals']
cases = [([], []), ([[3,5],[1,2]], [[1,2],[3,5]]),
         ([[1,10],[2,3]], [[1,10]]), ([[1,2],[2,4]], [[1,4]]),
         ([[5,7],[1,3],[2,6]], [[1,7]]), ([[-4,-1],[-2,0],[3,3]], [[-4,0],[3,3]])]
results=[]
for original, expected in cases:
    data=copy.deepcopy(original)
    try:
        actual=f(data)
        results.append(dict(input=original, expected=expected,actual=actual,
                            unchanged=data==original,passed=actual==expected and data==original))
    except Exception as e: results.append(dict(input=original,passed=False,error=repr(e)))
print(json.dumps(dict(passed=all(r['passed'] for r in results),cases=results)))
'''

def validate_code(code):
    tree=ast.parse(code)
    forbidden=(ast.Import,ast.ImportFrom,ast.Global,ast.Nonlocal,ast.ClassDef,ast.With,ast.AsyncWith)
    calls={'sorted','len','min','max','range','list','tuple','enumerate','zip','merge_intervals'}
    attrs={'append','extend','sort','copy'}
    for node in ast.walk(tree):
        if isinstance(node,forbidden):raise ValueError('Only a self-contained function is allowed')
        if isinstance(node,ast.Name) and node.id.startswith('__'):raise ValueError('Dunder names prohibited')
        if isinstance(node,ast.Attribute) and node.attr not in attrs:raise ValueError('Unsupported attribute')
        if isinstance(node,ast.Call) and not ((isinstance(node.func,ast.Name) and node.func.id in calls) or
                    (isinstance(node.func,ast.Attribute) and node.func.attr in attrs)):
            raise ValueError('Unsupported call')

def limits():
    resource.setrlimit(resource.RLIMIT_CPU,(2,2))
    resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))

def execute(action,work):
    tool=action.get('tool')
    if tool=='read_file':
        name=action.get('path')
        if name not in ['intervals.py','test_intervals.py','SPEC.txt']:raise ValueError('Unknown fixture file')
        return {'content':(work/name).read_text()}
    if tool=='write_file':
        if action.get('path')!='intervals.py':raise ValueError('Only intervals.py is editable')
        code=action['content'];validate_code(code);(work/'intervals.py').write_text(code)
        return {'written_bytes':len(code.encode()),'sha256':hashlib.sha256(code.encode()).hexdigest()}
    if tool=='run_tests':
        result=subprocess.run([sys.executable,'-B','test_intervals.py'],cwd=work,capture_output=True,
                              text=True,timeout=4,preexec_fn=limits)
        return {'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr}
    if tool=='finish':return {'answer':action.get('answer','')}
    raise ValueError('Unknown tool')
