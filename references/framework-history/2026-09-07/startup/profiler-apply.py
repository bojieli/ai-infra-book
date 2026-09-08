import shutil
import sys
from pathlib import Path

def apply_vllm_changes(vllm_path):
    vllm_dir = Path(vllm_path)
    
    targets = [
        vllm_dir / "model_executor/model_loader/base_loader.py",
        vllm_dir / "model_executor/model_loader/tensorizer_loader.py",
        vllm_dir / "v1/engine/llm_engine.py",
        vllm_dir / "v1/worker/gpu_model_runner.py",
        vllm_dir / "v1/engine/async_llm.py",
    ]
    
    for target in targets:
        shutil.copy2(f"vllm_files/{target.name}", target)
    
    print(f"Changes applied!")

if __name__ == "__main__":
    try:
        import vllm
        import os
        vllm_path = os.path.dirname(vllm.__file__)
    except ImportError:
        print("Error: 'vllm' is not installed.")
        sys.exit(1)
        
    apply_vllm_changes(vllm_path)