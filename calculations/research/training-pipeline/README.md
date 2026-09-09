# Qwen3-8B GPipe / synchronous 1F1B candidate

The implementation and five focused tests are under public/. See CONTRACT.md for exact schedule, resource, service-time and retention semantics. This independent candidate changes no shared code.

Run:

```sh
python -m unittest discover -s calculations/research/training-pipeline/public/tests -v
python calculations/research/training-pipeline/build_delivery.py
```

Five test groups pass across M=1/4/8/16, both policies, balanced analytic schedules, unequal F/B, slow stage, independent/shared links, dependency/resource/lifetime invariants, true Qwen work/parameter conservation, recompute policy, scenario replay and bad inputs. Fourteen JSON/Markdown outputs, scenario-summary.json and source/dependency hashes are generated. The build script writes only this candidate directory.

No whole-model peak or actual runtime is inferred. Default forward/backward times are explicit conditional scenario values. Saved nonlinear objects are real existing reference objects; their full-stage reservation is conservative and partial. Output gradient/activation transfer buffers are counted separately, and additional saved bytes can be supplied by stage.
