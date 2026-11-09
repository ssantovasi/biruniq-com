/* biruniq.com v2 — motion. No libraries, no external requests.
   The YouTube player is created only after the visitor presses play. */
(() => {
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];

  /* ── header: solid on scroll, mobile menu ─────────────────────────── */
  const hdr = $(".hdr");
  const onScroll = () => {
    hdr && hdr.classList.toggle("solid", scrollY > 24);
    const h = innerHeight || 1;
    document.documentElement.style.setProperty("--sy", Math.min(1, scrollY / h).toFixed(3));
  };
  addEventListener("scroll", onScroll, { passive: true }); onScroll();
  const mb = $(".menu-btn"), nav = $(".nav");
  if (mb && nav) mb.addEventListener("click", () => {
    const open = nav.classList.toggle("open");
    mb.setAttribute("aria-expanded", open); mb.textContent = open ? "Close" : "Menu";
  });

  /* ── starfield ────────────────────────────────────────────────────── */
  const cv = $("#stars");
  if (cv) {
    const ctx = cv.getContext("2d");
    let W, H, stars = [], dpr = Math.min(2, devicePixelRatio || 1);
    const seed = (n => () => (n = (n * 16807) % 2147483647) / 2147483647)(73);
    const size = () => {
      W = cv.width = innerWidth * dpr; H = cv.height = innerHeight * dpr;
      const n = Math.round((innerWidth * innerHeight) / 5200);
      stars = Array.from({ length: n }, () => ({
        x: seed() * W, y: seed() * H, r: (seed() ** 3 * 1.4 + .25) * dpr,
        a: seed() * .7 + .15, p: seed() * Math.PI * 2, s: seed() * .9 + .2, z: seed() * .6 + .2,
      }));
    };
    size(); addEventListener("resize", size);
    let t0 = performance.now();
    const draw = (t) => {
      const dt = (t - t0) / 1000; ctx.clearRect(0, 0, W, H);
      const off = (scrollY * dpr);
      for (const s of stars) {
        const tw = reduce ? 1 : .65 + .35 * Math.sin(dt * s.s + s.p);
        let y = (s.y - off * s.z * .25) % H; if (y < 0) y += H;
        ctx.globalAlpha = s.a * tw;
        ctx.fillStyle = s.r > 1.4 * dpr ? "#dcefff" : "#f7f5ef";
        ctx.beginPath(); ctx.arc(s.x, y, s.r, 0, 6.283); ctx.fill();
      }
      ctx.globalAlpha = 1;
      if (!reduce) requestAnimationFrame(draw);
    };
    requestAnimationFrame(draw);
    if (reduce) addEventListener("scroll", () => requestAnimationFrame(draw), { passive: true });
  }

  /* ── split headings into words for the rise animation ─────────────── */
  $$(".split").forEach(el => {
    const walk = (node) => {
      [...node.childNodes].forEach(n => {
        if (n.nodeType === 3) {
          const frag = document.createDocumentFragment();
          n.textContent.split(/(\s+)/).forEach(w => {
            if (!w) return;
            if (/^\s+$/.test(w)) { frag.append(w); return; }
            const o = document.createElement("span"); o.className = "w";
            const i = document.createElement("span"); i.textContent = w; o.append(i); frag.append(o);
          });
          n.replaceWith(frag);
        } else if (n.nodeType === 1 && !n.classList.contains("tm")) walk(n);
      });
    };
    walk(el);
    $$(".w > span", el).forEach((s, k) => s.style.transitionDelay = (k * 45) + "ms");
  });

  /* ── reveal on scroll ─────────────────────────────────────────────── */
  const io = new IntersectionObserver((es) => es.forEach(e => {
    if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
  }), { rootMargin: "0px 0px -8% 0px", threshold: .08 });
  $$(".rv,.split").forEach(el => io.observe(el));

  /* ── counters ─────────────────────────────────────────────────────── */
  const co = new IntersectionObserver((es) => es.forEach(e => {
    if (!e.isIntersecting) return; co.unobserve(e.target);
    const el = e.target, to = +el.dataset.count, dur = 1600, t0 = performance.now();
    if (reduce) { el.textContent = to; return; }
    const step = (t) => {
      const k = Math.min(1, (t - t0) / dur), v = Math.round(to * (1 - Math.pow(1 - k, 4)));
      el.textContent = v; if (k < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }), { threshold: .4 });
  $$("[data-count]").forEach(el => { el.textContent = "0"; co.observe(el); });

  /* ── videos: play only while visible ──────────────────────────────── */
  const vo = new IntersectionObserver((es) => es.forEach(e => {
    const v = e.target;
    if (e.isIntersecting) {
      if (!v.src && v.dataset.src) { v.src = v.dataset.src; v.load(); }
      if (!reduce && v.dataset.auto !== "hover") v.play().catch(() => {});
    } else v.pause();
  }), { threshold: .2 });
  $$("video[data-src]").forEach(v => {
    v.muted = true; v.playsInline = true; v.loop = true;
    v.addEventListener("canplay", () => v.classList.add("ready"), { once: true });
    vo.observe(v);
  });
  // edition cards: video plays on hover
  $$(".ed-card").forEach(c => {
    const v = $("video", c); if (!v) return;
    c.addEventListener("mouseenter", () => { if (!v.src) { v.src = v.dataset.src; } if (!reduce) v.play().catch(() => {}); });
    c.addEventListener("mouseleave", () => v.pause());
  });

  /* ── card spotlight ───────────────────────────────────────────────── */
  $$(".card").forEach(c => c.addEventListener("pointermove", (e) => {
    const r = c.getBoundingClientRect();
    c.style.setProperty("--mx", (e.clientX - r.left) + "px"); c.style.setProperty("--my", (e.clientY - r.top) + "px");
  }));

  /* ── reel: switch the stage as each group scrolls through ─────────── */
  const stage = $(".reel-stage");
  if (stage) {
    const vids = $$(".vid", stage), items = $$(".reel-item");
    const show = (k) => {
      items.forEach((it, i) => it.classList.toggle("on", i === k));
      vids.forEach((v, i) => {
        v.classList.toggle("on", i === k);
        const el = $("video", v); if (!el) return;
        if (i === k) { if (!el.src) el.src = el.dataset.src; if (!reduce) el.play().catch(() => {}); } else el.pause();
      });
    };
    const ro = new IntersectionObserver((es) => es.forEach(e => {
      if (e.isIntersecting) show(items.indexOf(e.target));
    }), { rootMargin: "-45% 0px -45% 0px" });
    items.forEach(it => ro.observe(it));
    show(0);
  }

  /* the trailer gate and the sign-up form live in signup.js */
})();
