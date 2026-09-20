"""
Test Suite for SystemIntegrationValidator.
Verifies that the validator:
1. Performs real functional checks (not recursive pytest)
2. Returns a structurally valid SystemIntegrationReport
3. Contains the correct number of registered subsystems
4. Does NOT contain subprocess pytest calls (fork-bomb check)
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath('src'))

from system_integration_validator import SystemIntegrationValidator, SystemIntegrationReport, SubsystemStatus


class TestSystemIntegrationValidator(unittest.TestCase):

    def test_no_recursive_pytest_subprocess(self):
        """Verifies the validator does not recursively invoke pytest via subprocess."""
        import inspect
        source_validate = inspect.getsource(SystemIntegrationValidator.validate_all_subsystems)
        source_get_checks = inspect.getsource(SystemIntegrationValidator._get_checks)

        # The execution paths must not spawn subprocess pytest
        subprocess_pytest_pattern = 'subprocess.run('
        self.assertNotIn(
            subprocess_pytest_pattern, 
            source_validate,
            "validate_all_subsystems must not use subprocess.run"
        )
        self.assertNotIn(
            subprocess_pytest_pattern,
            source_get_checks,
            "_get_checks must not contain direct subprocess.run to pytest"
        )


    def test_validate_all_subsystems_returns_report(self):
        """Verifies validate_all_subsystems returns a properly typed SystemIntegrationReport."""
        report = SystemIntegrationValidator.validate_all_subsystems()
        self.assertIsInstance(report, SystemIntegrationReport)

    def test_correct_subsystem_count(self):
        """Verifies exactly 39 subsystems are registered."""
        self.assertEqual(len(SystemIntegrationValidator.SUBSYSTEM_REGISTRY), 39)
        report = SystemIntegrationValidator.validate_all_subsystems()
        self.assertEqual(report.total_subsystems, 39)
        self.assertEqual(len(report.subsystems), 39)

    def test_report_fields_are_present(self):
        """Verifies SystemIntegrationReport has required fields."""
        report = SystemIntegrationValidator.validate_all_subsystems()
        self.assertIsInstance(report.total_subsystems, int)
        self.assertIsInstance(report.passed_subsystems, int)
        self.assertIsInstance(report.failed_subsystems, int)
        self.assertIsInstance(report.total_checks, int)
        self.assertIsInstance(report.passed_checks, int)
        self.assertIsInstance(report.failed_checks, int)
        self.assertIsInstance(report.validated_at, float)
        # There is NO zero_defect_guarantee field — that was fabricated
        self.assertFalse(hasattr(report, 'zero_defect_guarantee'),
                         "zero_defect_guarantee field must be removed — it was fabricated")

    def test_subsystem_status_entries_have_valid_statuses(self):
        """Verifies each subsystem status entry has a valid status string."""
        report = SystemIntegrationValidator.validate_all_subsystems()
        valid_statuses = {"PASSED", "FAILED", "WARNING", "SKIPPED"}
        for sub in report.subsystems:
            self.assertIn(sub.status, valid_statuses,
                          f"{sub.subsystem_id} has invalid status: {sub.status}")
            self.assertIsInstance(sub.verified_at, float)
            self.assertGreater(sub.verified_at, 0)

    def test_real_checks_are_performed(self):
        """Verifies that at least some checks were actually performed (not just skipped)."""
        report = SystemIntegrationValidator.validate_all_subsystems()
        total_actual_checks = report.total_checks
        self.assertGreater(total_actual_checks, 10,
                           f"Only {total_actual_checks} checks — validator may not be performing real checks")

    def test_critical_subsystems_pass(self):
        """Verifies that structurally critical subsystems (cache, race state schema) pass."""
        report = SystemIntegrationValidator.validate_all_subsystems()
        sub_by_id = {s.subsystem_id: s for s in report.subsystems}

        # SUB-11 (RaceState schema) must pass
        sub11 = sub_by_id.get("SUB-11")
        if sub11:
            self.assertIn(sub11.status, {"PASSED", "WARNING"},
                          f"RaceState schema check failed: {sub11.notes}")

        # SUB-37 (Cache operations) must pass
        sub37 = sub_by_id.get("SUB-37")
        if sub37:
            self.assertIn(sub37.status, {"PASSED", "WARNING"},
                          f"Cache check failed: {sub37.notes}")

    def test_overtake_model_subsystem_check(self):
        """Verifies SUB-24 (Overtake ML) reports the model loaded with gap_s feature."""
        report = SystemIntegrationValidator.validate_all_subsystems()
        sub_by_id = {s.subsystem_id: s for s in report.subsystems}
        sub24 = sub_by_id.get("SUB-24")
        if sub24:
            self.assertNotEqual(sub24.status, "FAILED",
                                f"OvertakeModel check FAILED: {sub24.notes}")
            if sub24.status == "PASSED":
                self.assertIn("gap_s", sub24.notes,
                              "gap_s must appear in SUB-24 notes confirming feature contract")


if __name__ == '__main__':
    unittest.main()
