# Service Profiling Guide

In an inference service process, it is sometimes necessary to monitor the internal execution flow of the inference service framework to identify performance issues. By collecting start and end timestamps of key processes, identifying key functions or iterations, recording critical events, and gathering various types of information, performance bottlenecks can be quickly located.

This guide will walk you through the process of collecting performance data from the vLLM-Ascend service framework and operators. It covers the complete workflow from preparation, collection, analysis, to visualization, helping you quickly get started with performance collection tools.

Two performance collection solutions are provided below: Ascend PyTorch Profiler and MS Service Profiler. You can choose the appropriate tool for performance analysis and troubleshooting based on your actual requirements.  

## Solution Comparison

| Feature | Ascend PyTorch Profiler | MS Service Profiler |
|:-----|:------------------------|:------------------|
| Installation Method | Built-in, no additional installation required | Requires building msserviceprofiler from source |
| Collection Granularity | PyTorch operator level | Service framework function level |
| Control Method | API request control | Configuration file control |
| Applicable Scenarios | Model operator performance analysis | Service framework workflow analysis |
| Data Format | ascend_pt format | Chrome Tracing + CSV |
| Main Advantage | Operator-level performance analysis | Service framework workflow visualization |
| Supported Collection Capabilities | PyTorch operator level | PyTorch operator level and Service framework function level |

## Quick Selection Guide

- [**Model Operator Performance** → Use Ascend PyTorch Profiler](#ascend-pytorch-profiler)
- [**Service Framework Workflow** → Use MS Service Profiler](#ms-service-profiler)

---

## Ascend PyTorch Profiler  

### 0. Installation and Configuration

No additional packages need to be installed; it can be enabled through command-line configuration. Currently, vLLM enables **python stack** by default, which can significantly inflate the collected performance data. If you do not wish to collect **python stack**, you can disable it using `torch_profiler_with_stack=false`.

### 1. Preparation for Collection

Start the online service and set the `--profiler-config` parameter to control the path for saving performance files. After the parameter is set, the collection function is enabled.

```bash
python3 -m vllm.entrypoints.openai.api_server \
--port 8080 \
--model "facebook/opt-125m" \
--tensor-parallel-size 1 \
--max-num-seqs 128 \
--profiler-config '{"profiler": "torch", "torch_profiler_dir": "./vllm_profile", "torch_profiler_with_stack": false}' \
--dtype bfloat16 \
--max-model-len 256
```

> Note: **January 19, 2026: The vLLM mainline has deprecated the VLLM_TORCH_PROFILER_DIR environment variable.** [Related PR](https://github.com/vllm-project/vllm-ascend/pull/5928)  When using the vLLM Ascend mainline code to collect profiler data, remember to use the `--profiler-config` (online) parameter or the `profiler_config` (offline) parameter.

### 2. Start Collection

!!! note

    The `/start_profile` and `/stop_profile` endpoints are **only registered** when the server is launched with `--profiler-config` set (profiler field non-empty). If you forget to set `--profiler-config`, these endpoints will not exist and `curl` will return **404 Not Found**.

Performance collection is controlled by sending API requests. You can start collection after stabilizing the actual business data and collect profiling for a few seconds before stopping; or you can start collection first, then send business requests, and finally stop.

Send the following request to start the profiling service:

```bash
curl -X POST http://localhost:8080/start_profile
```

Send the following request to stop the profiling service:

```bash
curl -X POST http://localhost:8080/stop_profile
```

### 3. Send Requests

Send requests according to your actual business data. After sending the requests, stop the profiling service, and the data will be automatically saved to the previously configured path:

```bash
curl http://localhost:8080/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "facebook/opt-125m",
    "prompt": "San Francisco is a",
    "max_tokens": 7,
    "temperature": 0
}'

curl -X POST http://localhost:8080/stop_profile
```

### 4. Analyze Data

Navigate to the `./vllm_profile` directory and locate the generated `*ascend_pt` folder. This folder needs to be analyzed before profiling data can be examined.

```python
from torch_npu.profiler.profiler import analyse
analyse("./vllm_profile/localhost.localdomain_*_ascend_pt/")
```

### 5. View Results

After analysis, the `*ascend_pt` directory will contain many files, with the main analysis focus being the `ASCEND_PROFILER_OUTPUT` folder. This directory will include the following files:

- `analysis.db`: Performance data in database format

- `api_statistic.csv`: API call statistics

- `ascend_pytorch_profiler_0.db`: Performance data in database format

- `kernel_details.csv`: Kernel-level related data

- `operator_details.csv`: Operator-level related data

- `op_statistic.csv`: Operator utilization data

- `step_trace_time.csv`: Scheduling data

- `trace_view.json`: Chrome tracing format data, can be opened with [MindStudio Insight](https://www.hiascend.com/document/detail/zh/mindstudio/81RC1/GUI_baseddevelopmenttool/msascendinsightug/Insight_userguide_0002.html)

### Supplementary: Profiling in PD Disaggregation Scenarios

In PD (Prefill-Decode) disaggregation deployments, the Prefiller and Decoder are **separate vLLM instances**, each with its own API server. Profiling must be configured and controlled **independently** on each node:

1. **Both P and D** must launch with `--profiler-config` (pointing to different directories to avoid overwriting).

2. The main PD load-balance proxy (`load_balance_proxy_server_example.py`) does **not** forward `/start_profile` or `/stop_profile`. You must curl **each node's HTTP port directly**:

```bash
# Start profiling on both P and D
curl -X POST http://<prefiller_ip>:<prefiller_port>/start_profile
curl -X POST http://<decoder_ip>:<decoder_port>/start_profile

# Send business requests through the proxy...

# Stop profiling on both P and D
curl -X POST http://<prefiller_ip>:<prefiller_port>/stop_profile
curl -X POST http://<decoder_ip>:<decoder_port>/stop_profile
```

!!! note

    The EPD proxy (`epd_load_balance_proxy_layerwise_server_example.py`) **does** support broadcasting profiling commands to all E/P/D instances.

---

## MS Service Profiler  

### 0. Build from Source and Upgrade

The `msserviceprofiler` tool is pre-installed with the CANN Toolkit package. Use the following commands to install or upgrade from source.

```bash
git clone https://gitcode.com/Ascend/msserviceprofiler.git
cd msserviceprofiler
bash scripts/build_and_upgrade.sh
```

### 1. Preparation

Before starting the service, set the environment variable `SERVICE_PROF_CONFIG_PATH` to point to the profiling configuration file, and set the environment variable `PROFILING_SYMBOLS_PATH` to specify the YAML configuration file for the symbols that need to be imported. After that, start the vLLM service according to your deployment method.

```bash
cd ${path_to_store_profiling_files}
# Set environment variable
export SERVICE_PROF_CONFIG_PATH=ms_service_profiler_config.json
export PROFILING_SYMBOLS_PATH=service_profiling_symbols.yaml

# Start vLLM service
vllm serve Qwen/Qwen2.5-0.5B-Instruct &
```

The file `ms_service_profiler_config.json` is the profiling configuration. If it does not exist at the specified path, a default configuration will be generated automatically. If needed, you can customize it in advance according to the instructions in the `Profiling Configuration File` section below.

`service_profiling_symbols.yaml` is the configuration file containing the profiling points to be imported. You can choose **not** to set the `PROFILING_SYMBOLS_PATH` environment variable, in which case the default configuration file will be used. If the file does not exist at the path you specified, likewise, the system will generate a configuration file at your specified path for future configuration. You can customize it according to the instructions in the `Symbols Configuration File` section below.

### 2. Enable Profiling

To enable the performance data collection switch, change the `enable` field from `0` to `1` in the configuration file `ms_service_profiler_config.json`. This can be accomplished by executing the following sed command:

```bash
sed -i 's/"enable":\s*0/"enable": 1/' ./ms_service_profiler_config.json
```

### 3. Send Requests

Choose a request-sending method that suits your actual profiling needs:

```bash
curl http://localhost:8000/v1/completions \
    -H "Content-Type: application/json"  \
    -d '{
         "model": "Qwen/Qwen2.5-0.5B-Instruct",
        "prompt": "Beijing is a",
        "max_tokens": 5,
        "temperature": 0
}' | python3 -m json.tool
```

### 4. Parse Data

```bash
# xxxx-xxxx is the directory automatically created based on vLLM startup time
cd /root/.ms_server_profiler/xxxx-xxxx

# parse data
msserviceprofiler parse --input-path=./ --output-path output
```

### 5. View Results

After parsing, the `output` directory will contain:

- `chrome_tracing.json`: Chrome tracing format data, which can be opened in [MindStudio Insight](https://www.hiascend.com/document/detail/zh/mindstudio/830/GUI_baseddevelopmenttool/msascendinsightug/Insight_userguide_0002.html?framework=mindspore).
- `profiler.db`: Performance data in database format.
- `request.csv`: Request-related data.
- `kvcache.csv`: KV Cache-related data.
- `batch.csv`: Batch scheduling-related data.

---

### 6. Appendix related to MS Service Profiler

#### 6.1 Profiling Configuration File

The profiling configuration file controls profiling parameters and behavior.

##### File Format

The configuration is in JSON format. Main parameters:

| Parameter | Description | Required |
|:------:|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-----:|
| enable | Switch for profiling: <br />0: disable<br />1: enable<br />Default: 0 | Yes |
| prof_dir | Directory to store collected performance data. <br />Default: `${HOME}/.ms_server_profiler` | No |
| profiler_level | Data collection level. Default is "INFO" (normal level). | No |
| acl_task_time | Switch to collect operator dispatch latency and execution latency. Values: <br />0: off. Default; 0 or any invalid value means off.<br />1: on. When enabled, calls `aclprofCreateConfig` with `ACL_PROF_TASK_TIME_L0`.<br />2: on. MSPTI-based dump. When enabled, set before starting the service: `export LD_PRELOAD={INSTALL_DIR}/lib64/libmspti.so`, where `{INSTALL_DIR}` is the CANN installation root (e.g. `/usr/local/Ascend/cann` for a typical root install).<br />3: on. Torch Profiler–based dump. | No |
| acl_prof_task_time_level | Profiling level and duration. Values: <br />L0: collect operator dispatch and execution latency only; lower overhead (no operator basic info).<br />L1: collect AscendCL interface performance (host–device and inter-device sync/async memory copy latencies), plus operator dispatch, execution, and basic info for comprehensive analysis.<br />`{time}`: optional duration segment; integer 1–999, unit seconds.<br />If unset, defaults to L0 until program exit; invalid values fall back to defaults.<br />Level and duration can be combined, e.g., `"acl_prof_task_time_level": "L1;10"`.<br />**Note:** When Torch Profiler is used (`acl_task_time` set to `3`), `{time}` duration is not supported. | No |
| timelimit | Profiling duration for the service. The process stops automatically after this time. Range: integer 0–7200, unit: seconds. Default 0 means unlimited. Recommend at least 120s; shorter runs may lack data for parsed outputs and trigger warnings. | No |
| domain | Limit profiling to the specified domains to reduce data volume. String, separated by semicolons, case-sensitive, e.g., "Request; KVCache".<br />Empty means all available domains.<br />Available domains: Request, KVCache, ModelExecute, BatchSchedule, Communication.<br />Note: If the selected domains are incomplete, analysis output may show warnings due to missing data. See [Reference Table 1](https://www.hiascend.com/document/detail/zh/canncommercial/850/devaids/Profiling/mindieprofiling_0010.html). | No |
| torch_prof_stack | Collect operator call stacks (framework and CPU operators). Values: `false` (default, off), `true` (on). Requires `acl_task_time` set to `3`. **Note:** Enabling this configuration introduces additional performance overhead. | No |
| torch_prof_step_num | Torch Profiler step limit. Integer ≥ 0. Default `0` means collect all steps.<br />Requires `acl_task_time` set to `3`. | No |
| profiler_step_num | Step limit for operator and service framework profiling. Integer ≥ 0.<br />`0` or invalid values stop the entire service profiling process.<br />The number of steps actually recorded depends on `modelRunnerExec` events. | No |

##### Example Configuration

```json
{
    "enable": 1,
    "prof_dir": "./vllm_prof",
    "acl_task_time": 0,
    "acl_prof_task_time_level": ""
}
```

---

#### 6.2 Symbols Configuration File

The symbols configuration file defines which functions/methods to profile and supports flexible configuration with custom attribute collection.

##### File Name and Loading

- Default load path: `~/.config/vllm_ascend/service_profiling_symbols.MAJOR.MINOR.PATCH.yaml` (According to the installed version of vLLM)

If you need to customize the profiling points, it is highly recommended to copy a symbol configuration file to your working directory and point to it with the `PROFILING_SYMBOLS_PATH` environment variable.

##### Configuration file updates

After you change profiling symbols, restart the vLLM service so the updated configuration file is loaded.

##### Field Descriptions

| Field | Description | Example |
|:-----:|:-----|:-----|
| symbol | Python import path + attribute chain | `"vllm.v1.core.kv_cache_manager:KVCacheManager.free"` |
| handler | Handler type | `"timer"` (default) or `"pkg.mod:func"` (custom) |
| domain | Domain tag | `"KVCache"`, `"ModelExecute"` |
| name | Event name | `"EngineCoreExecute"` |
| min_version | Minimum supported vLLM version | `"0.9.1"` |
| max_version | Maximum supported vLLM version | `"0.11.0"` |
| attributes | Custom attribute collection | Only supported for `"timer"` handler. See the section below |

##### Configuration Examples

- Example 1: Custom handler

```yaml
- symbol: vllm.v1.core.kv_cache_manager:KVCacheManager.free
  handler: ms_service_profiler.patcher.config.custom_handler_example.kvcache_manager_free_example_handler
  domain: Example
  name: example_custom
```

- Example 2: Default timer
  
```yaml
- symbol: vllm.v1.engine.core:EngineCore.execute_model
  domain: ModelExecute
  name: EngineCoreExecute
```

- Example 3: Version constraint

```yaml
- symbol: vllm.v1.executor.abstract:Executor.execute_model
  min_version: "0.9.1"
  # No handler specified -> default timer
```

##### Custom Attribute Collection

The `attributes` field supports flexible custom attribute collection and allows operations and transformations on function arguments and return values.

###### Basic Syntax

- Argument access: use the parameter name directly, e.g., `input_ids`
- Return value access: use the `return` keyword
- Pipeline operations: use `|` to chain multiple operations
- Attribute access: use `attr` to access object attributes

###### Example

```yaml
- symbol: vllm_ascend.worker.model_runner_v1:NPUModelRunner.execute_model
  name: ModelRunnerExecuteModel
  domain: ModelExecute
  attributes:
  - name: device
    expr: args[0] | attr device | str
  - name: dp
    expr: args[0] | attr dp_rank | str
  - name: batch_size
    expr: args[0] | attr input_batch | attr _req_ids | len
```

###### Expression Notes

1. `len(input_ids)`: get the length of parameter `input_ids`.
2. `len(return) | str`: get the length of the return value and convert to string (equivalent to `str(len(return))`).
3. `return[0] | attr input_ids | len`: get the length of the `input_ids` attribute of the first element in the return value.

###### Supported Expression Types

- Basic operations: `len()`, `str()`, `int()`, `float()`
- Index access: `return[0]`, `return['key']`
- Attribute access: `return | attr attr_name`
- Pipeline composition: chain operations with `|`

###### Advanced Examples

```yaml
attributes:
  # Get tensor shape
  - name: tensor_shape
    expr: input_tensor | attr shape | str
  
  # Get specific value from a dict
  - name: batch_size
    expr: kwargs['batch_size']
  
  # Conditional expression (requires custom handler support)
  - name: is_training_mode
    expr: training | bool
  
  # Complex data processing
  - name: processed_data_len
    expr: data | attr items | len | str
```

##### Custom Handler

When `handler` specifies a custom function, it must match the following signature:

```python
def custom_handler(original_func, this, *args, **kwargs):
    """
    Custom handler
    
    Args:
        original_func: the original function object
        this: the bound object (for methods)
        *args: positional arguments
        **kwargs: keyword arguments
    
    Returns:
        processing result
    """
    # Custom logic
    pass
```

If the custom handler fails to import, the system will automatically fall back to the default timer mode.
