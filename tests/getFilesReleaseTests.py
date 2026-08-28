import unittest
from unittest.mock import MagicMock, patch

from wwpdb.apps.val_rel.utils.getFilesRelease import FileContext, FileSource, getFilesRelease

SITE_ID = "WWPDB_DEPLOY_TEST"
MODULE = "wwpdb.apps.val_rel.utils.getFilesRelease"


class GetFilesReleaseTests(unittest.TestCase):
    """Unit tests for getFilesRelease.

    ValConfig (site config) and every protocol backend (OneDep, FTP, HTTP --
    the HTTP ones being what would otherwise reach ValConfig/EmailHandler
    again one level down) are all mocked, so these tests only exercise
    getFilesRelease's own routing/fallback logic and never touch real site
    config, the network, or any wwpdb.apps.validation code.
    """

    def setUp(self) -> None:
        site_id_patcher = patch(f"{MODULE}.getSiteId")
        self.mock_get_site_id = site_id_patcher.start()
        self.addCleanup(site_id_patcher.stop)
        self.mock_get_site_id.return_value = SITE_ID

        vc_patcher = patch(f"{MODULE}.ValConfig")
        mock_vc_class = vc_patcher.start()
        self.addCleanup(vc_patcher.stop)
        self.mock_vc = MagicMock()
        self.mock_vc.val_rel_protocol = "http"
        mock_vc_class.return_value = self.mock_vc

        onedep_patcher = patch(f"{MODULE}.getFilesReleaseOneDep")
        self.mock_onedep_class = onedep_patcher.start()
        self.addCleanup(onedep_patcher.stop)
        self.mock_onedep = MagicMock()
        self.mock_onedep.get_model.return_value = (None, False)
        self.mock_onedep.get_sf.return_value = (None, False)
        self.mock_onedep.get_cs.return_value = (None, False)
        self.mock_onedep.get_nmr_data.return_value = (None, False)
        self.mock_onedep.get_emdb_xml.return_value = (None, False)
        self.mock_onedep.get_emdb_volume.return_value = (None, False)
        self.mock_onedep.get_emdb_fsc.return_value = (None, False)
        self.mock_onedep_class.return_value = self.mock_onedep

        self.mock_http_pdb = MagicMock()
        self.mock_http_emdb = MagicMock()
        self.mock_ftp_pdb = MagicMock()
        self.mock_ftp_emdb = MagicMock()

        http_pdb_patcher = patch(f"{MODULE}.getFilesReleaseHttpPDB")
        self.mock_http_pdb_class = http_pdb_patcher.start()
        self.addCleanup(http_pdb_patcher.stop)
        self.mock_http_pdb_class.return_value = self.mock_http_pdb

        http_emdb_patcher = patch(f"{MODULE}.getFilesReleaseHttpEMDB")
        self.mock_http_emdb_class = http_emdb_patcher.start()
        self.addCleanup(http_emdb_patcher.stop)
        self.mock_http_emdb_class.return_value = self.mock_http_emdb

        ftp_pdb_patcher = patch(f"{MODULE}.getFilesReleaseFtpPDB")
        self.mock_ftp_pdb_class = ftp_pdb_patcher.start()
        self.addCleanup(ftp_pdb_patcher.stop)
        self.mock_ftp_pdb_class.return_value = self.mock_ftp_pdb

        ftp_emdb_patcher = patch(f"{MODULE}.getFilesReleaseFtpEMDB")
        self.mock_ftp_emdb_class = ftp_emdb_patcher.start()
        self.addCleanup(ftp_emdb_patcher.stop)
        self.mock_ftp_emdb_class.return_value = self.mock_ftp_emdb

    # -- constructor ---------------------------------------------------------

    def test_site_id_defaults_via_get_site_id(self) -> None:
        getFilesRelease(pdb_id="1abc", siteID=None)
        self.mock_get_site_id.assert_called_once()

    def test_site_id_explicit_skips_get_site_id(self) -> None:
        getFilesRelease(pdb_id="1abc", siteID=SITE_ID)
        self.mock_get_site_id.assert_not_called()

    def test_http_protocol_uses_http_backends(self) -> None:
        self.mock_vc.val_rel_protocol = "http"
        getFilesRelease(pdb_id="1abc", emdb_id="EMD-1234", siteID=SITE_ID, cache="/cache")
        self.mock_http_pdb_class.assert_called_once_with(site_id=SITE_ID, pdbid="1abc", cache="/cache")
        self.mock_http_emdb_class.assert_called_once_with(site_id=SITE_ID, emdbid="EMD-1234", cache="/cache")
        self.mock_ftp_pdb_class.assert_not_called()
        self.mock_ftp_emdb_class.assert_not_called()

    def test_https_protocol_uses_http_backends(self) -> None:
        self.mock_vc.val_rel_protocol = "https"
        getFilesRelease(pdb_id="1abc", siteID=SITE_ID)
        self.mock_http_pdb_class.assert_called_once()
        self.mock_ftp_pdb_class.assert_not_called()

    def test_ftp_protocol_uses_ftp_backends(self) -> None:
        self.mock_vc.val_rel_protocol = "ftp"
        getFilesRelease(pdb_id="1abc", emdb_id="EMD-1234", siteID=SITE_ID, cache="/cache")
        self.mock_ftp_pdb_class.assert_called_once_with(site_id=SITE_ID, pdbid="1abc", cache="/cache")
        self.mock_ftp_emdb_class.assert_called_once_with(site_id=SITE_ID, emdbid="EMD-1234", cache="/cache")
        self.mock_http_pdb_class.assert_not_called()
        self.mock_http_emdb_class.assert_not_called()

    def test_constructor_builds_onedep_backend(self) -> None:
        getFilesRelease(pdb_id="1abc", emdb_id="EMD-1234", siteID=SITE_ID)
        self.mock_onedep_class.assert_called_once_with(siteID=SITE_ID, pdb_id="1abc", emdb_id="EMD-1234")

    # -- close_connections / remove_local_temp_files --------------------------

    def test_close_connections_closes_both_backends(self) -> None:
        gfr = getFilesRelease(pdb_id="1abc", emdb_id="EMD-1234", siteID=SITE_ID)
        gfr.close_connections()
        self.mock_http_pdb.close_connection.assert_called_once()
        self.mock_http_emdb.close_connection.assert_called_once()

    def test_remove_local_temp_files_removes_both_backends(self) -> None:
        gfr = getFilesRelease(pdb_id="1abc", emdb_id="EMD-1234", siteID=SITE_ID)
        gfr.remove_local_temp_files()
        self.mock_http_pdb.remove_local_temp_files.assert_called_once()
        self.mock_http_emdb.remove_local_temp_files.assert_called_once()

    # -- set_pdb_id / set_emdb_id ----------------------------------------------

    def test_set_pdb_id_same_id_is_noop(self) -> None:
        gfr = getFilesRelease(pdb_id="1abc", siteID=SITE_ID)
        self.mock_onedep_class.reset_mock()
        self.mock_http_pdb_class.reset_mock()
        gfr.set_pdb_id("1abc")
        self.mock_onedep_class.assert_not_called()
        self.mock_http_pdb_class.assert_not_called()
        self.mock_http_pdb.close_connection.assert_not_called()

    def test_set_pdb_id_new_id_rebuilds_backends(self) -> None:
        gfr = getFilesRelease(pdb_id="1abc", emdb_id="EMD-1234", siteID=SITE_ID, cache="/cache")
        self.mock_onedep_class.reset_mock()
        self.mock_http_pdb_class.reset_mock()
        gfr.set_pdb_id("2xyz")
        self.mock_onedep_class.assert_called_once_with(siteID=SITE_ID, pdb_id="2xyz", emdb_id="EMD-1234")
        self.mock_http_pdb.close_connection.assert_called_once()
        self.mock_http_pdb_class.assert_called_once_with(site_id=SITE_ID, pdbid="2xyz", cache="/cache")

    def test_set_emdb_id_same_id_is_noop(self) -> None:
        gfr = getFilesRelease(emdb_id="EMD-1234", siteID=SITE_ID)
        self.mock_onedep_class.reset_mock()
        self.mock_http_emdb_class.reset_mock()
        gfr.set_emdb_id("EMD-1234")
        self.mock_onedep_class.assert_not_called()
        self.mock_http_emdb_class.assert_not_called()
        self.mock_http_emdb.close_connection.assert_not_called()

    def test_set_emdb_id_new_id_rebuilds_backends(self) -> None:
        gfr = getFilesRelease(pdb_id="1abc", emdb_id="EMD-1234", siteID=SITE_ID, cache="/cache")
        self.mock_onedep_class.reset_mock()
        self.mock_http_emdb_class.reset_mock()
        gfr.set_emdb_id("EMD-5678")
        self.mock_onedep_class.assert_called_once_with(siteID=SITE_ID, pdb_id="1abc", emdb_id="EMD-5678")
        self.mock_http_emdb.close_connection.assert_called_once()
        self.mock_http_emdb_class.assert_called_once_with(site_id=SITE_ID, emdbid="EMD-5678", cache="/cache")

    def test_set_cache_used_by_subsequent_set_pdb_id(self) -> None:
        gfr = getFilesRelease(pdb_id="1abc", siteID=SITE_ID, cache="/old")
        gfr.set_cache("/new")
        gfr.set_pdb_id("2xyz")
        self.mock_http_pdb_class.assert_called_with(site_id=SITE_ID, pdbid="2xyz", cache="/new")

    # -- get_model / get_sf / get_cs / get_nmr_data (onedep-then-remote fallback) --

    def test_get_model_uses_onedep_when_present(self) -> None:
        self.mock_onedep.get_model.return_value = ("onedep.cif", True)
        gfr = getFilesRelease(pdb_id="1abc", siteID=SITE_ID)
        model = gfr.get_model()
        self.assertEqual(model.path, "onedep.cif")
        self.assertEqual(model.context, FileContext.MODEL)
        self.assertEqual(model.loc, FileSource.ONEDEP_REL)
        self.mock_http_pdb.get_model.assert_not_called()

    def test_get_model_uses_onedep_prev(self) -> None:
        self.mock_onedep.get_model.return_value = ("onedep.cif", False)
        gfr = getFilesRelease(pdb_id="1abc", siteID=SITE_ID)
        model = gfr.get_model()
        self.assertEqual(model.path, "onedep.cif")
        self.assertEqual(model.context, FileContext.MODEL)
        self.assertEqual(model.loc, FileSource.ONEDEP_PREV)
        self.mock_http_pdb.get_model.assert_not_called()

    def test_get_model_falls_back_to_remote(self) -> None:
        self.mock_onedep.get_model.return_value = (None, False)
        self.mock_http_pdb.get_model.return_value = "remote.cif"
        gfr = getFilesRelease(pdb_id="1abc", siteID=SITE_ID)
        model = gfr.get_model()
        self.assertEqual(model.path, "remote.cif")
        self.assertEqual(model.context, FileContext.MODEL)
        self.assertEqual(model.loc, FileSource.REMOTE)

    def test_get_sf_uses_onedep_and_sets_current_flag(self) -> None:
        self.mock_onedep.get_sf.return_value = ("onedep-sf.cif", True)
        gfr = getFilesRelease(pdb_id="1abc", siteID=SITE_ID)
        sf = gfr.get_sf()
        self.assertEqual(sf.path, "onedep-sf.cif")
        self.assertEqual(sf.context, FileContext.SF)
        self.assertEqual(sf.loc, FileSource.ONEDEP_REL)
        self.assertTrue(gfr.is_sf_current())
        self.mock_http_pdb.get_sf.assert_not_called()

    def test_get_sf_uses_onedep_prev(self) -> None:
        self.mock_onedep.get_sf.return_value = ("onedep-sf.cif", False)
        gfr = getFilesRelease(pdb_id="1abc", siteID=SITE_ID)
        sf = gfr.get_sf()
        self.assertEqual(sf.path, "onedep-sf.cif")
        self.assertEqual(sf.context, FileContext.SF)
        self.assertEqual(sf.loc, FileSource.ONEDEP_PREV)
        self.assertFalse(gfr.is_sf_current())
        self.mock_http_pdb.get_sf.assert_not_called()

    def test_get_sf_falls_back_and_current_false(self) -> None:
        self.mock_onedep.get_sf.return_value = (None, False)
        self.mock_http_pdb.get_sf.return_value = "remote-sf.cif"
        gfr = getFilesRelease(pdb_id="1abc", siteID=SITE_ID)
        sf = gfr.get_sf()
        self.assertEqual(sf.path, "remote-sf.cif")
        self.assertEqual(sf.context, FileContext.SF)
        self.assertEqual(sf.loc, FileSource.REMOTE)
        self.assertFalse(gfr.is_sf_current())

    def test_get_cs_uses_onedep_and_sets_current_flag(self) -> None:
        self.mock_onedep.get_cs.return_value = ("onedep_cs.str", True)
        gfr = getFilesRelease(pdb_id="1abc", siteID=SITE_ID)
        cs = gfr.get_cs()
        self.assertEqual(cs.path, "onedep_cs.str")
        self.assertEqual(cs.context, FileContext.CS)
        self.assertEqual(cs.loc, FileSource.ONEDEP_REL)
        self.assertTrue(gfr.is_cs_current())

    def test_get_cs_uses_onedep_prev(self) -> None:
        self.mock_onedep.get_cs.return_value = ("onedep_cs.str", False)
        gfr = getFilesRelease(pdb_id="1abc", siteID=SITE_ID)
        cs = gfr.get_cs()
        self.assertEqual(cs.path, "onedep_cs.str")
        self.assertEqual(cs.context, FileContext.CS)
        self.assertEqual(cs.loc, FileSource.ONEDEP_PREV)
        self.assertFalse(gfr.is_cs_current())

    def test_get_cs_falls_back_to_remote(self) -> None:
        self.mock_onedep.get_cs.return_value = (None, False)
        self.mock_http_pdb.get_cs.return_value = "remote_cs.str"
        gfr = getFilesRelease(pdb_id="1abc", siteID=SITE_ID)
        cs = gfr.get_cs()
        self.assertEqual(cs.path, "remote_cs.str")
        self.assertEqual(cs.context, FileContext.CS)
        self.assertEqual(cs.loc, FileSource.REMOTE)

    def test_get_nmr_data_uses_onedep(self) -> None:
        self.mock_onedep.get_nmr_data.return_value = ("onedep_nmr-data.str", True)
        gfr = getFilesRelease(pdb_id="1abc", siteID=SITE_ID)
        nmr = gfr.get_nmr_data()
        self.assertEqual(nmr.path, "onedep_nmr-data.str")
        self.assertEqual(nmr.context, FileContext.NMR_DATA)
        self.assertEqual(nmr.loc, FileSource.ONEDEP_REL)

    def test_get_nmr_data_uses_onedep_prev(self) -> None:
        self.mock_onedep.get_nmr_data.return_value = ("onedep_nmr-data.str", False)
        gfr = getFilesRelease(pdb_id="1abc", siteID=SITE_ID)
        nmr = gfr.get_nmr_data()
        self.assertEqual(nmr.path, "onedep_nmr-data.str")
        self.assertEqual(nmr.context, FileContext.NMR_DATA)
        self.assertEqual(nmr.loc, FileSource.ONEDEP_PREV)

    def test_get_nmr_data_falls_back_to_remote(self) -> None:
        self.mock_onedep.get_nmr_data.return_value = (None, False)
        self.mock_http_pdb.get_nmr_data.return_value = "remote_nmr-data.str"
        gfr = getFilesRelease(pdb_id="1abc", siteID=SITE_ID)
        nmr = gfr.get_nmr_data()
        self.assertEqual(nmr.path, "remote_nmr-data.str")
        self.assertEqual(nmr.context, FileContext.NMR_DATA)
        self.assertEqual(nmr.loc, FileSource.REMOTE)

    # -- EMDB fallbacks --------------------------------------------------------

    def test_get_emdb_xml_uses_onedep_and_sets_current_flag(self) -> None:
        self.mock_onedep.get_emdb_xml.return_value = ("onedep.xml", True)
        gfr = getFilesRelease(emdb_id="EMD-1234", siteID=SITE_ID)
        xml = gfr.get_emdb_xml()
        self.assertEqual(xml.path, "onedep.xml")
        self.assertEqual(xml.context, FileContext.EMDB_XML)
        self.assertEqual(xml.loc, FileSource.ONEDEP_REL)
        self.assertTrue(gfr.is_em_xml_current())
        self.mock_http_emdb.get_emdb_xml.assert_not_called()

    def test_get_emdb_xml_uses_onedep_prev(self) -> None:
        self.mock_onedep.get_emdb_xml.return_value = ("onedep.xml", False)
        gfr = getFilesRelease(emdb_id="EMD-1234", siteID=SITE_ID)
        xml = gfr.get_emdb_xml()
        self.assertEqual(xml.path, "onedep.xml")
        self.assertEqual(xml.context, FileContext.EMDB_XML)
        self.assertEqual(xml.loc, FileSource.ONEDEP_PREV)
        self.assertFalse(gfr.is_em_xml_current())
        self.mock_http_emdb.get_emdb_xml.assert_not_called()

    def test_get_emdb_xml_falls_back_to_remote(self) -> None:
        self.mock_onedep.get_emdb_xml.return_value = (None, False)
        self.mock_http_emdb.get_emdb_xml.return_value = "remote.xml"
        gfr = getFilesRelease(emdb_id="EMD-1234", siteID=SITE_ID)
        xml = gfr.get_emdb_xml()
        self.assertEqual(xml.path, "remote.xml")
        self.assertEqual(xml.context, FileContext.EMDB_XML)
        self.assertEqual(xml.loc, FileSource.REMOTE)
        self.assertFalse(gfr.is_em_xml_current())

    def test_get_emdb_volume_uses_onedep(self) -> None:
        self.mock_onedep.get_emdb_volume.return_value = ("onedep.map", True)
        gfr = getFilesRelease(emdb_id="EMD-1234", siteID=SITE_ID)
        vol = gfr.get_emdb_volume()
        self.assertEqual(vol.path, "onedep.map")
        self.assertEqual(vol.context, FileContext.EMDB_VOL)
        self.assertEqual(vol.loc, FileSource.ONEDEP_REL)
        self.mock_http_emdb.get_emdb_volume.assert_not_called()

    def test_get_emdb_volume_uses_onedep_prev(self) -> None:
        self.mock_onedep.get_emdb_volume.return_value = ("onedep.map", False)
        gfr = getFilesRelease(emdb_id="EMD-1234", siteID=SITE_ID)
        vol = gfr.get_emdb_volume()
        self.assertEqual(vol.path, "onedep.map")
        self.assertEqual(vol.context, FileContext.EMDB_VOL)
        self.assertEqual(vol.loc, FileSource.ONEDEP_PREV)
        self.mock_http_emdb.get_emdb_volume.assert_not_called()

    def test_get_emdb_volume_falls_back_to_remote(self) -> None:
        self.mock_onedep.get_emdb_volume.return_value = (None, False)
        self.mock_http_emdb.get_emdb_volume.return_value = "remote.map"
        gfr = getFilesRelease(emdb_id="EMD-1234", siteID=SITE_ID)
        vol = gfr.get_emdb_volume()
        self.assertEqual(vol.path, "remote.map")
        self.assertEqual(vol.context, FileContext.EMDB_VOL)
        self.assertEqual(vol.loc, FileSource.REMOTE)

    def test_get_emdb_fsc_uses_onedep(self) -> None:
        self.mock_onedep.get_emdb_fsc.return_value = ("onedep_fsc.xml", True)
        gfr = getFilesRelease(emdb_id="EMD-1234", siteID=SITE_ID)
        fsc = gfr.get_emdb_fsc()
        self.assertEqual(fsc.path, "onedep_fsc.xml")
        self.assertEqual(fsc.context, FileContext.EMDB_FSC)
        self.assertEqual(fsc.loc, FileSource.ONEDEP_REL)
        self.mock_http_emdb.get_emdb_fsc.assert_not_called()

    def test_get_emdb_fsc_uses_onedep_prev(self) -> None:
        self.mock_onedep.get_emdb_fsc.return_value = ("onedep_fsc.xml", False)
        gfr = getFilesRelease(emdb_id="EMD-1234", siteID=SITE_ID)
        fsc = gfr.get_emdb_fsc()
        self.assertEqual(fsc.path, "onedep_fsc.xml")
        self.assertEqual(fsc.context, FileContext.EMDB_FSC)
        self.assertEqual(fsc.loc, FileSource.ONEDEP_PREV)
        self.mock_http_emdb.get_emdb_fsc.assert_not_called()

    def test_get_emdb_fsc_falls_back_to_remote(self) -> None:
        self.mock_onedep.get_emdb_fsc.return_value = (None, False)
        self.mock_http_emdb.get_emdb_fsc.return_value = "remote_fsc.xml"
        gfr = getFilesRelease(emdb_id="EMD-1234", siteID=SITE_ID)
        fsc = gfr.get_emdb_fsc()
        self.assertEqual(fsc.path, "remote_fsc.xml")
        self.assertEqual(fsc.context, FileContext.EMDB_FSC)
        self.assertEqual(fsc.loc, FileSource.REMOTE)

    def test_get_emdb_metadata_uses_onedep(self) -> None:
        self.mock_onedep.get_emdb_metadata.return_value = ("onedep_metadata.cif.gz", True)
        gfr = getFilesRelease(emdb_id="EMD-1234", siteID=SITE_ID)
        meta = gfr.get_emdb_metadata()
        self.assertEqual(meta.path, "onedep_metadata.cif.gz")
        self.assertEqual(meta.context, FileContext.EMDB_METADATA)
        self.assertEqual(meta.loc, FileSource.ONEDEP_REL)
        self.mock_http_emdb.get_emdb_metadata.assert_not_called()

    def test_get_emdb_metadata_uses_onedep_prev(self) -> None:
        self.mock_onedep.get_emdb_metadata.return_value = ("onedep_metadata.cif.gz", False)
        gfr = getFilesRelease(emdb_id="EMD-1234", siteID=SITE_ID)
        meta = gfr.get_emdb_metadata()
        self.assertEqual(meta.path, "onedep_metadata.cif.gz")
        self.assertEqual(meta.context, FileContext.EMDB_METADATA)
        self.assertEqual(meta.loc, FileSource.ONEDEP_PREV)
        self.mock_http_emdb.get_emdb_metadata.assert_not_called()

    def test_get_emdb_metadata_falls_back_to_remote(self) -> None:
        self.mock_onedep.get_emdb_metadata.return_value = (None, False)
        self.mock_http_emdb.get_emdb_metadata.return_value = "remote_metadata.cif.gz"
        gfr = getFilesRelease(emdb_id="EMD-1234", siteID=SITE_ID)
        meta = gfr.get_emdb_metadata()
        self.assertEqual(meta.path, "remote_metadata.cif.gz")
        self.assertEqual(meta.context, FileContext.EMDB_METADATA)
        self.assertEqual(meta.loc, FileSource.REMOTE)

    # -- current flags default before any get_* call --------------------------

    def test_current_flags_default_false(self) -> None:
        gfr = getFilesRelease(pdb_id="1abc", emdb_id="EMD-1234", siteID=SITE_ID)
        self.assertFalse(gfr.is_sf_current())
        self.assertFalse(gfr.is_cs_current())
        self.assertFalse(gfr.is_em_xml_current())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
