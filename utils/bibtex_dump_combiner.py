from json import loads, dumps
from os.path import exists

bibtex_dump_filepaths = ["dblp_bibtex_cache1.txt",
                         "dblp_bibtex_cache2.txt"]

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

if not exists("dblp_bibtex_cache.txt"):
    with open("dblp_bibtex_cache.txt", "w") as file:
        for url in sorted(entries.keys(),key = lambda url: url.split("/")[4]):
            file.write(dumps([url,entries[url]]) + "\n")
