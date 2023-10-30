import fitz
from os.path import exists
from os import makedirs
from re import findall, search
from pprint import pprint

doi_regex = "10\.\d{4,9}/[-\._;\(\)/:a-zA-Z0-9]+"

def run(pdfpath, contentstart, contentend, documentend, offset = 0):

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

def run_no_contents(pdfpath, contentstart, contentend, documentend, offset):

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

if __name__ == "__main__":

    #run("chiir23-proceedings.pdf", 7, 12, 519, 20)
    #run_no_contents("chiir23-proceedings.pdf", 7, 12, 519, 20)
    
    #run("ecir23-proceedings-part-2.pdf", 22, 27, 727)
    #run_no_contents("ecir23-proceedings-part-2.pdf", 22, 27, 727)

    run_no_contents("adcs22-proceedings.pdf", 7, 12, 48, 20)
    
