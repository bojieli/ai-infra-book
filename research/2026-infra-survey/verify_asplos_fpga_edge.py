"""Verify the sealed FPGA/edge abstract packet without rewriting its reports."""
from pathlib import Path
from hashlib import sha256
import json
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
REL = Path('references/proceedings/ASPLOS/2025')
BASE = ROOT / REL
PACKET = BASE / 'parallel-fpga-edge'

def verify():
    before = {str(p.relative_to(PACKET)): sha256(p.read_bytes()).hexdigest()
              for p in PACKET.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    provenance = json.loads((PACKET / 'local-copy-provenance.json').read_text())
    with tempfile.TemporaryDirectory(prefix='asplos-fpga-edge-') as temporary:
        root = Path(temporary)
        base = root / REL
        base.mkdir(parents=True)
        shutil.copyfile(BASE / 'manifest.json', base / 'manifest.json')
        source = root / provenance['source_archive_path']
        source.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / provenance['source_archive_path'], source)
        target = base / PACKET.name
        shutil.copytree(PACKET, target, ignore=shutil.ignore_patterns('__pycache__'))
        run = subprocess.run([sys.executable, '-B', str(target / 'verify.py')],
                             cwd=root, capture_output=True, text=True, check=True)
        report = json.loads(run.stdout)
    assert report['status'] == 'pass'
    assert report['reextracted_orders'] == [19, 25, 29, 30, 31]
    assert (report['full_primary_abstracts_reextracted'], report['representative_pdfs'],
            report['representative_pdf_pages'], report['selected_body_pages']) == (5, 3, 46, 0)
    assert report['unresolved_original_abstracts'] == [32]
    for path, digest in before.items():
        assert sha256((PACKET / path).read_bytes()).hexdigest() == digest
    records = json.loads((PACKET / 'reading-records.json').read_text())
    return {'status': 'pass', 'records': records['records'], 'gaps': records['gaps'],
            'verification': report, 'sealed_source_files_unchanged': True}

if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False))
