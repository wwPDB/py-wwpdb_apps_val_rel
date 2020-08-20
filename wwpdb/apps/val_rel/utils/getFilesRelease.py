import logging

from wwpdb.utils.config.ConfigInfo import getSiteId

from wwpdb.apps.val_rel.utils.getFilesReleaseFTP_EMDB import getFilesReleaseFtpEMDB
from wwpdb.apps.val_rel.utils.getFilesReleaseFTP_PDB import getFilesReleaseFtpPDB
from wwpdb.apps.val_rel.utils.getFilesReleaseOneDep import getFilesReleaseOneDep

logger = logging.getLogger(__name__)


class getFilesRelease:
    """Class to access prior/public release files"""

    def __init__(self, pdb_id=None, emdb_id=None, siteID=getSiteId()):
        self.__siteID = siteID
        self.pdb_id = pdb_id
        self.emdb_id = emdb_id
        self.__release_file_from_onedep = getFilesReleaseOneDep(siteID=self.__siteID, pdb_id=pdb_id, emdb_id=emdb_id)
        self.__release_file_from_ftp_emdb = getFilesReleaseFtpEMDB(site_id=self.__siteID, emdbid=emdb_id)
        self.__release_file_from_ftp_pdb = getFilesReleaseFtpPDB(site_id=self.__siteID, pdbid=pdb_id)
        self.model_current = False
        self.sf_current = False
        self.cs_current = False
        self.mr_current = False
        self.em_xml_current = False
        self.__tempFTP = None

    def set_pdb_id(self, pdb_id):
        self.pdb_id = pdb_id
        self.__release_file_from_onedep = getFilesReleaseOneDep(siteID=self.__siteID,
                                                                pdb_id=self.pdb_id,
                                                                emdb_id=self.emdb_id)
        self.__release_file_from_ftp_pdb = getFilesReleaseFtpPDB(site_id=self.__siteID, pdbid=pdb_id)

    def set_emdb_id(self, emdb_id):
        self.emdb_id = emdb_id
        self.__release_file_from_onedep = getFilesReleaseOneDep(siteID=self.__siteID,
                                                                pdb_id=self.pdb_id,
                                                                emdb_id=emdb_id)
        self.__release_file_from_ftp_emdb = getFilesReleaseFtpEMDB(site_id=self.__siteID, emdbid=emdb_id)

    def get_model(self):
        """
        get the PDB model file - from OneDep then local FTP
        :param pdbid: PDB ID
        :return: file name if present or None
        """
        file_name, self.model_current = self.__release_file_from_onedep.get_model()
        if not file_name:
            file_name = self.__release_file_from_ftp_pdb.get_model()
        return file_name

    def get_sf(self):
        """
        get the PDB structure factor file - from OneDep then local FTP
        :param pdbid: PDB ID
        :return: file name if present or None
        """
        file_name, self.sf_current = self.__release_file_from_onedep.get_sf()
        if not file_name:
            file_name = self.__release_file_from_ftp_pdb.get_sf()
        return file_name

    def get_cs(self):
        """
        get the PDB chemical shift file - from OneDep then local FTP
        :param pdbid: PDB ID
        :return: file name if present or None
        """
        file_name, self.cs_current = self.__release_file_from_onedep.get_cs()
        if not file_name:
            file_name = self.__release_file_from_ftp_pdb.get_cs()
        return file_name

    def get_nmr_data(self):
        """
        Get the PDB combined NMR data file - from OneDep then local FTP
        :param pdbid: PDB ID
        :return: file name if present or None
        """
        file_name, self.cs_current = self.__release_file_from_onedep.get_nmr_data()
        if not file_name:
            file_name = self.__release_file_from_ftp_pdb.get_nmr_data()
        return file_name

    def get_emdb_xml(self):
        file_name, self.em_xml_current = self.__release_file_from_onedep.get_emdb_xml()
        if not file_name:
            file_name = self.__release_file_from_ftp_emdb.get_emdb_xml()
        return file_name

    def get_emdb_volume(self):
        file_name, _ = self.__release_file_from_onedep.get_emdb_volume()
        if not file_name:
            file_name = self.__release_file_from_ftp_emdb.get_emdb_volume()

        return file_name

    def get_emdb_fsc(self):
        file_name, _ = self.__release_file_from_onedep.get_emdb_fsc()
        if not file_name:
            file_name = self.__release_file_from_ftp_emdb.get_emdb_fsc()

        return file_name

    def is_sf_current(self):
        return self.sf_current

    def is_cs_current(self):
        return self.cs_current

    def is_em_xml_current(self):
        return self.em_xml_current
