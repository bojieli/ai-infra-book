# Pruner

Pruner is a "Draft-then-Verify" exploration mechanism that accelerates the schedule search process.

This repository is the official implementation of <br>
[**Pruner: A Draft-then-Verify Exploration Mechanism to Accelerate Tensor Program Tuning**](https://doi.org/10.1145/3676641.3716269) <br>
(Liang Qiao et al; ASPLOS 2025).


## Installation

- This repo is based on a fork of [Tenset](https://github.com/tlc-pack/tenset).

1. Build and install this repo following the [guide](https://github.com/AnonymousAsplos25/Pruner/blob/master/docs/install/from_source.rst).

2. Version information can refer to [here](requirements.txt).

3. Register device abstraction on Pruner as [abstraction](docs/try_Pruner_on_NvidiaA100.md)


## Using Pruner on Nvidia GPUs
Quick tutorial on using  Pruner on NVIDIA A100 refer to [tutorial](docs/try_Pruner_on_NvidiaA100.md).
###  On-Line cost model Mode
#### Steps
1. Search with Pruner (tuning 2,000 trials)
```
python3 tune_network.py --network resnet_50 --n-trials 2000 --cost-model pam --target "cuda --model=a100" --psa a100_40
```

2. Search with the MoA-Pruner (tuning 2,000 trials)
```
python3 tune_network.py --network resnet_50 --n-trials 2000 --cost-model pam-siamese-update --load-model pam_k80_1500.pkl --target "cuda --model=a100" --psa a100_40
```
3. Search with Ansor (tuning 2,000 trials)
```
# Using TensetMLP code
python3 tune_network.py --network resnet_50 --n-trials 2000 --cost-model mlp --target "cuda --model=a100"
```

### Off-line cost model Mode
#### Steps
1. Pretrain or Finetune a model refer to [tutorial](docs/try_Pruner_on_NvidiaA100.md)



2. Search with the Pruner w/ finetuned model (tuning 2,000 trials)
```
python3 tune_network.py --network resnet_50 --n-trials 2000 --cost-model pam-no-update --load-model pam_finetune.pkl --target "cuda --model=a100" --psa a100_40
```

3. Search with the TensetMLP (tuning 2,000 trials)
```
# Using TenSetMLP code
python3 tune_network.py --network resnet_50 --n-trials 2000 --cost-model mlp-no-update --load-model mlp_finetune.pkl --target "cuda --model=a100"
```

### Summary
| method (tuning 2,000 trails)  | ansor | Pruner | MoA-Pruner | TenSetMLP   | Pruner w/ finetuned model |
| ----------------- |  --- |  --- |--- | --- | --- |
| Update mode       | on-line| online| online| offline | offline |
| Search time(s)       | 6,691| 5,563 | 4,978 | 5,469 | 4,212|
| Estimated total latency(ms) | 1.592| 1.476| 1.457 |1.621 | 1.469|

Note: Details are reported in './scripts/res/resnet_50'

- The Resnet-50's tuning curve with different method is shown as follows.

![R50_a100](./docs/R50_A100_tuning_curve.png)




## Citation
A paper describing Pruner's techniques is available [on acm dl](https://dl.acm.org/doi/abs/10.1145/3676641.3716269). Please cite Pruner as:

``` bibtex
@inproceedings{qiao2025pruner,
  title={Pruner: A Draft-then-Verify Exploration Mechanism to Accelerate Tensor Program Tuning},
  author={Qiao, Liang and Shi, Jun and Hao, Xiaoyu and Fang, Xi and Zhang, Sen and Zhao, Minfan and Zhu, Ziqi and Chen, Junshi and An, Hong and Tang, Xulong and others},
  booktitle={Proceedings of the 30th ACM International Conference on Architectural Support for Programming Languages and Operating Systems, Volume 2},
  pages={949--965},
  year={2025}
}
```
