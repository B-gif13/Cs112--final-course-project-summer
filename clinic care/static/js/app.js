/* =========================================================
   ClinicCare-Lite — Shared frontend behavior
   ========================================================= */

/**
 * Wires up a drag-and-drop + click-to-browse upload dropzone.
 * Client-side extension/size checks are UX only — Naeem's backend
 * must re-validate on submit (never trust the client).
 */
function initUploadDropzone(opts) {
  const dropzone = document.getElementById(opts.dropzoneId);
  const fileInput = document.getElementById(opts.fileInputId);
  const chipContainer = document.getElementById(opts.chipContainerId);
  const textEl = document.getElementById(opts.textId);
  const errorEl = document.getElementById(opts.errorId);
  if (!dropzone || !fileInput) return;

  const maxBytes = (opts.maxSizeMB || 10) * 1024 * 1024;

  function showError(msg) {
    if (!errorEl) return;
    errorEl.textContent = msg;
    errorEl.style.display = msg ? 'block' : 'none';
  }

  function validExtension(name) {
    const lower = name.toLowerCase();
    return opts.acceptedExtensions.some(ext => lower.endsWith(ext));
  }

  function renderFile(file) {
    showError('');
    if (!validExtension(file.name)) {
      showError(`"${file.name}" isn't an accepted file type. Use ${opts.acceptedExtensions.join(', ')}.`);
      fileInput.value = '';
      chipContainer.innerHTML = '';
      return;
    }
    if (file.size > maxBytes) {
      showError(`"${file.name}" is too large. Max size is ${opts.maxSizeMB}MB.`);
      fileInput.value = '';
      chipContainer.innerHTML = '';
      return;
    }
    textEl.style.display = 'none';
    const sizeKb = Math.round(file.size / 1024);
    chipContainer.innerHTML = `
      <div class="file-chip">
        📎 ${file.name} (${sizeKb} KB)
        <span class="remove" data-role="remove-file">✕</span>
      </div>`;
    chipContainer.querySelector('[data-role="remove-file"]').addEventListener('click', (e) => {
      e.stopPropagation();
      fileInput.value = '';
      chipContainer.innerHTML = '';
      textEl.style.display = 'block';
    });
  }

  dropzone.addEventListener('click', () => fileInput.click());
  dropzone.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); fileInput.click(); }
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files.length) renderFile(fileInput.files[0]);
  });

  ['dragenter', 'dragover'].forEach(evt =>
    dropzone.addEventListener(evt, (e) => { e.preventDefault(); dropzone.classList.add('dragover'); })
  );
  ['dragleave', 'drop'].forEach(evt =>
    dropzone.addEventListener(evt, (e) => { e.preventDefault(); dropzone.classList.remove('dragover'); })
  );
  dropzone.addEventListener('drop', (e) => {
    const file = e.dataTransfer.files[0];
    if (!file) return;
    const dt = new DataTransfer();
    dt.items.add(file);
    fileInput.files = dt.files;
    renderFile(file);
  });
}

/** Keeps the message thread scrolled to the latest message on load. */
function scrollMessagesToBottom(scrollElId) {
  const el = document.getElementById(scrollElId);
  if (el) el.scrollTop = el.scrollHeight;
}

/**
 * Optional: poll the current messages page for new messages without a full
 * reload. Only activate this once Naeem exposes a JSON endpoint, e.g.
 * GET /api/threads/<id>/messages — left here as a ready-to-wire stub.
 */
function pollThread(threadId, endpointBuilder, intervalMs = 4000) {
  if (!threadId) return;
  setInterval(async () => {
    try {
      const res = await fetch(endpointBuilder(threadId));
      if (!res.ok) return;
      const data = await res.json();
      // TODO: diff against current DOM and append only new messages.
      console.debug('poll tick', data);
    } catch (err) {
      console.error('Message poll failed', err);
    }
  }, intervalMs);
}
