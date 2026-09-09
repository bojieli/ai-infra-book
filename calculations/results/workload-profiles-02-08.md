# 封存请求画像与 p95

p95 使用 nearest-rank；空指标保留 null，小样本不能代表总体尾部。

## chat_capture

| 指标 | 单位 | 样本/缺失 | min | median | mean | p95 | max |
| --- | --- | --- | --- | --- | --- | --- | --- |
| input_tokens | tokens | 4/0 | 116 | 192.5 | 188.25 | 252 | 252 |
| output_id_tokens | returned token IDs | 4/0 | 8 | 21.0 | 19.75 | 29 | 29 |
| cached_tokens | tokens | 4/0 | 0 | 138.0 | 122.25 | 213 | 213 |
| previous_same_worker_completion_gap_s | seconds | 3/1 | 0.00071111717261374 | 0.0007473889272660017 | 0.000819801352918148 | 0.0010008979588747025 | 0.0010008979588747025 |
| model_s | seconds | 4/0 | 0.09583428199402988 | 0.23093588755000383 | 0.2164401414920576 | 0.30805450887419283 | 0.30805450887419283 |
| tool_s | seconds | 0/4 | None | None | None | None | None |

## chat_round_robin_trial0

| 指标 | 单位 | 样本/缺失 | min | median | mean | p95 | max |
| --- | --- | --- | --- | --- | --- | --- | --- |
| input_tokens | tokens | 4/0 | 116 | 192.5 | 188.25 | 252 | 252 |
| output_id_tokens | returned token IDs | 4/0 | 8 | 21.0 | 19.75 | 29 | 29 |
| cached_tokens | tokens | 4/0 | 0 | 56.0 | 69 | 164 | 164 |
| previous_same_worker_completion_gap_s | seconds | 2/2 | 0.09693896514363587 | 0.136028140084818 | 0.136028140084818 | 0.17511731502600014 | 0.17511731502600014 |
| model_s | seconds | 4/0 | 0.09670481202192605 | 0.2295973099535331 | 0.22040927573107183 | 0.32573767099529505 | 0.32573767099529505 |
| tool_s | seconds | 0/4 | None | None | None | None | None |

## chat_cache_aware_trial0

| 指标 | 单位 | 样本/缺失 | min | median | mean | p95 | max |
| --- | --- | --- | --- | --- | --- | --- | --- |
| input_tokens | tokens | 4/0 | 116 | 192.5 | 188.25 | 252 | 252 |
| output_id_tokens | returned token IDs | 4/0 | 8 | 21.0 | 19.75 | 29 | 29 |
| cached_tokens | tokens | 4/0 | 0 | 138.0 | 122.25 | 213 | 213 |
| previous_same_worker_completion_gap_s | seconds | 3/1 | 0.00012062489986419678 | 0.0001258370466530323 | 0.0001274316261212031 | 0.00013583293184638023 | 0.00013583293184638023 |
| model_s | seconds | 4/0 | 0.09641105099581182 | 0.231897140503861 | 0.2167507252888754 | 0.30679756915196776 | 0.30679756915196776 |
| tool_s | seconds | 0/4 | None | None | None | None | None |

## chat_power_of_two_trial0

| 指标 | 单位 | 样本/缺失 | min | median | mean | p95 | max |
| --- | --- | --- | --- | --- | --- | --- | --- |
| input_tokens | tokens | 4/0 | 116 | 192.5 | 188.25 | 252 | 252 |
| output_id_tokens | returned token IDs | 4/0 | 8 | 21.0 | 19.75 | 29 | 29 |
| cached_tokens | tokens | 4/0 | 0 | 56.0 | 69 | 164 | 164 |
| previous_same_worker_completion_gap_s | seconds | 2/2 | 0.09692051005549729 | 0.13905591994989663 | 0.13905591994989663 | 0.18119132984429598 | 0.18119132984429598 |
| model_s | seconds | 4/0 | 0.09666296816430986 | 0.23276351403910667 | 0.21732506883563474 | 0.30711027910001576 | 0.30711027910001576 |
| tool_s | seconds | 0/4 | None | None | None | None | None |

## chat_power_of_two_trial1

| 指标 | 单位 | 样本/缺失 | min | median | mean | p95 | max |
| --- | --- | --- | --- | --- | --- | --- | --- |
| input_tokens | tokens | 4/0 | 116 | 192.5 | 188.25 | 252 | 252 |
| output_id_tokens | returned token IDs | 4/0 | 8 | 21.0 | 19.75 | 29 | 29 |
| cached_tokens | tokens | 4/0 | 0 | 56.0 | 69 | 164 | 164 |
| previous_same_worker_completion_gap_s | seconds | 2/2 | 0.09686613292433321 | 0.13905277545563877 | 0.13905277545563877 | 0.18123941798694432 | 0.18123941798694432 |
| model_s | seconds | 4/0 | 0.09661875385791063 | 0.23297353752423078 | 0.21738497650949284 | 0.3069740771315992 | 0.3069740771315992 |
| tool_s | seconds | 0/4 | None | None | None | None | None |

## chat_cache_aware_trial1

| 指标 | 单位 | 样本/缺失 | min | median | mean | p95 | max |
| --- | --- | --- | --- | --- | --- | --- | --- |
| input_tokens | tokens | 4/0 | 116 | 192.5 | 188.25 | 252 | 252 |
| output_id_tokens | returned token IDs | 4/0 | 8 | 21.0 | 19.75 | 29 | 29 |
| cached_tokens | tokens | 4/0 | 0 | 138.0 | 122.25 | 213 | 213 |
| previous_same_worker_completion_gap_s | seconds | 3/1 | 9.262398816645145e-05 | 0.00011562788859009743 | 0.00010866097485025723 | 0.00011773104779422283 | 0.00011773104779422283 |
| model_s | seconds | 4/0 | 0.09660550393164158 | 0.2314896455500275 | 0.21656421525403857 | 0.30667206598445773 | 0.30667206598445773 |
| tool_s | seconds | 0/4 | None | None | None | None | None |

## chat_round_robin_trial1

| 指标 | 单位 | 样本/缺失 | min | median | mean | p95 | max |
| --- | --- | --- | --- | --- | --- | --- | --- |
| input_tokens | tokens | 4/0 | 116 | 192.5 | 188.25 | 252 | 252 |
| output_id_tokens | returned token IDs | 4/0 | 8 | 21.0 | 19.75 | 29 | 29 |
| cached_tokens | tokens | 4/0 | 0 | 56.0 | 69 | 164 | 164 |
| previous_same_worker_completion_gap_s | seconds | 2/2 | 0.0930466610006988 | 0.13882985548116267 | 0.13882985548116267 | 0.18461304996162653 | 0.18461304996162653 |
| model_s | seconds | 4/0 | 0.09280901588499546 | 0.23440988850779831 | 0.21720150572946295 | 0.3071772300172597 | 0.3071772300172597 |
| tool_s | seconds | 0/4 | None | None | None | None | None |

## agent_thinking_off

| 指标 | 单位 | 样本/缺失 | min | median | mean | p95 | max |
| --- | --- | --- | --- | --- | --- | --- | --- |
| input_tokens | tokens | 12/0 | 210 | 1621.5 | 1629.6666666666667 | 3136 | 3136 |
| output_id_tokens | returned token IDs | 12/0 | 20 | 20.0 | 63.75 | 125 | 125 |
| cached_tokens | tokens | 12/0 | 0 | 1328.0 | 1358.6666666666667 | 2912 | 2912 |
| previous_same_worker_completion_gap_s | seconds | 11/1 | 0.0019418210722506046 | 0.062331815948709846 | 0.044973301108587875 | 0.09059542301110923 | 0.09059542301110923 |
| model_s | seconds | 12/0 | 0.31017042184248567 | 0.3776013065362349 | 1.096370850224048 | 2.33632974489592 | 2.33632974489592 |
| tool_s | seconds | 12/0 | 0.00015548104420304298 | 0.05734895449131727 | 0.039700846711639315 | 0.0841115228831768 | 0.0841115228831768 |

## agent_thinking_on

| 指标 | 单位 | 样本/缺失 | min | median | mean | p95 | max |
| --- | --- | --- | --- | --- | --- | --- | --- |
| input_tokens | tokens | 4/0 | 206 | 1549.5 | 1324.25 | 1992 | 1992 |
| output_id_tokens | returned token IDs | 4/0 | 134 | 699.5 | 683.25 | 1200 | 1200 |
| cached_tokens | tokens | 4/0 | 0 | 1416.0 | 1120 | 1648 | 1648 |
| previous_same_worker_completion_gap_s | seconds | 3/1 | 0.00721334689296782 | 0.009870798792690039 | 0.03329766859921316 | 0.08280886011198163 | 0.08280886011198163 |
| model_s | seconds | 4/0 | 3.456244467990473 | 18.231043312116526 | 19.07341070030816 | 36.37531170900911 | 36.37531170900911 |
| tool_s | seconds | 4/0 | 6.058579310774803e-05 | 0.0016988785937428474 | 0.01942559878807515 | 0.07424405217170715 | 0.07424405217170715 |

## 范围

- Rows come from the hash-locked derived analysis of the archived 02-08 captures; no new model execution or timing measurement.
- p95 is sorted_values[ceil(0.95*n)-1]; for at most 19 observations it equals the maximum. Empty metrics retain null, not zero.
- Returned output IDs include EOS when recorded. These counts are not silently converted into decode calls or useful answer tokens.
- The completion-to-next-send gap includes controller/tool behavior; it is not human think time, exact block reuse distance or KV residency.
- Recorded model/tool seconds describe these captures only; they are not GPU predictions or throughput comparisons across groups.

## 封存来源

- [experiments/ch02/02-08/summary.json](../../experiments/ch02/02-08/summary.json) SHA256 `43ada8e6e7b59088afc9f54fc353a1f0677975b000a714e9cb282ad0b037cd30`
- [experiments/ch02/02-08/analyze.py](../../experiments/ch02/02-08/analyze.py) SHA256 `7bbd65c5635bcd1783860d574dceae23f16117e8dbfe65bb3cf859f8e72db961`
- [experiments/ch02/02-08/source-index.json](../../experiments/ch02/02-08/source-index.json) SHA256 `fa89a24405fccb0072a9874a8b3959e09e2060a5dfffe015bc28625cb51ff1cd`
