# 实验 6-7 结果：功率预算下的超节点规模

每设备完整功率份额＝设备 ＋ 网络 150 W ＋ 主机分摊 100 W，再乘散热系数 1.30（均为声明输入）。

## 候选规模

| 功率预算 | 设备 | 单设备 TDP | 完整份额 | 可容纳设备数 | 总容量 |
| ---: | --- | ---: | ---: | ---: | ---: |
| 120 kW | A100 80GB SXM | 400 W | 845 W | 142 | 11.4 TB |
| 120 kW | H100 SXM 80GB | 700 W | 1235 W | 97 | 7.8 TB |
| 120 kW | NVIDIA B200 SXM | 1000 W | 1625 W | 73 | 13.1 TB |
| 120 kW | RTX PRO 6000 Blackwell Workstation Edition | 600 W | 1105 W | 108 | 10.4 TB |
| 250 kW | A100 80GB SXM | 400 W | 845 W | 295 | 23.6 TB |
| 250 kW | H100 SXM 80GB | 700 W | 1235 W | 202 | 16.2 TB |
| 250 kW | NVIDIA B200 SXM | 1000 W | 1625 W | 153 | 27.5 TB |
| 250 kW | RTX PRO 6000 Blackwell Workstation Edition | 600 W | 1105 W | 226 | 21.7 TB |
| 500 kW | A100 80GB SXM | 400 W | 845 W | 591 | 47.3 TB |
| 500 kW | H100 SXM 80GB | 700 W | 1235 W | 404 | 32.3 TB |
| 500 kW | NVIDIA B200 SXM | 1000 W | 1625 W | 307 | 55.3 TB |
| 500 kW | RTX PRO 6000 Blackwell Workstation Edition | 600 W | 1105 W | 452 | 43.4 TB |
| 1000 kW | A100 80GB SXM | 400 W | 845 W | 1183 | 94.6 TB |
| 1000 kW | H100 SXM 80GB | 700 W | 1235 W | 809 | 64.7 TB |
| 1000 kW | NVIDIA B200 SXM | 1000 W | 1625 W | 615 | 110.7 TB |
| 1000 kW | RTX PRO 6000 Blackwell Workstation Edition | 600 W | 1105 W | 904 | 86.8 TB |

## 同一预算下的模型服务能力

| 功率预算 | 设备 | 模型 | 每副本卡数 | 副本数 | 每步下界 | 满配吞吐 |
| ---: | --- | --- | ---: | ---: | ---: | ---: |
| 120 kW | a100-80gb-sxm | qwen3-8b | 2 | 71 | 22.97 ms | 197783 tok/s |
| 120 kW | a100-80gb-sxm | qwen3-235b-a22b | 8 | 17 | 35.01 ms | 31075 tok/s |
| 120 kW | h100-sxm | qwen3-8b | 2 | 48 | 13.98 ms | 219684 tok/s |
| 120 kW | h100-sxm | qwen3-235b-a22b | 8 | 12 | 21.31 ms | 36039 tok/s |
| 120 kW | b200-sxm | qwen3-8b | 1 | 73 | 11.71 ms | 398929 tok/s |
| 120 kW | b200-sxm | qwen3-235b-a22b | 4 | 18 | 17.85 ms | 64547 tok/s |
| 120 kW | rtx-pro6000-blackwell-ws | qwen3-8b | 1 | 108 | 52.28 ms | 132204 tok/s |
| 120 kW | rtx-pro6000-blackwell-ws | qwen3-235b-a22b | 6 | 18 | 53.12 ms | 21688 tok/s |
| 250 kW | a100-80gb-sxm | qwen3-8b | 2 | 147 | 22.97 ms | 409494 tok/s |
| 250 kW | a100-80gb-sxm | qwen3-235b-a22b | 8 | 36 | 35.01 ms | 65806 tok/s |
| 250 kW | h100-sxm | qwen3-8b | 2 | 101 | 13.98 ms | 462252 tok/s |
| 250 kW | h100-sxm | qwen3-235b-a22b | 8 | 25 | 21.31 ms | 75081 tok/s |
| 250 kW | b200-sxm | qwen3-8b | 1 | 153 | 11.71 ms | 836111 tok/s |
| 250 kW | b200-sxm | qwen3-235b-a22b | 4 | 38 | 17.85 ms | 136266 tok/s |
| 250 kW | rtx-pro6000-blackwell-ws | qwen3-8b | 1 | 226 | 52.28 ms | 276649 tok/s |
| 250 kW | rtx-pro6000-blackwell-ws | qwen3-235b-a22b | 6 | 37 | 53.12 ms | 44580 tok/s |
| 500 kW | a100-80gb-sxm | qwen3-8b | 2 | 295 | 22.97 ms | 821773 tok/s |
| 500 kW | a100-80gb-sxm | qwen3-235b-a22b | 8 | 73 | 35.01 ms | 133439 tok/s |
| 500 kW | h100-sxm | qwen3-8b | 2 | 202 | 13.98 ms | 924504 tok/s |
| 500 kW | h100-sxm | qwen3-235b-a22b | 8 | 50 | 21.31 ms | 150161 tok/s |
| 500 kW | b200-sxm | qwen3-8b | 1 | 307 | 11.71 ms | 1677687 tok/s |
| 500 kW | b200-sxm | qwen3-235b-a22b | 4 | 76 | 17.85 ms | 272532 tok/s |
| 500 kW | rtx-pro6000-blackwell-ws | qwen3-8b | 1 | 452 | 52.28 ms | 553298 tok/s |
| 500 kW | rtx-pro6000-blackwell-ws | qwen3-235b-a22b | 6 | 75 | 53.12 ms | 90366 tok/s |
| 1000 kW | a100-80gb-sxm | qwen3-8b | 2 | 591 | 22.97 ms | 1646332 tok/s |
| 1000 kW | a100-80gb-sxm | qwen3-235b-a22b | 8 | 147 | 35.01 ms | 268706 tok/s |
| 1000 kW | h100-sxm | qwen3-8b | 2 | 404 | 13.98 ms | 1849008 tok/s |
| 1000 kW | h100-sxm | qwen3-235b-a22b | 8 | 101 | 21.31 ms | 303326 tok/s |
| 1000 kW | b200-sxm | qwen3-8b | 1 | 615 | 11.71 ms | 3360839 tok/s |
| 1000 kW | b200-sxm | qwen3-235b-a22b | 4 | 153 | 17.85 ms | 548649 tok/s |
| 1000 kW | rtx-pro6000-blackwell-ws | qwen3-8b | 1 | 904 | 52.28 ms | 1106596 tok/s |
| 1000 kW | rtx-pro6000-blackwell-ws | qwen3-235b-a22b | 6 | 150 | 53.12 ms | 180732 tok/s |
