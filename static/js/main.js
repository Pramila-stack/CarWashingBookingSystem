'use strict';

/* ══════════════════════════════════════════════════════════════════
   SparkleWash · Main JS
   Sections:
     1. Navbar (scroll shadow + hamburger)
     2. Toast auto-dismiss
     3. Car wash animation (drip generator + wheel spin)
     4. Booking summary live update (book_service page)
     5. Global form helpers (date min, confirm cancel)
══════════════════════════════════════════════════════════════════ */

/* ── 1. Navbar ─────────────────────────────────────────────────── */
(function initNavbar() {
  const navbar = document.getElementById('navbar');
  const toggle = document.getElementById('navToggle');
  const links  = document.getElementById('navLinks');
  if (!navbar) return;

  // Scroll shadow
  const onScroll = () => navbar.classList.toggle('scrolled', window.scrollY > 20);
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // Hamburger toggle
  if (toggle && links) {
    toggle.addEventListener('click', () => {
      const open = links.classList.toggle('nav-open');
      toggle.setAttribute('aria-expanded', String(open));
      // Animate hamburger bars
      const bars = toggle.querySelectorAll('span');
      if (open) {
        bars[0].style.cssText = 'transform:translateY(7px) rotate(45deg)';
        bars[1].style.cssText = 'opacity:0';
        bars[2].style.cssText = 'transform:translateY(-7px) rotate(-45deg)';
      } else {
        bars.forEach(b => b.style.cssText = '');
      }
    });

    // Close on outside click
    document.addEventListener('click', e => {
      if (!navbar.contains(e.target)) {
        links.classList.remove('nav-open');
        toggle.querySelectorAll('span').forEach(b => b.style.cssText = '');
      }
    });
  }
})();

/* ── 2. Toast auto-dismiss ─────────────────────────────────────── */
(function initToasts() {
  document.querySelectorAll('.toast').forEach((toast, i) => {
    // Stagger entrance, then auto-remove after 5 s
    setTimeout(() => {
      toast.style.transition = 'opacity .5s ease, transform .5s ease';
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(30px)';
      setTimeout(() => toast.remove(), 500);
    }, 5000 + i * 300);
  });
})();

/* ── 3. Car Wash Animation ─────────────────────────────────────── */
(function initCarAnimation() {
  const container = document.getElementById('dripContainer');
  if (!container) return;

  // Generate realistic drip drops at random positions along the car body
  const DRIP_INTERVAL = 320;   // ms between drops
  const DRIP_LIFETIME = 900;   // ms a drop is visible
  const DRIP_POSITIONS = [
    { x: 22, topPct: 55 }, { x: 55, topPct: 45 }, { x: 88, topPct: 50 },
    { x: 115, topPct: 48 },{ x: 140, topPct: 40 },{ x: 160, topPct: 38 },
    { x: 180, topPct: 40 },{ x: 205, topPct: 46 },{ x: 230, topPct: 52 },
    { x: 258, topPct: 48 },{ x: 290, topPct: 50 },
  ];

  function spawnDrip() {
    const pos   = DRIP_POSITIONS[Math.floor(Math.random() * DRIP_POSITIONS.length)];
    const height = 8 + Math.random() * 18;      // px
    const opacity = 0.45 + Math.random() * 0.45;
    const xJitter = (Math.random() - .5) * 14;  // horizontal variation

    const drip = document.createElement('div');
    drip.className = 'drip';
    Object.assign(drip.style, {
      left:          (pos.x + xJitter) + 'px',
      top:           pos.topPct + '%',
      height:        height + 'px',
      opacity:       String(opacity),
      animationDuration: DRIP_LIFETIME + 'ms',
    });
    container.appendChild(drip);
    setTimeout(() => drip.remove(), DRIP_LIFETIME + 50);
  }

  const dripTimer = setInterval(spawnDrip, DRIP_INTERVAL);

  // Wheel spin — target the two wheel groups by their cx attribute
  const carSvg = document.querySelector('.car-svg');
  if (carSvg) {
    const wheelCenters = carSvg.querySelectorAll('circle[r="24"]');
    wheelCenters.forEach(w => {
      const cx = w.getAttribute('cx');
      const cy = w.getAttribute('cy');
      // Apply rotation animation via inline style
      w.style.transformOrigin = `${cx}px ${cy}px`;
      w.style.animation = 'wheelSpin 1.6s linear infinite';
    });

    // Find spoke lines near wheels and spin them too
    const lines = carSvg.querySelectorAll('line');
    lines.forEach(line => {
      const x1 = parseFloat(line.getAttribute('x1') || 0);
      const y1 = parseFloat(line.getAttribute('y1') || 0);
      // Front wheel spokes (centre ~93,118) and rear (227,118)
      if ((Math.abs(x1 - 93) < 20 && Math.abs(y1 - 118) < 30) ||
          (Math.abs(x1 - 227) < 20 && Math.abs(y1 - 118) < 30)) {
        const cx = Math.abs(x1 - 93) < 20 ? 93 : 227;
        line.style.transformOrigin = `${cx}px 118px`;
        line.style.animation = 'wheelSpin 1.6s linear infinite';
      }
    });
  }

  // Pause animation when tab is hidden (perf)
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      clearInterval(dripTimer);
    }
  });
})();

/* Inject wheelSpin keyframe once */
(function injectWheelSpin() {
  if (document.getElementById('sw-keyframes')) return;
  const style = document.createElement('style');
  style.id = 'sw-keyframes';
  style.textContent = '@keyframes wheelSpin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }';
  document.head.appendChild(style);
})();

/* ── 4. Booking summary live update ────────────────────────────── */
(function initBookingSummary() {
  const pkgSelect  = document.getElementById('id_service_package');
  const dateInput  = document.getElementById('id_appointment_date');
  const vehSelect  = document.getElementById('id_vehicle_type');
  if (!pkgSelect) return;   // not on book_service page

  // Enforce minimum date = today
  if (dateInput) {
    const today = new Date().toISOString().split('T')[0];
    dateInput.setAttribute('min', today);
  }

  const summary  = document.getElementById('bookingSummary');
  const bsName   = document.getElementById('bsName');
  const bsDate   = document.getElementById('bsDate');
  const bsVehicle= document.getElementById('bsVehicle');
  const bsPrice  = document.getElementById('bsPrice');
  const cards    = document.querySelectorAll('.pkg-pick-card');

  function formatDate(val) {
    if (!val) return '—';
    const d = new Date(val + 'T00:00');
    return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' });
  }

  function highlight(id) {
    cards.forEach(c => c.classList.toggle('ppc-active', c.dataset.id === String(id)));
  }

  function refresh() {
    const selOpt = pkgSelect.options[pkgSelect.selectedIndex];
    const hasPackage = selOpt && selOpt.value;

    if (summary) summary.style.display = hasPackage ? 'block' : 'none';
    if (!hasPackage) return;

    const card = [...cards].find(c => c.dataset.id === selOpt.value);
    if (bsName)  bsName.textContent  = selOpt.text;
    if (bsPrice) bsPrice.textContent = card ? '$' + parseFloat(card.dataset.price).toFixed(2) : '—';
    if (bsDate)  bsDate.textContent  = formatDate(dateInput ? dateInput.value : '');
    if (bsVehicle && vehSelect) {
      const vOpt = vehSelect.options[vehSelect.selectedIndex];
      bsVehicle.textContent = vOpt && vOpt.value ? vOpt.text : '—';
    }
    highlight(selOpt.value);
  }

  pkgSelect.addEventListener('change', refresh);
  if (dateInput)  dateInput.addEventListener('change', refresh);
  if (vehSelect)  vehSelect.addEventListener('change', refresh);

  // Clicking a package card sets the select value
  cards.forEach(card => {
    card.addEventListener('click', () => {
      pkgSelect.value = card.dataset.id;
      refresh();
    });
  });

  refresh(); // init on page load
})();

/* ── 5. Global helpers ─────────────────────────────────────────── */

// Cancel-booking confirmation
function confirmCancel() {
  return confirm('Are you sure you want to cancel this booking?');
}

// Animate stat numbers on dashboard (count up)
(function animateStats() {
  const nums = document.querySelectorAll('.stat-num, .kpi-num');
  if (!nums.length || !('IntersectionObserver' in window)) return;

  const obs = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      obs.unobserve(entry.target);
      const el  = entry.target;
      const raw = el.textContent.replace(/[^0-9.]/g, '');
      const end = parseFloat(raw);
      if (!end || end > 99999) return; // skip revenue / large numbers
      const prefix = el.textContent.startsWith('$') ? '$' : '';
      const duration = 800;
      const start  = performance.now();
      const isFloat = raw.includes('.');
      (function tick(now) {
        const progress = Math.min((now - start) / duration, 1);
        const ease = 1 - Math.pow(1 - progress, 3);
        const current = end * ease;
        el.textContent = prefix + (isFloat ? current.toFixed(1) : Math.floor(current));
        if (progress < 1) requestAnimationFrame(tick);
        else el.textContent = prefix + (isFloat ? end.toFixed(1) : end);
      })(start);
    });
  }, { threshold: .3 });

  nums.forEach(n => obs.observe(n));
})();
