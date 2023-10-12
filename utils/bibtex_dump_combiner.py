from json import loads, dumps
from os.path import exists

bibtex_dump_filepaths = ["/media/wolfgang/Data/Work/github/ir-anthology-scraper/output/2023-10-12/bibtex_dump.txt",
                         "/media/wolfgang/Data/Work/github/ir-anthology-scraper/output/2023-10-12 first run/bibtex_dump.txt"]

entries = {}

for bibtex_dump_filepath in bibtex_dump_filepaths:

    with open(bibtex_dump_filepath) as file:
        for line in file:
            url, bibtex = loads(line)
            if url not in entries:
                entries[url] = bibtex
            else:
                if bibtex != entries[url]:
                    print("Bibtex mismatch:", url)

print(len(entries))

if not exists("bibtex_dump.txt"):
    with open("bibtex_dump.txt", "w") as file:
        for url in sorted(entries.keys(),key = lambda url: url.split("/")[4]):
            file.write(dumps([url,entries[url]]) + "\n")
