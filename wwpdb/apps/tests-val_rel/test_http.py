import unittest
import os
import tempfile
import shutil
import gzip
import logging

from wwpdb.apps.val_rel.utils.http_protocol.getFilesReleaseHTTP_EMDB import getFilesReleaseHttpEMDB
from wwpdb.apps.val_rel.utils.http_protocol.getFilesReleaseHTTP_PDB import getFilesReleaseHttpPDB
from wwpdb.apps.val_rel.utils.http_protocol.getRemoteFilesHTTP import GetRemoteFilesHttp
from wwpdb.apps.val_rel.utils.XmlInfo import XmlInfo
from wwpdb.apps.val_rel.config.ValConfig import ValConfig

logging.basicConfig(level=logging.INFO)


class TestHTTP(unittest.TestCase):


    def setUp(self):
        logging.info("running setup")
        pdb_testpath = "https://files.wwpdb.org/pub/pdb/data/structures/all/mmCIF"
        emdb_testpath = "https://files.wwpdb.org/pub/emdb/structures"
        zipfiles = ["8glv.cif.gz", "7n82.cif.gz"]
        non_existent_files = ["1abc.cif.gz"]
        xmlfile = os.path.join(emdb_testpath, "EMD-5030", "header", "emd-5030-v30.xml")
        self.large_test_file = "https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-59/fasta/triticum_aestivum/dna/Triticum_aestivum.IWGSC.dna.toplevel.fa.gz"
        self.zipfiles = [os.path.join(pdb_testpath, file) for file in zipfiles]
        self.non_existent_files = [os.path.join(pdb_testpath, file) for file in non_existent_files]
        self.temp_dir = tempfile.mkdtemp()
        self.xmlfiles = [xmlfile]
        self.xray_id = "2aco"
        self.nmr_id = "2l9r"
        self.pdb_non_existent = "0abc"
        self.emdb_id = "EMD-5030"
        self.emdb_fsc_id = "EMD-10294"
        self.emdb_non_existent = "EMD-0000"
        self.temp_paths = []
        logging.info("created temp dir %s", self.temp_dir)


    def tearDown(self):
        logging.info("running teardown")
        if os.path.exists(self.temp_dir):
            for f in os.listdir(self.temp_dir):
                os.unlink(os.path.join(self.temp_dir, f))
            shutil.rmtree(self.temp_dir)
        else:
            logging.warning("Temp dir does not exist")
        self.assertFalse(os.path.exists(self.temp_dir), "error - could not remove temp dir %s" % self.temp_dir)
        if self.temp_paths and len(self.temp_paths) > 0:
            vc = ValConfig()
            session_path = vc.session_path
            for path in self.temp_paths:
                entry = path.replace(session_path, '')
                if entry.startswith('/'):
                    entry = entry[1:]
                basename = entry.split('/')[0]
                assert basename != '', "error - could not parse path %s" % path
                temp_path = os.path.join(session_path, basename)
                if os.path.exists(temp_path):
                    shutil.rmtree(temp_path)
                    logging.info("removing temp path %s", temp_path)
                else:
                    logging.warning("could not remove temp path %s", temp_path)


    def test_is_file(self):
        logging.info("testing is_file")
        grf = GetRemoteFilesHttp()
        grf.read_timeout = 60
        grf.use_read_timeout = True
        # test status code 200
        for file in self.zipfiles:
            self.assertTrue(grf.is_file(file), "error - %s" % os.path.basename(file))
        self.assertTrue(grf.is_file(self.large_test_file), "error - %s" % self.large_test_file)
        # test 404 error
        for file in self.non_existent_files:
            self.assertFalse(grf.is_file(file), "error - %s" % os.path.basename(file))


    def test_streaming_http_request(self):
        logging.info("testing streaming http_request")
        grf = GetRemoteFilesHttp()
        grf.read_timeout = 60
        grf.use_read_timeout = True
        logging.info("saving files to %s", self.temp_dir)
        # test download
        for file in self.zipfiles:
            outfile = os.path.join(self.temp_dir, os.path.basename(file))
            self.assertTrue(grf.httpRequest(file, outfile), "error downloading - %s" % os.path.basename(file))
            # verify readable zip file
            with gzip.open(outfile, 'rb') as r:
                self.assertTrue(r.read(1), "error reading gzip file %s" % os.path.basename(file))
        # test 404 error
        for file in self.non_existent_files:
            self.assertFalse(grf.httpRequest(file, os.path.join(self.temp_dir, os.path.basename(file))),
                             "error downloading - %s" % os.path.basename(file))


    def test_non_streaming_http_request(self):
        logging.info("testing non-streaming http_request")
        grf = GetRemoteFilesHttp()
        grf.use_read_timeout = False
        logging.info("saving files to %s", self.temp_dir)
        # test download
        for file in self.zipfiles:
            outfile = os.path.join(self.temp_dir, os.path.basename(file))
            self.assertTrue(grf.httpRequest(file, outfile), "error downloading - %s" % os.path.basename(file))
            # verify readable zip file
            with gzip.open(outfile, 'rb') as r:
                self.assertTrue(r.read(1), "error reading gzip file %s" % os.path.basename(file))
        # test 404 error
        for file in self.non_existent_files:
            self.assertFalse(grf.httpRequest(file, os.path.join(self.temp_dir, os.path.basename(file))),
                             "error downloading - %s" % os.path.basename(file))


    def test_xml_header_file(self):
        logging.info("testing xml header file")
        grf = GetRemoteFilesHttp()
        grf.read_timeout = 60
        grf.use_read_timeout = True
        logging.info("saving files to %s", self.temp_dir)
        # test download
        for file in self.xmlfiles:
            outfile = os.path.join(self.temp_dir, os.path.basename(file))
            logging.info("downloading %s to %s", file, outfile)
            self.assertTrue(grf.httpRequest(file, outfile), "error downloading - %s" % os.path.basename(file))
            # verify readable file
            pdbids = XmlInfo(outfile).get_pdbids_from_xml()
            self.assertTrue(isinstance(pdbids, list), "error - no pdbids found in xml file %s" % os.path.basename(file))
            self.assertTrue(len(pdbids) > 0, "error - no pdbids found in xml file %s" % os.path.basename(file))


    def test_gfr_pdb(self):
        logging.info("testing get files release pdb")
        # test xray
        pdbid = self.xray_id
        gfr = getFilesReleaseHttpPDB(pdbid)
        model_path = gfr.get_model()
        self.assertTrue(os.path.exists(model_path), "error - could not download %s" % model_path)
        logging.info("downloaded %s", model_path)
        self.temp_paths.append(model_path)
        sf_path = gfr.get_sf()
        self.assertTrue(os.path.exists(sf_path), "error - could not download %s" % sf_path)
        logging.info("downloaded %s", sf_path)
        self.temp_paths.append(sf_path)
        # test nmr
        pdbid = self.nmr_id
        gfr = getFilesReleaseHttpPDB(pdbid)
        cs_path = gfr.get_cs()
        self.assertTrue(os.path.exists(cs_path), "error - could not download %s" % model_path)
        logging.info("downloaded %s", cs_path)
        self.temp_paths.append(cs_path)
        nmr_data_path = gfr.get_nmr_data()
        self.assertTrue(os.path.exists(nmr_data_path), "error - could not download %s" % sf_path)
        logging.info("downloaded %s", nmr_data_path)
        self.temp_paths.append(nmr_data_path)
        # test non-existent
        pdbid = self.pdb_non_existent
        gfr = getFilesReleaseHttpPDB(pdbid)
        model_path = gfr.get_model()
        self.assertFalse(model_path, "error - downloaded %s" % model_path)
        sf_path = gfr.get_sf()
        self.assertFalse(sf_path, "error - downloaded %s" % sf_path)


    def test_gfr_emdb(self):
        logging.info("testing get files release emdb")
        emdbid = self.emdb_id
        gfr = getFilesReleaseHttpEMDB(emdbid)
        # test volume file
        vol_path = gfr.get_emdb_volume()
        self.assertTrue(os.path.exists(vol_path), "error - could not download %s" % vol_path)
        logging.info("downloaded %s", vol_path)
        self.temp_paths.append(vol_path)
        # test xml file
        xml_path = gfr.get_emdb_xml()
        self.assertTrue(os.path.exists(xml_path), "error - could not download %s" % xml_path)
        logging.info("downloaded %s", xml_path)
        self.temp_paths.append(xml_path)
        # test fsc file
        emdbid = self.emdb_fsc_id
        gfr = getFilesReleaseHttpEMDB(emdbid)
        fsc_path = gfr.get_emdb_fsc()
        self.assertTrue(os.path.exists(fsc_path), "error - could not download %s" % fsc_path)
        logging.info("downloaded %s", fsc_path)
        self.temp_paths.append(fsc_path)
        # test non-existent
        emdbid = self.emdb_non_existent
        gfr = getFilesReleaseHttpEMDB(emdbid)
        vol_path = gfr.get_emdb_volume()
        self.assertFalse(vol_path, "error - downloaded %s" % vol_path)


if __name__ == '__main__':
    unittest.main()

