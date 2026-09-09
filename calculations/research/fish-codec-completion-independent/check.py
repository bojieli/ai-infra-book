"""Independent source-order, integer clock, single-decode and copy-boundary audit."""
import hashlib
import importlib.util
import json
import sys
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from infra_calc.topics import omni_audio
HERE = Path(__file__).resolve().parent
CANDIDATE = ROOT / "research/fish-codec-completion"
MODULE = CANDIDATE / "fish_wave_export.py"
spec = importlib.util.spec_from_file_location("fish_candidate", MODULE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
checks = []
for row in json.loads((CANDIDATE / "source-lock.json").read_text()):
    data = (ROOT / row["file"]).read_bytes()
    assert len(data) == row["bytes"] and hashlib.sha256(data).hexdigest() == row["sha256"]
    checks.append("verified " + row["file"])
source = (ROOT / "research/generative-audio-analysis/fish/fish_speech/models/text2semantic/inference.py").read_text()
standalone = (ROOT / "research/generative-audio-analysis/fish/fish_speech/models/dac/inference.py").read_text()
assert source.index('codes = y[1:, prompt_length:-1].clone()') < source.index('parts=[VQPart(codes=codes.cpu()') < source.index('yield GenerateResponse(action="sample"')
main = source[source.index('    for response in generator:'):]
assert main.index('torch.cat(codes, dim=1)') < main.index('merged_codes.cpu().numpy()') < main.index('decode_to_audio(merged_codes.to(device), codec)') < main.index('audio.cpu().float().numpy()')
assert 'fake_audios[0, 0].float().cpu().numpy()' in standalone
checks.append("pinned GPU clone/D2H/yield/concat/save/codec/CPU-cast order")

# The fixed decoder restores a4x latent downsample and its DAC rates multiply
# to512; the product is2048 output samples/frame, independent of text chunks.
for frames in ([1], [21, 22], [7, 13, 23], [32768]):
    for dtype, width in (("bf16", 2), ("fp32", 4)):
        for code_width in (4, 8):
            with patch.object(omni_audio, "omni_codec_operators", wraps=omni_audio.omni_codec_operators) as decoder:
                result = module.calculate(frames, waveform_dtype=dtype, code_element_bytes=code_width)
                assert decoder.call_count == 1
                assert decoder.call_args.args[0] == sum(frames)
            s, events = result["summary"], result["wrapper_stages"]
            samples = sum(frames) * 2048
            codes = sum(frames) * 10 * code_width
            assert s["output_samples"] == samples
            assert Fraction(s["exact_audio_duration_seconds"]) == Fraction(samples, 44100)
            assert s["code_device_to_host_bytes"] == 2 * codes
            assert s["waveform_device_to_host_bytes"] == samples * width
            assert s["standalone_dac_cli_wave_device_to_host_bytes"] == samples * 4
            clones = events[:len(frames)]
            assert sum(e["device_copy_read_bytes"] for e in clones) == codes
            assert sum(e["device_copy_write_bytes"] for e in clones) == codes
            assert sum(e["device_to_host_bytes"] for e in clones) == codes
            assert clones[-1]["held_code_list_device_bytes"] == codes
            assert events[len(frames)]["code_list_plus_merged_device_bytes"] == 2 * codes
            wave = events[-1]
            assert wave["host_cast_write_bytes"] == (samples * 4 if width == 2 else 0)
            assert wave["host_cast_read_bytes"] == (samples * 2 if width == 2 else 0)
            assert wave["host_numpy_alias_bytes"] == samples * 4
            for key in ("full_request_latency_seconds", "first_audio_latency_seconds", "measured_rtf", "output_file_bytes", "full_runtime_peak_bytes"):
                assert s[key] is None
            checks.append(f"chunks={frames},dtype={dtype},codebytes={code_width}: clock/copies/singledecode/unknown")

# Split code chunks cannot imply multiple decoders, changed waveform duration,
# or frame count derived from text bytes. Decode matrix and samples invariant.
a, b = module.calculate([43]), module.calculate([21, 22])
assert a["codec_operations"] == b["codec_operations"]
assert a["summary"]["exact_audio_duration_seconds"] == b["summary"]["exact_audio_duration_seconds"]
checks.append("chunk segmentation invariant codec and clock")
for frames in ([], [0], [-1], [True], [32769]):
    try:
        module.calculate(frames)
    except ValueError:
        checks.append(f"unsupported emitted frames {frames} rejected")
    else:
        raise AssertionError(frames)
(HERE / "results.json").write_text(json.dumps(dict(module_sha256=hashlib.sha256(MODULE.read_bytes()).hexdigest(), checks=checks, count=len(checks)), indent=2) + "\n")
print(f"PASS {len(checks)} independent groups")
