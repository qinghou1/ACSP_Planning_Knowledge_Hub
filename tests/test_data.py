"""Standard-library checks for content validation and safe portable builds."""
import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from validate import load_site, validate_record
from build import build


class DataValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.site = load_site()
        cls.tax = cls.site['taxonomy']
        cls.collection_ids = {x['id'] for x in cls.site['collections']}

    def resource(self):
        record = copy.deepcopy(self.site['examples'][0])
        record.pop('isExample')
        record.update(id='test-resource', url='https://example.org/resource', topics=[], collectionIds=[], method='')
        return record

    def test_site_data_validates(self):
        self.assertEqual(len(self.site['taxonomy']['topics']), 12)
        self.assertEqual(self.site['taxonomy']['domains'], ['Education','Research','Practice'])

    def test_non_ai_no_track_no_collection_is_valid(self):
        validate_record(self.resource(), 'resource', self.tax, self.collection_ids)

    def test_unsafe_url_rejected(self):
        for url in ['javascript:alert(1)', 'data:text/html,test', 'ftp://example.org/', 'https://user:secret@example.org/']:
            with self.subTest(url=url):
                r = self.resource(); r['url'] = url
                with self.assertRaises(ValueError):
                    validate_record(r, 'resource', self.tax, self.collection_ids)

    def test_missing_or_unknown_field_rejected(self):
        for fields in [[], ['made-up-field']]:
            r = self.resource(); r['fields'] = fields
            with self.assertRaises(ValueError):
                validate_record(r, 'resource', self.tax, self.collection_ids)

    def test_description_length_enforced(self):
        for desc in ['Too short.', 'word ' * 101]:
            r = self.resource(); r['description'] = desc
            with self.assertRaises(ValueError):
                validate_record(r, 'resource', self.tax, self.collection_ids)

    def test_unknown_collection_rejected(self):
        r = self.resource(); r['collectionIds'] = ['missing-collection']
        with self.assertRaises(ValueError):
            validate_record(r, 'resource', self.tax, self.collection_ids)

    def test_sample_cannot_be_published(self):
        for example in self.site['examples']:
            with self.assertRaises(ValueError):
                validate_record(example, 'resource', self.tax, self.collection_ids)

    def test_cross_listing_is_valid(self):
        r = self.resource(); r['collectionIds'] = list(self.collection_ids)[:2]
        validate_record(r, 'resource', self.tax, self.collection_ids)

    def test_private_or_unknown_fields_rejected(self):
        r = self.resource(); r['privateEmail'] = 'private@example.org'
        with self.assertRaises(ValueError):
            validate_record(r, 'resource', self.tax, self.collection_ids)

    def test_safe_build_and_identical_snapshots(self):
        with tempfile.TemporaryDirectory() as directory:
            tmp = Path(directory)
            shutil.copytree(ROOT / 'src', tmp / 'src')
            shutil.copytree(ROOT / 'data', tmp / 'data')
            r = self.resource()
            r['title'] = '</script><img src=x onerror=alert(1)>'
            (tmp / 'data/resources/general/test-resource.json').write_text(json.dumps(r), encoding='utf-8')
            out = build(tmp)
            html = (out / 'index.html').read_text(encoding='utf-8')
            self.assertNotIn(r['title'], html)
            self.assertIn('\\u003c/script\\u003e', html)
            self.assertEqual((tmp / 'index.html').read_bytes(), (tmp / 'Planning-Knowledge-Hub-Self-Contained.html').read_bytes())
            self.assertNotIn('/*__DATA__*/', html)


if __name__ == '__main__':
    unittest.main()
