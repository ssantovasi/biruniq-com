/* biruniq.com sign-up endpoint (Cloudflare Worker), 2026-11-08.
 *
 * POST /api/signup  JSON {name, email, organisation, role, country, interests[], message, consent, website}
 *   -> stores the sign-up in D1, emails a notification to NOTIFY_TO through
 *      Resend (from no-reply@biruniq.com), sends the visitor a confirmation with
 *      the trailer link, and returns { ok: true, video: VIDEO_ID }.
 *
 * The trailer's id is a Worker secret (VIDEO_ID), so it is in neither the page source nor the repo.
 * The gate is still soft: anyone who already has the YouTube link can watch.
 *
 * Abuse controls:
 * - a honeypot field ("website") that people never fill;
 * - a per-IP limit (5 an hour), counted in D1 from a salted hash, never the raw IP;
 * - strict field lengths;
 * - CORS limited to the site's origins.
 */
const ORIGINS = ["https://biruniq.com", "https://www.biruniq.com"];
const MAX = { name: 120, email: 200, organisation: 160, role: 120, country: 80, message: 2000, interest: 40 };

function cors(origin) {
  const ok = ORIGINS.includes(origin) || /^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/.test(origin || "");
  return {
    "Access-Control-Allow-Origin": ok ? origin : ORIGINS[0],
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "86400",
    "Vary": "Origin",
  };
}

const json = (body, status, origin) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json", ...cors(origin) } });

const clean = (v, n) => String(v ?? "").replace(/[\u0000-\u001f\u007f]/g, " ").trim().slice(0, n);
const esc = (s) => s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

async function sha256(s) {
  const d = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
  return [...new Uint8Array(d)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

async function send(env, to, subject, html, replyTo) {
  if (!env.RESEND_API_KEY) { console.log("mail skipped: no RESEND_API_KEY"); return false; }
  const r = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: { Authorization: `Bearer ${env.RESEND_API_KEY}`, "Content-Type": "application/json" },
    body: JSON.stringify({ from: env.MAIL_FROM, to: [to], subject, html, ...(replyTo ? { reply_to: replyTo } : {}) }),
  });
  // Logged for `wrangler tail`; the visitor's sign-up never fails on mail.
  console.log(`resend ${r.status} for "${subject.slice(0, 40)}": ${(await r.text()).slice(0, 300)}`);
  return r.ok;
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    const origin = req.headers.get("Origin") || "";
    if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: cors(origin) });
    if (url.pathname !== "/api/signup" || req.method !== "POST") return json({ ok: false, error: "not found" }, 404, origin);

    let b;
    try { b = await req.json(); } catch { return json({ ok: false, error: "bad request" }, 400, origin); }
    // honeypot: pretend success, store nothing
    if (b.website) return json({ ok: true, video: env.VIDEO_ID }, 200, origin);

    const s = {
      name: clean(b.name, MAX.name),
      email: clean(b.email, MAX.email).toLowerCase(),
      organisation: clean(b.organisation, MAX.organisation),
      role: clean(b.role, MAX.role),
      country: clean(b.country, MAX.country),
      message: clean(b.message, MAX.message),
      interests: (Array.isArray(b.interests) ? b.interests : []).slice(0, 20).map((x) => clean(x, MAX.interest)).filter(Boolean),
      consent: b.consent === true || b.consent === "yes",
    };
    if (!s.name || !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(s.email) || !s.organisation || !s.consent)
      return json({ ok: false, error: "Please give your name, a work email, your organisation, and tick the consent box." }, 422, origin);

    const ip = req.headers.get("CF-Connecting-IP") || "0";
    const ipHash = await sha256(`${env.IP_SALT || "biruniq"}:${ip}`);
    const hour = new Date(Date.now() - 3600e3).toISOString();
    const { n } = await env.DB.prepare("SELECT COUNT(*) AS n FROM signups WHERE ip_hash = ? AND created_at > ?").bind(ipHash, hour).first();
    if (n >= 5) return json({ ok: false, error: "Too many sign-ups from this network. Please try again later." }, 429, origin);

    const now = new Date().toISOString();
    await env.DB.prepare(
      "INSERT INTO signups (created_at, name, email, organisation, role, country, interests, message, consent_text, page, ip_hash, user_agent) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)"
    ).bind(now, s.name, s.email, s.organisation, s.role, s.country, JSON.stringify(s.interests), s.message,
      clean(b.consent_text, 600), clean(b.page, 300), ipHash, clean(req.headers.get("User-Agent"), 300)).run();

    const link = `https://youtu.be/${env.VIDEO_ID}`;
    const rows = [["Name", s.name], ["Email", s.email], ["Organisation", s.organisation], ["Role", s.role], ["Country", s.country],
      ["Interests", s.interests.join(", ")], ["Message", s.message], ["Page", clean(b.page, 300)], ["When", now]]
      .map(([k, v]) => `<tr><td style="padding:4px 12px 4px 0;color:#666">${k}</td><td>${esc(v || "—")}</td></tr>`).join("");
    // Mail failures never fail the sign-up: the row is already stored.
    await Promise.allSettled([
      send(env, env.NOTIFY_TO, `New BirunIQ sign-up: ${s.name}, ${s.organisation}`, `<table>${rows}</table>`, s.email),
      send(env, s.email, "Your BirunIQ trailer link",
        `<p>Hello ${esc(s.name)},</p><p>Thank you for your interest in BirunIQ. Here is the trailer: six minutes inside the running platform.</p>` +
        `<p><a href="${link}">${link}</a></p><p>All data shown is synthetic demonstration data or publicly available data.</p>` +
        `<p>We will be in touch about a briefing. If you did not ask for this, ignore this email; we will not write again unless you reply.</p>` +
        `<p>BirunIQ · Bitruvius, Inc.<br/>Unlock your world.™</p>`),
    ]);
    return json({ ok: true, video: env.VIDEO_ID }, 200, origin);
  },
};
