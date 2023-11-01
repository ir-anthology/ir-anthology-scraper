import fitz
import bibtexparser
from glob import glob
from os.path import dirname, exists, sep
from os import makedirs
from re import findall, search
from pprint import pprint

doi_regex = "10\.\d{4,9}/[-\._;\(\)/:a-zA-Z0-9]+"

def extract_with_contents(pdfpath, contentstart, contentend, documentend, offset = 0):

    with fitz.open(pdfpath) as pdf:

        page_numbers_of_papers = set()
        
        for page in pdf.pages(contentstart - 1, contentend):
            for link in page.get_links():
                if "page" in link:
                    page_numbers_of_papers.add(link["page"])

        if page_numbers_of_papers == set():
            for page in pdf.pages(contentstart - 1, contentend):
                page_lines = page.get_text().split("\n")
                for line in page_lines:
                    numbers = [item for item in findall("\d*", line) if item]
                    for number in numbers[::-1]:
                        if line.strip().endswith(number):
                            page_number = int(number) + offset - 1
                            page_numbers_of_papers.add(page_number)
                            break

        page_numbers_of_papers = sorted(page_numbers_of_papers) + [documentend]
        
        papers = []
        for index in range(len(page_numbers_of_papers) - 1):
            text_of_first_page = pdf.get_page_text(page_numbers_of_papers[index])
            dois = findall(doi_regex, text_of_first_page)
            if dois:
                doi = max(dois, key = lambda doi: len(doi))
                papers.append([page_numbers_of_papers[index],
                               page_numbers_of_papers[index + 1],
                               doi])                           

        for index in range(len(papers)):
            print(papers[index])
            paper = fitz.open()
            paper.insert_pdf(pdf, from_page=papers[index][0], to_page=papers[index][1] - 1)
            prefix = papers[index][2].split("/")[0]
            if not exists(prefix):
                makedirs(prefix)
            paper.save(papers[index][2] + ".pdf")

def extract_without_contents(pdfpath, contentstart, contentend, documentend, offset):

    with fitz.open(pdfpath) as pdf:

        papers = []

        for index, page in enumerate(pdf.pages()):
            page_text = page.get_text()
            if "abstract" in page_text.lower() and "introduction" in page_text.lower():
                dois = findall(doi_regex, page_text)
                if dois:
                    doi = max(dois, key = lambda doi: len(doi))
                    if papers == []:
                        papers.append([index, doi])
                    else:
                        papers[-1].insert(1, index)
                        papers.append([index, doi])

        papers[-1].insert(1, documentend)
        for paper in papers:
            print(paper)

def extract_known(directory, proceedings_pdfs, paper_bib):
    with open(paper_bib) as file:
        entries = [(entry["ID"], entry["title"], entry.get("doi", None), entry.get("pages")) for entry in bibtexparser.load(file).entries]

    entries = [(bibkey, title, doi, int(pages.split("--")[1]) - int(pages.split("--")[0])) for bibkey, title, doi, pages in entries if doi and pages]

    entries_found = []

    for proceedings_pdf in proceedings_pdfs:
        with fitz.open(proceedings_pdf) as pdf:
            for page_number, page in enumerate(pdf.pages()):
                page_text = page.get_text().replace("\n", " ")
                for bibkey, title, doi, pages in entries:
                    doi = doi.replace("\\", "")
                    if doi in page_text and title in page_text:
                        entries_found.append([bibkey, title, doi, proceedings_pdf, page_number, page_number+pages])

    for bibkey, title, doi, proceedings_pdf, from_page, to_page in entries_found:
        with fitz.open(proceedings_pdf) as pdf:
            paper = fitz.open()
            paper.insert_pdf(pdf, from_page=from_page, to_page=to_page)
            filepath = directory + "/" + doi + ".pdf"
            if not exists(dirname(filepath)):
                makedirs(dirname(filepath))
            paper.save(filepath)

    return len(entries_found)


if __name__ == "__main__":

    #run("chiir23-proceedings.pdf", 7, 12, 519, 20)
    #run_no_contents("chiir23-proceedings.pdf", 7, 12, 519, 20)
    
    #run("ecir23-proceedings-part-2.pdf", 22, 27, 727)
    #run_no_contents("ecir23-proceedings-part-2.pdf", 22, 27, 727)

    #run_no_contents("adcs22-proceedings.pdf", 7, 12, 48, 20)

    directories = glob("resources/*/*")

    paper_count = 0

    for directory in directories:
        root, venue, year = directory.split("/")    
        paper_count += extract_known(directory,
                                     glob(directory + sep + "*-proceedings*.pdf"),
                                     glob(directory + sep + "*.bib")[0])

    print(paper_count)
