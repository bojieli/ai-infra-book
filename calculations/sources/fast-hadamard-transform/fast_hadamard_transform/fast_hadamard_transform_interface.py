# Copyright (c) 2023, Tri Dao.

import math
try:
    from scipy.linalg import hadamard
except ImportError:
    hadamard = None

import torch
import torch.nn.functional as F


import fast_hadamard_transform_cuda


class HadamardTransformFn(torch.autograd.Function):

    @staticmethod
    def forward(ctx, x, scale=1.0):
        ctx._hadamard_transform_scale = scale
        return fast_hadamard_transform_cuda.fast_hadamard_transform(x, scale)

    @staticmethod
    def backward(ctx, dout):
        # The Hadamard transform matrix is symmetric, so in the backward pass we multiply by its
        # transpose, which is itself.
        return fast_hadamard_transform_cuda.fast_hadamard_transform(dout, ctx._hadamard_transform_scale), None


def hadamard_transform(x, scale=1.0):
    """
    Arguments:
        x: (..., dim)
        scale: float. Multiply the output by this number.
    Returns:
        out: (..., dim)

    Multiply each row of x by the Hadamard transform matrix.
    Equivalent to F.linear(x, torch.tensor(scipy.linalg.hadamard(dim))) * scale.
    If dim is not a power of 2, we implicitly pad x with zero so that dim is the next power of 2.
    """
    return HadamardTransformFn.apply(x, scale)


class HadamardTransform12NFn(torch.autograd.Function):

    @staticmethod
    def forward(ctx, x, scale=1.0):
        ctx._hadamard_transform_scale = scale
        return fast_hadamard_transform_cuda.fast_hadamard_transform_12N(x, scale)

    @staticmethod
    def backward(ctx, dout):
        # The Hadamard transform matrix is symmetric, so in the backward pass we multiply by its
        # transpose, which is itself.
        return fast_hadamard_transform_cuda.fast_hadamard_transform_12N(dout, ctx._hadamard_transform_scale), None
    

def hadamard_transform_12N(x, scale=1.0):
    """
    Arguments:
        x: (..., dim)
        scale: float. Multiply the output by this number.
    Returns:
        out: (..., dim)

    Multiply each row of x by the Hadamard transform matrix, where dim = 12 * power of 2.
    If dim is not 12 * a power of 2, we implicitly pad x with zero so that dim is 12 * the next power of 2.
    """
    return HadamardTransform12NFn.apply(x, scale)



class HadamardTransform20NFn(torch.autograd.Function):

    @staticmethod
    def forward(ctx, x, scale=1.0):
        ctx._hadamard_transform_scale = scale
        return fast_hadamard_transform_cuda.fast_hadamard_transform_20N(x, scale)

    @staticmethod
    def backward(ctx, dout):
        # The Hadamard transform matrix is symmetric, so in the backward pass we multiply by its
        # transpose, which is itself.
        return fast_hadamard_transform_cuda.fast_hadamard_transform_20N(dout, ctx._hadamard_transform_scale), None


def hadamard_transform_20N(x, scale=1.0):
    """
    Arguments:
        x: (..., dim)
        scale: float. Multiply the output by this number.
    Returns:
        out: (..., dim)

    Multiply each row of x by the Hadamard transform matrix, where dim = 20 * power of 2.
    If dim is not 20 * a power of 2, we implicitly pad x with zero so that dim is 20 * the next power of 2.
    """
    return HadamardTransform20NFn.apply(x, scale)


class HadamardTransform28NFn(torch.autograd.Function):

    @staticmethod
    def forward(ctx, x, scale=1.0):
        ctx._hadamard_transform_scale = scale
        return fast_hadamard_transform_cuda.fast_hadamard_transform_28N(x, scale)

    @staticmethod
    def backward(ctx, dout):
        # The Hadamard transform matrix is symmetric, so in the backward pass we multiply by its
        # transpose, which is itself.
        return fast_hadamard_transform_cuda.fast_hadamard_transform_28N(dout, ctx._hadamard_transform_scale), None


def hadamard_transform_28N(x, scale=1.0):
    """
    Arguments:
        x: (..., dim)
        scale: float. Multiply the output by this number.
    Returns:
        out: (..., dim)

    Multiply each row of x by the Hadamard transform matrix, where dim = 28 * power of 2.
    If dim is not 28 * a power of 2, we implicitly pad x with zero so that dim is 28 * the next power of 2.
    """
    return HadamardTransform28NFn.apply(x, scale)


class HadamardTransform40NFn(torch.autograd.Function):

    @staticmethod
    def forward(ctx, x, scale=1.0):
        ctx._hadamard_transform_scale = scale
        return fast_hadamard_transform_cuda.fast_hadamard_transform_40N(x, scale)

    @staticmethod
    def backward(ctx, dout):
        # The Hadamard transform matrix is symmetric, so in the backward pass we multiply by its
        # transpose, which is itself.
        return fast_hadamard_transform_cuda.fast_hadamard_transform_40N(dout, ctx._hadamard_transform_scale), None

def hadamard_transform_40N(x, scale=1.0):
    """
    Arguments:
        x: (..., dim)
        scale: float. Multiply the output by this number.
    Returns:
        out: (..., dim)

    Multiply each row of x by the Hadamard transform matrix, where dim = 40 * power of 2.
    If dim is not 40 * a power of 2, we implicitly pad x with zero so that dim is 40 * the next power of 2.
    """
    return HadamardTransform40NFn.apply(x, scale)

def hadamard_transform_ref(x, scale=1.0):
    """
    x: (..., dim)
    out: (..., dim)
    """
    if hadamard is None:
        raise ImportError("Please install scipy")
    x_shape = x.shape
    dim = x.shape[-1]
    x = x.reshape(-1, dim)
    log_dim = math.ceil(math.log2(dim))
    dim_padded = 2 ** log_dim
    if dim != dim_padded:
        x = F.pad(x, (0, dim_padded - dim))
    out = F.linear(x, torch.tensor(hadamard(dim_padded, dtype=float), dtype=x.dtype, device=x.device))
    out = out * scale
    return out[..., :dim].reshape(*x_shape)
