import unittest
from datetime import timedelta

from helpers import la
from schedule import Decision, decide


class ScheduleTest(unittest.TestCase):
    def test_first_run_refreshes(self):
        self.assertEqual(decide(la(2026, 10, 10, 3, 30), None, None), Decision(True, False))

    def test_refresh_every_2h50(self):
        now = la(2026, 10, 10, 14, 30)
        self.assertFalse(decide(now, now - timedelta(hours=2, minutes=49), "2026-10-10").refresh)
        self.assertTrue(decide(now, now - timedelta(hours=2, minutes=50), "2026-10-10").refresh)

    def test_digest_window_is_07_00_to_10_59(self):
        recent = la(2026, 10, 10, 6, 0)
        self.assertFalse(decide(la(2026, 10, 10, 6, 59), recent, "2026-10-09").digest)
        self.assertEqual(decide(la(2026, 10, 10, 7, 0), recent, "2026-10-09"), Decision(True, True))
        self.assertTrue(decide(la(2026, 10, 10, 10, 59), recent, "2026-10-09").digest)
        self.assertFalse(decide(la(2026, 10, 10, 11, 0), recent, "2026-10-09").digest)

    def test_digest_already_sent_today(self):
        now = la(2026, 10, 10, 8, 30)
        self.assertEqual(decide(now, now - timedelta(hours=1), "2026-10-10"), Decision(False, False))

    def test_failed_digest_retries_next_hour(self):
        now = la(2026, 10, 10, 8, 30)
        self.assertEqual(decide(now, now - timedelta(hours=1), "2026-10-09"), Decision(True, True))

    def test_no_webhook_means_no_digest_and_no_extra_refreshes(self):
        now = la(2026, 10, 10, 8, 30)
        self.assertEqual(decide(now, now - timedelta(hours=1), None, digest_enabled=False), Decision(False, False))

    def test_force_digest(self):
        now = la(2026, 10, 10, 15, 0)
        self.assertEqual(decide(now, now - timedelta(minutes=5), "2026-10-10", force_digest=True),
                         Decision(True, True))

    def test_digest_on_dst_change_days(self):
        # 2026-03-08 (spring forward) and 2026-11-01 (fall back): 07:30 local is still digest time.
        self.assertTrue(decide(la(2026, 3, 8, 7, 30), la(2026, 3, 8, 4, 0), "2026-03-07").digest)
        self.assertTrue(decide(la(2026, 11, 1, 7, 30), la(2026, 11, 1, 4, 0), "2026-10-31").digest)

    def test_elapsed_time_is_real_time_across_fall_back(self):
        # 00:30 PDT to 02:30 PST on 2026-11-01 is 3 real hours, though the wall clock moved 2.
        last = la(2026, 11, 1, 0, 30)               # PDT (-07:00)
        now = la(2026, 11, 1, 2, 30)                # PST (-08:00)
        self.assertTrue(decide(now, last, "2026-11-01").refresh)


if __name__ == "__main__":
    unittest.main()
