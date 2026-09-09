# Public vision preprocessing candidate

Copy src/infra_calc/topics/vision_preprocess.py, tests/test_vision_preprocess.py, configs/vision-preprocess.lock.json and sources/vision-preprocess into calculations. Register vision-preprocess calculate()/markdown() and append the four book.append.json scenarios. Suggested CLI inputs: --height, --width, --encoder-dtype bf16|fp32, --normalization-cache cold|warm. The module imports the normal project path helper; no research Python is loaded.

Numerics are unchanged from the frozen candidate. Every call validates the independent source lock, reads the fixed preprocessor config, generates true filter tap ranges and INT16 coefficients, and reports per-stage scalar/integer work/semantic bytes. resize_axes retains all coefficients for direct reproduction. Four full result/report pairs are included: aligned640, nonsquare257×385, min-area32², max-area4608² geometry/budget. Do not interpret the last budget as an executed large-image performance measurement.

Join summary.resized_height/width to existing vision_encoding with one image and the declared dtype. Processor pixel_values remains FP32; the optional BF16 cast belongs at the visual boundary once. Existing patch matrix and language totals must not change. H2D/JPEG/PNG/ICC/device runtime are excluded explicitly; do not claim all C81 closed. The single-image CPU grouping path is intentionally fixed.

Run `PYTHONDONTWRITEBYTECODE=1 python calculations/research/vision-preprocess/public/replay.py`: compares all four scenario/summary/axis/stage values against the original frozen files, normalizing only source-reference paths, then generates reports and bindings. Run portable tests with `PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s calculations/research/vision-preprocess/public/tests -v` (five tests; the sixth original test was solely the unrelated hardware-prose proposal).

Necessary official processor/backend/geometry/misc/PyTorch kernel/config/model entry sources and frozen numerical verification are included under the dedicated lock. Full numerical replay stays in the original numeric_check.py, requiring torch2.7/torchvision0.22 CPU non-AVX; public ordinary tests need no tensor allocation. Source AST replay is not notebook/model code execution in the topic.

Hardware prose patch remains separately in ../hardware-prose.patch.json and is not part of these preprocessing data/config changes.
