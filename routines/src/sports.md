Write my weekly sports brief and publish it via the git pipeline. Use today's date (Monday) in Europe/Zurich.

The repo (`khalic-lab/claude-routines`) is cloned as your working directory. Before doing anything else, sync:

```bash
git pull --ff-only origin main
```

# Mission

A weekly Monday read on the past 7 days of sport, written for a smart reader who does NOT closely follow sport — anchored to what matters from Switzerland plus the global majors. Coverage window: the past 7 days (roughly last Monday through Sunday).

**Scope — Swiss + global majors:**
- **Football (the spine):** Swiss Super League + the Swiss national team; UEFA competitions (Champions League, Europa League, Euro/Nations League); the big-5 European leagues (Premier League, LaLiga, Serie A, Bundesliga, Ligue 1); plus the summer/winter transfer windows when open.
- **Formula 1 & motorsport:** race results, championship standings, FIA rulings and penalties, team/driver moves.
- **Tennis:** ATP/WTA tournaments and Grand Slams, ranking moves, Swiss players.
- **Winter sports & the rest:** alpine skiing World Cup (big in CH), ice hockey (Swiss National League + NHL headlines), and a catch-all for cycling (Tour de Suisse / de France), athletics, and other genuinely notable events.

**The trap to design against (read this before selecting anything).** A box score is a commodity — every outlet on earth has the same final score. A brief that just lists results is exactly the aggregator-shape this pipeline treats as failure, not a product. Your job is the layer a scoreboard cannot give: **what the result MEANS** — what it did to the title race, the qualification math, the relegation fight, the championship standings; the story behind it; and, because the reader doesn't follow sport, the context that makes it legible (who these teams/athletes are, what was at stake, why anyone cares). Lead with meaning, never with the score.

**Seasonality — omit ruthlessly.** Sport is seasonal: football runs Aug–May with a summer transfer window; F1 runs Mar–Dec; alpine skiing Dec–Mar; tennis has a grass/hard/clay calendar; hockey Sep–Apr. A desk that is out of season this week has no section — no placeholder, no "the season hasn't started." In a quiet mid-summer week the brief may be mostly the football transfer window plus F1 and tennis; in deep winter it may be skiing and hockey with football. Follow the calendar, not this list's order.

<!-- include: _shared/newsroom-ethos.md -->

**Beat tag for THIS stream (overrides the general beat list above):** sports is a single-topic stream — tag EVERY story you record with `topics: ["sports"]` (one beat; the stream itself is the beat). Do not use `switzerland`/`world`/etc. for sports stories; favouring Swiss content happens in what you SELECT, not in the beat tag. `importance` still ranks across the whole edition as usual.

# Sourcing rules (non-negotiable)

The "primary source" in sport is the authoritative first-hand record, not the punditry or aggregation on top of it.

1. **Tiers.**
   - **T1 = primary:** the official result/standings from the league or governing body itself (Swiss Football League, UEFA, FIFA, Premier League & the big-5 leagues, Formula1.com / FIA, ATP / WTA, FIS, Swiss National League / IIHF, IOC); official club / federation / team **announcements** (transfers confirmed, injuries, roster and contract moves, disciplinary decisions); on-record **press-conference** statements and official athlete/club channels; and **rulings** from CAS (Court of Arbitration for Sport, Lausanne) and WADA. This is the sports analogue of "a number / ruling / release moved."
   - **T2 = quality secondary:** reputable sports journalism (BBC Sport, The Athletic, L'Équipe, kicker, Gazzetta dello Sport, Autosport; Swiss: SRF Sport, Blick, NZZ, RTS). Use it for narrative, context and triangulation — cite it alongside, not instead of, the primary.
   - **T3 = discovery only:** social / Reddit / forums / rumour accounts — used to FIND a story, NEVER cited. Click through to the official source.
2. **The transfer / rumour exception (the one place sport differs).** For transfers, a tier-1 reporter often breaks the fact BEFORE the club confirms. Discipline: **the official confirmation is the fact.** Report a completed move only once the club/federation has announced it (link the official announcement). Anything earlier — talks, "advanced negotiations", a medical booked, a fee agreed — is labelled explicitly and tagged `[rumour]` / `[unconfirmed]`, with the stage named ("personal terms agreed, no club-to-club deal") and the reporting source named. Never launder a rumour into a done deal. **Sourcing an unconfirmed scoop (resolves the T3 tension):** the best transfer reporters (Romano, Ornstein, …) often break first on social — but social stays **never-cited**, even here. So: cite a **T2 outlet's write-up** that names the same reporter and stage (most reputable outlets republish within hours) — never link the raw social post. If no T2 write-up exists yet, **hold the item** rather than cite social directly; a rumour is not so time-critical that it must ship this week uncorroborated.
3. **Citation format.** Every item ends with a markdown link to one specific URL (official result page, federation release, ruling PDF, or article landing). Include the source name and date. No "according to reports" without a link.
4. **Triangulation.** A contested or reported-not-confirmed claim needs two independent sources where feasible; single-sourced → tag `[single-source]`; disagreements → surface both versions.
5. **Tags.** Unconfirmed/negotiating → `[rumour]` / `[unconfirmed]`. Single source → `[single-source]`. Contested → `[disputed]`.
6. **No fabrication.** Never invent a score, a scorer, a time, a table position, a quote, a transfer fee, or a URL. **This extends to dates and results**: if you cannot verify a result actually happened in the past 7 days, do not report it under a section that claims this week. When you cannot fetch an official result, say so — do not reconstruct a scoreline from memory.
7. **Volume cap.** 3–7 items per desk, quality-capped. Better 3 results that genuinely moved something than 7 padded fixtures.
8. **Fetch transparency.** Confirmed fetch → no marker. Search-snippet-only citation → append `[via snippet]`.

<!-- include: _shared/reader-profile-source-weights.md -->

<!-- include: _shared/feed-first-source-order.md -->

## Sports fetch mechanics (specific to this stream)

Most official sports sites (uefa.com, fifa.com, premierleague.com, formula1.com, atptour.com, …) are heavy JavaScript SPAs behind Cloudflare — a proxy fetch often returns a JS shell, not the results data. Work around it:

- **`tools/fetch.py --proxy` first** for any official site the preflight marks `method: proxy`; a wrapper success with real content is a direct fetch. When the proxy returns only a JS shell or a challenge, don't fake a result — fall to the next option.
- **Feeds and directly-fetchable secondaries** are your reliable spine: BBC Sport RSS (`https://feeds.bbci.co.uk/sport/rss.xml`) and SRF Sport, both direct on the wrapper's first attempt — they carry results and reports with links back to the primary; cite the official page as the primary where you can reach it, the outlet as T2 where you cannot.
- **Wikipedia season/results pages** (e.g. "2026 Formula One World Championship", "2025–26 Swiss Super League") are comprehensive and directly fetchable — use them to **cross-check** scores, standings and dates, but Wikipedia is tertiary: never cite it as the primary, and prefer the official result page for the citation.
- **Official news/press-release pages** (fia.com/news, wada-ama.org/en/news, tas-cas.org media releases, club press rooms) are usually more fetchable than the live-scores SPA and are the correct primary for announcements and rulings.
- If you genuinely cannot reach a primary and rely on a T2 report for a result, tag the item `[single-source]` and name the outlet; note unreachable official sites in the Gaps footer.

# Research methodology

1. **Source plan first** — run the preflight (above), then sweep its fetch list: BBC Sport / SRF feeds via curl; official league/governing pages via the proxy; Wikipedia results pages via curl for cross-check.
2. **Establish the week's window** — build the dated weekday table (date-discipline below) so "this week" = the correct past-7-day span, and every fixture/result is dated correctly.
3. **Per desk in season:** find the results and announcements that actually moved something; read the official page; decode what changed and why it matters.
4. **Transfers:** separate confirmed (official) from reported (tag `[rumour]`); name the stage and the source.
5. **Cross-check** scores, scorers, standings and dates against a second source (Wikipedia results table is fine for cross-check only).
6. **Stop** when the genuinely-significant items are covered — do not pad to fill a desk.

# Sections (in order — OMIT any desk out of season or with nothing that moved)

Favour Swiss-relevant items throughout (Super League, the Swiss national team, Swiss athletes) — they get more space than an equal-weight foreign item, per the reader profile. If there is a notable Swiss sport story, it is a strong candidate for the edition lead.

## ⚽ Football

Swiss Super League + Swiss national team first, then UEFA competitions and the big-5 leagues. For each result that matters: what it did to the table / title race / European qualification / relegation, not just the score. **Transfers** live here — confirmed moves as fact (official announcement linked), everything else tagged `[rumour]` with the stage and source named. During a transfer window this may be the bulk of the desk.

## 🏎️ Formula 1 & motorsport

The race result and — more importantly — what it did to the drivers' and constructors' championships; FIA rulings, penalties and technical directives; confirmed driver/team moves. Omit entirely outside the F1 calendar.

## 🎾 Tennis

ATP/WTA tournament outcomes and Grand Slams, ranking moves, and Swiss players. Explain what a title or result means for the season/rankings race. Omit if the calendar is dark this week.

## ⛷️🏒 Winter sports & the rest

Alpine skiing World Cup (favour Swiss racers), Swiss National League + NHL headlines, and a catch-all for cycling (Tour de Suisse / de France), athletics, and other notable events. In-season only; omit anything with nothing new.

## 🧠 Why it matters (the one place to be opinionated — include only if warranted)

1–2 synthesis threads across the week: a title race tightening, a qualification picture, a shifting era, a governance/doping story with real stakes. This is the single highest-value part of the brief — the thing a scoreboard cannot do. Omit if no genuine thread emerged; do not manufacture one.

# Format

```
# Sports — {YYYY-MM-DD}

_Generated {ISO timestamp} Europe/Zurich. Coverage: {date 7 days ago} to {today}._

## ⚽ Football

### [What happened, in a phrase — e.g. "Basel open a 4-point Super League lead"]
**[Official result / announcement](URL)** · {competition / matchday} · {date} · `[rumour]` (only if unconfirmed)
2–4 sentences in your own words: the result, then immediately what it MEANS (table/race/qualification/relegation implication), then the context a non-follower needs (who, what was at stake). Name confirmed vs reported for transfers.
*Why it matters:* one-line plain-language take.

## 🏎️ Formula 1 & motorsport
[same item format — result then championship implication]

## 🎾 Tennis
[same item format]

## ⛷️🏒 Winter sports & the rest
[same item format]

## 🧠 Why it matters
- ...

---

## Coverage footer
<!-- operational telemetry — the computed lines (tier split, direct-vs-snippet, word count,
token estimate, Feeds hit) are filled in by the publish command (tools/footer.py); write ONLY:
- Items: N (filtered from M reviewed) — Football: N, F1/motorsport: N, Tennis: N, Winter/other: N
- Confirmed vs reported: {N confirmed, N tagged [rumour]}
- Languages: {languages of your cited sources, e.g. EN, FR, DE}
-->
- Gaps: things you tried to find but couldn't (unreachable official sites, unverified results).
- Discovery: {met (<new domain(s) anchored>) | waived — <concrete reason>}
```

# Constraints

- **Lead with meaning, never the score.** Every item's first job after the headline is what the result changed. A bare scoreline with no implication does not earn a place.
- **Confirmed vs reported is a hard line.** Only official announcements are reported as fact; everything else is tagged `[rumour]`/`[unconfirmed]` with the stage and source named.
- Dates and identifiers matter: put the match/event date next to each item; get table positions and championship points right (cross-check).
- Length: 1200–2500 words (weekly window, in-season desks only). Don't pad — ship the strong items and stop.
- Write in English. French/German/Italian source titles can stay in original language inside link text.
- Discovery aggregators and rumour accounts (Reddit, X, forums) → never cited as source.

<!-- include: _shared/pedagogical-tone.md -->

# Story deduplication (best-effort — never abort the brief on failure)

Before composing AND after writing the brief, follow `tools/dedup/DEDUP.md` exactly. It dedupes your candidate stories against the rolling embeddings index so a story isn't re-run week to week. **This routine's slug is `sports`.** If any dedup step errors, compose normally and note "dedup unavailable" in the Gaps footer.

<!-- include: _shared/date-discipline.md -->

# Output: write the brief to git + drop a notification stub

This routine writes to the git repo (working directory is the cloned `claude-routines` repo). It does NOT write to Google Drive, does NOT POST to ntfy directly, and does NOT send email. A local bridge polls `pending-notifications/` every ~10 min and handles the ntfy push.

Individual brief pages are retired (2026-07-18): the homepage story feed at
`https://khalic-lab.github.io/claude-routines/` carries every story's full prose, and the
notification stub the publish command writes clicks through there.

### 1. Write the brief

Use the Write tool to create `_posts/{YYYY-MM-DD}-sports.md`. The file MUST start with this front-matter block, then a blank line, then the brief body:

```
---
layout: single
title: "Sports — {YYYY-MM-DD}"
date: {full ISO 8601 timestamp WITH timezone offset, identical to the _Generated line — e.g. 2026-07-20T09:04:12+02:00; NOT a bare date, which makes same-day briefs sort out of chronological order}
categories: [sports]
---
```

### 2. Publish — one command

Everything after the brief file is deterministic and runs through the orchestrator: dedup record → anchors → computed footer telemetry → source lint → registry/institutions sync → date lint → homepage feed + stats → source health → notification stub → commit → push, with the homefeed rebase-conflict retry built in.

```bash
python3 tools/publish.py --slug sports --date {YYYY-MM-DD} \
  --final /tmp/final.json \
  --notify-title "Sports — {YYYY-MM-DD}" \
  --notify-body "{teaser}" --notify-tags soccer
```

- `{teaser}` rules: ≤200 chars. The single most significant thing this week — the result that moved a title race, a marquee transfer confirmed, an F1 championship swing, a Swiss athlete's win. Concrete (e.g. "Basel go 4 clear at the top; Verstappen cuts the gap to 12 after Spa; Wimbledon final set"), not generic. Pass it as a normal shell argument — the stub is JSON-encoded for you, no manual quote-escaping.
- If dedup was unavailable (Step A failed), omit `--final` — every other step still runs; note "dedup unavailable" in the Gaps line before publishing.
- The orchestrator prints one OK/FAIL line per step and, if the final push fails after its built-in retry, notes it in the brief itself. Do not re-run the git steps by hand, and do not write the stub or telemetry yourself.
