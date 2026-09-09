# Independent selected CPU preprocessing review

12,772 independent assertions and six original accounting/interface tests passed without skips. Expanded-polynomial NumPy reconstruction checks support intervals, normalized INT16 coefficients and precision bits across enlargement, reduction and boundary sizes. Tap enumeration checks integer MAC/operand bytes. Locked C++ coefficient initialization/normalization/repack and fixed processor normalization/layout were read directly; source hashes match.

Official-AST numerical oracle rerun (evidence redirected to numeric-replay.json): five full images, four extra resize kernels and five geometry cases pass. This author-oracle replay is distinguished from independent coefficient/accounting reconstruction. Torch2.7/torchvision0.22/non-AVX identities checked. Maximum-area case is geometry/budget only. Five public tests pass; all four public result objects exactly replay frozen candidates.

Accepted only single already-decoded contiguous RGB CPU selected path. Integer convolution is not floating-point work; operand traffic is not external-memory measurement. Decode/color handling, arbitrary backend/AutoProcessor dispatch, device transfer and runtime peak/latency remain excluded. Encoder matrices stay downstream, BF16 boundary cast counted once.
