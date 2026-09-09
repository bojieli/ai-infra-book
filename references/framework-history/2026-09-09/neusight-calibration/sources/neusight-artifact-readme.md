# Experiment Workflow

The `results` and `summary` directories already contain the numbers shown in Figures 7, 8, and 9, and Tables 7 and 8 of the paper. Data for these figures and tables is available in `/scripts/asplos/summary`. Note that latency predictions may vary slightly (~10%) due to the non-deterministic behavior of DNN models used in the publication.

## Steps

1. **(Optional) Run scripts to collect datasets from scratch:**
   1. Run `run_collect.py` on each target GPU to collect datasets.
   2. After collecting datasets, run `run_dataset.py` to process the collected datasets.
   3. Run the following scripts to collect measured latency of ML model executions:
      - `run_label_amd.py`
      - `run_label_nvidia.py`
      - `run_label_fusion.py`
      - `run_label_distributed.py`
   4. For distributed training, run `install_megatron.sh` beforehand to install Megatron-LM.

2. **(Optional) Train NeuSight with the collected dataset:**
   1. Run `run_train.py` to train NeuSight with the processed datasets.
   2. Additionally, run the following scripts to train NeuSight and baseline models with the processed datasets:
      - `run_train_amd_neusight.py`
      - `run_train_nvidia_habitat.py`
      - `run_train_nvidia_micro.py`
      - `run_train_nvidia_neusight.py`

3. **Use the provided evaluation scripts to predict model execution latencies:**
   - `run_pred_amd_neusight.py`
   - `run_pred_nvidia_habitat.py`
   - `run_pred_nvidia_micro.py`
   - `run_pred_nvidia_neusight.py`
   - `run_pred_nvidia_roofline.py`

4. **Compare predictions against ground truth:**
   - Use the provided `summarize.py` and `table.py` scripts. These will generate the summary of the prediction results and the table of the prediction results in the `summary` directory.