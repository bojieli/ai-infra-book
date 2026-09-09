# C81 单一补项：静态图像位置桥接

选此项而非重算视觉：现有 `vl_request.language_stage` 明确将三轴位置值视作外部输入；视觉编码、placeholder 替换、DeepStack 和语言矩阵已经覆盖。固定官方 `get_rope_index` 根据按序模态块生成位置，图像占用的语言 token 数与三轴坐标跨度不同。因此仅用总 text_tokens 和图片数不能重建实际位置值。

候选 `position_bridge.py` 接收已完成模板/tokenizer 的最大连续 text/image 块序列。一张图对应一个 image 块，视觉起止控制 token 计入相邻 text 块。固定 patch16、spatial merge2，静态图 T=1，无 padding、batch1、无语言前缀缓存。图像特征命中不改变这些索引；无需重新计算视觉矩阵。

## 官方路径与公式

固定 Transformers commit `cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55`，完整 URL 与 SHA 见 sources.lock.json。

- 源码885–935：`get_vision_position_ids`，高度/宽度除 spatial merge，meshgrid 后 stack；时间维最后加 start_position。
- 937–1043：`get_rope_index` 依 mm_token_type_ids 的连续分组遍历。文本三个轴相同；静态图像在起点 s、merged h×w 下的列坐标为 `(s,s+y,s+x)`。图像后的 current_pos 增加 max(h,w)，不是 h*w。
- 1136–1147：已缓存 rope_delta 的无 mask 直接 model decode 路径，以实际 KV 序列长度为 arange 起点，再加 rope_delta。
- 1395–1429：generation wrapper 有额外四平面 position 拼接与 superclass 准备。此候选明确选择直接 model 位置路径，未把 wrapper 额外工作隐去后声称通用 generate 完整预算。

公式：P=文本数+Σhᵢwᵢ；delta=max(position_ids)+1−P；第 i 次 consumed decode 的三轴旋转位置为 P+i+delta，但 KV 位置仍 P+i。feature cache 不改变任一值。全为静态图片且非空时 next_rotary_position=文本数+Σmax(hᵢ,wᵢ)。

固定短例：四张640²图片，每图前100个文本/控制位置，P=2000，其中1600图像位置。next_rotary_position=480，delta=−1520。生成128个 token 时仅127次 decode，最终 KV 长度2127；decode 首次旋转位置480。不能把2127 KV位置错减成607。

## 接入建议与完整性边界

新增参数 `segments`，其文本总数和 image 顺序尺寸需与现有 vl_request 输入双向检查；输出独立 `position_bridge` 表，把位置值交给已有 mrope table。不要再次累加 vision/language/DeepStack。独立 `source_steps` 提供 text expand+add、图像arange/stack/时间偏移、position零初始化/cat/assign、max/delta 与后续 decode 加法的有限算术/接口预算。reduction 比较次数是逻辑最小比较数，非具体 GPU kernel 实测。

尚不闭合：tokenizer/template、padding、视频、beam扩展、`.tolist()` 的同步/host grouping时间、实际 arange/reduction算法、allocator/HBM。源代码常量/host control小操作不假装完整底层指令。官方原件沿用既有锁而非重新获取漂移版本。当前候选没有修改共享源码、配置或场景。

验证：5项 unittest（含16个矩形网格的独立坐标枚举）。测试验证数值语义和接口公式，不冒充执行完整官方 Torch 模型。运行：`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s calculations/research/vl-position-bridge -p 'test_*.py'`。

## 独立复核后修正

Direct decode补计每步int64 arange输出8B及delta.repeat_interleave(1)读8B/写8B，不能只列三轴加法。纯文本fresh direct-model交语言层构造默认arange+past，并不执行get_rope_index；候选改为独立source_route和步骤表，等价delta0明确未缓存、容量0。公共迁移候选在public/，含锁、可直接迁移测试和4场景；verify_public.py隔离加载验证9测试通过。真实算子内部算法/host同步时间仍不冒充精确执行计数。
