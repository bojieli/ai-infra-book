import hashlib,json,subprocess,sys
from pathlib import Path
root=Path(__file__).parent
count=0
for manifest in [root/'profiles/profile-manifest.json',root/'results/followup-manifest.json']:
    files=json.loads(manifest.read_text())
    for name,digest in files.items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
    count+=len(files)
for script in ['analyze_profiles.py','analyze_q_control.py']:
    subprocess.run([sys.executable,str(root/script)],check=True)
print(f'PASS: {count} sealed follow-up files, two actual Nsight captures, fixed-scale Q-BF16 control with observed backend input types')
