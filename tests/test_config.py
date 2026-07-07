import importlib
import os
import sys
import unittest
from unittest.mock import patch


class ConfigEnvironmentTests(unittest.TestCase):
    def setUp(self):
        sys.modules.pop("checkin", None)

    def import_checkin(self):
        return importlib.import_module("checkin")

    def test_import_does_not_require_pushdeer_and_push_service_is_removed(self):
        checkin = self.import_checkin()

        self.assertFalse(hasattr(checkin.Config, "ENV_PUSH_KEY"))
        self.assertFalse(hasattr(checkin, "PushService"))

    def test_blank_optional_environment_values_use_defaults_without_warning(self):
        checkin = self.import_checkin()
        env = {
            "GLADOS_COOKIES": "koa:sess=fake; koa:sess.sig=fake;",
            "GLADOS_EXCHANGE_PLAN": "",
            "GLADOS_VERBOSE": "",
        }

        with patch.dict(os.environ, env, clear=True), self.assertLogs(checkin.logger, level="INFO") as logs:
            config = checkin.Config()

        self.assertEqual(config.cookies_list, ["koa:sess=fake; koa:sess.sig=fake;"])
        self.assertEqual(config.exchange_plan, "plan500")
        self.assertFalse(config.verbose)
        warning_lines = [line for line in logs.output if "WARNING" in line]
        self.assertEqual(warning_lines, [])

    def test_invalid_non_empty_optional_values_still_warn_and_fall_back(self):
        checkin = self.import_checkin()
        env = {
            "GLADOS_COOKIES": "koa:sess=fake; koa:sess.sig=fake;",
            "GLADOS_EXCHANGE_PLAN": "bad-plan",
            "GLADOS_VERBOSE": "maybe",
        }

        with patch.dict(os.environ, env, clear=True), self.assertLogs(checkin.logger, level="WARNING") as logs:
            config = checkin.Config()

        self.assertEqual(config.exchange_plan, "plan500")
        self.assertFalse(config.verbose)
        joined_logs = "\n".join(logs.output)
        self.assertIn("GLADOS_EXCHANGE_PLAN", joined_logs)
        self.assertIn("bad-plan", joined_logs)
        self.assertIn("GLADOS_VERBOSE", joined_logs)
        self.assertIn("maybe", joined_logs)

    def test_default_domains_only_include_glados_cloud(self):
        checkin = self.import_checkin()

        self.assertEqual(checkin.Config.DOMAINS, ["glados.cloud"])


if __name__ == "__main__":
    unittest.main()
