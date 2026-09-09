from abc import ABC, abstractmethod
from typing import NoReturn, Optional


class GetFilesReleaseBasePDB(ABC):
    """Base class for retrieving files from release repositories."""

    def __init__(self, pdbid: Optional[str], site_id: Optional[str], cache: Optional[str]) -> None:
        """Initialize the base class.

        Args:
            pdbid: The PDB id.  Optional as initialization of class does not connect, and might be model only
            site_id: Optional site_id
            cache: Optional cache path

        """
        self._pdbid = pdbid
        self._siteid = site_id
        self._cache = cache

    @abstractmethod
    def close_connection(self) -> None:
        """Closes remote connection."""

    @abstractmethod
    def remove_local_temp_files(self) -> None:
        """Removes any temporary directories directories."""

    @abstractmethod
    def get_model(self) -> Optional[str]:
        """Get the PDB model file.

        Returns:
            File name if filename present or None
        """

    @abstractmethod
    def get_sf(self) -> Optional[str]:
        """Get the PDB structure factor file.

        Returns:
            File name if filename present or None
        """

    @abstractmethod
    def get_cs(self) -> Optional[str]:
        """Get the PDB chemical shift file.

        Returns:
            File name if filename present or None
        """

    @abstractmethod
    def get_nmr_data(self) -> Optional[str]:
        """Get the PDB combined NMR data file.

        Returns:
            File name if filename present or None
        """


class GetFilesReleaseBaseEMDB(ABC):
    """Base class for retrieving files from release repositories."""

    def __init__(
        self,
        emdbid: Optional[str],
        site_id: Optional[str] = None,
        local_ftp_emdb_path: Optional[str] = None,
        cache: Optional[str] = None,
    ) -> None:
        """Initialize the base class.

        Args:
            emdbid: Optional The EMDB id.  Interface supports None.
            site_id: Optional site_id
            local_ftp_emdb_path: Optional local FTP path
            cache: Optional cache path

        """
        self._emdbid = emdbid
        self._siteid = site_id
        self._cache = cache
        self._local_ftp_emdb_path = local_ftp_emdb_path

    @abstractmethod
    def close_connection(self) -> None:
        """Closes remote connection."""

    @abstractmethod
    def remove_local_temp_files(self) -> None:
        """Removes any temporary directories directories."""

    @abstractmethod
    def get_emdb_xml(self) -> Optional[str]:
        """Get the EMDB XML file.

        Returns:
            File name if filename present or None
        """

    @abstractmethod
    def get_emdb_fsc(self) -> Optional[str]:
        """Get the EMDB FSC file.

        Returns:
            File name if filename present or None
        """

    @abstractmethod
    def get_emdb_volume(self) -> Optional[str]:
        """Pulls in all files for EMDB analysis

        Returns:
            File name or path containing files
        """

    @abstractmethod
    def get_emdb_metadata(self) -> Optional[str]:
        """Returs path to EMDB metadata file if present

        Returns:
            File name if present or none.
        """


def raise_no_emdb() -> NoReturn:
    msg = "EMDB id not set"
    raise ValueError(msg)


def raise_no_pdb() -> NoReturn:
    msg = "PDB id not set"
    raise ValueError(msg)
