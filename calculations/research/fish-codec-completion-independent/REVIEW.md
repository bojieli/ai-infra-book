# Independent Fish code collection / waveform export review

Verdict: no remaining numerical or execution-order blocker for the declared GPU text2semantic CLI wrapper after the emitted-frame wording correction. This is an outer interface ledger around the already available Fish codec. It does not complete all Fish request work, runtime latency or C78/C79.

The final reviewed root/public calculate ASTs are identical. bindings.json binds both sources, contract and source lock; snapshot.py preserves the reviewed root module. Public module SHA at review: `8c40005dde594ebdafd9acd3f3fe9bfa03af46a106939fd2e9fdf8f1ee9bbee9` (includes renderer). Reviewer did not edit author or shared files.

## Source execution order

All five direct official originals match their locked SHA256 and byte counts, revision befe4001745417f8c42131739d862b8a6fdbd15a. In text2semantic/inference.py the generated-code slice is cloned on device, checked nonnegative, then copied to CPU for conversation storage; the yielded sample retains device codes. The outer CLI appends those code chunks without decoding. On next it concatenates once, copies merged codes to CPU for np.save input, then calls codec.from_indices once through decode_to_audio. Thus code D2H payload is twice the complete10-codebook array; chunk count does not multiply codec work.

The waveform export is audio.cpu().float().numpy(): BF16 waveform crosses D2H as2-byte elements, then is cast on CPU to4-byte float32. Standalone dac/inference.py is fake_audios[0,0].float().cpu().numpy(), reversing the cast/copy order and transferring4-byte elements. Both NumPy calls alias the corresponding CPU tensor data. Neither NumPy bytes nor float32 waveform bytes establish the eventual soundfile container/subtype/file size.

Code-list+merged overlap is correctly only a selected object overlap, not full peak. Generator locals and conversation data can remain live; codec buffers, temporary kernels, allocation behavior and file writer buffers are outside this partial graph. Nonnegative scalar host checks are identified separately; the code D2H subtotal is not asserted to contain all synchronization traffic.

## G / emitted-frame boundary correction

The original wording called the removed last position terminal. Fixed source slices y[1:,prompt_length:-1] unconditionally. If generation exhausts its budget, the removed last column need not be a terminal token. Author corrected scope and CONTRACT to use actual emitted frames = returned_y_length - prompt_length -1. No calculation changed: inputs were already explicit emitted chunk frames, not text bytes, generation budget or predicted output count.

The fixed generate implementation also calls decode_n_tokens(max_new_tokens-1), whose empty loop returns torch.cat([]). A max_new_tokens1 path therefore fails rather than defining a successful zero-frame sample. Rejecting zero emitted-frame inputs in this selected successful wrapper is consistent; do not extrapolate it to a supported one-token generator path. Earlier EOS and budget limits mean the frame count cannot be inferred from a max-token budget alone.

## Independent checks and time contract

check.py passes28 independent groups: five original hash/length checks, source-order checks,16 chunk/dtype/code-width cases (including32768-frame supported edge), segmentation invariance and invalid bounds. Each case mocks the codec entry to verify exactly one invocation on the merged frame count; integer sample clock is derived from4x restoration times512 DAC upsampling =2048 samples/frame at44100Hz. It checks clone/read/write payloads, conversation and merged-save D2H, list+merged overlap, BF16 CPU cast and FP32 alias cases, standalone contrasting D2H bytes, and all unknown latency/file/peak fields. Four author tests were independently rerun and passed.

For21+22 frames, output is88064 samples and exact duration88064/44100 seconds. int64 codes transfer6880 bytes across the two D2H copies; BF16 waveform D2H is176128 bytes and CPU float32 output352256 bytes. These are payload/count facts, not timing measurements.

There is no supplied wall-clock record. First waveform depends on all code chunks, next, concat/save input, codec and host conversion; first code sample is not first audio. TTFA, full request latency and measured RTF correctly remain null. Exact duration is a sample-clock quantity and must not be substituted for elapsed inference time. Existing AR and codec stage work must each be counted once when integrating this wrapper.
