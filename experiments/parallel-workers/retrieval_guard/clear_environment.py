import os, subprocess, sys
env = dict(os.environ)
env.pop("BOOK_RETRIEVAL_TOKEN", None)
child = subprocess.Popen([sys.executable, "-c", "import os,time; print(os.getpid(), flush=True); time.sleep(3)"], env=env)
raise SystemExit(child.wait())
