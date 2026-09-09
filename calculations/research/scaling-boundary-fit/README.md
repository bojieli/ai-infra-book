# 真实Scaling点的非负边界拟合诊断

`fit(records, exponent_grid, N0=1e9, D0=1e10)`在每对有限指数下枚举E/A/B八个非负约束面，以小型QR解各独立活动列，再按训练SSE选择。只用fit记录选择系数和指数，holdout仅作预测/残差。原公共scaling_law.fit与compute_optimum保持不变。

与原严格正A/B入口的区别是允许零系数作为诊断：B=0时beta不再影响预测，不能把首个网格值称为识别出的数据指数。完整设计列相关、N/D坐标数及指数可识别性分别输出；正系数的formula-domain标志不保证外推可信。不同实验控制不能由本函数认证，held-out模型大小也不等于评估文档未进入训练。

8项测试通过，包括40随机设计与SciPy NNLS对照、负数据斜率落B0边界、相关设计及修改holdout不改变选择。实际求解只需标准库；独立测试用miniconda Python3.11/SciPy1.15.2。结果是确定性有限网格敏感性，不是置信区间；保留所有实际残差，不加入合成点替代真实观测。

当前为供真实数据适配器复用的候选，尚未接公共CLI/正文。

数值范围修复：列/target缩放QR、幂的对数回退、有限SSE、max-scaled RMS；坏grid分类后继续，有效点不受前点溢出中断。输出JSON拒绝NaN/Infinity；大数列与1e308可表示RMSE已独立复核。
