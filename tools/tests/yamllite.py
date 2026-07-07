"""Dependency-free YAML-subset loader for the sources test suite.

registry.py is expected to be stdlib-only (like every other tool in this repo — grep
`tools/*.py` for imports and you will not find a third-party one), so it will hand-write
plain block-style YAML rather than shell out to PyYAML. These tests must therefore be able
to read that file back without requiring PyYAML to be installed in the test environment.

`load(text)` uses the real `yaml.safe_load` when PyYAML happens to be importable (so a
richer implementation is still verified faithfully), and otherwise falls back to a small
hand-rolled parser covering the subset actually needed here: block mappings, block
sequences (`- item` and `- key: value` list-of-maps), nested maps/lists via 2-space (or
consistent) indentation, quoted/unquoted scalar strings, ints, floats, null/true/false, and
empty `[]`/`{}`. It is intentionally not a general YAML parser — flow-style non-empty
collections (`[a, b]`) and multiline block scalars are out of scope; every field in the
registry/sources contract can be expressed in the covered subset.
"""
import re


def _scalar(s):
    s = s.strip()
    if s == "" or s in ("~", "null", "Null", "NULL"):
        return None
    if s in ("true", "True", "TRUE"):
        return True
    if s in ("false", "False", "FALSE"):
        return False
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        return s[1:-1]
    if s == "[]":
        return []
    if s == "{}":
        return {}
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    return s


def _tokenize(text):
    out = []
    for raw in text.split("\n"):
        if not raw.strip():
            continue
        stripped = raw.strip()
        if stripped.startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        out.append((indent, stripped))
    return out


def _loads_fallback(text):
    lines = _tokenize(text)
    pos = [0]

    def peek():
        return lines[pos[0]] if pos[0] < len(lines) else None

    def parse_block(indent):
        node = peek()
        if node is None or node[0] < indent:
            return None
        return parse_list(indent) if node[1].startswith("- ") else parse_map(indent)

    def parse_list(indent):
        result = []
        while True:
            node = peek()
            if node is None or node[0] != indent or not node[1].startswith("- "):
                break
            pos[0] += 1
            body = node[1][2:]
            if ":" in body and not (body.strip().startswith(("'", '"'))):
                key, _, val = body.partition(":")
                key, val = key.strip(), val.strip()
                item = {}
                item[key] = parse_block(indent + 2) if val == "" else _scalar(val)
                while True:
                    nxt = peek()
                    if nxt is None or nxt[0] != indent + 2 or nxt[1].startswith("- "):
                        break
                    pos[0] += 1
                    k2, _, v2 = nxt[1].partition(":")
                    k2, v2 = k2.strip(), v2.strip()
                    item[k2] = parse_block(indent + 4) if v2 == "" else _scalar(v2)
                result.append(item)
            else:
                result.append(_scalar(body))
        return result

    def parse_map(indent):
        result = {}
        while True:
            node = peek()
            if node is None or node[0] != indent or node[1].startswith("- "):
                break
            pos[0] += 1
            key, _, val = node[1].partition(":")
            key, val = key.strip(), val.strip()
            if val == "":
                nxt = peek()
                result[key] = parse_block(nxt[0]) if nxt is not None and nxt[0] > indent else None
            else:
                result[key] = _scalar(val)
        return result

    return parse_map(0)


def load(text):
    try:
        import yaml  # type: ignore
    except ImportError:
        return _loads_fallback(text)
    return yaml.safe_load(text)


def _dump_scalar(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v)
    if s == "" or s in ("~", "null", "true", "false") or s != s.strip():
        return repr(s).replace("'", '"') if '"' not in s else "'%s'" % s
    return s


def dump(data, _indent=0):
    """Block-style YAML dumper for the fixed subset `load()`/`_loads_fallback` understand
    (mappings, sequences, scalars) -- used to build registry.yml fixtures for preflight.py /
    health.py tests without hand-typing indentation-sensitive text."""
    pad = "  " * _indent
    lines = []
    if isinstance(data, dict):
        if not data:
            return pad + "{}\n"
        for key in data:
            val = data[key]
            if isinstance(val, (dict, list)) and val:
                lines.append(f"{pad}{key}:")
                lines.append(dump(val, _indent + 1).rstrip("\n"))
            elif isinstance(val, dict):
                lines.append(f"{pad}{key}: {{}}")
            elif isinstance(val, list):
                lines.append(f"{pad}{key}: []")
            else:
                lines.append(f"{pad}{key}: {_dump_scalar(val)}")
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                sub_lines = dump(item, _indent + 1).split("\n")
                sub_lines = [l for l in sub_lines if l.strip()]
                if sub_lines:
                    first = sub_lines[0].strip()
                    lines.append(f"{pad}- {first}")
                    for l in sub_lines[1:]:
                        lines.append(l)
            else:
                lines.append(f"{pad}- {_dump_scalar(item)}")
    return "\n".join(lines) + "\n"
