import sympy as sp

from .utils import *

class ReductionProcessor:
    """处理归约操作的分解和处理"""

    def __init__(self, configs: list[ReductionConfig], x_map: dict, y_map: dict, c_map: dict):
        self.configs = configs
        self.x_map = x_map
        self.y_map = y_map
        self.c_map = c_map
        self.exprs = []
        self.y_syms = dict()
        self.x_syms = dict()
        self.c_syms = dict()
        self.fixed_x_syms = dict()
        self.fixed_y_syms = dict()
        self.prev_y_syms = dict()
        self.op_params = {}  # 存储可能的额外参数 {reduce_target: {...}}
        self._parse_config()

    def process_reductions(self) -> tuple[list[tuple[BMat, BMat, str | None]], list[tuple[BMat | None, BMat | None, BMat | None]]]:
        """
        处理所有归约操作

        Returns:
            tuple: (exprs_list, reduce_funcs_list)
                - exprs_list: 每个配置的表达式列表 [(target, F_expr, reduce_op), ...]
                - reduce_funcs_list: 每个配置的分解函数列表 [(Gx, Hy, prev_Hy), ...]
        """
        exprs = []
        reduce_funcs = []
        for config,F_expr in zip(self.configs, self.exprs):
            terms, components = self._decompose_single(config, F_expr)
            exprs.extend(terms)
            reduce_funcs.extend(components)
        return exprs, reduce_funcs

    def _decompose_single(self, config: ReductionConfig, F_expr: BMat) -> tuple[list[tuple[BMat, BMat, str | None]], list[tuple[BMat | None, BMat | None, BMat | None]]]:
        reduce_op = self._get_reduce_function(config.reduce_op, F_expr)

        if reduce_op in ("reduce_sum", "gemm"):
            # TODO: 支持 sum(A+B) 分拆为 sum(A) + sum(B)
            F_exprs = [F_expr]
        elif reduce_op in ("reduce_max", "reduce_topk"):
            F_exprs = [F_expr]
        else:
            raise NotImplementedError(f"Unsupported op type {reduce_op}")

        results = [self._split_gxhy(F_expr, config) for F_expr in F_exprs]

        raw_target = self.y_syms[config.reduce_target]
        targets = (
            [
                BMat(
                    sp.MatrixSymbol(
                        f"{config.reduce_target}_{i}", *raw_target.shape
                    )
                )
                for i in range(len(F_exprs))
            ]
            if len(F_exprs) > 1
            else [raw_target]
        )

        # 构建表达式列表
        exprs = [(target, F_expr, reduce_op) for target, F_expr in zip(targets, F_exprs)]

        if len(F_exprs) > 1:
            temp_expr = targets[0]
            for t in targets[1:]:
                temp_expr = temp_expr + t
            exprs.append((raw_target, temp_expr, None))
            results.append((None, None, None))

        return exprs, results

    def _split_gxhy(self, Ft_expr: BMat, config: ReductionConfig) -> tuple[BMat, BMat, BMat]:
        """
        将表达式分解为 g(x) * h(y) 或 g(x) + h(y) 的形式

        Args:
            term: 待分解的 BMat 表达式

        Returns:
            tuple: (G_expr, H_expr, prev_H_expr)
                - G_expr: g(x) 表达式
                - H_expr: h(y) 表达式
                - prev_H_expr: h(prev_y) 表达式
        """
        reduce_op = self._get_reduce_function(config.reduce_op, Ft_expr)

        F0_expr = BMat(Ft_expr.subs(self.fixed_x_syms | self.fixed_y_syms))
        G_expr = BMat(Ft_expr.subs(self.fixed_y_syms))
        H_expr = BMat(Ft_expr.subs(self.fixed_x_syms))

        # 根据归约操作选择验证函数
        if reduce_op in ("reduce_sum", "gemm"):
            eval_func = (Ft_expr * F0_expr) - (G_expr * H_expr)
        elif reduce_op in ("reduce_max", "reduce_topk"):
            eval_func = (Ft_expr + F0_expr) - (G_expr + H_expr)
        else:
            raise NotImplementedError(f"Unsupported op type {reduce_op}")

        for i in range(eval_func.shape[0]):
            for j in range(eval_func.shape[1]):
                if sp.simplify(eval_func[i, j], force=True) != 0:
                    raise ValueError(f"Cannot be decomposed {Ft_expr}")

        # 消除固定后缀并计算 prev_H
        G_expr = G_expr.eliminate_fixed_suffix(False)
        H_expr = (H_expr / F0_expr).eliminate_fixed_suffix(False)
        prev_H_expr = H_expr.subs(self.prev_y_syms)

        return (G_expr, H_expr, prev_H_expr)

    def _parse_config(self):
        local = {"BMat": BMat, "max": sp.Max, "abs": sp.Abs, "fabs": sp.Abs, "topk": TopK} # 这里虽然写了topk,但实际并没有用
        for c in self.c_map.keys():
            self.c_syms[c] = sp.Symbol(c, real=True, positive=True)
        for x in self.x_map.keys():
            self.x_syms[x] = BMat(sp.MatrixSymbol(x, BMat_M, BMat_N))
            self.fixed_x_syms[self.x_syms[x]] = BMat(sp.MatrixSymbol(f"{x}_fixed", BMat_M, BMat_N))
        for config in self.configs:
            # 注: topk的reduce_func在这里是x0,在当前的case里是能work的
            F_expr = BMat(sp.sympify(config.reduce_func, locals=local | self.x_syms | self.y_syms | self.c_syms))
            if self.y_syms.get(config.reduce_target, None) is None:
                shape = (BMat_M, BMat_N) if config.reduce_op == '+' and isinstance(strip_bmat(F_expr), sp.MatMul) else (BMat_M, 1)
                self.y_syms[config.reduce_target] = BMat(sp.MatrixSymbol(config.reduce_target, *(shape)))
                self.fixed_y_syms[self.y_syms[config.reduce_target]] = BMat(sp.MatrixSymbol(f"{config.reduce_target}_fixed", *(shape)))
                self.prev_y_syms[self.y_syms[config.reduce_target]] = BMat(sp.MatrixSymbol(f"prev_{config.reduce_target}", *(shape)))
            self.exprs.append(F_expr)

    def _get_reduce_function(self, reduce_op, F_expr):
        func_map = {
            "+": "gemm" if isinstance(strip_bmat(F_expr), sp.MatMul) else "reduce_sum",
            "max": "reduce_max",
            "topk": "reduce_topk",
        }
        return func_map[reduce_op.lower()]

if __name__ == "__main__":
    A = BMat(sp.MatrixSymbol("A", 2, 2))
    B = BMat(sp.MatrixSymbol("B", 2, 2))
    expr = sp.sympify("max(A, c0)", locals={"A": A, "B": B, "max": sp.Max, "abs": sp.Abs})
    print(expr.expr)
