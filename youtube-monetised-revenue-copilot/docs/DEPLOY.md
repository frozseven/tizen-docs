# Deploying the dashboard so it's installable on your phone + laptop

This turns the local-only web dashboard into a real installable app: a
permanent URL reachable from anywhere, which you then "Install" from the
browser on both your phone and your Windows laptop (a Progressive Web App —
same technique Twitter/X, Spotify Web, etc. use for their installable web
apps). No app store, no separate codebase — it's the same FastAPI app,
just hosted somewhere instead of run locally.

We'll use [Render](https://render.com) — it has a genuine free tier, no
credit card required to start.

## 1. Create a Render account

1. Go to `https://render.com` and sign up (easiest: "Sign up with GitHub").
2. Authorize Render to access your GitHub account. When asked which repos
   to grant access to, choose `frozseven/tizen-docs` (or "All repositories"
   if you're comfortable with that).

## 2. Create the web service

1. In the Render dashboard, click **New +** → **Web Service**.
2. Select the `frozseven/tizen-docs` repository.
3. Fill in these fields exactly:

   | Field | Value |
   |---|---|
   | **Name** | anything, e.g. `wealthsheikh-copilot` |
   | **Branch** | `claude/youtube-monetization-analyzer-s2f9am` |
   | **Root Directory** | `youtube-monetised-revenue-copilot` |
   | **Runtime** | Python 3 |
   | **Build Command** | `pip install -e ".[web]"` |
   | **Start Command** | `uvicorn webapp.app:app --host 0.0.0.0 --port $PORT` |
   | **Instance Type** | Free |

   The Root Directory field is what makes this work even though the rest
   of the `tizen-docs` repo is unrelated Tizen documentation — Render only
   builds/runs from inside that one folder.

4. Don't click Create yet — first add the environment variables below.

## 3. Add environment variables

Still on the create-service screen, find **Environment Variables** and add
each of these (same values as your local `.env` file — type them in fresh,
don't paste screenshots anywhere, including here):

- `YOUTUBE_API_KEY`
- `YOUTUBE_OAUTH_CLIENT_ID`
- `YOUTUBE_OAUTH_CLIENT_SECRET`
- `GEMINI_API_KEY`
- `WEBAPP_USERNAME` — **required here** (unlike localhost, this URL is
  public; anyone who finds it could otherwise spend your Gemini/YouTube
  quota). Pick any username.
- `WEBAPP_PASSWORD` — pick a real password, not something guessable.
- `WEBAPP_OAUTH_REDIRECT_URI` — leave a placeholder for now, e.g.
  `https://placeholder.onrender.com/auth/callback` — you'll fix this in
  step 5 once you know your real URL.

Now click **Create Web Service**. The first build/deploy takes a few
minutes — you'll see build logs streaming live.

## 4. Get your URL

Once it says "Live", Render shows your URL at the top, something like:
```
https://wealthsheikh-copilot.onrender.com
```
That's your permanent app URL — works from any device, any network.

## 5. Fix the OAuth redirect URI (only needed if you'll use "Connect YouTube Analytics")

1. Go back to `https://console.cloud.google.com/apis/credentials`, open
   your OAuth client, and under **Authorized redirect URIs** add:
   ```
   https://wealthsheikh-copilot.onrender.com/auth/callback
   ```
   (your real Render URL + `/auth/callback`) — keep the existing
   `http://localhost:8000/auth/callback` entry too, no need to remove it.
2. Back in Render, go to your service → **Environment**, edit
   `WEBAPP_OAUTH_REDIRECT_URI` to that same real URL, and save (Render
   redeploys automatically when env vars change).

## 6. Visit it and log in

Open your Render URL in a browser. It'll prompt for the
`WEBAPP_USERNAME`/`WEBAPP_PASSWORD` you set — that's HTTP Basic Auth
working as intended.

## 7. Install it as an app

**On your phone (Android, Chrome):** tap the **⋮** menu → **Install app**
(or **Add to Home screen**).

**On your phone (iPhone, Safari):** tap the **Share** icon → **Add to Home
Screen**.

**On your Windows laptop (Chrome or Edge):** look for an install icon in
the address bar (a small monitor-with-arrow, or ⊕) → **Install**.

Either way you now get a real app icon (launches in its own window, no
browser address bar) on both devices, pointing at the same live service.

## Known limitations of the free tier — read before relying on it

- **It sleeps.** After ~15 minutes with no visitors, Render's free tier
  spins the service down. The next visit takes 30–60 seconds to wake back
  up (you'll just see a slow load, not an error) — normal, not broken.
- **The filesystem is not persistent.** Every redeploy (including the
  automatic one whenever new code is pushed to this branch) wipes local
  files. Concretely:
  - The YouTube Analytics OAuth token (`.ytcopilot_token.json`) gets
    wiped on every restart. **Fix this once:** after connecting via
    "Connect YouTube Analytics," the Dashboard shows a box with a refresh
    token to copy into a `YOUTUBE_OAUTH_REFRESH_TOKEN` environment variable
    on Render (Environment tab, same place as your other keys). Once that's
    set and redeployed, restarts no longer wipe the connection — the box
    stops appearing once it detects that variable is set.
  - Anything `ytcopilot plan` generates under `output/` on the server
    should be downloaded/saved locally right after you generate it —
    don't treat the server as permanent storage for scripts/thumbnails.
    (No env-var workaround for this one — it's actual generated files, not
    a small token.)
  - Separately, Google itself expires refresh tokens after 7 days for
    OAuth consent screens still in "Testing" publishing status — persisting
    the token above doesn't help if this hits. Go to Google Cloud Console →
    your project → **APIs & Services → OAuth consent screen** (or **Google
    Auth Platform → Audience**) → **Publish app**. For a personal app only
    you'll ever sign into, this just means a one-time "Google hasn't
    verified this app" warning to click through on your next sign-in — not
    an actual review process.
- **Your API keys live on Render's servers**, not just your laptop, since
  the whole point is that it runs somewhere other than your machine. Only
  you and Render can see them (set as environment variables, not visible
  in the code or the URL), but it's a different trust boundary than
  local-only use.

None of these are bugs — they're inherent to using a free hosted tier
instead of your own always-on machine. If they become annoying, a paid
Render tier (or any other host) removes the sleep/ephemeral-storage
limits; not necessary to start.
