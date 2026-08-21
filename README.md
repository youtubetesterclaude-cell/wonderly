# Autonomous Faceless YouTube Channel Pipeline

An automated content pipeline that generates, produces, and uploads short videos,
then reallocates effort toward whichever niche/format performs best — a simple
multi-armed-bandit strategy driven by real YouTube Analytics data.

## How it works (the loop)

```
allocator.py  →  picks which niche/format to try this run (weighted by past performance)
       ↓
topic_gen.py  →  Gemini (free tier) generates a specific topic within that niche
       ↓
script_gen.py →  Gemini (free tier) writes the narration script
       ↓
tts_gen.py    →  edge-tts converts script to voiceover (free)
       ↓
visuals.py    →  pulls matching stock clips/images from Pexels (free)
       ↓
assemble.py   →  FFmpeg stitches voiceover + visuals + auto captions into an MP4
       ↓
thumbnail.py  →  generates a thumbnail (text overlay on a still frame)
       ↓
upload.py     →  uploads to YouTube via Data API, saves video_id + niche/format tag
       ↓
   ... 48-72 hrs later ...
       ↓
track.py      →  pulls views/CTR/avg-view-duration/likes via Analytics API,
                  updates performance_log.json
       ↓
allocator.py  →  next run, reads performance_log.json and shifts weight toward winners
```

This is a **weighted-random bandit**, not true reinforcement learning — simple,
transparent, and good enough at low volume. You can see exactly why it picked what
it picked by reading `data/performance_log.json`.

## What you need to set up (do this first — nothing runs without these)

### 1. Gemini API key (free)
- Sign up at aistudio.google.com, create an API key (no credit card needed)
- Uses a Flash model (e.g. gemini-2.5-flash) — Pro models were removed from
  the free tier in April 2026, but Flash is plenty capable for short scripts
  and stays free at low volume (roughly 10-15 requests/min, up to 1,000/day)
- Note: your Google AI Pro subscription doesn't automatically grant free API
  quota for scripts run outside AI Studio's own interface — this separate,
  free API key is what the pipeline actually needs

### 2. Pexels API key (free)
- Sign up at pexels.com/api — instant, free, generous free quota

### 3. YouTube Data API + OAuth credentials (free)
- Go to Google Cloud Console → create a project → enable "YouTube Data API v3"
  and "YouTube Analytics API"
- Create OAuth 2.0 credentials (Desktop app type)
- Download the credentials JSON, run `scripts/youtube_auth_setup.py` once locally
  to generate a refresh token (this needs a browser — can't be done in CI)
- **Important:** your channel needs to be verified for uploads longer than 15 min,
  and Google's OAuth consent screen stays in "testing" mode (100 users cap, fine
  for personal use) unless you submit for verification

### 4. A YouTube channel
- Create it, set it up (banner, description, etc. — do this manually, once)

## Where your API keys actually go

You'll end up with 5 key/secret values total (Gemini, Pexels, and 3 YouTube
OAuth values). Where they go depends on how you're running the pipeline —
**pick one, not both**:

**Running locally on your machine:**
Put them in a file named `.env` in the project root (copy `.env.example` to
`.env` first, then fill in the real values). The pipeline loads this
automatically — nothing else to configure. This file is git-ignored on
purpose; never commit it.

**Running on GitHub Actions (the "autopilot" schedule):**
`.env` files don't work here — GitHub Actions doesn't read them. Instead you
add each value as a **repo secret**: on GitHub, go to your repo →
**Settings → Secrets and variables → Actions → New repository secret**, and
add each of these one at a time (name exactly as shown, value = your actual key):
- `GEMINI_API_KEY`
- `PEXELS_API_KEY`
- `YT_CLIENT_ID`
- `YT_CLIENT_SECRET`
- `YT_REFRESH_TOKEN`

The workflow files in `.github/workflows/` already reference these exact
secret names (`${{ secrets.GEMINI_API_KEY }}` etc.) — you don't need to edit
the workflow files, just add the secrets with matching names in the GitHub UI.

## Running it

**Locally (to test):**
```bash
pip install -r requirements.txt
python scripts/main_pipeline.py --once
```

**On autopilot (GitHub Actions):**
1. Push this repo to a **private** GitHub repo (private repos get 2000 free
   Actions minutes/month — plenty for this)
2. Add the 5 secrets above via Settings → Secrets and variables → Actions
3. The workflow in `.github/workflows/pipeline.yml` runs on a schedule
   (default: every 2 days) — edit the cron line to change frequency
4. A second workflow, `.github/workflows/track_performance.yml`, runs daily
   to pull analytics and update the bandit weights

## Realistic expectations (read this before you get excited)

- **This will not guarantee views.** The bandit optimizes *among the ideas you
  give it* — it can't invent a genuinely good idea out of nothing. Garbage niches
  in, garbage results out, just faster.
- **YouTube actively demonetizes/suppresses "reused/low-effort" content** —
  channels that are 100% templated AI voiceover + stock footage with zero
  original editing are a known enforcement target as of 2024-2025 policy updates.
  Add some genuine variation (custom b-roll, original thumbnails, a consistent
  voice/persona) or expect throttling.
- **Budget a few hours/week of human review anyway.** Fully unsupervised
  pipelines drift — scripts get repetitive, TTS mispronounces things, thumbnails
  get weird. Spot-check the queue before it publishes, at least early on.
- **Start at low volume** (1 video every 2-3 days across 3-4 niches) so you don't
  burn API quota or flood your channel with unwatched backlog before you know
  what's working.

## File structure

```
ai-youtube-channel/
├── scripts/
│   ├── allocator.py       # bandit logic — decides niche/format for next video
│   ├── topic_gen.py       # Claude: pick specific topic
│   ├── script_gen.py      # Claude: write narration script
│   ├── tts_gen.py         # edge-tts: script -> audio
│   ├── visuals.py         # Pexels: fetch matching stock clips
│   ├── assemble.py        # FFmpeg: stitch video + captions
│   ├── thumbnail.py       # generate thumbnail
│   ├── upload.py          # YouTube Data API upload
│   ├── track.py           # YouTube Analytics API pull
│   ├── youtube_auth_setup.py  # one-time OAuth setup (run locally)
│   └── main_pipeline.py   # orchestrates the full loop
├── workflows/
│   ├── pipeline.yml       # GitHub Actions: content generation schedule
│   └── track_performance.yml  # GitHub Actions: analytics pull schedule
├── data/
│   ├── niches.json        # your niche/format definitions — EDIT THIS
│   └── performance_log.json  # bandit's memory (auto-generated)
├── requirements.txt
└── .env.example
```

## Next steps after setup

1. Edit `data/niches.json` — define your 3-5 starting niches/formats
2. Run `python scripts/youtube_auth_setup.py` locally once
3. Test with `python scripts/main_pipeline.py --once` before scheduling
4. Watch the first few outputs manually before trusting the schedule
