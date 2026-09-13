"""Spec tests for tools/admin/apply.py -- the admin apply path (PLAN 2026-09-13 §2.3).

Every §2.3 branch is exercised, including the whole-batch schema-rejection path (a batch that would
drop a stream below its usable floor is discarded and every action rejected). Two tests use the
REAL sources/registry.yml: a no-op batch must leave it byte-identical, and a single mutating action
must change only the target domain's text block -- the guard against a dumper that silently reformats
the file (which would merge-conflict every edition that fires the same minute).
"""
import importlib.util
import json
import os
import shutil
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FIXTURE_REGISTRY = os.path.join(os.path.dirname(__file__), "fixtures", "admin", "registry.yml")


def _load(name, relpath):
    spec = importlib.util.spec_from_file_location(name, os.path.join(REPO, relpath))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


apply_mod = _load("_admin_apply", "tools/admin/apply.py")
registry = apply_mod.registry
TODAY = "2026-09-13"


def _read(path):
    with open(path) as f:
        return f.read()


def _blocks(text):
    """Split a registry.yml into {domain-header-line: block-text}. Top-level domain keys are the
    only unindented lines, so a block runs from one to the next. Used to prove a mutating apply
    touched only the target domain's block."""
    blocks, key, cur = {}, None, []
    for line in text.splitlines(keepends=True):
        if line.strip() and not line.startswith((" ", "\t")):
            if key is not None:
                blocks[key] = "".join(cur)
            key, cur = line, [line]
        else:
            cur.append(line)
    if key is not None:
        blocks[key] = "".join(cur)
    return blocks


class ApplyBase(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="admin-apply-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        os.makedirs(os.path.join(self.root, "sources"))
        self.reg_path = os.path.join(self.root, "sources", "registry.yml")
        shutil.copy(FIXTURE_REGISTRY, self.reg_path)
        self.original = _read(self.reg_path)

    def apply(self, actions):
        return apply_mod.apply_actions(self.root, actions, today=TODAY)

    def reg(self):
        return registry.yaml_load(_read(self.reg_path))

    def log(self):
        path = os.path.join(self.root, "index", "admin", "actions.jsonl")
        if not os.path.exists(path):
            return []
        with open(path) as f:
            return [json.loads(l) for l in f if l.strip()]


class RetireTest(ApplyBase):
    def test_retire_existing_probation(self):
        res = self.apply([{"type": "retire", "domain": "src01.example", "note": "low signal"}])
        self.assertEqual(res[0]["result"], "applied")
        entry = self.reg()["src01.example"]
        self.assertEqual(entry["status"], "retired")
        last = entry["lifecycle"][-1]
        self.assertEqual(last["event"], "retired")
        self.assertEqual(last["status"], "retired")
        self.assertEqual(last["note"], "admin: low signal")
        self.assertEqual(last["date"], TODAY)

    def test_retire_with_no_note_records_admin(self):
        res = self.apply([{"type": "retire", "domain": "src01.example"}])
        self.assertEqual(res[0]["result"], "applied")
        self.assertEqual(self.reg()["src01.example"]["lifecycle"][-1]["note"], "admin")

    def test_retire_unknown_domain_rejected(self):
        res = self.apply([{"type": "retire", "domain": "nope.example"}])
        self.assertEqual(res[0]["result"], "rejected")
        self.assertEqual(res[0]["error"], "unknown domain")
        self.assertEqual(_read(self.reg_path), self.original)

    def test_retire_already_retired_rejected(self):
        res = self.apply([{"type": "retire", "domain": "retired.example"}])
        self.assertEqual(res[0]["result"], "rejected")
        self.assertEqual(res[0]["error"], "already retired")
        self.assertEqual(_read(self.reg_path), self.original)


class RestoreTest(ApplyBase):
    def test_restore_from_retired(self):
        res = self.apply([{"type": "restore", "domain": "retired.example"}])
        self.assertEqual(res[0]["result"], "applied")
        entry = self.reg()["retired.example"]
        self.assertEqual(entry["status"], "probation")
        self.assertEqual(entry["lifecycle"][-1]["event"], "restored")
        self.assertEqual(entry["lifecycle"][-1]["status"], "probation")

    def test_restore_from_demoted(self):
        res = self.apply([{"type": "restore", "domain": "demoted.example"}])
        self.assertEqual(res[0]["result"], "applied")
        self.assertEqual(self.reg()["demoted.example"]["status"], "probation")

    def test_restore_non_retired_rejected(self):
        res = self.apply([{"type": "restore", "domain": "src01.example"}])
        self.assertEqual(res[0]["result"], "rejected")
        self.assertEqual(res[0]["error"], "not retired or demoted")


class AddTest(ApplyBase):
    def test_add_new_defaults(self):
        res = self.apply([{"type": "add", "domain": "new-outlet.example", "streams": ["news"]}])
        self.assertEqual(res[0]["result"], "applied")
        entry = self.reg()["new-outlet.example"]
        self.assertEqual(entry["status"], "probation")   # default
        self.assertEqual(entry["reach"], "direct")       # default
        self.assertEqual(entry["tier"], "T2")            # default
        self.assertEqual(entry["class"], "outlet")       # classify_domain
        self.assertEqual(entry["streams"], ["news"])
        self.assertEqual(entry["lifecycle"][-1]["event"], "added")

    def test_add_infers_class_from_domain(self):
        res = self.apply([{"type": "add", "domain": "some.gov", "streams": ["news"]}])
        self.assertEqual(res[0]["result"], "applied")
        self.assertEqual(self.reg()["some.gov"]["class"], "institutional")

    def test_add_reach_proxy_forces_probe_method(self):
        # reach and probe method must agree; a curl method on a proxy reach is rewritten to proxy.
        res = self.apply([{"type": "add", "domain": "proxied.example", "streams": ["ai-ml"],
                           "reach": "proxy",
                           "probe": {"url": "https://proxied.example/feed", "method": "curl"}}])
        self.assertEqual(res[0]["result"], "applied")
        self.assertEqual(self.reg()["proxied.example"]["probe"]["method"], "proxy")

    def test_add_existing_rejected(self):
        res = self.apply([{"type": "add", "domain": "src01.example", "streams": ["news"]}])
        self.assertEqual(res[0]["result"], "rejected")
        self.assertEqual(res[0]["error"], "exists; use restore or set")

    def test_add_empty_streams_rejected(self):
        res = self.apply([{"type": "add", "domain": "x.example", "streams": []}])
        self.assertEqual(res[0]["result"], "rejected")
        self.assertIn("streams", res[0]["error"])


class SetTest(ApplyBase):
    def test_set_scalar_field(self):
        res = self.apply([{"type": "set", "domain": "src01.example", "field": "tier",
                           "value": "T1", "note": "promote"}])
        self.assertEqual(res[0]["result"], "applied")
        entry = self.reg()["src01.example"]
        self.assertEqual(entry["tier"], "T1")
        self.assertEqual(entry["lifecycle"][-1]["event"], "set tier")
        self.assertEqual(entry["lifecycle"][-1]["note"], "T2 -> T1 (admin: promote)")

    def test_set_streams_list(self):
        res = self.apply([{"type": "set", "domain": "hub.example", "field": "streams",
                           "value": ["science", "weekend"]}])
        self.assertEqual(res[0]["result"], "applied")
        entry = self.reg()["hub.example"]
        self.assertEqual(entry["streams"], ["science", "weekend"])
        self.assertEqual(entry["lifecycle"][-1]["note"], "science -> science,weekend")

    def test_set_status_cannot_retire(self):
        res = self.apply([{"type": "set", "domain": "src01.example", "field": "status",
                           "value": "retired"}])
        self.assertEqual(res[0]["result"], "rejected")
        self.assertIn("retire", res[0]["error"])

    def test_set_unknown_field_rejected(self):
        res = self.apply([{"type": "set", "domain": "src01.example", "field": "probe",
                           "value": "x"}])
        self.assertEqual(res[0]["result"], "rejected")

    def test_set_unknown_domain_rejected(self):
        res = self.apply([{"type": "set", "domain": "nope.example", "field": "tier",
                           "value": "T1"}])
        self.assertEqual(res[0]["result"], "rejected")
        self.assertEqual(res[0]["error"], "unknown domain")


class ShapeAndBatchTest(ApplyBase):
    def test_bad_domain_rejected(self):
        res = self.apply([{"type": "retire", "domain": "NOT A DOMAIN"}])
        self.assertEqual(res[0]["result"], "rejected")
        self.assertIn("domain", res[0]["error"])

    def test_unknown_type_rejected(self):
        res = self.apply([{"type": "frobnicate", "domain": "src01.example"}])
        self.assertEqual(res[0]["result"], "rejected")

    def test_shape_reject_does_not_block_good_actions(self):
        # A malformed action must not sink the good actions beside it in the same batch.
        res = self.apply([
            {"type": "retire", "domain": "nope.example"},          # rejected (unknown)
            {"type": "retire", "domain": "src01.example"},         # applied
        ])
        self.assertEqual([r["result"] for r in res], ["rejected", "applied"])
        self.assertEqual(self.reg()["src01.example"]["status"], "retired")

    def test_batch_discarded_when_floor_breaks(self):
        # Retiring two of the six all-stream sources drops every stream to 4 usable (< 5 floor):
        # registry.validate() flags it, the batch is discarded, both actions rejected, file intact.
        res = self.apply([
            {"type": "retire", "domain": "src01.example"},
            {"type": "retire", "domain": "src02.example"},
        ])
        self.assertTrue(all(r["result"] == "rejected" for r in res))
        self.assertTrue(all(r["error"].startswith("batch validation failed") for r in res))
        self.assertEqual(_read(self.reg_path), self.original)

    def test_every_action_is_logged_with_key(self):
        res = self.apply([{"type": "retire", "domain": "src01.example", "key": "adm:1:a"},
                          {"type": "retire", "domain": "nope.example", "key": "adm:2:b"}])
        # keys ride the returned results (for the bridge ack) but are stripped from the log record.
        self.assertEqual([r["key"] for r in res], ["adm:1:a", "adm:2:b"])
        log = self.log()
        self.assertEqual(len(log), 2)
        self.assertNotIn("key", log[0])
        self.assertEqual({r["result"] for r in log}, {"applied", "rejected"})

    def test_no_write_when_nothing_applied(self):
        # A batch that only rejects must not create sources/registry.yml churn.
        self.apply([{"type": "retire", "domain": "nope.example"}])
        self.assertEqual(_read(self.reg_path), self.original)


class RealRegistryTest(unittest.TestCase):
    """These run against the live sources/registry.yml -- the byte-identity guarantee of §S3."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="admin-apply-real-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        os.makedirs(os.path.join(self.root, "sources"))
        self.reg_path = os.path.join(self.root, "sources", "registry.yml")
        shutil.copy(os.path.join(REPO, "sources", "registry.yml"), self.reg_path)
        self.original = _read(self.reg_path)

    def test_noop_batch_leaves_registry_byte_identical(self):
        apply_mod.apply_actions(self.root, [], today=TODAY)
        self.assertEqual(_read(self.reg_path), self.original)

    def test_mutating_action_changes_only_its_domain_block(self):
        # A probation weekend source: retiring it keeps every stream above the floor, so the batch
        # applies and writes. Only acoup.blog's text block may differ afterwards.
        target = "acoup.blog"
        self.assertEqual(registry.yaml_load(self.original)[target]["status"], "probation")
        res = apply_mod.apply_actions(self.root, [{"type": "retire", "domain": target}], today=TODAY)
        self.assertEqual(res[0]["result"], "applied", res[0].get("error"))
        before, after = _blocks(self.original), _blocks(_read(self.reg_path))
        self.assertEqual(set(before), set(after), "a domain block appeared or vanished")
        for key in before:
            if key.strip() == target + ":":
                self.assertNotEqual(before[key], after[key], "target block did not change")
            else:
                self.assertEqual(before[key], after[key],
                                 "unrelated block reformatted: %r" % key.strip())


if __name__ == "__main__":
    unittest.main()
