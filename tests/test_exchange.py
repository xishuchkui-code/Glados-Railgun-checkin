import unittest
from unittest.mock import patch

import checkin


class FakeResponse:
    ok = True
    text = "{}"


class FakeSession:
    def __init__(self):
        self.headers = {}
        self.post_calls = []

    def post(self, url, headers=None, json=None, timeout=None):
        self.post_calls.append({
            "url": url,
            "headers": headers,
            "json": json,
            "timeout": timeout,
        })
        return FakeResponse()

    def get(self, url, headers=None, timeout=None):
        return FakeResponse()

    def close(self):
        pass


class ApiRequestTests(unittest.TestCase):
    def test_post_requests_send_json_body(self):
        api = checkin.API("glados.cloud", cookie_index=1)
        fake_session = FakeSession()
        api.session = fake_session

        response = api._make_request(
            "https://glados.cloud/api/user/exchange",
            "POST",
            {"planType": "plan500"},
            "koa:sess=fake;",
        )

        self.assertIsInstance(response, FakeResponse)
        self.assertEqual(fake_session.post_calls[0]["json"], {"planType": "plan500"})
        self.assertEqual(fake_session.post_calls[0]["headers"]["cookie"], "koa:sess=fake;")


class FakeConfig:
    verbose = False
    exchange_plan = "plan500"
    EXCHANGE_PLANS = {"plan500": 500}


class FakeAPI:
    instances = []

    def __init__(self, domain, cookie_index, verbose=False):
        self.exchange_calls = []
        FakeAPI.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def get_status(self, cookie):
        return "10 天", 0

    def checkin(self, cookie):
        return {"status": "签到成功", "points": "1", "message": "ok", "code": checkin.CheckinStatus.SUCCESS}

    def get_points(self, cookie):
        return "100 积分", 100

    def exchange(self, cookie, plan, required_points):
        self.exchange_calls.append((cookie, plan, required_points))
        return "兑换成功: plan500"


class CheckerExchangeTests(unittest.TestCase):
    def test_skip_exchange_when_points_are_below_required_plan_points(self):
        FakeAPI.instances = []
        checker = checkin.Checker(FakeConfig())

        with patch.object(checkin, "API", FakeAPI):
            result = checker._checkin_on_domain("koa:sess=fake;", 1, "glados.cloud")

        self.assertEqual(result.exchange, "积分不足，未兑换")
        self.assertEqual(FakeAPI.instances[0].exchange_calls, [])


if __name__ == "__main__":
    unittest.main()
