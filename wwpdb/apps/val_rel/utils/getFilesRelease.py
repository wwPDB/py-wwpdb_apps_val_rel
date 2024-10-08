import logging
from wwpdb.utils.config.ConfigInfo import getSiteId
from wwpdb.apps.val_rel.config.ValConfig import ValConfig
from wwpdb.apps.val_rel.utils.getFilesReleaseOneDep import getFilesReleaseOneDep

from wwpdb.apps.val_rel.utils.http_protocol.getFilesReleaseHTTP_EMDB import getFilesReleaseHttpEMDB
from wwpdb.apps.val_rel.utils.http_protocol.getFilesReleaseHTTP_PDB import getFilesReleaseHttpPDB
from wwpdb.apps.val_rel.utils.getFilesReleaseFTP_EMDB import getFilesReleaseFtpEMDB
from wwpdb.apps.val_rel.utils.getFilesReleaseFTP_PDB import getFilesReleaseFtpPDB

logger = logging.getLogger(__name__)



class getFilesRelease:
    """Class to access prior/public release files"""

    def __init__(self, pdb_id=None, emdb_id=None, siteID=getSiteId(), cache=None):
        self.__siteID = siteID
        self.pdb_id = pdb_id
        self.emdb_id = emdb_id
        self.__cache = cache
        self.model_current = False
        self.sf_current = False
        self.cs_current = False
        self.mr_current = False
        self.em_xml_current = False
        self.__tempFTP = None

        # Determine which routing
        config = ValConfig(site_id=siteID)
        if config.val_rel_protocol in ["http", "https"]:
            self.__files_pdb_func = getFilesReleaseHttpPDB
            self.__files_emdb_func = getFilesReleaseHttpEMDB
        else:
            self.__files_pdb_func = getFilesReleaseFtpPDB
            self.__files_emdb_func = getFilesReleaseFtpEMDB

        self.__release_file_from_onedep = getFilesReleaseOneDep(siteID=self.__siteID, pdb_id=pdb_id, emdb_id=emdb_id)
        self.__release_file_from_remote_emdb = self.__files_emdb_func(site_id=self.__siteID, emdbid=emdb_id, cache=self.__cache)
        self.__release_file_from_remote_pdb = self.__files_pdb_func(site_id=self.__siteID, pdbid=pdb_id, cache=self.__cache)


    def close_connections(self):
        """This method should be used to close all open
        connections in subclasses.
        """
        self.__release_file_from_remote_pdb.close_connection()
        self.__release_file_from_remote_emdb.close_connection()

    def set_pdb_id(self, pdb_id):
        """Sets up pdb_id for processing release files"""

        # Do not create a new path if same pdb_id. Prevents excessive downloads
        if self.pdb_id != pdb_id:
            self.pdb_id = pdb_id
            self.__release_file_from_onedep = getFilesReleaseOneDep(siteID=self.__siteID,
                                                                    pdb_id=self.pdb_id,
                                                                    emdb_id=self.emdb_id)
            if self.__release_file_from_remote_pdb  is not None:
                self.__release_file_from_remote_pdb.close_connection()

            self.__release_file_from_remote_pdb = self.__files_pdb_func(site_id=self.__siteID, pdbid=pdb_id, cache=self.__cache)

    def set_emdb_id(self, emdb_id):
        """Sets up emdb_id for processing release files"""

        # Do not create a new path if same pdb_id
        if self.emdb_id != emdb_id:
            self.emdb_id = emdb_id
            self.__release_file_from_onedep = getFilesReleaseOneDep(siteID=self.__siteID,
                                                                    pdb_id=self.pdb_id,
                                                                    emdb_id=emdb_id)

            if self.__release_file_from_remote_emdb is not None:
                self.__release_file_from_remote_emdb.close_connection()

            self.__release_file_from_remote_emdb = self.__files_emdb_func(site_id=self.__siteID, emdbid=emdb_id, cache=self.__cache)

    def remove_local_temp_files(self):
        """Removes any temporary FTP directories"""
        self.__release_file_from_remote_pdb.remove_local_temp_files()
        self.__release_file_from_remote_emdb.remove_local_temp_files()

    def get_model(self):
        """
        get the PDB model file - from OneDep then local FTP
        :param pdbid: PDB ID
        :return: file name if present or None
        """
        file_name, self.model_current = self.__release_file_from_onedep.get_model()
        if not file_name:
            file_name = self.__release_file_from_remote_pdb.get_model()
        return file_name

    def get_sf(self):
        """
        get the PDB structure factor file - from OneDep then local FTP
        :param pdbid: PDB ID
        :return: file name if present or None
        """
        file_name, self.sf_current = self.__release_file_from_onedep.get_sf()
        if not file_name:
            file_name = self.__release_file_from_remote_pdb.get_sf()
        return file_name

    def get_cs(self):
        """
        get the PDB chemical shift file - from OneDep then local FTP
        :param pdbid: PDB ID
        :return: file name if present or None
        """
        file_name, self.cs_current = self.__release_file_from_onedep.get_cs()
        if not file_name:
            file_name = self.__release_file_from_remote_pdb.get_cs()
        return file_name

    def get_nmr_data(self):
        """
        Get the PDB combined NMR data file - from OneDep then local FTP
        :param pdbid: PDB ID
        :return: file name if present or None
        """
        file_name, self.cs_current = self.__release_file_from_onedep.get_nmr_data()
        if not file_name:
            file_name = self.__release_file_from_remote_pdb.get_nmr_data()
        return file_name

    def get_emdb_xml(self):
        file_name, self.em_xml_current = self.__release_file_from_onedep.get_emdb_xml()
        if not file_name:
            file_name = self.__release_file_from_remote_emdb.get_emdb_xml()
        return file_name

    def get_emdb_volume(self):
        file_name, _ = self.__release_file_from_onedep.get_emdb_volume()
        if not file_name:
            file_name = self.__release_file_from_remote_emdb.get_emdb_volume()

        return file_name

    def get_emdb_fsc(self):
        file_name, _ = self.__release_file_from_onedep.get_emdb_fsc()
        if not file_name:
            file_name = self.__release_file_from_remote_emdb.get_emdb_fsc()

        return file_name

    def is_sf_current(self):
        return self.sf_current

    def is_cs_current(self):
        return self.cs_current

    def is_em_xml_current(self):
        return self.em_xml_current

    def set_cache(self, fpath):
        self.__cache = fpath

