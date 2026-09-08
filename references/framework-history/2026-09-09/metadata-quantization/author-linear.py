import torch
from torch import nn
from mxq.quantize.quant_func import QuantConfig


class QuantLinear(nn.Module):

    def __init__(self, linear: nn.Linear, quant_config: QuantConfig):
        super().__init__()
        self.quant_config = quant_config
        self.register_buffer("weight", self.quant_config.weight(linear.weight.data))
        if linear.bias is not None:
            self.register_buffer("bias", linear.bias.data)

    @torch.no_grad()
    def forward(self, x):
        x_q = self.quant_config.activation(x)
        out = x_q @ self.weight.T

        bias = getattr(self, "bias", None)
        if bias is not None:
            out = out + bias
        return out
