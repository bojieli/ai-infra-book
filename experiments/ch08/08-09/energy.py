"""Read-only component energy snapshot; invoke with permission for RAPL."""
import json,time
from pathlib import Path
import pynvml as n
n.nvmlInit();h=n.nvmlDeviceGetHandleByIndex(0);a=time.monotonic_ns();gpu=n.nvmlDeviceGetTotalEnergyConsumption(h);b=time.monotonic_ns()
p=Path('/sys/class/powercap/intel-rapl:0/energy_uj').resolve();assert (p.parent/'name').read_text().strip()=='package-0';c=time.monotonic_ns();cpu=int(p.read_text());d=time.monotonic_ns()
print(json.dumps(dict(gpu_uuid=n.nvmlDeviceGetUUID(h),gpu_energy_mj=gpu,gpu_read_start_ns=a,gpu_read_end_ns=b,cpu_package_energy_uj=cpu,cpu_read_start_ns=c,cpu_read_end_ns=d,cpu_path=str(p),cpu_max_energy_range_uj=int((p.parent/'max_energy_range_uj').read_text()),scope='Shared GPU board and CPU package counters; not whole-machine or exclusive-job energy')));n.nvmlShutdown()
