"""Public-only producer must not overwrite in-root private files via directory symlink."""
import json
import tempfile
import unittest
from pathlib import Path
from core.public_corpus import record_public_sample
SRC={'id':'shared-name','auth':'public_feed','kind':'rss','platform':'synthetic'}
ROWS=[{'url':'https://example.org/public','title':'Public','summary':'Public synthetic'}]

class DirectorySymlinkScope(unittest.TestCase):
    def test_corpus_directory_symlink_pointing_inside_root_is_denied(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'data').mkdir();(root/'private').mkdir()
            existing=root/'private/shared-name.json';existing.write_text('PRIVATE_KEEP')
            (root/'data/public-corpus').symlink_to(root/'private',target_is_directory=True)
            with self.assertRaisesRegex(ValueError,'CORPUS_SYMLINK_PATH_FORBIDDEN'):
                record_public_sample(root,'rss',SRC,ROWS,[False])
            self.assertEqual(existing.read_text(),'PRIVATE_KEEP')

    def test_parent_data_symlink_pointing_inside_root_is_denied(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'private').mkdir();(root/'private/public-corpus').mkdir()
            existing=root/'private/public-corpus/shared-name.json';existing.write_text('PRIVATE_KEEP')
            (root/'data').symlink_to(root/'private',target_is_directory=True)
            with self.assertRaisesRegex(ValueError,'CORPUS_SYMLINK_PATH_FORBIDDEN'):
                record_public_sample(root,'rss',SRC,ROWS,[False])
            self.assertEqual(existing.read_text(),'PRIVATE_KEEP')

    def test_normal_non_symlink_directory_still_writes_public_sample(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            out=record_public_sample(root,'rss',SRC,ROWS,[False])
            self.assertTrue(out.is_file())
            self.assertEqual(json.loads(out.read_text())['rows'][0]['accepted'],False)

if __name__=='__main__':unittest.main()
