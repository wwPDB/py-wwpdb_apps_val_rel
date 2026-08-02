import unittest
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, patch

from wwpdb.apps.val_rel.config.ValConfig import ValConfig

SITE_ID = "WWPDB_DEPLOY_TEST"


class FakeConfigInfo:
    """Stand-in for ConfigInfo returning caller-supplied values for known keys."""

    def __init__(self, values: Dict[str, Any]) -> None:
        self._values = values

    def get(self, keyword: str, default: Any = None) -> Any:
        return self._values.get(keyword, default)


class ValConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_common = MagicMock()
        self.mock_common.get_site_web_apps_sessions_path.return_value = "/sessions"
        self.mock_common.get_site_web_apps_top_sessions_path.return_value = "/top_sessions"

        common_patcher = patch("wwpdb.apps.val_rel.config.ValConfig.ConfigInfoAppCommon")
        mock_common_class = common_patcher.start()
        self.addCleanup(common_patcher.stop)
        mock_common_class.return_value = self.mock_common

        self.config_patcher = patch("wwpdb.apps.val_rel.config.ValConfig.ConfigInfo")
        self.mock_config_class = self.config_patcher.start()
        self.addCleanup(self.config_patcher.stop)

        site_id_patcher = patch("wwpdb.apps.val_rel.config.ValConfig.getSiteId")
        self.mock_get_site_id = site_id_patcher.start()
        self.addCleanup(site_id_patcher.stop)
        self.mock_get_site_id.return_value = SITE_ID

    def _make_val_config(self, values: Optional[Dict[str, Any]] = None, site_id: Optional[str] = SITE_ID) -> ValConfig:
        self.mock_config_class.return_value = FakeConfigInfo(values or {})
        return ValConfig(site_id=site_id)

    def test_default_protocol_is_http(self) -> None:
        vc = self._make_val_config()
        self.assertEqual(vc.val_rel_protocol, "http")

    def test_valid_protocol_ftp(self) -> None:
        vc = self._make_val_config({"VAL_REL_PROTOCOL": "ftp"})
        self.assertEqual(vc.val_rel_protocol, "ftp")

    def test_invalid_protocol_falls_back_to_http(self) -> None:
        vc = self._make_val_config({"VAL_REL_PROTOCOL": "bogus"})
        self.assertEqual(vc.val_rel_protocol, "http")

    def test_site_id_defaults_via_get_site_id(self) -> None:
        self._make_val_config(site_id=None)
        self.mock_get_site_id.assert_called_once()

    def test_queue_name_from_config(self) -> None:
        vc = self._make_val_config({"SITE_MESSAGE_QUEUE": "my_queue"})
        self.assertEqual(vc.queue_name, "my_queue")

    def test_queue_name_default(self) -> None:
        vc = self._make_val_config()
        self.assertEqual(vc.queue_name, "val_release_queue_%s" % SITE_ID)

    def test_routing_key(self) -> None:
        vc = self._make_val_config()
        self.assertEqual(vc.routing_key, "val_release_requests_%s" % SITE_ID)

    def test_exchange(self) -> None:
        vc = self._make_val_config()
        self.assertEqual(vc.exchange, "val_release_exchange_%s" % SITE_ID)

    def test_http_server_default(self) -> None:
        vc = self._make_val_config()
        self.assertEqual(vc.http_server, "files.wwpdb.org")

    def test_http_server_custom(self) -> None:
        vc = self._make_val_config({"SITE_HTTP_SERVER": "custom.example.org"})
        self.assertEqual(vc.http_server, "custom.example.org")

    def test_ftp_server_default(self) -> None:
        vc = self._make_val_config()
        self.assertEqual(vc.ftp_server, "ftp.wwpdb.org")

    def test_ftp_server_custom(self) -> None:
        vc = self._make_val_config({"SITE_FTP_SERVER": "ftp.example.org"})
        self.assertEqual(vc.ftp_server, "ftp.example.org")

    def test_http_prefix_default(self) -> None:
        vc = self._make_val_config()
        self.assertEqual(vc.http_prefix, "/pub")

    def test_http_prefix_custom(self) -> None:
        vc = self._make_val_config({"SITE_HTTP_SERVER_PREFIX": "/custom"})
        self.assertEqual(vc.http_prefix, "/custom")

    def test_ftp_prefix_default(self) -> None:
        vc = self._make_val_config()
        self.assertEqual(vc.ftp_prefix, "/pub")

    def test_ftp_prefix_custom(self) -> None:
        vc = self._make_val_config({"SITE_FTP_SERVER_PREFIX": "/custom"})
        self.assertEqual(vc.ftp_prefix, "/custom")

    def test_session_path(self) -> None:
        vc = self._make_val_config()
        self.assertEqual(vc.session_path, "/sessions")

    def test_top_session_path(self) -> None:
        vc = self._make_val_config()
        self.assertEqual(vc.top_session_path, "/top_sessions")

    def test_top_session_path_raises_when_unset(self) -> None:
        self.mock_common.get_site_web_apps_top_sessions_path.return_value = None
        vc = self._make_val_config()
        with self.assertRaises(ValueError):
            _ = vc.top_session_path

    def test_val_cut_off(self) -> None:
        cutoff = {"pdb": "12:00", "emdb": "12:00"}
        vc = self._make_val_config({"PROJECT_VAL_REL_CUTOFF": cutoff})
        self.assertEqual(vc.val_cut_off, cutoff)

    def test_val_admin_email_empty_when_unset(self) -> None:
        vc = self._make_val_config()
        self.assertEqual(vc.val_admin_email, [])

    def test_val_admin_email_parses_csv(self) -> None:
        vc = self._make_val_config({"VAL_REL_ADMIN_EMAIL": "a@example.org,b@example.org"})
        self.assertEqual(vc.val_admin_email, ["a@example.org", "b@example.org"])

    def test_val_admin_email_raises_for_non_str(self) -> None:
        vc = self._make_val_config({"VAL_REL_ADMIN_EMAIL": ["a@example.org"]})
        with self.assertRaises(ValueError):
            _ = vc.val_admin_email

    def test_val_disable_multithread_true(self) -> None:
        vc = self._make_val_config({"VAL_REL_DISABLE_MULTITHREAD": True})
        self.assertTrue(vc.val_disable_multithread)

    def test_val_disable_multithread_false_when_unset(self) -> None:
        vc = self._make_val_config()
        self.assertFalse(vc.val_disable_multithread)

    def test_val_email_interval(self) -> None:
        vc = self._make_val_config()
        self.assertEqual(vc.val_email_interval, 60 * 60 * 24)

    def test_val_max_per_interval(self) -> None:
        vc = self._make_val_config()
        self.assertEqual(vc.val_max_per_interval, 10)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
