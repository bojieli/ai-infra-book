"""Replay fixed official function AST and independent integer resize/layout oracle."""

import ast
import functools
import hashlib
import json
import math
from pathlib import Path
import platform
from typing import Any
import numpy as np
import torch
import torchvision
from torchvision.transforms.v2.functional import _geometry, _misc
from torchvision.transforms.v2 import functional as tvF
from transformers.image_utils import SizeDict, PILImageResampling
from transformers.image_processing_base import BatchFeature
from vision_preprocess import axis_weights, calculate

HERE = Path(__file__).resolve().parent


def functions(file, names, cls=None):
    tree = ast.parse((HERE / file).read_text())
    body = tree.body
    if cls:
        body = next(
            n for n in body if isinstance(n, ast.ClassDef) and n.name == cls
        ).body
    selected = [n for n in body if isinstance(n, ast.FunctionDef) and n.name in names]
    namespace = dict(
        torch=torch,
        math=math,
        np=np,
        tvF=tvF,
        lru_cache=functools.lru_cache,
        SizeDict=SizeDict,
        BatchFeature=BatchFeature,
        PILImageResampling=PILImageResampling,
        pil_torch_interpolation_mapping={
            PILImageResampling.BICUBIC: tvF.InterpolationMode.BICUBIC
        },
        is_torchdynamo_compiling=lambda: False,
    )
    module = ast.Module(
        body=[
            ast.ImportFrom(
                module="__future__", names=[ast.alias(name="annotations")], level=0
            )
        ]
        + selected,
        type_ignores=[],
    )
    exec(
        compile(ast.fix_missing_locations(module), str(HERE / file), "exec"), namespace
    )
    return namespace


base_funcs = functions(
    "image_processing_backends.py",
    [
        "resize",
        "normalize",
        "_fuse_mean_std_and_rescale_factor",
        "rescale_and_normalize",
    ],
    cls="TorchvisionBackend",
)


class Base:
    pass


for name in [
    "resize",
    "normalize",
    "_fuse_mean_std_and_rescale_factor",
    "rescale_and_normalize",
]:
    setattr(Base, name, base_funcs[name])


class Processor(Base):
    pass


image_funcs = functions(
    "image_processing_qwen2_vl.py",
    ["resize", "patchify", "_preprocess"],
    cls="Qwen2VLImageProcessor",
)
# Recompile methods inside their own class so zero-argument super() retains its class cell.
source = ast.parse((HERE / "image_processing_qwen2_vl.py").read_text())
old = next(
    n
    for n in source.body
    if isinstance(n, ast.ClassDef) and n.name == "Qwen2VLImageProcessor"
)
methods = [
    n
    for n in old.body
    if isinstance(n, ast.FunctionDef)
    and n.name in ("resize", "patchify", "_preprocess")
]
klass = ast.ClassDef(
    name="Processor",
    bases=[ast.Name(id="Base", ctx=ast.Load())],
    keywords=[],
    body=methods,
    decorator_list=[],
)
groups = functions(
    "image_transforms.py", ["group_images_by_shape", "reorder_images", "_iterate_items"]
)
smart = functions("image_processing_qwen2_vl.py", ["smart_resize"])["smart_resize"]
namespace = dict(
    image_funcs,
    Base=Base,
    smart_resize=smart,
    group_images_by_shape=groups["group_images_by_shape"],
    reorder_images=groups["reorder_images"],
)
exec(
    compile(
        ast.fix_missing_locations(
            ast.Module(
                body=[
                    ast.ImportFrom(
                        module="__future__",
                        names=[ast.alias(name="annotations")],
                        level=0,
                    ),
                    klass,
                ],
                type_ignores=[],
            )
        ),
        str(HERE / "image_processing_qwen2_vl.py"),
        "exec",
    ),
    namespace,
)
Processor = namespace["Processor"]


def independent_resize(image, height, width):
    out = image
    for dimension, size in [(1, width), (0, height)]:
        if out.shape[dimension] == size:
            continue
        weights = axis_weights(out.shape[dimension], size)
        moved = np.moveaxis(out, dimension, 0)
        result = np.empty((size,) + moved.shape[1:], dtype=np.uint8)
        for i, row in enumerate(weights["ranges"]):
            k = row["count"]
            values = moved[row["start"] : row["start"] + k].astype(np.int64)
            w = np.array(row["int16_weights"][:k], dtype=np.int64).reshape(
                (k,) + (1,) * (values.ndim - 1)
            )
            accum = (values * w).sum(axis=0) + (
                1 << (weights["weights_precision_bits"] - 1)
            )
            result[i] = np.clip(
                accum >> weights["weights_precision_bits"], 0, 255
            ).astype(np.uint8)
        out = np.moveaxis(result, 0, dimension)
    return out


def check():
    if (
        torch.__version__.split("+")[0] != "2.7.0"
        or torch.backends.cpu.get_cpu_capability() != "NO AVX"
    ):
        raise RuntimeError(
            "Numerical proof requires pinned torch2.7 generic non-AVX CPU"
        )
    assert torchvision.__version__.split("+")[0] == "0.22.0"
    assert torch.version.git_version == "134179474539648ba7dee1317959529fbd0e7f89"
    for name, module in [("_geometry.py", _geometry), ("_misc.py", _misc)]:
        assert (
            hashlib.sha256((HERE / name).read_bytes()).digest()
            == hashlib.sha256(Path(module.__file__).read_bytes()).digest()
        )
    rng = np.random.default_rng(7101)
    cases = []
    for h, w in [(32, 32), (257, 385), (256, 256), (64, 256), (317, 281)]:
        image = rng.integers(0, 256, size=(h, w, 3), dtype=np.uint8)
        budget = calculate(h, w)
        rh, rw = budget["summary"]["resized_height"], budget["summary"]["resized_width"]
        chw = torch.from_numpy(image).permute(2, 0, 1).contiguous()
        official_resize = tvF.resize(
            chw, [rh, rw], interpolation=tvF.InterpolationMode.BICUBIC, antialias=True
        )
        oracle = independent_resize(image, rh, rw)
        assert np.array_equal(oracle, official_resize.permute(1, 2, 0).numpy())
        processor = Processor()
        actual = processor._preprocess(
            [chw],
            do_resize=True,
            size=SizeDict(shortest_edge=65536, longest_edge=16777216),
            resample=PILImageResampling.BICUBIC,
            do_rescale=True,
            rescale_factor=1 / 255,
            do_normalize=True,
            image_mean=(0.5, 0.5, 0.5),
            image_std=(0.5, 0.5, 0.5),
            patch_size=16,
            temporal_patch_size=2,
            merge_size=2,
            disable_grouping=True,
            return_tensors="pt",
        )
        norm = (oracle.astype(np.float32) - np.float32(127.5)) / np.float32(127.5)
        # Independent coordinate loops implement merge-major ordering, channels, time then patch pixels.
        rows = []
        for gy in range(rh // 32):
            for gx in range(rw // 32):
                for my in range(2):
                    for mx in range(2):
                        tile = norm[
                            (gy * 2 + my) * 16 : (gy * 2 + my + 1) * 16,
                            (gx * 2 + mx) * 16 : (gx * 2 + mx + 1) * 16,
                        ]
                        rows.append(
                            np.stack([tile.transpose(2, 0, 1)] * 2, axis=1).reshape(-1)
                        )
        expected = np.stack(rows)
        assert np.array_equal(expected, actual["pixel_values"].numpy())
        assert actual["image_grid_thw"].tolist() == [
            budget["summary"]["image_grid_thw"]
        ]
        assert (
            list(actual["pixel_values"].shape)
            == budget["summary"]["pixel_values_shape"]
        )
        cases.append(
            dict(
                input=[h, w],
                resized=[rh, rw],
                resize_uint8_exact=True,
                official_selected_methods_patch_values_exact=True,
                pixel_values_shape=list(expected.shape),
                max_abs_error=float(
                    np.max(abs(expected - actual["pixel_values"].numpy()))
                ),
            )
        )
    resize_kernel_cases = []
    for h, w, rh, rw in [
        (64, 80, 17, 23),
        (257, 385, 64, 80),
        (128, 64, 32, 64),
        (64, 128, 64, 32),
    ]:
        image = rng.integers(0, 256, size=(h, w, 3), dtype=np.uint8)
        expected = independent_resize(image, rh, rw)
        actual = (
            tvF.resize(
                torch.from_numpy(image).permute(2, 0, 1).contiguous(),
                [rh, rw],
                interpolation=tvF.InterpolationMode.BICUBIC,
                antialias=True,
            )
            .permute(1, 2, 0)
            .numpy()
        )
        assert np.array_equal(expected, actual)
        resize_kernel_cases.append(
            dict(
                input=[h, w],
                output=[rh, rw],
                uint8_exact=True,
                scope="kernel-only geometry to test large antialias support and single-axis skip",
            )
        )
    # Geometry boundary, including max-area reduction, without allocating huge images.
    for h, w in [(4608, 4608), (4096, 4128), (1, 200), (1, 201), (640, 640)]:
        try:
            expected = smart(h, w, 32, 65536, 16777216)
        except ValueError:
            try:
                calculate(h, w)
            except ValueError:
                continue
            raise AssertionError("Expected aspect rejection")
        summary = calculate(h, w)["summary"]
        assert expected == (summary["resized_height"], summary["resized_width"])
    result = dict(
        cases=cases,
        resize_kernel_cases=resize_kernel_cases,
        geometry_boundary_cases=5,
        torch=torch.__version__,
        torchvision=torchvision.__version__,
        torchvision_installed_files_match_locked_official=True,
        torch_git_version=torch.version.git_version,
        cpu_capability=torch.backends.cpu.get_cpu_capability(),
        machine=platform.machine(),
        proof_scope="Verbatim AST of locked selected official methods + installed pinned torchvision/PyTorch kernel; independent uint8 separable integer resize and coordinate-loop patch oracle. Not a full Transformers load/decode or performance benchmark.",
        source_sha256={
            f: hashlib.sha256((HERE / f).read_bytes()).hexdigest()
            for f in [
                "image_processing_qwen2_vl.py",
                "image_processing_backends.py",
                "image_transforms.py",
                "UpSampleKernel.cpp",
            ]
        },
    )
    (HERE / "numeric-verification.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    check()
