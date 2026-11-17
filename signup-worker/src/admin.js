/* Sign-up admin for biruniq.com (2026-11-17).
 *
 * GET  /admin                    the sign-ups page (HTML, same origin)
 * GET  /api/admin/signups        newest first, up to 500, with which are new since this viewer last looked
 * POST /api/admin/seen           marks everything up to now as seen for this viewer
 * GET  /api/admin/summary        { total, new, last_at } for BirunIQ's Admin (server to server)
 *
 * Who may call (fails closed: with neither configured, every call is refused):
 *   1. A person through Cloudflare Access: the request carries Cf-Access-Jwt-Assertion, verified here
 *      (RS256 against the team's certs, audience ACCESS_AUD, issuer https://<ACCESS_TEAM>.cloudflareaccess.com,
 *      not expired) and the email must be in ADMIN_EMAILS (comma-separated). Access in front of /admin*
 *      is the first lock; this check is the second, so a mis-scoped Access policy still fails closed.
 *   2. A server holding ADMIN_API_KEY as a Bearer token (BirunIQ's API). It may read the summary and the
 *      list; its "seen" mark is kept separately under the viewer "api".
 * Nothing here sets CORS headers, so no other website can read these responses in a browser.
 */
const enc = new TextEncoder();
let certCache = { at: 0, keys: [] };

const noStore = { "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff", "Referrer-Policy": "no-referrer" };
const jsonOut = (body, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json", ...noStore } });

function b64urlBytes(s) {
  const b = atob(s.replace(/-/g, "+").replace(/_/g, "/") + "===".slice((s.length + 3) % 4));
  return Uint8Array.from(b, (c) => c.charCodeAt(0));
}

function sameBytes(a, b) {
  const x = enc.encode(a), y = enc.encode(b);
  let d = x.length ^ y.length;
  for (let i = 0; i < Math.max(x.length, y.length); i++) d |= (x[i] || 0) ^ (y[i] || 0);
  return d === 0;
}

async function accessKeys(team) {
  if (Date.now() - certCache.at < 3600_000 && certCache.keys.length) return certCache.keys;
  const r = await fetch(`https://${team}.cloudflareaccess.com/cdn-cgi/access/certs`);
  if (!r.ok) throw new Error(`certs ${r.status}`);
  const j = await r.json();
  certCache = { at: Date.now(), keys: j.keys || [] };
  return certCache.keys;
}

/** The Access email, or null. Never throws. */
async function accessEmail(req, env) {
  const tok = req.headers.get("Cf-Access-Jwt-Assertion");
  if (!tok || !env.ACCESS_TEAM || !env.ACCESS_AUD) return null;
  try {
    const [h64, p64, s64] = tok.split(".");
    const head = JSON.parse(new TextDecoder().decode(b64urlBytes(h64)));
    const pay = JSON.parse(new TextDecoder().decode(b64urlBytes(p64)));
    if (head.alg !== "RS256") return null;
    const jwk = (await accessKeys(env.ACCESS_TEAM)).find((k) => k.kid === head.kid);
    if (!jwk) return null;
    const key = await crypto.subtle.importKey("jwk", jwk, { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["verify"]);
    const ok = await crypto.subtle.verify("RSASSA-PKCS1-v1_5", key, b64urlBytes(s64), enc.encode(`${h64}.${p64}`));
    if (!ok) return null;
    const now = Math.floor(Date.now() / 1000);
    const aud = Array.isArray(pay.aud) ? pay.aud : [pay.aud];
    if (!aud.includes(env.ACCESS_AUD)) return null;
    if (pay.iss !== `https://${env.ACCESS_TEAM}.cloudflareaccess.com`) return null;
    if (!pay.exp || pay.exp < now) return null;
    const email = String(pay.email || "").toLowerCase();
    const allowed = String(env.ADMIN_EMAILS || "").toLowerCase().split(",").map((s) => s.trim()).filter(Boolean);
    return allowed.includes(email) ? email : null;
  } catch (e) {
    console.log(`access check failed: ${e && e.message}`);
    return null;
  }
}

/** "person:<email>", "api", or null. */
export async function adminViewer(req, env) {
  const email = await accessEmail(req, env);
  if (email) return `person:${email}`;
  const auth = req.headers.get("Authorization") || "";
  if (env.ADMIN_API_KEY && env.ADMIN_API_KEY.length >= 32 && auth.startsWith("Bearer ") && sameBytes(auth.slice(7), env.ADMIN_API_KEY)) return "api";
  return null;
}

async function seenAt(env, who) {
  await env.DB.prepare("CREATE TABLE IF NOT EXISTS admin_seen (who TEXT PRIMARY KEY, seen_at TEXT NOT NULL)").run();
  const row = await env.DB.prepare("SELECT seen_at FROM admin_seen WHERE who = ?").bind(who).first();
  return row ? row.seen_at : "";
}

export async function handleAdmin(req, env, url) {
  const p = url.pathname;
  if (!(p === "/admin" || p.startsWith("/api/admin/"))) return null;
  const who = await adminViewer(req, env);
  if (!who) {
    const configured = (env.ACCESS_TEAM && env.ACCESS_AUD && env.ADMIN_EMAILS) || env.ADMIN_API_KEY;
    return jsonOut({ ok: false, error: configured ? "not allowed" : "sign-up admin is not configured" }, configured ? 403 : 503);
  }
  if (p === "/admin" && req.method === "GET" && who.startsWith("person:")) {
    return new Response(PAGE, { headers: { "Content-Type": "text/html; charset=utf-8", "Content-Security-Policy": "default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; frame-ancestors 'none'", ...noStore } });
  }
  const seen = await seenAt(env, who);
  if (p === "/api/admin/summary" && req.method === "GET") {
    const r = await env.DB.prepare("SELECT COUNT(*) AS total, SUM(CASE WHEN created_at > ? THEN 1 ELSE 0 END) AS fresh, MAX(created_at) AS last_at FROM signups").bind(seen).first();
    return jsonOut({ ok: true, total: r.total || 0, new: r.fresh || 0, last_at: r.last_at || null, seen_at: seen || null });
  }
  if (p === "/api/admin/signups" && req.method === "GET") {
    const { results } = await env.DB.prepare(
      "SELECT id, created_at, name, email, organisation, role, country, interests, message, page FROM signups ORDER BY created_at DESC LIMIT 500"
    ).all();
    const rows = results.map((r) => ({ ...r, interests: (() => { try { return JSON.parse(r.interests || "[]"); } catch (_) { return []; } })(), is_new: r.created_at > seen }));
    return jsonOut({ ok: true, viewer: who.replace(/^person:/, ""), seen_at: seen || null, signups: rows });
  }
  if (p === "/api/admin/seen" && req.method === "POST") {
    const now = new Date().toISOString();
    await env.DB.prepare("INSERT INTO admin_seen (who, seen_at) VALUES (?, ?) ON CONFLICT(who) DO UPDATE SET seen_at = excluded.seen_at").bind(who, now).run();
    return jsonOut({ ok: true, seen_at: now });
  }
  return jsonOut({ ok: false, error: "not found" }, 404);
}

const PAGE = `<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sign-ups · BirunIQ</title><meta name="robots" content="noindex">
<style>
:root{--bg:#0A1E38;--card:#102A54;--ink:#F2EFE6;--mut:#B5BFD0;--line:#24406E;--brass:#E3B733;color-scheme:dark}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
.wrap{max-width:1100px;margin:0 auto;padding:24px max(16px,env(safe-area-inset-left)) 48px}
h1{font-size:1.4rem;margin:0}h1 b{color:var(--brass)}.sub{color:var(--mut);margin:4px 0 18px}
.bar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-bottom:14px}
.pill{border:1px solid var(--line);border-radius:999px;padding:4px 12px;font-size:.85rem}.pill.new{border-color:var(--brass);color:var(--brass)}
button{font:600 .85rem system-ui;border-radius:999px;border:1px solid var(--line);background:var(--card);color:var(--ink);padding:6px 14px;cursor:pointer}
button:hover{border-color:var(--brass)}input{font:inherit;padding:8px 10px;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--ink);min-width:220px}
.tbl{overflow-x:auto;border:1px solid var(--line);border-radius:12px}table{width:100%;border-collapse:collapse;font-size:.9rem}
th,td{text-align:left;padding:10px 12px;border-bottom:1px solid var(--line);vertical-align:top}th{font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;color:var(--mut)}
tr.new td:first-child{box-shadow:inset 3px 0 0 var(--brass)}.tag{color:var(--brass);font-weight:700;font-size:.72rem;margin-left:6px}
.mut{color:var(--mut);font-size:.82rem}.msg{max-width:36ch;white-space:pre-wrap}a{color:#8DB8EC}
</style></head><body><div class="wrap">
<h1>Birun<b>IQ</b> sign-ups</h1><p class="sub" id="sub">Loading…</p>
<div class="bar"><span class="pill" id="total"></span><span class="pill new" id="fresh"></span><input id="q" type="search" placeholder="Search name, email, organisation" aria-label="Search"><button id="seen" type="button">Mark all as seen</button></div>
<div class="tbl"><table><thead><tr><th>When (UTC)</th><th>Name</th><th>Organisation · role</th><th>Email</th><th>Country</th><th>Interests</th><th>Message</th><th>Page</th></tr></thead><tbody id="rows"></tbody></table></div>
</div><script>
const e=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
let data=[],q="";
function draw(){const ql=q.toLowerCase();const rows=data.filter(r=>!ql||(r.name+" "+r.email+" "+r.organisation).toLowerCase().includes(ql));
document.getElementById("rows").innerHTML=rows.map(r=>'<tr class="'+(r.is_new?"new":"")+'"><td>'+e(r.created_at.replace("T"," ").slice(0,16))+(r.is_new?'<span class="tag">NEW</span>':"")+'</td><td>'+e(r.name)+'</td><td>'+e(r.organisation)+(r.role?'<div class="mut">'+e(r.role)+'</div>':"")+'</td><td>'+e(r.email)+'</td><td>'+e(r.country)+'</td><td class="mut">'+e((r.interests||[]).join(", "))+'</td><td class="msg">'+e(r.message)+'</td><td class="mut">'+e((r.page||"").replace(/^https?:\\/\\/(www\\.)?biruniq\\.com/,""))+'</td></tr>').join("")||'<tr><td colspan="8" class="mut">No sign-ups match.</td></tr>';}
async function load(){const r=await fetch("/api/admin/signups",{credentials:"same-origin"});const j=await r.json();if(!j.ok){document.getElementById("sub").textContent="Not allowed: "+(j.error||r.status);return;}
data=j.signups;const n=data.filter(x=>x.is_new).length;document.getElementById("total").textContent=data.length+" sign-ups";document.getElementById("fresh").textContent=n+" new since your last visit";
document.getElementById("sub").textContent="Signed in as "+j.viewer+(j.seen_at?" · last marked seen "+j.seen_at.replace("T"," ").slice(0,16)+" UTC":"");draw();}
document.getElementById("q").addEventListener("input",ev=>{q=ev.target.value;draw();});
document.getElementById("seen").addEventListener("click",async()=>{await fetch("/api/admin/seen",{method:"POST",credentials:"same-origin"});load();});
load();
</script></body></html>`;
