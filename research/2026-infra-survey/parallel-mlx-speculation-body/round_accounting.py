#!/usr/bin/env python3
"""Independent teaching arithmetic; never imports or runs archived Ollama code."""
from fractions import Fraction
import json

def build():
    rows = []
    for label, accepted, eos in [('reject_first', 0, False), ('reject_third', 2, False), ('accept_all', 4, False), ('accepted_eos_second', 2, True)]:
        before, drafted = 100, 4
        kept_drafts = accepted - int(eos)
        emitted = accepted + int(not eos)
        rows.append(dict(case=label, before=before, drafted=drafted, target_rows=drafted+1,
                         accepted_drafts=accepted, returned_results_including_eos=emitted,
                         extra_sample=int(not eos), kept_draft_states=kept_drafts,
                         committed_positions=1+kept_drafts, after=before+1+kept_drafts,
                         discarded_target_rows=drafted-kept_drafts))
    conditional = [Fraction(4,5), Fraction(7,10), Fraction(3,5), Fraction(1,2)]
    costs_ms = [Fraction(2), Fraction(5,2), Fraction(16,5), Fraction(5), Fraction(7)]
    expected, survive = Fraction(1), Fraction(1)
    choices = []
    for depth, cost in enumerate(costs_ms):
        if depth:
            survive *= conditional[depth-1]
            expected += survive
        choices.append(dict(draft_depth=depth, target_rows=depth+1,
                            expected_nonterminal_output=float(expected),
                            expected_nonterminal_output_exact=str(expected),
                            assumed_complete_round_ms=float(cost),
                            expected_tokens_per_second=float(1000*expected/cost)))
    return dict(status='teaching_arithmetic_only_not_framework_execution',
                assumptions=['One sequence; no EOS or output cap for expected-value table.',
                             'Four fixed conditional probabilities; stationary for this comparison.',
                             'Costs are explicit teaching inputs for complete rounds, not hardware observations.',
                             'Round ledger counts returned Result objects including EOS, not visible/billed text.',
                             'No byte estimate or measured allocation is inferred from logical cache positions.'],
                fixed_round=rows, conditional_probabilities=[float(x) for x in conditional],
                depth_comparison=choices,
                best_depth=max(choices,key=lambda r:r['expected_tokens_per_second'])['draft_depth'])

if __name__ == '__main__':
    print(json.dumps(build(),ensure_ascii=False,indent=2))
