import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('media', Path(__file__).resolve().parents[1] / 'tools/optimize_videos.py')
media = importlib.util.module_from_spec(spec)
spec.loader.exec_module(media)


def box(kind, payload=b''):
    return struct.pack('>I4s', 8 + len(payload), kind) + payload


class MetadataLayoutTests(unittest.TestCase):
    def check_layout(self, contents):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'clip.mp4'
            path.write_bytes(contents)
            return media.needs_faststart(path)

    def test_ready_video(self):
        self.assertFalse(self.check_layout(box(b'ftyp') + box(b'moov') + box(b'mdat', b'video')))

    def test_metadata_at_end(self):
        self.assertTrue(self.check_layout(box(b'ftyp') + box(b'mdat', b'video') + box(b'moov')))

    def test_extended_size(self):
        extended = struct.pack('>I4sQ', 1, b'mdat', 20) + b'data'
        self.assertTrue(self.check_layout(extended + box(b'moov')))

    def test_truncated_and_missing_metadata(self):
        for contents in [b'broken', box(b'mdat'), struct.pack('>I4s', 99, b'ftyp')]:
            with self.subTest(contents=contents), self.assertRaises(ValueError):
                self.check_layout(contents)


if __name__ == '__main__':
    unittest.main()
