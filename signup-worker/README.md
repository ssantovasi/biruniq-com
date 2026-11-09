# biruniq.com sign-up Worker

This Worker receives the sign-up form on biruniq.com:
- It stores each sign-up in Cloudflare D1 (`biruniq-signups`).
- It emails a notification through Resend to `NOTIFY_TO`, a Worker secret holding Steven's inbox. support@biruniq.com's Cloudflare forward silently dropped Resend mail on 2026-11-08.
- It emails the visitor a confirmation with the trailer link.
- It returns the trailer's video id, so the site can show the player.

The video id is a Worker secret, so it appears in neither the page source nor this public repo. The gate is still soft: anyone who already has the YouTube link can watch. The video should be **Unlisted** on YouTube.

## Deploy (once)

```
cd signup-worker
npx wrangler login                                  # opens a browser; sign in to the Cloudflare account that holds biruniq.com
npx wrangler d1 create biruniq-signups              # paste the database_id into wrangler.toml
npx wrangler d1 execute biruniq-signups --remote --file schema.sql
npx wrangler secret put RESEND_API_KEY              # sending-only key for the biruniq.com domain
npx wrangler secret put IP_SALT                     # any long random string
npx wrangler secret put VIDEO_ID                    # the trailer's YouTube id (kept out of this public repo)
npx wrangler secret put NOTIFY_TO                   # the inbox that receives sign-up notifications
npx wrangler deploy                                 # creates https://signup.biruniq.com
```

Test it with:

```
curl -s -X POST https://signup.biruniq.com/api/signup -H "Origin: https://biruniq.com" -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"support@biruniq.com","organisation":"Test","consent":true}'
```

## Reading sign-ups

```
npx wrangler d1 execute biruniq-signups --remote --command "SELECT created_at,name,email,organisation,role,interests FROM signups ORDER BY id DESC LIMIT 50"
```

## Abuse controls

- **Honeypot field.** A hidden form field that people never fill in.
- **Rate limit.** Five sign-ups an hour per network. The limit counts a salted hash of the IP; the raw IP is never stored.
- **Field length limits.**
- **CORS.** Only `biruniq.com` and `www.biruniq.com` can call the Worker.
- **Not yet added:** a challenge such as Cloudflare Turnstile. Add one if spam appears.
