class releaseFileNames:
    def __init__(self, gzip=False):
        self.gzip = gzip

    def add_gzip(self, filename, set_gzip=False):
        if set_gzip:
            self.gzip = True
        if self.gzip:
            return filename + ".gz"
        return filename

    def get_emdb_number(self, accession):
        return accession[4:]
        #return accession.split("-")[-1]

    def emdb_underscore_format(self, accession):
        return "emd_{}".format(self.get_emdb_number(accession))

    def emdb_hyphen_format(self, accession):
        return "emd-{}".format(self.get_emdb_number(accession))

    def get_model(self, accession, for_release=False):
        return accession + ".cif.gz"

    def get_structure_factor(self, accession, for_release=False):
        if for_release:
            return accession + "-sf.cif"
        return "r{}sf.ent.gz".format(accession)

    def get_chemical_shifts(self, accession, for_release=False):
        fname = "{}_cs.str".format(accession)
        if for_release:
            return fname
        return fname + '.gz'

    def get_emdb_xml(self, accession, for_release=False):
        if for_release:
            return self.add_gzip(self.emdb_underscore_format(accession) + "_v3.xml")
        return self.add_gzip(self.emdb_hyphen_format(accession) + "-v30.xml")

    def get_emdb_map(self, accession, for_release=False):
        return self.emdb_underscore_format(accession) + ".map.gz"

    def get_emdb_fsc(self, accession, for_release=False):
        return self.add_gzip(self.emdb_underscore_format(accession) + "_fsc.xml")

    def get_validation_pdf(self, accession, for_release=False):
        return self.add_gzip(accession + "_validation.pdf")

    def get_validation_full_pdf(self, accession, for_release=False):
        return self.add_gzip(accession + "_full_validation.pdf")

    def get_validation_xml(self, accession, for_release=False):
        return self.add_gzip(accession + "_validation.xml")

    def get_validation_png(self, accession, for_release=False):
        return self.add_gzip(accession + "_multipercentile_validation.png")

    def get_validation_svg(self, accession, for_release=False):
        return self.add_gzip(accession + "_multipercentile_validation.svg")

    def get_2fofc(self, accession, for_release=False):
        return self.add_gzip(accession + "_validation_2fo-fc_map_coef.cif")

    def get_fofc(self, accession, for_release=False):
        return self.add_gzip(accession + "_validation_fo-fc_map_coef.cif")

