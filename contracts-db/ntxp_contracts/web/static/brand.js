// NTXP-DOC-STANDARD 2.1: the look is fixed (tokens live in styles.css), so brand.js no longer repaints colours
// or fonts from whatever brand skill happens to be installed. It only (a) mounts the Document Engine's own
// reversed logo from /assets — fixed 1.55in zone, 0.82in tall, never recoloured — and (b) fills the date.
// If the logo asset is missing we draw NO substitute mark: text alternative only, plus a console note.
(function () {
  const zone = document.getElementById('logo');
  if (zone) {
    const img = new Image();
    img.alt = 'NTXP LLC General Contractors';
    img.src = '/assets/ntxp_logo_reversed.png';
    img.onload = () => { window.__logo = true; zone.appendChild(img); };
    img.onerror = () => {
      window.__logo = false;
      const t = document.createElement('span'); t.className = 'sr'; t.textContent = img.alt; zone.appendChild(t);
      console.warn('NTXP logo asset missing: set NTXP_ASSETS_DIR to a folder holding ntxp_logo_reversed.png');
    };
  }
  // Dark is the default (same deep-navy base); a toggle in the band switches to the light engine look.
  const acct = document.querySelector('.acct');
  if (acct) {
    const b = document.createElement('button');
    b.type = 'button'; b.className = 'theme'; b.id = 'theme';
    const paint = () => {
      const dark = document.documentElement.getAttribute('data-theme') !== 'light';
      b.textContent = dark ? 'Light mode' : 'Dark mode';
      b.setAttribute('aria-pressed', String(dark)); b.setAttribute('aria-label', dark ? 'Switch to light mode' : 'Switch to dark mode');
    };
    b.addEventListener('click', () => {
      const next = document.documentElement.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
      document.documentElement.setAttribute('data-theme', next);
      try { localStorage.setItem('ntxp.theme', next); } catch (e) { /* private mode */ }
      paint();
    });
    paint(); acct.appendChild(b);
  }
  const d = document.getElementById('tagD');
  if (d) d.textContent = new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
})();
