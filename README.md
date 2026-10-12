# Push Anything

Project website for **Push Anything: Single- and Multi-Object Pushing From First Sight with Contact-Implicit MPC**, hosted at https://dairlab.github.io/push-anything/.

The site is static HTML, CSS, and JavaScript. GitHub Pages serves it directly; no package installation or build step is needed.

## Media loading

- Videos have no `src` until a visitor presses play or selects an experiment.
- A shared experiment player exposes all 61 original demo choices, filtered by object count.
- The original five-by-five object grid and 24 rotating GIF previews are preserved. Push-T uses a still frame from its hardware video. Small WebP stills appear first; animated GIFs are requested only when their choices approach the viewport. Visitors who prefer reduced motion keep the still previews. Other previews and figures load lazily.
- Changing object categories cancels the current experiment request without downloading another clip. Only one video plays at a time, and offscreen/background videos pause.
- Intro and overview MP4s have their metadata moved to the front for faster startup, with no re-encoding or quality loss.
- System fonts and native browser controls avoid font, library, and icon CDN requests.

The original long experiment clips retain their MP4 layout and size. To inspect remaining clips, run:

```sh
python3 tools/optimize_videos.py
```

To losslessly remux them after installing ffmpeg:

```sh
python3 tools/optimize_videos.py --apply
```

The default command only inspects files. `--apply` replaces each clip atomically after successful conversion and a metadata-layout check. Rewriting the remaining clips changes about 3.6 GB of tracked video data, increasing Git history; review storage and GitHub publishing limits before committing that separate change. For a much larger collection, external video hosting or adaptive streaming can reduce the repository footprint and improve delivery.

## Local preview and checks

```sh
python3 -m http.server 8000
python3 -m unittest discover -s tests -v
node --check script.js
```

Open http://localhost:8000/ to preview. The basic Python server is sufficient for layout checks; use a server supporting HTTP byte ranges for realistic seeking/playback tests.
