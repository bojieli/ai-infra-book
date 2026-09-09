"""Independent closed forms verify implementation; all output stays in this folder."""
import json,sys,hashlib
from pathlib import Path
from fractions import Fraction
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
sys.path.insert(0,str(ROOT/'src'))
from infra_calc.topics.ub_scope import calculate
from infra_calc.sources import model_config
from renderer import ub_scope_markdown
base=calculate();threshold=Fraction(base['scope_crossover']['remote_bandwidth_threshold_bytes_per_second_exact'])
a,b=base['scope_candidates'];lo=b['summary']['maximum_card_resident_bytes'];hi=a['summary']['maximum_card_resident_bytes']
rows=[dict(id='ub-scope-qwen32-default'),
      dict(id='ub-scope-remote-below',remote_bytes_per_second=str(threshold/2)),
      dict(id='ub-scope-remote-tie',remote_bytes_per_second=str(threshold)),
      dict(id='ub-scope-remote-above',remote_bytes_per_second=str(threshold*2)),
      dict(id='ub-scope-capacity-none',capacity_bytes=lo-1),
      dict(id='ub-scope-capacity-dual-only',capacity_bytes=lo),
      dict(id='ub-scope-capacity-both',capacity_bytes=hi),
      dict(id='ub-scope-startup-blocked',remote_startup_ns=10000000),
      dict(id='ub-scope-b2-seven',batch=2,decode_steps=7),
      dict(id='ub-scope-one-forward',history=0,decode_steps=1)]
(OUT/'scenarios.json').write_text(json.dumps({'ub_scope':rows},indent=2)+'\n')
summary=[]
for row in rows:
    inp={k:v for k,v in row.items() if k!='id'};r=calculate(**inp);assert calculate(**r['scenario'])==r
    s=r['scenario'];c=model_config(s['model']);H,V,L,Q,KV,D,F=(c[k] for k in ('hidden_size','vocab_size','num_hidden_layers','num_attention_heads','num_key_value_heads','head_dim','intermediate_size'))
    B=s['batch'];N=s['history']+s['decode_steps'];M=2*B*H;Z=4*B*V;token=4*B
    for candidate,TP,PP in zip(r['scope_candidates'],(8,4),(1,2)):
        # Closed-form source path: embedding AR + two AR per layer + logits AG + token tree.
        rounds=TP.bit_length()-1
        local=(2*L+1)*(2*(TP-1)*Fraction(s['local_startup_ns'],10**9)+Fraction(2*(TP-1)*M,TP)/Fraction(s['local_bytes_per_second']))
        local+=(TP-1+rounds)*Fraction(s['local_startup_ns'],10**9)
        local+=(Fraction((TP-1)*Z,TP)+rounds*token)/Fraction(s['local_bytes_per_second'])
        remote=Fraction(0) if PP==1 else 2*Fraction(s['remote_startup_ns'],10**9)+Fraction(TP*M+token)/Fraction(s['remote_bytes_per_second'])
        z=candidate['summary'];assert Fraction(z['serial_communication_seconds_per_forward_exact'])==local+remote
        assert Fraction(z['serial_communication_seconds_all_forwards_exact'])==(local+remote)*s['decode_steps']
        assert len(candidate['handoff_operations'])==2*L+3+(2 if PP==2 else 0)
        for card in candidate['placement_cards']:
            n=L//PP;stage=card['stage'];parameters=n*(H*(2*(Q//TP)*D+2*(KV//TP)*D)+3*H*(F//TP)+2*D+2*H)
            if stage==0:parameters+=(V//TP)*H
            if stage==PP-1:parameters+=(V//TP)*H+H
            kv=2*n*(KV//TP)*D*N*B*2
            assert card['weight_bytes']==2*parameters and card['kv_bytes']==kv
            assert card['resident_bytes']==2*parameters+kv+s['workspace_bytes']
    (OUT/(row['id']+'.json')).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    md=ub_scope_markdown(r);assert '容量先于选择' in md and '历史材料仅证明时间线' in md
    (OUT/(row['id']+'.md')).write_text(md)
    summary.append(dict(id=row['id'],both_fit=r['scope_crossover']['both_capacity_feasible'],preference=r['scope_crossover']['communication_only_preference'],candidates=[dict(name=x['name'],**x['summary']) for x in r['scope_candidates']]))
assert [x['preference'] for x in summary[1:4]]==['single_server_tp8','tie','two_servers_tp4_pp2']
assert [x['all_cards_fit'] for x in summary[4]['candidates']]==[False,False]
assert [x['all_cards_fit'] for x in summary[5]['candidates']]==[False,True]
assert [x['all_cards_fit'] for x in summary[6]['candidates']]==[True,True]
(OUT/'validation.json').write_text(json.dumps(dict(scenarios_verified=len(rows),independent_checks=['exact closed-form collective/startup/path service time','per-card weight inventory formula','GQA KV formula at last forward','one-byte capacity boundary','exact rational bandwidth crossover','scenario replay','standalone markdown'],capacity_dual_threshold_bytes=lo,capacity_both_threshold_bytes=hi,remote_bandwidth_threshold_exact=str(threshold),remote_bandwidth_threshold_decimal=float(threshold),results=summary),indent=2)+'\n')
print('verified',len(rows),'scenarios','capacity thresholds',lo,hi,'bandwidth threshold',float(threshold))
