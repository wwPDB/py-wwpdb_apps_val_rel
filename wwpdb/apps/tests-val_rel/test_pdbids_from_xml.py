import unittest
import logging
import os
import tempfile
import shutil
import time
from wwpdb.apps.val_rel.utils.XmlInfo import XmlInfo

class XmlInfoTests(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.test_dir, 'test.xml')


    def tearDown(self):
        if self.test_dir:
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_get_pdb_from_xml(self):
        test_xml_data = """<?xml version="1.0" encoding="UTF-8"?>
<emd xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="https://github.com/emdb-empiar/emdb-schemas/blob/master/v3/v3_0_1_5/emdb.xs
d" emdb_id="EMD-3863" version="3.0.1.5">
     <crossreferences>
     <pdb_list>
            <pdb_reference>
                <pdb_id>5oyp</pdb_id>
                <relationship>
                    <in_frame>FULLOVERLAP</in_frame>
                </relationship>
            </pdb_reference>
        </pdb_list>
    </crossreferences>
    </emd>
       """
        with open(self.test_file, 'w') as outFile:
            outFile.write(test_xml_data)

        ret = XmlInfo(xml_file=self.test_file).get_pdbids_from_xml()
        self.assertTrue(ret == ['5oyp'])

    
    def test_get_pdbs_from_xml(self):
        test_xml_data = """<?xml version="1.0" encoding="UTF-8"?>
<emd xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="https://github.com/emdb-empiar/emdb-schemas/blob/master/v3/v3_0_1_5/emdb.xs
d" emdb_id="EMD-3863" version="3.0.1.5">
     <crossreferences>
     <pdb_list>
            <pdb_reference>
                <pdb_id>5oyp</pdb_id>
                <relationship>
                    <in_frame>FULLOVERLAP</in_frame>
                </relationship>
            </pdb_reference>
            <pdb_reference>
                <pdb_id>5oyt</pdb_id>
                <relationship>
                    <in_frame>FULLOVERLAP</in_frame>
                </relationship>
            </pdb_reference>
        </pdb_list>
    </crossreferences>
    </emd>
       """
        
        
        with open(self.test_file, 'w') as outFile:
            outFile.write(test_xml_data)

        ret = XmlInfo(xml_file=self.test_file).get_pdbids_from_xml()
        self.assertTrue(ret == ['5oyp', '5oyt'])


    def test_get_pdbs_not_starting_from_xml(self):
        test_xml_data = """<?xml version="1.0" encoding="UTF-8"?>
<emd xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="https://github.com/emdb-empiar/emdb-schemas/blob/master/v3/v3_0_1_5/emdb.xs
d" emdb_id="EMD-3863" version="3.0.1.5">
     <crossreferences>
     <pdb_list>
            <pdb_reference>
                <pdb_id>5oyp</pdb_id>
                <relationship>
                    <in_frame>FULLOVERLAP</in_frame>
                </relationship>
            </pdb_reference>
            <pdb_reference>
                <pdb_id>5oyt</pdb_id>
                <relationship>
                    <in_frame>FULLOVERLAP</in_frame>
                </relationship>
            </pdb_reference>
        </pdb_list>
        <startup_model type_of_model="PDB ENTRY">
                <pdb_model>
                    <pdb_id>5CDC</pdb_id>
                </pdb_model>
                <details>Deposited IAPV model low pass filtered to resolution 40 A.</details>
        </startup_model>

    </crossreferences>
    </emd>
       """
        with open(self.test_file, 'w') as outFile:
            outFile.write(test_xml_data)

        ret = XmlInfo(xml_file=self.test_file).get_pdbids_from_xml()
        self.assertTrue(ret == ['5oyp', '5oyt'])



if __name__ == "__main__":
    unittest.main()
