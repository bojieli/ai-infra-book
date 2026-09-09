# 8-4 cache_salt执行前方案

固定真实Agent最后一轮3136输入token，BF16 Qwen3-8B，APC开启6GiB，eager单请求，强制1输出。五轮不同首token以隔离轮间前缀；每轮顺序A冷/A热/B冷/B热/A返回/无salt冷/无salt热/空salt/改首tokenA/原输入A返回。记录实际cached_tokens、输出、TTFT和输入哈希；不同非空salt冷/同salt热、空字符串与无salt的行为由实际入口验证。不同salt不是认证机制，仅检查内部缓存身份边界。相同输入跨salt输出一致，改首token不要求相同。固定顺序不做严格性能排名。
