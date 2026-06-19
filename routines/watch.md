Poll the topic-watch registry and queue an ntfy notification on any match.

# Inputs

- Repo: `https://github.com/khalic-lab/claude-routines` (cloned into the sandbox via Source).
- Registry: `watches.yml` at the repo root.
- Notification queue: `pending-notifications/` directory at the repo root. A local bridge skill drains this directory and POSTs each stub to ntfy.sh, then commits the deletion. The cloud sandbox cannot reach ntfy.sh directly (egress allowlist).
- Today's date in Europe/Zurich.

# Steps

1. **Pull latest.** `cd` into the cloned repo and `git pull --ff-only origin main` so you're working against the current `watches.yml`.

2. **Read `watches.yml`.** Parse as YAML. Schema per entry:
   ```yaml
   - id: <slug>
     query: <WebSearch query string>
     match_when: <natural-language predicate the model judges against snippets>
     cooldown_days: <int, default 14>
     last_fired: <ISO date or null>
   ```
   If the file is malformed, exit silently. Do not commit.

3. **For each watch, decide whether to probe:**
   - `last_fired` is `null` -> probe.
   - `(today - last_fired) >= cooldown_days` -> probe.
   - Otherwise skip (still in cooldown).

4. **Probe = `WebSearch(query)`.** Read the top result snippets (titles + descriptions). Apply judgment:
   - Does the evidence in the snippets clearly support `match_when` as true *today*? Concrete, dated evidence -- not 'will eventually', not 'rumored', not 'plans to'.
   - If yes -> **match**. Pick the most authoritative result URL as the click target (prefer official sources over aggregators).
   - If unsure or no clear evidence -> **no match**. Be conservative; a false positive burns `cooldown_days` of signal.

5. **On match -- write a notification stub to `pending-notifications/`.**

   Filename: `pending-notifications/{YYYYMMDDTHHMMSS}-watch-{id}.json` using current UTC time in compact ISO form (e.g. `20260518T143015-watch-meteoswiss-inca.json`).

   Content: a single JSON object with fields:
   - `title`: `"Watch fired -- {id}"`
   - `click`: the top result URL chosen above
   - `body`: a one-line summary of what matched, <=200 chars, ending with the source publication name in parens
   - `tags`: `"eyes"`

   Use the Write tool to create the file.

   Set that watch's `last_fired` to today's ISO date (`YYYY-MM-DD`, Europe/Zurich). Leave all other fields untouched.

6. **Persist state and push.** If any `last_fired` changed:
   - Edit `watches.yml` in place (preserve comments, formatting, ordering).
   - Stage both files:
     ```bash
     git add watches.yml pending-notifications/
     git commit -m "Watch fired: <comma-separated ids>"
     git push origin main
     ```
   - If `git push` fails after `git pull --ff-only` returned cleanly, retry the push exactly once. If it still fails, do NOT retry further. Next cron run will pick up the unpushed stub.

7. **No matches?** Exit silently. No commit, no log noise.

# Constraints

- `WebFetch` and `Bash{curl}` are 403'd by the sandbox proxy for most public sites including ntfy.sh. **Use `WebSearch` for probes.** Do NOT attempt curl to ntfy.sh -- it will fail. Stub-write is the only delivery mechanism.
- Do not modify any field other than `last_fired`. The user owns `query`, `match_when`, `cooldown_days`, `id`.
- Do not add or remove watches.
- Do not delete files in `pending-notifications/` -- only the local bridge does that.
- No Drive write, no markdown brief output. The stub + bridge is the only user-visible signal.