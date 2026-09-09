import concurrent.futures,json,pathlib,subprocess,sys
B=pathlib.Path(__file__).resolve().parent;pin=json.loads((B/'github/commit.json').read_text())['sha']
files=['docs/guides/router-replay.md','docs/local-workstation.md','docs/install.md','pyproject.toml','examples/configs/grpo_math_1B.yaml','examples/configs/recipes/llm/grpo-qwen3-30ba3b-8n8g-megatron-cp2-r3.yaml','examples/configs/recipes/llm/grpo-qwen3-30ba3b-8n8g-megatron.yaml','tests/test_suites/llm/grpo-qwen3-30ba3b-8n8g-megatron-cp2-r3.sh','nemo_rl/models/megatron/router_replay.py','nemo_rl/utils/r3_trace.py','tools/check_r3_trace.py','tests/unit/models/megatron/test_router_replay.py','nemo_rl/models/generation/vllm/vllm_worker.py']
tree={x['path'] for x in json.loads((B/'github/tree.json').read_text())['tree']}
files=[x for x in files if x in tree]
def fetch(f):
 p=subprocess.run([sys.executable,'-B',str(B/'fetch.py'),f'https://raw.githubusercontent.com/NVIDIA-NeMo/RL/{pin}/{f}','nemo/'+f],capture_output=True,text=True);assert p.returncode==0,(f,p.stderr);return p.stdout.strip()
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 for result in pool.map(fetch,files):print(result)
