import datetime
import logging
from typing import Any, Dict, List, Literal, Optional, Set, Tuple, Union, overload

from mmcif.api.DataCategory import DataCategory
from mmcif.api.PdbxContainers import CifName, DataContainer
from mmcif.io.IoAdapterCore import IoAdapterCore

logger = logging.getLogger(__name__)


_EM_SKIP_LIST = {
    "audit_conform",
    "citation",
    "citation_author",
    "database_2",
    "em_admin",  # Skip all but title - see SKIP_ATTR
    "em_3d_fitting",
    "em_buffer",
    "em_crystal_formation",
    "em_db_reference",
    "em_entity_assembly",
    "em_entity_assembly_molwt",
    "em_entity_assembly_naturalsource",
    "em_entity_assembly_recombinant",
    "em_euler_angle_assignment",
    "em_final_classification",
    "em_grid_pretreatment",
    "em_image_processing",
    "em_image_scans",
    "em_imaging_optics",
    "em_obsolete",
    "em_particle_selection",
    "em_sample_support",
    "em_software",
    "em_specimen",
    "em_staining",
    "em_start_model",
    "em_supersede",
    "em_support_film",
    "em_tomography_specimen",
    "em_virus_entity",
    "em_virus_natural_host",
    "em_vitrification",
    "pdbx_initial_refinement_model",
    "pdbx_database_PDB_obs_spr",
    "pdbx_entity_src_syn",
    "struct_keywords",
}

_PDB_SKIP_LIST = {
    "audit_conform",
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
    "pdbx_database_PDB_obs_spr",
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
    "struct_sheet_order",
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
    "pdbx_nonpoly_feature_evidence",
    "pdbx_nonpoly_atom_coordination",
    "pdbx_nonpoly_atom_coordination_sphere",
    "pdbx_nonpoly_atom_coordination_sphere_order",
}

_PDB_COMBINED_SKIP_LIST = _PDB_SKIP_LIST.union(_EM_SKIP_LIST)  # Bring in EM categories - in case in coordinate file

_SKIP_ATTR = {
    "database_2": ["pdbx_DOI", "pdbx_database_accession"],
    "em_admin": ["emd_id", "current_status", "last_update", "deposition_date", "map_release_date", "details"],
}


def _parsedate(date_str: str) -> Optional[datetime.date]:
    """Parses a date string in YYYY-MM-DD format, returning a datetime.date.

    Returns None if the string cannot be parsed.
    """
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=datetime.timezone.utc).date()
    except (TypeError, ValueError):
        return None


def is_simple_modification(model_path: str) -> bool:
    """if there are only simple changes based the audit - skip calculation of validation report
    (currently, citation, citation_author, pdbx_audit_support, pdbx_initial_refinement_model)

    returns True is only simple changes present
    """
    return __simple_modification(model_path, "Structure model", _PDB_COMBINED_SKIP_LIST, _SKIP_ATTR)


def is_simple_emdb_modification(model_path: str) -> bool:
    """if there are only simple changes based the audit - skip calculation of validation report
    (currently, citation, citation_author, pdbx_audit_support, pdbx_initial_refinement_model)

    returns True is only simple changes present
    """
    return __simple_modification(model_path, "EM metadata", _EM_SKIP_LIST, _SKIP_ATTR)


def __simple_modification(
    model_path: str,
    content_type: Literal["Structure model", "EM metadata"],
    skip_cat: Set[str],
    skip_attr: Optional[Dict[str, List[str]]],
) -> bool:
    """Determines if a modification with the given content time is a simple modification using a list of categories
    (skip_cat) and optional dictionary of categories and attributes"""

    cf = mmCIFInfo(model_path)
    modified_cats, latest_ordinal, no_audit = cf.get_latest_modified_categories(content_type=content_type)
    if latest_ordinal:
        attrs = cf.get_modified_items(latest_ordinal)
    else:
        attrs = {}

    if modified_cats:
        for item in modified_cats:
            if item not in skip_cat:
                return False

            # For certain categories - check specific changes
            if skip_attr and item in skip_attr:
                # Get list of modifications for category item:
                if item not in attrs:
                    logger.error("%s audit history messed up", model_path)
                    return False

                # All modified items in this category must be in allowed list
                for attr in attrs[item]:
                    if attr not in skip_attr[item]:
                        return False

        logger.debug("%s only a simple modification: %s", model_path, ",".join(modified_cats))
        return True

    # Revision history not relevant here to PDB - so return True
    if no_audit:
        return False
    # We have audit records - but this release not relevant to model file
    return True


class mmCIFInfo:
    """Class for parsing model file mmCIF file"""

    def __init__(self, mmCIF_file: str, IoAdapter: Optional[Any] = None) -> None:
        self.__mmcif = mmCIF_file
        self.__io: Any = IoAdapter if IoAdapter else IoAdapterCore()
        self.__mmcif_data: Optional[DataContainer] = None

        self.__exclude_category_list = ["atom_site", "atom_site_anisotrop"]

    def parse_mmcif(self) -> Optional[DataContainer]:
        if self.__mmcif:
            try:
                logger.debug("parsing %s", self.__mmcif)
                cList = self.__io.readFile(self.__mmcif, selectList=self.__exclude_category_list, excludeFlag=True)
                self.__mmcif_data = cList[0]
                return self.__mmcif_data
            except Exception as e:  # noqa: BLE001
                logger.error("failed to parse: %s error %s", self.__mmcif, str(e))

        return None

    def __get_category(self, category: str) -> Optional[DataCategory]:
        if not self.__mmcif_data:
            self.parse_mmcif()
        if self.__mmcif_data:
            dcObj = self.__mmcif_data.getObj(category)
            return dcObj
        return None

    def __get_category_keys(self, category: str) -> Dict[str, int]:
        """Returns a dictionary of attribute name and ordinal if category exists"""
        cat_dict = {}
        dcObj = self.__get_category(category)
        if dcObj is not None:
            keys_in_list_of_sets = dcObj.getAttributeListWithOrder()
            for key in keys_in_list_of_sets:
                cat_dict[key[0]] = key[1]
        return cat_dict

    def __get_category_list_of_dictionaries(self, category: str) -> List[Dict[str, str]]:
        return_list = []
        cat_items = self.__get_category_keys(category=category)
        cat_data = self.__get_category(category=category)
        if cat_data is not None:
            for row in range(len(cat_data.data)):
                row_dict = {}
                for item in cat_items:
                    value = cat_data.getValueOrDefault(attributeName=item, defaultValue="", rowIndex=row)
                    row_dict[item] = value
                return_list.append(row_dict)

        return return_list

    def __get_cat_item_values(self, category: str, item: str) -> List[str]:
        value_list = []
        cat = self.__get_category(category=category)
        if cat is not None:
            for row in range(len(cat.data)):
                value = cat.getValueOrDefault(attributeName=item, defaultValue="", rowIndex=row)
                value_list.append(value)

        return value_list

    def get_exp_methods(self) -> List[str]:
        return self.__get_cat_item_values(category="exptl", item="method")

    def get_associated_emdb(self) -> Optional[str]:
        """Returns the first 'associated EM volume' in pdbx_database_related"""
        emdb_ids = []
        ret = self.__get_category_list_of_dictionaries(category="pdbx_database_related")
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

    @overload
    def get_latest_modified_categories(
        self, content_type: None = None
    ) -> Tuple[List[str], Optional[str]]:  # fmt: skip
        ...

    @overload
    def get_latest_modified_categories(
        self, content_type: Literal["Structure model", "EM metadata"]
    ) -> Tuple[List[str], Optional[str], bool]:  # fmt: skip
        ...

    def get_latest_modified_categories(
        self, content_type: Optional[Literal["Structure model", "EM metadata"]] = None
    ) -> Union[Tuple[List[str], Optional[str]], Tuple[List[str], Optional[str], bool]]:
        """Returns the latet modified categories and ordinal associated with it for a given content type (Structure model or EM metadata)
        If content_type is None - returns True if no audit history present
        """
        latest_audit_ordinal: Optional[str] = None
        latest_audit_categories: List[str] = []
        latest_audit_revision: Optional[datetime.date] = None
        ret_no_audit = (
            True  # two or three arguments depending on content_type - if None - return True if no audit history
        )

        if content_type is None:
            content_type = "Structure model"  # default to structure model
            ret_no_audit = False

        ret = self.__get_category_list_of_dictionaries(category="pdbx_audit_revision_history")

        # We will determine the latest date as a reference and then find values for proper categories.  It is
        # possible that the coordinate file might be updated one week and not a map volume.
        if ret:
            # Get the latest revision date - as that is global
            for row in ret:
                revision_date = row.get("revision_date")  # Better be there

                if not revision_date:
                    continue
                rdate = _parsedate(revision_date)
                # if could not parse -- skip
                if not rdate:
                    continue
                if latest_audit_revision:
                    latest_audit_revision = max(latest_audit_revision, rdate)
                else:
                    latest_audit_revision = rdate

        if latest_audit_revision:
            # Now get the latest ordinal for this date matching the content type
            for row in ret:
                revision_date = row.get("revision_date")  # Better be there
                ordinal = row.get("ordinal")
                if not revision_date or not ordinal:
                    continue
                rdate = _parsedate(revision_date)
                if not rdate:
                    continue
                if rdate == latest_audit_revision and row.get("data_content_type") == content_type:
                    latest_audit_ordinal = ordinal
                    break

        if latest_audit_ordinal:
            logger.debug("latest audit ordinal: %s", latest_audit_ordinal)

            ret = self.__get_category_list_of_dictionaries(category="pdbx_audit_revision_category")
            if ret:
                for row in ret:
                    revision_ordinal = row.get("revision_ordinal")  # Better be there
                    category = row.get("category")
                    if category and revision_ordinal == latest_audit_ordinal:
                        latest_audit_categories.append(category)

        if ret_no_audit:
            return latest_audit_categories, latest_audit_ordinal, bool(not ret)
        return latest_audit_categories, latest_audit_ordinal

    def get_modified_items(self, ordinal: str) -> Dict[str, List[str]]:
        """Returns the dictionary of latet modified attributes for ordinal keyed on category name"""
        ret: Dict[str, List[str]] = {}
        cdata = self.__get_category_list_of_dictionaries(category="pdbx_audit_revision_item")

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
