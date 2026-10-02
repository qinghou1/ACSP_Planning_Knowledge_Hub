#!/usr/bin/env python3
"""Validate shared data before building. Python standard library only."""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
ID = re.compile(r'^[a-z0-9][a-z0-9-]{0,99}$')


def read_json(path: Path):
    with path.open(encoding='utf-8') as handle:
        return json.load(handle)


def require_text(value, label: str, maximum: int, required: bool = False) -> str:
    if not isinstance(value, str):
        raise ValueError(f'{label} must be text.')
    if required and not value.strip():
        raise ValueError(f'{label} is required.')
    if len(value) > maximum:
        raise ValueError(f'{label} exceeds {maximum} characters.')
    return value.strip()


def require_list(value, label: str, allowed=None, maximum: int = 24) -> list[str]:
    if not isinstance(value, list) or len(value) > maximum:
        raise ValueError(f'{label} must be a list of at most {maximum} items.')
    for v in value:
        require_text(v, label, 140, required=True)
        if allowed is not None and v not in allowed:
            raise ValueError(f'{label}: unknown value {v!r}.')
    if len(set(value)) != len(value):
        raise ValueError(f'{label} contains duplicates.')
    return value


def validate_record(record: dict, kind: str, tax: dict, collection_ids=None, *, example=False) -> None:
    if not isinstance(record, dict):
        raise ValueError('A record must be a JSON object.')
    id_ = require_text(record.get('id', ''), 'id', 100, True)
    if not ID.fullmatch(id_):
        raise ValueError('IDs must contain lowercase letters, numbers, and hyphens.')
    require_text(record.get('title', ''), 'title', 160 if kind == 'resource' else 140, True)
    desc = require_text(record.get('description', ''), 'description', 2200, True)
    min_words = 50 if kind == 'resource' else 20
    if not min_words <= len(desc.split()) <= 100:
        raise ValueError(f'description must contain {min_words}–100 words; found {len(desc.split())}.')
    fields = require_list(record.get('fields', []), 'fields', [x['id'] for x in tax['fields']])
    if not fields:
        raise ValueError('At least one field is required.')
    require_list(record.get('topics', []), 'topics', [x['id'] for x in tax['topics']])
    common = {'id', 'title', 'description', 'fields', 'topics', 'institution'}
    if kind == 'resource':
        keys = common | {'url','domain','resourceType','collectionIds','method','keywords','contributor','date','geography','license','audience'}
        if example:
            keys |= {'isExample'}
        if set(record) - keys:
            raise ValueError(f'Unknown or forbidden resource keys: {set(record) - keys}')
        url = require_text(record.get('url', ''), 'url', 1500, not example)
        if example:
            if record.get('isExample') is not True or url:
                raise ValueError('Examples must be explicitly flagged and have no resource URL.')
        else:
            parsed = urlparse(url)
            if parsed.scheme not in {'http', 'https'} or not parsed.hostname or parsed.username or parsed.password:
                raise ValueError('Use an http(s) URL without embedded credentials.')
            if id_.startswith('example-'):
                raise ValueError('Example records cannot enter the published catalog.')
        if record.get('domain') not in tax['domains']:
            raise ValueError('Invalid domain.')
        if record.get('resourceType') not in tax['resourceTypes']:
            raise ValueError('Invalid resource type.')
        cols = require_list(record.get('collectionIds', []), 'collectionIds')
        for col in cols:
            if not ID.fullmatch(col):
                raise ValueError('Invalid collection ID.')
            if collection_ids is not None and col not in collection_ids:
                raise ValueError(f'Unknown collection ID: {col}. Add its collection record first.')
        require_list(record.get('keywords', []), 'keywords', maximum=20)
        lengths = {'method':120,'institution':180,'contributor':120,'date':60,'geography':140,'license':700,'audience':180}
        for name, length in lengths.items():
            require_text(record.get(name, ''), name, length)
    elif kind == 'collection':
        keys = common | {'organizerType','organizer','status'}
        if set(record) - keys:
            raise ValueError(f'Unknown collection keys: {set(record) - keys}')
        if record.get('organizerType') not in tax['organizerTypes']:
            raise ValueError('Invalid organizer type.')
        require_text(record.get('organizer', ''), 'organizer', 180)
        require_text(record.get('institution', ''), 'institution', 250)
        if record.get('status', 'proposed') not in {'starter','proposed','active'}:
            raise ValueError('Collection status must be starter, proposed, or active.')
    else:
        raise ValueError(f'Unknown record type: {kind}')


def load_site(root: Path = ROOT) -> dict:
    data_dir = root / 'data'
    config = read_json(data_dir / 'config.json')
    tax = read_json(data_dir / 'taxonomy.json')
    require_text(config.get('siteTitle', ''), 'siteTitle', 150, True)
    repo = config.get('githubRepository', '')
    if repo and not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9_.-]{1,100}', repo):
        raise ValueError('githubRepository must be empty or owner/repository, not a URL.')
    if repo.endswith('/.') or repo.endswith('/..'):
        raise ValueError('Invalid repository name.')
    for key in ['fields', 'topics']:
        ids = [x['id'] for x in tax[key]]
        if len(set(ids)) != len(ids) or any(not ID.fullmatch(x) for x in ids):
            raise ValueError(f'Invalid or duplicate {key} IDs.')
        for item in tax[key]:
            require_text(item['label'], key + ' label', 180, True)
    collections, resources = [], []
    for folder, kind, target in [('collections', 'collection', collections), ('resources', 'resource', resources)]:
        for path in sorted((data_dir / folder).rglob('*.json')):
            record = read_json(path)
            try:
                validate_record(record, kind, tax, {c['id'] for c in collections} if kind == 'resource' else None)
                if path.stem != record['id']:
                    raise ValueError('Filename must match the record ID.')
                if any(x['id'] == record['id'] for x in target):
                    raise ValueError('Duplicate record ID.')
            except (ValueError, TypeError, KeyError) as error:
                raise ValueError(f'{path.relative_to(root)}: {error}') from error
            target.append(record)
    examples = read_json(data_dir / 'examples.json')
    for example in examples:
        validate_record(example, 'resource', tax, {c['id'] for c in collections}, example=True)
    if len({e['id'] for e in examples}) != len(examples):
        raise ValueError('Duplicate example IDs.')
    return {'config':config, 'taxonomy':tax, 'collections':collections, 'resources':resources, 'examples':examples}


def main() -> int:
    try:
        site = load_site()
        print(f"Valid: {len(site['resources'])} published resources, {len(site['collections'])} collections, {len(site['examples'])} separate fictional examples.")
        return 0
    except (ValueError, KeyError, OSError, TypeError) as error:
        print(f'Validation failed: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
