# Fast Hadamard Transform in CUDA, with a PyTorch interface

Features:
- Support fp32, fp16, bf16, for dimension up to 32768.
- Implicitly pad with zeros if dimension is not a power of 2.


## Installation
```
git clone https://github.com/Dao-AILab/fast-hadamard-transform.git fast-hadamard-transform
cd fast-hadamard-transform
pip install -v .
```

## How to use

```
from fast_hadamard_transform import hadamard_transform
```

```
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
```

## Speed

Benchmarked on A100, for not too small batch size, compared to memcpy
(torch.clone), which is a lower bound for the time taken as we'd need to read
inputs from GPU memory and write output to GPU memory anyway.

| Data type |  Dimension | Time taken vs memcpy |
| --------- | ---------- | -------------------- |
| fp16/bf16 |     <= 512 |                 1.0x |
|           | 512 - 8192 |              <= 1.2x |
|           |      16384 |                 1.3x |
|           |      32768 |                 1.8x |
| fp32      |    <= 8192 |                 1.0x |
|           |      16384 |                 1.1x |
|           |      32768 |                 1.2x |
