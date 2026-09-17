const zone = document.querySelector('#dropzone');
const input = document.querySelector('#file-input');
const results = document.querySelector('#results');
const resultsSection = document.querySelector('#results-section');
const loading = document.querySelector('#upload-loading');
const modal = document.querySelector('#error-modal');
const modalMessage = document.querySelector('#modal-message');
const shutdownModal = document.querySelector('#shutdown-modal');

const supportedExtensions = new Set(['avi', 'mp4', 'mov', 'mkv', 'wmv']);
const isVercelDeployment = window.location.hostname.endsWith('.vercel.app');
const vercelRequestLimit = 4 * 1024 * 1024;

let rows = [];
let activeUploads = 0;


// Always cancel the browser's default file-open behavior.
// The dropzone has its own handler below.
['dragover', 'drop'].forEach((type) => {
  document.addEventListener(
    type,
    (event) => event.preventDefault(),
    true,
  );
});


document.querySelector('#browse').addEventListener('click', () => {
  if (!activeUploads) {
    input.click();
  }
});


input.addEventListener('change', (event) => {
  send([...event.target.files]);
  input.value = '';
});


document.querySelector('#clear').addEventListener('click', () => {
  rows = [];
  render();
});


document
  .querySelectorAll('[data-close-modal], #modal-confirm')
  .forEach((button) => {
    button.addEventListener('click', closeModal);
  });


document.querySelector('#shutdown-button').addEventListener('click', () => {
  shutdownModal.hidden = false;
  document.body.classList.add('modal-open');

  const confirmButton = document.querySelector('#shutdown-confirm');
  confirmButton.disabled = false;
  confirmButton.textContent = '프로그램 종료';
  confirmButton.focus();
});


document
  .querySelectorAll('[data-close-shutdown]')
  .forEach((button) => {
    button.addEventListener('click', closeShutdownModal);
  });


document
  .querySelector('#shutdown-confirm')
  .addEventListener('click', shutdownProgram);


zone.addEventListener('click', (event) => {
  if (!activeUploads && !event.target.closest('button')) {
    input.click();
  }
});


zone.addEventListener('dragenter', (event) => {
  event.preventDefault();

  if (!activeUploads) {
    zone.classList.add('drag');
  }
});


zone.addEventListener('dragover', (event) => {
  event.preventDefault();

  if (!activeUploads) {
    zone.classList.add('drag');
  }
});


zone.addEventListener('dragleave', () => {
  zone.classList.remove('drag');
});


zone.addEventListener('drop', (event) => {
  event.preventDefault();
  zone.classList.remove('drag');

  if (!activeUploads) {
    send([...event.dataTransfer.files]);
  }
});


async function send(files) {
  if (!files.length || activeUploads) {
    return;
  }

  const accepted = files.filter(isSupported);
  const rejected = files.filter((file) => !isSupported(file));

  if (rejected.length) {
    showModal(
      'Unsupported file type',
      `${rejected
        .map((file) => `<strong>${escapeHtml(file.name)}</strong>`)
        .join('<br>')}
      <br><br>
      Supported: AVI, MP4, MOV, MKV, WMV`,
    );
  }

  if (!accepted.length) {
    return;
  }

  if (
    isVercelDeployment &&
    accepted.reduce((total, file) => total + file.size, 0) > vercelRequestLimit
  ) {
    showModal(
      'Upload is too large for Vercel',
      'Vercel Functions accept requests smaller than 4.5 MB. Please analyze this video locally or use a direct-to-storage upload service.',
    );

    return;
  }

  const form = new FormData();

  accepted.forEach((file) => {
    form.append('files', file);
  });

  const pending = accepted.map((file) => ({
    file: file.name,
    status: 'loading',
  }));

  rows.push(...pending);

  activeUploads += 1;

  setLoading(true);
  render();

  resultsSection.scrollIntoView({
    behavior: 'smooth',
    block: 'start',
  });

  try {
    const response = await fetch('/api/analyze', {
      method: 'POST',
      body: form,
    });

    const isJson = response.headers
      .get('content-type')
      ?.includes('application/json');

    const data = isJson
      ? await response.json()
      : null;

    if (!response.ok) {
      const reason =
        data?.error ||
        `Server returned HTTP ${response.status} ${response.statusText}`;

      throw new Error(reason);
    }

    pending.forEach((item, index) => {
      Object.assign(
        item,
        data.results[index] || {
          file: item.file,
          status: 'error',
          issues: ['No analysis result returned.'],
        },
      );
    });
  } catch (error) {
    pending.forEach((item) => {
      Object.assign(item, {
        status: 'error',
        issues: [
          error instanceof Error
            ? error.message
            : String(error),
        ],
      });
    });
  } finally {
    activeUploads -= 1;

    setLoading(activeUploads > 0);
    showAnalysisErrors(pending);
    render();
  }
}


function setLoading(isLoading) {
  zone.classList.toggle('analyzing', isLoading);
  zone.setAttribute('aria-busy', String(isLoading));

  input.disabled = isLoading;
  loading.hidden = !isLoading;

  const uploadContent = zone.querySelector('.upload-content');

  if (uploadContent) {
    uploadContent.hidden = isLoading;
  }
}


function showAnalysisErrors(items) {
  const errors = items.filter((item) => item.status === 'error');

  if (!errors.length) {
    return;
  }

  showModal(
    'Could not analyze file',
    errors
      .map(
        (item) =>
          `<strong>${escapeHtml(item.file)}</strong><br>${
            (item.issues || ['Unknown error.'])
              .map(escapeHtml)
              .join('<br>')
          }`,
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


function closeShutdownModal() {
  shutdownModal.hidden = true;
  document.body.classList.remove('modal-open');
}


async function shutdownProgram() {
  const button = document.querySelector('#shutdown-confirm');

  button.disabled = true;
  button.textContent = '종료 중...';

  try {
    const response = await fetch('/api/shutdown', {
      method: 'POST',
      cache: 'no-store',
    });

    const isJson = response.headers
      .get('content-type')
      ?.includes('application/json');

    const data = isJson
      ? await response.json()
      : null;

    if (!response.ok) {
      throw new Error(
        data?.error ||
        `The program could not be closed. HTTP ${response.status}`,
      );
    }

    closeShutdownModal();
    showRestartScreen();

    // Browsers may refuse window.close() if the tab was not opened by script.
    // The EXE itself will still be terminated by the Flask backend.
    window.setTimeout(() => {
      window.close();
    }, 300);
  } catch (error) {
    closeShutdownModal();

    button.disabled = false;
    button.textContent = '프로그램 종료';

    const message =
      error instanceof Error
        ? error.message
        : String(error);

    showModal(
      'Unable to close program',
      escapeHtml(message),
    );
  }
}


function showRestartScreen() {
  document.body.innerHTML = `
    <main
      style="
        min-height:100vh;
        display:grid;
        place-items:center;
        padding:24px;
        background:#fff;
        font-family:Pretendard Variable,Pretendard,Arial,sans-serif;
        color:#111;
        text-align:center;
      "
    >
      <section style="max-width:420px">
        <p
          style="
            margin:0 0 12px;
            color:#737373;
            font-size:12px;
            font-weight:700;
            letter-spacing:.12em;
          "
        >
          PROGRAM CLOSED
        </p>

        <h1
          style="
            margin:0;
            font-size:32px;
            letter-spacing:-.05em;
          "
        >
          프로그램을 재시작해주세요.
        </h1>

        <p
          style="
            margin:16px 0 0;
            color:#737373;
            font-size:14px;
            line-height:1.7;
          "
        >
          로컬 분석 서버가 종료되었습니다.<br>
          <code>.exe</code> 실행 파일을 더블 클릭하여 다시 접속하세요.
        </p>
      </section>
    </main>
  `;
}


function isSupported(file) {
  const extension = file.name
    .split('.')
    .pop()
    ?.toLowerCase();

  return supportedExtensions.has(extension);
}


function render() {
  const finished = rows.filter(
    (item) => item.status !== 'loading',
  );

  setText('#file-count', rows.length);
  setText('#total', rows.length);

  setText(
    '#normal',
    finished.filter(
      (item) => item.status === 'normal',
    ).length,
  );

  setText(
    '#issue',
    finished.filter(
      (item) => item.status !== 'normal',
    ).length,
  );

  setProperty(
    '#clear',
    'disabled',
    !rows.length,
  );

  setProperty(
    '#empty',
    'hidden',
    Boolean(rows.length),
  );

  setProperty(
    '#table-wrap',
    'hidden',
    !rows.length,
  );

  results.innerHTML = rows
    .map(createRow)
    .join('');
}


function setText(selector, value) {
  const element = document.querySelector(selector);

  if (element) {
    element.textContent = value;
  }
}


function setProperty(selector, property, value) {
  const element = document.querySelector(selector);

  if (element) {
    element[property] = value;
  }
}


function createRow(item) {
  const labels = {
    normal: 'GOOD',
    issue: 'WARNING',
    loading: 'ANALYZING',
    error: 'ERROR',
  };

  const classes = {
    normal: 'status-good',
    issue: 'status-warning',
    loading: 'status-analyzing',
    error: 'status-error',
  };

  const notes =
    item.status === 'loading'
      ? `
        <span class="analysis-status">
          <span class="inline-loader"></span>
          Analyzing with OpenCV
        </span>
      `
      : (
          item.issues || []
        )
          .map(escapeHtml)
          .join('<br>') ||
        'FPS validation passed';

  return `
    <tr class="result-row-${item.status}">
      <td class="file-cell">
        <span class="file-name">
          ${escapeHtml(item.file)}
        </span>
      </td>

      <td>
        <span class="badge ${classes[item.status] || 'status-error'}">
          ${labels[item.status] || 'ERROR'}
        </span>
      </td>

      <td class="number-cell">
        ${number(item.fps, 3)}
      </td>

      <td class="number-cell">
        ${item.frame_count ?? '-'}
      </td>

      <td class="number-cell">
        ${
          item.duration_seconds == null
            ? '-'
            : `${number(item.duration_seconds, 3)} s`
        }
      </td>

      <td class="number-cell">
        ${
          item.width && item.height
            ? `${item.width} x ${item.height}`
            : '-'
        }
      </td>

      <td class="codec-cell">
        <span class="codec">
          ${escapeHtml(item.codec || '-')}
        </span>

        ${
          item.size_bytes
            ? `<small class="file-size">${fileSize(item.size_bytes)}</small>`
            : ''
        }
      </td>

      <td class="notes">
        ${notes}
      </td>
    </tr>
  `;
}


function number(value, digits) {
  const numericValue = Number(value);

  return Number.isFinite(numericValue)
    ? numericValue.toFixed(digits)
    : '-';
}


function fileSize(bytes) {
  return bytes < 1048576
    ? `${(bytes / 1024).toFixed(0)} KB`
    : `${(bytes / 1048576).toFixed(1)} MB`;
}


function escapeHtml(value) {
  return String(value ?? '').replace(
    /[&<>'"]/g,
    (char) =>
      ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        "'": '&#39;',
        '"': '&quot;',
      })[char],
  );
}