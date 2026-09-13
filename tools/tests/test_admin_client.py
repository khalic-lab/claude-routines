"""Spec tests for tools/admin/admin.py -- the bridge-side client (PLAN 2026-09-13 §2.5).

The network is faked (a stub urlopen that records each Request), so these assert the client's
contract without egress: drain-apply GETs /admin/drain, applies the batch to the registry and stashes
the keys; ack POSTs the stashed keys to /admin/ack and clears the stash; snapshot-push PUTs the built
snapshot to /admin/snapshot; every call sends the identifiable admin User-Agent; and any failure
warns and exits 1 (the bridge treats it as non-fatal).
"""
import importlib.util
import json
import os
import shutil
import tempfile
import unittest
import urllib.error

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FIXTURE_REGISTRY = os.path.join(os.path.dirname(__file__), "fixtures", "admin", "registry.yml")


def _load(name, relpath):
    spec = importlib.util.spec_from_file_location(name, os.path.join(REPO, relpath))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


admin = _load("_admin_client", "tools/admin/admin.py")


class _FakeResp:
    def __init__(self, payload):
        self._b = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._b

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class ClientBase(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="admin-client-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        os.makedirs(os.path.join(self.root, "sources"))
        shutil.copy(FIXTURE_REGISTRY, os.path.join(self.root, "sources", "registry.yml"))
        self.stash = os.path.join(self.root, "ack.json")

        self._saved = (admin.REPO, admin._ACK_STASH, admin.urllib.request.urlopen)
        admin.REPO = self.root
        admin._ACK_STASH = self.stash
        self.calls = []
        self.addCleanup(self._restore)

    def _restore(self):
        admin.REPO, admin._ACK_STASH, admin.urllib.request.urlopen = self._saved

    def install(self, handler):
        """handler(req) -> payload dict; records the Request for assertions."""
        def fake(req, timeout=None):
            self.calls.append(req)
            return _FakeResp(handler(req))
        admin.urllib.request.urlopen = fake

    def reg(self):
        path = os.path.join(self.root, "sources", "registry.yml")
        with open(path) as f:
            return admin.apply_mod.registry.yaml_load(f.read())


class DrainApplyTest(ClientBase):
    def test_drains_applies_and_stashes_keys(self):
        self.install(lambda req: {"records": [
            {"key": "adm:1:a", "type": "retire", "domain": "src01.example", "note": "x"}]})
        rc = admin.main(["drain-apply", "--worker", "https://w.example", "--token", "T"])
        self.assertEqual(rc, 0)
        req = self.calls[0]
        self.assertEqual(req.get_method(), "GET")
        self.assertEqual(req.full_url, "https://w.example/admin/drain")
        self.assertIn("admin-bridge", req.get_header("User-agent"))
        # applied to the registry
        self.assertEqual(self.reg()["src01.example"]["status"], "retired")
        # keys staged for ack
        with open(self.stash) as f:
            self.assertEqual(json.load(f)["keys"], ["adm:1:a"])

    def test_bad_action_still_stashed_for_ack(self):
        # A rejected action must be acked too, or it loops forever.
        self.install(lambda req: {"records": [
            {"key": "adm:9:z", "type": "retire", "domain": "nope.example"}]})
        admin.main(["drain-apply", "--worker", "https://w.example", "--token", "T"])
        with open(self.stash) as f:
            self.assertEqual(json.load(f)["keys"], ["adm:9:z"])

    def test_missing_creds_exits_1(self):
        # No --worker and no env: warn + exit 1, no request attempted.
        old = os.environ.pop("FEEDBACK_WORKER_URL", None)
        self.addCleanup(lambda: os.environ.__setitem__("FEEDBACK_WORKER_URL", old) if old else None)
        self.install(lambda req: {})
        rc = admin.main(["drain-apply", "--token", "T"])
        self.assertEqual(rc, 1)
        self.assertEqual(self.calls, [])


class AckTest(ClientBase):
    def test_posts_stashed_keys_and_clears_stash(self):
        with open(self.stash, "w") as f:
            json.dump({"keys": ["adm:1:a", "adm:2:b"], "worker": "https://w.example"}, f)
        self.install(lambda req: {"deleted": 2})
        rc = admin.main(["ack", "--token", "T"])
        self.assertEqual(rc, 0)
        req = self.calls[0]
        self.assertEqual(req.get_method(), "POST")
        self.assertEqual(req.full_url, "https://w.example/admin/ack")
        self.assertEqual(json.loads(req.data.decode())["keys"], ["adm:1:a", "adm:2:b"])
        self.assertFalse(os.path.exists(self.stash))  # cleared

    def test_no_stash_is_a_noop(self):
        self.install(lambda req: {})
        rc = admin.main(["ack", "--token", "T"])
        self.assertEqual(rc, 0)
        self.assertEqual(self.calls, [])


class SnapshotPushTest(ClientBase):
    def test_puts_built_snapshot(self):
        self.install(lambda req: {"ok": True, "bytes": 4096})
        rc = admin.main(["snapshot-push", "--worker", "https://w.example", "--token", "T"])
        self.assertEqual(rc, 0)
        req = self.calls[0]
        self.assertEqual(req.get_method(), "PUT")
        self.assertEqual(req.full_url, "https://w.example/admin/snapshot")
        self.assertIn("admin-bridge", req.get_header("User-agent"))
        body = json.loads(req.data.decode())
        self.assertIn("sources", body)
        self.assertIn("generated", body)
        self.assertGreater(len(body["sources"]), 0)

    def test_network_failure_warns_and_exits_1(self):
        def boom(req, timeout=None):
            raise urllib.error.URLError("no route")
        admin.urllib.request.urlopen = boom
        rc = admin.main(["snapshot-push", "--worker", "https://w.example", "--token", "T"])
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
