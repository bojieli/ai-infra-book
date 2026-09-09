from pathlib import Path
import tempfile,shutil,subprocess,os,json
R=Path(__file__).resolve().parents[2];O=Path(__file__).parent
with tempfile.TemporaryDirectory() as temp:
 book=Path(temp);p=book/'calculations';p.mkdir();shutil.copytree(R/'src',p/'src',ignore=shutil.ignore_patterns('__pycache__'));shutil.copytree(R/'tests',p/'tests',ignore=shutil.ignore_patterns('__pycache__'));shutil.copy2(R/'calc.py',p/'calc.py')
 for name in ['configs','sources','research','scenarios']:(p/name).symlink_to(R/name,target_is_directory=True)
 (book/'references').symlink_to(R.parent/'references',target_is_directory=True)
 for f in (O/'candidate').glob('*.py'):shutil.copy2(f,p/'src/infra_calc'/f.name)
 shutil.copy2(O/'test_foundation_contract.py',p/'tests/test_foundation_contract.py')
 env={**os.environ,'PYTHONPATH':str(p/'src'),'PYTHONDONTWRITEBYTECODE':'1'}
 cmd=['python','-m','unittest','discover','-s',str(p/'tests'),'-p','test_foundation_contract.py','-v'];r=subprocess.run(cmd,cwd=p,env=env,capture_output=True,text=True);(O/'candidate-tests.log').write_text(r.stdout+r.stderr)
 if os.environ.get('F03_CONTRACT_ONLY'):
  print(r.stdout+r.stderr);raise SystemExit(r.returncode)
 cmd2=['python','-m','unittest','discover','-s',str(p/'tests'),'-p','test_accounting.py','-v'];r2=subprocess.run(cmd2,cwd=p,env=env,capture_output=True,text=True);(O/'existing-accounting-tests.log').write_text(r2.stdout+r2.stderr)
 results={'new_contract_tests_exit':r.returncode,'existing_accounting_tests_exit':r2.returncode};(O/'candidate-test-results.json').write_text(json.dumps(results,indent=2));print(results);print((r.stdout+r.stderr)[-800:]);print((r2.stdout+r2.stderr)[-800:])
