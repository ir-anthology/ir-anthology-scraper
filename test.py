import bibtexparser
from getpass import getuser
from shutil import copyfile
from glob import glob
from os.path import dirname, exists, sep
from os import makedirs
from tqdm import tqdm

bibfilepaths = glob("/media/" + getuser() + "/Ceph/data-in-production/ir-anthology/pdfs/civr/*/*.bib")
pdffilepaths = glob("/media/" + getuser() + "/Ceph/data-in-production/ir-anthology/sources/wlgc/papers-by-doi/*/*")

entry_count = 0
pdf_count = 0

for bibfilepath_count, bibfilepath in enumerate(bibfilepaths, 1):
    with open(bibfilepath) as bibfile:
        with open("log.txt", "a") as logfile:
            logfile.write("/".join(bibfilepath.split("/")[-3:-1]) + "\n")
        entries = bibtexparser.load(bibfile).entries
        for entry in entries:
            entry_count += 1
            if "doi" in entry:
                pdf_src_path = "/media/" + getuser() + "/Ceph/data-in-production/ir-anthology/sources/wlgc/papers-by-doi/" + entry["doi"] + ".pdf"
                if exists(pdf_src_path):
                    pdf_dst_path = dirname(bibfilepath) + sep + entry["ID"] + ".pdf"
                    copyfile(pdf_src_path, pdf_dst_path)
                    pdf_count += 1
                    with open("log.txt", "a") as logfile:
                        logfile.write("   - " + entry["ID"] + ".pdf" + "\n")
                        
with open("log.txt", "a") as logfile:
    logfile.write("PDFs: " + str(pdf_count) + "\n")
    logfile.write("PDFs: " + str(entry_count) + "\n")
