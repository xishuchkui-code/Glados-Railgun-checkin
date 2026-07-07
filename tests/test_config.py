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


class FakeConfig:
    verbose = False
    DOMAINS = ["glados.cloud"]
    cookies_list = ["koa:sess=fake; koa:sess.sig=fake;"]


class ResultFormattingTests(unittest.TestCase):
    def test_repeat_result_uses_repeat_emoji_instead_of_warning(self):
        checkin = importlib.import_module("checkin")
        checker = checkin.Checker(FakeConfig())
        repeat_result = checkin.CheckinResult(
            cookie_index=1,
            domain="glados.cloud",
            status="重复签到",
            code=checkin.CheckinStatus.REPEAT,
        )

        with patch.object(checker, "_checkin_on_domain", return_value=repeat_result), self.assertLogs(checkin.logger, level="INFO") as logs:
            checker.checkin_all()

        joined_logs = "\n".join(logs.output)
        self.assertIn("🔄 结果: 重复签到", joined_logs)
        self.assertNotIn("⚠️  结果: 重复签到", joined_logs)

    def test_verbose_summary_uses_readable_fields_without_p_zero_prefix(self):
        checkin = importlib.import_module("checkin")
        config = FakeConfig()
        config.verbose = True
        checker = checkin.Checker(config)
        checker.results = [
            checkin.CheckinResult(
                cookie_index=1,
                domain="glados.cloud",
                status="重复签到",
                points="0",
                days="371 天",
                points_total="26 积分",
                exchange="积分不足，未兑换",
                code=checkin.CheckinStatus.REPEAT,
            )
        ]

        _title, content, log_content = checker.format_results()

        expected = "#1 重复签到 | 剩余:371 天 | 总积分:26 积分 | 积分不足，未兑换"
        self.assertEqual(content, expected)
        self.assertEqual(log_content, expected)
        self.assertNotIn("P:0", content)

    def test_exit_code_is_failure_only_when_all_results_failed(self):
        checkin = importlib.import_module("checkin")
        checker = checkin.Checker(FakeConfig())

        checker.results = [
            checkin.CheckinResult(1, "glados.cloud", status="签到失败", code=checkin.CheckinStatus.FAILURE)
        ]
        self.assertEqual(checker.get_exit_code(), 1)

        checker.results = [
            checkin.CheckinResult(1, "glados.cloud", status="重复签到", code=checkin.CheckinStatus.REPEAT)
        ]
        self.assertEqual(checker.get_exit_code(), 0)


if __name__ == "__main__":
    unittest.main()
