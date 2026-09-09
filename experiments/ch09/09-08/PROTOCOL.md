# 9-8 HiCache 文件后端恢复验证

使用固定SGLang0.5.13.post1，固定Qwen3-8B BF16、1024输入、每次强制16输出、Triton attention、关闭CUDA Graph。启用原生HiCache写穿、layer_first/kernel、file后端及wait_complete预取；页面16token，GPU缓存上限4096token，host比2。输入/配置完整保存。

先在新存储目录启动producer，连续3请求并观察文件；退出引擎后consumer新进程复用文件执行同输入。只记录原始HiCacheFile.get/set调用，未替换读写实现。验证实际加载、cached token层级字段、完整输出一致和文件哈希。调用结束不等于断电持久性：当前tofile写法无显式fsync/原子发布，实验只证明正常关闭后的进程重启，不证明崩溃一致性。目录/页面存在也不等于所有请求可复用。

本轮为单GPU顺序两实例，非网络远端传输、并发PD或A100/H20性能对照。后续还需缺失/不兼容状态及容量/预取策略变体。已有共享环境不修改；专用环境安装与JIT修复见ENVIRONMENT.md，不动其他服务和calculations。
