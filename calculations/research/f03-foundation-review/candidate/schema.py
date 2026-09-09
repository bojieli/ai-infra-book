"""Small explicit accounting records shared by all model adapters."""
from dataclasses import dataclass, field, asdict
from math import prod

from .units import positive_int


@dataclass(frozen=True)
class Scenario:
    batch: int = 1
    history: int = 0
    tokens: int = 8192
    output_head: str = "last"
    weight_bytes: int = 2
    activation_bytes: int = 2
    kv_bytes: int = 2
    score_bytes: int = 4

    def __post_init__(self):
        for name in ("batch", "tokens", "weight_bytes", "activation_bytes", "kv_bytes", "score_bytes"):
            positive_int(getattr(self, name), name)
        positive_int(self.history, "history", allow_zero=True)
        if self.output_head not in ("last", "all", "none"):
            raise ValueError("output_head must be last, all or none")

    @property
    def rows(self) -> int:
        return self.batch * self.tokens

    @property
    def pairs(self) -> int:
        """Valid causal query/key position pairs, including the current token."""
        return self.batch * (self.tokens * self.history + self.tokens * (self.tokens + 1) // 2)

    @property
    def rectangular_pairs(self) -> int:
        return self.rows * (self.history + self.tokens)

    @property
    def head_rows(self) -> int:
        return {"none": 0, "last": self.batch, "all": self.rows}[self.output_head]


@dataclass(frozen=True)
class Weight:
    name: str
    shape: tuple[int, ...]
    copies: int = 1
    note: str = ""

    def __post_init__(self):
        for dimension in self.shape:
            positive_int(dimension, "weight shape dimension")
        positive_int(self.copies, "weight copies", allow_zero=True)

    @property
    def parameters(self) -> int:
        return prod(self.shape) * self.copies

    def record(self, bytes_per_element: int) -> dict:
        positive_int(bytes_per_element, "bytes_per_element")
        return {**asdict(self), "parameters": self.parameters,
                "resident_bytes": self.parameters * bytes_per_element}


@dataclass
class Operator:
    name: str
    category: str
    shapes: dict
    repeats: int = 1
    matrix_flops: int = 0
    scalar_flops: int = 0
    special_ops: dict = field(default_factory=dict)
    weight_read_bytes: int = 0
    activation_read_bytes: int = 0
    activation_write_bytes: int = 0
    notes: str = ""

    def __post_init__(self):
        for field_name in ("repeats", "matrix_flops", "scalar_flops", "weight_read_bytes",
                           "activation_read_bytes", "activation_write_bytes"):
            positive_int(getattr(self, field_name), field_name, allow_zero=True)
        for name, count in self.special_ops.items():
            positive_int(count, "special operation " + name, allow_zero=True)

    def record(self) -> dict:
        """Costs are per occurrence; repeats explicitly scales the total."""
        self.__post_init__()
        return asdict(self)


def linear(name: str, rows: int, inputs: int, outputs: int,
           scenario: Scenario, *, repeats: int = 1, note: str = "") -> Operator:
    positive_int(rows, "rows", allow_zero=True)
    positive_int(inputs, "inputs")
    positive_int(outputs, "outputs")
    positive_int(repeats, "repeats", allow_zero=True)
    return Operator(
        name=name, category="linear", repeats=repeats,
        shapes={"input": [rows, inputs], "weight_math": [inputs, outputs],
                "weight_storage": [outputs, inputs], "output": [rows, outputs]},
        matrix_flops=2 * rows * inputs * outputs,
        weight_read_bytes=inputs * outputs * scenario.weight_bytes,
        activation_read_bytes=rows * inputs * scenario.activation_bytes,
        activation_write_bytes=rows * outputs * scenario.activation_bytes,
        notes=note or "独立 GEMM：权重与输入各读一次、输出写一次的操作数载荷；不预测 tile 重读。",
    )
