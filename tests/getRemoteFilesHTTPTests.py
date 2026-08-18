import os
import shutil
import tempfile
import unittest
from typing import Any
from unittest.mock import MagicMock, PropertyMock, patch

import requests
from urllib3.exceptions import MaxRetryError

from wwpdb.apps.val_rel.utils.http_protocol.getRemoteFilesHTTP import (
    GetRemoteFilesHttp,
    remove_local_temp_http,
    setup_local_temp_http,
)

SITE_ID = "WWPDB_DEPLOY_TEST"
MODULE = "wwpdb.apps.val_rel.utils.http_protocol.getRemoteFilesHTTP"


class SetupRemoveLocalTempHttpTests(unittest.TestCase):
    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_returns_existing_temp_dir_unchanged(self) -> None:
        ret = setup_local_temp_http(temp_dir=self.test_dir, suffix="pdb", session_path="/does/not/matter")
        self.assertEqual(ret, self.test_dir)

    def test_creates_temp_dir_under_session_path(self) -> None:
        session_path = os.path.join(self.test_dir, "sessions")
        ret = setup_local_temp_http(temp_dir=None, suffix="pdb", session_path=session_path)
        self.assertTrue(os.path.exists(session_path))
        self.assertTrue(os.path.exists(ret))
        self.assertTrue(os.path.dirname(ret) == session_path)
        self.assertIn("http_pdb_", os.path.basename(ret))

    def test_remove_temp_dir(self) -> None:
        target = os.path.join(self.test_dir, "target")
        os.makedirs(target)
        remove_local_temp_http(target)
        self.assertFalse(os.path.exists(target))

    def test_remove_missing_temp_dir_no_error(self) -> None:
        remove_local_temp_http(os.path.join(self.test_dir, "does_not_exist"))

    def test_remove_require_empty_skips_non_empty_dir(self) -> None:
        target = os.path.join(self.test_dir, "target")
        os.makedirs(target)
        with open(os.path.join(target, "file.txt"), "w") as fout:
            fout.write("data")
        remove_local_temp_http(target, require_empty=True)
        self.assertTrue(os.path.exists(target))

    def test_remove_require_empty_removes_empty_dir(self) -> None:
        target = os.path.join(self.test_dir, "target")
        os.makedirs(target)
        remove_local_temp_http(target, require_empty=True)
        self.assertFalse(os.path.exists(target))


class GetRemoteFilesHttpTests(unittest.TestCase):
    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()

        vc_patcher = patch(f"{MODULE}.ValConfig")
        mock_vc_class = vc_patcher.start()
        self.addCleanup(vc_patcher.stop)
        self.mock_vc = MagicMock()
        self.mock_vc.connection_timeout = 5
        self.mock_vc.read_timeout = 5
        self.mock_vc.retries = 3
        self.mock_vc.backoff_factor = 1
        self.mock_vc.status_force_list = [429, 500, 502, 503, 504]
        mock_vc_class.return_value = self.mock_vc

        eh_patcher = patch(f"{MODULE}.EmailHandler")
        self.mock_eh_class = eh_patcher.start()
        self.addCleanup(eh_patcher.stop)
        self.mock_eh = MagicMock()
        self.mock_eh_class.return_value = self.mock_eh

        session_patcher = patch(f"{MODULE}.requests.Session")
        mock_session_class = session_patcher.start()
        self.addCleanup(session_patcher.stop)
        self.mock_session = MagicMock()
        mock_session_class.return_value.__enter__.return_value = self.mock_session

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _make_response(self, status_code: int = 200, content: bytes = b"data", content_length: Any = None) -> MagicMock:
        response = MagicMock()
        response.status_code = status_code
        response.content = content
        headers = {}
        if content_length is not None:
            headers["content-length"] = str(content_length)
        response.headers = headers
        return response

    def test_constructor_reads_val_config_and_creates_email_handler(self) -> None:
        GetRemoteFilesHttp(server="files.wwpdb.org", cache=None, site_id=SITE_ID)
        self.mock_eh_class.assert_called_once_with(SITE_ID)

    def test_get_url_raises_without_url(self) -> None:
        grf = GetRemoteFilesHttp(site_id=SITE_ID)
        with self.assertRaises(ValueError):
            grf.get_url(url=None, output_path=self.test_dir)

    def test_get_url_raises_without_output_path(self) -> None:
        grf = GetRemoteFilesHttp(site_id=SITE_ID)
        with self.assertRaises(ValueError):
            grf.get_url(url="https://example.org/1abc.cif", output_path=None)

    def test_get_url_delegates_to_get_file(self) -> None:
        grf = GetRemoteFilesHttp(site_id=SITE_ID)
        with patch.object(grf, "get_file") as mock_get_file:
            ret = grf.get_url(url="https://example.org/1abc.cif", output_path=self.test_dir)
            mock_get_file.assert_called_once_with("https://example.org/1abc.cif", self.test_dir)
            self.assertEqual(ret, "1abc.cif")

    def test_is_file_true_for_small_ok_response(self) -> None:
        self.mock_session.head.return_value = self._make_response(status_code=200, content_length=100)
        grf = GetRemoteFilesHttp(site_id=SITE_ID)
        self.assertTrue(grf.is_file("https://example.org/1abc.cif"))

    def test_is_file_false_for_error_status(self) -> None:
        self.mock_session.head.return_value = self._make_response(status_code=404, content_length=100)
        grf = GetRemoteFilesHttp(site_id=SITE_ID)
        self.assertFalse(grf.is_file("https://example.org/1abc.cif"))

    def test_is_file_false_without_content_length(self) -> None:
        self.mock_session.head.return_value = self._make_response(status_code=200, content_length=None)
        grf = GetRemoteFilesHttp(site_id=SITE_ID)
        self.assertFalse(grf.is_file("https://example.org/1abc.cif"))

    def test_is_file_false_for_zero_content_length(self) -> None:
        self.mock_session.head.return_value = self._make_response(status_code=200, content_length=0)
        grf = GetRemoteFilesHttp(site_id=SITE_ID)
        self.assertFalse(grf.is_file("https://example.org/1abc.cif"))

    def test_is_file_reraises_on_exception(self) -> None:
        self.mock_session.head.side_effect = requests.exceptions.ConnectionError("boom")
        grf = GetRemoteFilesHttp(site_id=SITE_ID)
        with self.assertRaises(requests.exceptions.ConnectionError):
            grf.is_file("https://example.org/1abc.cif")

    def test_http_request_success_writes_file(self) -> None:
        self.mock_session.get.return_value = self._make_response(status_code=200, content=b"hello", content_length=5)
        grf = GetRemoteFilesHttp(site_id=SITE_ID)
        outfile = os.path.join(self.test_dir, "out.cif")
        ret = grf.httpRequest("https://example.org/1abc.cif", outfile)
        self.assertTrue(ret)
        with open(outfile, "rb") as fin:
            self.assertEqual(fin.read(), b"hello")
        self.mock_eh.send_email_admins.assert_not_called()

    def test_http_request_success_despite_content_length_mismatch(self) -> None:
        self.mock_session.get.return_value = self._make_response(status_code=200, content=b"hello", content_length=999)
        grf = GetRemoteFilesHttp(site_id=SITE_ID)
        outfile = os.path.join(self.test_dir, "out.cif")
        ret = grf.httpRequest("https://example.org/1abc.cif", outfile)
        self.assertTrue(ret)

    def test_http_request_error_status_sends_admin_email(self) -> None:
        self.mock_session.get.return_value = self._make_response(status_code=404, content=b"", content_length=0)
        grf = GetRemoteFilesHttp(site_id=SITE_ID)
        outfile = os.path.join(self.test_dir, "out.cif")
        ret = grf.httpRequest("https://example.org/1abc.cif", outfile)
        self.assertFalse(ret)
        self.mock_eh.send_email_admins.assert_called_once()

    def test_http_request_max_retry_error_sends_admin_email(self) -> None:
        self.mock_session.get.side_effect = MaxRetryError(pool=MagicMock(), url="https://example.org/1abc.cif")
        grf = GetRemoteFilesHttp(site_id=SITE_ID)
        outfile = os.path.join(self.test_dir, "out.cif")
        ret = grf.httpRequest("https://example.org/1abc.cif", outfile)
        self.assertFalse(ret)
        self.mock_eh.send_email_admins.assert_called_once()

    def test_http_request_connect_timeout_sends_admin_email(self) -> None:
        self.mock_session.get.side_effect = requests.exceptions.ConnectTimeout("boom")
        grf = GetRemoteFilesHttp(site_id=SITE_ID)
        outfile = os.path.join(self.test_dir, "out.cif")
        ret = grf.httpRequest("https://example.org/1abc.cif", outfile)
        self.assertFalse(ret)
        self.mock_eh.send_email_admins.assert_called_once()

    def test_http_request_connection_error_sends_admin_email(self) -> None:
        self.mock_session.get.side_effect = requests.exceptions.ConnectionError("boom")
        grf = GetRemoteFilesHttp(site_id=SITE_ID)
        outfile = os.path.join(self.test_dir, "out.cif")
        ret = grf.httpRequest("https://example.org/1abc.cif", outfile)
        self.assertFalse(ret)
        self.mock_eh.send_email_admins.assert_called_once()

    def test_http_request_read_timeout_during_get_sends_admin_email(self) -> None:
        self.mock_session.get.side_effect = requests.exceptions.ReadTimeout("boom")
        grf = GetRemoteFilesHttp(site_id=SITE_ID)
        outfile = os.path.join(self.test_dir, "out.cif")
        ret = grf.httpRequest("https://example.org/1abc.cif", outfile)
        self.assertFalse(ret)
        self.mock_eh.send_email_admins.assert_called_once()

    def test_http_request_generic_request_exception_sends_admin_email(self) -> None:
        self.mock_session.get.side_effect = requests.exceptions.RequestException("boom")
        grf = GetRemoteFilesHttp(site_id=SITE_ID)
        outfile = os.path.join(self.test_dir, "out.cif")
        ret = grf.httpRequest("https://example.org/1abc.cif", outfile)
        self.assertFalse(ret)
        self.mock_eh.send_email_admins.assert_called_once()

    def test_http_request_read_timeout_while_writing_removes_partial_file(self) -> None:
        response = self._make_response(status_code=200, content_length=5)
        type(response).content = PropertyMock(side_effect=requests.exceptions.ReadTimeout("boom"))
        self.mock_session.get.return_value = response
        grf = GetRemoteFilesHttp(site_id=SITE_ID)
        outfile = os.path.join(self.test_dir, "out.cif")
        with open(outfile, "w") as fout:
            fout.write("partial")
        ret = grf.httpRequest("https://example.org/1abc.cif", outfile)
        self.assertFalse(ret)
        self.assertFalse(os.path.exists(outfile))
        self.mock_eh.send_email_admins.assert_called_once()

    def test_setup_output_path_creates_missing_directory(self) -> None:
        grf = GetRemoteFilesHttp(site_id=SITE_ID)
        missing_dir = os.path.join(self.test_dir, "missing")
        grf._setup_output_path(missing_dir)  # noqa: SLF001 pylint: disable=protected-access
        self.assertTrue(os.path.exists(missing_dir))

    def test_get_file_uses_cache_hit_and_skips_download(self) -> None:
        with patch(f"{MODULE}.PersistFileCache") as mock_pfc_class:
            mock_pfc = MagicMock()
            mock_pfc.exists.return_value = True
            mock_pfc_class.return_value = mock_pfc
            grf = GetRemoteFilesHttp(cache=self.test_dir, site_id=SITE_ID)
            output_path = os.path.join(self.test_dir, "outdir")
            grf.get_file("https://example.org/1abc.cif", output_path)
            mock_pfc.get_file.assert_called_once()
            self.mock_session.head.assert_not_called()
            self.mock_session.get.assert_not_called()

    def test_get_file_cache_miss_downloads_and_populates_cache(self) -> None:
        self.mock_session.head.return_value = self._make_response(status_code=200, content_length=5)
        self.mock_session.get.return_value = self._make_response(status_code=200, content=b"hello", content_length=5)
        with patch(f"{MODULE}.PersistFileCache") as mock_pfc_class:
            mock_pfc = MagicMock()
            mock_pfc.exists.return_value = False
            mock_pfc_class.return_value = mock_pfc
            grf = GetRemoteFilesHttp(cache=self.test_dir, site_id=SITE_ID)
            output_path = os.path.join(self.test_dir, "outdir")
            grf.get_file("https://example.org/1abc.cif", output_path)
            mock_pfc.add_file.assert_called_once()

    def test_get_file_no_cache_skips_download_when_not_a_file(self) -> None:
        self.mock_session.head.return_value = self._make_response(status_code=404, content_length=0)
        grf = GetRemoteFilesHttp(cache=None, site_id=SITE_ID)
        output_path = os.path.join(self.test_dir, "outdir")
        grf.get_file("https://example.org/1abc.cif", output_path)
        self.mock_session.get.assert_not_called()

    def test_handle_exception_sends_single_admin_email(self) -> None:
        grf = GetRemoteFilesHttp(site_id=SITE_ID)
        grf.handle_exception("something broke")
        self.mock_eh.send_email_admins.assert_called_once_with("something broke")

    def test_disconnect_is_noop(self) -> None:
        grf = GetRemoteFilesHttp(site_id=SITE_ID)
        grf.disconnect()  # should not raise


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
