# H03 最后两项公开来源审查（2026-09-09）

800I A3 白皮书正文和兼容工具公开查询均已实际检查。可合并数据在 `h03-final-patch.json`；24 份官方原件及响应的 URL、时间、字节数和 SHA-256 在 `h03-final-sources/manifest.json`。未修改共享硬件目录或来源锁。

## 800I A3 正文结果

[官方资源入口](https://e.huawei.com/cn/documents/products/computing/5f99170196404c5f90a7d0638c613652) 的公开 attachment URL 可直接下载。原产品页资源标签为04；下载 URL 和实际 PDF 封面/页脚为 **07，2026-05-12**。本地 `800i-whitepaper-04.pdf` 仅保留初始归档名，锁和记录按实际07版本。

表7-1（物理第66页，印刷第59页）直接给出10U风冷整机8 NPU、单处理器560 TFLOPS FP16 /150 TFLOPS FP32、整机4.48 PFLOPS FP16 /1.20 PFLOPS FP32；脚注明确稠密、理论设计稳定峰值。单一一组数值没有多档斜线配对问题。输入精度标签保留，累加精度及执行单元仍 unspecified，不能自动当作 IEEE FP32 Vector。

同表给整机1024 GB、单模块最大128 GB；2×1600 GB/s 的主体与聚合范围仍未完全确定，聚合带宽留 null。第7.3节（物理第71页，印刷第64页）给最大输入功率14.6 kW，记录为整机功率。

补丁新增 `atlas-800i-a3-fp16-560` 和 `huawei-atlas-800i-a3-whitepaper-07`。已通过现有 validate_device；2条峰值要求明确 FP32 累加/Cube 的选择均正确拒绝。24份原件 SHA 和长度复核通过。

## 公开兼容工具：完成实际查询

入口是[华为兼容工具](https://info.support.huawei.com/computing/tools/compatibility-query/enterprise/ascend-computing/component-compatibility)。读取官方页面公开静态 JS，按其 GET 路由和参数查询；没有登录、认证 token、私有 cookie 或修改请求。普通页面 Referer 与 Accept 仅重现公开浏览器请求上下文。端点及完整参数都已进入原件 manifest。

| 已检查集合 | 返回结果 |
|---|---|
| 昇腾组件类型，type=2 | HTTP200，Atlas系列3021与整柜3031 |
| Atlas服务器公开板型，series=3021 | HTTP200，16项；含800T A2=10524、800T A3=10579、800I A3=10580 |
| 上述三个板型的组件分类 | HTTP200，PCIe NPU类别8011可选 |
| 三个板型各自 PCIe NPU 查询 | 全部HTTP200，totalRows=0 |
| 800T A2/A3 OtherComponents 搜索910 | 全部HTTP200，totalRows=0 |
| 公开整柜列表，series=3031 | HTTP200，900 A2 PoD、900 A2 PoDc、900 A3 SuperPoD；没有950条目 |
| 900 A3 SuperPoD 节点列表，series=3037 | HTTP200，节点10559 |
| 节点10559 PCIe NPU 查询 | HTTP200，totalRows=0 |
| 权限检查 checkKbcaAuth | HTTP403，用户未登录；未尝试越过该边界 |

公开板型选择器中没有 Atlas350、950或950DT。本查询集合不是全产品目录，PCIe 兼容组件也不保证覆盖板载处理器，因此空结果不能证明不存在实际料号，也不能推断空结果一定由未登录造成。这里只能确定：**已查公开结果没有提供所需 B/C 精确 bin 映射或950DT实际板卡映射**。额外登录资料和未公开资料不在此次公开审查范围。

## 验收与剩余限制

这两项原“未查”已变成有具体原件、版本与查询结果的“已查”。合并补丁并重绑 `inventory/h03-source-review.json` 后，原H03公开官方来源审查可勾选完成。库存保留合并前21设备179峰值绑定，以及补丁合并后的预计22设备181峰值绑定，不能将预计绑定当作已合并状态。

非阻塞未知仍保留：未公开或未返回的确切订货料号、部分累加精度/执行单元/时钟、950疏密性、A3带宽聚合范围、900 A3产品页288.7与白皮书档位导出的288.768差异。未知不补猜测；源表宣传值不冒充实际硬件测量。
