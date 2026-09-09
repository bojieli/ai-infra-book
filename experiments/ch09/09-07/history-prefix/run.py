"""Actual tokenizer experiment: frozen history serialization, no model execution."""
import argparse, copy, hashlib, json, platform
from pathlib import Path
import transformers
from transformers import AutoTokenizer

ROOT = Path(__file__).absolute().parent

def prefix(a, b):
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return i
    return min(len(a), len(b))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--tokenizer', default=str(ROOT/'tokenizer'))
    ap.add_argument('--out', type=Path, default=ROOT/'results'); args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    tok = AutoTokenizer.from_pretrained(args.tokenizer, local_files_only=True)
    rows = [json.loads(x) for x in (ROOT/'original-rounds.jsonl').read_text().splitlines()]
    # Restricted serializer for this trace's string system/user/assistant messages.
    # Preserve the exact empty thinking prefix that was part of each old prompt.
    blank = '<think>\n\n</think>\n\n'
    modes = {x: [] for x in ['default', 'empty_reasoning_field', 'preserved_text', 'append_tokens']}
    checks = 0
    for i, row in enumerate(rows):
        messages = row['messages']
        assert all(m['role'] in ('system','user','assistant') and isinstance(m['content'],str) for m in messages)
        ids = tok.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, enable_thinking=False, return_dict=False)
        assert ids == row['prompt_token_ids']; checks += 1
        modes['default'].append(ids)
        patched = copy.deepcopy(messages)
        for m in patched:
            if m['role'] == 'assistant': m['reasoning_content'] = ''
        ids2 = tok.apply_chat_template(patched, tokenize=True, add_generation_prompt=True, enable_thinking=False, return_dict=False)
        modes['empty_reasoning_field'].append(ids2)
        text = ''.join('<|im_start|>'+m['role']+'\n'+(blank if m['role']=='assistant' else '')+m['content']+'<|im_end|>\n' for m in messages)
        text += '<|im_start|>assistant\n'+blank
        preserved = tok.encode(text, add_special_tokens=False)
        modes['preserved_text'].append(preserved)
        if i == 0:
            appended = ids
        else:
            old = rows[i-1]
            assert messages[:len(old['messages'])] == old['messages']
            added = messages[len(old['messages']):]
            assert len(added) == 2 and added[0]['role']=='assistant' and added[1]['role']=='user'
            assert added[0]['content'] == old['output_text']
            assert old['output_token_ids'][-1] == tok.eos_token_id
            assert tok.decode(old['output_token_ids'][:-1]) == old['output_text']
            suffix = '\n<|im_start|>user\n'+added[1]['content']+'<|im_end|>\n<|im_start|>assistant\n'+blank
            appended = modes['append_tokens'][-1]+old['output_token_ids']+tok.encode(suffix,add_special_tokens=False)
            checks += 5
        modes['append_tokens'].append(appended)
        assert tok.decode(appended) == text; checks += 1
    transitions = []
    for mode, prompts in modes.items():
        for i in range(11):
            consumed = prompts[i]+rows[i]['output_token_ids'][:-1]
            n = prefix(consumed, prompts[i+1])
            transitions.append(dict(mode=mode,turn=i,prompt_tokens=len(prompts[i]),generated_consumed_tokens=len(rows[i]['output_token_ids'])-1,common_prefix=n,entire_consumed_prefix_preserved=n==len(consumed),common_generated_tokens=max(0,n-len(prompts[i])),next_prompt_tokens=len(prompts[i+1]),block256_prefix=n//256*256))
    summary = {mode: dict(transitions=11,full_prefix_preserved=sum(x['entire_consumed_prefix_preserved'] for x in transitions if x['mode']==mode),prompt_tokens=sum(map(len,prompts))) for mode,prompts in modes.items()}
    # No speed, KV transfer or new answer quality follows from serialization alone.
    output = dict(source_sha256=hashlib.sha256((ROOT/'original-rounds.jsonl').read_bytes()).hexdigest(),checks=checks,summary=summary,transitions=transitions,prompts=modes,scope='CPU tokenizer only; source outputs are frozen failed-Agent history; no inference or cache transfer')
    (args.out/'analysis.json').write_text(json.dumps(output,indent=2)+'\n')
    (args.out/'environment.json').write_text(json.dumps(dict(python=platform.python_version(),transformers=transformers.__version__,tokenizer_class=type(tok).__name__),indent=2)+'\n')
    print(json.dumps(summary))
if __name__ == '__main__': main()
