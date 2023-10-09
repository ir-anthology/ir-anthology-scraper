from argparse import ArgumentParser
from scripts.dblp_scraper import DBLPscraper
from os.path import dirname, exists, sep
from os import makedirs
from json import load
from tqdm import tqdm
import traceback

def write_bibtex_string_to_file(bibtex_string, output_filepath):
    with open(output_filepath, "w") as file:
        file.write(bibtex_string)


if __name__ == "__main__":


    with open("config.json") as file:
        config = load(file)

        
    scraper = DBLPscraper("output")

    for conference, years in config.items():

        for year in years:

            try:
                entry_list = scraper.scrape_conference(conference, year)
                print("Scraping bibtex entries...")
                bibtex_list = []
                for entry in tqdm(entry_list, total=len(entry_list)):
                    bibtex_list.append(scraper.scrape_bibtex(entry))
                bibtex_string = scraper.generate_bibtex_string(entry_list, bibtex_list)

                write_bibtex_string_to_file(bibtex_string, scraper.output_directory + sep + conference + "-" + str(year) + ".txt")
            except:
                scraper.log(traceback.format_exc())

        scraper.log("="*100)
