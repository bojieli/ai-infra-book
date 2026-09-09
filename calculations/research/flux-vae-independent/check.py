"""Independent decoder graph formula and explicit-lifetime checks."""

from pathlib import Path
import hashlib
import importlib.util
import json
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
source = ROOT / "research/flux-vae-decode/flux_vae_decode.py"
spec = importlib.util.spec_from_file_location("review_flux", source)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


# Construct an independent list of convolution/linear dimensions from source
# stage channel counts; no candidate weight list or image_stages helper used.
def oracle(height, width, batch):
    h, w = height // 8, width // 8
    conv = []
    norm = []

    def add(ci, co, k=3):
        conv.append((ci, co, k, h, w))

    def res(ci, co):
        norm.extend([ci, co])
        add(ci, co)
        add(co, co)
        if ci != co:
            add(ci, co, 1)

    add(32, 32, 1)
    add(32, 512)
    res(512, 512)
    norm.append(512)
    for _ in range(4):
        add(512, 512, 1)
    res(512, 512)
    previous = 512
    for i, co in enumerate([512, 512, 256, 128]):
        res(previous, co)
        res(co, co)
        res(co, co)
        previous = co
        if i < 3:
            h *= 2
            w *= 2
            add(co, co)
    norm.append(128)
    add(128, 3)
    assert len(conv) == 40 and len(norm) == 30
    parameters = sum(ci * co * k * k + co for ci, co, k, _, _ in conv) + sum(
        2 * c for c in norm
    )
    matrix = sum(2 * batch * h * w * ci * co * k * k for ci, co, k, h, w in conv)
    valid = sum(
        2
        * batch
        * ci
        * co
        * ((h if k == 1 else 3 * h - 2) * (w if k == 1 else 3 * w - 2))
        for ci, co, k, h, w in conv
    )
    attn = 4 * batch * (height // 8 * (width // 8)) ** 2 * 512
    return parameters, matrix + attn, valid + attn


cases = []
for height, width, batch in [(8, 8, 1), (16, 24, 2), (64, 128, 1), (1024, 1024, 1)]:
    for dtype in ["bf16", "fp32"]:
        for attention in ["eager", "sdpa"]:
            r = m.calculate(
                height=height,
                width=width,
                batch=batch,
                dtype=dtype,
                attention=attention,
            )
            expected = oracle(height, width, batch)
            assert expected == (
                r["summary"]["decoder_weight_parameters"],
                r["summary"]["dense_matrix_and_conv_flops"],
                r["summary"]["nonpadding_matrix_and_conv_flops"],
            )
            assert expected[0] == 49620259
            for op in r["operators"]:
                if op["kind"] == "groupnorm":
                    b, c, h, w = r["tensors"][op["output"]]["shape"]
                    e = b * c * h * w
                    g = b * 32
                    # mean (e-g)+g; deviations e; squares e; variance
                    # (e-g)+g; eps g; normalize e; affine2e.
                    assert (
                        op["scalar_flops"]
                        == (e - g) + g + e + e + (e - g) + g + g + e + 2 * e
                    )
                if op["kind"] == "nearest2d":
                    assert op["matrix_flops"] == op["scalar_flops"] == 0
                    assert op["output_bytes"] == 4 * op["input_bytes"]
            active_peaks = []
            for i in range(len(r["operators"])):
                active = {
                    n: t["bytes"]
                    for n, t in r["tensors"].items()
                    if t["producer"] <= i <= t["last_use"]
                }
                assert sum(active.values()) == r["lifetime_events"][i]["live_bytes"]
                assert set(active) == set(r["lifetime_events"][i]["live_tensors"])
                active_peaks.append(sum(active.values()))
            assert (
                max(active_peaks) == r["summary"]["declared_tensor_boundary_peak_bytes"]
            )
            if attention == "eager":
                names = {op["name"]: op["id"] for op in r["operators"]}
                scratch = r["tensors"]["mid.attention.beta0_scratch"]
                assert (
                    scratch["producer"]
                    == scratch["last_use"]
                    == names["mid.attention.qk"]
                )
                assert (
                    "mid.attention.beta0_scratch"
                    not in r["lifetime_events"][names["mid.attention.softmax"]][
                        "live_tensors"
                    ]
                )
                if dtype == "bf16":
                    assert (
                        r["tensors"]["mid.attention.upcast"]["last_use"]
                        == names["mid.attention.softmax"]
                    )
                    assert (
                        "mid.attention.upcast"
                        not in r["lifetime_events"][
                            names["mid.attention.probability_cast"]
                        ]["live_tensors"]
                    )
            else:
                assert not any(
                    t["shape"]
                    == [
                        batch,
                        (height // 8) * (width // 8),
                        (height // 8) * (width // 8),
                    ]
                    for t in r["tensors"].values()
                )
            assert r["summary"]["actual_runtime_peak_bytes"] is None
            assert r["summary"]["conditional_weights_boundary_workspace_bytes"] is None
            cases.append(
                dict(
                    height=height,
                    width=width,
                    batch=batch,
                    dtype=dtype,
                    attention=attention,
                    peak=r["summary"]["declared_tensor_boundary_peak_bytes"],
                )
            )
a = m.calculate(height=16, width=24, workspace_bytes=12345)
assert (
    a["summary"]["conditional_weights_boundary_workspace_bytes"]
    == a["summary"]["decoder_weight_bytes"]
    + a["summary"]["declared_tensor_boundary_peak_bytes"]
    + 12345
)
for kwargs in [dict(height=8, width=8, batch=64), dict(height=8192, width=8192)]:
    large = m.calculate(**kwargs, workspace_bytes=12345)
    assert large["summary"]["layout_copy_bytes_unknown"]
    assert large["summary"]["conditional_weights_boundary_workspace_bytes"] is None
    assert any(
        row["materialized_copy_bytes"] is None
        for row in large["summary"]["upsample_contiguous_interfaces"]
    )
# Equality is legal: source uses strictly greater-than at2**31.
for kwargs in [dict(height=4096, width=4096), dict(height=8, width=8, batch=63)]:
    boundary = m.calculate(**kwargs, workspace_bytes=12345)
    assert not boundary["summary"]["layout_copy_bytes_unknown"]
    assert (
        boundary["summary"]["conditional_weights_boundary_workspace_bytes"] is not None
    )
rows = m.evidence()
for row in rows:
    data = (ROOT / row["file"]).read_bytes()
    assert (
        len(data) == row["bytes"] and hashlib.sha256(data).hexdigest() == row["sha256"]
    )
(HERE / "sources.lock.json").write_text(json.dumps(rows, indent=2) + "\n")
(HERE / "flux_vae_decode.snapshot.py").write_bytes(source.read_bytes())
(HERE / "results.json").write_text(
    json.dumps(
        dict(
            cases=cases,
            case_count=len(cases),
            candidate_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            parameters=49620259,
            official_source_sha_and_length_verified=True,
            conditional_workspace_check=True,
        ),
        indent=2,
    )
    + "\n"
)
print("Independent16cases and explicit source del boundaries passed")
