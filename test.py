import bibtexparser
from getpass import getuser
from shutil import copyfile
from glob import glob
from os.path import dirname, exists, sep
from os import makedirs
from tqdm import tqdm

bibfilepaths = glob("/media/" + getuser() + "/Ceph/data-in-production/ir-anthology/pdfs/*/*/*.bib")
pdffilepaths = glob("/media/" + getuser() + "/Ceph/data-in-production/ir-anthology/sources/wlgc/papers-by-doi/*/*")

entry_count = 0
pdf_count = 0

for bibfilepath in tqdm(bibfilepaths, total=len(bibfilepaths)):
    with open(bibfilepath) as bibfile:
        entries = bibtexparser.load(bibfile).entries
        for entry in entries:
            entry_count += 1
            if "doi" in entry:
                pdf_src_path = "/media/" + getuser() + "/Ceph/data-in-production/ir-anthology/sources/wlgc/papers-by-doi/" + entry["doi"] + ".pdf"
                if exists(pdf_src_path):
                    copyfile(pdf_src_path, dirname(bibfilepath) + sep + entry["ID"] + ".pdf")
                    pdf_count += 1

print(pdf_count)
print(entry_count)
