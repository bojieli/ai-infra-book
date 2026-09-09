"""Run selected pinned official classes, with only dependency/array containers stubbed."""

import ast, enum, json, logging, warnings
from pathlib import Path
import numpy as np
import torch

HERE = Path(__file__).resolve().parent


class PaddingStrategy(enum.Enum):
    LONGEST = "longest"
    MAX_LENGTH = "max_length"
    DO_NOT_PAD = "do_not_pad"


class BatchFeature(dict):
    def __init__(self, data=None, tensor_type=None):
        super().__init__(data or {})
        if tensor_type:
            self.convert_to_tensors(tensor_type)

    def convert_to_tensors(self, tensor_type):
        for k, v in self.items():
            if tensor_type == "np":
                self[k] = np.asarray(v)
            elif tensor_type == "pt":
                self[k] = torch.from_numpy(np.asarray(v))
            else:
                raise ValueError(tensor_type)
        return self


class FeatureExtractionMixin:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def load():
    namespace = dict(
        np=np,
        torch=torch,
        warnings=warnings,
        logger=logging.getLogger("pinned"),
        PaddingStrategy=PaddingStrategy,
        BatchFeature=BatchFeature,
        FeatureExtractionMixin=FeatureExtractionMixin,
        is_torch_available=lambda: True,
        is_torch_tensor=lambda x: isinstance(x, torch.Tensor),
        is_tf_tensor=lambda x: False,
        to_numpy=np.asarray,
    )

    def select(file, names):
        tree = ast.parse((HERE / "sources" / file).read_text())
        nodes = [
            n
            for n in tree.body
            if isinstance(n, (ast.ClassDef, ast.FunctionDef)) and n.name in names
        ]
        body = [
            ast.ImportFrom(
                module="__future__", names=[ast.alias(name="annotations")], level=0
            )
        ] + nodes
        exec(
            compile(
                ast.fix_missing_locations(ast.Module(body=body, type_ignores=[])),
                file,
                "exec",
            ),
            namespace,
        )

    select(
        "audio_utils.py",
        {
            "hertz_to_mel",
            "mel_to_hertz",
            "_create_triangular_filter_bank",
            "mel_filter_bank",
        },
    )
    select("feature_extraction_sequence_utils.py", {"SequenceFeatureExtractor"})
    select("feature_extraction_whisper.py", {"WhisperFeatureExtractor"})
    config = json.loads((HERE / "sources/preprocessor_config.json").read_text())
    return namespace["WhisperFeatureExtractor"](**config)


if __name__ == "__main__":
    e = load()
    x = e(
        np.zeros(16000, dtype=np.float32),
        sampling_rate=16000,
        padding=True,
        return_attention_mask=True,
        return_tensors="np",
    )
    print(
        e.n_samples,
        e.nb_max_frames,
        e.chunk_length,
        {k: (v.shape, str(v.dtype)) for k, v in x.items()},
    )
