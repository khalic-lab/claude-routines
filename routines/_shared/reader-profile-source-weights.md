# Reader profile + source weights (read before selecting and ordering stories)

Before composing, read two human-gated files from the repo root and let them shape what you
SELECT and how you WEIGHT it — not just wording:
- `reader-profile.md` — a standing editorial brief for this specific reader (Rafael). Favor
  what it says to favor, demote/cut what it says to demote; it reflects the reader, not generic
  newsworthiness. A "Learned preferences" line that corrects an error the reader caught in a
  published brief (a wrong word, label, date, attribution or source) is binding, not guidance:
  check your draft against those lines, headlines and decks included, before publishing.
- `reader-profile/source-weights.yml` — two domain lists, matched on a story's primary source
  domain (lowercased host, leading "www." stripped):
  - `never:` — HARD filter: drop any story whose primary source is one of these domains.
  - `reduce:` — soft penalty: keep only if the story is clearly significant on its own; else
    demote or cut it.
These files are maintained via the Weekly Evaluator under a human gate — treat them as standing
editorial instruction. If a file is missing or empty, proceed normally.
