#!/usr/bin/env python3
"""Assemble the Traditional Chinese edition from manuscripts using tools/translate_tw.py."""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TRANSLATE_SCRIPT = HERE / 'tools' / 'translate_tw.py'

def main():
    print('Assembling Traditional Chinese edition...')
    subprocess.run([sys.executable, str(TRANSLATE_SCRIPT)], check=True)
    print('Assembly complete.')

if __name__ == '__main__':
    main()
