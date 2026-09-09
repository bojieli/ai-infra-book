# slime 数据流补读入口

固定提交 `4c193f1f37509cca70f0e88807a9305b70f63f4e`。

本轮仅读使用指南 1–180 行及 README 的三个组件说明；来源、哈希和范围见 sources.json／reading-proof.json。没有执行文档命令或源码。

文档把 Megatron 训练、SGLang 生成与 Data Buffer 分开；共置不等于内存开销消失。外部引擎还可经共享文件更新权重，这与已读 SGLang 磁盘更新控制层可以衔接。上述仅为文档能力声明，完整调用与失败恢复尚未核实。

下一步只沿一个普通同步配置读取入口、样本到训练批次的转换、loss 分母和权重更新；再和已读 AReaL 部分 rollout 作同任务比较。暂不采用文档的性能优越性表述，不加入新框架节。

## 同步入口与损失接口的静态补读

同一固定版本新增 tree、train.py、actor.py、loss.py 原字节；来源目录中的仓库文件均已与 Git tree blob 对上。train.py 全文已读；actor 仅读 _get_rollout_data 开头，loss 仅读最终 loss_function，范围与哈希在 reading-proof.json。

普通同步 train.py 先等待 generate 返回，随后等待 actor 的 async_train 返回，再触发 update_weights。第一次 rollout 之前也有权重更新。critic、offload、release_train、保存与评估为条件分支，不能凭方法名 async_train 把这个入口说成跨轮异步采样。update_weights 内部的完成与失败语义尚未追到。

actor 数据入口按不含 CP 的 DP rank/size 取样本，并搬运 tokens、loss_masks；调用方已有 rollout_mask_sums 时也搬运它。这里只见接口，尚未验证样本分派、packing 或掩码生成。

loss_function 使用 step_global_batch_size，而不是直接假定每个 DP rank 的样本数相同。按样本分支乘微批数与含 CP 的 DP 大小，再除全局样本数；按 token 分支乘 CP 大小并返回 token 计数。计数逐样本将 mask 总数至少取一，所以不能把该变量直接描述成所有边界条件下的原始有效 token 总数。全零 mask 的结果须沿 reducer 和下游归一化核对，不能凭这一行报告缺陷。

这解释了为何前一轮的统一分母教学题必须继续查看真实框架：局部接口的缩放可能是为抵消 Megatron 的其他缩放。下一次只读 cp_utils.get_sum_of_sample_mean、训练调用和对应 Megatron 接口；在此之前不宣称完整 loss 正确性已经验证，也不把日志分母当作梯度分母。

## 整步分母与 Megatron 交接

本次补读 cp_utils 的 reducer、actor 调用训练的片段，以及 model.py 的后向调度／更新接口。所有新增范围见 reading-proof.json；未执行任何下载函数。model.py 的 raw HTTP 连续两次 IncompleteRead（14952/42000、16536/42000 bytes），未采纳残缺响应；改用固定 Git blob JSON 解码取得完整42000字节并校验身份。

reducer 默认按每个样本自己的 mask 总和求平均再加总；提供 sample_denoms 时改用预计算分母。其文档解释，同一 rollout 的多个片段需要共享整步 mask 总数，不能在微批内各算一次。CP 分片切局部 mask，但仍沿用传入分母；按 token 模式则返回掩码后的和。这是局部 reducer 的行为，不是完整损失函数的所有分支证明。

model.train 的 global_batch_sizes 明确按每步 rollout 数计量，常见一条 rollout 对应一个 sample；拆段时二者不能自动等同。前一节 loss_function 将它简称 sample count，应以上游真实数据组织为准。actor 传入每步微批数及这份规模序列，model 每步绑定 loss_function 后交给 Megatron forward/backward，再执行 optimizer.step，成功后以本步规模推进学习率调度。

config.finalize_model_grads_func 绑定外部 Megatron 的 finalize_model_grads。当前档案没有固定实际安装的 Megatron 依赖，所以本次不宣称已闭合其 DP 平均、CP 补偿或 token 归一化。日志 reduce_train_step_metrics 发生在更新后的另一路，也不能由日志值直接推出梯度分母。

可进入既有实验的结论已经明确：比较调度前先写清目标按 token、样本还是 rollout 加权；检查切分后分母来自哪个范围，再核对后端额外缩放。本书的简单反例用于验证这个问题，不替代具体训练栈的正确性测试。只在第10章原有梯度累积变体引用此接口，完整算法、所有框架排名及未公开性能不展开。
