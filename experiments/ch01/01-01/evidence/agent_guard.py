"""Restrict model candidates to the kernel interface; not a security sandbox."""
import ast

ATTRS = set('jit constexpr program_id arange load store float32 bfloat16 float16 int32 exp exp2 sigmoid where minimum maximum abs sum max multiple_of max_contiguous cdiv next_power_of_2 empty empty_like shape device dtype numel to float contiguous reshape view stride sigmoid silu nn functional zeros full sqrt rsqrt log tanh'.split())

def validate_code(code):
    tree = ast.parse(code)
    for node in tree.body:
        if not isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef)):
            raise ValueError('Only imports and function definitions at module level')
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(a.name not in {'torch', 'triton', 'triton.language'} for a in node.names):
                raise ValueError('Only torch/triton imports')
        if isinstance(node, ast.ImportFrom):
            raise ValueError('Use import torch, import triton, import triton.language as tl')
        if isinstance(node, (ast.ClassDef, ast.Global, ast.Nonlocal, ast.With, ast.AsyncWith)):
            raise ValueError('Unsupported syntax')
        if isinstance(node, ast.Name) and (node.id.startswith('__') or node.id in {'eval','exec','open','compile','getattr','setattr','globals','locals','vars','input','breakpoint','help','type'}):
            raise ValueError('Unsupported name: '+node.id)
        if isinstance(node, ast.Attribute) and node.attr not in ATTRS:
            raise ValueError('Unsupported attribute: '+node.attr)
    if not any(isinstance(n,ast.FunctionDef) and n.name=='run' for n in tree.body):
        raise ValueError('Must define run(x)')
