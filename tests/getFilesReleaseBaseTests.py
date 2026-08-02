import unittest
from typing import Optional

from wwpdb.apps.val_rel.utils.getFilesReleaseBase import GetFilesReleaseBaseEMDB, GetFilesReleaseBasePDB


class ConcreteGetFilesReleaseBasePDB(GetFilesReleaseBasePDB):
    """Minimal concrete subclass to exercise the base class's own behavior."""

    def close_connection(self) -> None:
        pass

    def remove_local_temp_files(self) -> None:
        pass

    def get_model(self) -> Optional[str]:
        return None

    def get_sf(self) -> Optional[str]:
        return None

    def get_cs(self) -> Optional[str]:
        return None

    def get_nmr_data(self) -> Optional[str]:
        return None


class ConcreteGetFilesReleaseBaseEMDB(GetFilesReleaseBaseEMDB):
    """Minimal concrete subclass to exercise the base class's own behavior."""

    def close_connection(self) -> None:
        pass

    def remove_local_temp_files(self) -> None:
        pass

    def get_emdb_xml(self) -> Optional[str]:
        return None

    def get_emdb_fsc(self) -> Optional[str]:
        return None

    def get_emdb_volume(self) -> Optional[str]:
        return None


class GetFilesReleaseBasePDBTests(unittest.TestCase):
    def test_cannot_instantiate_abstract_class(self) -> None:
        with self.assertRaises(TypeError):
            GetFilesReleaseBasePDB(pdbid="1abc", site_id="PDBE", cache="/tmp")  # type: ignore[abstract]  # noqa: S108 pylint: disable=abstract-class-instantiated

    def test_constructor_stores_arguments(self) -> None:
        obj = ConcreteGetFilesReleaseBasePDB(pdbid="1abc", site_id="PDBE", cache="/tmp")  # noqa: S108
        self.assertEqual(obj._pdbid, "1abc")  # noqa: SLF001 pylint: disable=protected-access
        self.assertEqual(obj._siteid, "PDBE")  # noqa: SLF001  pylint: disable=protected-access
        self.assertEqual(obj._cache, "/tmp")  # noqa: S108,SLF001 pylint: disable=protected-access

    def test_constructor_accepts_none(self) -> None:
        obj = ConcreteGetFilesReleaseBasePDB(pdbid=None, site_id=None, cache=None)
        self.assertIsNone(obj._pdbid)  # noqa: SLF001 pylint: disable=protected-access
        self.assertIsNone(obj._siteid)  # noqa: SLF001 pylint: disable=protected-access
        self.assertIsNone(obj._cache)  # noqa: SLF001 pylint: disable=protected-access


class GetFilesReleaseBaseEMDBTests(unittest.TestCase):
    def test_cannot_instantiate_abstract_class(self) -> None:
        with self.assertRaises(TypeError):
            GetFilesReleaseBaseEMDB(emdbid="EMD-1234")  # type: ignore[abstract]  # noqa: S108 pylint: disable=abstract-class-instantiated

    def test_constructor_stores_arguments(self) -> None:
        obj = ConcreteGetFilesReleaseBaseEMDB(
            emdbid="EMD-1234", site_id="PDBE", local_ftp_emdb_path="/ftp/emdb", cache="/tmp"  # noqa: S108
        )
        self.assertEqual(obj._emdbid, "EMD-1234")  # noqa: SLF001 pylint: disable=protected-access
        self.assertEqual(obj._siteid, "PDBE")  # noqa: SLF001 pylint: disable=protected-access
        self.assertEqual(obj._local_ftp_emdb_path, "/ftp/emdb")  # noqa: SLF001 pylint: disable=protected-access
        self.assertEqual(obj._cache, "/tmp")  # noqa: S108,SLF001 pylint: disable=protected-access

    def test_constructor_defaults_to_none(self) -> None:
        obj = ConcreteGetFilesReleaseBaseEMDB(emdbid="EMD-1234")
        self.assertEqual(obj._emdbid, "EMD-1234")  # noqa: SLF001 pylint: disable=protected-access
        self.assertIsNone(obj._siteid)  # noqa: SLF001 pylint: disable=protected-access
        self.assertIsNone(obj._local_ftp_emdb_path)  # noqa: SLF001 pylint: disable=protected-access
        self.assertIsNone(obj._cache)  # noqa: SLF001 pylint: disable=protected-access

    def test_constructor_accepts_none_emdbid(self) -> None:
        obj = ConcreteGetFilesReleaseBaseEMDB(emdbid=None)
        self.assertIsNone(obj._emdbid)  # noqa: SLF001 pylint: disable=protected-access


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
