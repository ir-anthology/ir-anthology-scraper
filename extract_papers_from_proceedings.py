import fitz
import bibtexparser
from glob import glob
from os.path import dirname, exists, sep
from os import makedirs

def get_page_count(pages):
    pages_split = pages.split("--")
    if len(pages_split) == 1:
        return 1
    else:
        return int(pages_split[1]) - int(pages_split[0])

def extract_known(directory, proceeding_pdf_filepaths, bibfile_paths):
    if bibfile_paths:
        bibfile_path = bibfile_paths[0]
    else:
        return 0
    with open(bibfile_path) as file:
        entries = [(entry["ID"], entry["title"], entry.get("doi", None), entry.get("pages")) for entry in bibtexparser.load(file).entries]

    entries = [(bibkey, title, doi, get_page_count(pages)) for bibkey, title, doi, pages in entries if doi and pages]

    entries_found = []

    for proceeding_pdf_filepath in proceeding_pdf_filepaths:
        with fitz.open(proceeding_pdf_filepath) as pdf:
            for page_number, page in enumerate(pdf.pages()):
                page_text = page.get_text().replace("\n", " ")
                for bibkey, title, doi, pages in entries:
                    doi = doi.replace("\\", "")
                    if doi in page_text and title in page_text:
                        entries_found.append([bibkey, title, doi, proceeding_pdf_filepath, page_number, page_number+pages])

    for bibkey, title, doi, proceeding_pdf_filepath, from_page, to_page in entries_found:
        with fitz.open(proceeding_pdf_filepath) as pdf:
            paper = fitz.open()
            paper.insert_pdf(pdf, from_page=from_page, to_page=to_page)
            filepath = directory + "/" + doi + ".pdf"
            if not exists(dirname(filepath)):
                makedirs(dirname(filepath))
            paper.save(filepath)

    return len(entries_found)


if __name__ == "__main__":

    directories = sorted(glob("../sources/proceedings-by-venue/spire/*") + glob("../sources/proceedings-by-venue/airs/*"))

    paper_count = 0

    for directory in directories:
        print(directory)
        directory_path_split = directory.split("/")
        venue, year = directory_path_split[-2:]
        paper_count += extract_known(directory,
                                     glob(directory + sep + "*-proceedings*.pdf"),
                                     glob("../conf" + sep + venue + sep + year + sep + "*.bib"))

    print(paper_count)
