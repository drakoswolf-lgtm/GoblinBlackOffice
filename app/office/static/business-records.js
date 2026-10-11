/* Keep record creation contextual without a separate wizard or modal. */
(() => {
  const allowed = new Set(["#add-client", "#add-project"]);
  const reveal = (hash) => {
    if (!allowed.has(hash)) return;
    const panel = document.querySelector(hash);
    if (panel instanceof HTMLDetailsElement) panel.open = true;
  };
  for (const link of document.querySelectorAll('a[href="#add-client"],a[href="#add-project"]')) {
    link.addEventListener("click", () => reveal(link.getAttribute("href")));
  }
  reveal(window.location.hash);
  window.addEventListener("hashchange", () => reveal(window.location.hash));
})();
