import re
import sys
from datetime import datetime

def extract_time(line, pattern):
    """Extract time from a line using a regex pattern."""
    match = re.search(pattern, line)
    if match:
        return float(match.group(1))
    return 0

def extract_datetime(log_line):
    """extracts datetime"""
    DATE_PATTERN = re.compile(r"\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}(?:\.\d{3})?")

    match = DATE_PATTERN.search(log_line)
    if match is None:
        return None

    value = match.group()

    # Define the format string that matches the input time string
    time_format = "%m-%d %H:%M:%S.%f" if "." in value else "%m-%d %H:%M:%S"

    try:
        return datetime.strptime(value, time_format)
    except ValueError:
        raise ValueError(
            "Failed converting time value '%s' using format '%s'",
            value,
            time_format,
        )

def main(file_name):
    profiling_results = {
        "detect_platform": None,
        "llm_imports": None,
        "get_model_info": None,
        "worker_init": None,
        "framework_bootstrap": None,
        "tokenizer_init": None,
        "model_init": None,
        "load_weights": None,
        "model_loading": None,
        "dynamo_transform_time": None,
        "graph_compile_general_shape": None,
        "graph_compile_cached": None,
        "torch.compile": None,
        "kv_cache_profiling": None,
        "graph_capturing": None,
        "init_engine": None,
        "total_time": 0,
        "actual_total_time": 0,
    }
    
    # init_engine includes: kv_cache profiling, kv_cache init, graph capturing
    # model_loading includes: load_weights, model_init, pre- and post-processing (not mentioned in the log)
    # dynamo_transform_time: time taken by TorchDynamo to transform the code to an intermediate representation
    # torch.compile: It includes graph_compile_general_shape and dynamo time
    # kv_cache_profiling: time taken to profile the KV cache. It includes torch.compile + graph_compile_cached
    
    with open(file_name, "r") as f:
        lines = f.readlines()

    worker_init_start = None
    worker_init_end = None
    detect_platform_start = None
    detect_platform_end = None
    llm_imports_end = None
    get_model_info_end = None
    
    for line in lines:
        if "Loading weights took" in line:
            s = extract_time(line, r"Loading weights took ([\d.]+) seconds")
            profiling_results["load_weights"] = s

        elif "Model loading took" in line:
            s = extract_time(line, r"GiB and ([\d.]+) seconds")
            profiling_results["model_loading"] = s

        elif "Graph capturing finished" in line:
            s = extract_time(line, r"finished in ([\d.]+) secs")
            profiling_results["graph_capturing"] = s

        elif "init engine (profile, create kv cache, warmup model)" in line:
            s = extract_time(line, r"took ([\d.]+) seconds")
            profiling_results["init_engine"] = s

        elif "Dynamo bytecode transform time" in line:
            s = extract_time(line, r"time: ([\d.]+) s")
            profiling_results["dynamo_transform_time"] = s

        elif "Compiling a graph for" in line:
            s = extract_time(line, r"takes ([\d.]+) s")
            profiling_results["graph_compile_general_shape"] = s
            
        elif "Directly load the compiled" in line:
            s = extract_time(line, r"took ([\d.]+) s")
            profiling_results["graph_compile_cached"] = s

        elif "torch.compile takes" in line:
            s = extract_time(line, r"takes ([\d.]+) s in total")
            profiling_results["torch.compile"] = s
            
        elif "Memory profiling takes" in line:
            s = extract_time(line, r"takes ([\d.]+) seconds")
            profiling_results["kv_cache_profiling"] = s

        elif "Init Tokenizer took" in line:
            s = extract_time(line, r"took ([\d.]+) seconds")
            profiling_results["tokenizer_init"] = s

        elif "Initializing Model took" in line:
            s = extract_time(line, r"took ([\d.]+) seconds")
            profiling_results["model_init"] = s

        
        # Now for custom logs
        if "No plugins for group" in line:
            detect_platform_start = extract_datetime(line)
        elif "detected platform" in line:
            detect_platform_end = extract_datetime(line)
            if detect_platform_start is not None:
                profiling_results["detect_platform"] = (detect_platform_end - detect_platform_start).total_seconds()
        elif "Available plugins for group" in line:
            llm_imports_end = extract_datetime(line)
            if detect_platform_end is not None:
                profiling_results["llm_imports"] = (llm_imports_end - detect_platform_end).total_seconds()
        elif "Chunked prefill is" in line:
            get_model_info_end = extract_datetime(line)
            if llm_imports_end is not None:
                profiling_results["get_model_info"] = (get_model_info_end - llm_imports_end).total_seconds()
        elif "Waiting for init message" in line:
            worker_init_start = extract_datetime(line)
        elif "Starting to load model" in line:
            worker_init_end = extract_datetime(line)
            if worker_init_start is not None:
                profiling_results["worker_init"] = (worker_init_end - worker_init_start).total_seconds()
            
    # Fix KV cache profiling
    # It includes torch.compile + graph_compile_cached  
    graph_compile_cached = profiling_results["graph_compile_cached"] or 0
    torch_compile = profiling_results["torch.compile"] or 0
    if profiling_results["kv_cache_profiling"] is not None:
        profiling_results["kv_cache_profiling"] -= torch_compile + graph_compile_cached
    
    # Calc actual_total_time as the difference between first and last line
    total_seconds = None
    
    first_timestamp = extract_datetime(lines[0])
    for line in lines[::-1]:
        last_timestamp = extract_datetime(line)
        if last_timestamp is not None:
            break
    total_seconds = (last_timestamp - first_timestamp).total_seconds()
        
    profiling_results["actual_total_time"] = total_seconds
    
    # Calc framework_bootstrap time
    detect_platform = profiling_results["detect_platform"] or 0
    llm_imports = profiling_results["llm_imports"] or 0
    get_model_info = profiling_results["get_model_info"] or 0
    worker_init = profiling_results["worker_init"] or 0
    profiling_results["framework_bootstrap"] = detect_platform + llm_imports + get_model_info + worker_init
    
    # Calculate total time
    total_time_keys = ["framework_bootstrap", "model_loading", "init_engine", "tokenizer_init"]
    total_time = 0
    for key in total_time_keys:
        if profiling_results[key] is not None:
            total_time += profiling_results[key]
    profiling_results["total_time"] = total_time        
    
    # In some cases (bitsandbytes qunantization), load_weights is not logged
    # Deduce it from model_loading and model_init when possible
    if profiling_results["load_weights"] is None:
        if profiling_results["model_loading"] is not None and profiling_results["model_init"] is not None:
            profiling_results["load_weights"] = profiling_results["model_loading"] - profiling_results["model_init"]
            
    return profiling_results  
                
                
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python3 {sys.argv[0]} <vllm_log_file>")
        sys.exit(1)
        
    file_path = sys.argv[1]
    profiling_results = main(file_path)
    
    print("Profiling Results:")
    for key, value in profiling_results.items():
        if value is None:
            print(f"{key}: None")  
        else:
            print(f"{key}: {value:.3f} seconds")  
            