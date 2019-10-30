class releaseFileNames():

    def __init__(self, accession, gzip=False):
        self.gzip = gzip
        self.accession = accession

    def get_model(self):
        return self.accession + '.cif'

    def get_structure_factor(self):
        return 'r{}sf.ent'.format(self.accession)

    def get_validation_pdf(self):
        return self.accession + "_validation.pdf"
    
    def get_validation_full_pdf(self):
        return self.accession + "_full_validation.pdf"

    def get_validation_xml(self):
        return self.accession + "_validation.xml"

    def get_validation_png(self):
        return self.accession + "_multipercentile_validation.png"

    def get_validation_svg(self):
        return self.accession + "_multipercentile_validation.svg"

    def get_2fofc(self):
        return self.accession + "_validation_2fo-fc_map_coef.cif"

    def get_fofc(self):
        return self.accession + "_validation_fo-fc_map_coef.cif"

