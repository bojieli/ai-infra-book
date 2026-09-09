"""Second arm preserves casts using the installed compiler's explicit precision option."""
import argparse,hashlib,json
from pathlib import Path
import torch._inductor.config as config
import run
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
config.emulate_precision_casts=True
run.main(a.output)
(a.output/'compiler-control.json').write_text(json.dumps(dict(emulate_precision_casts=config.emulate_precision_casts,wrapper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),compiler_config_sha256=hashlib.sha256(Path(config.__file__).read_bytes()).hexdigest()),indent=2)+'\n')
