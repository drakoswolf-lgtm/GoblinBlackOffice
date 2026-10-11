/* Beta Mk.III: shared mobile-safe input rows and in-project document preview. */
(() => {
  document.querySelectorAll('[data-repeatable-rows]').forEach(section => {
    const list = section.querySelector('[data-row-list]');
    const template = section.querySelector('template[data-row-template]');
    const add = section.querySelector('[data-add-row]');
    if (!list || !template || !add) return;
    add.addEventListener('click', () => {
      list.append(template.content.cloneNode(true));
      const added = list.lastElementChild;
      if (added) added.querySelector('input')?.focus();
    });
    list.addEventListener('click', e => {
      const remove = e.target.closest('[data-remove-row]');
      if (!remove) return;
      const row = remove.closest('[data-entry-row]');
      if (!row) return;
      row.remove();
      if (!list.children.length) list.append(template.content.cloneNode(true));
    });
  });

  const dialog = document.querySelector('[data-pdf-dialog]');
  if (dialog && typeof dialog.showModal === 'function') {
    const viewer = dialog.querySelector('[data-pdf-frame]');
    const download = dialog.querySelector('[data-pdf-download]');
    const external = dialog.querySelector('[data-pdf-external]');
    const title = dialog.querySelector('[data-pdf-title]');
    const status = dialog.querySelector('[data-pdf-status]');
    document.querySelectorAll('[data-pdf-preview]').forEach(link => {
      link.addEventListener('click', e => {
        e.preventDefault();
        const url = link.href;
        viewer.src = url;
        external.href = url;
        download.href = url + (url.includes('?') ? '&' : '?') + 'download=1';
        title.textContent = link.dataset.pdfTitle || 'Document preview';
        status.textContent = 'Preview loaded when your browser supports embedded PDFs.';
        dialog.showModal();
      });
    });
    dialog.querySelector('[data-pdf-close]')?.addEventListener('click', () => dialog.close());
    download?.addEventListener('click', () => {
      status.textContent = 'Download requested. Check your browser downloads to confirm it saved.';
    });
    dialog.addEventListener('close', () => { viewer.removeAttribute('src'); });
  }
})();
