import logging

from mmcif.io.IoAdapterCore import IoAdapterCore as IoAdapterCore

logger = logging.getLogger(__name__)


class mmCIFInfo:
    """Class for parsing model file mmCIF file"""
    def __init__(self, mmCIF_file, IoAdapter=IoAdapterCore()):
        self.__mmcif = mmCIF_file
        self.__io = IoAdapter
        self.__mmcif_data = None

        self.exclude_category_list = ['atom_site', 'atom_site_anisotrop']

    def parse_mmcif(self):
        if self.__mmcif:
            try:
                logger.debug("parsing %s", self.__mmcif)
                cList = self.__io.readFile(self.__mmcif, selectList=self.exclude_category_list, excludeFlag=True)
                self.__mmcif_data = cList[0]
                return self.__mmcif_data
            except Exception as e:
                logger.error("failed to parse: %s error %s", self.__mmcif, str(e))

        return None

    def get_category(self, category):
        if not self.__mmcif_data:
            self.parse_mmcif()
        if self.__mmcif_data:
            dcObj = self.__mmcif_data.getObj(category)
            return dcObj
        return None

    def get_category_keys(self, category):
        cat_dict = {}
        dcObj = self.get_category(category)
        if dcObj is not None:
            keys_in_list_of_sets = dcObj.getAttributeListWithOrder()
            for key in keys_in_list_of_sets:
                cat_dict[key[0]] = key[1]
        return cat_dict

    def get_category_list_of_dictionaries(self, category):
        return_list = []
        cat_items = self.get_category_keys(category=category)
        cat_data = self.get_category(category=category)
        if cat_data is not None:
            for row in range(len(cat_data.data)):
                row_dict = {}
                for item in cat_items:
                    value = cat_data.getValueOrDefault(
                        attributeName=item, defaultValue="", rowIndex=row
                    )
                    row_dict[item] = value
                return_list.append(row_dict)
        return return_list

    def get_cat_item_values(self, category, item):
        value_list = []
        cat = self.get_category(category=category)
        if cat is not None:
            for row in range(len(cat.data)):
                value = cat.getValueOrDefault(
                    attributeName=item, defaultValue="", rowIndex=row
                )
                value_list.append(value)

        return value_list

    def get_exp_methods(self):
        return self.get_cat_item_values(category="exptl", item="method")

    def get_associated_emdb(self):
        emdb_ids = []
        ret = self.get_category_list_of_dictionaries(category="pdbx_database_related")
        if ret:
            for row in ret:
                # db_name = row.get("db_name")
                content_type = row.get("content_type")
                db_id = row.get("db_id")
                if content_type == "associated EM volume":
                    emdb_ids.append(db_id)
        if emdb_ids:
            return emdb_ids[0]
        return None

    def get_em_map_contour_level(self):
        ret = self.get_category_list_of_dictionaries(category="em_map")
        if ret:
            for row in ret:
                contour_level = row.get("contour_level")
                map_type = row.get("type")
                if map_type == "primary":
                    return contour_level
        return None

    def get_latest_modified_categories(self):
        latest_audit_ordinal = None
        latest_audit_categories = []
        ret = self.get_category_list_of_dictionaries(category="pdbx_audit_revision_history")
        if ret:
            for row in ret:
                ordinal = row.get('ordinal')
                if latest_audit_ordinal:
                    if ordinal > latest_audit_ordinal:
                        latest_audit_ordinal = ordinal
                else:
                    latest_audit_ordinal = ordinal
        if latest_audit_ordinal:
            logger.info('latest audit ordinal: %s', latest_audit_ordinal)
            ret = self.get_category_list_of_dictionaries(category="pdbx_audit_revision_category")
            if ret:
                for row in ret:
                    revision_ordinal = row.get('revision_ordinal')
                    category = row.get('category')
                    if revision_ordinal == latest_audit_ordinal:
                        latest_audit_categories.append(category)

        return latest_audit_categories
