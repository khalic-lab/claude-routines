Poll the topic-watch registry and queue an ntfy notification on any match.

# Inputs

- Repo: `https://github.com/khalic-lab/claude-routines` (cloned into the sandbox via Source).
- Registry: `watches.yml` at the repo root. You never parse or edit it by hand -- the two tools below do all bookkeeping.
- Notification queue: `pending-notifications/` directory at the repo root. A local bridge drains this directory and POSTs each stub to ntfy.sh, then commits the deletion. The cloud sandbox cannot reach ntfy.sh directly (egress allowlist).

# Steps

1. **Pull latest.** `cd` into the cloned repo and run:
   ```bash
   git pull --ff-only origin main && python3 tools/watch/due.py
   ```
   `due.py` does the cooldown arithmetic (last_fired null, or today - last_fired >= cooldown_days, Europe/Zurich) and prints either `NONE DUE` or a JSON list of due watches (id, query, match_when).

2. **If it printed `NONE DUE`, STOP immediately.** No further reads, no commits, no output. This is the common case.

3. **For each due watch, probe: `WebSearch(query)`.** Read the top result snippets (titles + descriptions). Apply judgment -- this is your ONLY judgment call in this routine:
   - Does the evidence in the snippets clearly support `match_when` as true *today*? Concrete, dated evidence -- not 'will eventually', not 'rumored', not 'plans to'.
   - If yes -> **match**. Pick the most authoritative result URL as the click target (prefer official sources over aggregators).
   - If unsure or no clear evidence -> **no match**. Be conservative; a false positive burns `cooldown_days` of signal.

4. **On each match, run the bookkeeping tool** (writes the stub with proper JSON encoding and updates that watch's `last_fired` in place, preserving comments and formatting):
   ```bash
   python3 tools/watch/fire.py match --id <watch-id> --url "<click-url>" --body "<one-liner>"
   ```
   `--body`: a one-line summary of what matched, <=200 chars, ending with the source publication name in parens. Pass it as a normal shell argument -- no manual quote-escaping.

5. **After all probes, push** (a silent no-op when nothing matched; derives the commit message from the stubs, retries the push exactly once):
   ```bash
   python3 tools/watch/fire.py push
   ```

# Constraints

- `WebFetch` and `Bash{curl}` are 403'd by the sandbox proxy for most public sites including ntfy.sh. **Use `WebSearch` for probes.** Do NOT attempt curl to ntfy.sh -- the stub + bridge is the only delivery mechanism.
- Never edit `watches.yml` yourself -- `fire.py` owns the `last_fired` writes; the user owns `query`, `match_when`, `cooldown_days`, `id`. Do not add or remove watches.
- Do not delete files in `pending-notifications/` -- only the local bridge does that.
- If `due.py` errors or `watches.yml` is malformed, exit silently. Do not commit.
- No Drive write, no markdown brief output. The stub + bridge is the only user-visible signal.
