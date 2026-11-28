"""Spec tests for tools/health/schedule.py + tools/health/freshness.py.

Contract: the schedule comes from routines/MANIFEST.md's table (Zurich wall-clock crons);
a writer fire at least `grace` old whose `_posts/{date}-{slug}.md` is missing is overdue,
classed lost / no-post / no-run from the usage ledger; each overdue edition is printed once
(state file), and the state forgets editions older than 14 days.
"""
import contextlib
import datetime as dt
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(TOOLS)
sys.path.insert(0, os.path.join(TOOLS, "health"))
import schedule  # noqa: E402
import freshness  # noqa: E402

Z = schedule.ZURICH


def zt(y, mo, d, h=0, mi=0):
    return dt.datetime(y, mo, d, h, mi, tzinfo=Z)


class CronTest(unittest.TestCase):
    def test_step_range_equals_list(self):
        # Watch's cron is written both ways in the docs; they must be the same schedule.
        self.assertTrue(schedule.same_schedule("27 2-22/4 * * *", "27 2,6,10,14,18,22 * * *"))
        self.assertFalse(schedule.same_schedule("27 2-22/4 * * *", "27 */4 * * *"))

    def test_cron_tz_prefix_and_sunday_seven(self):
        a = schedule.parse_cron("CRON_TZ=Europe/Zurich 30 11 * * 7")
        self.assertEqual(a["dow"], {0})
        self.assertEqual((a["minute"], a["hour"]), ({30}, {11}))

    def test_bad_cron_raises(self):
        for bad in ("0 25 * * *", "0 12 * *", "*/0 * * * *"):
            with self.assertRaises(ValueError):
                schedule.parse_cron(bad)

    def test_fires_between_is_zurich_wall_clock_across_dst(self):
        # 2026-03-29 is the spring-forward Sunday: 12:00 Zurich is 11:00 UTC the day
        # before and 10:00 UTC on it -- the slot stays at noon local.
        fires = schedule.fires_between("0 12 * * *", zt(2026, 3, 27, 13), zt(2026, 3, 29, 13))
        self.assertEqual([f.isoformat() for f in fires],
                         ["2026-03-28T12:00:00+01:00", "2026-03-29T12:00:00+02:00"])

    def test_fires_between_excludes_start_includes_end(self):
        fires = schedule.fires_between("0 12 * * 2,5", zt(2026, 11, 24, 12), zt(2026, 11, 27, 12))
        self.assertEqual([f.date().isoformat() for f in fires], ["2026-11-27"])


class ManifestTest(unittest.TestCase):
    def test_real_manifest_parses_every_routine(self):
        rows = schedule.load(REPO)
        slugs = [r["slug"] for r in rows]
        self.assertEqual(slugs, ["news", "ai-ml", "science", "weekend", "sports", "evaluator", None])
        self.assertTrue(all(r["trigger_id"].startswith("trig_") for r in rows))
        self.assertEqual([r["shim"] for r in rows][-1], "no")  # Watch is the inline one

    def test_empty_table_fails_loudly(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "routines"))
            with open(os.path.join(d, "routines", "MANIFEST.md"), "w") as fh:
                fh.write("# no table here\n")
            with self.assertRaises(ValueError):
                schedule.load(d)


class OverdueTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.root, "routines"))
        os.makedirs(os.path.join(self.root, "_posts"))
        os.makedirs(os.path.join(self.root, "index", "usage"))
        shutil.copy(os.path.join(REPO, "routines", "MANIFEST.md"),
                    os.path.join(self.root, "routines", "MANIFEST.md"))
        # Saturday 2026-11-28 15:00 Zurich: the 48h window holds News 11-27 and 11-28,
        # AI/ML Fri 11-27 and Weekend Sat 11-28 09:30. Watch never counts.
        self.now = zt(2026, 11, 28, 15)
        for name in ("2026-11-27-news.md", "2026-11-27-ai-ml.md", "2026-11-28-weekend.md"):
            open(os.path.join(self.root, "_posts", name), "w").close()

    def tearDown(self):
        shutil.rmtree(self.root)

    def _usage(self, routine, started, edition=None, stage="stop"):
        path = os.path.join(self.root, "index", "usage", "2026-11-%s.jsonl" % routine)
        with open(path, "a") as fh:
            fh.write(json.dumps({"routine": routine, "started": started, "edition": edition,
                                 "stage": stage, "session_id": "s-" + started}) + "\n")

    def test_missing_post_with_no_record_is_no_run(self):
        got = freshness.overdue(self.root, self.now)
        self.assertEqual([(g["key"], g["reason"]) for g in got], [("news|2026-11-28", "no-run")])

    def test_grace_hides_a_slot_that_is_too_recent(self):
        self.assertEqual(freshness.overdue(self.root, zt(2026, 11, 28, 13, 59)), [])
        self.assertEqual(len(freshness.overdue(self.root, zt(2026, 11, 28, 14, 0))), 1)

    def test_measured_edition_without_post_is_lost(self):
        self._usage("news", "2026-11-28T11:06:30Z", edition="2026-11-28-news", stage="publish")
        got = freshness.overdue(self.root, self.now)
        self.assertEqual(got[0]["reason"], "lost")

    def test_run_near_slot_without_edition_is_no_post(self):
        self._usage("news", "2026-11-28T11:07:00Z")
        self._usage("news", "2026-11-26T11:07:00Z")  # a different day's run does not count
        got = freshness.overdue(self.root, self.now)
        self.assertEqual(got[0]["reason"], "no-post")

    def test_main_prints_each_edition_once_and_prunes_state(self):
        state = os.path.join(self.root, "state.json")
        with open(state, "w") as fh:
            json.dump({"news|2026-10-01": "2026-10-01T14:00:00+02:00"}, fh)
        args = ["--root", self.root, "--state", state, "--now", self.now.isoformat()]
        out1, out2 = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out1):
            freshness.main(args)
        with contextlib.redirect_stdout(out2):
            freshness.main(args)
        lines = out1.getvalue().splitlines()
        self.assertEqual(len(lines), 1)
        title, body = lines[0].split("\t")
        self.assertEqual(title, "Missing edition: News 2026-11-28")
        self.assertIn("_posts/2026-11-28-news.md", body)
        self.assertEqual(out2.getvalue(), "")
        with open(state) as fh:
            kept = json.load(fh)
        self.assertEqual(sorted(kept), ["news|2026-11-28"])  # 10-01 is past 14 days

    def test_dry_run_writes_no_state(self):
        state = os.path.join(self.root, "state.json")
        with contextlib.redirect_stdout(io.StringIO()):
            freshness.main(["--root", self.root, "--state", state, "--dry-run",
                            "--now", self.now.isoformat()])
        self.assertFalse(os.path.exists(state))


if __name__ == "__main__":
    unittest.main()
