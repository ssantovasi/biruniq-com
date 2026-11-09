/* Sign-up form and the trailer gate (biruniq.com v2).
   The trailer's YouTube id is not in this site's source: the sign-up endpoint
   returns it. A visitor who has signed up keeps access for the browser session
   (sessionStorage, as the Privacy Policy describes for access flags). */
(() => {
  // Local preview (python -m http.server on 127.0.0.1) talks to `wrangler dev` on :8787.
  const ENDPOINT = /^(127\.0\.0\.1|localhost)$/.test(location.hostname)
    ? "http://127.0.0.1:8787/api/signup" : "https://signup.biruniq.com/api/signup";
  const KEY = "biq_trailer";
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const get = () => { try { return sessionStorage.getItem(KEY); } catch (_) { return null; } };
  const put = (v) => { try { sessionStorage.setItem(KEY, v); } catch (_) {} };

  function player(box, id, start) {
    const f = document.createElement("iframe");
    f.src = `https://www.youtube-nocookie.com/embed/${encodeURIComponent(id)}?autoplay=1&rel=0&modestbranding=1&playsinline=1&start=${start || 0}`;
    f.title = "BirunIQ trailer"; f.allow = "autoplay; encrypted-media; picture-in-picture; fullscreen";
    f.allowFullscreen = true; f.referrerPolicy = "strict-origin-when-cross-origin";
    box.innerHTML = ""; box.append(f); box.classList.add("playing");
  }

  function unlock(id) {
    document.documentElement.classList.add("unlocked");
    $$(".trailer.gated").forEach((box) => {
      box.classList.remove("locked");
      const lbl = $(".gate-label", box); if (lbl) lbl.textContent = "Play the trailer";
      box.dataset.vid = id;
    });
    $$("[data-yt-link]").forEach((a) => { a.href = "https://youtu.be/" + id; a.hidden = false; });
  }

  // Trailer boxes: play if unlocked, otherwise take the visitor to the form.
  $$(".trailer.gated").forEach((box) => {
    const btn = $("button", box); if (!btn) return;
    btn.addEventListener("click", () => {
      if (box.dataset.vid) { player(box, box.dataset.vid, box.dataset.start); return; }
      const form = $("#signup"); if (form) {
        form.scrollIntoView({ behavior: "smooth", block: "start" });
        setTimeout(() => { const n = $("input[name=name]", form); n && n.focus({ preventScroll: true }); }, 600);
      }
    });
  });
  $$("[data-seek]").forEach((a) => a.addEventListener("click", (e) => {
    const box = $(".trailer.gated"); if (!box) return;
    e.preventDefault(); box.dataset.start = a.dataset.seek;
    if (box.dataset.vid) { player(box, box.dataset.vid, a.dataset.seek); box.scrollIntoView({ behavior: "smooth", block: "center" }); }
    else { const f = $("#signup"); f && f.scrollIntoView({ behavior: "smooth", block: "start" }); }
  }));

  const saved = get(); if (saved) unlock(saved);

  // The form
  $$("form.signup").forEach((form) => {
    const status = $(".status", form);
    const say = (m, ok) => { status.textContent = m; status.className = "status " + (ok ? "ok" : "err"); };
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (!form.checkValidity()) { form.reportValidity(); return; }
      const fd = new FormData(form);
      const body = {
        name: fd.get("name"), email: fd.get("email"), organisation: fd.get("organisation"),
        role: fd.get("role"), country: fd.get("country"), message: fd.get("message"),
        interests: fd.getAll("interests"), website: fd.get("website"),
        consent: !!fd.get("consent"), consent_text: ($(".consent-text", form) || {}).textContent || "",
        page: location.href,
      };
      const btn = $("button[type=submit]", form); btn.disabled = true; say("Sending…", true);
      try {
        const r = await fetch(ENDPOINT, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
        const j = await r.json().catch(() => ({}));
        if (!r.ok || !j.ok) throw new Error(j.error || "Sign-up failed");
        put(j.video); unlock(j.video);
        form.classList.add("done");
        say("Thank you. The trailer is unlocked above, and we've emailed you the link.", true);
        const box = $(".trailer.gated");
        if (box) { box.scrollIntoView({ behavior: "smooth", block: "center" }); }
      } catch (err) {
        say((err && err.message && err.message !== "Failed to fetch") ? err.message :
          "Sorry, the sign-up could not be sent. Please email support@biruniq.com.", false);
      } finally { btn.disabled = false; }
    });
  });
})();
