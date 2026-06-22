# Prior-Art Survey — Reader-Feedback Loops for AI-Generated Briefs

Compiled 2026-06-08. Covers **new ground only** — source credibility (A) and editor+writer
patterns (B) are in `PRIOR-ART-2026-05-31-credibility-and-editor.md`; the 7-day brief audit
is in `AUDIT-2026-05-31-briefs.md`. This document covers: (C) product patterns for
lightweight feedback capture and consumption, (D) the n=1 solo-reader problem, (E) ntfy
action-button capability verdict, (F) the write-only anti-pattern and how to close the loop.

---

## C. Product patterns — feedback capture and what consumes it

### C1. ChatGPT thumbs + memory (OpenAI)

ChatGPT presents thumbs-up / thumbs-down on every response. At the population level, these
signals historically fed RLHF reward-model training — crowdsourced preference pairs used to
update the model weights. The sycophancy regression in July 2025 (GPT-4o rollback) was
directly caused by over-weighting short-term thumbs-up signals over long-term satisfaction,
illustrating the gap between "user clicked thumbs-up" and "user was actually better served"
([Valentus summary of the rollback](https://valentusproducts.com/gpt4o-sycophancy-july-2025-rollback/)).

Since April 2025, ChatGPT also maintains a **persistent memory store** — key-value notes
auto-generated from conversations — that is injected into future system context. This is the
closest existing product implementation of the profile-in-prompt pattern for a single user:
explicit user preferences (diet, style, priorities) are extracted from interactions and stored
as discrete memory notes; the model reads them at the start of each session
([OpenAI Memory announcement](https://openai.com/index/memory-and-new-controls-for-chatgpt/)).
The memory is editable and deletable. Crucially, the thumbs-feedback and the memory-update
are **two separate mechanisms** — the thumbs go to OpenAI's training pipeline; the memory
updates the individual user's context. At n=1, the memory mechanism is what matters.

**Signal → consumption path**: user action (chat content, explicit save) → memory note
written → injected into future system prompt. Thumbs → training data → (eventual) model
update → affects all users, not just the one who clicked.

### C2. Netflix double-thumbs / YouTube "not interested" / Google Discover

**Netflix** replaced 5-star ratings with thumbs in 2017, added "double thumbs up" in 2022
([About Netflix announcement](http://about.netflix.com/en/news/two-thumbs-up-even-better-recommendations)).
The explicit rationale: stars measured "how much you'd rate a title" (a memory judgment);
thumbs measure "would you watch something like this" (a forward-looking taste signal). The
three tiers — double-up / up / down — create gradient signal without requiring free text.
Netflix's 2024 TechBlog post on long-term satisfaction
([netflixtechblog.com, Aug 2024](https://netflixtechblog.com/recommending-for-long-term-member-satisfaction-at-netflix-ac15cada49ef))
draws a sharp distinction between short-term click signals and long-term retention signals:
the documented problem is that feedback is **delayed and often missing** — a member may watch
a few minutes on day one and only complete the show weeks later; many members never rate at
all. The paper's framing is that optimizing on immediate engagement proxies (clicks, starts)
can diverge from what members find valuable over time. It also notes the **feedback-lag
tradeoff**: waiting longer for delayed signals produces more accurate reward estimates but
makes the policy stale, which degrades recommendation quality for new items. The specific
retraining cadence and retention windows are internal and not published.

**Google Discover** offers "Not interested in this story", "Not interested in [topic]", and
"Don't show content from [source]". These operate at three levels of granularity. The
publisher-level block fires **before** any interest-matching or ranking; a dismissed URL is
permanently excluded. The topic-suppression signal updates a preference weight for a category.
Per Google's support documentation, dismissals carry more weight per interaction than positive
clicks — the penalty for a dismissed story is larger than the uplift for a clicked one
([Google Search Help](https://support.google.com/websearch/answer/2819496)).

**YouTube** "Not interested" and "Don't recommend channel" work analogously: URL-level
suppression is permanent and pre-filters before ranking; the channel-level block removes the
source entirely. These are the canonical product patterns for **asymmetric feedback weighting**
— negative signals are structurally more valuable per click than positive ones.

**Key pattern across all three**: the signal is captured in one of three registers:
1. **URL/item-level** — never surface this specific item again (permanent, high-confidence)
2. **Topic/category-level** — reduce weight for this semantic cluster (probabilistic, decays)
3. **Source-level** — suppress this publisher entirely (permanent, binary)

### C3. Feedly Leo AI — per-user priority feed

Feedly's Leo AI lets users train a per-account feed: mark an article as "good job" or "bad
job", follow keywords or sources to boost, mute keywords or sources to suppress. Leo applies
these as a pre-rank filter — prioritized articles get a green badge indicating why Leo
surfaced them. The critical design decision is that **explicit Leo training overrides implicit
engagement signals** — a "mute this keyword" command fires immediately and permanently, while
click-dwell time is a weaker slower signal
([Feedly Leo documentation](https://docs.feedly.com/article/769-saving-ai-feeds-feedly)).
This is the product equivalent of "explicit preference beats inferred preference at n=1".

### C4. Artifact "tune your feed" (2023, now defunct)

Artifact (Instagram cofounders, Jan 2023 – Jan 2024) offered:
- Topic-level sliders: "show more / show less of [topic]"
- Source-level pause/block: suppress a publisher
- Thumbs up/down on individual stories

The personalization model was topics × sources × authors as the three-vector preference space.
Importantly, Artifact's post-shutdown comment was not "personalization didn't work" but "the
market isn't big enough" — confirming the feedback mechanism functioned but the product
context didn't differentiate. Yahoo acquired it and folded the personalization tech into Yahoo
News
([Artifact Wikipedia](https://en.wikipedia.org/wiki/Artifact_(app)),
[TechCrunch public launch](https://techcrunch.com/2023/02/22/instagrams-co-founders-personalized-news-app-artifact-launches-to-the-public-with-new-features/)).

### C5. Newsletter footer ratings — beehiiv polls / SparkLoop Reactions

Newsletter platforms have standardized on a one-click emoji-rating pattern: "How was this
issue? 😀😐☹️" inline in the email footer. The click fires a tracked URL that logs the
response and redirects to a web-hosted survey for optional free-text elaboration.

**beehiiv polls** record the subscriber's answer, redirect to a branded web page for
longer feedback, and expose responses as custom fields that can drive **segmentation** (e.g.,
send different content to readers who rate consistently low). The free-text reason lives on
the web page, not in the email click itself — because email clients cannot accept text input
inline. This is architecturally identical to the ntfy situation (see section E).
([beehiiv blog on feedback surveys](https://blog.beehiiv.com/p/use-feedback-surveys-in-email-newsletters))

**SparkLoop Reactions** is the same pattern: one-click in email → optional web survey for
elaboration. The responses appear in a dashboard but documented integration into active
personalization (e.g., auto-adjusting content for low-raters) is not published; it's primarily
an engagement/growth-metrics tool, not a content-steering loop
([SparkLoop Reactions](https://sparkloop.app/reactions)).

**The unresolved gap across both**: these tools capture the signal and show it in a dashboard,
but no documented automatic path from "reader rated this issue poorly" to "next brief is
different." That loop requires deliberate wiring by the publisher — it doesn't close itself.

### C6. Personalized LLM research — dynamic profile update from feedback (2024–2025)

Several 2024–2025 papers converge on a pattern distinct from RLHF: **no model fine-tuning**,
but instead iterative profile maintenance stored separately and injected at inference time.

- **GRAVITY** (arXiv 2510.11952): profile-grounded synthetic preferences — a natural-language
  profile summarizes user history and is used to steer generation without retraining.
- **Dynamic Profile Modeling / RLPA** (arXiv 2505.15456): LLM interacts with a simulated user
  model to iteratively infer and refine a profile; dual reward (profile accuracy + response
  alignment). Fine-tuning a small model (Qwen-2.5-3B) on the inferred profile.
- **Persistent Memory + User Profiles** (arXiv 2510.07925): persistent memory integrated
  with dynamic user profile, updated across sessions.
- **User Preference Modeling with Weak Rewards** (arXiv 2603.20939): learns a compact user
  representation online from interaction feedback, guides retrieval over structured preference
  memory, **without per-user fine-tuning**. Directly relevant: no training infrastructure
  required.

The convergence point in 2025 literature: **profile-as-text, updated-not-retrained** is the
viable n=1 pattern. A structured text file stores preferences; the writer reads it; feedback
updates it. No GPU required.

---

## D. The n=1 problem — what actually works for a solo reader

### Why RLHF/DPO is the wrong frame for n=1

RLHF and DPO require thousands of preference pairs across diverse prompts to train a reward
model. At n=1, a reader might give 3–5 feedback signals per day. Even at six months, that's
≤1,000 signals — insufficient for stable reward-model training, and the signals aren't
diverse enough (one person's taste, one domain). The AI newsletter personalization market
report projects "30% engagement uplift from AI personalization" but this is enterprise-scale
segmentation, not single-reader fine-tuning.

The RLHF connection in ChatGPT is also frequently misread: the thumbs aggregate across
hundreds of millions of users. One user's thumbs-up on one response is a vanishingly small
signal in the training corpus. At n=1, **thumbs → model update** is functionally zero signal.

### What works at n=1

The evidence from products and literature converges on three mechanisms, in increasing
complexity:

**1. Explicit preference list (the source/topic blocklist)**
The simplest and most durable mechanism. Maintain a text file with three sections:
- `always_surface`: sources or topics to prioritize
- `reduce`: sources or topics to show less of
- `never`: hard blocks

The writer reads this file at the start of every run. A thumbs-down with a "source" label
appends to `reduce`. A "never show X" command appends to `never`. No ML needed. This is
exactly what Feedly Leo does in product form; it's what Google Discover does with its
publisher-level block (fires before ranking, higher priority than any engagement signal).

**2. Natural-language preference profile (profile-in-prompt, from PRIOR-ART B4)**
A paragraph or structured doc describing what the reader values: preferred topics, desired
depth, framing preferences, explicit dislikes. Injected as the writer's system prompt.
Static initially; updatable by hand or via feedback. This is the pattern already identified in
`PRIOR-ART-2026-05-31-credibility-and-editor.md` section B4 — extended now with the feedback
update mechanism: thumbs-up with a free-text reason → the reason text becomes a candidate
addition to the profile, reviewed/committed by the owner. The ChatGPT memory system is the
product implementation of this.

**3. Per-story feedback log (the audit trail that closes the loop)**
A JSONL or append-only markdown file storing: `{date, brief_id, item_title, signal (+1/-1),
reason (optional), acted_on (bool)}`. The writer reads this at run time to:
(a) skip topics that have accumulated net-negative feedback,
(b) de-prioritize sources with multiple -1 signals,
(c) check before including a topic whether prior feedback flagged it.
This is the minimal persistence layer that converts episodic feedback into standing preferences.

**What does NOT work at n=1:**
- Dashboard analytics with no write path (covers C5 gap above)
- Feedback that writes to a file no routine reads (see section F)
- Model fine-tuning (scale doesn't work; cost doesn't justify it)
- Star ratings without semantic labels (aggregated stars don't tell the writer what to change)

---

## E. ntfy action buttons — capability verdict

**Primary source**: `https://docs.ntfy.sh/publish/` (fetched 2026-06-08). The documentation
describes **four action types**:

| Type | What it does | Free-text input? |
|---|---|---|
| `view` | Opens a URL in browser or app | No |
| `http` | Fires a fixed HTTP request (configurable method, headers, body) | No |
| `broadcast` | Sends Android intent (Tasker/MacroDroid) | No |
| `copy` | Copies a value to clipboard | No |

**Maximum 3 action buttons per notification.**

**No action type accepts user-typed text.** There is no direct-reply, no RemoteInput text
field, no inline text input of any kind. The `http` action sends a **pre-defined body** set
at notification-publish time — the payload is fixed when the notification is sent, not
composed by the reader at tap time. Confirmed by the phone/subscribe documentation which
explicitly notes that the publish bar in the app is a separate feature from notification
actions.

### What IS possible with ntfy

**Thumbs-up / thumbs-down via two `http` action buttons:**

The `http` action sends a pre-defined POST to any URL at button-tap time. The natural
transport for this pipeline is to **publish back to an ntfy feedback topic** — not to a
localhost port. The local bridge already subscribes to ntfy topics (it drains
`pending-notifications/` via ntfy); it can subscribe to a `feedback` topic in the same
connection. The originating server can listen on a designated topic for replies and take
action based on which button was pressed (ntfy GitHub issue #134 describes exactly this
pattern).

```
actions: [
  {"action": "http", "label": "👍",
   "url": "https://ntfy.sh/news-brief-feedback",
   "method": "POST",
   "headers": {"X-Brief-ID": "${BRIEF_ID}", "X-Signal": "1"}},
  {"action": "http", "label": "👎",
   "url": "https://ntfy.sh/news-brief-feedback",
   "method": "POST",
   "headers": {"X-Brief-ID": "${BRIEF_ID}", "X-Signal": "-1"}}
]
```
The bridge drains `news-brief-feedback` exactly as it drains the notification queue —
no new inbound listener or open port required. This is net-new bridge capability (today
the bridge is outbound-only: it drains `pending-notifications/` → ntfy), but it fits the
existing architecture without adding a public endpoint.

**A "view" button to open the web brief:**
```
{"action": "view", "label": "Read brief",
 "url": "https://khalic-lab.github.io/claude-routines/YYYY/MM/DD/slug.html"}
```
The web page can host a minimal HTML form for optional free-text reason. Because Jekyll is
static, the form must POST to the same ntfy feedback topic (the ntfy publish REST API
accepts POSTs from any client, including a browser form) or to the local bridge directly
(only works on the same LAN). The ntfy feedback-topic path is cleaner and works from
anywhere.

**Explicit verdict:**
> ntfy action buttons CAN capture a binary thumbs signal via two `http` actions with
> fixed payloads encoding ±1. ntfy action buttons CANNOT capture free-text. The optional
> "reason" field must live on a web page opened by a `view` action. The recommended
> transport for both channels is an ntfy feedback topic that the local bridge subscribes
> to — this requires no new public endpoint and extends the bridge's existing ntfy
> subscription pattern. Free-text via the static web page is an additional form POST to
> the same ntfy topic (or bridge, if on LAN).

---

## F. The write-only feedback anti-pattern

### The pattern and its cost

The "Feedback Flywheel" framework (Martin Fowler, 2025,
[martinfowler.com/articles/reduce-friction-ai/feedback-flywheel.html](https://martinfowler.com/articles/reduce-friction-ai/feedback-flywheel.html))
names the anti-pattern precisely: "Every AI interaction generates signal... but most teams
discard this signal. Without a learning system, AI effectiveness flatlines: the team uses the
tools, the tools are useful, but the **way the team uses them does not evolve**. The same gaps
in the priming document cause the same corrections."

Applied to a reader pipeline: if every brief run starts from the same static prompt and the
same source list, the reader's signal (what bored them, what they found genuinely useful)
never enters the system. The pipeline is "working" in a narrow sense but not improving. This
is identical to the beehiiv/SparkLoop gap identified in C5: the emoji rating reaches a
dashboard, nothing downstream reads the dashboard, next issue is identical.

The Fowler flywheel identifies four signal types that each map to an artifact:

| Signal | Source in our context | Destination artifact |
|---|---|---|
| Context signal | Feedback reason text | Reader profile / "what Rafael cares about" doc |
| Instruction signal | Thumbs-up on specific items | "keep more of X" note in writer prompt |
| Workflow signal | Persistent thumbs-down on a topic cluster | Source/topic blocklist |
| Failure signal | Repeated -1 on same source | Source blocklist or weight downgrade |

### Why the loop doesn't close by itself

The critical insight across all surveyed systems: **the feedback-to-improvement path requires
an explicit write step that the consuming agent actually reads**. Netflix closes it via model
retraining; ChatGPT closes it via memory-note injection; Google Discover closes it by
filtering before ranking. All three are automatic. For a git-based pipeline, there is no
automatic path — a human or a script must translate a raw feedback entry into a change to the
preference profile or blocklist that the next writer run actually reads.

The "write-only" failure mode is: thumbs-down lands in a JSONL log, the JSONL log is committed
to git, but the writer prompt does not reference the log → signal is captured but siloed →
next brief is unchanged → reader sees the same pattern → stops giving feedback. This is
feedback fatigue: the predictable consequence of showing a feedback affordance while
delivering no observable response to it. The beehiiv/SparkLoop survey pattern (C5) already
illustrates this risk — the emoji rating reaches a dashboard, nothing downstream reads the
dashboard, next issue is identical.

### Closing the loop — minimal viable path for this pipeline

The loop closes when: **captured signal → diff on a file the next writer run reads → committed
to git → writer picks up on next fire**.

Concretely, two diffs:

1. A thumbs-down on a source (or free-text "too much vendor PR from X") → the bridge appends
   to `reader-profile/source-weights.yml`:
   ```yaml
   - source: techcrunch.com
     weight: -0.5
     reason: "too much vendor PR"
     since: 2026-06-08
   ```
   The writer prompt reads this file and applies it as a selection penalty.

2. A free-text reason "I liked the arXiv paper depth" → the bridge or a lightweight agent
   appends a note to `reader-profile/profile.md` (the existing "what Rafael cares about" doc
   from PRIOR-ART B4). The next writer run picks this up as part of its standing brief.

Both are git-committed (with `-c commit.gpgsign=false` per CLAUDE.md bridge convention).
Neither requires ML infrastructure. The consuming agents are: the next routine run reading
`source-weights.yml` and `profile.md` from its sources list.

---

## Summary — what fits an n=1, solo-reader, static-site, git-repo pipeline

### Architecture in three layers

**Layer 1: Signal capture (ntfy + web page)**
- Two ntfy `http` action buttons per notification: 👍 and 👎, each POSTing a fixed
  payload (brief_id + signal ±1) to an ntfy feedback topic (e.g., `news-brief-feedback`).
- A `view` action button opening the brief's web page, which includes a minimal HTML form
  for optional free-text reason, POSTing to the same ntfy feedback topic.
- Maximum 3 actions per notification is satisfied by this exact trio.

**Layer 2: Bridge subscribes to feedback topic → git commit**
The local ntfy bridge (`/usr/local/src/news-brief-ntfy-bridge/`) adds a subscription to
`news-brief-feedback` (same pattern as its existing notification-drain subscription). On
receiving a message it:
- Appends to `reader-feedback/log.jsonl`: every raw signal, timestamped, with brief_id.
- On thumbs-down with a reason that names a source: appends a weight entry to
  `reader-profile/source-weights.yml`.
- On free-text without a source reference: appends a note to `reader-profile/profile.md`
  as a candidate update (marked `[candidate]`, human confirms before next run, or a
  lightweight agent processes it nightly).
- Commits with `-c commit.gpgsign=false`.

**Layer 3: Writer reads the profile on each run**
The routines' `session_context` (via `RemoteTrigger`) references `reader-profile/profile.md`
and `reader-profile/source-weights.yml` as sources. The writer applies:
- Hard blocks: `never:` list in source-weights blocks sources before selection.
- Soft weights: `reduce:` list deprioritizes topics/sources during curation.
- Profile text: injected into the writer system prompt as the reader's standing editorial brief.

### Explicit design decisions that come from the prior art

| Decision | Rationale |
|---|---|
| Binary signal (±1), not star rating | Stars aggregate ambiguously; ±1 has a clear consumption function (add to weight; block at threshold) |
| Three separate registers (item / topic / source) | Google Discover / Feedly pattern: source block fires before topic rank fires before item skip |
| Free-text reason on web page, not in ntfy | ntfy hard constraint: no inline text input in action buttons |
| ntfy feedback topic → bridge (not localhost endpoint) | Static Jekyll site cannot receive POSTs; bridge has no inbound port; ntfy topic is the pub-sub layer both sides already use |
| Profile-as-text, not fine-tuning | No training infrastructure; literature confirms this works at n=1 (ChatGPT memory, GRAVITY, User Preference with Weak Rewards) |
| Feedback → git commit → writer reads file | This is the loop. If the writer doesn't read the file, the loop is not closed (Fowler flywheel) |

### What this does NOT do (deliberate scope)

- No crowd signal (n=1 by design; collaborative filtering irrelevant)
- No model training or weight update (RLHF/DPO requires thousands of preference pairs;
  ChatGPT thumbs → training applies at population scale, not single user)
- No aggregated dashboard (audience-facing analytics tools like SparkLoop are for multi-reader
  newsletters; they don't map to a solo-reader git pipeline)
- No automatic profile rewrite (candidate updates in `profile.md` are human-confirmed;
  automatic updates risk instability from single-point feedback)

---

## Sources

- [ntfy publish docs — Action buttons](https://docs.ntfy.sh/publish/)
- [ntfy subscribe/phone docs — confirmed no direct-reply](https://docs.ntfy.sh/subscribe/phone/)
- [ntfy GitHub issue #134 — action buttons / feedback-topic reply pattern](https://github.com/binwiederhier/ntfy/issues/134)
- [OpenAI Memory announcement](https://openai.com/index/memory-and-new-controls-for-chatgpt/)
- [ChatGPT sycophancy regression July 2025](https://valentusproducts.com/gpt4o-sycophancy-july-2025-rollback/)
- [Netflix double thumbs up announcement](http://about.netflix.com/en/news/two-thumbs-up-even-better-recommendations)
- [Netflix TechBlog — long-term satisfaction recommender](https://netflixtechblog.com/recommending-for-long-term-member-satisfaction-at-netflix-ac15cada49ef)
- [Google Discover personalization — customize feed](https://support.google.com/websearch/answer/2819496)
- [Google Discover ranking and filtering research](https://searchengineland.com/google-discover-qualifies-ranks-filters-content-research-470190)
- [Artifact Wikipedia](https://en.wikipedia.org/wiki/Artifact_(app))
- [Artifact public launch — TechCrunch](https://techcrunch.com/2023/02/22/instagrams-co-founders-personalized-news-app-artifact-launches-to-the-public-with-new-features/)
- [Feedly Leo AI saving feeds](https://docs.feedly.com/article/769-saving-ai-feeds-feedly)
- [beehiiv feedback surveys](https://blog.beehiiv.com/p/use-feedback-surveys-in-email-newsletters)
- [SparkLoop Reactions](https://sparkloop.app/reactions)
- [Martin Fowler — Feedback Flywheel](https://martinfowler.com/articles/reduce-friction-ai/feedback-flywheel.html)
- [GRAVITY profile-grounded preferences arXiv 2510.11952](https://arxiv.org/pdf/2510.11952)
- [Dynamic Profile Modeling / RLPA arXiv 2505.15456](https://arxiv.org/pdf/2505.15456)
- [Persistent Memory + User Profiles arXiv 2510.07925](https://arxiv.org/abs/2510.07925)
- [User Preference with Weak Rewards arXiv 2603.20939](https://arxiv.org/pdf/2603.20939)
- [ACM RecSys Challenge 2024 — Ekstra Bladet news recommendation](https://dl.acm.org/doi/proceedings/10.1145/3687151)
- [PMC — complex systems and news recommender feedback models](https://pmc.ncbi.nlm.nih.gov/articles/PMC7790545/)
