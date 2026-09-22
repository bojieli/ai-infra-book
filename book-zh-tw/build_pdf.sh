#!/usr/bin/env bash
# Build the Traditional Chinese edition as a single PDF.
# Usage: bash book-zh-tw/build_pdf.sh [--output-dir DIR] [--source-ref SHA]
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/build_pdf.py" "$@"
