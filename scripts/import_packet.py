#!/usr/bin/env python3
"""Import a downloaded contribution packet into source data. Dry-run by default.

Use on a branch. Review the data before --apply. No network calls or automatic
publication. --replace is additionally required to replace an existing record.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from validate import ROOT, load_site, validate_record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('packet', type=Path)
    parser.add_argument('--apply', action='store_true', help='Write the validated records to data/.')
    parser.add_argument('--replace', action='store_true', help='Permit replacement of matching IDs after review.')
    args = parser.parse_args()
    if args.packet.stat().st_size > 1024 * 1024:
        parser.error('Packet exceeds 1 MB.')
    raw = json.loads(args.packet.read_text(encoding='utf-8'))
    site = load_site()
    if not isinstance(raw, dict) or raw.get('schemaVersion') != 1:
        parser.error('Expected a version-1 contribution packet.')
    packets = raw.get('collections', []) + raw.get('resources', []) if raw.get('kind') == 'workspace' else [raw]
    if not isinstance(packets, list) or len(packets) > 500:
        parser.error('Invalid packet list or more than 500 records.')
    collection_ids = {c['id'] for c in site['collections']}
    for p in packets:
        if not isinstance(p, dict) or p.get('schemaVersion') != 1 or p.get('kind') not in {'collection','resource'}:
            parser.error('Invalid contribution packet.')
        if p.get('kind') == 'collection':
            collection_ids.add(p.get('record', {}).get('id'))
    plan, seen = [], set()
    for p in sorted(packets, key=lambda x: x['kind'] != 'collection'):
        kind, record = p['kind'], p['record']
        validate_record(record, kind, site['taxonomy'], collection_ids)
        pair = (kind, record['id'])
        if pair in seen:
            parser.error('Duplicate record in packet.')
        seen.add(pair)
        action = p.get('action', 'add')
        if action not in {'add','update'}:
            parser.error('Invalid action.')
        folder = ROOT / 'data' / ('collections' if kind == 'collection' else 'resources')
        existing = list(folder.rglob(record['id'] + '.json'))
        if len(existing) > 1:
            parser.error('Multiple existing records share this ID.')
        if existing and not args.replace:
            parser.error(f'{record["id"]} already exists; inspect it and use --replace to permit replacement.')
        if action == 'update' and not existing:
            parser.error(f'Cannot update {record["id"]}: it does not exist in shared data.')
        if existing:
            target = existing[0]
        elif kind == 'collection':
            target = folder / (record['id'] + '.json')
        else:
            home = (record.get('collectionIds') or ['general'])[0]
            target = folder / home / (record['id'] + '.json')
        if not target.resolve().is_relative_to((ROOT / 'data').resolve()):
            parser.error('Unsafe destination path.')
        plan.append((target, record))
    for target, record in plan:
        print(('WRITE ' if args.apply else 'PLAN  ') + str(target.relative_to(ROOT)))
    if args.apply:
        # All records have been validated before any file is written.
        for target, record in plan:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print('Imported into source data only. Run validation/build and propose a pull request.')
    else:
        print('Dry run only. Check the packet, then repeat with --apply to write files.')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f'Import stopped: {error}', file=sys.stderr)
        raise SystemExit(1)
