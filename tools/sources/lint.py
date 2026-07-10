#!/usr/bin/env python3
"""Discovery/credibility lint -- SPIKE-2026-07-07-continuous-news.md §4 ("Caps, discovery
quota, [new source] tag integrity ... deterministic, lint.py at Step C.25; hard-fail
(report-only until armed)").

Recomputes, against the registry, what a brief's own citations and Discovery footer claim --
never trusts the prose (mirrors §4's framing: "the model cannot self-certify a known domain as
new"). Checks:
  (1) [new source] tag integrity -- flagged if an unregistered domain is cited untagged, or a
      registered domain is tagged (a false novelty claim).
  (2) Discovery footer format -- exactly one `- Discovery: met (...)` / `waived -- <reason>`
      line. Format-only violations are reported but never gate --arm.
  (3) per-domain outlet cap (flat 2, hubs exempt) / institutional 30% share bar, and discovery-
      quota realization (recomputing what "met" actually requires -- for ai-ml, only non-hub
      novel domains count).

Domain attribution always uses the FIRST markdown link in a citation line (bullet or heading
register) -- a second corroborating link never counts, mirroring store/anchor.py's own rule.

Report-only by default: always exits 0. --arm exits 1 iff a cap/quota/tag violation exists
(footer-format violations never gate). Also appends newly tagged [new source] domains to
sources/candidates.jsonl (report-only mode included; --dry-run skips the write). Stdlib only.

Usage: lint.py <post.md> [--root PATH] [--arm] [--dry-run]
"""
import argparse
import datetime
import json
import os
import re
import sys
from urllib.parse import urlparse

import registry

QUOTA = {"news": 1, "ai-ml": 1, "science": 2, "weekend": 2}
OUTLET_CAP = 2
INSTITUTIONAL_BAR = 0.30
GATING_CATEGORIES = {"tag_missing", "tag_false", "outlet_cap", "institutional_bar", "discovery_quota"}

# Tolerates store/anchor.py's inline '<a id="st-..." class="st-a"></a>' (Step C.25 runs
# anchor.py BEFORE lint.py, so a brief's bullets are routinely already anchored) as well as
# the plain un-anchored form.
BULLET_RE = re.compile(r"^-\s+(?:<a\b[^>]*></a>\s*)?\*\*")
HEADING_CITE_RE = re.compile(r"^\*\*\[")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
NEW_SOURCE_TAG_RE = re.compile(r"\[new source\]")
DISCOVERY_LINE_RE = re.compile(r"^-\s*Discovery:\s*(.*)$")
DISCOVERY_CLAIM_RE = re.compile(r"^(met|waived)\b(.*)$")
SLUG_FROM_FILENAME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-([a-z0-9-]+)\.md$")
DATE_RE = re.compile(r"^date:\s*(\d{4}-\d{2}-\d{2})", re.M)


def domain_of(url):
    netloc = urlparse(url).netloc.lower()
    return netloc[4:] if netloc.startswith("www.") else netloc


def extract_citations(text):
    """One entry per bullet/heading citation line: {domain, tagged, url}. Domain attribution
    uses the FIRST markdown link only -- a second, corroborating link never counts."""
    out = []
    for line in text.split("\n"):
        if not (BULLET_RE.match(line) or HEADING_CITE_RE.match(line)):
            continue
        urls = LINK_RE.findall(line)
        if not urls:
            continue
        out.append({
            "domain": domain_of(urls[0]),
            "tagged": bool(NEW_SOURCE_TAG_RE.search(line)),
            "url": urls[0],
        })
    return out


def discovery_footer(text):
    """Returns (claim, violation_message): claim is 'met'/'waived' only when exactly one
    well-formed line is present -- anything else can't be graded, so callers should skip
    quota-realization checks rather than guess at a malformed/missing/duplicate footer."""
    lines = [DISCOVERY_LINE_RE.match(l).group(1).strip() for l in text.split("\n") if DISCOVERY_LINE_RE.match(l)]
    if len(lines) == 0:
        return None, "Discovery footer missing -- exactly one '- Discovery: met (...)' or 'waived -- <reason>' line is required."
    if len(lines) > 1:
        return None, "multiple Discovery footer lines found (%d) -- exactly one is required." % len(lines)
    m = DISCOVERY_CLAIM_RE.match(lines[0])
    if not m:
        return None, "Discovery footer line is malformed (%r) -- must read 'met (...)' or 'waived -- <reason>'." % lines[0]
    claim, rest = m.group(1), m.group(2).strip(" -—")
    if claim == "waived" and not rest:
        return None, "Discovery footer 'waived' has no reason given."
    return claim, None


def slug_of(post_path):
    m = SLUG_FROM_FILENAME_RE.match(os.path.basename(post_path))
    return m.group(1) if m else None


def load_registry(root):
    path = registry.registry_path(root)
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        text = f.read()
    if not text.strip():
        return {}
    data = registry.yaml_load(text)
    return data if isinstance(data, dict) else {}


def compute_violations(text, citations, reg, slug):
    violations = []  # list of (category, message)

    # (1) tag integrity, recomputed against the registry -- never trusted from the prose.
    for c in citations:
        domain, tagged = c["domain"], c["tagged"]
        registered = domain in reg
        if not registered and not tagged:
            violations.append(("tag_missing",
                "%s cited without a [new source] tag but is not in the registry." % domain))
        elif registered and tagged:
            violations.append(("tag_false",
                "%s tagged [new source] but is already registered (status=%s)." %
                (domain, reg[domain].get("status"))))

    # (3a) per-domain outlet cap (flat 2, hubs exempt) / institutional 30% share bar.
    total = len(citations)
    counts = {}
    for c in citations:
        counts[c["domain"]] = counts.get(c["domain"], 0) + 1
    for domain in sorted(counts):
        count = counts[domain]
        cls = reg.get(domain, {}).get("class") or registry.classify_domain(domain)
        if cls == "hub":
            continue
        if cls == "institutional":
            share = count / total if total else 0
            if share > INSTITUTIONAL_BAR:
                violations.append(("institutional_bar",
                    "%s cited %d/%d (%.0f%%) -- over the institutional %d%% saturation bar." %
                    (domain, count, total, share * 100, int(INSTITUTIONAL_BAR * 100))))
        elif count > OUTLET_CAP:
            violations.append(("outlet_cap",
                "%s cited %dx -- over the outlet cap of %d per edition." % (domain, count, OUTLET_CAP)))

    # (2) Discovery footer exactly-one-line contract (format only -- never gates --arm).
    claim, footer_violation = discovery_footer(text)
    if footer_violation:
        violations.append(("discovery_footer", "Discovery: %s" % footer_violation))

    # (3b) discovery-quota realization: recompute what "met" requires, never trust the claim.
    if claim == "met":
        quota = QUOTA.get(slug, 0)
        novel = set()
        for c in citations:
            if c["tagged"] and c["domain"] not in reg:
                cls = registry.classify_domain(c["domain"])
                if slug == "ai-ml" and cls == "hub":
                    continue  # ai-ml's quota is explicitly non-hub (SPIKE §3.4)
                novel.add(c["domain"])
        if len(novel) < quota:
            violations.append(("discovery_quota",
                "Discovery footer claims 'met' but only %d/%d genuinely novel domain(s) verify -- "
                "quota violation." % (len(novel), quota)))
    return violations


def append_candidates(root, post_path, text, citations, reg, dry_run):
    tagged_novel = [c for c in citations if c["tagged"] and c["domain"] not in reg]
    if not tagged_novel or dry_run:
        return
    sources_dir = os.path.join(root, "sources")
    os.makedirs(sources_dir, exist_ok=True)
    path = os.path.join(sources_dir, "candidates.jsonl")

    existing_domains = set()
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                if isinstance(rec, dict):
                    existing_domains.add(rec.get("domain"))

    m = DATE_RE.search(text)
    first_seen = m.group(1) if m else datetime.date.today().isoformat()
    slug = slug_of(post_path) or ""

    seen_this_call = set()
    to_append = []
    for c in tagged_novel:
        domain = c["domain"]
        if domain in existing_domains or domain in seen_this_call:
            continue
        seen_this_call.add(domain)
        to_append.append(c)

    if not to_append:
        return

    with open(path, "a") as f:
        for c in to_append:
            f.write(json.dumps({
                "domain": c["domain"], "first_seen": first_seen, "via": "writer",
                "stream": slug, "url": c["url"],
            }) + "\n")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("post")
    p.add_argument("--root", default=".")
    p.add_argument("--arm", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    violations = []
    try:
        with open(args.post) as f:
            text = f.read()
        reg = load_registry(args.root)
        citations = extract_citations(text)
        slug = slug_of(args.post)
        violations = compute_violations(text, citations, reg, slug)
        append_candidates(args.root, args.post, text, citations, reg, args.dry_run)
    except Exception as exc:  # report-only tool: a crash never blocks the brief (§4)
        print("LINT-REPORT: lint.py crashed (%s) -- treat as report-only, never block the brief." % exc,
              file=sys.stderr)
        return 0

    if violations:
        print("LINT-REPORT (%d violation(s)):" % len(violations))
        for category, message in violations:
            print("- [%s] %s" % (category, message))
    else:
        print("lint: clean -- 0 violations.")

    if args.arm and any(cat in GATING_CATEGORIES for cat, _ in violations):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
