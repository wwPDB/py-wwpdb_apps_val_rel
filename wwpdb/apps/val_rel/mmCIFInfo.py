class mmCIFInfo:
    def __init__(self, mmCIF_file, IoAdapter=IoAdapterCore(), log=sys.stderr):
        self.mmcif = mmCIF_file
        self.logFileHandler = log
        self.io = IoAdapter
        self.mmcif_data = None

    def parse_mmcif(self):
        if self.mmcif:
            try:
                logging.debug("parsing {}".format(self.mmcif))
                cList = self.io.readFile(self.mmcif)
                self.mmcif_data = cList[0]
                return self.mmcif_data
            except Exception as e:
                logging.error("failed to parse: %s" % self.mmcif)
                logging.error(e)

        return None

    def get_category(self, category):
        if not self.mmcif_data:
            self.parse_mmcif()
        if self.mmcif_data:
            dcObj = self.mmcif_data.getObj(category)
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
        if emdb_ids and len(emdb_ids) == 1:
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
