#!/usr/bin/env python3
"""Preflight source plan -- SPIKE-2026-07-07-continuous-news.md §3.3/§3.4.

First research action for every writer fire (§3.3: "the plan -- not any prompt table -- is
the authority on what to fetch"): prints a markdown plan with three sections --

  ## Fetch list   registered domains affine to this stream, with probe info if any.
  ## Pressure     rolling-30d citation share per domain for this stream; >20% of an outlet's
                  (>30% of an institutional's; hubs exempt) share is flagged saturated.
  ## Discovery    today's discovery quota for this stream + registry candidate/dormant(>30d)
                  domains worth trying (candidates_to_try).

Report-only, always exits 0 -- a tool crash or a missing/empty registry degrades to a labeled
"source-plan unavailable" emergency-slate floor (§3.3 review C8 fix) rather than blocking the
writer. Stdlib only, no network.

Usage: preflight.py --slug {news|ai-ml|science|weekend} [--root PATH]
"""
import argparse
import os
import sys

import registry

QUOTA = {"news": 1, "ai-ml": 1, "science": 2, "weekend": 2}
SATURATION_BAR = {"outlet": 0.20, "institutional": 0.30}  # hub: exempt (SPIKE §2/§3.4)
DORMANT_DAYS = 30
WINDOW_DAYS = 30

EMERGENCY_FLOOR = """## Fetch list
source-plan unavailable -- degrading to the emergency slate (SRF, LeTemps, Al Jazeera, arXiv,
Nature feeds only; see routines/_shared/ for the degraded-mode floor). Note "source-plan
unavailable" in the brief's Gaps section.

## Pressure
source-plan unavailable -- no pressure computed this run.

## Discovery
source-plan unavailable -- no discovery quota computed this run."""


def load_registry(root):
    path = registry.registry_path(root)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        text = f.read()
    if not text.strip():
        return None
    data = registry.yaml_load(text)
    if not isinstance(data, dict) or not data:
        return None
    return data


def class_of(domain, reg):
    entry = reg.get(domain)
    if entry and entry.get("class"):
        return entry["class"]
    return registry.classify_domain(domain)


def build_fetch_section(slug, reg):
    lines = ["## Fetch list"]
    domains = sorted(d for d, rec in reg.items()
                      if slug in (rec.get("streams") or []) and rec.get("status") not in ("demoted", "retired"))
    if not domains:
        lines.append("(no registered domain is affine to %s yet)" % slug)
    for d in domains:
        rec = reg[d]
        probe = rec.get("probe") or {}
        probe_note = " -- probe: %s [%s]" % (probe["url"], probe.get("method")) if probe.get("url") else ""
        lines.append("- %s (%s, %s, reach=%s)%s" %
                     (d, rec.get("status"), rec.get("class"), rec.get("reach"), probe_note))
    return "\n".join(lines)


def build_pressure_section(slug, reg, root):
    lines = ["## Pressure"]
    counts = {}
    for rec in registry.load_story_records(root):
        if rec.get("stream") != slug:
            continue
        date = rec.get("date")
        domain = rec.get("source_domain")
        if not date or not domain:
            continue
        try:
            if registry.days_since(date) > WINDOW_DAYS:
                continue
        except ValueError:
            continue
        counts[domain] = counts.get(domain, 0) + 1
    total = sum(counts.values())
    if total == 0:
        lines.append("no citations in the rolling %dd window for %s." % (WINDOW_DAYS, slug))
        return "\n".join(lines)
    for domain in sorted(counts, key=lambda d: (-counts[d], d)):
        count = counts[domain]
        share = count / total
        cls = class_of(domain, reg)
        bar = SATURATION_BAR.get(cls)  # None for hub -- exempt
        flag = (" -- SATURATED (over the %d%% %s bar)" % (int(bar * 100), cls)
                if bar is not None and share > bar else "")
        lines.append("- %s: %d/%d citations (%.0f%%) in the rolling %dd window%s" %
                     (domain, count, total, share * 100, WINDOW_DAYS, flag))
    return "\n".join(lines)


def build_discovery_section(slug, reg):
    lines = ["## Discovery"]
    quota = QUOTA[slug]
    non_hub_note = " (non-hub)" if slug == "ai-ml" else ""
    lines.append("- Discovery quota for %s: >= %d novel-or-dormant anchor domain(s)%s "
                 "required this edition (waived-but-counted footer escape allowed)." %
                 (slug, quota, non_hub_note))
    candidates = []
    for domain, rec in reg.items():
        if slug not in (rec.get("streams") or []):
            continue
        status = rec.get("status")
        if status in ("demoted", "retired"):
            continue  # same exclusion as the fetch list: a dormant retired/deny-listed
                      # domain must not resurface as a discovery candidate
        last_cited = rec.get("last_cited")
        is_dormant = False
        if last_cited:
            try:
                is_dormant = registry.days_since(last_cited) > DORMANT_DAYS
            except ValueError:
                is_dormant = False
        if status == "candidate" or is_dormant:
            candidates.append((domain, status, last_cited))
    if not candidates:
        lines.append("- candidates_to_try: none on file for %s." % slug)
    else:
        for domain, status, last_cited in sorted(candidates):
            lines.append("- candidates_to_try: %s (%s, last_cited=%s)" % (domain, status, last_cited))
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--slug", required=True, choices=sorted(QUOTA))
    p.add_argument("--root", default=".")
    args = p.parse_args()

    try:
        reg = load_registry(args.root)
        if reg is None:
            print(EMERGENCY_FLOOR)
            return 0
        sections = [
            build_fetch_section(args.slug, reg),
            build_pressure_section(args.slug, reg, args.root),
            build_discovery_section(args.slug, reg),
        ]
        print("\n\n".join(sections))
    except Exception as exc:  # report-only: a crash degrades, never blocks the writer (§4)
        print(EMERGENCY_FLOOR)
        print("# preflight error (non-fatal): %s" % exc, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
