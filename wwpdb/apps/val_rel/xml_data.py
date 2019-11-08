import os
import xml.etree.ElementTree as ET


class xmlInfo:

    def __init__(self, xml_file):
        self.tree = ET.parse(xml_file)
        self.root = self.tree.getroot()      

    def get_values_from_xpath(self, xpath):
        ret = []
        values = self.tree.findall(xpath)
        for value in values:
            ret.append(value.text)
        return ret

    def get_pdbids_from_xml(self):
        xpath = './/crossreferences/pdb_list/pdb_reference/pdb_id'
        return self.get_values_from_xpath(xpath=xpath)
