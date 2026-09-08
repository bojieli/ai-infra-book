# Getting Started

In this repo, you can run automated tests, that profiles the startup latency of vLLM using different configurations. Moreover, it offers a lightweight predictor, that can be used to accuratly predict the startup latency of vLLM, given a model configuration and an infrastructure (CPU, GPU, etc...)

## Prepare The Environment

1) Clone the repo:
```bash
git clone https://github.com/upb-cn/vllm-startup-profiler
cd vllm-startup-profiler
```

2) Install vllm:
```bash
pip install vllm==0.10.1.1
```

3) Apply custom vllm changes (addition of profiling logs):
```bash
python3 apply_vllm_changes.py
```

## Running Tests

1) Create `env.json` file. Currently there is an example in `examples/model_size/env.json`. The file should follow the following format:
```json
{
    "env": {
        "YOUR_CUSTOM_ENV_VAR1": "CUSTOM_VALUE1",
        "YOUR_CUSTOM_ENV_VAR2": "CUSTOM_VALUE2",
    },
    "default_params": {
        "gpu-memory-utilization": 0.9,
        "max-model-len": [4096, 8192]
    },
    "configs": [
        {"model": "meta-llama/Llama-2-7b-hf"},
        {"model": "Qwen/Qwen1.5-4B", "max-num-seqs": 32}
    ]
}
```

When running vllm, all environment variables in `env` will be set, and all params in `default_params` will be passed to vllm for each config.

If the `default_params` value is an array, vllm will run each config for every value. If there are multiple array values, vllm will run for all possible combinations.

In the previous example, the following commands will be run:
```bash
python3 engine.py --model "meta-llama/Llama-2-7b-hf" --gpu-memory-utilization 0.9 --max-model-len 4096
python3 engine.py --model "meta-llama/Llama-2-7b-hf" --gpu-memory-utilization 0.9 --max-model-len 8192
python3 engine.py --model "Qwen/Qwen1.5-4B" --max-num-seqs 32 --gpu-memory-utilization 0.9 --max-model-len 4096
python3 engine.py --model "Qwen/Qwen1.5-4B" --max-num-seqs 32 --gpu-memory-utilization 0.9 --max-model-len 8192
```

2) Run tests multiple times:

```bash
bash run_iterations.sh $MACHINE_NAME $DIR_NAME $IS_FIRST_TIME $NUM_ITERATIONS
```

- `$MACHINE_NAME` is a folder name, located in `./experiments` (e.g., node1)
- `$DIR_NAME` is a folder name of the experiment you want to execute (e.g., batch_size). It must be located inside `./experiments/$EXP_MACHINE/examples/` and it must has a `env.json` file.
- `$IS_FIRST_TIME` is a boolean flag (true | false). If set to true, a dummy iteration will first run as a warm up, and will not be used for the average results.
- `$NUM_ITERATIONS` is the number of iterations each test is going to be executed

This script will run tests specified by a `env.json` file `$NUM_ITERATIONS` times and averages out the results.
The averaged results will be saved in `./experiments/$EXP_MACHINE/examples/$DIR_NAME/avg_comparison_results.json`

3) Visualize comparison results:

Finally, you can use the `visualize.ipynb` jupyter notebook to visualize the results.


## Use The Predictor

1) Generate a `avg_comparison_results.json` file using enough models from different families and architectures. See [the previous section](#prepare-the-environment) for more details.

2) Create a `models_config.json` file, which must contain the relevant information about each model used in the experiment. The file should follow this format:
```json
{
    "MODEL_NAME_KEY": {
        "size": "MODEL_SIZE_IN_BILLIONS",
        "layers": "NUMBER_OF_LAYERS",
        "vocab_size": "VOCAB SIZE",
        "tokenizer_size": "SIZE_OF_TOKENIZER_FILE_IN_MB",
        "compiled_graph_sizes": "SIZE_OF_TOTAL_COMPILED_GRAPH_SIZE"
    }
}
```

- Each model should **at least** contain these properties. Most of this informaiton can be found in the `config.json` file of the model. 
- To get the tokenizer size of a model, you can check the size of `tokenizer.json` file in **MB**.
- The compiled graph is the graph generated after the first run of `torch.compile` during the startup process. In order to easily fill this property, after you run the tests and have an iteration results, use this script to automatically fill this script to your `models_config.json` file:
```bash
python3 extract_graph_size.py iteration_output_dir_path models_config.json_path
```
Where `iteration_output_dir_path` is the path to the dir of a single iteration (e.g., `./experiments/$EXP_MACHINE/examples/$DIR_NAME/iterations/1`)

3) Train the predictor using the `predictor/train_predictor.py` script.
```bash
# Usage
python3 predictor/train_predictor.py --avg_comparison_results AVG_COMPARISON_RESULTS --models_config MODELS_CONFIG --models_output_dir MODELS_OUTPUT_DIR [--ignore_models IGNORE_MODELS]
```

- `AVG_COMPARISON_RESULTS`: Path to `avg_comparison_results.json`
- `MODELS_CONFIG`: Path to `models_config.json`
- `MODELS_OUTPUT_DIR`: Path where trained models will be saved and used later for prediction
- `IGNORE_MODELS`: Optional. Comma separated string of model labels that you don't want to use for training

4) Create `test_data.json`:
```bash
# Usage
python3 predictor/create_test_data.py --avg_comparison_results AVG_COMPARISON_RESULTS --models_config MODELS_CONFIG --output_path OUTPUT_PATH --validation_models VALIDATION_MODELS
```

- `AVG_COMPARISON_RESULTS`: Path to `avg_comparison_results.json`
- `MODELS_CONFIG`: Path to `models_config.json`
- `OUTPUT_PATH`: Path where `test_data.json` is going to be saved
- `VALIDATION_MODELS`: Comma separated string of model labels, which are going to be used for validation (usually the same models you ignored in the previous step)

5) Predict the startup latency:
```bash
# Usage
python3 predictor/run_predictor.py --models_path MODELS_PATH --test_data_path TEST_DATA_PATH [--verbose]
```

- `MODELS_PATH`: Path to model predictors created during step 3.
- `TEST_DATA_PATH`: Path to `test_data.json` created during step 4.
- `verbose`: Optional flag to print the output to the CLI.

## Reproducibility

In order to reproduce all the figures in our paper (e.g., Artifact Evaluation), we have prepared a separate documentation [here](./figures/README.md)

## Citation

If you are planning to use our work, please cite our paper:

```bib
@inproceedings{kabakibo2026breaking,
  title     = {Breaking the Ice: Analyzing Cold Start Latency in vLLM},
  author    = {Huzaifa Shaaban Kabakibo and Animesh Trivedi and Lin Wang},
  booktitle = {Proceedings of the 9th Conference on Machine Learning and Systems (MLSys)},
  year      = {2026},
  note      = {Accepted, to appear}
}
```
