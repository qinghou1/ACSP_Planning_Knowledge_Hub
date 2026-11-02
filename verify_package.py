#!/usr/bin/env python3
"""Verify workbook, catalogs, images, and GitHub Pages HTML consistency; no third-party packages."""
import argparse
import base64
import csv
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys

import export_website_catalog as exporter

HERE = Path(__file__).resolve().parent
FULL_HUB = '20261101Planning-Knowledge-Hub-Updated.html'
COLLECTION = 'Planning-Knowledge-Hub-Resource-Collection.html'


def require(condition, message):
    if not condition:
        raise ValueError(message)


class PortabilityCheck(HTMLParser):
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        require(tag != 'base', 'A base URL could break repository-subpath navigation.')
        for key in ('href', 'src'):
            value = attrs.get(key, '')
            require(not value.startswith('/'), f'Root-relative {tag} {key}: {value}')
            require(not value.startswith('file:'), f'Local-file dependency: {value}')
        if tag in ('script', 'img') and attrs.get('src'):
            require(attrs['src'].startswith('data:'), f'External {tag} dependency.')
        if tag == 'link' and 'stylesheet' in attrs.get('rel', '').split():
            require(attrs.get('href', '').startswith('data:'), 'External stylesheet dependency.')


def html_seed(path):
    text = path.read_text(encoding='utf-8')
    match = re.search(r'<script id="hub-data" type="application/json">(.*?)</script>', text, re.S)
    require(match is not None, f'Missing embedded catalog: {path.name}')
    PortabilityCheck().feed(text)
    return json.loads(match.group(1))


def normalized_rows(raw_rows, contexts):
    records = []
    for raw in raw_rows:
        record = exporter.normalize(raw)
        exporter.attach_photo(record, [HERE], contexts)
        records.append(record)
    exporter.verify_member_schools(records, [HERE])
    exporter.verify_research_journals(records)
    return records


def by_id(records):
    result = {record['id']: record for record in records}
    require(len(result) == len(records), 'Duplicate resource IDs.')
    return result


def verify():
    require((HERE / '.nojekyll').is_file(), 'Missing root .nojekyll file.')
    require((HERE / 'index.html').read_bytes() == (HERE / FULL_HUB).read_bytes(),
            'index.html differs from the full-hub standalone HTML. Run the default rebuild.')
    catalog = json.loads((HERE / 'ACSP-Website-Catalog.json').read_text(encoding='utf-8'))
    require(catalog.get('schemaVersion') == 3 and catalog.get('kind') == 'catalog', 'Wrong catalog schema.')
    rows = catalog['resources']
    expected = by_id(rows)
    require(bool(rows), 'The catalog is empty.')
    exporter.verify_member_schools(rows, [HERE])
    exporter.verify_research_journals(rows)
    contexts = exporter.image_contexts([HERE])
    workbook = normalized_rows(exporter.read_sheet(HERE / 'ACSP-Resource-Collection.xlsx'), contexts)
    require(by_id(workbook) == expected, 'Excel Website Import values differ from the enhanced catalog.')
    with (HERE / 'ACSP-Website-Import.csv').open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        require(reader.fieldnames == exporter.HEADERS, 'CSV headers are out of sync.')
        csv_rows = normalized_rows(list(reader), contexts)
    require(by_id(csv_rows) == expected, 'CSV values differ from the enhanced catalog.')

    assets = set()
    for row in rows:
        name = row['imageFile']
        require(bool(exporter.PHOTO_FILE.fullmatch(name) or exporter.FIGURE_FILE.fullmatch(name)),
                f'Unsupported cover path: {name}')
        raw = (HERE / name).read_bytes()
        require(len(raw) <= exporter.MAX_PHOTO_BYTES, f'Oversized cover: {name}')
        require(exporter.jpeg_dimensions(raw) == (800, 450), f'Wrong cover dimensions: {name}')
        data = 'data:image/jpeg;base64,' + base64.b64encode(raw).decode('ascii')
        require(row.get('imageData') == data, f'JSON cover differs from bundled asset: {row["id"]}')
        assets.add(name)

    expected_metadata = {key: {k: v for k, v in row.items() if k != 'imageData'}
                         for key, row in expected.items()}
    seeds = []
    for name in ('index.html', FULL_HUB, COLLECTION):
        seed = html_seed(HERE / name)
        require(by_id(seed['preparedResources']) == expected_metadata, f'HTML metadata mismatch: {name}')
        require(not seed.get('resources') and not seed.get('examples'), f'Unexpected extra seed resources: {name}')
        require(set(seed['photoImages']) == assets, f'HTML cover registry mismatch: {name}')
        for row in rows:
            photo = seed['photoImages'][row['imageFile']]
            require(photo['imageData'] == row['imageData'], f'HTML image mismatch: {name}: {row["id"]}')
        seeds.append(seed)
    for seed in seeds[1:]:
        require(seed == seeds[0], 'HTML data snapshots differ between entry points.')
    counts = {}
    schools = {}
    for label, domain in [('Teaching', 'Education'), ('Research', 'Research'), ('Applications', 'Practice')]:
        selected = [row for row in rows if domain in row['domains'] and 'ai-in-planning' in row['collectionIds']]
        counts[label] = len(selected)
        schools[label] = len({row['institution'] for row in selected})
        require(counts[label] == schools[label], f'Duplicate member school in {label}.')
    return {'status': 'passed', 'resources': len(rows), 'categories': counts,
            'distinctSchoolsPerCategory': schools, 'activeCoverAssets': len(assets),
            'workbookMatchesCatalog': True, 'csvMatchesCatalog': True,
            'allHtmlMetadataMatchesCatalog': True, 'allEmbeddedImagesMatchAssets': True,
            'allHtmlSeedSnapshotsIdentical': True, 'indexMatchesStandaloneBytes': True,
            'fullHubSha256': hashlib.sha256((HERE / FULL_HUB).read_bytes()).hexdigest(),
            'staticDependencies': 'inline', 'navigation': 'fragment routes; no root-relative asset URLs',
            'researchPolicy': 'journal papers first published from 2021 onward; MDPI excluded'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, help='Also write the current verification report as JSON')
    args = parser.parse_args()
    try:
        report = verify()
        if args.report:
            args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(report, indent=2))
        return 0
    except (ValueError, KeyError, OSError, AssertionError) as exc:
        print(f'Package verification failed: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
