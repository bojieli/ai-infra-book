# request_model_comparison 输出键序确定性修复

只修改两处 dict comprehension：将 `set(...) | set(...)` 遍历包在 `sorted(...)` 中。位置是 Qwen decode 的 special_slope，以及每个 decode step 的 special_ops。没有改变键值、公式、输入或其他代码格式。

`fix.patch` 可直接用于公共模块；`guard.json` 给出合入前后SHA。完整候选在 src/infra_calc/topics/request_model_comparison.py。公共文件未修改。

独立进程验证使用 PYTHONHASHSEED=0/1/7/42/123/987654；同一四模型prefix-boundary输入，旧公共模块和候选各运行6次。JSON采用indent=2/ensure_ascii=False/allow_nan=False，**不使用sort_keys**，因此确实检验模块构造顺序。

结果：旧模块6个不同字节hash；候选全部同一字节hash。12个解析对象全部相等，并与预先存在的冻结 results/request-four-models-prefix-boundary.json 完全相等。输入同时执行Qwen和K3多个decode步骤，两处修复均被覆盖。

复现命令：

```sh
/Users/boj/miniconda3/bin/python calculations/research/request-comparison-determinism/verify.py
```

详细seed/hash、冻结原件hash在validation.json；stable-result.json保存一个稳定结果。仅独立research文件有写入。
