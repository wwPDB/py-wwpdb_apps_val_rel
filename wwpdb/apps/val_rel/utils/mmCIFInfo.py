import logging
from typing import Any, Dict, List, Optional, Tuple

from mmcif.api.DataCategory import DataCategory
from mmcif.api.PdbxContainers import CifName, DataContainer
from mmcif.io.IoAdapterCore import IoAdapterCore

logger = logging.getLogger(__name__)


def is_simple_modification(model_path: str) -> bool:
    """if there are only simple changes based the audit - skip calculation of validation report
    (currently, citation, citation_author, pdbx_audit_support, pdbx_initial_refinement_model)

    returns True is only simple changes present
    """

    # database_2 is handled specially
    SKIP_LIST = [
        "citation",
        "citation_author",
        "pdbx_audit_support",
        "pdbx_contact_author",
        "database_PDB_caveat",
        "diffrn",
        "diffrn_detector",
        "diffrn_radiation",
        "diffrn_radiation_wavelength",
        "diffrn_source",
        "entity_name_com",
        "entity_src_gen",
        "entity_src_nat",
        "exptl_crystal",
        "exptl_crystal_grow",
        "pdbx_audit_support",
        "pdbx_contact_author",
        "pdbx_entity_src_syn",
        "pdbx_entry_details",
        "pdbx_nmr_chem_shift_experiment",
        "pdbx_nmr_chem_shift_ref",
        "pdbx_nmr_chem_shift_reference",
        "pdbx_nmr_chem_shift_software",
        "pdbx_nmr_computing",
        "pdbx_nmr_detail",
        "pdbx_nmr_exptl",
        "pdbx_nmr_exptl_sample",
        "pdbx_nmr_exptl_sample_conditions",
        "pdbx_nmr_force_constants",
        "pdbx_nmr_refine",
        "pdbx_nmr_sample_details",
        "pdbx_nmr_software_task",
        "pdbx_nmr_spectral_dim",
        "pdbx_nmr_spectral_peak_list",
        "pdbx_nmr_spectral_peak_software",
        "pdbx_nmr_spectrometer",
        "pdbx_nmr_systematic_chem_shift_offset",
        "pdbx_refine_tls",
        "pdbx_refine_tls_group",
        "pdbx_struct_assembly",
        "pdbx_struct_assembly_auth_evidence",
        "pdbx_struct_assembly_gen",
        "pdbx_struct_assembly_prop",
        "pdbx_struct_oper_list",
        "pdbx_struct_sheet_hbond",
        "refine_ls_restr",
        "refine_ls_restr_ncs",
        "refine_ls_shell",
        "reflns_shell",
        "struct_conf",
        "struct_conf_type",
        "struct_keywords",
        "struct_ncs_dom",
        "struct_ncs_dom_lim",
        "struct_ncs_ens",
        "struct_sheet",
        "struct_sheet",
        "struct_sheet_order",
        "struct_sheet_order",
        "struct_sheet_range",
        "struct_sheet_range",
        "struct_site",
        "pdbx_initial_refinement_model",
        "database_2",
        "chem_comp_atom",
        "chem_comp_bond",
        "chem_comp_angle",
        "pdbx_modification_feature",
        "pdbx_nonpoly_feature",
        "pdbx_nonpoly_atom_feature",
        "pdbx_nonpoly_atom_feature_evidence",
        "pdbx_nonpoly_feature_evidencepdbx_nonpoly_atom_coordination",
        "pdbx_nonpoly_atom_coordination_sphere",
        "pdbx_nonpoly_atom_coordination_sphere_order",
    ]

    SKIP_ATTR = {"database_2": ["pdbx_DOI", "pdbx_database_accession"]}

    cf = mmCIFInfo(model_path)
    modified_cats, latest_ordinal = cf.get_latest_modified_categories()
    if latest_ordinal:
        attrs = cf.get_modified_items(latest_ordinal)
    else:
        attrs = {}

    if modified_cats:
        for item in modified_cats:
            if item not in SKIP_LIST:
                return False

            # For certain categories - check specific changes
            if item in SKIP_ATTR:
                # Get list of modifications for category item:
                if item not in attrs:
                    logger.error("%s audit history messed up", model_path)
                    return False

                # All modified items in this category must be in allowed list
                for attr in attrs[item]:
                    if attr not in SKIP_ATTR[item]:
                        return False

        logger.debug("%s only a simple modification: %s", model_path, ",".join(modified_cats))
        return True
    return False


class mmCIFInfo:
    """Class for parsing model file mmCIF file"""

    def __init__(self, mmCIF_file: str, IoAdapter: Optional[Any] = None) -> None:
        self.__mmcif = mmCIF_file
        self.__io: Any = IoAdapter if IoAdapter else IoAdapterCore()
        self.__mmcif_data: Optional[DataContainer] = None

        self.exclude_category_list = ["atom_site", "atom_site_anisotrop"]

    def parse_mmcif(self) -> Optional[DataContainer]:
        if self.__mmcif:
            try:
                logger.debug("parsing %s", self.__mmcif)
                cList = self.__io.readFile(self.__mmcif, selectList=self.exclude_category_list, excludeFlag=True)
                self.__mmcif_data = cList[0]
                return self.__mmcif_data
            except Exception as e:  # noqa: BLE001
                logger.error("failed to parse: %s error %s", self.__mmcif, str(e))

        return None

    def get_category(self, category: str) -> Optional[DataCategory]:
        if not self.__mmcif_data:
            self.parse_mmcif()
        if self.__mmcif_data:
            dcObj = self.__mmcif_data.getObj(category)
            return dcObj
        return None

    def get_category_keys(self, category: str) -> Dict[str, int]:
        """Returns a dictionary of attribute name and ordinal if category exists"""
        cat_dict = {}
        dcObj = self.get_category(category)
        if dcObj is not None:
            keys_in_list_of_sets = dcObj.getAttributeListWithOrder()
            for key in keys_in_list_of_sets:
                cat_dict[key[0]] = key[1]
        return cat_dict

    def get_category_list_of_dictionaries(self, category: str) -> List[Dict[str, str]]:
        return_list = []
        cat_items = self.get_category_keys(category=category)
        cat_data = self.get_category(category=category)
        if cat_data is not None:
            for row in range(len(cat_data.data)):
                row_dict = {}
                for item in cat_items:
                    value = cat_data.getValueOrDefault(attributeName=item, defaultValue="", rowIndex=row)
                    row_dict[item] = value
                return_list.append(row_dict)

        return return_list

    def get_cat_item_values(self, category: str, item: str) -> List[str]:
        value_list = []
        cat = self.get_category(category=category)
        if cat is not None:
            for row in range(len(cat.data)):
                value = cat.getValueOrDefault(attributeName=item, defaultValue="", rowIndex=row)
                value_list.append(value)

        return value_list

    def get_exp_methods(self) -> List[str]:
        return self.get_cat_item_values(category="exptl", item="method")

    def get_associated_emdb(self) -> Optional[str]:
        """Returns the first 'associated EM volume' in pdbx_database_related"""
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
            emdb_id = emdb_ids[0]
            logger.debug("found EMDB ID: %s", emdb_id)
            return emdb_id
        return None

    # def get_em_map_contour_level(self) -> Optional[str]:
    #     """Returns the contour level of primary map - if present or None"""
    #     ret = self.get_category_list_of_dictionaries(category="em_map")
    #     if ret:
    #         for row in ret:
    #             contour_level = row.get("contour_level")
    #             map_type = row.get("type")
    #             if map_type == "primary":
    #                 return contour_level
    #     return None

    def get_latest_modified_categories(self) -> Tuple[List[str], Optional[str]]:
        """Returns the latet modified categories and ordinal associated with it"""
        latest_audit_ordinal: Optional[str] = None
        latest_audit_categories: List[str] = []
        ret = self.get_category_list_of_dictionaries(category="pdbx_audit_revision_history")
        if ret:
            for row in ret:
                ordinal = row.get("ordinal")  # Better be there
                if ordinal and latest_audit_ordinal:  # This should use int!!!!
                    latest_audit_ordinal = max(latest_audit_ordinal, ordinal)
                else:
                    latest_audit_ordinal = ordinal
        if latest_audit_ordinal:
            logger.debug("latest audit ordinal: %s", latest_audit_ordinal)
            ret = self.get_category_list_of_dictionaries(category="pdbx_audit_revision_category")
            if ret:
                for row in ret:
                    revision_ordinal = row.get("revision_ordinal")
                    category = row.get("category")
                    if category and revision_ordinal == latest_audit_ordinal:
                        latest_audit_categories.append(category)

        return latest_audit_categories, latest_audit_ordinal

    def get_modified_items(self, ordinal: str) -> Dict[str, List[str]]:
        """Returns the dictionary of latet modified attributes for ordinal keyed on category name"""
        ret: Dict[str, List[str]] = {}
        cdata = self.get_category_list_of_dictionaries(category="pdbx_audit_revision_item")

        cn = CifName()
        for c in cdata:
            if "revision_ordinal" in c and "item" in c:
                if c["revision_ordinal"] == ordinal:
                    item = c["item"]
                    cat = cn.categoryPart(item)
                    iname = cn.attributePart(item)

                    if cat not in ret:
                        ret[cat] = []
                    ret[cat].append(iname)

        return ret
