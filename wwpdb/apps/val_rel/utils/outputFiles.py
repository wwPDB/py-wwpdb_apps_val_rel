import logging
import os
from typing import Dict, Optional, cast

from wwpdb.io.locator.ReleaseFileNames import ReleaseFileNames
from wwpdb.io.locator.ReleasePathInfo import ReleasePathInfo
from wwpdb.utils.config.ConfigInfo import getSiteId

logger = logging.getLogger(__name__)


class outputFiles:
    def __init__(
        self,
        pdbID: Optional[str] = None,
        emdbID: Optional[str] = None,
        outputRoot: Optional[str] = "",
        siteID: Optional[str] = None,
        skip_pdb_hash: bool = False,
        validation_sub_directory: str = "current",
        temp_output_folder: Optional[str] = None,
    ):
        if siteID is None:
            siteID = getSiteId()
        self._pdbID = pdbID
        self._emdbID = emdbID
        self._siteID = siteID
        self._output_root = outputRoot
        self._validation_sub_directory = validation_sub_directory
        self._temp_output_folder = temp_output_folder
        self._entryID: Optional[str] = None
        self.__skip_pdb_hash = skip_pdb_hash
        self.__pdb_output_folder: Optional[str] = None
        self.__emdb_output_folder: Optional[str] = None
        self.__entry_output_folder: Optional[str] = None
        self.__with_emdb = False
        self.__accession = ""
        self.__rf = ReleaseFileNames()
        self.get_pdb_output_folder()
        self.get_emdb_output_folder()
        self.get_entry_output_folder()

    def get_pdb_root_folder(self) -> str:
        rp = ReleasePathInfo(self._siteID)
        return os.path.join(rp.getForReleasePath("val_reports"), self._validation_sub_directory)

    def get_validation_images_root_folder(self) -> str:
        rp = ReleasePathInfo(self._siteID)
        return cast("str", rp.getForReleasePath("val_images"))

    def get_root_state_folder(self) -> str:
        # Place under pdb val-reports as extra directory
        rp = ReleasePathInfo(self._siteID)
        return os.path.join(
            rp.getForReleasePath("val_reports"),
            self._validation_sub_directory + "_state",
        )

    def get_emdb_root_folder(self) -> str:
        rp = ReleasePathInfo(self._siteID)
        return os.path.join(rp.getForReleasePath("em_val_reports"), self._validation_sub_directory)

    def set_validation_subdirectory(self, sub_dir: str) -> None:
        self._validation_sub_directory = sub_dir

    def set_entry_id(self, entry_id: str) -> None:
        self._entryID = entry_id

    def set_pdb_id(self, entry_id: str) -> None:
        self._pdbID = entry_id

    def set_emdb_id(self, entry_id: str) -> None:
        self._emdbID = entry_id

    def get_pdb_id(self) -> str:
        if self._pdbID:
            return self._pdbID
        return ""

    def get_pdb_id_hash(self) -> str:  # Extended PDB ids issue
        if self.get_pdb_id():
            return self.get_pdb_id()[1:3]
        return ""

    def get_emdb_id(self) -> str:
        if self._emdbID:
            return self._emdbID
        return ""

    def get_emdb_lower_hyphen(self) -> str:
        if self.get_emdb_id():
            return cast("str", self.__rf.get_lower_emdb_hyphen_format(self.get_emdb_id()))
        return ""

    def get_emdb_lower_underscore(self) -> str:
        if self.get_emdb_id():
            return cast("str", self.__rf.get_lower_emdb_underscore_format(self.get_emdb_id()))
        return ""

    def get_entry_id(self) -> str:
        if self._entryID:
            return self._entryID
        return ""

    def set_accession(self) -> str:
        self.__accession = f"{self._entryID}"
        if self._emdbID and not self._pdbID:
            self.__accession = self.get_emdb_lower_underscore()

        return self.__accession

    def add_output_folder_accession(self, filename: str) -> str:
        if self._temp_output_folder:
            return os.path.join(self._temp_output_folder, filename)
        if not self.__entry_output_folder:
            emsg = "entry_output_folder not set"
            raise ValueError(emsg)
        return os.path.join(self.__entry_output_folder, filename)

    def get_validation_xml(self) -> str:
        return self.add_output_folder_accession(self.__rf.get_validation_xml(self.__accession))

    def get_validation_png(self) -> str:
        return self.add_output_folder_accession(self.__rf.get_validation_png(self.__accession))

    def get_validation_svg(self) -> str:
        return self.add_output_folder_accession(self.__rf.get_validation_svg(self.__accession))

    def get_validation_pdf(self) -> str:
        return self.add_output_folder_accession(self.__rf.get_validation_pdf(self.__accession))

    def get_validation_full_pdf(self) -> str:
        return self.add_output_folder_accession(self.__rf.get_validation_full_pdf(self.__accession))

    def get_validation_2fofc(self) -> str:
        return self.add_output_folder_accession(self.__rf.get_validation_2fofc(self.__accession))

    def get_validation_fofc(self) -> str:
        return self.add_output_folder_accession(self.__rf.get_validation_fofc(self.__accession))

    def get_validation_image_tar(self) -> str:
        return self.add_output_folder_accession(self.__rf.get_validation_image_tar(self.__accession))

    def get_validation_cif(self) -> str:
        return self.add_output_folder_accession(self.__rf.get_validation_cif(self.__accession))

    def get_core_validation_files(self) -> Dict[str, str]:
        logger.debug("getting core files for: %s", self._entryID)
        logger.debug("path: %s", self.__entry_output_folder)

        self.set_accession()
        logger.debug("accession set to %s", self.__accession)

        ret = {
            "pdf": self.get_validation_pdf(),
            "full_pdf": self.get_validation_full_pdf(),
            "xml": self.get_validation_xml(),
            "png": self.get_validation_png(),
            "svg": self.get_validation_svg(),
            "cif": self.get_validation_cif(),
        }

        logger.debug(ret)

        return ret

    def get_extra_validation_files(self) -> Dict[str, str]:
        ret = {
            "2fofc": self.get_validation_2fofc(),
            "fofc": self.get_validation_fofc(),
        }

        return ret

    def get_validation_files_for_separate_location(self) -> Dict[str, str]:
        ret = {"image_tar": self.get_validation_image_tar()}

        return ret

    def get_all_validation_files(self) -> Dict[str, str]:
        all_file_dict = self.get_core_validation_files().copy()
        all_file_dict.update(self.get_extra_validation_files())
        all_file_dict.update(self.get_validation_files_for_separate_location())

        return all_file_dict

    def ret_pdb_hash(self) -> str:
        if self.__skip_pdb_hash:
            pdb_hash = ""
        else:
            pdb_hash = self.get_pdb_id_hash()
        return pdb_hash

    def get_pdb_validation_images_output_folder(self) -> str:
        if self._output_root:
            return os.path.join(self._output_root, "val_images", self.get_pdb_id())
        return os.path.join(self.get_validation_images_root_folder(), self.get_pdb_id())

    def get_pdb_output_folder(self) -> str:
        """
        Gets the PDB output folder
        :return: PDB output folder
        """
        if self.get_pdb_id():
            self.set_entry_id(self.get_pdb_id())
            if self._output_root:
                self.__pdb_output_folder = os.path.join(
                    self._output_root, "pdb", self.ret_pdb_hash(), self.get_pdb_id()
                )
            else:
                self.__pdb_output_folder = os.path.join(self.get_pdb_root_folder(), self.get_pdb_id())
        return cast("str", self.__pdb_output_folder)

    def get_emdb_output_folder(self) -> str:
        """
        gets the EMDB output folder
        :return: EMDB output folder
        """
        if self.get_emdb_id():
            self.set_entry_id(self.get_emdb_id())
            if self._output_root:
                self.__emdb_output_folder = os.path.join(self._output_root, "emd", self.get_emdb_id(), "validation")
            else:
                self.__emdb_output_folder = os.path.join(self.get_emdb_root_folder(), self.get_emdb_id(), "validation")
        return cast("str", self.__emdb_output_folder)

    def get_entry_output_folder(self) -> Optional[str]:
        if self.get_pdb_id():
            self.__entry_output_folder = self.get_pdb_output_folder()
        elif self.get_emdb_id():
            self.__entry_output_folder = self.get_emdb_output_folder()
        return self.__entry_output_folder

    def get_ftp_cache_folder(self) -> str:
        # Same for both x-ray/em
        rp = ReleasePathInfo(self._siteID)
        return os.path.join(rp.getForReleasePath("val_reports"), "cache")
