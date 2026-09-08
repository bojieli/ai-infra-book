#!/usr/bin/env python3
"""Verify the declared metadata match, not abstract/full-text coverage."""
from pathlib import Path
from datetime import datetime, timezone
import collections
import hashlib
import importlib.util
import json

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / 'references/proceedings/ASPLOS/2025'


def verify():
    spec = importlib.util.spec_from_file_location('asplos2025_reconcile', ROOT / 'references/reconcile_asplos2025.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sources = json.loads((DEST / 'sources.json').read_text())
    assert len(sources) == 8
    for item in sources:
        data = (ROOT / item['file']).read_bytes()
        assert item['status_code'] == 200
        assert len(data) == item['bytes'] and hashlib.sha256(data).hexdigest() == item['sha256']
    for volume in ['3622781', '3669940', '3676641']:
        data = json.loads((DEST / f'articles-{volume}.json').read_text())['message']
        assert data['total-results'] == 0 and data['items'] == []
    manifest = json.loads((DEST / 'manifest.json').read_text())
    program = next(p for p in json.loads((ROOT / 'references/proceedings/discovery/2026-09-08/program-index.json').read_text())['programs'] if p['source_id'] == 'asplos2025-program')
    program_bytes = (ROOT / manifest['source_program']['file']).read_bytes()
    assert hashlib.sha256(program_bytes).hexdigest() == manifest['source_program']['sha256'] == program['source_sha256']
    assert len(manifest['papers']) == len(program['entries']) == manifest['metadata_matched'] == 184
    queries = {name: json.loads((DEST / name).read_text())['message']['items'] for name in ['asplos2025-title-query.json', 'asplos2024-vol4-title-query.json']}
    assert all(len(items) == 1000 for items in queries.values())
    assert not manifest['query_exhaustive']
    for row, entry in zip(manifest['papers'], program['entries']):
        assert row['program_order'] == entry['program_order']
        assert 'https://doi.org/' + row['doi'] in {p['url'] for p in entry['links']}
        for location in row['metadata_sources']:
            item = queries[Path(location['file']).name][location['item_index']]
            assert item['DOI'].lower() == row['doi']
            assert item['title'][0] == row['publisher_title']
            assert item.get('published') == row['publication_date']
            assert item.get('author', []) == row['author_metadata']
        assert row['title_matches_normalized'] == (module.normalized(row['publisher_title']) == module.normalized(entry['title']))
        assert row['abstract'] is None
        assert row['reading_status'] in ['metadata_matched_not_screened', 'abstract_screened', 'selected_sections_read']
    counts = dict(collections.Counter(p['volume_doi'] for p in manifest['papers']))
    assert counts == manifest['volume_counts'] == {'10.1145/3676641': 88, '10.1145/3669940': 72, '10.1145/3622781': 24}
    variants = [p['program_order'] for p in manifest['papers'] if not p['title_matches_normalized']]
    assert variants == [7, 124, 148, 155] and manifest['title_variants'] == 4
    previous = json.loads((ROOT / 'references/proceedings/ASPLOS/2024/manifest.json').read_text())['papers']
    assert not ({p['doi'] for p in previous} & {p['doi'] for p in manifest['papers']})
    report = dict(verified_at=datetime.now(timezone.utc).isoformat(), scope='Official program DOI/metadata reconciliation only; no abstract or full-text reading claim.', responses=8, successful_empty_isbn_queries=3, program_entries_matched=184, volume_counts=counts, title_variants=variants, abstract_metadata_available=0, query_exhaustive=False, asplos2024_program_overlap=0, status='passed')
    (DEST / 'metadata-audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    return report


if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False))
