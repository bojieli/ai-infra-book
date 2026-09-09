# Sealed Chat prefix lifetime and restore bridge

Scope: three transitions between the same four original Chat requests already used by trace_resource_bridge. Source hashes are verified through that public bridge. Raw token IDs prove longest common token prefixes of 112/164/213; these equal reported cached_tokens, with cached_tokens_details device=N, host=0. This does not establish physical page identity or residency lifetime.

Declared policy: under the existing serial-returned-ID interpretation, retain the reused BF16 Qwen8 prefix from prior application completion until the next application send. This finite gap integral is not full-request memory occupancy, nor an observed allocator trace. Actual page lifetimes, restore bytes and times stay null. No claim that the entire preceding final state is retained.

Official full GQA BF16 state is 36 layers × K/V × 8 KV heads × 128 head width × 2 bytes = 147456 bytes/token. Reused prefix payloads are 16515072, 24182784 and 31408128 bytes. No arbitrary 16-token page rounding is applied to counters of 164/213 tokens; page layout is unknown.

Counterfactual host and remote alternatives use the same prefix payload. Default host effective bandwidth is a caller-assumed 25 GB/s; remote is 5 GB/s plus 10 us lookup, then serial H2D. Gap-fit is conditional on proactive movement starting at prior completion; it is not evidence that a transfer happened. Only the first host copy fits its recorded gap under these rates. Changing bandwidth never changes original observations, prefill work or retention integral.

Cold/warm prefill ledgers come from the existing source-backed Qwen8 calculation for these same request lengths. Three tests verify independent KV formula, exact rational retention integral, null observation fields, rate sensitivity, replay and input rejection. Public CLI/outline integration and independent review remain pending.

Root follow-up verified the archived capture script uses one monotonic application clock. Exact fractions preserve the decimal JSON timestamps, not instrument precision. Proactive movement requires advance knowledge of the next reused prefix. Minimum host bandwidth is bytes/gap; minimum remote bandwidth is bytes/(gap−lookup−H2D), undefined when no positive remote window remains. Independent raw-ID/Decimal-time/formula audit checks the integer rates immediately below and above each host threshold; 25 checks pass. Three candidate tests pass. Readable reports now expose default, host50gb and lookup2ms alternatives. Public integration remains pending.
