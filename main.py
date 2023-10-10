from argparse import ArgumentParser
from scripts.dblp_scraper import DBLPscraper
from os.path import dirname, exists, sep
from os import makedirs
from json import dumps, loads, load
from tqdm import tqdm
import traceback

def write_bibtex_string_to_file(bibtex_string, output_filepath):
    with open(output_filepath, "w") as file:
        file.write(bibtex_string)


if __name__ == "__main__":


    with open("config.json") as file:
        config = load(file)

    bibtex_dump = {}
    if exists("bibtex_dump.txt"):
        with open("bibtex_dump.txt") as file:
            for line in file:
                url, bibtex = loads(line)
                bibtex_dump[url] = bibtex
        
    scraper = DBLPscraper("output")

    for conference, years in config.items():

        for year in years:

            try:
                entry_list = scraper.scrape_conference(conference, year)
                print("Scraping bibtex entries...")
                bibtex_list = []
                for entry in tqdm(entry_list, total=len(entry_list)):
                    try:
                        bibtex_list.append(bibtex_dump[entry["info"]["url"]])
                    except KeyError:
                        bibtex = scraper.scrape_bibtex(entry)
                        with open("bibtex_dump.txt", "a") as file:
                            file.write(dumps([entry["info"]["url"],bibtex]) + "\n")
                        bibtex_list.append(bibtex)
                bibtex_string = scraper.generate_bibtex_string(entry_list, bibtex_list)

                write_bibtex_string_to_file(bibtex_string, scraper.output_directory + sep + conference + "-" + str(year) + ".txt")
            except:
                scraper.log(traceback.format_exc())

        scraper.log("="*100)
