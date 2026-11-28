"""Docs consistency: every routine's model and cron agree across the repo's copies.

routines/MANIFEST.md's table is the reference (tools/health/schedule.py parses it; the live
triggers are reachable only through RemoteTrigger). Held to it: MANIFEST's per-routine
session_context blocks, the ARCHITECTURE.md overview box, diagrams/01 and diagrams/02.
On 2026-11-27 the diagrams still showed Watch on Opus and UTC crons after both had changed;
this is the check that would have caught it. Changelog prose is not parsed -- history is
allowed to name old models.
"""
import json
import os
import re
import sys
import unittest

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(TOOLS)
sys.path.insert(0, os.path.join(TOOLS, "health"))
import schedule  # noqa: E402

MODEL_RE = r"(claude-[a-z]+-[0-9][a-z0-9-]*)"


def _read(rel):
    with open(os.path.join(REPO, rel), encoding="utf-8") as fh:
        return fh.read()


class DocsConsistencyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = schedule.load(REPO)
        cls.by_slug = {r["slug"] or "watch": r for r in cls.rows}
        cls.by_trigger = {r["trigger_id"]: r for r in cls.rows}

    def test_manifest_session_context_blocks_match_the_table(self):
        text = _read("routines/MANIFEST.md")
        blocks = re.findall(r"^### ([a-z-]+) \(trigger `(trig_\w+)`[^\n]*\n```json\n(.*?)\n```",
                            text, re.S | re.M)
        self.assertEqual(len(blocks), len(self.rows), "one session_context block per routine")
        for name, trig, body in blocks:
            row = self.by_trigger[trig]
            self.assertEqual(row["file"], name + ".md", "block %s names trigger %s" % (name, trig))
            self.assertEqual(json.loads(body)["model"], row["model"], "MANIFEST block " + name)

    def test_architecture_box_matches_the_table(self):
        # The routines box: from the ANTHROPIC CLOUD banner to its closing border.
        text = _read("ARCHITECTURE.md")
        start = text.index("ANTHROPIC CLOUD (routines)")
        box = text[start:text.index("╚", start)]
        writers = re.search(r"WRITERS \(" + MODEL_RE + r"\)", box).group(1)
        seen = set()
        for line in box.splitlines():
            m = re.search(r"((?:\S+\s+){5})(_posts/\{d\}-([a-z-]+)\.md|pending-notifications/)", line)
            if not m:
                continue
            slug = m.group(3) or "watch"
            row = self.by_slug[slug]
            cron = " ".join(m.group(1).split())
            self.assertTrue(schedule.same_schedule(cron, row["cron"]),
                            "ARCHITECTURE box %s cron %r vs MANIFEST %r" % (slug, cron, row["cron"]))
            own = re.search(r"\(" + MODEL_RE + r"\)", line)
            model = own.group(1) if own else writers
            self.assertEqual(model, row["model"], "ARCHITECTURE box %s model" % slug)
            seen.add(slug)
        self.assertEqual(seen, set(self.by_slug), "every routine appears in the box")

    def test_system_overview_diagram_matches_the_table(self):
        text = _read("diagrams/01-system-overview.md")
        w = re.search(r'W\["Writers — ' + MODEL_RE + r" \(Sports: " + MODEL_RE + r"\)", text)
        for slug in ("news", "ai-ml", "science", "weekend"):
            self.assertEqual(w.group(1), self.by_slug[slug]["model"], "diagram 01 writers: " + slug)
        self.assertEqual(w.group(2), self.by_slug["sports"]["model"], "diagram 01 sports")
        self.assertEqual(re.search(r'WA\["Watch — ' + MODEL_RE, text).group(1),
                         self.by_slug["watch"]["model"], "diagram 01 watch")
        self.assertEqual(re.search(r'EV\["Weekly Evaluator — ' + MODEL_RE, text).group(1),
                         self.by_slug["evaluator"]["model"], "diagram 01 evaluator")

    def test_routines_diagram_matches_the_table(self):
        model, seen = None, set()
        for line in _read("diagrams/02-routines-and-schedules.md").splitlines():
            sg = re.search(r'subgraph \w+\["[^"]*· ' + MODEL_RE + r'"\]', line)
            if sg:
                model = sg.group(1)
                continue
            node = re.search(r"(trig_\w+)<br/>cron ((?:\S+ ){4}\S+) \(", line)
            if not node or "REMOVED" in line:
                continue
            row = self.by_trigger[node.group(1)]
            self.assertTrue(schedule.same_schedule(node.group(2), row["cron"]),
                            "diagram 02 %s cron %r vs %r" % (row["name"], node.group(2), row["cron"]))
            self.assertEqual(model, row["model"], "diagram 02 %s model" % row["name"])
            seen.add(node.group(1))
        self.assertEqual(seen, set(self.by_trigger), "every routine appears in diagram 02")


if __name__ == "__main__":
    unittest.main()
