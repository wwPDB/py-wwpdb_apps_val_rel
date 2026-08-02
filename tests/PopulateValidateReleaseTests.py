import json
import os
import unittest
from typing import Any
from unittest.mock import MagicMock, patch

from wwpdb.apps.val_rel.PopulateValidateRelease import PopulateValidateRelease

SITE_ID = "WWPDB_DEPLOY_TEST"
MODULE = "wwpdb.apps.val_rel.PopulateValidateRelease"


class BasePopulateValidateReleaseTest(unittest.TestCase):
    """Common mocking for PopulateValidateRelease tests.

    getSiteId/ValConfig (site config), FindAndProcessEntries/FindEntries (which
    have their own dedicated, separately-mocked test coverage), and
    MessagePublisher (the message queue -- not wwpdb.apps.validation, but still
    an external system) are all mocked, so these tests never touch real site
    config, a real queue, or any wwpdb.apps.validation code.
    """

    def setUp(self) -> None:
        site_id_patcher = patch(f"{MODULE}.getSiteId")
        self.mock_get_site_id = site_id_patcher.start()
        self.addCleanup(site_id_patcher.stop)
        self.mock_get_site_id.return_value = SITE_ID

        fape_patcher = patch(f"{MODULE}.FindAndProcessEntries")
        self.mock_fape_class = fape_patcher.start()
        self.addCleanup(fape_patcher.stop)
        self.mock_fape = MagicMock()
        self.mock_fape.get_found_entries.return_value = []
        self.mock_fape_class.return_value = self.mock_fape

        fe_patcher = patch(f"{MODULE}.FindEntries")
        self.mock_fe_class = fe_patcher.start()
        self.addCleanup(fe_patcher.stop)
        self.mock_fe = MagicMock()
        self.mock_fe.get_modified_pdb_paths.return_value = []
        self.mock_fe.get_added_pdb_paths.return_value = []
        self.mock_fe.get_emdb_paths.return_value = []
        self.mock_fe_class.return_value = self.mock_fe

        vc_patcher = patch(f"{MODULE}.ValConfig")
        self.mock_vc_class = vc_patcher.start()
        self.addCleanup(vc_patcher.stop)
        self.mock_vc = MagicMock()
        self.mock_vc.exchange = "the_exchange"
        self.mock_vc.queue_name = "the_queue"
        self.mock_vc.routing_key = "the_routing_key"
        self.mock_vc_class.return_value = self.mock_vc

        mp_patcher = patch(f"{MODULE}.MessagePublisher")
        self.mock_mp_class = mp_patcher.start()
        self.addCleanup(mp_patcher.stop)
        self.mock_mp = MagicMock()
        self.mock_mp.publish.return_value = True
        self.mock_mp.publishDirect.return_value = True
        self.mock_mp_class.return_value = self.mock_mp


class ConstructorTests(BasePopulateValidateReleaseTest):
    def test_site_id_defaults_via_get_site_id(self) -> None:
        PopulateValidateRelease(site_id=None)
        self.mock_get_site_id.assert_called_once()

    def test_site_id_explicit_skips_get_site_id(self) -> None:
        PopulateValidateRelease(site_id=SITE_ID)
        self.mock_get_site_id.assert_not_called()

    def test_priority_and_subscribe_together_exits(self) -> None:
        with patch(f"{MODULE}.sys.exit") as mock_exit:
            PopulateValidateRelease(site_id=SITE_ID, priority=True, subscribe="some_exchange")
        mock_exit.assert_called_once()

    def test_priority_true_builds_priorities(self) -> None:
        PopulateValidateRelease(site_id=SITE_ID, priority=True)
        self.mock_fe_class.assert_called_once_with(siteID=SITE_ID)

    def test_priority_false_does_not_build_priorities(self) -> None:
        PopulateValidateRelease(site_id=SITE_ID, priority=False)
        self.mock_fe_class.assert_not_called()


class FindAndProcessEntriesMethodTests(BasePopulateValidateReleaseTest):
    def test_find_and_process_entries_constructs_fape_with_expected_args(self) -> None:
        pvr = PopulateValidateRelease(
            site_id=SITE_ID,
            entry_string="1abc",
            entry_file="entries.txt",
            entry_list=["2xyz"],
            skip_emdb=True,
            pdb_release=True,
            emdb_release=True,
            nocache=True,
        )
        pvr.find_and_process_entries()
        self.mock_fape_class.assert_called_once_with(
            entry_string="1abc",
            entry_file="entries.txt",
            entry_list=["2xyz"],
            skip_emdb=True,
            pdb_release=True,
            emdb_release=True,
            site_id=SITE_ID,
            nocache=True,
        )
        self.mock_fape.run_process.assert_called_once()

    def test_find_and_process_entries_stores_found_entries(self) -> None:
        # __messages has no public getter; verify indirectly through the one
        # place it's consumed -- the message actually published.
        self.mock_fape.get_found_entries.return_value = [{"pdbID": "1abc"}]
        pvr = PopulateValidateRelease(site_id=SITE_ID)
        pvr.find_and_process_entries()
        pvr.process_messages()
        sent_message = json.loads(self.mock_mp.publish.call_args.kwargs["message"])
        self.assertEqual(sent_message["pdbID"], "1abc")

    def test_run_process_calls_find_and_process_then_process_messages(self) -> None:
        pvr = PopulateValidateRelease(site_id=SITE_ID)
        with patch.object(pvr, "find_and_process_entries") as mock_find, patch.object(
            pvr, "process_messages"
        ) as mock_process:
            pvr.run_process()
        mock_find.assert_called_once()
        mock_process.assert_called_once()


class MakePrioritiesTests(BasePopulateValidateReleaseTest):
    def test_make_priorities_builds_modified_basename_list(self) -> None:
        self.mock_fe.get_modified_pdb_paths.return_value = ["/data/modified/1abc", "/data/modified/2xyz"]
        pvr = PopulateValidateRelease(site_id=SITE_ID, priority=True)
        self.assertEqual(pvr.modified_priorities, ["1abc", "2xyz"])

    # __added_priorities/__emdb_priorities have no public getters; they are
    # covered indirectly through get_priority() in GetPriorityTests below.


class GetPriorityTests(BasePopulateValidateReleaseTest):
    def _make_with_priorities(
        self,
        modified: Any = None,
        added: Any = None,
        emdb_paths: Any = None,
        validation_sub_dir: str = "current",
        always_recalculate: bool = False,
    ) -> PopulateValidateRelease:
        self.mock_fe.get_modified_pdb_paths.return_value = modified or []
        self.mock_fe.get_added_pdb_paths.return_value = added or []
        self.mock_fe.get_emdb_paths.return_value = emdb_paths or []
        return PopulateValidateRelease(
            site_id=SITE_ID,
            priority=True,
            validation_sub_dir=validation_sub_dir,
            always_recalculate=always_recalculate,
        )

    def test_missing_subdir_always_returns_10(self) -> None:
        pvr = self._make_with_priorities(validation_sub_dir="missing")
        self.assertEqual(pvr.get_priority({"pdbID": "1abc"}), 10)
        self.assertEqual(pvr.get_priority({}), 10)

    def test_neither_pdb_nor_emdb_returns_1(self) -> None:
        pvr = self._make_with_priorities()
        self.assertEqual(pvr.get_priority({}), 1)

    def test_both_pdb_and_emdb_treated_as_emdb_only(self) -> None:
        pvr = self._make_with_priorities(emdb_paths=["/data/emd/EMD-1234"])
        ret = pvr.get_priority({"pdbID": "1abc", "emdbID": "EMD-1234"})
        # treated as emd-only; EMD-1234 has no discoverable map dir => modified True => priority 2
        self.assertEqual(ret, 2)

    def test_always_recalculate_pdb_gives_priority_4(self) -> None:
        pvr = self._make_with_priorities(always_recalculate=True)
        self.assertEqual(pvr.get_priority({"pdbID": "1abc"}), 4)

    def test_always_recalculate_emdb_gives_priority_2(self) -> None:
        pvr = self._make_with_priorities(always_recalculate=True)
        self.assertEqual(pvr.get_priority({"emdbID": "EMD-1234"}), 2)

    def test_pdb_in_modified_gives_priority_4(self) -> None:
        pvr = self._make_with_priorities(modified=["/data/modified/1abc"])
        self.assertEqual(pvr.get_priority({"pdbID": "1abc"}), 4)

    def test_pdb_in_added_gives_priority_8(self) -> None:
        pvr = self._make_with_priorities(added=["/data/added/1abc"])
        self.assertEqual(pvr.get_priority({"pdbID": "1abc"}), 8)

    def test_pdb_unknown_returns_1(self) -> None:
        pvr = self._make_with_priorities()
        self.assertEqual(pvr.get_priority({"pdbID": "1abc"}), 1)

    def test_emdb_with_map_dir_present_gives_priority_6(self) -> None:
        emd_path = os.path.dirname(__file__)  # a directory that definitely exists
        map_dir = os.path.join(emd_path, "map")
        os.makedirs(map_dir, exist_ok=True)
        try:
            pvr = self._make_with_priorities(emdb_paths=[emd_path])
            emdb_id = os.path.basename(emd_path)
            self.assertEqual(pvr.get_priority({"emdbID": emdb_id}), 6)
        finally:
            os.rmdir(map_dir)

    def test_emdb_without_map_dir_gives_priority_2(self) -> None:
        emd_path = os.path.dirname(__file__)
        pvr = self._make_with_priorities(emdb_paths=[emd_path])
        emdb_id = os.path.basename(emd_path)
        self.assertEqual(pvr.get_priority({"emdbID": emdb_id}), 2)

    def test_emdb_unknown_returns_1(self) -> None:
        pvr = self._make_with_priorities()
        self.assertEqual(pvr.get_priority({"emdbID": "EMD-0000"}), 1)


class ProcessMessagesTests(BasePopulateValidateReleaseTest):
    def test_empty_messages_does_not_publish(self) -> None:
        pvr = PopulateValidateRelease(site_id=SITE_ID)
        pvr.process_messages()
        self.mock_mp.publish.assert_not_called()

    def test_message_gets_common_fields(self) -> None:
        self.mock_fape.get_found_entries.return_value = [{"pdbID": "1abc"}]
        pvr = PopulateValidateRelease(site_id=SITE_ID, keep_logs=True, validation_sub_dir="current")
        pvr.find_and_process_entries()
        pvr.process_messages()
        sent_message = json.loads(self.mock_mp.publish.call_args.kwargs["message"])
        self.assertEqual(sent_message["siteID"], SITE_ID)
        self.assertTrue(sent_message["keepLog"])
        self.assertEqual(sent_message["subfolder"], "current")

    def test_optional_fields_only_added_when_true(self) -> None:
        self.mock_fape.get_found_entries.return_value = [{"pdbID": "1abc"}]
        pvr = PopulateValidateRelease(site_id=SITE_ID)
        pvr.find_and_process_entries()
        pvr.process_messages()
        sent_message = json.loads(self.mock_mp.publish.call_args.kwargs["message"])
        for optional_field in ("nocache", "outputRoot", "alwaysRecalculate", "skipGzip", "skip_emdb"):
            self.assertNotIn(optional_field, sent_message)

    def test_optional_fields_present_when_flags_set(self) -> None:
        self.mock_fape.get_found_entries.return_value = [{"pdbID": "1abc"}]
        pvr = PopulateValidateRelease(
            site_id=SITE_ID,
            nocache=True,
            output_root="/out",
            always_recalculate=True,
            skip_gzip=True,
            skip_emdb=True,
        )
        pvr.find_and_process_entries()
        pvr.process_messages()
        sent_message = json.loads(self.mock_mp.publish.call_args.kwargs["message"])
        self.assertTrue(sent_message["nocache"])
        self.assertEqual(sent_message["outputRoot"], "/out")
        self.assertTrue(sent_message["alwaysRecalculate"])
        self.assertTrue(sent_message["skipGzip"])
        self.assertTrue(sent_message["skip_emdb"])

    def test_publishes_via_standard_queue_by_default(self) -> None:
        self.mock_fape.get_found_entries.return_value = [{"pdbID": "1abc"}]
        pvr = PopulateValidateRelease(site_id=SITE_ID)
        pvr.find_and_process_entries()
        pvr.process_messages()
        self.mock_mp.publish.assert_called_once_with(
            message=json.dumps(
                {
                    "pdbID": "1abc",
                    "siteID": SITE_ID,
                    "keepLog": False,
                    "subfolder": "current",
                }
            ),
            exchangeName="the_exchange",
            queueName="the_queue",
            routingKey="the_routing_key",
        )
        self.mock_mp.publishDirect.assert_not_called()

    def test_publishes_with_priority_when_priority_queue(self) -> None:
        self.mock_fape.get_found_entries.return_value = [{"pdbID": "1abc"}]
        pvr = PopulateValidateRelease(site_id=SITE_ID, priority=True, always_recalculate=True)
        pvr.find_and_process_entries()
        pvr.process_messages()
        self.assertEqual(self.mock_mp.publish.call_args.kwargs["priority"], 4)

    def test_publishes_direct_when_subscribe_set(self) -> None:
        self.mock_fape.get_found_entries.return_value = [{"pdbID": "1abc"}]
        pvr = PopulateValidateRelease(site_id=SITE_ID, subscribe="some_exchange")
        pvr.find_and_process_entries()
        pvr.process_messages()
        self.mock_mp.publishDirect.assert_called_once()
        self.assertEqual(self.mock_mp.publishDirect.call_args.kwargs["exchangeName"], "some_exchange")
        self.mock_mp.publish.assert_not_called()

    def test_stops_publishing_after_failure(self) -> None:
        self.mock_fape.get_found_entries.return_value = [{"pdbID": "1abc"}, {"pdbID": "2xyz"}]
        self.mock_mp.publish.side_effect = [False, True]
        pvr = PopulateValidateRelease(site_id=SITE_ID)
        pvr.find_and_process_entries()
        pvr.process_messages()
        self.assertEqual(self.mock_mp.publish.call_count, 1)


class TestMethodTests(BasePopulateValidateReleaseTest):
    def test_non_priority_queue_logs_and_returns(self) -> None:
        pvr = PopulateValidateRelease(site_id=SITE_ID, priority=False)
        pvr.test()
        self.mock_fape_class.assert_not_called()

    def test_priority_queue_processes_and_logs_without_publishing(self) -> None:
        self.mock_fape.get_found_entries.return_value = [{"pdbID": "1abc"}]
        pvr = PopulateValidateRelease(site_id=SITE_ID, priority=True)
        pvr.test()
        self.mock_fape.find_onedep_entries.assert_called_once()
        self.mock_fape.process_pdb_entries.assert_called_once()
        self.mock_fape.process_emdb_entries.assert_called_once()
        self.mock_mp.publish.assert_not_called()

    def test_priority_queue_emdb_release_adds_missing_emdb_messages(self) -> None:
        self.mock_fape.get_emdb_entries.return_value = ["EMD-1234"]
        self.mock_fape.get_added_entries.return_value = []
        pvr = PopulateValidateRelease(site_id=SITE_ID, priority=True, emdb_release=True)
        pvr.test()
        self.mock_fape.add_message.assert_called_once_with({"pdbID": "EMD-1234"})
        self.mock_fape.add_entry.assert_called_once_with("EMD-1234")

    def test_priority_queue_emdb_release_skips_already_added(self) -> None:
        self.mock_fape.get_emdb_entries.return_value = ["EMD-1234"]
        self.mock_fape.get_added_entries.return_value = ["EMD-1234"]
        pvr = PopulateValidateRelease(site_id=SITE_ID, priority=True, emdb_release=True)
        pvr.test()
        self.mock_fape.add_message.assert_not_called()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
