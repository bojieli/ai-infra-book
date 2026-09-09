# Pythia: Interpreting Transformers Across Time and Scale

This repository is for EleutherAI's project *Pythia* which combines interpretability analysis and scaling laws to understand how knowledge develops and evolves during training in autoregressive transformers. For detailed info on the models, their training, and their properties, please see our paper [Pythia: A Suite for Analyzing Large Language Models Across Training and Scaling](https://arxiv.org/abs/2304.01373).

The Pythia suite was developed with the explicit purpose of enabling research in interpretability, learning dynamics, and ethics and transparency for which existing model suites were inadequate. The key features of the Pythia suite are:
1. All models, data, and code used in the paper are publicly released, enabling full reproducibility of results. All results in our paper have been independently verified by at least one other lab.
2. All models feature 154 checkpoints saved throughout training, enabling the study of learning dynamics of LLMs.
3. All models were trained on the same data in the same order, enabling researchers to explore causal interventions on the training process.

At time of release, Pythia was the only model suite in the world to meet these desiderata. In fact, the 154 checkpoints we released for our 12B parameter models represented more partially trained checkpoints for each model than the rest of the world had ever released for all 12B+ models combined. Our work has inspired several others to create similar projects, including LLM360's [Amber](https://arxiv.org/abs/2312.06550) and [K2-65B](https://arxiv.org/abs/2501.07124), AI2's [OLMo](https://arxiv.org/abs/2402.00838), and Zyphra's [BlackMamba](https://arxiv.org/abs/2402.01771).

Aside from the Pythia suite itself, this repository also acts as a hub containing information, code, and reproducibility instructions for the following papers:
* Emergent and Predictable Memorization in Large Language Models [[code](/predictable-memorization)] [[paper](https://arxiv.org/abs/2304.11158)]
* PolyPythias: Stability and Outliers across Fifty Language Model Pre-Training Runs [[code](/polypythias)] [[paper](https://openreview.net/forum?id=bmrYu2Ekdz)]

## Changelog

[March 10, 2025] Added info for the PolyPythias paper.

[July 9, 2024] Substantially revamped the readme, including better historical contextualization and promoting lots of cool research people have done with Pythia. Also added links to subsequently trained models.

[November 2, 2023] We have added 14M and 31M models at the request of some researchers. We plan on training deduped versions of these models in the future.

[April 3, 2023] We have released a new version of all Pythia models, fixing various inconsistencies in the original suite. Please see Appendix B in [the Pythia paper](https://arxiv.org/abs/2304.01373) for details on the changes. The old models ("v0") remain available [here](https://huggingface.co/models?other=pythia_v0) and may be useful for ablation studies.

[January 20, 2023] On January 20, 2023, we chose to rename the Pythia model suite to include both embedding layer and unembedding layer parameters in our total parameter counts, in line with many other model suites and because we believe this convention better reflects the on-device memory usage of these models. We also discovered that due to a typo one of our models was smaller than we thought, and replaced it with a model of the intended size. See [here](https://huggingface.co/EleutherAI/pythia-410m-deduped#naming-convention-and-parameter-count) for more details.

## Table of contents

- [Models](#models)
  * [Multiple random seeds](#multiple-random-seeds)
  * [Changelog](#changelog)
- [Using Pythia](#using-pythia)
  * [Quickstart](#quickstart)
  * [Reproducing Training](#reproducing-training)
  * [Exploring the Dataset](#exploring-the-dataset)
  * [Pythia Paper Replication](#pythia-paper-replication)
- [Benchmark Scores](#benchmark-scores)
- [Research Building on Pythia](#research-building-on-pythia)
  * [Language model internals](#language-model-internals)
  * [Learning dynamics](#learning-dynamics)
  * [How training data determines model behavior](#how-training-data-determines-model-behavior)
  * [Security, auditing, and compliance research](#security-auditing-and-compliance-research)
- [Citation Details](#citation-details)
- [License](#license)

## Models

We train and release a suite of 8 model sizes on the Pile ([paper](https://pile.eleuther.ai/), [datasheet](https://arxiv.org/abs/2201.07311)) as well as the Pile with deduplication applied. All 8 model sizes are trained on the exact same data, in the exact same order. Each model saw 299,892,736,000 ~= 300B tokens during training. This corresponds to just under 1 epoch on the Pile for "standard" models, and ~= 1.5 epochs on the deduped Pile (which contains 207B tokens in 1 epoch). All models are trained with mixed precision, using fp16 for all models except `EleutherAI/pythia-1b` which trained with bf16, because in fp16 the model experienced an irreconcilable loss spike late in training.

After our initial release, we trained 14M and 31M parameter models at the request of alignment researchers interested in scaling sparse autoencoders.

| Params | n_layers | d_model | n_heads | d_head | Batch Size | Learning Rate | Hugging Face Checkpoints                                                |
| ------ | -------- | ------- | ------- | ------ | ---------- | ------------- | ---------------------------------------------------------- |
| 14M    | 6        | 128     | 4       | 32     | 2M         | 1.0e-3          | [Standard](https://huggingface.co/EleutherAI/pythia-14m)  |
| 31M    | 6        | 256     | 8       | 32     | 2M         | 1.0e-3          | [Standard](https://huggingface.co/EleutherAI/pythia-31m) |
| 70M    | 6        | 512     | 8       | 64     | 2M         | 1.0e-3          | [Standard](https://huggingface.co/EleutherAI/pythia-70m), [Deduped](https://huggingface.co/EleutherAI/pythia-70m-deduped)  |
| 160M   | 12       | 768     | 12      | 64     | 2M         | 6.0e-4          | [Standard](https://huggingface.co/EleutherAI/pythia-160m), [Deduped](https://huggingface.co/EleutherAI/pythia-160m-deduped)|
| 410M   | 24       | 1024    | 16      | 64     | 2M         | 3.0e-4          | [Standard](https://huggingface.co/EleutherAI/pythia-410m), [Deduped](https://huggingface.co/EleutherAI/pythia-410m-deduped)|
| 1B     | 16       | 2048    | 8       | 256    | 2M         | 3.0e-4          | [Standard](https://huggingface.co/EleutherAI/pythia-1b), [Deduped](https://huggingface.co/EleutherAI/pythia-1b-deduped)    |
| 1.4B   | 24       | 2048    | 16      | 128    | 2M         | 2.0e-4          | [Standard](https://huggingface.co/EleutherAI/pythia-1.4b), [Deduped](https://huggingface.co/EleutherAI/pythia-1.4b-deduped)|
| 2.8B   | 32       | 2560    | 32      | 80     | 2M         | 1.6e-4        | [Standard](https://huggingface.co/EleutherAI/pythia-2.8b), [Deduped](https://huggingface.co/EleutherAI/pythia-2.8b-deduped)|
| 6.9B   | 32       | 4096    | 32      | 128    | 2M         | 1.2e-4        | [Standard](https://huggingface.co/EleutherAI/pythia-6.9b), [Deduped](https://huggingface.co/EleutherAI/pythia-6.9b-deduped)|
| 12B    | 36       | 5120    | 40      | 128    | 2M         | 1.2e-4        | [Standard](https://huggingface.co/EleutherAI/pythia-12b), [Deduped](https://huggingface.co/EleutherAI/pythia-12b-deduped)  |


To promote research on the learning dynamics of LLMs we make 154 checkpoints available for each model, representing steps 0 (initialization), 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1000, and then every 1,000 subsequent steps. We also upload the pre-tokenized data files and a script to reconstruct the dataloader as seen during training for all models. See [Reproducing Training](#reproducing-training) section for more details.

Config files used to train these models with the [GPT-NeoX library](https://github.com/EleutherAI/gpt-neox) can be found at the `models/` directory within this repository, as well as in the GPT-NeoX library itself.

We made a mistake while originally training these models resulting in some inconsistencies across runs. We reran the entire model suite with these inconsistencies fixed and the original runs are available under the name `EleutherAI/pythia-160m-v0`. See the Pythia paper for further details on how the v0 models differ from the main suite.

The loss curves for all models are contained in our (messy!) wandb project [here](https://wandb.ai/eleutherai/pythia).

A rough and partial correspondence between models and wandb runs is given by:
| Model | Wandb |
| --------- | --------- |
| Pythia-2.8b | [Link](https://wandb.ai/eleutherai/pythia/groups/2.7B%20New_36751euw?workspace=user-schoelkopf) |
| Pythia-2.8b-deduped | [Link](https://wandb.ai/eleutherai/pythia/groups/2.7B%20Deduped%20New_1ygfbs9n?workspace=user-schoelkopf) |
| Pythia-1b | [Link](https://wandb.ai/eleutherai/pythia/groups/800M%20Pythia_1zw5etef/workspace) |
| Pythia-1.4b | [Link](https://wandb.ai/eleutherai/pythia/groups/Pythia%201.3B_lepj8rtx/workspace?workspace=user-schoelkopf) |
| Pythia-1.4b-deduped | [Link](https://wandb.ai/eleutherai/pythia/groups/1.3B%20Dedup_10v5wko4/workspace?workspace=user-schoelkopf) |
| Pythia-160m | [Link](https://wandb.ai/eleutherai/pythia/groups/Pythia%20125M_1mpgqyzx/workspace?workspace=user-schoelkopf) |
| Pythia-160m-deduped | [Link](https://wandb.ai/eleutherai/pythia/groups/125M%20Dedup_ym78zh5k/workspace?workspace=user-schoelkopf) |

### Multiple random seeds

The random seed used to train the Pythia models is the GPT-NeoX default: 1234. To enable research into how randomness effects model behavior, we have been training more models with different random seeds. We have currently trained and released the following models using each random seed from 1 to 9.

- Pythia 14M
- Pythia 31M
- Pythia 70M
- Pythia 160M
- Pythia 410M

All of these models are the _standard_ Pythia models, not the ones trained on the deduplicated Pile. Combined with the originally released models they represent ten otherwise identical variants using different random seeds. They can be found on HuggingFace using the naming pattern `https://huggingface.co/EleutherAI/pythia-[size]-seed[num]`. For example, `https://huggingface.co/EleutherAI/pythia-160m-seed7`. Note that the models trained with seed 1234 do not have a seed specified in their url.

Runs replicating the smaller Pythia models across multiple seeds are at: https://wandb.ai/eleutherai/pythia-extra-seeds

#### Erata

As noted [in this issue](https://github.com/EleutherAI/pythia/issues/135) the 6.9B and 12B models accidentially used a different initializaiton due to not having the initialization value specified in the config file.

## Using Pythia

### Quickstart

All Pythia models are hosted on [the Huggingface hub](https://huggingface.co/EleutherAI). They can be loaded and used via the following code (shown for the 3000-step `pythia-70M-deduped` model checkpoint):

```python
from transformers import GPTNeoXForCausalLM, AutoTokenizer

model = GPTNeoXForCausalLM.from_pretrained(
  "EleutherAI/pythia-70m-deduped",
  revision="step3000",
  cache_dir="./pythia-70m-deduped/step3000",
)

tokenizer = AutoTokenizer.from_pretrained(
  "EleutherAI/pythia-70m-deduped",
  revision="step3000",
  cache_dir="./pythia-70m-deduped/step3000",
)

inputs = tokenizer("Hello, I am", return_tensors="pt")
tokens = model.generate(**inputs)
print(tokenizer.decode(tokens[0]))
```

All models were trained for the equivalent of 143000 steps at a batch size of 2,097,152 tokens. Revision/branch `step143000` corresponds exactly to the model checkpoint on the `main` branch of each model.

We additionally have all model checkpoints in the format accepted by the [GPT-NeoX library](https://github.com/EleutherAI/gpt-neox), with final-step checkpoints+optimizer states downloadable from the Hugging Face Hub at `EleutherAI/neox-ckpt-pythia-xxx-deduped-v1` but do not serve them for all steps at scale due to size of optimizer states and anticipated lower demand. If you would like to perform analysis using the intermediate models within the GPT-NeoX codebase, or would like the optimizer states for other steps, please email hailey@eleuther.ai and stella@eleuther.ai.

> ❗ `pythia-{size}-v0` models on Huggingface of sizes `160m, 410m, 1.4b` were trained with a batch size of 4M tokens across 71500 steps and checkpointed every 500 steps. The step names on Huggingface for these v0 models are renamed for consistency with all 2M batch models so the model checkpointed labeled `step1000` of `pythia-1.4b-v0` was actually step 500, but has seen the same number of tokens as the other step1000 checkpoints.

### Reproducing Training

_(Expanded reproduction instructions provided by @BaruchG )._

We provide the training data for replication of our training runs. The [GPT-NeoX library](https://github.com/EleutherAI/gpt-neox) requires the pre-tokenized training data in the form of 2 memory-mapped numpy arrays: a `.bin` and `.idx` file. We provide these files via the Hugging Face hub. To download and use the deduplicated Pile training data:
```bash
git lfs clone https://huggingface.co/datasets/EleutherAI/pythia_deduped_pile_idxmaps

# Optionally, to ensure against corrupt files
python utils/checksum_shards.py

python utils/unshard_memmap.py --input_file ./pythia_deduped_pile_idxmaps/pile_0.87_deduped_text_document-00000-of-00082.bin --num_shards 83 --output_dir ./pythia_pile_idxmaps/

# The correct sha256 for the full file is 0cd548efd15974d5cca78f9baddbd59220ca675535dcfc0c350087c79f504693
# This can be checked with sha256sum ./pythia_pile_idxmaps/*
``` 
This will take over a day to run, though it should not require more than 5 GB of RAM. We recommend downloading this rather than retokenizing the Pile from scratch in order to guarantee preservation of the data order seen by the Pythia models. In addition to the training data, you will need to make a local copy of the tokenizer we used to train our models. You can find it [here](https://github.com/EleutherAI/pythia/blob/main/utils/20B_tokenizer.json).

Next you will need to set up the training environment:
```
git clone https://github.com/EleutherAI/gpt-neox.git
cd gpt-neox
git checkout v1.0
pip install -r requirements/requirements-flashattention.txt
wget https://github.com/EleutherAI/pythia/blob/main/models/160M/pythia-160m-deduped.yml
docker build -t pythia:latest .
```
After the container finishes building, run the container using the following command (from the root of the GPT-NeoX repo with your pythia yaml accessible from within that folder):
```
docker run --runtime=nvidia --rm -it -e NVIDIA_VISIBLE_DEVICES=0,1,2,3 --shm-size=1g --ulimit memlock=-1 --mount type=bind,src=$PWD,dst=/gpt-neox -v $(pwd):/workspace/ pythia:latest bash
```
You can use the -v argument to add more connected volumes for the dataset and the Yaml file if is not accessible from within the docker container.

Change the lines of the data paths and tokenizer paths as follows:
```
  "train-data-paths": ["/fsx/pile/pile_20B_tokenizer_text_document"], #point this to your folder which was generated in step 1 containing the .bin and .idx file
  "valid-data-paths": ["/fsx/pile/pile_20B_tokenizer_text_document"], #point this to your folder which was generated in step 1 containing the .bin and .idx file
  "test-data-paths": ["/fsx/pile/pile_20B_tokenizer_text_document"], #point this to your folder which was generated in step 1 containing the .bin and .idx file

  "tokenizer-type": "HFTokenizer",
  "vocab-file": "/fsx/pile/20B_tokenizer.json", # point this to the tokenizer retrieved in step 2
```
Depending on how much VRAM you have available you may need to adjust the batch sizes. The total batch size is calculated via `Total GPUs * train_micro_batch_size_per_gpu * gradient_accumulation_steps / (pipe-parallel-size * model-parallel-size)` and needs to be kept at 1024 to match the Pythia training batch size. You 
```
   "train_micro_batch_size_per_gpu": XXX, # make this a value that will fit within your GPU memory
   "gradient_accumulation_steps": 1, # make this a value to compensate to make the total batch size 1024.
```
If you would like your weights to be saved add that information to the yaml file as well. For example, to save in the checkpoints folder, at the bottom you can add:
```
  "launcher": "slurm",
  "deepspeed_slurm": false,

  "save": "checkpoints",
  "load": "checkpoints",
  "checkpoint_validation_with_forward_pass": False,
}
```
Make sure the paths are the paths from inside your docker container and if you want the weights to have persistence, make sure that they are accessible from outside the container, for example in /workspace/ .

You should now be able to start training your model by running:
```
python deepy.py train.py pythia-160m-deduped.yml  2>&1 | tee output.txt
```
the output will be saved to output.txt, if you don’t want that just delete the end.

In order to convert your model to the Hugging Face `transformers` format, you can use the script `tools/convert_to_hf.py` from within the GPT-NeoX library. You may have to add `from typing import List` to the type of the file and change the line [here](https://github.com/EleutherAI/gpt-neox/blob/71df4d5017f9f4919566a11454fe3a507ffdc632/tools/convert_to_hf.py#L44) from `list[torch.Tensor]` to `List[torch.Tensor]`. You can then run the script like this to convert the weights at step 143000:
```
python tools/convert_to_hf.py --input_dir checkpoints/global_step143000/ --config_file checkpoints2/global_step 143000/configs/pythia-70m.yml --output_dir ./output/ 
```
This should output a file structure similar to the one found at https://huggingface.co/EleutherAI/pythia-70m-deduped/tree/main.

> ❗ Sometimes people find that they don't end up with the right tokenizer for reasons we have been unable to debug. If your `tokenizer_config.json` looks different than the one [here](https://huggingface.co/EleutherAI/pythia-70m-deduped/blob/main/tokenizer_config.json) and `special_tokens_map.json` look different than [here](https://huggingface.co/EleutherAI/pythia-70m-deduped/blob/main/special_tokens_map.json) you may need to replace them with the ones on Huggingface.

To run evaluations using our evaluation library, install the containers [here](https://hub.docker.com/r/huggingface/transformers-pytorch-gpu/tags) (tested with the 4.28 and 4.29 versions). After setting up that docker container run:
```
git clone https://github.com/EleutherAI/lm-evaluation-harness
cd lm-evaluation-harness
pip install -e .
```
as outlined in the Harness repository. You should then be able to run the benchmark by pointing it at your weights (which should be in your container) by running a command similar to this:
```
python3 main.py --model hf-causal-experimental  --model_args pretrained=../gpt-neox/output/ --tasks lambada_openai,piqa,winogrande,arc_easy,sciq,wikitext --device cuda:0
```

### Exploring the Dataset

We provide a tool to view particular portions of the training dataloader used by all models during training, at `utils/batch_viewer.py`.

First, we need to clone the Pythia repository:
```
git clone https://github.com/EleutherAI/pythia
```
Next, we must install dependencies:
```
pip install torch==1.13.0+cu117 -f https://download.pytorch.org/whl/torch/
pip install numpy tqdm huggingface_hub
```

Next, we must download the appropriate dataset. We provide preshuffled versions of the duped and deduped pile. Download the appropriate one using Huggingface's utilities as follows:

> Tip: Make sure to replace `path/to/*` to appropriate paths where you intend to save datasets downloaded from Huggingface.
- To download standard version, use 
  ```py
  from huggingface_hub import hf_hub_download
  hf_hub_download(repo_id="EleutherAI/pile-standard-pythia-preshuffled", repo_type="dataset", cache_dir="path/to/local/folder")
  ```
- To download the deduped version, use
  ```py
  from huggingface_hub import hf_hub_download
  hf_hub_download(repo_id="EleutherAI/pile-deduped-pythia-preshuffled", repo_type="dataset", cache_dir="path/to/local/folder")
  ```

You can now merge the files by using the script `utils/unshard_memmap.py` : 

```sh
python3 utils/unshard_memmap.py --input_file "path/to/local/folder/document-00000-of-00020.bin" --num_shards 21 --output_dir "path/to/merged/folder/"
```

Make sure to also copy index file to the merged folder, using the command
```sh
cp path/to/local/folder/document.idx path/to/merged/folder/document.idx
```

Now, we're all set up to run `utils/batch_viewer.py` !

```sh
python3 utils/batch_viewer.py \
  --start_iteration 0 \
  --end_iteration 1000 \
  --load_path path/to/merged/folder/document \
  --save_path path/to/save/folder/ \
  --conf_dir utils/dummy_config.yml 
```

This will save a separate file containing all the indicies as a numpy array. 

You can now load this using numpy as 

```py
import numpy as np

indicies = np.load("path/to/save/folder/indicies.npy")
```

These indicies contain tokenized sequences of integers of size (None, 2049), where an integer corresponds to a unique token index.
Note that documents are concatenated and saperated by an `EOD` token. Thus, each sample or batch may not start with an EOD token. During training, target tokens are left shifted by 1. Thus, a model of sequence length 2048 requires 2049 length sequences for training (For more info, refer to [this comment](https://github.com/EleutherAI/pythia/issues/123#issuecomment-1791136253))

### Pythia Paper Replication

We provide further information for those interested in replicating the case studies performed in the Pythia suite paper in the `case-studies/` folder of this repository.

### Benchmark Scores

We also provide benchmark 0-shot and 5-shot results on a variety of NLP datasets:

- ARC-challenge (`arc_challenge`)
- ARC-easy (`arc_easy`)
- BLiMP (`blimp_*`)
- Lambada (`lambada_openai`)
- LogiQA (`logiqa`)
- MMLU (`hendrycksTest*`)
- PiQA (`piqa`)
- SciQ (`sciq`)
- Wikitext (`wikitext`)
- Winogrande (`winogrande`)
- WSC (`wsc`)

Evaluations were performed in GPT-NeoX using the [LM Evaluation Harness](https://github.com/EleutherAI/lm-evaluation-harness) and are viewable by model and step at `evals/pythia-v1/*/*` in this repository. **Warning:** All evaluations were run using the **to-do** commit of the language model evaluation harness almost years ago and may not be reproducible by the current version.

## Research Building on Pythia

Our primary goal with the Pythia project is to enable research on topics including interpretability and learning dynamics at EleutherAI and in the community writ large. Here we document select papers using our models, focusing on work that is uniquely empowered by the Pythia suite and would be less feasible or infeasible with models released by other organizations. For a larger list of papers citing Pythia, see [here](https://www.semanticscholar.org/paper/Pythia%3A-A-Suite-for-Analyzing-Large-Language-Models-Biderman-Schoelkopf/be55e8ec4213868db08f2c3168ae666001bea4b8#citing-papers).

### Language model internals

- Belrose, et al. "[Eliciting latent predictions from transformers with the tuned lens](https://arxiv.org/abs/2303.08112)." _arXiv preprint arXiv:2303.08112_ (2023). **EleutherAI Paper**
- Brown, et al. "[Understanding the Inner Workings of Language Models Through Representation Dissimilarity](https://arxiv.org/abs/2310.14993)." _Conference on Empirical Methods in Natural Language Processing_ (2023).
- Feng and Steinhardt. "[How do Language Models Bind Entities in Context?](https://arxiv.org/abs/2310.17191)." _International Conference on Learning Representations_ (2023).
- Garde, Kran, and Barez. "[DeepDecipher: Accessing and Investigating Neuron Activation in Large Language Models](https://arxiv.org/abs/2310.01870)." _arXiv preprint arXiv:2310.01870_ (2023).
- Gurnee, et al. "[Finding Neurons in a Haystack: Case Studies with Sparse Probing](https://arxiv.org/abs/2305.01610)." _Transactions of Machine Learning Research_ (2023).
- Stolfo, Belinkov, and Sachan. "[Understanding Arithmetic Reasoning in Language Models using Causal Mediation Analysis](https://arxiv.org/abs/2305.15054)." _Conference on Empirical Methods in Natural Language Processing_ (2023).

### Learning dynamics

- Gupta, et al. "[Continual Pre-Training of Large Language Models: How to re-warm your model?](https://arxiv.org/abs/2308.04014)." _Workshop on Efficient Systems for Foundation Models @ ICML_ (2023).
- Michaelov and Bergen. "[Emergent inabilities? Inverse scaling over the course of pretraining](https://arxiv.org/abs/2305.14681)." _Findings of the Association for Computational Linguistics: EMNLP_ (2023).
- Sanyal, et al. "[Understanding the Effectiveness of Early Weight Averaging for Training Large Language Models](https://arxiv.org/abs/2306.03241)." _arXiv preprint arXiv:2306.03241_ (2023).
- Tian, et al. "[JoMA: Demystifying Multilayer Transformers via JOint Dynamics of MLP and Attention](https://arxiv.org/abs/2310.00535)." _arXiv preprint arXiv:2310.0053_ (2023).
- Ye, et al. "[Language Versatilists vs. Specialists: An Empirical Revisiting on Multilingual Transfer Ability](https://arxiv.org/abs/2306.06688)." arXiv preprint arXiv:2306.06688 (2023).
- Belrose, et al. "[Neural Networks Learn Statistics of Increasing Complexity](https://arxiv.org/abs/2402.04362)." _International Conference on Learning Representations_ (2024). **EleutherAI Paper**
- Godey et al. "[Why do small language models underperform? Studying Language Model Saturation via the Softmax Bottleneck](https://arxiv.org/abs/2404.07647)." _arXiv preprint arXiv:2404.07647_ (2024).
- Singh, et al. "[Hallmarks of Optimization Trajectories in Neural Networks: Directional Exploration and Redundancy](https://arxiv.org/abs/2403.07379)." _arXiv preprint arXiv:2403.07379_ (2024).
- Tigges, et al. "[Stability and Generalizability of Language Model Mechanisms Across Training and Scale](https://openreview.net/forum?id=1WeLXvaNJP)." _Mechanistic Interpretability Workshop @ ICML_ (2024). **EleutherAI Paper**
- Diehl Martinez, et al. "[Tending Towards Stability: Convergence Challenges in Small Language Models](https://aclanthology.org/2024.findings-emnlp.187/) " _Findings of the Association for Computational Linguistics: EMNLP_ (2024).

### How training data determines model behavior

- Roger. "[Large Language Models Sometimes Generate Purely Negatively-Reinforced Text](https://arxiv.org/abs/2306.07567)." _arXiv preprint arXiv:2306.07567_ (2023).
- Oh, et al. "[Frequency Explains the Inverse Correlation of Large Language Models’ Size, Training Data Amount, and Surprisal’s Fit to Reading Times](https://arxiv.org/abs/2402.02255)." _arXiv preprint arXiv:2402.02255_ (2024).
- Liu, et al. "[On Training Data Influence of GPT Models](https://arxiv.org/abs/2404.07840)." _arXiv preprint arXiv:2404.07840_ (2024).
- Lesci, et al. "[Causal Estimation of Memorisation Profiles](https://arxiv.org/abs/2406.04327)." _Association for Computational Linguistics_ (2024).

### Security, auditing, and compliance research

- Ippolito, et al. "[Reverse-Engineering Decoding Strategies Given Blackbox Access to a Language Generation System.](https://aclanthology.org/2023.inlg-main.28/)" _International Natural Language Generation Conference_. 2023.
- Biderman, et al. "[Emergent and predictable memorization in large language models.](https://arxiv.org/abs/2304.11158)" _Neural Information Processing Systems_ (2023). **EleutherAI Paper**
- Choi, Shavit, and Duvenaud. "[Tools for Verifying Neural Models' Training Data](https://arxiv.org/abs/2307.00682)." _Neural Information Processing Systems_ (2023).
- Li, et al. "[MoPe: Model Perturbation-based Privacy Attacks on Language Models](https://arxiv.org/abs/2310.14369)." _Conference on Empirical Methods in Natural Language Processing_ (2023).
- Min, et al. "[SILO Language Models: Isolating Legal Risk In a Nonparametric Datastore](https://arxiv.org/abs/2308.04430)." _International Conference on Learning Representations_ (2024).
- Pawelczyk, et al. "[Machine Unlearning Fails to Remove Data Poisoning Attacks](https://arxiv.org/abs/2406.17216)." _arXiv preprint arXiv:2406.17216_ (2024).
- Prashanth, et al. "[Recite, Reconstruct, Recollect: Memorization in LMs as a Multifaceted Phenomenon](https://arxiv.org/abs/2406.17746)." _arXiv preprint arXiv:2406.17746_ (2024). **EleutherAI Paper**
- Duan, et al. "[Do Membership Inference Attacks Work on Large Language Models?](https://arxiv.org/abs/2402.07841)." _Conference on Language Modeling_ (2024).

## Citation Details

If you use the Pythia models in your research, please cite our paper via:

```
@inproceedings{biderman2023pythia,
  title={Pythia: A suite for analyzing large language models across training and scaling},
  author={Biderman, Stella and Schoelkopf, Hailey and Anthony, Quentin Gregory and Bradley, Herbie and O’Brien, Kyle and Hallahan, Eric and Khan, Mohammad Aflah and Purohit, Shivanshu and Prashanth, USVSN Sai and Raff, Edward and others},
  booktitle={International Conference on Machine Learning},
  pages={2397--2430},
  year={2023},
  organization={PMLR}
}
```
If you use data or results from other papers found in this repository, please cite the corresponding papers. Citation information can be found in the respective README and are also reproduced below for convenience:
```
@inproceedings{biderman2023emergent,
      title={Emergent and Predictable Memorization in Large Language Models}, 
      author={Biderman, Stella and Prashanth, USVSN Sai and Sutawika, Lintang and Schoelkopf, Hailey and Anthony, Quentin and Purohit, Shivanshu and Raff, Edward},
      booktitle={Advances in Neural Information Processing Systems},
      year={2023}
}

@inproceedings{van2025polypythias,
      title={PolyPythias: Stability and Outliers across Fifty Language Model Pre-Training Runs},
      author={van der Wal, Oskar and Lesci, Pietro and M{\"u}ller-Eberstein, Max and Saphra, Naomi and Schoelkopf, Hailey and Zuidema, Willem and Biderman, Stella},
      booktitle={{The Thirteenth International Conference on Learning Representations}},
      year={2025}
```
If you are interested in citing our training data, training library, or evaluation library you can do so with the following:

```
@article{gao2020pile,
  title={The pile: An 800gb dataset of diverse text for language modeling},
  author={Gao, Leo and Biderman, Stella and Black, Sid and Golding, Laurence and Hoppe, Travis and Foster, Charles and Phang, Jason and He, Horace and Thite, Anish and Nabeshima, Noa and others},
  journal={arXiv preprint arXiv:2101.00027},
  year={2020}
}

@article{biderman2022datasheet,
  title={Datasheet for the pile},
  author={Biderman, Stella and Bicheno, Kieran and Gao, Leo},
  journal={arXiv preprint arXiv:2201.07311},
  year={2022}
}

@software{gpt-neox-library,
  title = {{GPT-NeoX: Large Scale Autoregressive Language Modeling in PyTorch}},
  author = {Andonian, Alex and Anthony, Quentin and Biderman, Stella and Black, Sid and Gali, Preetham and Gao, Leo and Hallahan, Eric and Levy-Kramer, Josh and Leahy, Connor and Nestler, Lucas and Parker, Kip and Pieler, Michael and Phang, Jason and Purohit, Shivanshu and Schoelkopf, Hailey and Stander, Dashiell and Songz, Tri and Tigges, Curt and Thérien, Benjamin and Wang, Phil and Weinbach, Samuel},
  url = {https://www.github.com/eleutherai/gpt-neox},
  doi = {10.5281/zenodo.5879544},
  month = {9},
  year = {2023},
  version = {2.0.0},
}

@misc{eval-harness,
  author       = {Gao, Leo and Tow, Jonathan and Abbasi, Baber and Biderman, Stella and Black, Sid and DiPofi, Anthony and Foster, Charles and Golding, Laurence and Hsu, Jeffrey and Le Noac'h, Alain and Li, Haonan and McDonell, Kyle and Muennighoff, Niklas and Ociepa, Chris and Phang, Jason and Reynolds, Laria and Schoelkopf, Hailey and Skowron, Aviya and Sutawika, Lintang and Tang, Eric and Thite, Anish and Wang, Ben and Wang, Kevin and Zou, Andy},
  title        = {A framework for few-shot language model evaluation},
  month        = sep,
  year         = 2021,
  publisher    = {Zenodo},
  version      = {v0.0.1},
  doi          = {10.5281/zenodo.5371628},
  url          = {https://doi.org/10.5281/zenodo.5371628}
}
```

## License
The following license applies to all code in this GitHub repo, as well as the Pythia models and any other copyrightable artifacts contained in this repository.

```
   Copyright 2024 EleutherAI

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
```
