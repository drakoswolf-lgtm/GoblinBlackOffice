(() => {
  const root = document.querySelector('[data-curriculum]');
  if (!root) return;

  const form = root.querySelector('[data-curriculum-form]');
  const screens = [...root.querySelectorAll('[data-screen]')];
  const rail = [...root.querySelectorAll('[data-step-target]')];
  const back = root.querySelector('[data-curriculum-back]');
  const next = root.querySelector('[data-curriculum-next]');
  const deploy = root.querySelector('[data-curriculum-deploy]');
  const progress = root.querySelector('[data-curriculum-progress]');
  const completenessBar = root.querySelector('[data-completeness-bar]');
  const completenessLabel = root.querySelector('[data-completeness-label]');
  const sectionReadout = root.querySelector('[data-section-readout]');
  const line = root.querySelector('[data-aeterna-line]');
  const aeterna = root.querySelector('.aeterna-briefing');
  const operatingModel = root.querySelector('[data-operating-model]');
  const addressBlock = root.querySelector('[data-address-block]');
  const franchiseStatus = root.querySelector('[data-franchise-status]');
  const franchisorField = root.querySelector('[data-franchisor-field]');
  const taxStatus = root.querySelector('[data-tax-status]');
  const gstField = root.querySelector('[data-gst-field]');
  let current = 0;
  let busy = false;

  function setConditionalVisibility() {
    if (addressBlock && operatingModel) {
      const onlineOnly = operatingModel.value === 'Online';
      addressBlock.classList.toggle('is-collapsed', onlineOnly);
    }
    if (franchisorField && franchiseStatus) {
      const relevant = ['Franchisee','Franchisor'].includes(franchiseStatus.value);
      franchisorField.classList.toggle('is-revealed', relevant);
    }
    if (gstField && taxStatus) {
      gstField.classList.toggle('is-revealed', taxStatus.value === 'Registered');
    }
  }

  function validateCurrent() {
    const required = [...screens[current].querySelectorAll('[required]')];
    for (const field of required) {
      if (!field.checkValidity()) {
        field.reportValidity();
        field.focus();
        return false;
      }
    }
    return true;
  }

  function updateUI(index, direction = 1) {
    current = Math.max(0, Math.min(screens.length - 1, index));
    screens.forEach((screen, i) => {
      screen.classList.toggle('is-active', i === current);
      screen.classList.remove('from-left','from-right');
      if (i === current) screen.classList.add(direction > 0 ? 'from-right' : 'from-left');
    });
    rail.forEach((item, i) => {
      item.classList.toggle('is-active', i === current);
      item.classList.toggle('is-complete', i < current);
      item.disabled = i > current;
    });

    const screen = screens[current];
    const pct = Number(screen.dataset.percent || 0);
    progress.style.width = pct + '%';
    completenessBar.style.width = pct + '%';
    completenessLabel.textContent = pct + '%';
    sectionReadout.textContent = String(current + 1).padStart(2,'0') + ' / ' + rail[current].querySelector('.rail-label').textContent.toUpperCase();
    line.textContent = screen.dataset.line || '';
    back.disabled = current === 0;
    next.hidden = current === screens.length - 1;
    deploy.hidden = current !== screens.length - 1;
    aeterna.classList.remove('is-speaking');
    requestAnimationFrame(() => {
      aeterna.classList.add('is-speaking');
      window.setTimeout(() => aeterna.classList.remove('is-speaking'), 850);
    });
  }

  function transitionTo(target) {
    if (busy || target === current) return;
    if (target > current && !validateCurrent()) return;
    busy = true;
    const old = screens[current];
    const direction = target > current ? 1 : -1;
    old.classList.add(direction > 0 ? 'is-leaving-left' : 'is-leaving-right');
    window.setTimeout(() => {
      old.classList.remove('is-leaving-left','is-leaving-right');
      updateUI(target, direction);
      busy = false;
    }, 220);
  }

  next.addEventListener('click', () => transitionTo(current + 1));
  back.addEventListener('click', () => transitionTo(current - 1));
  rail.forEach((item, i) => item.addEventListener('click', () => {
    if (i <= current) transitionTo(i);
  }));

  operatingModel?.addEventListener('change', setConditionalVisibility);
  franchiseStatus?.addEventListener('change', setConditionalVisibility);
  taxStatus?.addEventListener('change', setConditionalVisibility);

  form.addEventListener('submit', (event) => {
    if (!validateCurrent()) event.preventDefault();
    else root.classList.add('is-deploying');
  });

  setConditionalVisibility();
  updateUI(0, 1);
})();
