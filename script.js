'use strict';

const loops = [...document.querySelectorAll('video[autoplay]')];
const videos = [...document.querySelectorAll('video:not([autoplay])')];
const visibleLoops = new Set();
const status = document.getElementById('media-status');

function playVideo(video) {
  // Keep src absent until a user asks to play; preload alone does not prevent requests.
  if (!video.getAttribute('src')) {
    video.src = video.dataset.src;
    video.load();
  }
  video.controls = true;
  const overlay = document.querySelector(`[data-play="${video.id}"]`);
  overlay.hidden = true;
  status.textContent = '';
  video.play().catch(() => {
    // Native controls remain available if the browser declines programmatic playback.
    if (!video.error) status.textContent = 'Use the video controls to start playback.';
  });
}

document.querySelectorAll('[data-play]').forEach(button => {
  button.addEventListener('click', () => playVideo(document.getElementById(button.dataset.play)));
});

videos.forEach(video => {
  video.addEventListener('play', () => {
    videos.forEach(other => { if (other !== video) other.pause(); });
    document.querySelector(`[data-play="${video.id}"]`).hidden = true;
  });
  video.addEventListener('error', () => {
    const overlay = document.querySelector(`[data-play="${video.id}"]`);
    overlay.hidden = false;
    video.controls = false;
    if (video.id === 'experiment-video') {
      status.textContent = 'This clip could not load. Try again or use “Open video” to watch it directly.';
    } else {
      overlay.querySelector('span:last-child').textContent = 'Video could not load. Select to retry.';
    }
    video.removeAttribute('src');
  });
});

const player = document.getElementById('experiment-video');
const choices = [...document.querySelectorAll('.demo-choice')];

function selectExperiment(choice, autoplay) {
  player.pause();
  player.controls = false;
  // Cancel the previous request when switching experiments, including buffered clips.
  player.removeAttribute('src');
  player.load();
  player.dataset.src = choice.dataset.src;
  player.poster = choice.dataset.poster;
  document.getElementById('experiment-title').textContent = choice.dataset.title;
  document.getElementById('experiment-file').href = choice.dataset.src;
  const group = Number(choice.dataset.group);
  document.getElementById('experiment-category').textContent = `${group === 1 ? 'SINGLE OBJECT' : `${group} OBJECTS`} · ${group === 1 ? '1' : group === 2 ? '3' : '10'}× SPEED`;
  choices.forEach(item => item.setAttribute('aria-pressed', String(item === choice)));
  document.querySelector('[data-play="experiment-video"]').hidden = false;
  status.textContent = '';
  if (autoplay) playVideo(player);
}

choices.forEach(choice => choice.addEventListener('click', () => selectExperiment(choice, true)));
const filters = [...document.querySelectorAll('[data-filter]')];
filters.forEach(filter => filter.addEventListener('click', () => {
  filters.forEach(item => item.setAttribute('aria-pressed', String(item === filter)));
  document.querySelector('.experiment-layout').dataset.group = filter.dataset.filter;
  choices.forEach(choice => { choice.hidden = choice.dataset.group !== filter.dataset.filter; });
  selectExperiment(choices.find(choice => !choice.hidden), false);
  document.querySelector('.demo-list').scrollTop = 0;
}));

function updateLoopPlayback(video) {
  if (visibleLoops.has(video) && !document.hidden) {
    if (!video.getAttribute('src')) {
      video.src = video.dataset.src;
      video.load();
    }
    // Some browsers block autoplay; retain the poster if playback is declined.
    video.play().catch(() => {});
  } else {
    video.pause();
  }
}

// Decorative loops resume on return; the credits source stays deferred until visible.
if ('IntersectionObserver' in window) {
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.target.autoplay) {
        if (entry.isIntersecting) visibleLoops.add(entry.target);
        else visibleLoops.delete(entry.target);
        updateLoopPlayback(entry.target);
      } else if (!entry.isIntersecting) {
        entry.target.pause();
      }
    });
  }, { threshold: 0.05 });
  [...loops, ...videos].forEach(video => observer.observe(video));
} else {
  loops.forEach(video => { visibleLoops.add(video); updateLoopPlayback(video); });
}
document.addEventListener('visibilitychange', () => {
  if (document.hidden) videos.forEach(video => video.pause());
  loops.forEach(updateLoopPlayback);
});

document.getElementById('copy-citation').addEventListener('click', async () => {
  const copyStatus = document.getElementById('copy-status');
  try {
    await navigator.clipboard.writeText(document.querySelector('.citation pre').textContent.trim());
    copyStatus.textContent = 'BibTeX copied.';
  } catch {
    copyStatus.textContent = 'Copy is unavailable in this browser. Select the BibTeX text and copy it manually.';
  }
});

// Keep the original rotating GIFs, but fetch them only as their choices approach the viewport.
const animatedPreviews = [...document.querySelectorAll('[data-animated-src]')];
if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
  if ('IntersectionObserver' in window) {
    const previewObserver = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        entry.target.src = entry.target.dataset.animatedSrc;
        previewObserver.unobserve(entry.target);
      });
    }, { rootMargin: '100px' });
    animatedPreviews.forEach(image => previewObserver.observe(image));
  } else {
    animatedPreviews.forEach(image => { image.src = image.dataset.animatedSrc; });
  }
}
