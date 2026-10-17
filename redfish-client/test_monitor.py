"""Basic unit tests that do not need a running mock server."""

import unittest
from unittest.mock import patch

import requests

import monitor


class MonitorTests(unittest.TestCase):
    @patch("monitor.requests.get")
    def test_get_json_uses_redfish_path_and_timeout(self, fake_get):
        fake_get.return_value.json.return_value = {"Name": "Demo Server"}
        result = monitor.get_json("/redfish/v1/Systems/1")
        self.assertEqual(result["Name"], "Demo Server")
        fake_get.assert_called_once_with(
            "http://127.0.0.1:8000/redfish/v1/Systems/1",
            headers={"Accept": "application/json"},
            timeout=5,
        )
        fake_get.return_value.raise_for_status.assert_called_once()

    def test_status_when_missing(self):
        self.assertEqual(monitor.status_text({}), "Unknown")

    def test_status_health(self):
        self.assertEqual(monitor.status_text({"Status": {"Health": "Warning"}}), "Warning")

    @patch("monitor.get_json")
    def test_get_members_follows_collection_links(self, fake_get_json):
        fake_get_json.side_effect = [
            {"Members": [{"@odata.id": "/redfish/v1/Systems/1"}]},
            {"Name": "Example System"},
        ]
        systems = monitor.get_members("/redfish/v1/Systems")
        self.assertEqual(systems[0]["Name"], "Example System")
        self.assertEqual(fake_get_json.call_count, 2)

    def test_reject_non_redfish_path(self):
        with self.assertRaises(ValueError):
            monitor.get_json("/invalid/path")
    #如果輸入 Warning 或 Critical，答案就應該是 True；其他這兩種正常或未知情況應該是 False。
    def test_needs_attention(self):
        self.assertTrue(monitor.needs_attention("Warning"))
        self.assertTrue(monitor.needs_attention("Critical"))
        self.assertFalse(monitor.needs_attention("OK"))
        self.assertFalse(monitor.needs_attention("Unknown"))

    def test_summarize_health(self):
        counts, overall = monitor.summarize_health(
            ["OK", "OK", "OK", "Warning"]
        )

        self.assertEqual(counts["OK"], 3)
        self.assertEqual(counts["Warning"], 1)
        self.assertEqual(counts["Critical"], 0)
        self.assertEqual(overall, "Warning")

    def test_summarize_health_empty(self):
        counts, overall = monitor.summarize_health([])

        self.assertEqual(sum(counts.values()), 0)
        self.assertEqual(overall, "Unknown")
    
if __name__ == "__main__":
    unittest.main()
