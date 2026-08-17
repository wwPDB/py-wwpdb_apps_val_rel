import datetime
import os
import shutil
import tempfile
import unittest

from wwpdb.apps.val_rel.utils.mmCIFInfo import _parsedate, is_simple_modification, mmCIFInfo


class mmCIFInfoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()
        self.mmCIF_file = ""  # Filename
        self.additional_content = ""
        self.base_mmcif_content = """
data_2GC2
#
_entry.id   2GC2
#
_audit_conform.dict_name       mmcif_pdbx.dic
_audit_conform.dict_version    5.281
_audit_conform.dict_location   http://mmcif.pdb.org/dictionaries/ascii/mmcif_pdbx.dic
#
loop_
_database_2.database_id
_database_2.database_code
PDB   2GC2
RCSB  RCSB036939
WWPDB D_1000036939
#
_exptl.entry_id          2GC2
_exptl.crystals_number   1
_exptl.method            'X-RAY DIFFRACTION'
#
"""

    def tearDown(self) -> None:
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def write_mmcif(self) -> None:
        mmcif_data = self.base_mmcif_content
        mmcif_data += self.additional_content
        self.mmCIF_file = os.path.join(self.test_dir, "test.cif")
        with open(self.mmCIF_file, "w") as outFile:
            outFile.write(mmcif_data)

    def test_get_exptl(self) -> None:
        self.write_mmcif()
        mf = mmCIFInfo(mmCIF_file=self.mmCIF_file)
        exptl = mf.get_exp_methods()
        self.assertTrue(exptl == ["X-RAY DIFFRACTION"])

    def test_get_associated_with_none(self) -> None:
        self.additional_content = """
loop_
_pdbx_database_related.db_name
_pdbx_database_related.db_id
_pdbx_database_related.details
_pdbx_database_related.content_type
PDB 1X7N ? unspecified
#
"""
        self.write_mmcif()
        mf = mmCIFInfo(mmCIF_file=self.mmCIF_file)
        emdb_id = mf.get_associated_emdb()
        self.assertTrue(emdb_id is None)

    def test_get_associated_with_emd_1234(self) -> None:
        self.additional_content = """
loop_
_pdbx_database_related.db_name
_pdbx_database_related.db_id
_pdbx_database_related.details
_pdbx_database_related.content_type
EMDB EMD-1234 ? 'associated EM volume'
#
"""
        self.write_mmcif()
        mf = mmCIFInfo(mmCIF_file=self.mmCIF_file)
        emdb_id = mf.get_associated_emdb()
        self.assertTrue(emdb_id == "EMD-1234")

    def test_get_modified_categories(self) -> None:
        self.additional_content = """
loop_
    _pdbx_audit_revision_history.ordinal
    _pdbx_audit_revision_history.data_content_type
    _pdbx_audit_revision_history.major_revision
    _pdbx_audit_revision_history.minor_revision
    _pdbx_audit_revision_history.revision_date
    1 'Structure model' 1 0 2017-03-01
    2 'Structure model' 1 1 2017-03-08
#
loop_
    _pdbx_audit_revision_category.ordinal
    _pdbx_audit_revision_category.revision_ordinal
    _pdbx_audit_revision_category.data_content_type
    _pdbx_audit_revision_category.category
    1 1 'Structure Model' 'audit_author'
    2 1 'Structure Model' 'citation'
    3 2 'Structure Model' 'citation_author'
    4 2 'Structure Model' 'citation'
#
"""
        self.write_mmcif()
        mf = mmCIFInfo(mmCIF_file=self.mmCIF_file)
        cats, ordinal = mf.get_latest_modified_categories()
        self.assertTrue(cats == ["citation_author", "citation"])
        self.assertEqual(ordinal, "2")

    def test_get_exptl_missing_category_returns_empty(self) -> None:
        self.write_mmcif()
        mf = mmCIFInfo(mmCIF_file=self.mmCIF_file)
        emdb_id = mf.get_associated_emdb()
        self.assertTrue(emdb_id is None)

    def test_get_latest_modified_categories_missing_returns_empty(self) -> None:
        self.write_mmcif()
        mf = mmCIFInfo(mmCIF_file=self.mmCIF_file)
        cats, ordinal = mf.get_latest_modified_categories()
        self.assertTrue(cats == [])
        self.assertTrue(ordinal is None)

    def test_parse_mmcif_missing_file_returns_none(self) -> None:
        mf = mmCIFInfo(mmCIF_file=os.path.join(self.test_dir, "does_not_exist.cif"))
        with self.assertLogs("wwpdb.apps.val_rel.utils.mmCIFInfo", level="ERROR") as log, self.assertLogs(
            "mmcif.io.IoAdapterBase", level="ERROR"
        ) as log2:
            ret = mf.parse_mmcif()
            self.assertIsNone(ret)
            self.assertIn("failed to parse", log.output[0])
            self.assertIn("Missing file", log2.output[0])

    def test_get_modified_items(self) -> None:
        self.additional_content = """
loop_
    _pdbx_audit_revision_item.ordinal
    _pdbx_audit_revision_item.revision_ordinal
    _pdbx_audit_revision_item.data_content_type
    _pdbx_audit_revision_item.item
    1 2 'Structure model' '_database_2.pdbx_DOI'
    2 2 'Structure model' '_database_2.database_id'
#
"""
        self.write_mmcif()
        mf = mmCIFInfo(mmCIF_file=self.mmCIF_file)
        items = mf.get_modified_items("2")
        self.assertEqual(items, {"database_2": ["pdbx_DOI", "database_id"]})

    def test_is_simple_modification_true_for_skip_list_category(self) -> None:
        self.additional_content = """
loop_
    _pdbx_audit_revision_history.ordinal
    _pdbx_audit_revision_history.data_content_type
    _pdbx_audit_revision_history.major_revision
    _pdbx_audit_revision_history.minor_revision
    _pdbx_audit_revision_history.revision_date
    1 'Structure model' 1 0 2017-03-01
#
loop_
    _pdbx_audit_revision_category.ordinal
    _pdbx_audit_revision_category.revision_ordinal
    _pdbx_audit_revision_category.data_content_type
    _pdbx_audit_revision_category.category
    1 1 'Structure Model' 'citation'
#
"""
        self.write_mmcif()
        self.assertTrue(is_simple_modification(self.mmCIF_file))

    def test_is_simple_modification_false_for_non_skip_list_category(self) -> None:
        self.additional_content = """
loop_
    _pdbx_audit_revision_history.ordinal
    _pdbx_audit_revision_history.data_content_type
    _pdbx_audit_revision_history.major_revision
    _pdbx_audit_revision_history.minor_revision
    _pdbx_audit_revision_history.revision_date
    1 'Structure model' 1 0 2017-03-01
#
loop_
    _pdbx_audit_revision_category.ordinal
    _pdbx_audit_revision_category.revision_ordinal
    _pdbx_audit_revision_category.data_content_type
    _pdbx_audit_revision_category.category
    1 1 'Structure Model' 'entity'
#
"""
        self.write_mmcif()
        self.assertFalse(is_simple_modification(self.mmCIF_file))

    def test_is_simple_modification_false_with_no_audit_history(self) -> None:
        self.write_mmcif()
        self.assertFalse(is_simple_modification(self.mmCIF_file))

    def test_is_simple_modification_true_for_allowed_database_2_attrs(self) -> None:
        self.additional_content = """
loop_
    _pdbx_audit_revision_history.ordinal
    _pdbx_audit_revision_history.data_content_type
    _pdbx_audit_revision_history.major_revision
    _pdbx_audit_revision_history.minor_revision
    _pdbx_audit_revision_history.revision_date
    1 'Structure model' 1 0 2017-03-01
#
loop_
    _pdbx_audit_revision_category.ordinal
    _pdbx_audit_revision_category.revision_ordinal
    _pdbx_audit_revision_category.data_content_type
    _pdbx_audit_revision_category.category
    1 1 'Structure Model' 'database_2'
#
loop_
    _pdbx_audit_revision_item.ordinal
    _pdbx_audit_revision_item.revision_ordinal
    _pdbx_audit_revision_item.data_content_type
    _pdbx_audit_revision_item.item
    1 1 'Structure model' '_database_2.pdbx_DOI'
#
"""
        self.write_mmcif()
        self.assertTrue(is_simple_modification(self.mmCIF_file))

    def test_is_simple_modification_false_for_disallowed_database_2_attrs(self) -> None:
        self.additional_content = """
loop_
    _pdbx_audit_revision_history.ordinal
    _pdbx_audit_revision_history.data_content_type
    _pdbx_audit_revision_history.major_revision
    _pdbx_audit_revision_history.minor_revision
    _pdbx_audit_revision_history.revision_date
    1 'Structure model' 1 0 2017-03-01
#
loop_
    _pdbx_audit_revision_category.ordinal
    _pdbx_audit_revision_category.revision_ordinal
    _pdbx_audit_revision_category.data_content_type
    _pdbx_audit_revision_category.category
    1 1 'Structure Model' 'database_2'
#
loop_
    _pdbx_audit_revision_item.ordinal
    _pdbx_audit_revision_item.revision_ordinal
    _pdbx_audit_revision_item.data_content_type
    _pdbx_audit_revision_item.item
    1 1 'Structure model' '_database_2.database_id'
#
"""
        self.write_mmcif()
        self.assertFalse(is_simple_modification(self.mmCIF_file))

    def test_is_simple_modification_true_for_emdb_revision_category(self) -> None:
        self.additional_content = """
loop_
    _pdbx_audit_revision_history.ordinal
    _pdbx_audit_revision_history.data_content_type
    _pdbx_audit_revision_history.major_revision
    _pdbx_audit_revision_history.minor_revision
    _pdbx_audit_revision_history.revision_date
    1 'Structure model' 1 0 2017-03-01
    2 'EM metadata'     1 0 2017-03-08
#
loop_
    _pdbx_audit_revision_category.ordinal
    _pdbx_audit_revision_category.revision_ordinal
    _pdbx_audit_revision_category.data_content_type
    _pdbx_audit_revision_category.category
    1 1 'Structure Model' 'entity'
#
"""
        self.write_mmcif()
        self.assertTrue(is_simple_modification(self.mmCIF_file))

    def test_is_simple_modification_true_for_pdb_and_emdb_revisioncategory(self) -> None:
        self.additional_content = """
loop_
    _pdbx_audit_revision_history.ordinal
    _pdbx_audit_revision_history.data_content_type
    _pdbx_audit_revision_history.major_revision
    _pdbx_audit_revision_history.minor_revision
    _pdbx_audit_revision_history.revision_date
    1 'Structure model' 1 0 2017-03-01
    2 'EM metadata'     1 0 2017-03-01
#
loop_
    _pdbx_audit_revision_category.ordinal
    _pdbx_audit_revision_category.revision_ordinal
    _pdbx_audit_revision_category.data_content_type
    _pdbx_audit_revision_category.category
    1 1 'Structure Model' 'citation'
#
"""
        self.write_mmcif()
        self.assertTrue(is_simple_modification(self.mmCIF_file))


    def test_parsedate_valid_date(self) -> None:
        date_str = "2023-06-15"
        parsed_date = _parsedate(date_str)
        self.assertEqual(parsed_date, datetime.date(2023, 6, 15))
        parsed_date = _parsedate(".")
        self.assertIsNone(parsed_date)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
