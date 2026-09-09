# Trace resource bridge public integration acceptance

Accepted module SHA `966e154198a92fdb64d256c9fdb9ad07172276f628842c3bc2ef86228e8bb460`. The installed module is byte-identical to the frozen candidate, stronger than AST-only equivalence. Original bindings and every copied local-source bundle entry match. Public execution needs no research imports.

Both scenarios match all frozen JSON fields after ordinary JSON tuple-to-array normalization (the reused weight ledger has Python tuple shapes). Native Python scenario replay also matches exactly. Four actual CLI subprocesses, JSON and complete Markdown for both scenarios, match frozen results. Four installed public tests pass, zero skipped.

Independent boundary checks confirm every recorded input length equals mapped restored prefix plus new tokens. Default unknown_steps leaves sampled_steps, decode call count, decode resource account, complete logical totals and final state null. The explicit serial policy counts G−1 decode calls from returned IDs as its declared assumption. Both policies keep observed_model_forward_calls null at aggregate and per-request levels. Thus the bridge maps observed lengths to logical resources; it does not retrospectively infer actual scheduler/model execution calls, nor remove EOS as if returned IDs were useful-answer tokens.

Negative checks invoke actual public CLI dispatch with only SOURCE_ROOT redirected to an isolated exact copy: a missing locked original and a same-length byte modification are both rejected, with nonzero exit and no result output. The modified case identifies a sealed trace source mismatch. Shared sources were never mutated, avoiding interference with parent reproduction.

Evidence is in results.json, tests.log and check.py. Validation used /Users/boj/miniconda3/bin/python. Recorded request/engine wall time and tool-null fields remain distinct from logical compute; no GPU throughput or complete runtime trace is inferred. No remaining integration issue was found.
