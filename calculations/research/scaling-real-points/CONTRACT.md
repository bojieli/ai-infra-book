# Experiment3-8 real training-point source availability and initial contract

可用性：已找到作者官方huggingface/datablations（NeurIPS2023《Scaling Data-Constrained Language Models》）的原始数值notebook，而不是第三方读图或合成点。固定commit13701315b163f1c54642b94ad237b2699187c3ee，原件README、utils/parametric_fit.ipynb与官方会议paper.pdf已下载，URL/SHA/bytes锁在sources.lock.json。

notebook cell1明确NAMES_TO_VAL_LOSSES来自各模型Hub的val文件夹Log/TensorBoard，loss0表示未完成而排除。PARAMS_MAP给作者采用的真实N（如25m键实际35.5M，不能用名字粗读），TOKENS_MAP/后续解析给训练token总数D、unique U。原本地Beyond Chinchilla论文有实验配置但未找到逐点loss原表，因此本次单独选这一个有作者数值材料的论文，不混论文拟合。

候选candidate-points.json从作者literal字典提取33条非零、无suffix变更标签、D=U原始记录；这是可用性候选，不是已认可同控制可拟合集。没有从作者后续Chinchilla图数字化CSV混入点，也没有拟合参数或残差。data-cell.py是notebook cell1逐字提取，不能当原创脚本运行全notebook。

必要控制复核仍待：作者README说明C4/OSCAR都做过，模型名解析有歧义，必须查每个选中模型的官方sbatch/config明确数据、tokenizer、架构族、学习率日程、精确训练token预算和最终验证集。主文PDF缺补充评价细节；须补作者supplement或模型eval配置核loss定义/210M验证token声明。参数是否包含embedding也需按作者实际PARAMS_MAP生成方法定位，不能自行宣称non-embedding。

范围先限定C4/gpt2 tokenizer、regular非muP、D=U无重复、无dedup/filter/code/opt变更，后续仅用核实满足此控制族的点拟合。若架构/训练日程是按N/D预定缩放规则，control_id需记该规则，而不是写所有超参常数相同。未知关键字段的点留excluded，不能默认同控制。

预先固定留出规则（当前未做任何拟合或残差检查）：在最终合格点中N>=2e9全部作为模型尺度外推holdout，其余train；同模型ID/重复seed不得跨split。如果可拟合train不足或二维N/D设计不充分，返回不足并保留协议，不因拟合差修改阈值。此为本书复核协议，不是论文原作者的盲测协议；我们已读取公开loss列，不宣称对数据值盲法。

数据接口每行record_id/source_id/locator/N_definition/N/D_definition/D/U/loss_definition/loss/control_id/split/extraction_method/uncertainty。loss原始作者有限小数保留，不补实验置信区间；N/D标签精度也保留来源边界。raw value不是GPU本地重跑测量，实际任务质量与成本率仍另外输入。

下一步有限动作：锁官方训练目录树与候选模型sbatch（不下载权重），先验证一组覆盖多N/D的C4点；再形成确定included/excluded与预定split。只有控制审查通过后才适配现有scaling_law拟合/留出预测。当前不勾完整实验3-8。
