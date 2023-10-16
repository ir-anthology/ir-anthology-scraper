import bibtexparser
from getpass import getuser
from glob import glob
from os.path import exists
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
                if exists("/media/" + getuser() + "/Ceph/data-in-production/ir-anthology/sources/wlgc/papers-by-doi/" + entry["doi"] + ".pdf"):
                    print(bibfilepath)
                    print("/media/" + getuser() + "/Ceph/data-in-production/ir-anthology/sources/wlgc/papers-by-doi/" + entry["doi"] + ".pdf")
                    input()
                    pdf_count += 1

print(pdf_count)
print(entry_count)
