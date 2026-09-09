# 图2-8候选：原Chat/Agent记录、reasoning与条件KV

六面板分别展示4原Chat调用、4个thinking-on Agent轮次的输入/缓存/返回ID，Agent应用时间线、reasoning结束marker边界、独立毫秒尺度的工具时间与声明工具等待期间保留的BF16逻辑KV。所有单次值均显示，不只绘制均值。

先调用现有来源校验与Agent/Chat计算再取数据。首Agent轮1200返回ID、finish_reason=length，未出现reasoning结束marker，灰色斜线标为boundary not observed；不把全部输出归类为reasoning。其他轮按首个marker计数（包含delimiter）和首次达到该计数的流事件画标记，不当作GPU阶段结束时间。只有应用调用与工具起止是记录值；KV来自显式保留策略，不是观测页寿命。工具耗时0.063/3.335/74.244/0.061ms在总约76.5秒时间线上难以辨别，单独面板标数值。

已生成PNG/SVG/PDF和data.json，根实际打开PNG核对布局及未观测标记。2项数据测试通过，核原输入/命中/输出守恒、KV闭式、时间顺序与marker缺失边界。当前为绘图候选，尚需独立数据/图形审核、来源/产物manifest以及公共图命令与正文注册；T10/图2-8不提前勾选。

根后续审核：补入此前data只列Agent而遗漏的Chat来源引用；加入turn数量/身份校验，reasoning面板明确三类图例，固定SVG hash salt并移除SVG/PDF时间戳元数据。已重新生成三格式并实际查看PNG，图例不遮数据。manifest覆盖来源、计算Python依赖与四产物（含data）。根独立check.py直接读取原始两组记录，核全部时间字段、marker/首个对应输出事件、逐轮KV、Chat输入/输出/命中及所有绑定，共274检查通过；2数据tests通过。此为独立数据公式与hash审核及根视觉检查，不是另一个审核者签名。公共verify的完整输入集合防绕过、图注册/CLI/正文仍待实现。
