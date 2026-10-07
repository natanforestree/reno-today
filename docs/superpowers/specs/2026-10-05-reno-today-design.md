# Reno Today: design

Date: 2026-10-05 · Status: approved in chat, awaiting review of this written spec

## Why

Nathan and his partner live in Reno and have a son who's about one. Most days
they're trying to work out what to do, which means searching across venue
sites, calendars and Loving Reno (lovingreno.com). Reno Today puts **everything
happening in the Reno area on a given day** in one place. Things you can bring
a toddler to come first, but everything is shown and they use their own
judgement.

**Success:** with morning coffee, in about a minute, they've seen today's
options and picked something they can bring the baby to, without searching
anywhere else. It works for planning the day in the morning and for deciding
last-minute.

## Decisions made in chat

| Topic | Decision |
| --- | --- |
| Area | Reno + Sparks, plus **day trips** (Lake Tahoe, Carson City, Virginia City) marked "worth the drive" with a rough drive time |
| Kid focus | **Two tiers, kept loose:** "Great for little ones" (made for babies/toddlers) at the top, then everything else with light hints (all ages, outdoors, daytime, 21+). Nothing is hidden by default |
| Delivery | A page, **plus a 7:45am Discord message** (webhook into a channel they're both in) with today's picks and a link |
| Look and home | **Cozy pixel style**, matching his other projects, with an **Arcadipelago island showing a pixel Reno Arch** |
| Loving Reno | **Link, don't copy:** a guide card for their current seasonal guide, and a "Loving Reno pick" badge on our events that their guide mentions. Full inclusion only if the blogger says yes (Claude drafts a note for Nathan to send if he wants) |
| Quiet days | An **"Always an option"** list: standing places that suit a one-year-old, with today's hours |

## Architecture

The same proven setup as Ruby Radar (`natanforestree/finals-radar`):

- **New public repo `natanforestree/reno-today`.** GitHub Pages serves `docs/`.
- **`collector/`** is Python with the standard library only, so the Action needs no installs. One module per source, plus shared steps: normalise → classify → merge duplicates → write → digest.
- **A GitHub Actions workflow `collect.yml`** runs the collector and commits `docs/data/` and `state/`.
- **Trigger:** the existing Cloudflare Worker `ruby-radar` (`finals-radar/worker/`) already dispatches finals-radar every 10 minutes. It gains a second target and dispatches reno-today **hourly** (on its `:30` tick). The existing fine-grained token gets `reno-today` added (Nathan edits the token; no new token). GitHub's own schedule stays as an hourly backup, though it's proven unreliable.
- **Each run decides what to do** (times in `America/Los_Angeles` via `zoneinfo`):
  - full refresh if the last one was ≥ 2 h 50 min ago, otherwise exit without committing
  - from 07:00 local, if today's digest hasn't been sent: full refresh, then post the Discord digest, then record the date in `state/digest.json`. The date is recorded only on success, so a failed post retries on the next hourly run; after 10:59 it gives up for the day
  - daylight saving needs no special handling, because decisions use local time

```
Cloudflare cron (hourly) ─▶ GitHub workflow_dispatch ─▶ collector/collect.py
   sources/*  ─▶ normalise ─▶ classify ─▶ dedupe ─▶ docs/data/*.json ─▶ Pages
                                                 └▶ digest ─▶ Discord webhook (07:xx)
```

## Sources

**Phase 1 (verified reachable on 2026-10-05):**

| Source | Covers | Access |
| --- | --- | --- |
| Ticketmaster Discovery API | Concerts, shows, family shows and sports within ~60 mi of Reno (GSR, Silver Legacy, Reno Events Center, Pioneer Center, Tahoe and Carson venues) | Free key (`TICKETMASTER_KEY` secret); 5,000 calls/day, plenty |
| UNR events (Localist) | Campus talks, performances, exhibits | `events.unr.edu/api/2/events`, JSON, no key. Filter out non-Reno extension events |
| Nevada Wolf Pack | Home games | iCal feed `nevadawolfpack.com/calendar.ashx/calendar.ics`; keep home games only |
| Reno Aces | Home games | MLB Stats API `statsapi.mlb.com/api/v1/schedule?sportId=11&teamId=2310`, no key |
| Open-Meteo | Weather for the strip, "nice outside" windows and the digest | No key |
| Loving Reno | Guide card and badges only | Blogger Atom feed `lovingreno.com/feeds/posts/default` |

**Phase 2 (research each, add where they publish a calendar):**
- Washoe County Library: baby and toddler storytimes, likely the best family source
- The Discovery, Wilbur D. May Arboretum & Museum, Nevada Museum of Art
- City of Reno and City of Sparks parks & rec
- Farmers markets and Artown (seasonal)
- Calendars for Tahoe, Carson City and Virginia City

**Source rules:**
- Prefer APIs, iCal or RSS, then schema.org `Event` JSON-LD.
- Read HTML only when `robots.txt` allows it.
- Identify ourselves with a User-Agent that includes the repo URL, and send at most a few requests per source per refresh.
- Store and show only facts (name, time, place, price, link). Never copy write-ups.
- Sites that block programs (e.g. This Is Reno, which returns 403 to its API) are skipped.

## Data

`docs/data/events.json` holds the next 8 days (today + 7), rewritten on each refresh:

```jsonc
{
  "generatedAt": "2026-10-10T14:31:00Z",
  "timezone": "America/Los_Angeles",
  "events": [{
    "id": "tm:Z7r9jZ1A7…",               // source-prefixed, stable across runs
    "title": "Baby & Toddler Storytime",
    "start": "2026-10-10T10:30:00-07:00",
    "end": "2026-10-10T11:00:00-07:00",  // null if unknown
    "allDay": false,
    "ongoing": false,                     // multi-day exhibits/runs: shown in a collapsed "Ongoing" group
    "venue": { "name": "Downtown Reno Library", "address": "301 S Center St", "lat": 39.52, "lon": -119.81 },
    "area": "reno",                       // reno | sparks | tahoe | carson | virginia-city | other
    "drive": null,                        // e.g. "~50 min" for day-trip areas
    "price": { "free": true },            // or { "min": 25, "max": 60 } or null
    "tier": "little",                     // little | general
    "hints": ["all-ages", "daytime"],     // all-ages | outdoors | daytime | 21+
    "links": [{ "source": "library", "url": "https://…" }],
    "lovingReno": null                    // or { "title": "…Fall Guide", "url": "https://…" }
  }]
}
```

Other files:
- `docs/data/status.json`: per-source `{ ok, count, lastSuccess, error }`, used by the page's small "unreachable" notes.
- `docs/data/weather.json`: daily high, low and summary, hourly temperature and rain chance for 8 days, and "nice outside" windows (55–85°F, rain chance < 30 %, daylight).
- `docs/data/guide.json`: the current Loving Reno guide `{ title, url, published }`. No excerpt.
- `places.json` (repo root, hand-kept, copied to `docs/data/`): the Always an option list. Each entry has `name`, `area`, `goodFor` (e.g. "toddler play area"), `indoor`/`outdoor`, `hours` by weekday, `months` (for seasonal places such as splash pads), `url` and `notes`. About 12 places to start, with hours checked against official sites at build time. The page always shows a "check hours" link.
- `overrides.json` (repo root): corrections by id or title pattern, e.g. `{ "match": "…", "tier": "general" }`, `{ "match": "…", "hide": true }`, `{ "match": "…", "addHint": "21+" }`.
- `state/`: last-good events per source (kept up to 24 h when a source fails), `digest.json` (date last sent) and `refresh.json` (time of last full refresh).

## Classification

The rules are deterministic and live in one module, so they're testable and easy to correct:
- **`tier: "little"`:**
  - the title or description has storytime, story time, baby, babies, toddler, lap-sit/lapsit, little ones, preschool, family, families, kids, children, sensory, puppet or play group
  - or the source/category says so: library children's programs, The Discovery, Ticketmaster segment/genre "Family" or "Children's Theatre"
  - never when the event is 21+
- **`21+`:**
  - Ticketmaster age-restriction fields
  - or the text has 21+, 21 and over, 18+, bar crawl, pub crawl, wine tasting, beer tasting or burlesque
  - or the venue is on a short list of casino lounges and bars
- **`daytime`:** starts before 17:00. **`outdoors`:** a park or outdoor venue, or words like park, trail, festival grounds, outdoor or market. **`all-ages`:** stated by the source.
- `overrides.json` is applied last.

## Merging duplicates

The same event from two sources (e.g. UNR and Ticketmaster) is merged when it has the **same local date**, **start times within 30 minutes** and either **matching normalised titles** (lowercase, punctuation and filler words removed, token overlap ≥ 0.8) or **the same venue with a title token overlap ≥ 0.6**. The merged event keeps every link and takes each field from the most specific source (ticketing for price, the venue's or organiser's own feed for time and place).

## Page

Phone first, in cozy pixel style. The header is the pixel Reno Arch (neon RENO, red banner, chasing bulbs) against a dusk sky. Fonts and palette suit Reno: sage, sunset orange, Sierra blue, neon red and pink, on a warm dark background. Order:

1. **Day switcher:** Today · Tomorrow · the next 6 days.
2. **Weather strip:** high/low, a summary, and the "nice outside" window note.
3. **Filter chips:** Free · Outdoors · Little ones only · Hide 21+ · Live music (stored in localStorage; nothing is filtered by default). Live music with Hide 21+ is the all-ages live music view.
4. **👶 Great for little ones:** in time order.
5. **Everything else,** grouped **Morning / Afternoon / Evening / Late**. Each card has time, name, place (+ area if not Reno), price or **Free**, hint badges, a **Loving Reno pick** badge, and links to the source page and directions (a Google Maps search link). Today's in-progress events are marked **"on now"**.
6. **Ongoing:** collapsed exhibits and multi-day runs.
7. **🚗 Worth the drive:** day-trip areas with drive times from a static table (Carson ~35 min, Virginia City ~40 min, Tahoe ~45–60 min by town).
8. **Always an option:** places open on the chosen day, with that day's hours. Expanded when fewer than 3 "little ones" events, otherwise collapsed.
9. **Loving Reno guide card.**
10. **Footer:** sources, "unreachable this morning" notes from `status.json`, when it last updated, and a link back to Arcadipelago.

Plain JavaScript, no build step. All text from data is escaped. It works with an empty or partial `events.json`.

## Discord digest (07:xx Pacific)

Posted with the `DISCORD_WEBHOOK_URL` secret as plain message content (≤ 2,000 chars, trimmed to fit):

```
☀️ Saturday, Oct 10 · 64° → 78°, sunny
👶 For little ones
• 10:30 Baby & Toddler Storytime · Downtown Library · free
🎟️ Also today
• 1:05 Reno Aces vs Sacramento · Greater Nevada Field
🚗 Worth the drive: Lake Tahoe Oktoberfest (Tahoe City, ~50 min)
🏠 Always an option: The Discovery 10–5 · Idlewild Park
📖 Loving Reno: 2026 Halloween & Fall Guide
Full list → https://natanforestree.github.io/reno-today/
```

- Up to 5 items per section, and empty sections are skipped.
- "Always an option" appears when there are fewer than 3 little-ones events.
- "Also today" prefers free, all-ages and daytime events, then the rest.

## Loving Reno

- The **guide card** shows the newest feed post whose title contains "Guide" (or the newest post): its title, date and link only.
- **Badges:**
  - Fetch the current guide post's HTML (one request per full refresh; their robots.txt allows it).
  - For each event with a distinctive title (≥ 3 significant words, or a title plus venue match), set `lovingReno` when the guide's text contains it.
  - Only the guide's title and URL are stored.

## Arcadipelago island (phase 3)

A new island `island-reno-today` in `natanforestree/arcadipelago`:
- **The arch:** a pixel Reno Arch with neon RENO tubes (pink and red, with a gentle flicker), the red "biggest little city" banner (its text abstracted or tiny at this scale), chasing bulbs and the starburst on top.
- **The island:** a small chunk of Virginia Street with lamp posts, on the floating rock.
- **Animation:** 12 frames, following the README's "Adding a game" steps and the https link-out pattern.
- **Layout:** the front page already has 6 islands and both stages are full, so this phase includes re-laying out all islands for both layouts, kept passing the layout tests.

## Setup Nathan does (Claude drives where allowed)

1. Sign up for a free Ticketmaster developer key. Nathan creates the account; Claude stores the key with `gh secret set`.
2. Create a Discord webhook in the chosen channel (channel settings → Integrations → Webhooks). It's stored the same way.
3. Edit the existing fine-grained GitHub token to add `reno-today`, Actions read/write.

## Errors

- **Sources:** each is collected independently, with a timeout and one retry. A failure keeps that source's last-good events for up to 24 h and marks it in `status.json`. The page shows a small note, and the run still succeeds.
- **No events at all** (every source failed): don't overwrite `events.json`; keep the previous file and mark the status.
- **Discord failure:** the digest date isn't recorded, so the next hourly run retries; after 10:59 local it gives up for the day.
- **Ticketmaster rate or quota errors:** back off and skip that source for this run.

## Testing

- **Source parsers:** Python `unittest` with saved real responses in `tests/fixtures/` (recorded once during build), asserting the normalised events.
- **Classifier:** a table of real event titles and descriptions with their expected tier and hints.
- **Dedupe:** pairs that should and shouldn't merge.
- **Scheduler:** "should this run refresh / digest?" for given local times and state, including the DST change days.
- **Digest:** formatting, trimming to 2,000 chars, and skipping empty sections.
- **Page:** a fixture generator (`dev/make_fixture.py`) plus checks in a real browser (Playwright) at 390 px and 1280 px, covering the empty, partial and source-failure states.
- **Worker:** extend the existing tests for the second dispatch target.

## Phases

1. **Core:** repo, collector framework, Ticketmaster, UNR, Wolf Pack, Aces, Open-Meteo, the page with pixel header, the Discord digest, the Worker trigger, and the Loving Reno guide card.
2. **Family:** research and add the library, museums, parks & rec, markets and the day-trip calendars, plus the Always an option list (`places.json`).
3. **Polish:** Loving Reno badges, plus the Reno Arch island and the Arcadipelago re-layout.

## Out of scope (for now)

Map view, accounts or submissions, a weekend-preview message, notifications other than Discord, personalisation beyond the filter chips, and copying Loving Reno's guide events (unless they give permission).

## Risks

- **Family sources may not publish calendars.** The Always an option list keeps quiet days useful regardless.
- **HTML sources break when sites change.** The parser tests show which one, and the page degrades gracefully per source.
- **The Discord webhook URL is effectively a password.** It lives only in repo secrets; if it leaks, regenerate it in Discord.
- **Ticketmaster coverage of small venues is thin.** Phase 2 sources and the Holland Project/Cypress-type venues fill in where they publish calendars.
