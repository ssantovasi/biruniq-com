"""Generate biruniq.com v2 (cinematic site), 2026-11-08.

    python tools/build_site.py

Writes the marketing pages and the 17 edition pages, and re-skins the
hand-maintained pages (legal, contact, SMS terms) by replacing ONLY their
<head> assets, header and footer. Their body text is untouched: the legal
pages are shared word for word with the product site (cartos-Project
website/), and contact.html's SMS consent wording is the carrier-reviewed
proof-of-consent text.

Every product claim on these pages comes from one of:
  - the public teaser's narration (take 6),
    whose script cites a repo source for each line;
  - the module registry (tools/catalog-2026-11-08.json, extracted from
    crates/cartos-core/src/catalog.rs on main 9adacb94);
  - CLAUDE.md non-negotiables (deployment profiles, no telemetry).
Nothing here claims a customer, an accuracy figure or a certification.
"""
import html
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
CAT = json.loads((TOOLS / "catalog-2026-11-08.json").read_text(encoding="utf-8"))
TX = json.loads((TOOLS / "trailer-transcript.json").read_text(encoding="utf-8"))
E = html.escape
TM = '<span class="tm">™</span>'

# ── editions, in the buyer-group order (Steven, 2026-11-02) ────────────────
GROUPS = [
    ("gov", "Government & cities", "The agency's whole picture: city, continent, land."),
    ("safety", "Public safety & crisis", "Watch named places, score the infrastructure, run the incident."),
    ("defence", "Defence & maritime", "The command picture, and what moves at sea without a signal."),
    ("energy", "Utilities & energy", "Networks, storage, generation and the plant itself."),
    ("transport", "Transport & infrastructure", "Airports, roads and bridges, and the projects that build them."),
    ("land", "Land & environment", "Fields, habitat, groundwater and the evidence on the ground."),
]

ED = [
    # slug, catalog id, display name, group, sector line, one-liner, body paragraphs, film lines (start s, text)
    dict(slug="atlas", cat="atlas", name="Atlas", group="gov", sector="Government",
         line="The smart-city and government view.",
         body=["Atlas is the general-government edition. It puts a city's sensors, assets, incidents and responding units on one map: each sensor with its 24-hour trend, each asset with its record.",
               "Maritime traffic sits in the same picture, with every vessel's stored track, and a mapbook can be generated straight from the current view."],
         film=[(256.3, "Atlas is the smart-city view. Sensors with a 24 hour trend, assets, incidents, emergency units."),
               (266.6, "Maritime shows vessels with their stored tracks. And a mapbook can be generated straight from the current view.")]),
    dict(slug="africa", cat="africa", name="One Africa", group="gov", sector="Continental government",
         line="Continental programmes on one map.",
         body=["One Africa carries continental programmes in one place: command, food and agriculture, health and immunisation, borders, ports, land use and land cover, flood and climate risk, and settlements.",
               "In the trailer it runs a port: vessels, terminals and berth occupancy."],
         film=[(281.7, "One Africa runs a port. Vessels, terminals, berth occupancy.")]),
    dict(slug="terra", cat="terra", name="Terra", group="gov", sector="Land administration",
         line="From drone imagery to candidate parcels. Proposals, not titles.",
         body=["Terra turns drone imagery into candidate parcels and puts them in front of a reviewer one at a time, weakest first. Every candidate is a proposal. None of them is a title until a person says so.",
               "BacksightIQ, Terra's record view, shows the land record as a tamper-evident chain."],
         film=[(273.6, "Terra turns drone imagery into candidate parcels, reviewed one at a time. They're proposals. Not titles.")]),
    dict(slug="sentry", cat="sentry", name="Sentry", group="safety", sector="Crisis monitoring",
         line="Named sites, scored, with the reasons behind the score.",
         body=["Sentry watches named sites. Each one gets a risk score and the drivers behind it, so the score can be argued with. Incidents land in a console, and change detection runs alongside.",
               "In the demonstration, scores rest on Guardian's synthetic strike-risk model, and the screen says so."],
         film=[(108.4, "Sentry watches named sites. Each gets a risk score, and the drivers behind it, and incidents land in a console.")]),
    dict(slug="guardian", cat="guardian", name="Guardian", group="safety", sector="Critical-infrastructure protection",
         line="Score the infrastructure itself. Then stand it up in 3D.",
         body=["Guardian scores critical infrastructure directly: energy, utilities and transport, emergency services, defence. Each asset carries its own record and its stored risk score.",
               "In the 3D severity view every asset stands at its stored score. Taller means more severe, so the worst exposure reads from across the room."],
         film=[(115.9, "Guardian scores the infrastructure itself. Starting with energy."),
               (123.6, "Then bridges and tunnels. Four products, one system underneath."),
               (131.4, "Now critical infrastructure. In this view, every asset stands at its stored risk score. Taller means more severe.")]),
    dict(slug="floodsurge", cat="floodsurge", name="FloodSurge", group="safety", sector="Riverine flood",
         line="Critical facilities against the flood zones, the rivers and the forecast.",
         body=["FloodSurge sets critical facilities against FEMA flood zones, then adds modelled streamflow and river gauges with their stage.",
               "The sources are public and named on screen: the FEMA National Flood Hazard Layer, the NOAA National Water Model, the National Water Prediction Service and USGS gauges."],
         film=[(201.2, "FloodSurge sets critical facilities against FEMA flood zones. Then modelled streamflow, and river gauges.")]),
    dict(slug="spilltrace", cat="spilltrace", name="SpillTrace", group="safety", sector="Oil-spill response",
         line="The incident, the slick on every pass, and what lies in its path.",
         body=["SpillTrace records an incident, the slick area seen on each pass, and the receptors in its path. Drift and trajectory, escalation, shoreline survey, response assets and remediation follow from the same record.",
               "Records in the demonstration are synthetic, and each one says so."],
         film=[(193.3, "Environmental. SpillTrace records an incident, the slick area seen on each pass, and the receptors in its path.")]),
    dict(slug="watchfloor", cat="watchfloor", name="WatchFloor", group="defence", sector="Defence decision intelligence",
         line="The command picture. Every protected asset, with its own record.",
         body=["WatchFloor is the command picture: protected assets on one map, each with its own record.",
               "Around it sit the rest of the intelligence cycle: requirements and requests for information, collection management, exploitation, order of battle, the maritime, air and ground pictures, all-source fusion, and production."],
         film=[(91.9, "Start with defence and security. WatchFloor is the command picture. Protected assets on one map, each with its own record.")]),
    dict(slug="maritimelens", cat="maritimelens", name="MaritimeLens", group="defence", sector="Naval patrol",
         line="Dark vessels. And it says so when it can't tell.",
         body=["MaritimeLens flags radar detections that have no matching ship signal. Those are dark vessels. When the evidence can't settle it, the verdict says indeterminate rather than guessing.",
               "Piracy and armed robbery, trafficking, illegal fishing, force protection, patrol tasking, maritime zones and an incident register are part of the same edition."],
         film=[(100.5, "MaritimeLens flags radar detections with no matching ship signal. Dark vessels. And it says so when it can't tell.")]),
    dict(slug="grid", cat="grid", name="Grid", group="energy", sector="Electric utility",
         line="Outages, transformers, transmission. Nine department cockpits.",
         body=["Grid is the electric-utility edition, with nine department cockpits: command, network and asset operations, capital projects, storm response, fleet and field, vegetation, real estate, environmental and stakeholder management.",
               "Grid command shows outages with restoration, transformer records and transmission lines. In network operations assets cluster by count, and open into icons as you zoom."],
         film=[(139.6, "Grid command. Outages, transformer records, transmission lines."),
               (146.9, "Then network operations, where assets cluster by count, and open into icons as you zoom.")]),
    dict(slug="flux", cat="flux", name="Flux", group="energy", sector="Renewable energy",
         line="Storage, generation and corridors, each against its limit.",
         body=["Flux is the renewable-energy edition: storage state of charge, generation against its rating, and transmission corridors against their limits.",
               "Balance and forecast, the guarantee ledger, the operating envelope and revenue against degradation sit in the same edition."],
         film=[(157.2, "Flux. Storage state of charge, generation against its rating, corridors against their limits.")]),
    dict(slug="petrocore", cat="petrocore", name="PetroCore", group="energy", sector="Oil & gas",
         line="Watch the site for change, camera by camera.",
         body=["PetroCore watches a site for change, camera by camera. It flags dark contacts at loading points and process-safety impairments, plant by plant, alongside pipeline integrity, pre-incident plans and inspection reports.",
               "In the demonstration the live operations are simulated, and the screen says so."],
         film=[(164.3, "PetroCore watches a site for change, camera by camera. All of it simulated. The screen says so."),
               (171.5, "Dark contacts at loading points. And process-safety impairments, plant by plant.")]),
    dict(slug="tower", cat="tower", name="Tower", group="transport", sector="Airports",
         line="Airport lighting, surfaces, signage and traffic.",
         body=["Tower is the airport edition. It keeps airfield lighting fixture by fixture with each one's condition, along with surface condition, lane striping, signage, property leases, major projects, emergency services, vehicle and air traffic, and weather."],
         film=[(177.6, "Milepost keeps bridge inspections. Tower keeps airport lighting. Different industries. The same platform.")]),
    dict(slug="milepost", cat="milepost", name="Milepost", group="transport", sector="Departments of transportation",
         line="Bridges, pavement, roadwork and snow.",
         body=["Milepost is the transportation-department edition: bridge and facility inspections, pavement management, lane striping, live traffic, roadwork and obstructions, major projects, crew status, snow removal and emergency response."],
         film=[(177.6, "Milepost keeps bridge inspections. Tower keeps airport lighting. Different industries. The same platform.")]),
    dict(slug="blueprint", cat="blueprint", name="Blueprint", group="transport", sector="Architecture, engineering & construction",
         line="Every project's health, from site selection to inspection.",
         body=["Blueprint tracks construction projects from a portfolio view of project health through design status, site selection, constructability review, environmental and cultural review, construction inspections, safety reporting and stakeholder access."],
         film=[(286.3, "And Blueprint tracks construction projects.")]),
    dict(slug="harvest", cat="harvest", name="Harvest", group="land", sector="Agriculture intelligence",
         line="A crop calendar, a crop index, and field boundaries the model drew.",
         body=["Harvest brings a crop calendar, a crop index from Sentinel-2 satellite imagery, and field boundaries delineated by the model. The boundaries in the trailer are real model output, not demonstration data.",
               "Crop type and land use, crop health, yield forecast, water and drought, the field registry, and risk and finance complete the edition."],
         film=[(231.8, "And Harvest. A crop calendar, a crop index from satellite imagery, and field boundaries the model delineated. Real model output, not demo.")]),
    dict(slug="greenscope", cat="greenscope", name="GreenScope", group="land", sector="Environmental",
         line="Findings with photos, risk by zone, and every monitoring well.",
         body=["GreenScope keeps environmental findings with their inspection photos and risk by zone, alongside permitting, biodiversity and habitat change, and soil intelligence.",
               "Its groundwater view carries over thirteen hundred public monitoring wells, clustered by count. Zoom in and they open into well records, even over satellite imagery."],
         film=[(209.6, "GreenScope. Findings with inspection photos, and risk by zone."),
               (214.9, "Groundwater. Over thirteen hundred monitoring wells, clustered by count. Zoom in, and they open into well records.")]),
]
ED_BY = {e["slug"]: e for e in ED}
for e in ED:
    e["modules"] = [m["label"] for m in CAT[e["cat"]]["modules"]]
N_MODULES, N_INDUSTRIES, N_DEPT, N_CAPS = 133, 17, 130, 30  # update_counts.py --check, main 9adacb94
assert len(ED) == N_INDUSTRIES


# ── chrome ────────────────────────────────────────────────────────────────
DECK = json.loads((TOOLS / "deck-editions.json").read_text(encoding="utf-8"))
NAV = [("platform.html", "Platform"), ("editions.html", "Editions"), ("sovereignty.html", "Sovereignty"),
       ("trailer.html", "Trailer"), ("story.html", "The name")]


def head(title, desc, depth=0, og_img="assets/media/trailer-poster.webp"):
    up = "../" * depth
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}" />
<meta property="og:title" content="{E(title)}" />
<meta property="og:description" content="{E(desc)}" />
<meta property="og:type" content="website" />
<meta property="og:image" content="https://biruniq.com/{og_img}" />
<meta name="theme-color" content="#04080F" />
<link rel="icon" href="{up}assets/favicon.svg" type="image/svg+xml" />
<link rel="stylesheet" href="{up}assets/v2.css" />
<link rel="stylesheet" href="{up}assets/v2b.css" />
<script src="{up}assets/v2.js" defer></script>
<script src="{up}assets/signup.js" defer></script>
</head>"""


def header(active="", depth=0):
    up = "../" * depth
    links = "".join(
        f'<a href="{up}{h}"{" aria-current=\"page\"" if h == active else ""}>{t}</a>' for h, t in NAV)
    return f"""<body>
<a class="skip" href="#main">Skip to content</a>
<canvas id="stars" aria-hidden="true"></canvas>
<header class="hdr"><div class="wrap">
  <a class="logo" href="{up}./" aria-label="BirunIQ home"><img src="{up}assets/brand/biruniq-logo-horizontal-dark.svg" alt="BirunIQ" width="152" height="40" /></a>
  <nav class="nav" aria-label="Main">{links}<a class="btn sm primary" href="{up}trailer.html#signup">Sign up</a></nav>
  <button class="menu-btn" aria-expanded="false" aria-label="Menu">Menu</button>
</div></header>
<div class="page" id="main">"""


def footer(depth=0, earth_credit=False):
    up = "../" * depth
    credit = ('<span>Earth imagery: NASA Earth Observatory, <i>Blue Marble: Next Generation</i>.</span>'
              if earth_credit else "")
    eds = "".join(f'<a href="{up}editions/{e["slug"]}.html">{e["name"]}</a>' for e in ED[:9])
    eds2 = "".join(f'<a href="{up}editions/{e["slug"]}.html">{e["name"]}</a>' for e in ED[9:])
    return f"""</div>
<footer class="ftr"><div class="wrap">
  <div class="top">
    <div class="brand">
      <img src="{up}assets/brand/biruniq-logo-horizontal-dark.svg" alt="BirunIQ" width="168" height="44" />
      <p class="ds">Sovereign spatial intelligence</p>
      <p class="tg">Unlock your world.™</p>
      <p style="margin-top:18px"><a class="btn sm" href="{up}trailer.html#signup">Sign up for updates</a></p>
    </div>
    <div><h4>Platform</h4><nav><a href="{up}platform.html">One platform</a><a href="{up}sovereignty.html">Sovereignty</a><a href="{up}editions.html">All editions</a><a href="{up}trailer.html">Trailer</a><a href="{up}story.html">The name</a><a href="{up}contact.html">Contact</a></nav></div>
    <div><h4>Editions</h4><nav>{eds}</nav></div>
    <div><h4>&nbsp;</h4><nav>{eds2}</nav></div>
  </div>
  <div class="bot">
    <span>© 2026 Bitruvius, Inc. BirunIQ™. Patent pending.</span>
    <nav style="display:flex;gap:16px;flex-wrap:wrap"><a href="{up}about.html">About</a><a href="{up}privacy.html">Privacy</a><a href="{up}terms.html">Terms</a><a href="{up}eula.html">EULA</a><a href="{up}evaluation-terms.html">Evaluation Terms</a><a href="{up}attributions.html">Attributions</a><a href="{up}sms-terms.html">SMS Terms</a></nav>
    {credit}
  </div>
</div></footer>
</body>
</html>
"""


def vid(key, depth=0, label=None):
    up = "../" * depth
    lbl = f'<span class="lbl"><i></i>{E(label)}</span>' if label else ""
    return (f'<video muted loop playsinline preload="none" poster="{up}assets/media/loops/{key}.webp" '
            f'data-src="{up}assets/media/loops/{key}.mp4" aria-hidden="true"></video>{lbl}')


def ts(sec):
    s = int(round(sec)); return f"{s // 60}:{s % 60:02d}"


def trailer_box(depth=0):
    up = "../" * depth
    # No video id in the page: the sign-up endpoint returns it (assets/signup.js).
    return f"""<div class="trailer gated locked rv">
    <img src="{up}assets/media/trailer-poster.webp" alt="BirunIQ trailer: the Earth, the star and al-Biruni's sightline" loading="lazy" width="1600" height="900" />
    <button aria-label="Watch the BirunIQ trailer (sign up first)">
      <span class="pbtn" aria-hidden="true"><svg width="34" height="34" viewBox="0 0 24 24"><path d="M8 5v14l11-7z" fill="currentColor"/></svg></span>
      <span class="gate"><span class="lockico">●</span><span class="gate-label">Sign up to watch</span></span>
      <span class="meta"><b>BirunIQ · the trailer</b><span>6:12 · narrated · seventeen editions</span></span>
      <span class="note">All data shown is synthetic demonstration data or publicly available data.</span>
    </button>
  </div>"""


def signup_section(depth=0, title="Sign up to watch the trailer.", lede=None):
    up = "../" * depth
    lede = lede or ("Tell us who you are and we'll unlock the six-minute trailer right here, email you the link, "
                    "and keep you informed as BirunIQ moves toward general availability.")
    picks = "".join(f'<label><input type="checkbox" name="interests" value="{e["name"]}" /><span>{e["name"]}</span></label>' for e in ED)
    return f"""<section class="sec" id="signup"><div class="wrap signup-wrap">
  <div>
    <span class="eyebrow rv">Sign up</span>
    <h2 class="h2 split" style="margin-top:18px">{title}</h2>
    <p class="lede rv d2" style="margin-top:18px">{lede}</p>
    <div class="perks">
      <div class="rv"><i>01</i><span><b>The trailer, unlocked</b>Six minutes inside the running platform, across all seventeen editions.</span></div>
      <div class="rv d1"><i>02</i><span><b>The link, by email</b>So you can share it with your team.</span></div>
      <div class="rv d2"><i>03</i><span><b>A briefing, if you want one</b>On demonstration data, for the editions your agency runs.</span></div>
    </div>
    <p class="rv d3" style="margin-top:22px"><a class="yt-link" data-yt-link hidden href="#">Open the trailer on YouTube →</a></p>
  </div>
  <form class="signup rv d1" novalidate>
    <div class="row">
      <label>Name<input type="text" name="name" required maxlength="120" autocomplete="name" /></label>
      <label>Work email<input type="email" name="email" required maxlength="200" autocomplete="email" /></label>
    </div>
    <div class="row">
      <label>Organisation<input type="text" name="organisation" required maxlength="160" autocomplete="organization" /></label>
      <label>Role<input type="text" name="role" maxlength="120" autocomplete="organization-title" /></label>
    </div>
    <label>Country<input type="text" name="country" maxlength="80" autocomplete="country-name" /></label>
    <fieldset><legend>Which editions interest you? (optional)</legend><div class="picks">{picks}</div></fieldset>
    <label>Anything you'd like us to know? (optional)<textarea name="message" rows="3" maxlength="2000"></textarea></label>
    <div class="hp" aria-hidden="true"><label>Website<input type="text" name="website" tabindex="-1" autocomplete="off" /></label></div>
    <label class="check"><input type="checkbox" name="consent" required /><span class="consent-text">I agree that Bitruvius, Inc. (BirunIQ) may store these details and email me about BirunIQ, including the trailer link. I can ask to stop at any time. See the <a href="{up}privacy.html">Privacy Policy</a>.</span></label>
    <button class="btn primary" type="submit" style="justify-self:start">Unlock the trailer →</button>
    <p class="status" role="status" aria-live="polite"></p>
  </form>
</div></section>"""


# ── hero construction (al-Biruni's dip-angle diagram over the Earth) ──────
def construction():
    """al-Biruni's construction drawn on the hero Earth, in the Earth image's own
    coordinates (viewBox 0..100, centre 50,50, radius 50/1.12 = 44.64: the render's
    extent). A is the star, T the tangency (computed: A->T is tangent to the
    circle), P the foot of h on the surface along A->C."""
    return """<svg class="construct" viewBox="0 0 100 100" aria-hidden="true">
  <defs><radialGradient id="halo"><stop offset="0" stop-color="#FFE7A3" stop-opacity=".9"/><stop offset=".25" stop-color="#E3B733" stop-opacity=".35"/><stop offset="1" stop-color="#E3B733" stop-opacity="0"/></radialGradient></defs>
  <path class="c-line draw" pathLength="1" d="M94 -10 L37.04 7.28" stroke="#7FD6FF" stroke-width=".32" style="animation-delay:1.1s"/>
  <path class="c-line draw" pathLength="1" d="M37.04 7.28 L23.64 11.34" stroke="#7FD6FF" stroke-width=".18" stroke-opacity=".5" style="animation-delay:2.4s"/>
  <path class="c-line dots" d="M50 50 L37.04 7.28" stroke="#7FD6FF" stroke-width=".18" stroke-dasharray=".25 1.1" style="animation-delay:2.2s"/>
  <path class="c-line dots" d="M94 -10 L76.4 14" stroke="#7FD6FF" stroke-width=".18" stroke-dasharray=".25 1.1" style="animation-delay:2.0s"/>
  <path class="c-line dots" d="M94 -10 L74 -10" stroke="#E3B733" stroke-width=".16" stroke-dasharray=".8 .8" style="animation-delay:2.6s"/>
  <path class="c-line draw" pathLength="1" d="M85 -10 A9 9 0 0 0 85.39 -7.39" stroke="#E3B733" stroke-width=".22" style="animation-delay:2.9s"/>
  <circle class="fade" cx="37.04" cy="7.28" r=".95" fill="#E3B733" style="animation-delay:2s"/>
  <circle class="fade" cx="37.04" cy="7.28" r="2.1" fill="none" stroke="#E3B733" stroke-width=".14" stroke-opacity=".6" style="animation-delay:2.2s"/>
  <circle class="fade" cx="50" cy="50" r=".7" fill="none" stroke="#7FD6FF" stroke-width=".16" style="animation-delay:2.4s"/>
  <text class="fade" x="81.6" y="-10.9" fill="#E3B733" style="animation-delay:3.1s">θ</text>
  <text class="fade" x="33.6" y="5.4" fill="#E3B733" style="animation-delay:2.4s">T</text>
  <text class="fade" x="51.2" y="53.4" fill="#7FD6FF" style="animation-delay:2.6s">C</text>
  <text class="fade" x="86.6" y="3.4" fill="#7FD6FF" style="animation-delay:2.4s">h</text>
  <text class="fade" x="39.4" y="30.2" fill="#7FD6FF" style="animation-delay:2.6s">R</text>
  <text class="fade" x="95.6" y="-11.6" fill="#E3B733" style="animation-delay:1s">A</text>
  <circle class="star-halo" cx="94" cy="-10" r="12" fill="url(#halo)"/>
  <polygon points="94,-13.6 94.85,-10.85 97.6,-10 94.85,-9.15 94,-6.4 93.15,-9.15 90.4,-10 93.15,-10.85" fill="#E3B733"/>
  <circle cx="94" cy="-10" r=".5" fill="#FFF4D0"/>
</svg>"""


def whole_system(depth=0):
    up = "../" * depth
    return f"""<section class="sec"><div class="wrap sun">
  <div class="rv"><img src="{up}assets/media/diagrams/sunburst.svg" alt="The whole system as a sunburst: 17 sectors, 130 department modules, 346 declared tasks and 1,539 feature attachments around one engine" loading="lazy" width="1120" height="1120" /></div>
  <div style="display:grid;gap:22px">
    <span class="eyebrow rv">The whole system</span>
    <h2 class="h2 split">Platform, sector, module, task, feature.</h2>
    <div class="tiers">
      <div class="rv"><b>1</b><p><span>Platform</span>One sovereign engine: {N_CAPS} shared capabilities, one data fabric, one identity, one agent.</p></div>
      <div class="rv d1"><b data-count="17">17</b><p><span>Industry editions</span>A curated catalogue with its own theme, geography and data. All seventeen are live.</p></div>
      <div class="rv d2"><b data-count="130">130</b><p><span>Department modules</span>The unit a department buys and is held accountable for.</p></div>
      <div class="rv d3"><b data-count="346">346</b><p><span>Declared tasks</span>The use-cases a surface is built to answer. Where a module declares none, the ring shows the gap rather than filling it.</p></div>
      <div class="rv d4"><b data-count="1539">1539</b><p><span>Feature attachments</span>Any of the {N_CAPS} shared capabilities can be cross-added to any module.</p></div>
    </div>
    <p class="footnote rv">Every arc is generated from the engine's own catalogue. Nothing in this diagram is drawn by hand.</p>
  </div>
</div></section>"""


def grand_vision(depth=0):
    up = "../" * depth
    return f"""<section class="sec band"><div class="wrap">
  <div class="sec-head"><span class="eyebrow rv">The grand vision</span><h2 class="h2 split">One engine. One analyst. Every sector on it.</h2>
  <p class="lede rv d2">One deployment, one permission model, one audit trail, and departments that never shared data sitting on the same fabric. Seventeen courses laid, FireLens in design, room left to build.</p></div>
  <div class="wide-diagram rv"><div class="scroll-x"><img src="{up}assets/media/diagrams/grandvision.svg" alt="The BirunIQ platform as masonry: one engine, seventeen sector bricks, FireLens in design and room to build, with one analyst spanning all of it" loading="lazy" width="1560" height="566" /></div></div>
  <div class="grid g3" style="margin-top:22px">
    <div class="card rv"><span class="k">For a government</span><h3 class="h3">One system</h3><p>One deployment, one identity, one permission tree, one audit trail. Every sector inherits it; nothing above the engine re-implements what the engine already does.</p></div>
    <div class="card rv d1"><span class="k">It compounds</span><h3 class="h3">The analyst grows with every module</h3><p>A module added to the shared fabric extends what can be asked of all of them, not just of itself.</p></div>
    <div class="card rv d2"><span class="k">Honest by construction</span><h3 class="h3">The empty bricks are the point</h3><p>Each brick is as wide as the departments it ships. The open slots are drawn empty, not filled with names nobody has asked for.</p></div>
  </div>
</div></section>"""


# ── pages ──────────────────────────────────────────────────────────────────
def page_home():
    groups_html = ""
    for i, (gk, gname, gline) in enumerate(GROUPS):
        eds = [e for e in ED if e["group"] == gk]
        chips = "".join(f'<a class="chip" href="editions/{e["slug"]}.html">{e["name"]}</a>' for e in eds)
        groups_html += f"""<div class="reel-item"><span class="k">0{i + 1} / 06</span><h3 class="h3">{gname}</h3><p>{gline}</p><div class="eds">{chips}</div></div>"""
    stage = ""
    for gk, gname, _ in GROUPS:
        lead = [e for e in ED if e["group"] == gk][0]
        stage += (f'<div class="vid"><img class="fallback" src="assets/media/loops/{lead["slug"]}.webp" alt="" loading="lazy" /><video muted loop playsinline preload="none" poster="assets/media/loops/{lead["slug"]}.webp" '
                  f'data-src="assets/media/loops/{lead["slug"]}.mp4" aria-hidden="true"></video>'
                  f'<div class="cap"><b>BirunIQ {lead["name"]}</b><span>From the trailer · demonstration data</span></div></div>')
    marquee = "".join(f"<span>{e['name']}</span>" for e in ED) * 2
    return head("BirunIQ — Sovereign spatial intelligence",
                "One engine. Seventeen industries. 130 department modules. BirunIQ is sovereign, agent-native geospatial intelligence: SaaS, sovereign hybrid, or air-gap capable.") + header() + f"""
<section class="hero">
  <div class="hero-stage" aria-hidden="true">
    <div class="hero-earth"><img src="assets/media/earth-americas.webp" alt="" width="1800" height="1800" fetchpriority="high" />{construction()}</div>
    <div class="hero-veil"></div>
  </div>
  <div class="wrap"><div class="hero-copy">
    <span class="eyebrow rv">One engine · Seventeen industries · 130 department modules</span>
    <h1 class="split tag3"><span class="t">Unlock the evidence.</span> <span class="t">Unlock the answers.</span> <span class="t t3">Unlock your world.{TM}</span></h1>
    <p class="lede rv d3">BirunIQ is sovereign, agent-native geospatial intelligence. One map, one catalog of layers, one sign-in, so an agency, or many departments, can work from the same picture.</p>
    <div class="ctas rv d4"><a class="btn primary" href="#trailer"><span class="play">▶</span> Watch the trailer</a><a class="btn" href="editions.html">Explore the editions</a></div>
  </div></div>
  <div class="scroll-cue" aria-hidden="true"><i></i>Scroll</div>
</section>

<div class="marquee" aria-hidden="true"><div class="track">{marquee}</div></div>

<section class="sec"><div class="wrap">
  <div class="sec-head"><span class="eyebrow rv">The thesis</span><h2 class="display split" style="font-size:clamp(2.4rem,6vw,5.4rem)">From observation to insight, and from insight to <span class="iq">action.</span></h2>
  <p class="lede rv d2">Satellites, sensors, registries and crews in the field already produce more observation than any agency can read. BirunIQ is the layer that turns all of it into decisions an agency can defend, in seventeen industries at once, on one sovereign engine.</p></div>
  <div class="grid g3">
    <div class="card rv"><span class="k">01 · Observe</span><h3 class="h3">Every source, one fabric</h3><p>SAR, optical, thermal and 98 registered external sources, arriving continuously, plus what crews capture in the field.</p></div>
    <div class="card rv d1"><span class="k">02 · Reason</span><h3 class="h3">One analyst</h3><p>An agent that reasons across every source the asking user is entitled to see, and nothing more.</p></div>
    <div class="card rv d2"><span class="k" style="color:var(--brass)">03 · Act</span><h3 class="h3">The deliverable you're held to</h3><p>Department modules that produce the record, the report and the decision the agency is actually accountable for.</p></div>
  </div>
</div></section>

<section class="sec tight"><div class="wrap">
  <div class="stats">
    <div class="stat rv"><b data-count="{N_INDUSTRIES}">{N_INDUSTRIES}</b><span>Industries</span><small>Each a licensed edition, on the same engine.</small></div>
    <div class="stat rv d1"><b data-count="{N_MODULES}">{N_MODULES}</b><span>Modules</span><small>{N_DEPT} department modules and 3 platform modules.</small></div>
    <div class="stat rv d2"><b data-count="98">98</b><span>Registered sources</span><small>In seventeen categories, each connection-tested.</small></div>
    <div class="stat rv d3"><b data-count="{N_CAPS}">{N_CAPS}</b><span>Shared capabilities</span><small>Built once, inherited by every edition in the same release.</small></div>
  </div>
  <p class="footnote">Counts from the module registry and the source registry, November 2026.</p>
</div></section>

<section class="sec glow-top" id="trailer"><div class="wrap">
  <div class="sec-head"><span class="eyebrow rv">The trailer</span><h2 class="h2 split">Not a rendering. A running system.</h2>
  <p class="lede rv d2">Six minutes inside the product: seventeen editions, the admin console and the field app, every frame captured from the running platform. Sign up below and it unlocks right here.</p></div>
  {trailer_box()}
</div></section>
{signup_section()}

{whole_system()}

<section class="sec"><div class="wrap">
  <div class="sec-head"><span class="eyebrow rv">Seventeen editions · six buyer groups</span><h2 class="h2 split">A slice, not a fork.</h2>
  <p class="lede rv d2">Every edition is the same engine with the departments that industry runs. Nothing was forked; everything compounds. Scroll through the six buyer groups.</p></div>
  <div class="reel">
    <div class="reel-list">{groups_html}<div class="reel-item"><span class="k">+1</span><h3 class="h3">In design</h3><p>FireLens, for wildfire, is named and scoped. It is not built yet, and we say so.</p><div class="eds"><span class="chip dim">FireLens · in design</span></div></div></div>
    <div class="reel-stage" aria-hidden="true">{stage}</div>
  </div>
</div></section>

{grand_vision()}

<section class="sec"><div class="wrap">
  <div class="sec-head"><span class="eyebrow rv">AI-first</span><h2 class="h2 split">Ask, don't author.</h2>
  <p class="lede rv d2">The interface is an analyst, not a toolbar. One agent reasons across every source the asking user can see, and it inherits that user's grants exactly, because its tools are gated by the same checks as the interface.</p></div>
  <div class="ask rv">
    <p class="q">“Which substations in the flood polygon lost redundancy this week, and what did the SAR pass say?”</p>
    <div class="a"><span class="lbl2">The platform authors</span><p>Resolves the flood polygon, joins the asset record, runs change detection across modalities, decomposes the confidence, and returns the map, the list and the citation, inside the grants of the person who asked.</p></div>
  </div>
  <div class="grid g4" style="margin-top:18px">
    <div class="card rv"><span class="k">Platform functions</span><p>The agent's tools are the same functions the interface calls, not scraped screens.</p></div>
    <div class="card rv d1"><span class="k">Same grants</span><p>Disable a module and its agent tools disappear with it. There is no back door through the assistant.</p></div>
    <div class="card rv d2"><span class="k">Decomposed</span><p>Scores break into their components. Confidence is earned only where independent detectors agree.</p></div>
    <div class="card rv d3"><span class="k">Swappable model</span><p>The model sits behind an abstract interface. No contract names it.</p></div>
  </div>
</div></section>

<section class="sec band"><div class="wrap">
  <div class="sec-head"><span class="eyebrow rv">It says so</span><h2 class="h2 split">A platform that tells you what it doesn't know.</h2>
  <p class="lede rv d2">Every gap is stated on the face of the product instead of hidden behind a number. Lines from the trailer, read off the running product.</p></div>
  <div class="says">
    <div class="q rv"><span class="who">MaritimeLens</span><blockquote>Dark vessels. And it says so <em>when it can't tell.</em></blockquote></div>
    <div class="q rv"><span class="who">Terra</span><blockquote>They're proposals. <em>Not titles.</em></blockquote></div>
    <div class="q rv"><span class="who">PetroCore</span><blockquote>All of it simulated. <em>The screen says so.</em></blockquote></div>
    <div class="q rv"><span class="who">Flux</span><blockquote>An asset that isn't reporting is shown as <em>not reporting.</em></blockquote></div>
  </div>
</div></section>

<section class="sec"><div class="wrap">
  <div class="sec-head"><span class="eyebrow rv">Sovereign by construction</span><h2 class="h2 split">Sovereign is a property of the code, not the contract.</h2></div>
  <div class="grid g4">
    <div class="card rv"><span class="k">In-territory</span><h3 class="h3">Runs where you need it</h3><p>Container-packaged, with its own tenant, its own data and its own identity.</p></div>
    <div class="card rv d1"><span class="k">In the database</span><h3 class="h3">Isolation by row-level security</h3><p>Tenant and team isolation enforced by Postgres across every tenant table, not a filter in the application.</p></div>
    <div class="card rv d2"><span class="k">Licence as a gate</span><h3 class="h3">Resolved in code</h3><p>Every source carries a licence verdict. Avoid-sources are never offered; view-only sources are server-proxied.</p></div>
    <div class="card rv d3"><span class="k">Nothing spends itself</span><h3 class="h3">A human accepts the cost</h3><p>Commercial imagery tasking shows an indicative price before anyone commits.</p></div>
  </div>
  <div class="modes" style="margin-top:18px">
    <div class="mode rv"><span class="tagx">Connected</span><h3>SaaS</h3><p>Hosted for you. External data flows only through a gate, and each tenant can switch it off.</p></div>
    <div class="mode rv d1"><span class="tagx">Connected</span><h3>Sovereign hybrid</h3><p>For data that must stay under the customer's own control, with external data still behind the gate.</p></div>
    <div class="mode rv d2"><span class="tagx" style="color:var(--brass)">Lockout</span><h3>Air-gap capable</h3><p>A per-customer build in which no runtime call leaves the boundary, verified on the build before it ships.</p></div>
  </div>
  <p class="footnote" style="margin-top:26px">In every profile: no telemetry, no licence check, no crash reporter, no font from a CDN. <a href="sovereignty.html" style="color:var(--ivory)">Sovereignty in depth →</a></p>
</div></section>

<section class="sec band"><div class="wrap">
  <div class="sec-head"><span class="eyebrow rv">Why one engine</span><h2 class="h2 split">The market makes you pick one. We refuse the trade.</h2></div>
  <div class="vs rv">
    <div><b>General-purpose GIS</b><p>Powerful and generic. Becomes a solution only after a long integration programme.</p></div>
    <div><b>Point solutions</b><p>Excellent at one job. The second question needs a second vendor and a second contract.</p></div>
    <div><b>Consultancy builds</b><p>Fits on delivery day. Improves only when funded again, and never benefits from anything built for anyone else.</p></div>
    <div><b>Imagery and analytics APIs</b><p>Sell inputs, not decisions. Someone still has to build the operating picture.</p></div>
  </div>
  <div class="vs-all rv"><span class="eyebrow">BirunIQ · all four at once</span><p class="lede" style="margin-top:12px">Agent-native at the interface, enterprise-grade underneath, built for the way public agencies are actually held accountable, and delivered as purpose-built editions.</p><p class="bigline" style="margin-top:22px;font-size:clamp(1.6rem,3.6vw,2.8rem)">You are not buying a map. <span class="cy">You are buying the rate of change.</span></p></div>
</div></section>

<section class="sec" style="overflow:hidden"><div class="wrap story">
  <div class="diagram rv"><img src="assets/media/earth-biruni.webp" alt="The Earth from above Central and South Asia" loading="lazy" width="1400" height="1400" /></div>
  <div style="display:grid;gap:22px">
    <span class="eyebrow rv">The name</span>
    <h2 class="h2 split">Named for the man who measured the Earth from a mountain.</h2>
    <p class="lede rv d2">Abu Rayhan al-Biruni, the 11th-century scholar, sighted the horizon from a summit of known height, measured the dip of his line of sight, and recovered the radius of the planet from a single triangle.</p>
    <p class="formula rv d3"><i>R</i> = <i>h</i> · cos <span class="th">θ</span> / (1 − cos <span class="th">θ</span>)</p>
    <p class="rv d3">The BirunIQ mark is that construction: the Earth, the sightline, the point of tangency and the observer. A summit then. A satellite now.</p>
    <a class="btn rv d4" style="justify-self:start" href="story.html">Read the story →</a>
  </div>
</div></section>

<section class="sec band notbuilt"><div class="wrap">
  <div class="sec-head"><span class="eyebrow rv">What is next</span><h2 class="h2 split">Named, scoped, and not built yet.</h2>
  <p class="lede rv d2">Stated as not built because it is not built. The platform is built to be audited by someone who wants it to fail.</p></div>
  <div class="grid g3">
    <div class="card rv"><span class="k">Not built</span><h3 class="h3">FireLens</h3><p>Wildfire, the eighteenth edition: named and scoped, with no code behind it yet.</p></div>
    <div class="card rv d1"><span class="k">Not built</span><h3 class="h3">Calibrated confidence</h3><p>Confidence bands today are fused from independent detectors. Calibration against held-out data is the next step.</p></div>
    <div class="card rv d2"><span class="k">Not built</span><h3 class="h3">Live ocean forcing</h3><p>Spill drift forecasts stay labelled simulated until an ocean-forcing feed is connected.</p></div>
  </div>
</div></section>

<section class="cta-band finale"><div class="ring" aria-hidden="true"></div><div class="wrap" style="display:grid;justify-items:center;gap:26px">
  <span class="eyebrow nobar rv">The future</span>
  <h2 class="bigline split" style="text-align:center">The future of geospatial intelligence is not another map.</h2>
  <p class="lede rv d2" style="text-align:center">It is one sovereign engine that gets better every time anyone asks it a new question.</p>
  <div class="grid g3" style="text-align:left;width:100%;margin-top:10px">
    <div class="card rv"><span class="k">The engine</span><p>{N_CAPS} shared capabilities, one data fabric, one identity, one agent, built once and inherited by every edition in the same release.</p></div>
    <div class="card rv d1"><span class="k">The editions</span><p>Seventeen accountable industries and {N_DEPT} department modules, each a catalogue and a theme on the same engine, none of them a fork.</p></div>
    <div class="card rv d2"><span class="k">The standard</span><p>Provenance that holds, lineage that is recorded, and every gap stated on the face of the product.</p></div>
  </div>
  <p class="h3 rv" style="margin-top:20px">The platform that measures the Earth.</p>
  <div class="rv" style="display:flex;gap:14px;flex-wrap:wrap;justify-content:center"><a class="btn primary" href="#signup">Sign up for updates</a><a class="btn" href="contact.html">Request a briefing</a></div>
</div></section>

<section class="sec tight band" id="sms"><div class="wrap" style="max-width:860px">
  <span class="eyebrow">Text message (SMS) updates</span>
  <p style="margin-top:14px">Bitruvius, Inc. (“BirunIQ”) sends text messages only to people who have asked to receive them, for replies to enquiries, demo and meeting scheduling, and account and service notifications. You opt in on our <a href="contact.html">contact form</a> by ticking the SMS consent box, which is unticked by default and optional. Message frequency varies, up to 4 messages per month. Message and data rates may apply. Reply <b>STOP</b> to opt out or <b>HELP</b> for help. Mobile numbers and SMS consent are never shared with or sold to third parties or affiliates for marketing purposes. See our <a href="sms-terms.html">SMS Terms</a>, <a href="terms.html">Terms of Service</a> and <a href="privacy.html">Privacy Policy</a>.</p>
</div></section>
""" + footer(earth_credit=True)


def page_editions():
    body = ""
    for gk, gname, gline in GROUPS:
        eds = [e for e in ED if e["group"] == gk]
        cards = "".join(f"""<a class="ed-card rv" href="editions/{e['slug']}.html">
  <div class="media"><img src="assets/media/loops/{e['slug']}.webp" alt="" loading="lazy" width="1280" height="720" /><video muted loop playsinline preload="none" data-src="assets/media/loops/{e['slug']}.mp4" data-auto="hover" aria-hidden="true"></video></div>
  <div class="body"><span class="k">{E(e['sector'])} · {len(DECK[e['slug']]['modules'])} modules</span><b>BirunIQ {E(e['name'])}</b><p>{E(e['line'])}</p><span class="more">Explore {E(e['name'])} →</span></div></a>""" for e in eds)
        body += f"""<div class="group-h rv"><h2 class="h3">{gname}</h2><span class="k">{len(eds)} editions</span></div><p class="rv" style="margin:-8px 0 22px">{gline}</p><div class="grid g3">{cards}</div>"""
    return head("Editions · BirunIQ", "Seventeen BirunIQ editions in six buyer groups, from government and public safety to defence, energy, transport and environment, on one sovereign engine.") + header("editions.html") + f"""
<section class="phero"><div class="wrap">
  <span class="eyebrow rv">Editions</span>
  <h1 class="display split">Seventeen industries.<br/>One engine.</h1>
  <p class="lede rv d2">An edition is an industry: the departments it runs, as modules, each owned and accountable on its own, on the same map, catalog and sign-in. {N_DEPT} department modules in all. Hover a card to see it running.</p>
</div></section>
<section class="sec" style="padding-top:0"><div class="wrap">{body}
  <div class="group-h rv"><h2 class="h3">In design</h2><span class="k">1 edition</span></div>
  <div class="grid g3"><div class="card rv"><span class="k">Wildfire</span><h3 class="h3">FireLens</h3><p>Named and scoped, with no code behind it yet. It will be the eighteenth edition.</p></div></div>
</div></section>
{grand_vision()}
""" + footer()


def page_edition(e):
    d = DECK[e["slug"]]
    i = ED.index(e)
    prev_e, next_e = ED[i - 1], ED[(i + 1) % len(ED)]
    gname = dict((g[0], g[1]) for g in GROUPS)[e["group"]]
    served_who, _, pain = d["pain"].partition(" — ")
    headline = d["summary"].split(". ")[0].rstrip(".") + "."
    mods = "".join(f"<div class=\"rv\"><i>{k + 1:02d}</i><span><b>{E(n)}</b><p>{E(x)}</p></span></div>" for k, (n, x) in enumerate(d["modules"]))
    film = "".join(f"""<a href="../trailer.html#t{int(s)}" class="rv"><span class="t">{ts(s)}</span><b>{E(t)}</b><span class="go">In the trailer →</span></a>""" for s, t in e["film"])
    body = "".join(f'<p class="lede rv d{k + 1}" style="margin-top:{14 if k else 0}px">{E(p)}</p>' for k, p in enumerate(e["body"]))
    siblings = "".join(f'<a class="chip" href="{x["slug"]}.html">{x["name"]}</a>' for x in ED if x["group"] == e["group"] and x is not e)
    return head(f"BirunIQ {e['name']} · {e['sector']}", f"BirunIQ {e['name']}: {headline} {len(d['modules'])} department modules on one sovereign engine.", depth=1,
                og_img=f"assets/media/loops/{e['slug']}.webp") + header("editions.html", depth=1) + f"""
<section class="phero"><div class="wrap">
  <nav class="crumb rv" aria-label="Breadcrumb"><a href="../editions.html">Editions</a><span>/</span><span>{gname}</span><span>/</span><span>Edition {i + 1} of {len(ED)}</span></nav>
  <span class="eyebrow rv">{E(d['served'].title())}</span>
  <h1 class="display split">BirunIQ {E(e['name'])}</h1>
  <p class="lede rv d2" style="font-size:clamp(1.3rem,2.4vw,1.9rem);color:var(--ivory)">{E(headline)}</p>
</div></section>
<section class="sec" style="padding-top:0"><div class="wrap">
  <div class="frame rv" style="aspect-ratio:16/8">{vid(e['slug'], depth=1, label='From the trailer · demonstration data')}</div>

  <div class="feat" style="border-top:0;align-items:start">
    <div><span class="eyebrow rv">Industry served</span><p class="rv d1" style="margin-top:16px">{E(served_who)}</p></div>
    <div><p class="pain rv">{E(pain)}</p><div style="margin-top:26px">{body}</div></div>
  </div>

  <div class="feat" style="align-items:start">
    <div><span class="eyebrow rv">Department modules</span><p class="rv d1" style="margin-top:16px"><b style="font-size:3.4rem;color:var(--ivory);letter-spacing:-.04em;font-weight:620">{len(d['modules'])}</b><br/>each owned and accountable on its own.</p></div>
    <div class="modlist">{mods}</div>
  </div>

  <div class="practice rv" style="margin-top:10px">{E(d['practice'])}</div>

  <div class="feat" style="align-items:start">
    <div><span class="eyebrow rv">AI decision support</span><p class="rv d1" style="margin-top:16px">One analyst across every source the asking user can see, inside that user's grants.</p></div>
    <div class="ask rv">
      <p class="q">{E(d['asks'])}</p>
      <div class="a"><span class="lbl2">The platform resolves</span><p>{E(d['resolves'])}</p></div>
      <div class="guard"><b>The guardrail</b>{E(d['guardrail'])}</div>
    </div>
  </div>

  <div class="feat" style="align-items:start">
    <div><span class="eyebrow rv">In the trailer</span><p class="rv d1" style="margin-top:16px">Narration as heard in the film. Sign up to watch it.</p></div>
    <div class="chapters">{film}</div>
  </div>

  <div class="feat" style="align-items:start">
    <div><span class="eyebrow rv">Same platform underneath</span></div>
    <div class="grid g2">
      <div class="card rv"><span class="k">Shared</span><h3 class="h3">One map, one catalog, one sign-in</h3><p>{E(e['name'])} runs on the same engine as every other edition, with {N_CAPS} shared capabilities built once.</p></div>
      <div class="card rv d1"><span class="k">Deploy</span><h3 class="h3">SaaS, sovereign hybrid, air-gap capable</h3><p>Licensed per tenant, data kept apart by row-level security, access scoped by team. <a href="../sovereignty.html" style="color:var(--cyan)">Sovereignty →</a></p></div>
    </div>
  </div>

  <div class="feat" style="align-items:center">
    <div><span class="eyebrow rv">Also in {gname}</span><div class="eds rv" style="display:flex;gap:8px;flex-wrap:wrap;margin-top:16px">{siblings or '<span class="muted">—</span>'}</div></div>
    <div style="display:flex;gap:12px;flex-wrap:wrap;justify-content:flex-end" class="rv"><a class="btn" href="{prev_e['slug']}.html">← {prev_e['name']}</a><a class="btn" href="{next_e['slug']}.html">{next_e['name']} →</a></div>
  </div>
</div></section>
{signup_section(depth=1, title=f"Sign up for {E(e['name'])} updates.", lede=f"Tell us who you are and we'll unlock the trailer, email you the link, and follow up about {E(e['name'])} if you'd like a briefing.")}
""" + footer(depth=1)


CHAPTERS = [(0, "Open", "The Earth, the star and the sightline"), (20, "The premise", "One platform, one map, one catalog, one sign-in"),
            (34, "How it's built", "Rust, Postgres and PostGIS, React, Flutter; SaaS, sovereign hybrid, air-gap capable"),
            (53, "Seventeen industries", "From defence and critical infrastructure to environment, agriculture and land"),
            (62, "133 modules", "130 department modules, 3 platform modules, 30 shared capabilities"),
            (72, "One system", "Many tenants, licensed per edition, kept apart by row-level security"),
            (90, "Defence & security", "WatchFloor, MaritimeLens, Sentry, Guardian"),
            (130, "Critical infrastructure", "3D severity, Grid, Flux, PetroCore, Milepost, Tower"),
            (195, "Environmental", "SpillTrace, FloodSurge, GreenScope, groundwater, Harvest"),
            (251, "Government & land", "Atlas, maritime, mapbook, Terra, One Africa, Blueprint"),
            (291, "The platform", "One catalog, analysis and compare, the Admin console, data sources, BirunIQ Field"),
            (356, "Unlock your world", "The tagline and the close")]


def page_trailer():
    chap = "".join(f'<a href="#t{s}" data-seek="{s}"><span class="t">{ts(s)}</span><span><b>{E(t)}</b><br/><span>{E(d)}</span></span><span class="go">Play from here</span></a>' for s, t, d in CHAPTERS)
    lines = "".join(f'<p id="t{int(l["start"])}"><a class="ts" href="#t{int(l["start"])}" data-seek="{int(l["start"])}">{ts(l["start"])}</a>{E(l["text"])}</p>' for l in TX["lines"])
    return head("The trailer · BirunIQ", "Sign up to watch the BirunIQ trailer: six minutes inside the running platform across seventeen editions, with chapters and a full transcript.") + header("trailer.html") + f"""
<section class="phero" style="padding-bottom:40px"><div class="wrap">
  <span class="eyebrow rv">The trailer</span>
  <h1 class="display split">Six minutes inside the running product.</h1>
  <p class="lede rv d2">Seventeen editions, the admin console and the field app. Every frame was captured from the running platform. All data shown is synthetic demonstration data or publicly available data. Sign up below to watch.</p>
</div></section>
<section class="sec" style="padding-top:0"><div class="wrap">
  {trailer_box()}
  <p class="privacy-note">The trailer plays in YouTube's privacy-enhanced player, and nothing loads from YouTube until you press play.</p>
</div></section>
{signup_section()}
<section class="sec" style="padding-top:0"><div class="wrap">
  <div class="feat" style="align-items:start">
    <div><span class="eyebrow rv">Chapters</span><p class="rv d1" style="margin-top:14px">Jump straight to a sector once you've signed up.</p></div>
    <div class="chapters rv">{chap}</div>
  </div>
  <div class="feat" style="align-items:start">
    <div><span class="eyebrow rv">Transcript</span><p class="rv d1" style="margin-top:14px">The narration, line by line. Each line was checked against the product before it was recorded.</p></div>
    <div class="transcript rv">{lines}</div>
  </div>
</div></section>
""" + footer()


def page_platform():
    caps = ["Live raster overlays: NASA GIBS, ArcGIS REST, STAC", "Team-scoped data via row-level security", "Conversational AI agent control",
            "Three-tier administration", "Floating, dockable panels", "Sun-position lighting and 3D measurement", "Drawing and annotation tools",
            "WGS84 · UTM · MGRS · State Plane", "UTM/MGRS grid overlay", "Street-level imagery", "Themeable interface",
            "Background monitoring daemon", "Multi-modal change detection", "LADM-aligned cadastral fabric", "Geography-aware data registry",
            "External data-source integration (98)", "Commercial tasking with cost preview", "Point cloud and Gaussian splat rendering",
            "Print-ready map export", "Mapbook generation", "Module catalogue system", "KPI dashboards", "Categorical and graduated symbology",
            "Sketch and markup with GeoJSON export", "Live compass rail navigation", "Feature cross-pollination across modules",
            "Per-user data-source overrides", "Project-level access control", "Analyst-tunable thresholds", "Real-time feature synchronisation",
            "Sovereignty-enforced deployment"]
    caps_html = "".join(f"<li>{E(c)}</li>" for c in caps)
    return head("Platform · BirunIQ", "Inside the BirunIQ engine: one agent inside the user's grants, one substrate for many owners, 98 registered sources, BirunIQ Field, what leaves the building, the city in 3D, and a record with two clocks.") + header("platform.html") + f"""
<section class="phero"><div class="wrap">
  <span class="eyebrow rv">The platform</span>
  <h1 class="display split">Underneath all of it is one engine.</h1>
  <p class="lede rv d2">Seventeen editions share it: one data fabric, one identity, one agent, {N_CAPS} shared capabilities built once. Every engine-level improvement built for any edition lands in every other edition in the same release.</p>
</div></section>
<section class="sec" style="padding-top:0"><div class="wrap">
  <div class="frame rv" style="aspect-ratio:16/8">{vid("platform", label="Catalog · analysis · compare")}</div>
</div></section>
{whole_system()}

<section class="sec band"><div class="wrap">
  <div class="sec-head"><span class="eyebrow rv">The enterprise system</span><h2 class="h2 split">One substrate, many owners.</h2>
  <p class="lede rv d2">A grant flows down; a denial upstream ends the conversation. Default-deny, down to a single project.</p></div>
  <div class="chain rv">
    <div><span class="k">01</span><b>Sovereign instance</b><ul><li>Container-packaged</li><li>Its own identity provider</li><li>Credentials server-side, write-only</li></ul></div>
    <div><span class="k">02</span><b>Tenant</b><ul><li>The licensed editions</li><li>Own tenant, own data, own identity</li></ul></div>
    <div><span class="k">03</span><b>Team</b><ul><li>The row-level security boundary</li><li>Deny a team a module and no member reaches it</li></ul></div>
    <div><span class="k">04</span><b>Project</b><ul><li>Whole portfolio or a single project</li><li>Default-deny</li></ul></div>
    <div><span class="k">05</span><b>User</b><ul><li>Module-access grid across every edition</li><li>The agent inherits exactly these grants</li></ul></div>
  </div>
  <h3 class="h3 rv" style="margin:46px 0 18px">Five enforcement gates</h3>
  <div class="gates">
    <div class="rv"><b>01 · NAVIGATION</b><p>What appears at all.</p></div>
    <div class="rv d1"><b>02 · PANELS</b><p>Which surfaces resolve.</p></div>
    <div class="rv d2"><b>03 · AGENT TOOLS</b><p>What the analyst may reason over.</p></div>
    <div class="rv d3"><b>04 · ACCESS GRID</b><p>The per-user grant.</p></div>
    <div class="rv d4"><b>05 · ROW-LEVEL SECURITY</b><p>Postgres filters the rows themselves.</p></div>
  </div>
  <div class="feat rev" style="margin-top:30px">
    <div class="fx"><div class="frame rv">{vid("admin", label="Admin console")}</div></div>
    <div class="rv"><span class="eyebrow">Three admin tiers, in-app</span><h3 class="h2" style="margin:16px 0">No separate console.</h3>
      <ul class="mods" style="grid-template-columns:1fr"><li><span>01</span>Provider admin: which modules are enabled across the deployment</li><li><span>02</span>Tech admin: module defaults and the shared feature pool</li><li><span>03</span>User admin: users, roles and teams</li><li><span>04</span>Data sources, each external feed with its status, and one switch for external data</li></ul></div>
  </div>
</div></section>

<section class="sec"><div class="wrap">
  <div class="sec-head"><span class="eyebrow rv">AI · identity first</span><h2 class="h2 split">The agent knows who is asking.</h2>
  <p class="lede rv d2">Before it answers anything, the agent resolves who is asking (user, tenant, role and groups) and offers only what that grant can reach.</p></div>
  <div class="grid g4">
    <div class="card rv"><span class="k">01</span><h3 class="h3">Identity first</h3><p>Tenant, role and groups are read back to the user in the first reply.</p></div>
    <div class="card rv d1"><span class="k">02</span><h3 class="h3">Real functions</h3><p>The tools are the same calls the interface makes, gated by the same grants.</p></div>
    <div class="card rv d2"><span class="k">03</span><h3 class="h3">Refuses, not guesses</h3><p>An input it cannot act on runs nothing, and the reply says why.</p></div>
    <div class="card rv d3"><span class="k">04</span><h3 class="h3">Swappable model</h3><p>The backbone sits behind an abstract interface; no contract names it.</p></div>
  </div>
</div></section>

<section class="sec band"><div class="wrap">
  <div class="sec-head"><span class="eyebrow rv">The shared engine</span><h2 class="h2 split">Built once. Inherited by every edition.</h2></div>
  <ul class="caps rv">{caps_html}</ul>
</div></section>

<section class="sec"><div class="wrap">
  <div class="sec-head"><span class="eyebrow rv">Source data · the registry</span><h2 class="h2 split">98 registered sources. 17 categories. Each one connection-tested.</h2>
  <p class="lede rv d2">The registry is not a list of links. It is the integration programme a customer never has to run, the licence review they never have to repeat, and the silent feed failure they never have to discover in front of a minister.</p></div>
  <div class="grid g3">
    <div class="card rv"><span class="k">Boundaries & base</span><p>geoBoundaries · GADM · Overture · OpenStreetMap · OneGeology</p></div>
    <div class="card rv d1"><span class="k">Population & development</span><p>WorldPop · JRC GHSL · Kontur · HDX · World Bank · UN Data · Eurostat</p></div>
    <div class="card rv d2"><span class="k">Environment</span><p>GEBCO · EMODnet · GBIF · USGS</p></div>
    <div class="card rv"><span class="k">Real-time</span><p>NASA FIRMS · OpenAQ · Open-Meteo · GDACS · OpenSky · AIS</p></div>
    <div class="card rv d1"><span class="k">Imagery</span><p>NASA GIBS · STAC · Sentinel-1 SAR · Sentinel-2 · VIIRS</p></div>
    <div class="card rv d2"><span class="k">Tasking</span><p>Commercial SAR and optical tasking, costed before commitment. Nothing spends without a human.</p></div>
  </div>
  <div class="grid g4" style="margin-top:18px">
    <div class="card rv"><div class="big">98</div><p>Sources registered, each an agreement, an endpoint, a schema and a refresh cadence.</p></div>
    <div class="card rv d1"><div class="big">0</div><p>Licence breaches by accident: the verdict resolves in code, per module and per scope.</p></div>
    <div class="card rv d2"><div class="big">Pass</div><p>A dead feed is visible: failures surface as a red result to an administrator, not an empty map.</p></div>
    <div class="card rv d3"><div class="big">Geo</div><p>Geography-aware: a national cadastre where one exists, the open continental fabric where it does not.</p></div>
  </div>
</div></section>

<section class="sec band"><div class="wrap">
  <div class="sec-head"><span class="eyebrow rv">BirunIQ Field</span><h2 class="h2 split">The last mile is a person, offline.</h2>
  <p class="lede rv d2">No-code field apps with offline capture and sync. The inspector's photograph becomes a feature in the department's operating picture without an import step, and without a second system to license.</p></div>
  <div class="fieldvs">
    <div class="card rv"><span class="k">Without Field</span><h3 class="h3">Five hand-offs. Three days.</h3><ol><li>Paper form</li><li>Phone photo</li><li>Email to the office</li><li>Re-key into GIS</li><li>Someone hopes it was the right pole</li></ol></div>
    <div class="card with rv d1"><span class="k">With BirunIQ Field</span><h3 class="h3">One hand-off. Minutes.</h3><ol><li>Capture in the field, offline</li><li>Syncs on return to coverage</li><li>Appears as a feature in the module: located, permissioned, audited</li></ol></div>
  </div>
  <div class="grid g4" style="margin-top:18px">
    <div class="card rv"><span class="k">Configured, not coded</span><p>A field app is a configuration of an existing module, so it inherits that module's permissions and schema.</p></div>
    <div class="card rv d1"><span class="k">Offline by design</span><p>Capture without connectivity, sync when the vehicle returns to coverage.</p></div>
    <div class="card rv d2"><span class="k">No second system</span><p>No separate field product to license, and no second copy of the asset record to reconcile.</p></div>
    <div class="card rv d3"><span class="k">Evidence, not anecdote</span><p>Every capture is located, timestamped and attributed.</p></div>
  </div>
</div></section>

<section class="sec"><div class="wrap">
  <div class="sec-head"><span class="eyebrow rv">Export · layout · services</span><h2 class="h2 split">What leaves the building.</h2>
  <p class="lede rv d2">An operating picture that cannot produce the artefact an agency files is a demonstration, not a system.</p></div>
  <div class="grid g3">
    <div class="card rv"><span class="k">Export & layout</span><ul><li>Professional layout composer</li><li>Multi-page mapbook from the live scene</li><li>Print-ready map export</li><li>One-click DOCX incident reports</li><li>GeoJSON export of sketches and markup</li></ul></div>
    <div class="card rv d1"><span class="k">Local data & GIS services</span><ul><li>ArcGIS Feature and Map Server, query and upsert</li><li>COG · XYZ raster · GeoJSON URL · PostGIS</li><li>NASA GIBS and STAC as persistable overlays</li><li>Local GeoTIFF and CSV upload</li></ul></div>
    <div class="card rv d2"><span class="k">The surfaces</span><ul><li>Floating, snapshot-able panels</li><li>KPI dashboards and the module catalogue</li><li>Point clouds and Gaussian splats</li><li>UTM/MGRS grid and coordinate readout</li></ul></div>
  </div>
</div></section>

<section class="sec band"><div class="wrap">
  <div class="feat" style="border-top:0">
    <div class="rv"><span class="eyebrow">3D · the city as mesh</span><h2 class="h2" style="margin:16px 0">The city in three dimensions.</h2><p class="lede">Three independent mesh sources render in one scene, and features colour by attribute on both renderers. Coverage is stated: most buildings in the open sources carry no classification, and the legend says so rather than guessing.</p></div>
    <div class="fx"><div class="frame rv">{vid("guardian", label="3D severity")}</div></div>
  </div>
  <div class="feat rev">
    <div class="fx"><div class="frame rv">{vid("spilltrace", label="Incident record")}</div></div>
    <div class="rv"><span class="eyebrow">Record · two clocks</span><h2 class="h2" style="margin:16px 0">What we knew, and when we knew it.</h2><p class="lede">Every incident record carries two clocks: when something was true in the world, and when the system learned it. Corrections supersede; they never overwrite, and that is enforced at the database.</p></div>
  </div>
  <div class="feat">
    <div class="rv"><span class="eyebrow">Provenance</span><h2 class="h2" style="margin:16px 0">Know where every answer came from.</h2><p class="lede">Every model the platform runs has a manifest entry: source, commit, weight hashes, licence text and fetch date. Anything a model synthesised rather than observed is marked, and the mark follows it to whatever is derived from it.</p></div>
    <div class="fx"><div class="frame rv">{vid("harvest", label="Model output, reviewed")}</div></div>
  </div>
</div></section>

<section class="sec"><div class="wrap">
  <div class="feat" style="border-top:0;align-items:start">
    <div class="rv"><span class="eyebrow">The stack</span><h2 class="h2" style="margin:16px 0">Built in Rust.</h2></div>
    <div class="grid g2">
      <div class="card rv"><span class="k">Server</span><p>Rust, on Postgres and PostGIS.</p></div>
      <div class="card rv d1"><span class="k">Web</span><p>A React web client.</p></div>
      <div class="card rv d2"><span class="k">Mobile</span><p>A Flutter field app: BirunIQ Field.</p></div>
      <div class="card rv d3"><span class="k">Models</span><p>Inference in a containerised sidecar, behind an interface, so the model is swappable.</p></div>
    </div>
  </div>
</div></section>
{signup_section(title="Sign up for platform updates.")}
""" + footer()


def page_sovereignty():
    return head("Sovereignty · BirunIQ", "Deploy BirunIQ as SaaS, as a sovereign hybrid, or as an air-gap capable build. No telemetry, no licence check, no crash reporter in any profile; external data only through a gate each tenant can switch off.") + header("sovereignty.html") + f"""
<section class="phero"><div class="wrap">
  <img class="bg-earth" src="assets/media/earth-americas.webp" alt="" aria-hidden="true" />
  <span class="eyebrow rv">Sovereignty</span>
  <h1 class="display split">Your world. Inside your boundary.</h1>
  <p class="lede rv d2">“Your world” in the tagline is literal: your ground, your data, inside your boundary. BirunIQ deploys three ways, and the rules that matter hold in all three.</p>
</div></section>
<section class="sec" style="padding-top:0"><div class="wrap">
  <div class="modes">
    <div class="mode rv"><span class="tagx">Connected</span><h3>SaaS</h3><p>Hosted for you, on the same engine as every other deployment. External data flows only through the egress gate, and each tenant can switch external data off for itself.</p></div>
    <div class="mode rv d1"><span class="tagx">Connected</span><h3>Sovereign hybrid</h3><p>For customers whose data must stay under their own control, with external data still behind the gate and the same per-tenant switch.</p></div>
    <div class="mode rv d2"><span class="tagx" style="color:var(--brass)">Lockout</span><h3>Air-gap capable</h3><p>A per-customer build for customers who need a lockout. No runtime call leaves the deployment boundary: no external data, no model API, no CDN font. A delivery is called air-gapped only after it passes verification on that build.</p></div>
  </div>

  <div class="feat" style="align-items:start">
    <div class="rv"><span class="eyebrow">In every profile</span><h2 class="h2" style="margin:16px 0">Nothing phones home.</h2><p class="lede">If a dependency phones home on its own, it does not go in.</p></div>
    <ul class="mods rv d1" style="grid-template-columns:1fr">
      <li><span>01</span>No telemetry</li><li><span>02</span>No licence check</li><li><span>03</span>No crash reporter</li><li><span>04</span>No font from a CDN</li><li><span>05</span>A stored credential is sent only to the provider that issued it</li>
    </ul>
  </div>

  <div class="feat rev" style="align-items:start">
    <div class="fx"><div class="frame rv">{vid("admin", label="External data · on/off")}</div></div>
    <div class="rv"><span class="eyebrow">The egress gate</span><h2 class="h2" style="margin:16px 0">External data, on your terms.</h2><p class="lede">In a connected deployment, external data passes through one gate. Every external feed is listed with its status, and a tenant can switch external data off from the admin console.</p></div>
  </div>

  <div class="feat" style="align-items:start">
    <div class="rv"><span class="eyebrow">Separation</span><h2 class="h2" style="margin:16px 0">Kept apart where it counts.</h2></div>
    <div class="grid g2">
      <div class="card rv"><span class="k">Database</span><h3 class="h3">Row-level security</h3><p>Each tenant's data is separated in the database itself. The server refuses to start as a role that could bypass it.</p></div>
      <div class="card rv d1"><span class="k">Access</span><h3 class="h3">Scoped by team</h3><p>Inside a tenant, access follows the team, not the whole organisation.</p></div>
      <div class="card rv d2"><span class="k">Identity</span><h3 class="h3">One sign-in, two factors</h3><p>One identity across every edition and the field app, with a second factor at sign-in.</p></div>
      <div class="card rv d3"><span class="k">Licences</span><h3 class="h3">Clean supply chain</h3><p>Every model, dataset and dependency carries a licence class, and each model a provenance manifest.</p></div>
    </div>
  </div>
</div></section>
<section class="cta-band"><div class="ring" aria-hidden="true"></div><div class="wrap" style="display:grid;justify-items:center;gap:24px">
  <h2 class="h2 split" style="text-align:center">Tell us where it has to run.</h2>
  <p class="lede rv" style="text-align:center">We'll talk through the deployment your agency needs, including a lockout build.</p>
  <a class="btn primary rv" href="contact.html">Request a briefing</a>
</div></section>
""" + footer(earth_credit=True)


def page_story():
    return head("The name · BirunIQ", "BirunIQ is named for Abu Rayhan al-Biruni, the 11th-century scholar who measured the Earth from a single mountain. The mark is his construction.") + header("story.html") + f"""
<section class="phero"><div class="wrap">
  <span class="eyebrow rv">The name</span>
  <h1 class="display split">The platform that measures the Earth, named for the man who measured it first.</h1>
</div></section>
<section class="sec" style="padding-top:0"><div class="wrap">
  <div class="story">
    <div class="diagram rv" style="position:relative">
      <img src="assets/media/earth-biruni.webp" alt="The Earth over Central and South Asia" loading="lazy" width="1400" height="1400" />
      <svg viewBox="0 0 100 100" style="position:absolute;inset:0" aria-hidden="true">
        <path d="M86 9 L33 23" stroke="#7FD6FF" stroke-width=".45" fill="none"/>
        <path d="M86 9 L70 9" stroke="#E3B733" stroke-width=".3" stroke-dasharray="1 1" fill="none"/>
        <circle cx="33" cy="23" r="1.2" fill="#E3B733"/>
        <polygon points="86,6 86.8,8.2 89,9 86.8,9.8 86,12 85.2,9.8 83,9 85.2,8.2" fill="#E3B733"/>
      </svg>
    </div>
    <div class="prose" style="display:grid;gap:18px">
      <p class="lede rv">Abu Rayhan al-Biruni was an 11th-century scholar. From a summit of known height in present-day Pakistan, he sighted the horizon and measured the dip angle <span class="iq">θ</span> between the horizontal and his line of sight.</p>
      <p class="rv d1">That line is tangent to the Earth: it touches it at exactly one point. From one triangle he recovered the radius of the entire planet, a thousand years before satellites.</p>
      <p class="formula rv d2"><i>R</i> = <i>h</i> · cos <span class="th">θ</span> / (1 − cos <span class="th">θ</span>)</p>
    </div>
  </div>

  <div class="feat" style="align-items:start">
    <div class="rv"><span class="eyebrow">The mark is the measurement</span><h2 class="h2" style="margin:16px 0">Four parts. One theorem.</h2></div>
    <div class="grid g2">
      <div class="card rv"><span class="k">The circle</span><h3 class="h3">The Earth</h3><p>The thing being measured.</p></div>
      <div class="card rv d1"><span class="k">The tangent ray</span><h3 class="h3">The sightline</h3><p>A line that touches the Earth at exactly one point.</p></div>
      <div class="card rv d2"><span class="k">The brass node</span><h3 class="h3"><span class="iq">The tangency</span></h3><p>The point of measurement, where the sightline meets the Earth.</p></div>
      <div class="card rv d3"><span class="k">The brass star</span><h3 class="h3"><span class="iq">The observer</span></h3><p>A summit then. A satellite now.</p></div>
    </div>
  </div>

  <div class="feat" style="align-items:center">
    <div class="rv"><img src="assets/brand/biruniq-mark-dark.svg" alt="The BirunIQ mark" width="320" height="320" style="width:min(320px,70%)" /></div>
    <div class="rv"><span class="eyebrow">Brass is reserved</span><h2 class="h2" style="margin:16px 0">If everything is brass, nothing is.</h2><p class="lede">Deep navy is the sky al-Biruni worked under. Brass is the instrument: astrolabes, quadrants, the tools of Golden-Age measurement. In the mark it marks only the observer, the tangency and the IQ.</p></div>
  </div>

  <div class="feat" style="align-items:center">
    <div class="rv"><span class="eyebrow">The promise</span></div>
    <div class="rv"><p class="h2 tag3" style="font-weight:600"><span class="t">Unlock the evidence.</span><span class="t">Unlock the answers.</span><span class="t t3">Unlock your world.{TM}</span></p><p class="lede" style="margin-top:20px">Three steps in the order the platform works: the evidence comes first, the answers are drawn from it, and the customer acts on their own world.</p></div>
  </div>
</div></section>
""" + footer(earth_credit=True)


# ── re-skin hand-maintained pages (body text untouched) ───────────────────
KEEP = ["about", "privacy", "terms", "eula", "evaluation-terms", "attributions", "sms-terms", "contact"]


def reskin(name):
    p = ROOT / f"{name}.html"
    s = p.read_bytes().decode("utf-8")
    m_title = re.search(r"<title>(.*?)</title>", s, re.S)
    m_desc = re.search(r'<meta name="description" content="(.*?)"', s, re.S)
    m_main = re.search(r"<main[^>]*>(.*?)</main>", s, re.S)
    if not (m_title and m_main):
        raise SystemExit(f"{name}: no <title> or <main>")
    scripts = "".join(re.findall(r"<script(?![^>]*(?:v2|signup)\.js).*?</script>", s[m_main.end():], re.S))
    inner = m_main.group(1)
    inner = re.sub(r'^\s*<div class="wrap(?: prose)?"[^>]*>', "", inner); inner = re.sub(r'</div>\s*$', "", inner)
    title = html.unescape(m_title.group(1))
    desc = html.unescape(m_desc.group(1)) if m_desc else title
    out = (head(title, desc) + header("contact.html" if name == "contact" else "") +
           f'\n<section class="phero" style="padding-bottom:30px"><div class="wrap"><span class="eyebrow">{"Contact" if name == "contact" else "BirunIQ"}</span></div></section>\n'
           f'<main><div class="wrap prose" style="padding-bottom:110px">{inner}</div></main>\n{scripts}' + footer())
    return out, inner


def legal_text(s):
    """The legal body, as plain text, to prove a re-skin changed nothing in it."""
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def main():
    pages = {
        "index.html": page_home(), "editions.html": page_editions(), "trailer.html": page_trailer(),
        "platform.html": page_platform(), "sovereignty.html": page_sovereignty(), "story.html": page_story(),
    }
    (ROOT / "editions").mkdir(exist_ok=True)
    for e in ED:
        pages[f"editions/{e['slug']}.html"] = page_edition(e)
    for name in KEEP:
        p = ROOT / f"{name}.html"
        orig = p.read_bytes().decode("utf-8")
        before = legal_text(re.search(r"<main[^>]*>(.*?)</main>", orig, re.S).group(1))
        out, inner = reskin(name)
        after = legal_text(inner)
        if before != after:
            raise SystemExit(f"{name}: body text changed by the re-skin")
        pages[f"{name}.html"] = out
    for rel, s in pages.items():
        (ROOT / rel).write_bytes(s.encode("utf-8"))
    print(f"wrote {len(pages)} pages")


if __name__ == "__main__":
    main()
