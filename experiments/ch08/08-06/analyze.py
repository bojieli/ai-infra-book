"""Public condition checks and raw Agent boundary ledger; no speedup calculations."""
import hashlib,json,sys
from html.parser import HTMLParser
from pathlib import Path
B=Path(__file__).absolute().parent;O=Path(sys.argv[1]) if len(sys.argv)>1 else B/'results';O.mkdir(parents=True,exist_ok=True)
def read(p):return json.loads(p.read_text())
for r in read(B/'origins.json'):
    data=(B/r['saved']).read_bytes();assert len(data)==r['bytes'] and hashlib.sha256(data).hexdigest()==r['sha256']
meta=read(B/'sources/public-source.json');assert hashlib.sha256((B/'sources/mimo-tilert.html').read_bytes()).hexdigest()==meta['sha256']
text=(B/'sources/mimo-tilert.txt').read_text()
class SourceText(HTMLParser):
    def __init__(self):super().__init__();self.parts=[]
    def handle_data(self,data):self.parts.append(data)
parser=SourceText();parser.feed((B/'sources/mimo-tilert.html').read_text());html_text=' '.join(' '.join(parser.parts).split())
for phrase in ['standard 8-card general-purpose GPU node','only on the MoE Experts','MXFP4','mask block size to 8','1000 tokens/s']:
    assert phrase in text and phrase in html_text
trials=[]
for p in sorted((B/'records').iterdir()):
    rows=[json.loads(l) for l in (p/'rounds.jsonl').read_text().splitlines()]
    final=read(p/'final.json');holdout=json.loads(read(p/'independent-checks.json')['result']['stdout'])
    validation=json.loads(final['validation']['stdout'])
    ledger=[];end=None
    for r in rows:
        start=r['client_start_unix'];stop=r['client_end_unix'];assert start<=stop
        assert end is None or start>=end;end=stop
        assert r['request']['stream'] is False and r['http_status']==200
        assert r['prompt_token_ids'] is None and r['output_token_ids'] is None
        audit=r['tool_audit'];tool=None
        if 'start_unix' in audit:
            assert stop<=audit['start_unix']<=audit['end_unix']
            tool=dict(start_unix=audit['start_unix'],end_unix=audit['end_unix'],wall_s=audit['end_unix']-audit['start_unix'])
            end=audit['end_unix']
        ledger.append(dict(turn=r['turn'],http_start_unix=start,http_end_unix=stop,http_wall_s=stop-start,
                           usage=r['usage'],action=r['action'],audited_tool=tool,
                           prefill_s=None,decode_s=None,server_queue_s=None,first_token_time=None))
    assert end<=final['audit']['start_unix']<=final['audit']['end_unix']
    qualified=final['agent_finished'] and validation['passed']
    trials.append(dict(id=p.name,rounds=len(rows),agent_finished=final['agent_finished'],qualified_original_task=qualified,
                       original_cases_passed=sum(c['passed'] for c in validation['cases']),original_cases=len(validation['cases']),
                       holdout_passed=holdout['passed'],holdout_cases=holdout['cases'],
                       http_wall_sum_s=sum(r['http_wall_s'] for r in ledger),
                       audited_tool_count=sum(r['audited_tool'] is not None for r in ledger),
                       audited_tool_wall_sum_s=sum(r['audited_tool']['wall_s'] for r in ledger if r['audited_tool']),
                       observed_first_request_to_final_validation_s=final['audit']['end_unix']-ledger[0]['http_start_unix'],
                       ledger=ledger,all_tool_time_s=None,decode_only_speedup=None,prefill_only_speedup=None,
                       mimo_matched_quality=None))
j=dict(public_conditions=read(B/'public-conditions.json'),trials=trials,
       total_http_requests=sum(t['rounds'] for t in trials),qualified_trials=sum(t['qualified_original_task'] for t in trials),
       limitations=['Qwen Agent record is not a MiMo paired trial.',
                    'Non-streaming HTTP does not identify first token, prefill, decode or server queue.',
                    'Tool audit covers recorded timed subprocesses, not every read/write/controller operation.',
                    'Observed interval omits earlier preparation and later holdout; not a whole deployment lifecycle.',
                    'No speedup/cost extrapolation; C44 calculations owned separately.'])
(O/'analysis.json').write_text(json.dumps(j,indent=2)+'\n');print(json.dumps(dict(requests=j['total_http_requests'],qualified=j['qualified_trials'],trials=[{k:v for k,v in t.items() if k not in ['ledger']} for t in trials])))
