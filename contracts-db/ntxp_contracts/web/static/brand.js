// Pull the live brand (resolved from the newest brand skill in Claude's
// settings on every request) and paint it onto CSS variables. Shared by both
// the dashboard and the profile screen so a brand-skill change shows up
// everywhere on next load — nothing is hard-coded.
async function applyBrand() {
  let brand;
  try {
    brand = await (await fetch('/api/branding')).json();
  } catch (e) {
    return; // CSS defaults already cover this
  }
  const root = document.documentElement.style;
  const c = brand.colors || {};
  Object.entries(c).forEach(([k, v]) => root.setProperty('--' + k, v));
  const f = brand.fonts || {};
  if (f.heading) root.setProperty('--font-heading', f.heading);
  if (f.body) root.setProperty('--font-body', f.body);

  // Brand name + logo in the top bar, when present.
  document.querySelectorAll('[data-brand-name]').forEach(el => {
    el.textContent = (brand.name || 'NTXP');
  });
  if (brand.logo) {
    document.querySelectorAll('[data-brand-logo]').forEach(img => {
      img.src = brand.logo; img.style.display = 'block';
    });
  }
  window.__brand = brand;
}
applyBrand();
