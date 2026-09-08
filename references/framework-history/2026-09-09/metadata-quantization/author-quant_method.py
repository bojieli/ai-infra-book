from typing import Any, Optional

import torch
import torch.nn.functional as F

from vllm.model_executor.layers.linear import LinearBase
from vllm.model_executor.layers.linear import UnquantizedLinearMethod
from vllm.model_executor.layers.quantization import register_quantization_config
from vllm.model_executor.layers.quantization.base_config import QuantizationConfig
from mxq.quantize.quant_func import QuantConfig


class PseudoQuantLinearMethod(UnquantizedLinearMethod):
    """
    pseudo_quantization linear method.
    """

    def __init__(self, quant_config: QuantConfig) -> None:
        super().__init__()
        self.quant_config = quant_config

    def process_weights_after_loading(self, layer):
        layer.weight.data = self.quant_config.weight(layer.weight.data)

    def apply(
        self,
        layer: torch.nn.Module,
        x: torch.Tensor,
        bias: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:

        x_q = self.quant_config.activation(x)
        out = x_q @ layer.weight.data.T

        if bias is not None:
            out = out + bias

        return out


class PseudoQuantConfig(QuantizationConfig):
    """
    Pseudo quantization config.
    """

    def __init__(self, quant_config: QuantConfig) -> None:
        super().__init__()
        self.quant_config = quant_config

    def get_name(self) -> str:
        return "pseudo_quant"

    def get_supported_act_dtypes(self) -> list[torch.dtype]:
        return [torch.float16, torch.bfloat16]

    @classmethod
    def get_min_capability(cls) -> int:
        return -1

    @staticmethod
    def get_config_filenames() -> list[str]:
        return []

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "PseudoQuantConfig":
        raise RuntimeError("Shouldn't load from disk")

    def get_quant_method(
        self,
        layer: torch.nn.Module,
        prefix: str,
    ) -> Optional[PseudoQuantLinearMethod]:
        if isinstance(layer, LinearBase):
            return PseudoQuantLinearMethod(self.quant_config)
        return None


@register_quantization_config("mxfp")
class MXFPQuantConfig(PseudoQuantConfig):
    def __init__(self) -> None:
        super().__init__(
            QuantConfig(w_bit=4, w_mode="mxfp", a_bit=4, a_mode="mxfp", group_size=32)
        )

    def get_name(self):
        return "mxfp"


@register_quantization_config("m2xfp")
class MX2FPQuantConfig(PseudoQuantConfig):
    def __init__(self) -> None:
        super().__init__(
            QuantConfig(w_bit=4, w_mode="mxes", a_bit=4, a_mode="mxem", group_size=32)
        )

    def get_name(self):
        return "m2xfp"
