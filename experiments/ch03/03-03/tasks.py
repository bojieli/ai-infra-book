import itertools
TASKS=[dict(id='six',values=[2,3,5,7,8,11],target=15),dict(id='eight',values=[1,2,3,4,6,8,10,13],target=18),dict(id='twelve',values=[1,2,3,4,5,6,7,8,9,10,11,12],target=30),dict(id='fourteen',values=[1,2,3,4,5,6,7,8,9,10,11,12,13,14],target=40)]
def answer(t):
 return sum(sum(v for v,b in zip(t['values'],mask) if b)==t['target'] for mask in itertools.product([0,1],repeat=len(t['values'])))
def dp(t):
 counts=[1]+[0]*t['target']
 for v in t['values']:
  for n in range(t['target'],v-1,-1):counts[n]+=counts[n-v]
 return counts[-1]
def prompt(t):
 return 'How many subsets of '+str(t['values'])+' have sum exactly '+str(t['target'])+'? Each listed element can be selected at most once. Count subsets, not permutations. Give the final answer as exactly one JSON object with an integer count field.'
if __name__=='__main__':
 for t in TASKS:
  assert answer(t)==dp(t)
  print(t['id'],answer(t))
