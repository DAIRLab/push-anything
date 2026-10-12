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

    def test_automatic_loops_and_deferred_other_videos(self):
        videos = [attrs for tag, attrs in self.page.tags if tag == 'video']
        self.assertEqual(len(videos), 4)
        for attrs in videos:
            if attrs['id'] in ['teaser-video', 'credits-video']:
                for flag in ['autoplay', 'loop', 'muted', 'playsinline']:
                    self.assertIn(flag, attrs)
                self.assertNotIn('controls', attrs)
                self.assertFalse(any(a.get('data-play') == attrs['id'] for _, a in self.page.tags))
                if attrs['id'] == 'teaser-video':
                    self.assertIn('src', attrs)
                    continue
            else:
                self.assertNotIn('autoplay', attrs)
            self.assertNotIn('src', attrs)
            self.assertEqual(attrs['preload'], 'none')
            self.assertIn('data-src', attrs)

    def test_all_experiment_groups(self):
        choices = [attrs for _, attrs in self.page.tags if attrs.get('class') == 'demo-choice']
        self.assertEqual([sum(c['data-group'] == str(n) for c in choices) for n in range(1, 5)], [25, 10, 8, 18])
        self.assertEqual(len({c['data-src'] for c in choices}), 61)

    def test_rotating_previews_are_deferred_and_accessible(self):
        previews = [attrs for tag, attrs in self.page.tags if 'data-animated-src' in attrs]
        self.assertEqual(len(previews), 24)
        self.assertEqual(len({p['data-animated-src'] for p in previews}), 24)
        for preview in previews:
            self.assertTrue(preview['data-animated-src'].endswith('.gif'))
            self.assertTrue(preview['src'].endswith('.webp'))
        choices = [attrs for _, attrs in self.page.tags if attrs.get('class') == 'demo-choice' and attrs['data-group'] == '1']
        self.assertTrue(all(c.get('aria-label') for c in choices))

    def test_unique_ids_and_existing_assets(self):
        ids = [attrs['id'] for _, attrs in self.page.tags if 'id' in attrs]
        self.assertEqual(len(ids), len(set(ids)))
        tracked = set(subprocess.check_output(['git', 'ls-files'], cwd=ROOT, text=True).splitlines())
        for _, attrs in self.page.tags:
            for key in ['src', 'poster', 'data-src', 'data-poster', 'data-animated-src']:
                path = attrs.get(key, '')
                if path and not path.startswith(('https:', 'http:', '//')):
                    relative = path.removeprefix('./')
                    self.assertTrue((ROOT / relative).is_file() or relative in tracked, path)


if __name__ == '__main__':
    unittest.main()
