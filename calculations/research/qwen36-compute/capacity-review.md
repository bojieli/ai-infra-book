# Independent capacity review

Reviewed public `qwen36_capacity.py` and exercised actual `python -m infra_calc qwen36-capacity` CLI with default inputs, three custom inputs, an exact nominal80GB boundary and one byte above it, and five invalid inputs. No implementation blocker found.

Independent formula:

`required = selected_weights + batch * (20,480 * length + 62,914,560 + 1,966,080) + reserve_bytes`

The terms are respectively10 full-attention layers ×2 KV tensors ×2 KV heads ×256 channels ×2bytes per history token;30 linear layers ×32 value heads ×128×128 ×4bytes recurrent state;30 linear layers ×8192 convolution channels ×4 kernel slots ×2bytes. All experts reside in selected weights; top8 affects active arithmetic but does not shrink resident weight storage.

Header-derived base weights69,321,221,376bytes; complete checkpoint71,903,645,408bytes; difference2,582,424,032bytes equals vision893,142,496 plus MTP1,689,281,536. The auxiliary option retains these weights but does not count executing their states; this is stated accurately. File headers and index metadata overhead are excluded because the result counts tensor payloads, not checkpoint disk file sizes or allocation traces.

Default B1,length8192,reserve2GiB budget71,701,357,824bytes. RTX4090/5090 fail; nominal H10080GB, workstation96GB, and Mac96GB pass the declared necessary budget. This cannot establish runnable memory headroom, especially on shared Mac memory; runtime and throughput fields remain null, and prose explicitly preserves this limitation.

CLI checks passed:

- Default exact formula and all device flags.
- B3,length1,reserve0; B2,length262144 with auxiliary weights; default history with auxiliary weights.
- Required budget exactly80,000,000,000bytes passes H100 with zero headroom; plus1byte fails with minus1headroom.
- Boolean batch, zero length, length262145, negative reserve, and nonboolean auxiliary flag reject.

Keep chapter wording tied to the declared screen. Nominal vendorGB is interpreted as decimal by explicit assumption; it is not a measurement of usable device allocation. The arbitrary2GiB reserve likewise expresses a scenario condition, not a universal lower bound on actual workspace. Passing this screen is necessary only relative to these declared storage/state/reserve assumptions and says nothing about eager prefill activation peaks, installation support, or latency.

Read-only public review; only research review artifacts were written. Reproducer: `review_capacity_cli.py` in this directory.
