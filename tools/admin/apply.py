#!/usr/bin/env python3
"""Apply queued admin actions to sources/registry.yml -- PLAN 2026-09-13 §2.3.

The admin page queues source retire/restore/add/set actions in the feedback-sink Worker; the Mac
bridge drains them (tools/admin/admin.py) and hands the batch to apply_actions() here. Each action's
§2.2 shape is re-validated (the Worker validated it once, but a queue is never trusted), then applied
to an in-memory copy of the registry through registry.py's own yaml_load/yaml_dump -- never PyYAML,
which the routine sandbox does not have. After the whole batch, registry.validate() runs over the
entire registry: on ANY schema violation the batch is discarded and every action marked rejected,
because sources/registry.yml is an append-only audit trail and the spec suite runs on main -- a
batch must never land a registry that suite would then fail. Applied or rejected, every action is
appended to index/admin/actions.jsonl and returned (with its KV key) so the bridge can ack it; a bad
action is acked too, so it can never loop.

Stdlib only. Pure and clock-free when `today` is passed (lifecycle dates come from it); `applied_at`
is a real wall-clock stamp, which tests assert only the shape of.
"""
import argparse
import datetime
import importlib.util
import json
import os
import re
import sys
import tempfile

# Load the sibling registry module by path: apply.py is not in tools/sources/, so the bare
# `import registry` convention the sources scripts use does not reach it. registry.py is stdlib-only
# and imports no siblings, so exec'ing it here is safe.
_HERE = os.path.dirname(os.path.abspath(__file__))
_REG_PATH = os.path.normpath(os.path.join(_HERE, "..", "sources", "registry.py"))
_spec = importlib.util.spec_from_file_location("_admin_registry", _REG_PATH)
registry = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(registry)

ACTION_TYPES = {"retire", "restore", "add", "set"}
SET_FIELDS = {"tier", "reach", "streams", "status", "class"}
# `set field=status` cannot reach `retired` -- retirement is its own action so it always records a
# retired lifecycle event (PLAN §2.2).
SET_STATUS_VALUES = {"candidate", "probation", "established", "demoted"}
ADD_STATUS_VALUES = {"candidate", "probation", "established"}
STREAMS = registry._VALID_STREAMS
CLASSES = registry._VALID_CLASSES
TIERS = registry._VALID_TIERS
REACH = registry._VALID_REACH
MAX_NOTE = 500

# §2.2 domain grammar: lowercase, 4-253 chars, LDH labels, at least two labels.
DOMAIN_RE = re.compile(
    r"^(?=.{4,253}$)[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
    r"(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$")


def _admin_note(note, always=False):
    """A lifecycle note carrying the admin's optional free-text reason. Returns None when there is
    no note (and `always` is False) so the lifecycle entry simply omits the key."""
    n = (note or "").strip()
    if n:
        return "admin: " + n
    return "admin" if always else None


def _fmt(value):
    return ",".join(value) if isinstance(value, list) else str(value)


def _validate_action(action):
    """Return an error string if `action` fails its §2.2 shape, else None. Unknown keys are
    ignored (the Worker already dropped them); this guards the fields apply() reads."""
    if not isinstance(action, dict):
        return "action is not an object"
    atype = action.get("type")
    if atype not in ACTION_TYPES:
        return "type %r not in %s" % (atype, sorted(ACTION_TYPES))
    domain = action.get("domain")
    if not isinstance(domain, str) or not DOMAIN_RE.match(domain):
        return "domain %r is not a valid host" % (domain,)
    note = action.get("note")
    if note is not None and (not isinstance(note, str) or len(note) > MAX_NOTE):
        return "note must be a string of at most %d chars" % MAX_NOTE

    if atype in ("retire", "restore"):
        return None

    if atype == "add":
        tier = action.get("tier", "T2")
        if tier not in TIERS:
            return "tier %r not in %s" % (tier, sorted(TIERS))
        status = action.get("status", "probation")
        if status not in ADD_STATUS_VALUES:
            return "add status %r not in %s" % (status, sorted(ADD_STATUS_VALUES))
        reach = action.get("reach", "direct")
        if reach not in REACH:
            return "reach %r not in %s" % (reach, sorted(REACH))
        cls = action.get("class")
        if cls is not None and cls not in CLASSES:
            return "class %r not in %s" % (cls, sorted(CLASSES))
        streams = action.get("streams")
        if not isinstance(streams, list) or not streams:
            return "streams must be a non-empty list"
        for s in streams:
            if s not in STREAMS:
                return "unknown stream %r" % (s,)
        probe = action.get("probe")
        if probe is not None:
            if not isinstance(probe, dict) or not probe.get("url"):
                return "probe must be an object with a url"
            if not re.match(r"^https?://", str(probe["url"])):
                return "probe url is not absolute http(s)"
            method = probe.get("method")
            if method is not None and method not in ("curl", "proxy"):
                return "probe method %r not curl/proxy" % (method,)
        return None

    if atype == "set":
        field = action.get("field")
        if field not in SET_FIELDS:
            return "set field %r not in %s" % (field, sorted(SET_FIELDS))
        if "value" not in action:
            return "set requires a value"
        value = action.get("value")
        if field == "tier" and value not in TIERS:
            return "value %r not in %s" % (value, sorted(TIERS))
        if field == "reach" and value not in REACH:
            return "value %r not in %s" % (value, sorted(REACH))
        if field == "class" and value not in CLASSES:
            return "value %r not in %s" % (value, sorted(CLASSES))
        if field == "status" and value not in SET_STATUS_VALUES:
            return "value %r not in %s (retire uses the retire action)" % (value, sorted(SET_STATUS_VALUES))
        if field == "streams":
            if not isinstance(value, list) or not value:
                return "streams value must be a non-empty list"
            for s in value:
                if s not in STREAMS:
                    return "unknown stream %r" % (s,)
        return None

    return "unhandled type %r" % (atype,)  # unreachable given the ACTION_TYPES gate above


def _apply_one(reg, action, today):
    """Mutate `reg` for one already-shape-valid action. Return (applied, error). Semantic
    preconditions (entry exists / does not / has the right status) are checked here."""
    atype = action["type"]
    domain = action["domain"]
    note = action.get("note")
    entry = reg.get(domain)

    if atype == "retire":
        if entry is None:
            return False, "unknown domain"
        if entry.get("status") == "retired":
            return False, "already retired"
        entry["status"] = "retired"
        registry.lifecycle_append(entry, today, "retired", status="retired",
                                  note=_admin_note(note, always=True))
        return True, None

    if atype == "restore":
        if entry is None:
            return False, "unknown domain"
        if entry.get("status") not in ("retired", "demoted"):
            return False, "not retired or demoted"
        entry["status"] = "probation"
        registry.lifecycle_append(entry, today, "restored", status="probation",
                                  note=_admin_note(note))
        return True, None

    if atype == "add":
        if entry is not None:
            return False, "exists; use restore or set"
        reach = action.get("reach", "direct")
        status = action.get("status", "probation")
        new = {
            "class": action.get("class") or registry.classify_domain(domain),
            "tier": action.get("tier", "T2"),
            "status": status,
            "reach": reach,
            "streams": list(action["streams"]),
        }
        probe = action.get("probe")
        if probe and probe.get("url"):
            # reach and the probe method must agree (registry.REACH_METHOD); derive the method from
            # reach when reach pins one, else keep a valid provided method, else default curl.
            method = registry.REACH_METHOD.get(reach)
            if method is None:
                method = probe.get("method") if probe.get("method") in ("curl", "proxy") else "curl"
            new["probe"] = {"url": probe["url"], "method": method}
        new["lifecycle"] = []
        registry.lifecycle_append(new, today, "added", status=status, note=_admin_note(note))
        reg[domain] = new
        return True, None

    if atype == "set":
        if entry is None:
            return False, "unknown domain"
        field, value = action["field"], action["value"]
        old = entry.get(field)
        entry[field] = list(value) if field == "streams" else value
        change = "%s -> %s" % (_fmt(old), _fmt(entry[field]))
        n = (note or "").strip()
        if n:
            change += " (admin: %s)" % n
        registry.lifecycle_append(entry, today, "set %s" % field, note=change)
        return True, None

    return False, "unhandled type"  # unreachable


def _result(action, result, error, applied_at):
    """Build the log/return record for one action: the action's own fields (minus the transient KV
    key) plus result/error/applied_at, and a separate `key` the bridge acks with."""
    rec = {k: v for k, v in action.items() if k != "key"}
    rec["result"] = result
    rec["error"] = error
    rec["applied_at"] = applied_at
    rec["key"] = action.get("key")
    return rec


def _load_registry(root):
    path = registry.registry_path(root)
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        text = f.read()
    if not text.strip():
        return {}
    reg = registry.yaml_load(text)
    return reg if isinstance(reg, dict) else {}


def _write_registry(root, reg):
    """Atomic replace so a crash mid-write never leaves a truncated registry. The temp file is
    written in `root`, NOT in sources/: a crash between mkstemp and os.replace would leave a stray
    .registry-*.tmp, and the bridge stages sources/ wholesale (`git add sources/`) -- root itself is
    never staged, so a stray temp there is never committed. root is the same filesystem as sources/,
    so os.replace stays atomic."""
    path = registry.registry_path(root)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=root, prefix=".registry-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(registry.yaml_dump(reg))
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def _append_actions_log(root, results):
    """Append each result to index/admin/actions.jsonl (the KV key is transient, so it is dropped
    from the on-disk record, exactly as feedback.py drops it). A no-op batch writes nothing -- it
    must not create an empty ledger file the bridge would then stage."""
    if not results:
        return
    path = os.path.join(root, "index", "admin", "actions.jsonl")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a") as f:
        for res in results:
            rec = {k: v for k, v in res.items() if k != "key"}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def apply_actions(root, actions, today=None):
    """Apply a batch of admin actions in list order and return a result per action.

    Each result mirrors the action plus `result` ("applied"|"rejected"), `error` (None or a
    message), `applied_at` (ISO), and `key` (the KV key to ack). Shape- or precondition-rejected
    actions do not mutate the registry. If the mutated registry fails registry.validate(), the whole
    batch is discarded (nothing written) and every action is marked rejected with the violation
    text. All results are appended to index/admin/actions.jsonl regardless."""
    if today is None:
        today = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    applied_at = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    reg = _load_registry(root)
    results = []
    changed = False
    for action in actions:
        err = _validate_action(action)
        if err is not None:
            results.append(_result(action, "rejected", err, applied_at))
            continue
        ok, serr = _apply_one(reg, action, today)
        if ok:
            changed = True
            results.append(_result(action, "applied", None, applied_at))
        else:
            results.append(_result(action, "rejected", serr, applied_at))

    if changed:
        violations = registry.validate(reg)
        if violations:
            vtext = "batch validation failed: " + "; ".join(violations)
            changed = False  # discard -- never write a registry the schema suite would fail
            for res in results:
                res["result"] = "rejected"
                res["error"] = vtext

    if changed:
        _write_registry(root, reg)

    _append_actions_log(root, results)
    return results


def main(argv=None):
    p = argparse.ArgumentParser(description="Apply queued admin actions to sources/registry.yml.")
    p.add_argument("--root", default=".")
    p.add_argument("--actions", required=True, help="path to a JSON file: a list of action objects")
    p.add_argument("--today", default=None, help="YYYY-MM-DD for lifecycle dates (default: UTC today)")
    args = p.parse_args(argv)
    with open(args.actions) as f:
        actions = json.load(f)
    results = apply_actions(args.root, actions, today=args.today)
    # Drop the transient key from stdout too.
    print(json.dumps([{k: v for k, v in r.items() if k != "key"} for r in results], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
