from wwpdb.apps.validation.src.scripts.star_to_cif import starToPdbx

def convert_star_to_cif(star_file, cif_file):
    return starToPdbx(starPath=star_file, pdbxPath=cif_file)