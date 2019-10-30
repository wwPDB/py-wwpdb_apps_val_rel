class releaseFileNames():

    def __init__(self, gzip=False):
        self.gzip = gzip

    def add_gzip(self, filename, set_gzip=False):
        if set_gzip:
            self.gzip = True
        if self.gzip:
            return  filename + ".gz"
        return filename

    def get_model(self, accession):
        return self.add_gzip(accession + '.cif', set_gzip=True)

    def get_structure_factor(self, accession, for_release=False):
        if for_release:
            return accession + '-sf.cif'
        return self.add_gzip('r{}sf.ent'.format(accession), set_gzip=True)

    def get_chemical_shifts(self, accession, for_release=False):
        fname = '{}_cs.str'.format(accession)
        if for_release:
            return fname
        return self.add_gzip(fname, set_gzip=True)

    def get_emdb_xml(self, accession, for_release=False):
        if for_release:
            return self.add_gzip(accession + '_v3.xml')
        return self.add_gzip(accession + "-v30.xml")

    def get_emdb_map(self, accession):
        return self.add_gzip(accession + ".map", set_gzip=True)

    def get_emdb_fsc(self, accession):
        return self.add_gzip(accession + "_fsc.xml")

    def get_validation_pdf(self, accession):
        return self.add_gzip(accession + "_validation.pdf")
    
    def get_validation_full_pdf(self, accession):
        return self.add_gzip(accession + "_full_validation.pdf")

    def get_validation_xml(self, accession):
        return self.add_gzip(accession + "_validation.xml")

    def get_validation_png(self, accession):
        return self.add_gzip(accession + "_multipercentile_validation.png")

    def get_validation_svg(self, accession):
        return self.add_gzip(accession + "_multipercentile_validation.svg")

    def get_2fofc(self, accession):
        return self.add_gzip(accession + "_validation_2fo-fc_map_coef.cif")

    def get_fofc(self, accession):
        return self.add_gzip(accession + "_validation_fo-fc_map_coef.cif")

