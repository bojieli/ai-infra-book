import copy, json, runpy
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
