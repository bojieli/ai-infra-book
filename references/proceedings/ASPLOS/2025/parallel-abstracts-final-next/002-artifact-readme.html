# DynaX
Artifact Evaluation Reproduction for "DynaX: Sparse Attention Acceleration with Dynamic X:M Fine-Grained Structured Pruning", ASPLOS 2025

## Table of contens
1. [Directory Structure](#directory-structure)
2. [Getting Started](#getting-started)
3. [Experiments](#experiments)
4. [Citation](#citation)

# Directory Structure
```
DynaX     
|  README.md     
|  dataUtil.py  
|  eval_bloom.py 
|  eval_llama3.py 
|  qlora_merge.py
|  train_bloom.py 
|  train_llama.py
|--datasets
|--hardware
|   |--execute_unit
|   |   |  repe_array.scala
|   |   |  repe_row.scala
|   |   |  repe.scala
|   |   |  sram.scala
|   |--predict_unit
|   |   |  prepe_1_2.scala
|   |   |  prepe_1_4.scala
|   |   |  psum_softmax.scala
|   |   |  topl.scala
|--newModels     
|--output
|--configs
|   |  config.json
|   |  dense_config.json
|   |  nm_sparse_config.json
|   |  salo_sparse_config.json
|   |  sanger_sparse_config.json
|   |  xm_sparse_config.json
|   |  xm_sparse_config2.json 
|--models
|   |--utils
|   |   |  quant_utils.py
|   |   |  salo_spattn.py
|   |   |  sparse_attention.py
|   |  bloom_modeling.py
|   |  llama_modeling.py       
```

# Getting Started

## Requirements
python >= 3.10<br>
torch >= 2.3.0<br>
cuda >= 12.1<br>
datasets >= 3.2.0<br>
transformers >= 4.48.3<br>
peft >= 0.14.0

## Datasets Installation
By loading the dataset online or downloading it through the following link:<br>
Download the wikitext2 dataset from [here](https://huggingface.co/datasets/mindchain/wikitext2)<br>
Download the ptb dataset from [here](https://huggingface.co/datasets/ptb-text-only/ptb_text_only)<br>
Download the c4 dataset from [here](https://huggingface.co/datasets/allenai/c4)

# Experiments

## Evaluation Models
We have provided baseline methods and our method's parameter configuration files in the configs folder. For example, to evaluate the LLaMA3-8B model on the wikitext2 dataset using the configuration in `configs/xm_sparse_config.json`, you need to replace the content of config.json with the content of `xm_sparse_config.json`. Then, run the following command:
```
python eval_llama3.py --model_name_or_path=meta-llama/Meta-Llama-3-8b --dataset=wiki --max_seq_len=2048
```
## Fine-tune Models
After determining whether to use a sparse or dense configuration, you can fine-tune your model. To save GPU memory, we used LoRA for fine-tuning in our experiments, with the specific settings as shown below. For example, to fine-tune LLaMA3-8B on the wikitext2 dataset, you can run the following command: 
```
python train_llama.py --model_name_or_path=meta-llama/Meta-Llama-3-8b --dataset=wiki --out_model_path=output
```
Subsequently, you can obtain the adapter required for merging after LoRA fine-tuning in the `out_model_path` directory. Running following command: 
```
python qlora_merge.py --model_name_or_path=meta-llama/Meta-Llama-3-8b --adapter_name_or_path=output --save_path=newModels
```
will then generate the fully fine-tuned model in the `save_path` directory. You can run the following command to conduct the evaluation:
```
python eval_llama3.py --model_name_or_path=newModels --dataset=wiki --max_seq_len=2048
```

# Citation
Xiao Xiong, Zhaorui Chen, Yue Liang, Minghao Tian, Jiaxing Shang, Jiang Zhong, Dajiang Liu. DynaX: Sparse Attention Acceleration with Dynamic X:M Fine-Grained Structured Pruning. The ACM International Conference on Architectural Support for Programming Languages and Operating Systems (ASPLOS’25), 2025.
