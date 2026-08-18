import os
import shutil
import tempfile
import unittest
from typing import List, Optional
from unittest.mock import MagicMock, patch

from wwpdb.apps.val_rel.utils.emailHandler import EmailHandler

SITE_ID = "WWPDB_DEPLOY_TEST"


class EmailHandlerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state_dir = tempfile.mkdtemp()

        vc_patcher = patch("wwpdb.apps.val_rel.utils.emailHandler.ValConfig")
        self.mock_vc_class = vc_patcher.start()
        self.addCleanup(vc_patcher.stop)

        of_patcher = patch("wwpdb.apps.val_rel.utils.emailHandler.outputFiles")
        self.mock_of_class = of_patcher.start()
        self.addCleanup(of_patcher.stop)
        self.mock_of = MagicMock()
        self.mock_of.get_root_state_folder.return_value = self.state_dir
        self.mock_of_class.return_value = self.mock_of

        site_id_patcher = patch("wwpdb.apps.val_rel.utils.emailHandler.getSiteId")
        self.mock_get_site_id = site_id_patcher.start()
        self.addCleanup(site_id_patcher.stop)
        self.mock_get_site_id.return_value = SITE_ID

        comm_patcher = patch("wwpdb.apps.val_rel.utils.emailHandler.ConfigInfoAppCommunication")
        self.mock_comm_class = comm_patcher.start()
        self.addCleanup(comm_patcher.stop)
        self.mock_comm = MagicMock()
        self.mock_comm.get_mailserver_name.return_value = "smtp.example.org"
        self.mock_comm.get_noreply_address.return_value = "noreply@example.org"
        self.mock_comm_class.return_value = self.mock_comm

        smtp_patcher = patch("wwpdb.apps.val_rel.utils.emailHandler.smtplib.SMTP")
        self.mock_smtp_class = smtp_patcher.start()
        self.addCleanup(smtp_patcher.stop)
        self.mock_smtp = MagicMock()
        self.mock_smtp_class.return_value.__enter__.return_value = self.mock_smtp

    def tearDown(self) -> None:
        shutil.rmtree(self.state_dir, ignore_errors=True)

    def _make_handler(
        self,
        admin_list: Optional[List[str]] = None,
        email_interval: int = 60 * 60 * 24,
        max_per_interval: int = 10,
    ) -> EmailHandler:
        mock_vc = MagicMock()
        mock_vc.val_admin_email = admin_list if admin_list is not None else []
        mock_vc.val_email_interval = email_interval
        mock_vc.val_max_per_interval = max_per_interval
        self.mock_vc_class.return_value = mock_vc
        return EmailHandler(site_id=SITE_ID)

    def test_constructor_reads_admin_list_and_intervals(self) -> None:
        eh = self._make_handler(admin_list=["a@example.org"], email_interval=123, max_per_interval=4)
        with patch.object(eh, "send_email") as mock_send_email:
            eh.send_email_admins("boom")
            mock_send_email.assert_called_once_with("boom", "a@example.org")

    def test_send_email_admins_calls_for_each_admin(self) -> None:
        eh = self._make_handler(admin_list=["a@example.org", "b@example.org"])
        with patch.object(eh, "send_email") as mock_send_email:
            eh.send_email_admins("boom")
            self.assertEqual(
                mock_send_email.call_args_list,
                [unittest.mock.call("boom", "a@example.org"), unittest.mock.call("boom", "b@example.org")],
            )

    def test_send_email_creates_missing_state_dir(self) -> None:
        shutil.rmtree(self.state_dir)
        eh = self._make_handler()
        eh.send_email("boom", "a@example.org")
        self.assertTrue(os.path.exists(self.state_dir))

    def test_send_email_first_time_sends(self) -> None:
        eh = self._make_handler()
        eh.send_email("boom", "a@example.org")
        self.mock_smtp.send_message.assert_called_once()
        sent_msg = self.mock_smtp.send_message.call_args[0][0]
        self.assertEqual(sent_msg["To"], "a@example.org")
        self.assertEqual(sent_msg["From"], "noreply@example.org")
        self.assertEqual(sent_msg["Subject"], "WWPDB Val Rel Exception")
        self.assertIn("boom", sent_msg.get_content())

    def test_send_email_within_interval_under_max_still_sends(self) -> None:
        eh = self._make_handler(email_interval=60 * 60 * 24, max_per_interval=10)
        eh.send_email("first", "a@example.org")
        eh.send_email("second", "a@example.org")
        self.assertEqual(self.mock_smtp.send_message.call_count, 2)

    def test_send_email_within_interval_over_max_is_suppressed(self) -> None:
        eh = self._make_handler(email_interval=60 * 60 * 24, max_per_interval=1)
        eh.send_email("first", "a@example.org")
        eh.send_email("second", "a@example.org")
        self.assertEqual(self.mock_smtp.send_message.call_count, 1)

    def test_send_email_after_interval_expires_resets_and_sends(self) -> None:
        eh = self._make_handler(email_interval=0, max_per_interval=1)
        eh.send_email("first", "a@example.org")
        eh.send_email("second", "a@example.org")
        eh.send_email("third", "a@example.org")
        # Interval is 0, so every call is treated as a fresh window and always sends.
        self.assertEqual(self.mock_smtp.send_message.call_count, 3)

    def test_send_email_tracks_recipients_independently(self) -> None:
        eh = self._make_handler(email_interval=60 * 60 * 24, max_per_interval=1)
        eh.send_email("first", "a@example.org")
        eh.send_email("first", "b@example.org")
        self.assertEqual(self.mock_smtp.send_message.call_count, 2)

    def test_email_builds_and_sends_message(self) -> None:
        eh = self._make_handler()
        eh.email("hello world", "a@example.org")
        self.mock_smtp_class.assert_called_with("smtp.example.org")
        self.mock_smtp.send_message.assert_called_once()
        sent_msg = self.mock_smtp.send_message.call_args[0][0]
        self.assertEqual(sent_msg["To"], "a@example.org")
        self.assertEqual(sent_msg["From"], "noreply@example.org")
        self.assertIn("hello world", sent_msg.get_content())

    def test_email_swallows_smtp_exception(self) -> None:
        eh = self._make_handler()
        self.mock_smtp.send_message.side_effect = OSError("connection refused")
        eh.email("hello world", "a@example.org")  # should not raise


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
