"""Validate a local Hugging Face safetensors snapshot without loading the model.

Usage: python inspect_model.py SNAPSHOT --output results/model.json
The manifest records content hashes, not just cache-directory identity.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('snapshot', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    index_path = args.snapshot / 'model.safetensors.index.json'
    index = json.loads(index_path.read_text())
    seen, shards = {}, []
    total_tensor_bytes = 0
    for name in sorted(set(index['weight_map'].values())):
        path = args.snapshot / name
        with path.open('rb') as f:
            header_size = struct.unpack('<Q', f.read(8))[0]
            header = json.loads(f.read(header_size))
        tensors = {k: v for k, v in header.items() if k != '__metadata__'}
        intervals = []
        for key, tensor in tensors.items():
            assert key not in seen, key
            assert index['weight_map'][key] == name, key
            start, end = tensor['data_offsets']
            assert 0 <= start <= end <= path.stat().st_size - 8 - header_size
            intervals.append((start, end))
            total_tensor_bytes += end - start
            seen[key] = name
        cursor = 0
        for start, end in sorted(intervals):
            assert start == cursor, (name, start, cursor)
            cursor = end
        assert cursor == path.stat().st_size - 8 - header_size
        shards.append(dict(name=name, bytes=path.stat().st_size,
                           tensors=len(tensors), sha256=digest(path)))
    assert seen == index['weight_map']
    assert total_tensor_bytes == index['metadata']['total_size']
    metadata = {}
    for path in sorted(args.snapshot.iterdir()):
        if path.is_file() and path.suffix in {'.json', '.jinja', '.txt'}:
            metadata[path.name] = dict(bytes=path.stat().st_size, sha256=digest(path))
    result = dict(snapshot=str(args.snapshot), revision=args.snapshot.name,
                  total_tensors=len(seen), total_tensor_bytes=total_tensor_bytes,
                  shards=shards, metadata=metadata,
                  config=json.loads((args.snapshot / 'config.json').read_text()),
                  inspector_sha256=digest(Path(__file__)))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(output=str(args.output), tensors=len(seen),
                          tensor_bytes=total_tensor_bytes)))


if __name__ == '__main__':
    main()
