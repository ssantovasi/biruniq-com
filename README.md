# biruniq.com

Interim public site for BirunIQ, published on GitHub Pages (custom domain in `CNAME`).
Stood up 2026-10-02 for toll-free SMS number verification; to be replaced later.

- `index.html` — landing page: what BirunIQ is, the SMS program, contact
- `privacy.html` — privacy policy, including the mobile-information non-sharing clause carriers check for
- `contact.html` — contact form with the optional, unticked SMS opt-in checkbox (Twilio proof-of-consent URL). Static: set FORM_ENDPOINT (form service) or FALLBACK_EMAIL in its script
- `terms.html` — website Terms & Conditions
- `sms-terms.html` — SMS terms: program, opt-in, frequency, rates, STOP/HELP

Plain static HTML, system fonts, no external requests. Every `[TO FILL: …]` must be
replaced with real business details before the toll-free verification is submitted.
Brand assets come from `cartos-Project/docs/ip-protection-pack/biruniq-brand/svg/`.
