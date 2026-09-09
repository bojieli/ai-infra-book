#!/usr/bin/env python3
"""Verify published trace exports without requiring private native captures."""
import hashlib
import json
import sqlite3
from pathlib import Path


def verify(root: Path) -> None:
    experiments = (
        ("ch05/05-08", "results/provenance.json", "sha256"),
        ("ch05/05-09", "profiles/manifest.json", "files"),
        ("ch08/08-08", "profiles/profile-manifest.json", None),
    )
    count = 0
    for directory, manifest_name, key in experiments:
        base = root / directory
        publication = json.loads((base / "trace-publication.json").read_text())
        manifest = json.loads((base / manifest_name).read_text())
        files = manifest[key] if key else manifest
        assert "trace-publication.json" in files
        assert not set(publication["local_only_captures"]) & set(files)
        for name, digest in files.items():
            assert not name.endswith(".nsys-rep"), name
            assert hashlib.sha256((base / name).read_bytes()).hexdigest() == digest, name
        for export in publication["public_exports"]:
            name = export["file"]
            assert files[name] == export["published_sha256"]
            assert export["original_sha256"] != export["published_sha256"]
            connection = sqlite3.connect(f"file:{base / name}?mode=ro", uri=True)
            try:
                assert connection.execute("PRAGMA integrity_check").fetchone() == ("ok",)
                tables = {row[0] for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )}
                assert set(export["unchanged_event_tables"]) <= tables
            finally:
                connection.close()
            count += 1
    print(f"Verified {count} public SQLite exports and their file manifests. "
          "Original-to-export row equality was checked during redaction; "
          "this public check verifies identities and database integrity.")


if __name__ == "__main__":
    verify(Path(__file__).resolve().parent)
