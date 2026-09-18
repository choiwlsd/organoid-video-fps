const zone = document.querySelector('#dropzone');
const input = document.querySelector('#file-input');
const results = document.querySelector('#results');
const modal = document.querySelector('#error-modal');
const modalMessage = document.querySelector('#modal-message');
const supportedExtensions = new Set(['avi', 'mp4', 'mov', 'mkv', 'wmv']);
let rows = [];
let isAnalyzing = false;

['dragover', 'drop'].forEach((eventName) =>
  document.addEventListener(eventName, (event) => event.preventDefault(), true),
);

document.querySelector('#browse').addEventListener('click', () => input.click());
zone.addEventListener('click', (event) => {
  if (!isAnalyzing && !event.target.closest('button')) input.click();
});
input.addEventListener('change', (event) => {
  analyzeFiles([...event.target.files]);
  input.value = '';
});
['dragenter', 'dragover'].forEach((eventName) =>
  zone.addEventListener(eventName, () => !isAnalyzing && zone.classList.add('drag')),
);
zone.addEventListener('dragleave', () => zone.classList.remove('drag'));
zone.addEventListener('drop', (event) => {
  zone.classList.remove('drag');
  if (!isAnalyzing) analyzeFiles([...event.dataTransfer.files]);
});
document.querySelector('#clear').addEventListener('click', () => {
  rows = [];
  render();
});
document
  .querySelectorAll('[data-close-modal], #modal-confirm')
  .forEach((button) => button.addEventListener('click', closeModal));

const shutdownButton = document.querySelector('#shutdown-button');
const shutdownModal = document.querySelector('#shutdown-modal');
if (shutdownButton && shutdownModal) {
  shutdownButton.addEventListener('click', openShutdownModal);
  document
    .querySelectorAll('[data-close-shutdown]')
    .forEach((button) => button.addEventListener('click', closeShutdownModal));
  document.querySelector('#shutdown-confirm').addEventListener('click', shutdownProgram);
}

async function analyzeFiles(files) {
  if (isAnalyzing || !files.length) return;
  const accepted = files.filter(isSupported);
  const rejected = files.filter((file) => !isSupported(file));
  if (rejected.length)
    showModal(
      'Unsupported file type',
      `${rejected.map((file) => `<strong>${escapeHtml(file.name)}</strong>`).join('<br>')}<br><br>Supported: AVI, MP4, MOV, MKV, WMV`,
    );
  if (!accepted.length) return;
  const pending = accepted.map((file) => ({ file: file.name, status: 'loading' }));
  rows.push(...pending);
  isAnalyzing = true;
  setLoading(true);
  render();
  document.querySelector('#results-section').scrollIntoView({ behavior: 'smooth', block: 'start' });

  try {
    const formData = new FormData();
    accepted.forEach((file) => formData.append('files', file));
    const response = await fetch('/api/analyze', { method: 'POST', body: formData });
    const data = response.headers.get('content-type')?.includes('application/json')
      ? await response.json()
      : null;
    if (!response.ok) throw new Error(data?.error || `Server returned HTTP ${response.status}.`);
    pending.forEach((item, index) =>
      Object.assign(
        item,
        data.results[index] || errorResult(item.file, 'No analysis result returned.'),
      ),
    );
  } catch (error) {
    pending.forEach((item) =>
      Object.assign(
        item,
        errorResult(item.file, error instanceof Error ? error.message : String(error)),
      ),
    );
  } finally {
    isAnalyzing = false;
    setLoading(false);
    render();
    showAnalysisErrors(pending);
  }
}

function setLoading(active) {
  zone.classList.toggle('analyzing', active);
  zone.setAttribute('aria-busy', String(active));
  input.disabled = active;
  zone.querySelector('.upload-content').hidden = active;
  document.querySelector('#upload-loading').hidden = !active;
}

function render() {
  const complete = rows.filter((item) => item.status !== 'loading');
  setText('#file-count', rows.length);
  setText('#total', rows.length);
  setText('#normal', complete.filter((item) => item.status === 'normal').length);
  setText('#issue', complete.filter((item) => item.status !== 'normal').length);
  document.querySelector('#clear').disabled = !rows.length;
  document.querySelector('#empty').hidden = Boolean(rows.length);
  document.querySelector('#table-wrap').hidden = !rows.length;
  results.innerHTML = rows.map(createRow).join('');
}

function createRow(item) {
  const labels = { normal: 'GOOD', issue: 'WARNING', loading: 'ANALYZING', error: 'ERROR' };
  const notes =
    item.status === 'loading'
      ? '<span class="inline-loader"></span>Analyzing with OpenCV'
      : (item.issues || []).map(escapeHtml).join('<br>') || 'All checks passed';
  return `<tr class="result-row-${item.status}"><td class="file-name">${escapeHtml(item.file)}</td><td><span class="badge status-${item.status}">${labels[item.status]}</span></td><td class="number-cell">${formatNumber(item.fps, 3)}</td><td class="number-cell">${item.frame_count ?? '-'}</td><td class="number-cell">${item.duration_seconds == null ? '-' : `${formatNumber(item.duration_seconds, 3)} s`}</td><td class="number-cell">${item.width && item.height ? `${item.width} × ${item.height}` : '-'}</td><td>${escapeHtml(item.codec || '-')}<small>${item.size_bytes ? formatSize(item.size_bytes) : ''}</small></td><td class="notes">${notes}</td></tr>`;
}

function showAnalysisErrors(items) {
  const errors = items.filter((item) => item.status === 'error');
  if (errors.length)
    showModal(
      'Could not analyze file',
      errors
        .map(
          (item) =>
            `<strong>${escapeHtml(item.file)}</strong><br>${item.issues.map(escapeHtml).join('<br>')}`,
        )
        .join('<hr>'),
    );
}

function showModal(title, message) {
  document.querySelector('#modal-title').textContent = title;
  modalMessage.innerHTML = message;
  modal.hidden = false;
  document.body.classList.add('modal-open');
  document.querySelector('#modal-confirm').focus();
}

function closeModal() {
  modal.hidden = true;
  document.body.classList.remove('modal-open');
}
function setText(selector, value) {
  document.querySelector(selector).textContent = value;
}
function isSupported(file) {
  return supportedExtensions.has(file.name.split('.').pop()?.toLowerCase());
}
function errorResult(file, message) {
  return { file, status: 'error', issues: [message] };
}
function formatNumber(value, digits) {
  return Number.isFinite(Number(value)) ? Number(value).toFixed(digits) : '-';
}
function formatSize(bytes) {
  return bytes < 1048576 ? `${(bytes / 1024).toFixed(0)} KB` : `${(bytes / 1048576).toFixed(1)} MB`;
}
function escapeHtml(value) {
  return String(value ?? '').replace(
    /[&<>'"]/g,
    (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' })[char],
  );
}

function openShutdownModal() {
  shutdownModal.hidden = false;
  document.body.classList.add('modal-open');
  document.querySelector('#shutdown-confirm').focus();
}
function closeShutdownModal() {
  shutdownModal.hidden = true;
  document.body.classList.remove('modal-open');
}
async function shutdownProgram() {
  const response = await fetch('/api/shutdown', { method: 'POST' });
  if (!response.ok) {
    closeShutdownModal();
    showModal('Unable to close program', 'The local program could not be closed.');
    return;
  }
  closeShutdownModal();
  document.body.innerHTML =
    '<main class="restart-screen"><p>PROGRAM CLOSED</p><h1>프로그램을 재시작해주세요.</h1><span>실행 파일을 다시 열면 분석을 재개할 수 있습니다.</span></main>';
  window.setTimeout(() => window.close(), 300);
}
