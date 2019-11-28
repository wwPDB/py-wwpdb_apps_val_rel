import unittest
import logging
import os
import tempfile
import shutil
import time
from wwpdb.apps.val_rel.mmCIFInfo import mmCIFInfo

class mmCIFInfoTests(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.mmCIF_file = None
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

    def tearDown(self):
        if os.path.exists(self.mmCIF_file):
            os.remove(self.mmCIF_file)
        if os.path.exists(self.test_dir):
            os.remove(self.test_dir)

    def write_mmcif(self):
        mmcif_data = self.base_mmcif_content
        mmcif_data += self.additional_content
        self.mmCIF_file = os.path.join(self.test_dir, 'test.cif')
        with open(self.mmCIF_file, 'w') as outFile:
            outFile.write(mmcif_data)

    def test_get_exptl(self):
        mf = mmCIFInfo(mmCIF_file=self.mmCIF_file)
        exptl = mf.get_exp_methods()
        self.assertTrue(exptl == ['X-RAY DIFFRACTION'])

    def test_get_associated_with_none(self):
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

    def test_get_associated_with_emd_1234(self):
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
        self.assertTrue(emdb_id == 'EMD-1234')

    def test_get_modified_categories(self):
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
        cats = mf.get_latest_modified_categories()
        self.assertTrue(cats == ['citation_author', 'citation'])

if __name__ == "__main__":
    unittest.main()
