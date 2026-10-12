from html.parser import HTMLParser
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


class PageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = PageParser()
        cls.page.feed((ROOT / 'index.html').read_text())

    def test_no_initial_video_downloads(self):
        videos = [attrs for tag, attrs in self.page.tags if tag == 'video']
        self.assertEqual(len(videos), 4)
        for attrs in videos:
            self.assertNotIn('src', attrs)
            self.assertNotIn('autoplay', attrs)
            self.assertEqual(attrs['preload'], 'none')
            self.assertIn('data-src', attrs)

    def test_all_experiment_groups(self):
        choices = [attrs for _, attrs in self.page.tags if attrs.get('class') == 'demo-choice']
        self.assertEqual([sum(c['data-group'] == str(n) for c in choices) for n in range(1, 5)], [25, 10, 8, 18])
        self.assertEqual(len({c['data-src'] for c in choices}), 61)

    def test_unique_ids_and_existing_assets(self):
        ids = [attrs['id'] for _, attrs in self.page.tags if 'id' in attrs]
        self.assertEqual(len(ids), len(set(ids)))
        tracked = set(subprocess.check_output(['git', 'ls-files'], cwd=ROOT, text=True).splitlines())
        for _, attrs in self.page.tags:
            for key in ['src', 'poster', 'data-src', 'data-poster']:
                path = attrs.get(key, '')
                if path and not path.startswith(('https:', 'http:', '//')):
                    relative = path.removeprefix('./')
                    self.assertTrue((ROOT / relative).is_file() or relative in tracked, path)


if __name__ == '__main__':
    unittest.main()
