import torch
import torch.nn as nn
from tqdm import tqdm
import gc
from ..utils.module import set_op_by_name
from mxq.quantize.quant_func import QuantConfig


@torch.no_grad()
def make_quant_linear(model: nn.Module, quant_config: QuantConfig):
    from .pre_quant import get_blocks, get_named_linears

    layers = get_blocks(model)
    for i in tqdm(range(len(layers)), desc=" make quant linear..."):
        layer = layers[i]
        named_linears = get_named_linears(layer)
        for name, module in named_linears.items():
            # module.cuda()
            from .linear import QuantLinear

            q_linear = QuantLinear(module, quant_config)
            q_linear.to(next(layer.parameters()).device)
            set_op_by_name(layer, name, q_linear)
            
            del module
            torch.cuda.empty_cache()
            gc.collect()
