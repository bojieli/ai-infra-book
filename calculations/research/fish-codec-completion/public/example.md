# Fish CLI 代码块到波形导出

2个实际代码块，合计43帧；单次codec产生88064样本。

| 阶段 | D2H bytes | device复制写 bytes | CPU cast写 bytes |
|---|---:|---:|---:|
| sample_code_clone_and_cpu_conversation | 1680 | 1680 | 0 |
| sample_code_clone_and_cpu_conversation | 1760 | 1760 | 0 |
| next_concat_codes | 0 | 3440 | 0 |
| save_merged_codes_numpy_input | 3440 | 0 | 0 |
| single_codec_decode | 0 | 0 | 0 |
| wave_cpu_then_float | 176128 | 0 | 352256 |

复用codec矩阵FLOPs：290892476416；实际音频时长22016/11025秒。

TTFA、RTF、文件字节与完整runtime峰值未测量，保持unknown。

## 范围

- Pinned CLI with output enabled, one requested sample, GPU-generated code chunks and codec already loaded on that device. CPU path and codec model loading are not zero-cost substitutes.
- sample events expose codes only; CLI waits for next, concatenates all codes, then decodes once. No waveform is produced per emitted code chunk on this path.
- Requires actual emitted frame counts after unconditional y[1:, prompt_length:-1] slicing; removed last position need not be terminal. codeframes=returned_y_length-prompt_length-1. Text chunk_length is a text-byte limit, not audio frames or seconds.
- AR/fast-head work remains in omni_audio and is not duplicated here; codec_operations likewise replaces/reuses the existing codec stage, never add its matrices twice.
- Code CPU copies for conversation and NPY-save input are separate real copies. Their Python/CUDA overlap, total conversation lifetime and IO timing remain unknown.
- text2semantic export copies source waveform toCPU then converts toFP32; standalone dac CLI converts toFP32 on device beforeCPU. Their D2H bytes differ underBF16, though both hand float32 data to soundfile.
- NumPy views do not copy tensor data; soundfile encoding/default subtype/file buffering are not inferred from float32 host-array bytes.
- No wall-clock measurements supplied: TTFA/RTF are null. Required dependency is all code chunks -> next -> concatenation/save input -> codec -> host conversion -> file writer.

## 固定来源

- [research/generative-audio-analysis/transformers/src/transformers/models/qwen3_omni_moe/modeling_qwen3_omni_moe.py](https://raw.githubusercontent.com/huggingface/transformers/8cb5963cc22174954e7dca2c0a3320b7dc2f4edc/src/transformers/models/qwen3_omni_moe/modeling_qwen3_omni_moe.py)；SHA256 `809eaeb4d40cb0e59965a85b5f85ddc07e9ab7b6cdae84972c711f8cdadec296`。
- [research/generative-audio-analysis/transformers/src/transformers/models/qwen3_omni_moe/configuration_qwen3_omni_moe.py](https://raw.githubusercontent.com/huggingface/transformers/8cb5963cc22174954e7dca2c0a3320b7dc2f4edc/src/transformers/models/qwen3_omni_moe/configuration_qwen3_omni_moe.py)；SHA256 `779bf4b816425448d5d3a2ffa57928d1c7b7c10e2d66b09371fceaee62bcbf89`。
- [research/generative-audio-analysis/fish/fish_speech/models/text2semantic/llama.py](https://raw.githubusercontent.com/fishaudio/fish-speech/befe4001745417f8c42131739d862b8a6fdbd15a/fish_speech/models/text2semantic/llama.py)；SHA256 `b7dc3c039ddcbc05e445293e5d4babb1e80340b8a2944747fab0cf44c0919852`。
- [research/generative-audio-analysis/fish/fish_speech/models/text2semantic/inference.py](https://raw.githubusercontent.com/fishaudio/fish-speech/befe4001745417f8c42131739d862b8a6fdbd15a/fish_speech/models/text2semantic/inference.py)；SHA256 `9c85ce70e93dd990ac53a0831bf6d909d74eb434de5608f54fe00bfc129d4cae`。
- [research/generative-audio-analysis/fish/fish_speech/models/dac/modded_dac.py](https://raw.githubusercontent.com/fishaudio/fish-speech/befe4001745417f8c42131739d862b8a6fdbd15a/fish_speech/models/dac/modded_dac.py)；SHA256 `a08407421ee85d8af28377d6a14d989b5a17a985c9719f8b5701cd0a845840c0`。
- [research/generative-audio-analysis/fish/fish_speech/models/dac/inference.py](https://raw.githubusercontent.com/fishaudio/fish-speech/befe4001745417f8c42131739d862b8a6fdbd15a/fish_speech/models/dac/inference.py)；SHA256 `a34210e04904a2be93eb09c46878e740837661318a40ee0e9070148ce1401e60`。
- [research/generative-audio-analysis/fish/fish_speech/models/dac/rvq.py](https://raw.githubusercontent.com/fishaudio/fish-speech/befe4001745417f8c42131739d862b8a6fdbd15a/fish_speech/models/dac/rvq.py)；SHA256 `a4d38e529846473c712dd1b2f5eaa889eb0233fd56228799c168060f335c0246`。
- [research/generative-audio-analysis/fish/fish_speech/configs/modded_dac_vq.yaml](https://raw.githubusercontent.com/fishaudio/fish-speech/befe4001745417f8c42131739d862b8a6fdbd15a/fish_speech/configs/modded_dac_vq.yaml)；SHA256 `73321408579c372149620d877f0dfb841cf70465758a535f7243e1cb6553d56a`。
- [research/generative-audio-analysis/transformers-current/src/transformers/models/qwen3_omni_moe/modeling_qwen3_omni_moe.py](https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/src/transformers/models/qwen3_omni_moe/modeling_qwen3_omni_moe.py)；SHA256 `0ec28dd7714f09de8749edc958c25c0ebcc0628c9c2a0dca3abd905e7cddab04`。
- [research/generative-audio-analysis/fish/pyproject.toml](https://raw.githubusercontent.com/fishaudio/fish-speech/befe4001745417f8c42131739d862b8a6fdbd15a/pyproject.toml)；SHA256 `7fdd2e4f01746b884b368b7003c315d285cf86a36031035b3f28d7aafe68ea15`。
- [research/generative-audio-analysis/descript/dac/nn/quantize.py](https://raw.githubusercontent.com/descriptinc/descript-audio-codec/c7cfc5d2647e26471dc394f95846a0830e7bec34/dac/nn/quantize.py)；SHA256 `e2dc61f32f6123aa48a0aeb934a0d9a41ea29a5eae8db28119c791885c9f1b07`。
- [research/generative-audio-analysis/descript/dac/nn/layers.py](https://raw.githubusercontent.com/descriptinc/descript-audio-codec/c7cfc5d2647e26471dc394f95846a0830e7bec34/dac/nn/layers.py)；SHA256 `ec2649649d787b166a138d5ad9dcd585aeabbcd93670771b30cbbbab731c4b63`。
