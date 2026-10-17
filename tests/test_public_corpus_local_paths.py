"""Local OS paths embedded in public feed snippets are not public-source evidence."""
import json
import tempfile
import unittest
from pathlib import Path
from core.public_corpus import record_public_sample

SRC={'id':'synthetic-os-paths','auth':'public_feed','kind':'rss','platform':'synthetic'}

class LocalPathRedaction(unittest.TestCase):
    def test_windows_user_profile_path_not_persisted(self):
        with tempfile.TemporaryDirectory() as d:
            word=r'C:\Users\SyntheticPerson\Private\tokens.json'
            p=record_public_sample(Path(d),'rss',SRC,[{'url':'https://public.example.net/grants',
                       'title':'Source '+word,'summary':'Public'}],[False])
            stored=json.loads(p.read_text(encoding='utf-8'))['rows'][0]
            self.assertNotIn(word,stored['title'])

    def test_posix_home_and_unc_paths_not_persisted(self):
        with tempfile.TemporaryDirectory() as d:
            summary=r'Read /home/synthetic/private/notes.json then \\synthetic-server\Private\share\report.txt'
            p=record_public_sample(Path(d),'rss',SRC,[{'url':'https://public.example.net/grants',
                       'title':'Public grant', 'summary':summary}],[False])
            output=p.read_text(encoding='utf-8')
            self.assertNotIn('/home/synthetic/private/notes.json',output)
            self.assertNotIn('synthetic-server',output)
            self.assertTrue(json.loads(output)['rows'][0]['text_url_redacted'])

    def test_benign_public_web_home_path_kept(self):
        with tempfile.TemporaryDirectory() as d:
            u='https://public.example.net/home/grants'
            p=record_public_sample(Path(d),'rss',SRC,[{'url':u,'title':u, 'summary':'Public offer'}],[False])
            row=json.loads(p.read_text(encoding='utf-8'))['rows'][0]
            self.assertEqual(row['title'],u)
            self.assertTrue(row['url_identity_preserved'])

if __name__=='__main__':unittest.main()
