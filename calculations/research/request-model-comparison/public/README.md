# 公共接入候选

将 `src/infra_calc/topics/request_model_comparison.py` 原样新增为公共同路径文件；tests同路径迁入后使用正常公共import与独立src bootstrap。`book.append.json`为4个扁平场景，全部字段（去除id）可直接传calculate，不含fixed execution元数据。

模块与原冻结件字节完全一致，calculate数学无修改，包含专用markdown。10项公共形式测试通过，包括场景全结果重放、四模型/逐阶段/每步/接口、K3冲突、分配与unknown报告覆盖。`verify.py`在独立候选位置注入同名公共模块后运行tests；迁入公共后不需要此注入。

bindings.json保留模块、测试、book及已审公共依赖SHA。原4场景JSON/MD继续复用上级results，未重写数学产物或改共享目录。
