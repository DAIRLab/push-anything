#!/usr/bin/env python3
"""Inspect MP4 startup layout. Pass --apply to losslessly remux pending clips."""
import argparse
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def needs_faststart(path):
    """Read top-level box headers without loading the video payload into memory."""
    size = path.stat().st_size
    found_media = False
    with path.open('rb') as stream:
        while stream.tell() < size:
            offset = stream.tell()
            header = stream.read(8)
            if len(header) != 8:
                raise ValueError(f'Truncated MP4 header: {path}')
            length, kind = struct.unpack('>I4s', header)
            header_size = 8
            if length == 1:
                extended = stream.read(8)
                if len(extended) != 8:
                    raise ValueError(f'Truncated extended MP4 header: {path}')
                length = struct.unpack('>Q', extended)[0]
                header_size = 16
            elif length == 0:
                length = size - offset
            if length < header_size or offset + length > size:
                raise ValueError(f'Invalid MP4 box length: {path}')
            if kind == b'moov':
                return found_media
            if kind == b'mdat':
                found_media = True
            stream.seek(offset + length)
    raise ValueError(f'MP4 has no movie metadata: {path}')


def optimize(path):
    # Replace only after ffmpeg succeeds and the new file passes the layout check.
    fd, name = tempfile.mkstemp(prefix='.faststart-', suffix='.mp4', dir=path.parent)
    os.close(fd)
    temporary = Path(name)
    try:
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
                        '-i', str(path), '-map', '0', '-c', 'copy',
                        '-movflags', '+faststart', str(temporary)], check=True)
        if needs_faststart(temporary):
            raise ValueError(f'Output metadata is still at the end: {path}')
        shutil.copymode(path, temporary)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='rewrite pending MP4s; default is inspection only')
    args = parser.parse_args()
    pending = [p for p in sorted((ROOT / 'static').rglob('*.mp4')) if needs_faststart(p)]
    size = sum(p.stat().st_size for p in pending)
    print(f'{len(pending)} clips need fast-start metadata ({size / 1e9:.2f} GB).')
    if not args.apply:
        print('Inspection only. Use --apply with ffmpeg installed to rewrite these files.')
        return
    if not shutil.which('ffmpeg'):
        parser.error('ffmpeg must be installed before using --apply')
    for path in pending:
        print(f'Optimizing {path.relative_to(ROOT)}', flush=True)
        optimize(path)


if __name__ == '__main__':
    main()
