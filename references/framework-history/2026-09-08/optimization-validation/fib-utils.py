"""Utility functions for kernel evaluation.

This module provides helper functions for allocating output tensors and
normalizing kernel results during evaluation.
"""

from typing import Any, List

import torch

from flashinfer_bench.data import Definition


def allocate_outputs(definition: Definition, inputs: List[Any], device: str) -> List[torch.Tensor]:
    """Allocate output tensors based on definition and input shapes.

    Infers variable axis values from input tensor shapes and allocates
    empty output tensors with the correct shapes and dtypes.

    Parameters
    ----------
    definition : Definition
        The kernel definition specifying output tensor specs.
    inputs : List[Any]
        List of input values (tensors or scalars) in definition order.
    device : str
        The device to allocate tensors on (e.g., "cuda:0").

    Returns
    -------
    List[torch.Tensor]
        List of allocated (uninitialized) output tensors in definition order.
    """
    var_values = definition.get_axes_values_from_inputs(inputs)
    output_shapes = definition.get_output_shapes(var_values)

    dtypes = definition.torch_output_dtypes
    return [
        torch.empty(shape, dtype=dtype, device=device)
        for shape, dtype in zip(output_shapes, dtypes)
    ]


def normalize_result(definition: Definition, result: Any, device: str) -> List[torch.Tensor]:
    """Normalize a value-returning kernel result to a tensor list.

    Converts various return types (scalar, tensor, tuple, list) to a
    standardized list of tensors matching the definition's output order.

    Parameters
    ----------
    definition : Definition
        The kernel definition specifying expected outputs.
    result : Any
        The kernel return value. Can be:
        - A single value (int, float, bool, or torch.Tensor)
        - A tuple or list of values
    device : str
        The device to place resulting tensors on.

    Returns
    -------
    List[torch.Tensor]
        List of output tensors in definition order.

    Raises
    ------
    ValueError
        If the number of returned values doesn't match the expected outputs.
    """
    dtypes = definition.torch_output_dtypes
    n_outputs = len(dtypes)

    def to_tensor(v: Any, dtype: torch.dtype) -> torch.Tensor:
        if isinstance(v, torch.Tensor):
            return v.to(device) if str(v.device) != device else v
        return torch.tensor(v, dtype=dtype, device=device)

    if isinstance(result, (tuple, list)):
        if len(result) != n_outputs:
            raise ValueError(
                f"Tuple/list has {len(result)} elements but {n_outputs} outputs expected"
            )
        return [to_tensor(v, dtypes[i]) for i, v in enumerate(result)]

    # Single value: tensor, int, float, bool
    if n_outputs != 1:
        raise ValueError(f"Single value returned but {n_outputs} outputs expected")

    return [to_tensor(result, dtypes[0])]
