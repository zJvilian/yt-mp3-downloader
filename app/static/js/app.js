const $ = (sel) => document.querySelector(sel);
const audio = $('#audio');
const seek = $('#seek');
let data = JSON.parse($('#initial-data').textContent);
let currentTrack = null;
let seeking = false;

const toast = (message, variant = 'danger') => $('#toaster').create(message, { variant });

// ---- Confirm dialog (resolves true when the user confirms) ----
function confirmAction(message, okLabel = 'Delete') {
  const dialog = $('#confirm-dialog');
  $('#confirm-message').textContent = message;
  $('#confirm-ok').textContent = okLabel;
  dialog.open = true;
  return new Promise((resolve) => {
    const ok = () => { resolve(true); dialog.open = false; };
    $('#confirm-ok').addEventListener('click', ok, { once: true });
    dialog.addEventListener('wa-after-hide', () => { $('#confirm-ok').removeEventListener('click', ok); resolve(false); }, { once: true });
  });
}

async function post(url) {
  try {
    const res = await fetch(url, { method: 'POST' });
    const body = await res.json();
    if (!body.success) toast(body.error || 'Something went wrong.');
    return body.success;
  } catch {
    toast('Network error, please try again.');
    return false;
  }
}

// ---- Rendering ----
const formatTime = (s) => (isFinite(s) ? `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}` : '0:00');

function renderFiles(type) {
  const list = $(`#${type}-list`);
  const files = data[`${type}_files`];
  $(`#${type}-count`).textContent = files.length;
  if (list.dataset.files === JSON.stringify(files)) return; // unchanged, keep DOM (and focus) as is
  list.dataset.files = JSON.stringify(files);
  list.replaceChildren(...files.map((name) => {
    const row = $('#file-row').content.firstElementChild.cloneNode(true);
    row.dataset.name = name;
    row.querySelector('.row-name').textContent = name;
    row.querySelector('.row-name').title = name;
    row.querySelector('.row-download').href = `/${type}s/${encodeURIComponent(name)}`;
    row.querySelector('.row-download').download = name;
    return row;
  }));
  if (!files.length) {
    const empty = document.createElement('li');
    empty.className = 'empty';
    empty.textContent = type === 'mp3' ? 'No audio yet. Paste a link above to get started.' : 'No videos yet.';
    list.append(empty);
  }
  syncPlayingState();
}

function renderActive() {
  const jobs = Object.entries(data.active_downloads);
  const running = jobs.filter(([, job]) => job.status === 'downloading');
  $('#active-section').hidden = !running.length;
  $('#active-list').replaceChildren(...running.map(([id, job]) => {
    const row = $('#active-row').content.firstElementChild.cloneNode(true);
    row.dataset.id = id;
    row.querySelector('.row-name').textContent = job.url;
    row.querySelector('wa-tag').textContent = `${job.format.toUpperCase()} · ${job.current}/${job.total}`;
    const bar = row.querySelector('wa-progress-bar');
    bar.label = `Downloading ${job.url}`;
    if (job.total === '?' || !job.current) bar.indeterminate = true;
    else bar.value = (job.current / job.total) * 100;
    return row;
  }));
  $('#job-status').replaceChildren(...jobs.filter(([, job]) => job.status === 'failed').map(([, job]) => {
    const callout = document.createElement('wa-callout');
    callout.variant = 'danger';
    callout.size = 's';
    callout.textContent = `Download failed: ${job.error || job.url}`;
    return callout;
  }));
}

function render(next) {
  data = next;
  renderFiles('mp3');
  renderFiles('mp4');
  renderActive();
}

// ---- Audio player ----
function syncPlayingState() {
  const playing = !audio.paused;
  $('#play wa-icon').name = playing ? 'pause' : 'play';
  document.querySelectorAll('#mp3-list .row').forEach((row) => {
    const active = row.dataset.name === currentTrack;
    row.classList.toggle('playing', active);
    row.querySelector('.row-play wa-icon').name = active && playing ? 'pause' : 'play';
  });
}

function playTrack(name) {
  if (name === currentTrack) return audio.paused ? audio.play() : audio.pause();
  currentTrack = name;
  audio.src = `/mp3s/${encodeURIComponent(name)}`;
  $('#now-playing').textContent = name;
  $('#player').hidden = false;
  audio.play().catch(() => toast('Unable to play this file.'));
}

function step(delta) {
  const files = data.mp3_files;
  const next = files[files.indexOf(currentTrack) + delta];
  if (next) playTrack(next);
}

['play', 'pause', 'ended'].forEach((ev) => audio.addEventListener(ev, syncPlayingState));
audio.addEventListener('loadedmetadata', () => {
  seek.max = audio.duration || 1;
  $('#time-total').textContent = formatTime(audio.duration);
});
audio.addEventListener('timeupdate', () => {
  if (!seeking) seek.value = audio.currentTime;
  $('#time-current').textContent = formatTime(audio.currentTime);
});
seek.addEventListener('input', () => { seeking = true; $('#time-current').textContent = formatTime(seek.value); });
seek.addEventListener('change', () => { audio.currentTime = seek.value; seeking = false; });
$('#volume').addEventListener('input', (e) => { audio.volume = e.target.value / 100; audio.muted = false; });
audio.addEventListener('volumechange', () => {
  $('#mute wa-icon').name = audio.muted || audio.volume === 0 ? 'volume-xmark' : 'volume-high';
});
$('#mute').addEventListener('click', () => { audio.muted = !audio.muted; });
$('#play').addEventListener('click', () => (audio.paused ? audio.play() : audio.pause()));
$('#prev').addEventListener('click', () => step(-1));
$('#next').addEventListener('click', () => step(1));

// ---- Video ----
function playVideo(name) {
  const dialog = $('#video-dialog');
  $('#video').src = `/mp4s/${encodeURIComponent(name)}`;
  dialog.label = name;
  dialog.open = true;
  audio.pause();
  $('#video').play().catch(() => {});
}
$('#video-dialog').addEventListener('wa-hide', () => $('#video').pause());

// ---- Row actions (one delegated listener per list) ----
document.querySelectorAll('#mp3-list, #mp4-list').forEach((list) => list.addEventListener('click', async (e) => {
  const button = e.target.closest('[data-action]');
  if (!button) return;
  const name = button.closest('.row').dataset.name;
  const type = list.dataset.type;
  if (button.dataset.action === 'play') return type === 'mp3' ? playTrack(name) : playVideo(name);
  if (await confirmAction(`Delete “${name}”? This cannot be undone.`)) {
    if (await post(`/delete/${type}/${encodeURIComponent(name)}`)) button.closest('.row').remove();
  }
}));

$('#active-list').addEventListener('click', async (e) => {
  const button = e.target.closest('[data-action="cancel"]');
  if (button && await confirmAction('Cancel this download?', 'Cancel download')) {
    await post(`/cancel/${button.closest('.row').dataset.id}`);
  }
});

$('#clear-all').addEventListener('click', async () => {
  if (await confirmAction('Delete ALL downloaded audio and video files? This cannot be undone.', 'Delete everything')) {
    if (await post('/clear')) toast('Library cleared.', 'success');
  }
});

// ---- Theme ----
$('#theme-toggle').addEventListener('click', () => {
  const dark = document.documentElement.classList.toggle('wa-dark');
  try { localStorage.setItem('theme', dark ? 'dark' : 'light'); } catch {}
});

// ---- Download settings, remembered in this browser ----
document.querySelectorAll('[data-persist]').forEach((el) => {
  const key = `download-${el.getAttribute('name')}`;
  const prop = el.localName === 'wa-switch' ? 'checked' : 'value';
  try {
    const saved = localStorage.getItem(key);
    if (saved !== null && prop === 'checked') el.checked = saved === 'true';
    else if (saved !== null && el.querySelector(`[value="${CSS.escape(saved)}"]`)) el.value = saved;
  } catch { /* storage disabled: preferences are optional */ }
  el.addEventListener('change', () => { try { localStorage.setItem(key, el[prop]); } catch {} });
});

// ---- Live updates: SSE, falling back to polling ----
render(data);
const source = new EventSource('/events');
source.onmessage = (e) => {
  const msg = JSON.parse(e.data);
  if (msg.type !== 'heartbeat') render(msg);
};
source.onerror = () => {
  source.close();
  setInterval(() => fetch('/api/file-list').then((r) => r.json()).then(render).catch(() => {}), 1000);
};
