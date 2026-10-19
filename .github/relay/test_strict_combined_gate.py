import unittest

from strict_combined_gate import strict_summary


class StrictCombinedGateTest(unittest.TestCase):
    def test_real_unittest_success(self):
        s = strict_summary("Ran 455 tests in 20.1s\n\nOK\n", 0)
        self.assertEqual((s["status"], s["passed"], s["skipped"]), ("PASS", 455, 0))

    def test_success_exit_with_one_skip_must_fail(self):
        s = strict_summary("Ran 455 tests in 20.1s\n\nOK (skipped=1)\n", 0)
        self.assertEqual(s["status"], "FAIL")

    def test_expected_failure_must_fail(self):
        self.assertEqual(strict_summary("Ran 455 tests in 20.1s\n\nOK (expected failures=1)\n", 0)["status"], "FAIL")

    def test_nonzero_exit_must_fail(self):
        self.assertEqual(strict_summary("Ran 455 tests in 20.1s\n\nOK\n", 1)["status"], "FAIL")

    def test_missing_or_multiple_summary_must_fail(self):
        for output in ("Ran 455 tests in 20.1s\n", "Ran 1 test\nOK\nRan 455 tests\nOK\n"):
            with self.subTest(output=output):
                self.assertEqual(strict_summary(output, 0)["status"], "FAIL")

    def test_boolean_exit_code_must_fail(self):
        self.assertEqual(strict_summary("Ran 2 tests in 0.1s\n\nOK\n", False)["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
