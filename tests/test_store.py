import json
import os
import tempfile
import unittest
from datetime import timedelta

from helpers import la
import store


class StoreTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.s = store.Store(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_write_is_atomic_json_with_a_trailing_newline(self):
        self.s.write("docs/data/x.json", {"é": 1})
        path = os.path.join(self.tmp.name, "docs/data/x.json")
        with open(path, encoding="utf-8") as f:
            text = f.read()
        self.assertTrue(text.endswith("\n"))
        self.assertIn("é", text)
        self.assertFalse(os.path.exists(path + ".tmp"))
        self.assertEqual(self.s.read("docs/data/x.json"), {"é": 1})

    def test_missing_or_broken_files_read_as_default(self):
        self.assertEqual(self.s.read("nope.json", []), [])
        os.makedirs(os.path.join(self.tmp.name, "state"))
        with open(os.path.join(self.tmp.name, "state/refresh.json"), "w") as f:
            f.write("{broken")
        self.assertIsNone(self.s.last_refresh())

    def test_run_state(self):
        now = la(2026, 10, 10, 7, 31)
        self.assertIsNone(self.s.last_refresh())
        self.s.set_last_refresh(now)
        self.assertEqual(self.s.last_refresh(), now)
        self.assertEqual(self.s.read("state/refresh.json"), {"at": "2026-10-10T14:31:00Z"})
        self.assertIsNone(self.s.digest_date())
        self.s.set_digest_date("2026-10-10")
        self.assertEqual(self.s.digest_date(), "2026-10-10")

    def test_last_good_expires_after_24_hours(self):
        now = la(2026, 10, 10, 7, 31)
        self.s.remember("unr", [{"id": "unr:1"}], now)
        self.assertEqual(self.s.last_good("unr", now + timedelta(hours=23)), ([{"id": "unr:1"}], now))
        events, at = self.s.last_good("unr", now + timedelta(hours=25))
        self.assertEqual((events, at), ([], now))
        self.assertEqual(self.s.last_good("never", now), ([], None))


if __name__ == "__main__":
    unittest.main()
