"""Audit released structural records; never decode anonymous identifiers."""
import hashlib,json,math,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parent
source=json.loads((ROOT/'conversations-source.json').read_text());path=ROOT/'conversations_hashed.json'
assert hashlib.sha256(path.read_bytes()).hexdigest()==source['sha256']
conversations=json.loads(path.read_text());rows=[];pairs=[]
def p95(xs):return sorted(xs)[math.ceil(.95*len(xs))-1]
for i,conversation in enumerate(conversations):
    assert conversation and [r['turn'] for r in conversation]==list(range(len(conversation)))
    for turn,r in enumerate(conversation):
        assert set(r)=={'turn','timestamp','input_token_count','output_token_count','input_tokens','output_tokens'}
        assert isinstance(r['input_token_count'],int) and r['input_token_count']>=0
        assert isinstance(r['output_token_count'],int) and r['output_token_count']>=0
        assert all(isinstance(x,int) for x in r['input_tokens']+r['output_tokens'])
        rows.append(dict(conversation_index=i,turn=turn,timestamp=r['timestamp'],input_count=r['input_token_count'],output_count=r['output_token_count'],input_identifier_count=len(r['input_tokens']),output_identifier_count=len(r['output_tokens'])))
        if turn:
            previous=conversation[turn-1];delta=r['timestamp']-previous['timestamp'];assert delta>=0
            lcp=0
            for a,b in zip(previous['input_tokens'],r['input_tokens']):
                if a!=b:break
                lcp+=1
            pairs.append(dict(conversation_index=i,from_turn=turn-1,to_turn=turn,start_timestamp_gap_s=delta,shared_input_identifier_prefix=lcp))
result=dict(status='passed',conversations=len(conversations),requests=len(rows),adjacent_pairs=len(pairs),
    turns_min=min(map(len,conversations)),turns_max=max(map(len,conversations)),turns_median=statistics.median(map(len,conversations)),
    input_count_median=statistics.median(r['input_count'] for r in rows),input_count_p95=p95([r['input_count'] for r in rows]),
    output_count_median=statistics.median(r['output_count'] for r in rows),output_count_p95=p95([r['output_count'] for r in rows]),
    start_gap_median_s=statistics.median(p['start_timestamp_gap_s'] for p in pairs),start_gap_p95_s=p95([p['start_timestamp_gap_s'] for p in pairs]),
    input_array_length_mismatches=sum(r['input_count']!=r['input_identifier_count'] for r in rows),
    output_array_length_mismatches=sum(r['output_count']!=r['output_identifier_count'] for r in rows),
    positive_identifier_prefix_pairs=sum(p['shared_input_identifier_prefix']>0 for p in pairs),
    source_sha256=source['sha256'],
    scope='Released subset only, not all production conversations. List index is a local archive identity. Consecutive request timestamp gaps are not tool/think/wait duration: completion timestamps are absent. Identifier prefix is not token count, actual KV hits or reusable KV bytes. No user content reconstructed.')
(ROOT/'results/conversation-audit.json').write_text(json.dumps(result,indent=2)+'\n')
(ROOT/'results/conversation-rows.json').write_text(json.dumps(rows)+'\n');(ROOT/'results/conversation-pairs.json').write_text(json.dumps(pairs)+'\n');print(json.dumps(result,indent=2))
