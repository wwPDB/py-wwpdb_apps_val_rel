"""Parses EMDB XML header file and extracts pertinent data"""

import xml.etree.ElementTree as ET
from typing import List


class XmlInfo:
    def __init__(self, xml_file: str) -> None:
        self.__tree = ET.parse(xml_file)  # noqa: S314

    def __get_values_from_xpath(self, xpath: str) -> List[str]:
        ret: List[str] = []
        values = self.__tree.findall(xpath)
        for value in values:
            if value.text:  # In case empty string - will default to empty list
                ret.append(value.text)
        return ret

    def get_pdbids_from_xml(self) -> List[str]:
        xpath = ".//crossreferences/pdb_list/pdb_reference/pdb_id"
        return self.__get_values_from_xpath(xpath=xpath)
