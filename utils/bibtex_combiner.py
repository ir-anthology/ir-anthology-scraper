import bibtexparser
from glob import glob
from tqdm import tqdm

bibfilepaths = glob("pdfs/*/*/*.bib")

with open("ir-anthology.bib", "w") as file:
    for bibfilepath in tqdm(bibfilepaths, total=len(bibfilepaths)):
        with open(bibfilepath) as bibfile:
            file.write("".join(bibfile.readlines()) + "\n\n\n")


