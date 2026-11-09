# biruniq.com

The public BirunIQ site, published on GitHub Pages from `main` (custom domain in `CNAME`).

**v2, 2026-11-08: the cinematic site.** It replaces the interim site stood up on 2026-10-02 for toll-free SMS verification. Everything that verification relies on is kept:
- the SMS program block on the home page;
- `sms-terms.html`;
- the privacy policy's mobile-information non-sharing clause;
- the contact form's optional, unticked SMS opt-in (proof-of-consent wording unchanged).

## Pages

| Page | What it is |
|---|---|
| `index.html` | Home: hero over the Earth with al-Biruni's construction drawn live, the thesis, counts, the gated trailer and sign-up, the whole-system sunburst, the six buyer groups, the grand vision, the AI analyst, "it says so", sovereignty, why one engine, the name, what's not built, the finale |
| `editions.html`, `editions/<slug>.html` | All 17 editions. Each page has the industry served, its department modules with descriptions, one analyst question with its guardrail, a film loop, the trailer narration and a sign-up |
| `platform.html` | The engine: enterprise system and five gates, identity-first agent, shared capabilities, the 98-source registry, BirunIQ Field, export, 3D, two clocks, provenance, stack |
| `sovereignty.html` | SaaS, sovereign hybrid, air-gap capable; nothing phones home; the egress gate; separation |
| `trailer.html` | The trailer, behind the sign-up, with chapters and the full transcript |
| `story.html` | The name: al-Biruni's dip-angle construction and the mark |
| `contact.html` and the legal pages | Re-skinned only. Body text unchanged; the build asserts it |

⚠ The legal pages (`about`, `privacy`, `terms`, `eula`, `evaluation-terms`, `attributions`) share their text word for word with the product site (`cartos-Project/website/`). Change both together. Party: Bitruvius, Inc.; law: Delaware.

## Build

- `python tools/build_site.py` writes every page from:
  - `tools/deck-editions.json`: Platform Deck v3 edition content, cleaned of demo-location, partner and vendor names;
  - `tools/catalog-2026-11-08.json`: the module registry;
  - `tools/trailer-transcript.json`: the trailer narration.
  It re-skins the hand-maintained pages by swapping only their head, header and footer, and fails if their body text would change.
- `python tools/build_media.py` writes:
  - the NASA Blue Marble Earth renders, credited in the footer of every page that shows them;
  - the 6-second silent loops cut from the trailer's frames (synthetic or public data only);
  - the trailer poster.
- The two diagrams in `assets/media/diagrams/` come from `cartos-Project/tools/deck/sunburst.py` and `grandvision.py`.

Built from system fonts, inline SVG and vanilla JS, with no libraries and no external requests. The one exception is YouTube's privacy-enhanced player, which loads only after a visitor signs up and presses play. Motion respects `prefers-reduced-motion`.

## Sign-up and the trailer gate

- `assets/signup.js` posts the form to `https://signup.biruniq.com/api/signup`, the Worker in `signup-worker/` (see its README).
- The Worker stores the sign-up in Cloudflare D1 and emails `support@biruniq.com` through Resend.
- It sends the visitor the trailer link and returns the video id. The id is a Worker secret, so it is in neither the pages nor this repo.
- The gate is soft: anyone who already has the YouTube link can watch, so keep the video **Unlisted**.
- Local preview: run `python -m http.server 8765` here and `npx wrangler dev` in `signup-worker/`. `signup.js` talks to `127.0.0.1:8787` when the page is served from localhost.

Still `[TO FILL]` on the contact page: mailing address and toll-free number.
