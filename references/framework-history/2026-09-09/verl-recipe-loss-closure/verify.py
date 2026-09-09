#!/usr/bin/env python3
"""Static evidence/hash checks and scalar arithmetic only; never imports archived code."""
from pathlib import Path
from fractions import Fraction
import ast
import datetime
import hashlib
import json

BASE = Path(__file__).resolve().parent
ROOT = next(p for p in BASE.parents if (p / 'experiments/ch10/10-08').is_dir())
COMMIT = 'd040717b21af2e23e8e789a3e354cff2394ae2de'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read_json(path):
    return json.loads(path.read_text())

def function(path, name):
    tree = ast.parse(path.read_text())
    matches = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name]
    assert len(matches) == 1, (path, name, len(matches))
    return matches[0]

def calls(node):
    result = []
    for n in ast.walk(node):
        if isinstance(n, ast.Call):
            result.append((n.lineno, ast.unparse(n.func)))
    return sorted(result)

sources = read_json(BASE / 'sources.json')
assert len(sources) == 9
for s in sources:
    p = BASE / s['file']
    assert s['http_status'] == 200 and s['commit'] == COMMIT
    assert s['url'] == f"https://raw.githubusercontent.com/verl-project/verl/{COMMIT}/{s['path']}"
    assert sha(p) == s['sha256'] and p.stat().st_size == s['bytes']
reused = read_json(BASE / 'reused-sources.json')
for s in reused:
    assert sha(ROOT / s['file']) == s['sha256'], s['file']

patch_root = ROOT / 'experiments/ch10/10-08/patch'
original_matches = []
for s in read_json(patch_root / 'sources.json'):
    p = patch_root / s['path'].replace('/', '__')
    assert sha(p) == s['original_sha256']
    assert sha(p) != s['patched_sha256']
    original_matches.append(s['path'])

raw = BASE / 'raw'
base_node = function(raw / 'verl__workers__engine__base.py', 'train_batch')
base_calls = calls(base_node)
ordered = [name for _, name in base_calls if name in ['self.optimizer_zero_grad', 'self.forward_backward_batch', 'self.optimizer_step']]
assert ordered == ['self.optimizer_zero_grad', 'self.forward_backward_batch', 'self.optimizer_step']
fb = function(patch_root / 'verl__workers__engine__fsdp__transformer_impl.py', 'forward_backward_batch')
fb_calls = calls(fb)
lookup = dict((name, line) for line, name in fb_calls)
assert lookup['torch.distributed.all_reduce'] < lookup['prepare_micro_batches'] < lookup['self.forward_step'] < lookup['loss.backward']
assert not any(name.endswith('optimizer.step') for _, name in fb_calls)
agg = function(raw / 'verl__trainer__ppo__core_algos.py', 'agg_loss')
first_branch = agg.body[1]  # docstring followed by if
assert isinstance(first_branch, ast.If)
assert ast.unparse(first_branch.test) == "loss_agg_mode == 'token-mean'"
assert ast.unparse(first_branch.body[-1].value) == 'verl_F.masked_sum(loss_mat, loss_mask) / batch_num_tokens * dp_size'
ppo_text = ast.unparse(function(raw / 'verl__workers__utils__losses.py', 'ppo_loss'))
assert "config.global_batch_info['batch_num_tokens'] = data['batch_num_tokens']" in ppo_text
assert "config.global_batch_info['dp_size'] = data['dp_size']" in ppo_text
assert "policy_loss_fn = get_policy_loss_fn(loss_mode)" in ppo_text
vanilla_text = ast.unparse(function(raw / 'verl__trainer__ppo__core_algos.py', 'compute_policy_loss_vanilla'))
assert '**config.global_batch_info' in vanilla_text
assert 'agg_loss(loss_mat=pg_losses, loss_mask=response_mask' in vanilla_text

observed = []
for run in ['main', 'control']:
    run_dir = ROOT / 'experiments/ch10/10-08' / run
    overrides = read_json(run_dir / 'overrides.json')
    expected = ['data.train_batch_size=4', 'actor_rollout_ref.actor.ppo_mini_batch_size=4',
                'actor_rollout_ref.rollout.n=2', 'actor_rollout_ref.actor.ppo_epochs=1',
                'actor_rollout_ref.actor.ppo_micro_batch_size_per_gpu=1',
                'trainer.n_gpus_per_node=1', 'trainer.nnodes=1']
    assert all(v in overrides for v in expected)
    text = (run_dir / 'stdout.log').read_text()
    actor_text = '\n'.join(text.splitlines()[20:190])
    for phrase in ["'loss_agg_mode': 'token-mean'", "'loss_mode': 'vanilla'", "'use_dynamic_bsz': False", "'use_no_sync_for_gradient_accumulation': False", "'clip_grad': 1.0"]:
        assert phrase in actor_text, (run, phrase)
    assert 'since the world size is 1' in text and 'NO_SHARD' in text
    export = read_json(run_dir / 'tensor-export.json')
    for step in [1, 2]:
        batch = export['tensor_files'][f'advantage-batch-{step}.pt']
        masks = batch['response_mask']['values']
        lengths = [sum(m) for m in masks]
        assert lengths == [2, 3, 2, 3, 3, 2, 3, 2]
        assert sum(lengths) == 20
        response_ids = [[v for v, mask in zip(row, m) if mask] for row, m in zip(batch['responses']['values'], masks)]
        assert all(row[-1] == 151645 for row in response_ids)
        input_count = sum(sum(m) for m in batch['attention_mask']['values'])
        assert input_count == 366
        observed.append(dict(run=run, step=step, answers=len(lengths), response_lengths=lengths,
                             loss_denominator=20, input_tokens_for_compute=366,
                             response_token_ids=response_ids,
                             sequence_mean_weights=[str(Fraction(v,20)) for v in lengths],
                             expected_mini_batches=8//(4*2)*1, expected_micro_batches_per_mini=8//1))

# Teaching scalar loss: use observed lengths, hypothetical per-token coefficients only.
lengths = observed[0]['response_lengths']
coeff = [Fraction(1,5) if n == 2 else Fraction(2,5) for n in lengths]
partial = [n*c/Fraction(20) for n,c in zip(lengths,coeff)]
correct = sum(partial)
wrong_equal_sequence = sum(coeff)/8
wrong_double_average = correct/8
assert correct == Fraction(8,25) and wrong_equal_sequence == Fraction(3,10)
assert wrong_double_average == Fraction(1,25)
# Regrouping into size-2 or size-4 microbatches keeps the denominator at 20.
regrouped = {str(size): str(sum(sum(Fraction(n)*c for n,c in zip(lengths[i:i+size],coeff[i:i+size]))/20
                 for i in range(0,8,size))) for size in [1,2,4,8]}
assert set(regrouped.values()) == {'8/25'}
result = dict(status='PASS', checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              scope='source hash/AST/JSON and exact rational arithmetic only; no framework or GPU execution',
              source_commit=COMMIT, new_raw_source_files=len(sources), reused_input_files=len(reused),
              original_patch_matches=original_matches, base_call_order=base_calls,
              forward_backward_call_order=fb_calls, observed=observed,
              scalar=dict(hypothetical_token_coefficients=[str(c) for c in coeff],
                          micro_partial_gradients=[str(x) for x in partial], correct_gradient=str(correct),
                          incorrect_equal_sequence_gradient=str(wrong_equal_sequence),
                          incorrect_extra_divide_by_micro_count=str(wrong_double_average),
                          regrouping_same_denominator=regrouped),
              limitations=['No microbatch-size A/B framework rerun', 'No per-micro forward loss tensors were recorded',
                           'No CP/DP>1 proof', 'no_sync flag false in this recipe',
                           'AST markers are evidence consistency checks, not a formal program proof'])
(BASE/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k: result[k] for k in ['status','new_raw_source_files','reused_input_files','scope']},ensure_ascii=False))
