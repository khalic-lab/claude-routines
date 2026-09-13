#!/usr/bin/env python3
"""Parse a Claude Code run transcript into a measured token-usage summary.

The transcript (`<session>.jsonl`) is the only thing in the routine sandbox that MEASURES
spend: every assistant message carries `message.usage` with the exact input / cache /
output token counts the API billed. Summing those is a measurement, not the old estimate.

Two shapes of the file matter and are handled here:

  * One JSON object per LINE, and the SAME `message.id` repeats across several consecutive
    lines -- Claude Code writes one line per content block of a streamed message (measured
    locally: up to 15 lines for one id). The usage numbers are identical (or only grow)
    across those lines, so we dedupe by id and take the max per field, counting the id as
    ONE message. The tool_use content blocks, by contrast, are spread one-per-line, so tool
    calls are counted by summing the blocks across all of an id's lines.
  * A sibling `<stem>/subagents/agent-*.jsonl` directory (empty for today's routines, which
    have no Agent tool) holds sub-agent transcripts -- real spend, folded into the totals.

Only `type == "assistant"` lines whose `message.model` is a real string (not `"<synthetic>"`)
and not `isApiErrorMessage` are counted. Metadata (session id, routine, edition, timing)
comes from the main transcript only.
"""
import glob
import json
import os
import re


# Routine prompt paths (in the run's first user message) -> slug.
_ROUTINE_RE = re.compile(r"routines/(news|ai-ml|science|weekend|sports)\.md")
_EVALUATOR_RE = re.compile(r"routines/weekly-evaluator\.md")
# A publish call, used both to fall back to a slug and to name the edition.
_PUBLISH_RE = re.compile(r"tools/publish\.py\b[^\n]*?--slug\s+([a-z-]+)")
_PUBLISH_DATE_RE = re.compile(r"tools/publish\.py\b[^\n]*?--date\s+(\d{4}-\d{2}-\d{2})")


def _iter_lines(path):
    """Yield each parsed JSON object from a .jsonl file; skip blank / unparsable lines."""
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def _subagent_paths(path):
    """agent-*.jsonl under the transcript's sibling `<stem>/subagents/`, if present."""
    stem = os.path.splitext(os.path.basename(path))[0]
    subdir = os.path.join(os.path.dirname(path), stem, "subagents")
    if not os.path.isdir(subdir):
        return []
    return sorted(glob.glob(os.path.join(subdir, "agent-*.jsonl")))


def _text_of(content):
    """The text of a user message.content, whether it is a plain string or a block list."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(parts)
    return ""


def _is_counted_assistant(rec):
    if rec.get("type") != "assistant":
        return False
    if rec.get("isApiErrorMessage"):
        return False
    model = (rec.get("message") or {}).get("model")
    return isinstance(model, str) and model != "<synthetic>"


def _usage_fields(usage):
    """Pull the six token classes + two server-tool counters out of one usage object.

    `cache_creation` (the object) splits 5m / 1h; when it is absent the flat
    `cache_creation_input_tokens` is treated as 5m (the shape older lines use)."""
    cc = usage.get("cache_creation")
    if isinstance(cc, dict):
        cw5 = cc.get("ephemeral_5m_input_tokens", 0) or 0
        cw1 = cc.get("ephemeral_1h_input_tokens", 0) or 0
    else:
        cw5 = usage.get("cache_creation_input_tokens", 0) or 0
        cw1 = 0
    st = usage.get("server_tool_use") or {}
    return {
        "input": usage.get("input_tokens", 0) or 0,
        "cache_write_5m": cw5,
        "cache_write_1h": cw1,
        "cache_read": usage.get("cache_read_input_tokens", 0) or 0,
        "output": usage.get("output_tokens", 0) or 0,
        "web_search_requests": st.get("web_search_requests", 0) or 0,
        "web_fetch_requests": st.get("web_fetch_requests", 0) or 0,
    }


_TOKEN_KEYS = ("input", "cache_write_5m", "cache_write_1h", "cache_read", "output")
_SERVER_KEYS = ("web_search_requests", "web_fetch_requests")


def _aggregate(lines):
    """Fold counted assistant lines into per-message-id records (max per field), then into
    per-model totals, server-tool counts, and tool-call counts.

    Returns (by_id, tool_calls) where by_id maps id -> {model, <token/server fields>} and
    tool_calls maps tool name -> count. Tool blocks are summed across an id's lines, since
    each streamed content block lands on its own line."""
    by_id = {}
    id_tools = {}  # id -> Counter-like dict, so a message's tool blocks aren't double-added
    for rec in lines:
        if not _is_counted_assistant(rec):
            continue
        msg = rec["message"]
        mid = msg.get("id")
        if not mid:
            continue
        fields = _usage_fields(msg.get("usage") or {})
        cur = by_id.get(mid)
        if cur is None:
            cur = {"model": msg.get("model")}
            for k in _TOKEN_KEYS + _SERVER_KEYS:
                cur[k] = 0
            by_id[mid] = cur
            id_tools[mid] = {}
        # usage only grows while a message streams -> max is the settled value per field.
        for k in _TOKEN_KEYS + _SERVER_KEYS:
            if fields[k] > cur[k]:
                cur[k] = fields[k]
        for block in msg.get("content") or []:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                name = block.get("name") or "unknown"
                id_tools[mid][name] = id_tools[mid].get(name, 0) + 1
    tool_calls = {}
    for tools in id_tools.values():
        for name, n in tools.items():
            tool_calls[name] = tool_calls.get(name, 0) + n
    return by_id, tool_calls


def _bash_commands(lines):
    """Every Bash tool_use command string, in transcript order -- for routine/edition fallback."""
    cmds = []
    for rec in lines:
        if rec.get("type") != "assistant":
            continue
        for block in (rec.get("message") or {}).get("content") or []:
            if isinstance(block, dict) and block.get("type") == "tool_use" and block.get("name") == "Bash":
                cmd = (block.get("input") or {}).get("command")
                if isinstance(cmd, str):
                    cmds.append(cmd)
    return cmds


def _first_user_text(lines):
    for rec in lines:
        if rec.get("type") == "user":
            return _text_of((rec.get("message") or {}).get("content"))
    return ""


def detect_routine(first_user_text, bash_commands):
    """Which routine produced this run, by the contract's ordered rules."""
    m = _ROUTINE_RE.search(first_user_text or "")
    if m:
        return m.group(1)
    if _EVALUATOR_RE.search(first_user_text or ""):
        return "evaluator"
    if "tools/watch/due.py" in (first_user_text or "") or "Watch routine" in (first_user_text or ""):
        return "watch"
    for cmd in bash_commands:
        m = _PUBLISH_RE.search(cmd)
        if m:
            return m.group(1)
    return "unknown"


def detect_edition(bash_commands):
    """`<date>-<slug>` from the first publish call carrying both, else None."""
    for cmd in bash_commands:
        ms = _PUBLISH_RE.search(cmd)
        md = _PUBLISH_DATE_RE.search(cmd)
        if ms and md:
            return "%s-%s" % (md.group(1), ms.group(1))
    return None


def _timing(main_lines):
    """(started, ended): first user timestamp, last assistant timestamp -- or None."""
    started = None
    ended = None
    for rec in main_lines:
        ts = rec.get("timestamp")
        if not ts:
            continue
        if started is None and rec.get("type") == "user":
            started = ts
        if rec.get("type") == "assistant":
            ended = ts
    return started, ended


def _duration_s(started, ended):
    if not started or not ended:
        return None
    import datetime as dt
    try:
        a = dt.datetime.fromisoformat(started.replace("Z", "+00:00"))
        b = dt.datetime.fromisoformat(ended.replace("Z", "+00:00"))
    except ValueError:
        return None
    return int((b - a).total_seconds())


def parse(path, routine=None):
    """Parse the transcript at `path` (+ any sibling sub-agent files) into a summary dict.

    `routine`, when given, overrides detection (the publish-time `--find` path knows the slug
    already). The returned dict is the measured core of a usage record -- record.py wraps it
    with stage / cost / recorded_at to make the on-disk schema."""
    main_lines = list(_iter_lines(path))
    all_lines = list(main_lines)
    for sub in _subagent_paths(path):
        all_lines.extend(_iter_lines(sub))

    by_id, tool_calls = _aggregate(all_lines)

    models = {}
    totals = {k: 0 for k in _TOKEN_KEYS}
    server_tools = {k: 0 for k in _SERVER_KEYS}
    for rec in by_id.values():
        model = rec["model"]
        slot = models.get(model)
        if slot is None:
            slot = {k: 0 for k in _TOKEN_KEYS}
            slot["messages"] = 0
            models[model] = slot
        for k in _TOKEN_KEYS:
            slot[k] += rec[k]
            totals[k] += rec[k]
        slot["messages"] += 1
        for k in _SERVER_KEYS:
            server_tools[k] += rec[k]

    bash = _bash_commands(all_lines)
    first_user = _first_user_text(main_lines)
    started, ended = _timing(main_lines)

    # Session metadata: take the first line that carries each key.
    meta = {}
    for rec in main_lines:
        for k in ("sessionId", "cwd", "version", "gitBranch"):
            if k not in meta and rec.get(k):
                meta[k] = rec[k]

    return {
        "session_id": meta.get("sessionId"),
        "cwd": meta.get("cwd"),
        "claude_version": meta.get("version"),
        "git_branch": meta.get("gitBranch"),
        "started": started,
        "ended": ended,
        "duration_s": _duration_s(started, ended),
        "messages": len(by_id),
        "models": models,
        "totals": totals,
        "server_tools": server_tools,
        "tool_calls": tool_calls,
        "routine": routine or detect_routine(first_user, bash),
        "edition": detect_edition(bash),
        "transcript": os.path.abspath(path),
        "transcript_lines": len(main_lines),
    }
