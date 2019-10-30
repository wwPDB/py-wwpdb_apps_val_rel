import os
import logging
from wwpdb.apps.val_rel.release_file_names import releaseFileNames
from wwpdb.utils.config.ConfigInfo import ConfigInfo, getSiteId


class getFilesRelease:
    def __init__(self, siteID=getSiteId()):
        self.release = False
        self.modified = False
        self.previous_release = False
        self.previous_modified = False
        self.local_ftp = False
        self.ftp = False
        self.pdb_id = None
        self.emdb_id = None
        self.rf = releaseFileNames()
        self.siteID = siteID
        self.cI = ConfigInfo(self.siteID)
        self.for_release_path = self.cI.get("FOR_RELEASE_DATA_PATH", "")
        self.release_path = os.path.join(self.for_release_path, "added")
        self.modified_path = os.path.join(self.for_release_path, "modified")
        self.emdb_release_path = os.path.join(self.for_release_path, "emd")
        self.for_release_previous_path = self.cI.get(
            "FOR_RELEASE_PREVIOUS_DATA_PATH", ""
        )
        self.release_previous_path = os.path.join(
            self.for_release_previous_path, "added"
        )
        self.modified_previous_path = os.path.join(
            self.for_release_previous_path, "modified"
        )
        self.emdb_previous_release_path = os.path.join(
            self.for_release_previous_path, "emd"
        )
        self.local_ftp_mmcif_path = self.cI.get("SITE_MMCIF_DIR", "")
        self.local_ftp_sf_path = self.cI.get("SITE_STRFACTORS_DIR", "")
        self.local_ftp_cs_path = self.cI.get("CHEMICAL_SHIFTS_FTP", "")
        self.local_ftp_emdb_path = self.cI.get("SITE_EMDB_FTP", "")

    def get_pdb_path_search_order(self, pdbid, coordinates=False, sf=False, cs=False):
        ret_list = [
            os.path.join(self.release_path, pdbid),
            os.path.join(self.modified_path, pdbid),
            os.path.join(self.release_previous_path, pdbid),
            os.path.join(self.modified_previous_path, pdbid),
        ]
        if coordinates:
            ret_list.append(self.local_ftp_mmcif_path)
        if sf:
            ret_list.append(self.local_ftp_sf_path)
        if cs:
            ret_list.append(self.local_ftp_cs_path)
        return ret_list

    def search_nfs_pdb(self, filename, pdbid, coordinates=False, sf=False, cs=False):
        for path in self.get_pdb_path_search_order(pdbid, coordinates=coordinates, sf=sf, cs=cs):
            file_path = os.path.join(path, filename)
            logging.debug("searching: {}".format(file_path))
            if os.path.exists(file_path):
                logging.debug("found: {}".format(file_path))
                return file_path
        return None

    def get_model(self, pdbid):
        filename = self.rf.get_model(pdbid)
        file_path = self.search_nfs_pdb(filename=filename, pdbid=pdbid, coordinates=True)
        if file_path:
            return file_path
        return None

    def get_sf(self, pdbid):
        filename = self.rf.get_structure_factor(pdbid, for_release=True) 
        file_path = self.search_nfs_pdb(filename=filename, pdbid=pdbid, sf=True)
        if file_path:
            return file_path
        filename = self.rf.get_structure_factor(pdbid)
        file_path = self.search_nfs_pdb(filename=filename, pdbid=pdbid, sf=True)
        if file_path:
            return file_path
        return None

    def get_cs(self, pdbid):
        filename =  self.rf.get_chemical_shifts(pdbid, for_release=True)
        file_path = self.search_nfs_pdb(filename=filename, pdbid=pdbid, cs=True)
        if file_path:
            return file_path
        filename = self.rf.get_chemical_shifts(pdbid)
        file_path = self.search_nfs_pdb(filename=filename, pdbid=pdbid, cs=True)
        if file_path:
            return file_path
        return None

    def get_emdb_path_search_order(self, emdbid):
        ret_list = [
            os.path.join(self.emdb_release_path, emdbid),
            os.path.join(self.emdb_previous_release_path, emdbid),
            os.path.join(self.local_ftp_emdb_path, emdbid),
        ]

        return ret_list

    def return_emdb_path(self, filename, subfolder, emdbid):
        for path in self.get_emdb_path_search_order(emdbid):
            file_path = os.path.join(path, subfolder, filename)
            logging.debug(file_path)
            if os.path.exists(file_path):
                return file_path
        return None

    def get_emdb_id_file_format(self, emdbid):
        emdb_number = emdbid.split("-")[-1]
        return "emd_{}".format(emdb_number)

    def get_emdb_id_file_format_xml(self, emdbid):
        emdb_number = emdbid.split("-")[-1]
        return "emd-{}".format(emdb_number)

    def get_emdb_xml(self, emdbid):
        accession = self.get_emdb_id_file_format(emdbid)
        filename =  self.rf.get_emdb_xml(accession, for_release=True)
        if filename:
            return self.return_emdb_path(
                filename=filename, subfolder="header", emdbid=emdbid
            )
        accession = self.get_emdb_id_file_format_xml(emdbid)
        filename =  self.rf.get_emdb_xml(accession)
        if filename:
            return self.return_emdb_path(
                filename=filename, subfolder="header", emdbid=emdbid
            )
        return None

    def get_emdb_volume(self, emdbid):
        filename = self.rf.get_emdb_map(self.get_emdb_id_file_format(emdbid))
        return self.return_emdb_path(filename=filename, subfolder="map", emdbid=emdbid)

    def get_emdb_fsc(self, emdbid):
        filename = self.rf.get_emdb_fsc(self.get_emdb_id_file_format(emdbid))
        return self.return_emdb_path(filename=filename, subfolder="fsc", emdbid=emdbid)
