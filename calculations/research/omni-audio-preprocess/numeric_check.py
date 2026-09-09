"""Selected official classes vs independent frame/FFT/mask reference."""

from pathlib import Path
import cmath, functools, hashlib, json, math
import numpy as np
import torch
from source_runner import load
from omni_audio_preprocess import calculate, reference_fft_work

HERE = Path(__file__).resolve().parent


@functools.lru_cache(None)
def twiddle(n, j, k):
    return cmath.exp(-2j * math.pi * j * k / n)


def fft(values, counter=None):
    n = len(values)
    if n == 1:
        return list(values)
    radix = 2 if n % 2 == 0 else 5
    children = [fft(values[j::radix], counter) for j in range(radix)]
    output = []
    for k in range(n):
        terms = [twiddle(n, j, k) * children[j][k % (n // radix)] for j in range(radix)]
        total = terms[0]
        for value in terms[1:]:
            total += value
        output.append(total)
        if counter is not None:
            counter["real_multiplications"] += 4 * radix
            counter["real_additions"] += 2 * radix + 2 * (radix - 1)
            counter["complex_products"] += radix
    return output


def reference(waves, filters):
    valid = [np.asarray(x[:480000], dtype=np.float32) for x in waves]
    length = max(map(len, valid))
    frames = length // 160
    mel = []
    masks = []
    window = 0.5 - 0.5 * np.cos(2 * np.pi * np.arange(400) / 400)
    for wave in valid:
        right = np.pad(wave, (0, length - len(wave)))
        padded = np.pad(right, (200, 200), mode="reflect")
        spectra = []
        for frame in range(frames + 1):
            vec = padded[frame * 160 : frame * 160 + 400].astype(np.float64) * window
            spectra.append(fft(vec))
        power = np.abs(np.asarray(spectra)[:-1, :201].T) ** 2
        log = np.log10(np.maximum(filters.T @ power, 1e-10))
        log = np.maximum(log, log.max() - 8)
        mel.append(((log + 4) / 4).astype(np.float32))
        mask = np.zeros(length, dtype=np.int32)
        mask[: len(wave)] = 1
        mask = mask[::160]
        if length % 160:
            mask = mask[:-1]
        masks.append(mask)
    return np.asarray(mel), np.asarray(masks)


def main():
    extractor = load()
    assert extractor.n_samples == 480000 and extractor.nb_max_frames == 3000
    results = []
    cases = [
        ("zero", [np.zeros(320, dtype=np.float32)]),
        ("impulse", [np.eye(1, 401, 0, dtype=np.float32).ravel()]),
        ("signal", [np.sin(np.arange(961) * 0.037).astype(np.float32)]),
        (
            "mixed",
            [
                np.cos(np.arange(479) * 0.03).astype(np.float32),
                np.sin(np.arange(800) * 0.04).astype(np.float32),
            ],
        ),
    ]
    for name, waves in cases:
        actual = extractor(
            waves,
            sampling_rate=16000,
            padding=True,
            return_attention_mask=True,
            return_tensors="np",
        )
        expected, mask = reference(waves, extractor.mel_filters)
        error = float(np.max(np.abs(expected - actual["input_features"])))
        assert error < 1e-4, (name, error)
        assert np.array_equal(mask, actual["attention_mask"])
        result = calculate([len(x) for x in waves])
        assert result["geometry"]["valid_mel_lengths"] == mask.sum(-1).tolist()
        selected = (
            torch.from_numpy(actual["input_features"])
            .permute(0, 2, 1)[torch.from_numpy(mask).bool()]
            .permute(1, 0)
        )
        assert (
            list(selected.shape) == result["geometry"]["selected_encoder_input_shape"]
        )
        results.append(
            dict(
                case=name,
                max_absolute_mel_error=error,
                mask_exact=True,
                shape=list(expected.shape),
            )
        )
    counter = dict(real_multiplications=0, real_additions=0, complex_products=0)
    vec = [math.sin(i * 0.17) for i in range(400)]
    observed = np.array(fft(vec, counter))
    error = float(np.max(np.abs(observed - np.fft.fft(vec))))
    assert error < 1e-10
    assert counter == reference_fft_work()
    # Long/cap tests run official Torch; independent expected geometry, not huge Python FFT.
    boundaries = []
    for lengths in [[201], [319], [320], [321], [479, 800], [480001], [4800000]]:
        waves = [np.zeros(n, dtype=np.float32) for n in lengths]
        a = extractor(
            waves,
            sampling_rate=16000,
            padding=True,
            return_attention_mask=True,
            return_tensors="np",
        )
        r = calculate(lengths)
        assert list(a["input_features"].shape) == r["geometry"]["input_features_shape"]
        assert (
            a["attention_mask"].sum(-1).tolist() == r["geometry"]["valid_mel_lengths"]
        )
        boundaries.append(
            dict(
                lengths=lengths,
                shape=list(a["input_features"].shape),
                valid_frames=a["attention_mask"].sum(-1).tolist(),
            )
        )
    for length in [1, 160, 200]:
        try:
            extractor(
                [np.zeros(length, dtype=np.float32)],
                sampling_rate=16000,
                padding=True,
                return_attention_mask=True,
            )
        except RuntimeError:
            pass
        else:
            raise AssertionError("Expected official reflect-pad failure")
        try:
            calculate([length])
        except ValueError:
            pass
        else:
            raise AssertionError("Expected calculator rejection")
    output = dict(
        torch_version=torch.__version__,
        torch_git=torch.version.git_version,
        numpy_version=np.__version__,
        official_effective_n_samples=extractor.n_samples,
        official_effective_nb_max_frames=extractor.nb_max_frames,
        full_numerical_cases=results,
        boundary_cases=boundaries,
        fft_max_error=error,
        reference_fft_count=counter,
        short_reflect_rejections=[1, 160, 200],
        scope="Verbatim selected pinned class/functions via AST, dependency containers shimmed; no full model or hardware performance claim",
    )
    (HERE / "numeric-verification.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
