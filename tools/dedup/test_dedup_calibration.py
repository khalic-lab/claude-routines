#!/usr/bin/env python3
"""Offline regression test guarding the dedup calibration (2026-05-31 gold set).

Stdlib only, NO network: it never calls the embed Worker. It pulls the STORED
bge-m3 vectors out of index/stories/*.jsonl via dedup.decode_vec and asserts that
classify()/autolink(), at the shipped T_HIGH_DEFAULT/T_LOW_DEFAULT, still:

  * tag the two clearly-identical near-verbatim reruns (Oxford "quadsqueezing",
    cosine 0.9494 / 0.9518) as REPEAT, and
  * tag a handful of clearly-distinct same-day stories as NEW (definitely NOT REPEAT).

Only UNAMBIGUOUS gold pairs are asserted — the inseparable middle band is policy,
not threshold (see DEDUP.md Step B), so we don't test it here.

Run:  python3 tools/dedup/test_dedup_calibration.py
Exits non-zero on failure; prints "calibration test OK" on success.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dedup  # noqa: E402

REPO = dedup.REPO
INDEX_DIR = dedup.INDEX_DIR

# Clear-cut gold fixtures, keyed by (index file, lowercased headline substring).
# Stored vectors only — immune to embedding-model drift, but regenerate if the
# index is pruned past these dates (the loader raises a clear message if so).
FIXTURES = {
    # TRUE-REPEAT: Oxford "quadsqueezing" re-run near-verbatim across overview days.
    "quad_02": ("2026-05-02-overview.jsonl", "quadsqueez"),
    "quad_05": ("2026-05-05-overview.jsonl", "quadsqueez"),
    "quad_14": ("2026-05-14-overview.jsonl", "quadsqueez"),
    # TRUE-DISTINCT: unrelated same-day ai-ml stories (cosine 0.40-0.52).
    "anthropic": ("2026-05-27-ai-ml.jsonl", "anthropic signs"),
    "meta":      ("2026-05-27-ai-ml.jsonl", "meta raises"),
    "llamacpp":  ("2026-05-27-ai-ml.jsonl", "llama.cpp"),
    "euaiact":   ("2026-05-27-ai-ml.jsonl", "eu ai act"),
    # DISTINCT PAPERS, mis-threaded by the WRITER (not cosine): SASA (arXiv 2606.06333)
    # was hand-threaded onto the May-14 SoftSAE SAE paper and tagged "[ongoing since
    # 2026-05-14]". The two embed at only 0.71, so autolink never linked them — the fix
    # is the writer-thread validation in cmd_record, gated by the arXiv distinct-paper
    # guard. SoftSAE's url is an arXiv LISTING page (no paper id), so only the
    # candidate-side arXiv id distinguishes them.
    "sasa":    ("2026-06-06-weekend.jsonl", "subspace-aware sparse autoencoders"),
    "softsae": ("2026-05-14-overview.jsonl", "softsae"),
}


def _load_fixture(fname, needle):
    """Return one index record (with decoded `embedding`) matching `needle`."""
    path = os.path.join(INDEX_DIR, fname)
    if not os.path.exists(path):
        raise SystemExit(
            f"FIXTURE MISSING: {path} not found (index pruned?). "
            "Regenerate the gold fixture from a current index file."
        )
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if needle in rec.get("headline", "").lower() and rec.get("emb"):
                rec["embedding"] = dedup.decode_vec(rec["emb"])
                return rec
    raise SystemExit(
        f"FIXTURE MISSING: no record matching '{needle}' with an embedding in {path}. "
        "Regenerate the gold fixture."
    )


def main():
    fx = {k: _load_fixture(*v) for k, v in FIXTURES.items()}
    th, tl = dedup.T_HIGH_DEFAULT, dedup.T_LOW_DEFAULT

    # Pin the calibrated values directly. The classify() fixtures below pass at
    # several thresholds (the unambiguous repeats sit at 0.949/0.952, above both
    # the old 0.92 and the new 0.945), so on their own they would NOT catch the
    # likeliest drift — a revert to the old default. This exact-match guard forces
    # a conscious update on any genuine recalibration (2026-05-31 gold set).
    assert th == 0.945, f"T_HIGH_DEFAULT drifted to {th} (expected 0.945)"
    assert tl == 0.72, f"T_LOW_DEFAULT drifted to {tl} (expected 0.72)"

    # --- TRUE-REPEAT: the two unambiguous near-verbatim reruns must be REPEAT. ---
    repeat_cases = [
        ("quadsqueezing 05-05 vs 05-02", fx["quad_05"], fx["quad_02"]),
        ("quadsqueezing 05-14 vs 05-05", fx["quad_14"], fx["quad_05"]),
    ]
    for name, later, match in repeat_cases:
        res = dedup.classify(later["embedding"], [match], th, tl)
        assert res["verdict"] == "REPEAT", (
            f"{name}: expected REPEAT, got {res['verdict']} (cosine {res['score']}, "
            f"t_high={th})"
        )

    # --- TRUE-DISTINCT: clearly unrelated stories must NOT be REPEAT (expect NEW). ---
    distinct_cases = [
        ("Anthropic-SpaceX vs Meta capex", fx["anthropic"], fx["meta"]),
        ("EU AI Act vs llama.cpp build",   fx["euaiact"],    fx["llamacpp"]),
        ("Anthropic-SpaceX vs llama.cpp",  fx["anthropic"],  fx["llamacpp"]),
        ("Meta capex vs EU AI Act",        fx["meta"],       fx["euaiact"]),
    ]
    for name, a, b in distinct_cases:
        res = dedup.classify(a["embedding"], [b], th, tl)
        assert res["verdict"] != "REPEAT", (
            f"{name}: expected NOT REPEAT, got REPEAT (cosine {res['score']}, t_high={th})"
        )
        assert res["verdict"] == "NEW", (
            f"{name}: expected NEW, got {res['verdict']} (cosine {res['score']}, t_low={tl})"
        )

    # --- autolink(): the record-time thread-inheritance path (covers cmd_record). ---
    # A clear repeat inherits the matched thread_id + first_seen_date...
    link = dedup.autolink(fx["quad_05"]["embedding"], [fx["quad_02"]])
    assert link is not None, "autolink: expected a thread link for the 05-05 vs 05-02 repeat"
    thread_id, first_seen = link
    assert thread_id == (fx["quad_02"].get("thread_id") or fx["quad_02"]["id"]), \
        f"autolink: inherited wrong thread_id {thread_id!r}"
    assert first_seen == (fx["quad_02"].get("first_seen_date") or fx["quad_02"]["date"]), \
        f"autolink: inherited wrong first_seen_date {first_seen!r}"
    # ...a clearly-distinct story does not link...
    assert dedup.autolink(fx["anthropic"]["embedding"], [fx["meta"]]) is None, \
        "autolink: distinct story should not inherit a thread"
    # NOTE: the worst-case high-cosine *distinct* autolink-gate fixture (two different US
    # trading sessions at cosine 0.914) was removed 2026-06-18 with the Markets stream.
    # The AUTOLINK_MIN gate (0.93) is still exercised by the synthetic arXiv-guard control
    # below; when the gold set is refixtured, re-key this gate regression to a non-market
    # high-cosine distinct pair drawn from the current index.
    # ...and an empty/missing index is harmless.
    assert dedup.autolink(fx["anthropic"]["embedding"], []) is None, \
        "autolink: empty index must return None (no crash)"

    # --- Deterministic exact-source match (zero-judgment REPEAT). ---
    assert dedup.arxiv_ids("DashAttention arXiv:2605.18753 · May 2026") == {"2605.18753"}, \
        "arxiv_ids: should extract 2605.18753"
    assert dedup.arxiv_ids("build bumped to 13.452 in the changelog") == set(), \
        "arxiv_ids: must NOT match version-like 13.452 (month 45 invalid)"
    assert dedup.canon_url("https://www.Arxiv.org/abs/2605.18753v2?x=1#sec") == "arxiv.org/abs/2605.18753v2", \
        f"canon_url normalization wrong: {dedup.canon_url('https://www.Arxiv.org/abs/2605.18753v2?x=1#sec')!r}"
    # A bare host is NOT a story identity key (living leaderboards / blog indexes).
    assert "url:swebench.com" not in dedup.exact_keys("SWE-bench standings", "", "http://swebench.com/"), \
        "exact_keys: bare host must not become a url identity key"
    assert "url:arxiv.org/abs/2605.18753" in dedup.exact_keys("x", "", "https://arxiv.org/abs/2605.18753"), \
        "exact_keys: permalink URL should key"
    # Same arXiv id across days -> REPEAT via decide_verdict, regardless of cosine.
    prior = {"id": "2026-05-20-ai-ml-dashattention", "date": "2026-05-20",
             "headline": "DashAttention speeds long-context inference (arXiv:2605.18753)",
             "summary": "New attention kernel.", "url": "https://arxiv.org/abs/2605.18753",
             "thread_id": "2026-05-20-ai-ml-dashattention", "first_seen_date": "2026-05-20",
             "embedding": fx["llamacpp"]["embedding"]}  # so the cosine fallthrough (cand2) works
    exact = dedup._build_exact_index([prior])
    cand = {"headline": "A faster long-context kernel lands",  # reworded headline, same paper
            "summary": "see paper", "url": "https://arxiv.org/abs/2605.18753"}
    res = dedup.decide_verdict(cand, fx["meta"]["embedding"], [prior], exact, th, tl)
    assert res["verdict"] == "REPEAT" and res["match_reason"] == "exact-arxiv", \
        f"exact-arxiv match should be REPEAT, got {res}"
    # A different paper id is NOT an exact match (falls through to cosine -> not REPEAT here).
    cand2 = {"headline": "Unrelated paper", "summary": "x", "url": "https://arxiv.org/abs/2605.99999"}
    res2 = dedup.decide_verdict(cand2, fx["meta"]["embedding"], [prior], exact, th, tl)
    assert res2["verdict"] != "REPEAT", f"different arXiv id must not exact-match: {res2}"

    # --- arXiv distinct-paper guard: the SASA/SoftSAE false-merge regression. ---
    sasa, softsae = fx["sasa"], fx["softsae"]
    cand = {"headline": sasa["headline"], "summary": sasa.get("summary", ""),
            "url": sasa.get("url"), "thread_id": softsae["id"],
            "first_seen_date": softsae.get("first_seen_date") or softsae["date"]}
    # The real records ARE recognized as distinct papers (candidate carries arXiv
    # 2606.06333; the SoftSAE genesis carries none).
    assert dedup._distinct_paper(cand, softsae) is True, \
        "SASA must be distinct from the id-less SoftSAE record"
    # This merge was WRITER-supplied, not cosine: confirm cosine is well below the gate
    # so the writer-thread validation (not autolink) is the load-bearing fix.
    assert dedup.cosine(sasa["embedding"], softsae["embedding"]) < dedup.AUTOLINK_MIN_DEFAULT, \
        "fixture drift: SASA/SoftSAE now embed above the autolink gate"
    # Simulate cmd_record's writer-thread validation: a supplied thread to a distinct
    # paper is rejected -> fresh thread.
    genesis = {softsae["id"]: softsae}.get(cand["thread_id"])
    assert genesis is not None and dedup._distinct_paper(cand, genesis), \
        "WRITER-THREAD VALIDATION REGRESSION: the SASA mis-thread would survive"
    # ...but a same-paper thread (shared arXiv id) is NOT stripped (no over-fire).
    same = dict(softsae, url="https://arxiv.org/abs/2606.06333")
    assert dedup._distinct_paper(cand, same) is False, \
        "guard over-fired: a shared arXiv id must remain threadable"
    # autolink arXiv guard (synthetic high-cosine distinct papers): identical vector, so
    # cosine 1.0 >= gate; without cand it links, with a different-id cand it suppresses.
    vec = fx["quad_02"]["embedding"]
    match_rec = dict(fx["quad_02"], headline="Paper A", url="https://arxiv.org/abs/2501.11111")
    cand_b = {"headline": "Paper B", "summary": "", "url": "https://arxiv.org/abs/2502.22222"}
    assert dedup.autolink(vec, [match_rec]) is not None, "no-guard control should link"
    assert dedup.autolink(vec, [match_rec], cand=cand_b) is None, \
        "AUTOLINK GUARD REGRESSION: distinct arXiv papers linked despite the guard"
    # check-side branch: force the ONGOING band with a test-local t_low (real cosine
    # 0.71) so the distinct-paper continuation-strip is exercised on real records.
    dv = dedup.decide_verdict(cand, sasa["embedding"], [softsae], {}, th, 0.70)
    assert dv["verdict"] == "ONGOING", f"expected ONGOING with t_low=0.70: {dv['verdict']}"
    assert (dv["matched"].get("continuation") is False
            and dv["matched"]["first_seen_date"] is None
            and dv.get("match_reason") == "distinct-paper"), \
        f"distinct-paper ONGOING must strip continuation + since-date: {dv}"

    # --- scheduling lint: the real 2026-06-06 vote misdating must flag. ---
    # Both June-6 briefs put the 14-June SVP vote on the wrong weekend; the lint refuses
    # the bare relative framing that caused it.
    for fname, phrase in [("2026-06-06-weekend.md", "this weekend"),
                          ("2026-06-06-cyber-papers.md", "tomorrow")]:
        ppath = os.path.join(REPO, "_posts", fname)
        if os.path.exists(ppath):
            with open(ppath) as f:
                got = dedup.scheduling_flags(f.read())
            assert any(phrase in fl["phrase"].lower() for fl in got), \
                f"SCHEDULING LINT REGRESSION: {fname} no longer flags '{phrase}' (the vote misdating)"
    # --- event_date forward-carry: a scheduled (future) thread date carries; evolving doesn't. ---
    assert dedup.scheduled_event_date({"event_date": "2026-06-14", "first_seen_date": "2026-05-23"}) == "2026-06-14"
    assert dedup.scheduled_event_date({"event_date": "2026-05-02", "first_seen_date": "2026-05-02"}) is None

    print("calibration test OK")


if __name__ == "__main__":
    main()
