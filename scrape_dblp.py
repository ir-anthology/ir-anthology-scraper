from os.path import exists, sep
from os import makedirs
from shutil import copyfile
from json import dump, load
from tqdm import tqdm
import traceback

from scripts.dblp_logger import DBLPLogger
from scripts.dblp_bibtex_scraper import DBLPBibtexScraper
from scripts.dblp_entry_scraper import DBLPEntryScraper


if __name__ == "__main__":

    venuetype = "conf"
    output_directory = "output"
    config_filepath = "config.json"
    bibtex_cache_filepath = None#"output/conf/dblp_bibtex_cache.txt"

    with open(config_filepath) as file:
        config = load(file)
        assert venuetype == config["venuetype"]

    dblp_logger = DBLPLogger(output_directory)
    dblp_entry_scraper = DBLPEntryScraper(venuetype, output_directory, dblp_logger)
    dblp_bibtex_scraper = DBLPBibtexScraper(venuetype, output_directory, dblp_logger, bibtex_cache_filepath)

    copyfile(config_filepath, dblp_logger.logger_directory + sep + "config.json")
        
    fails = {}

    for venue, years in config["venues"].items():

        for year in years:

            try:
                print("Scraping bibtex entries of " + venue + " " + str(year) + "...")
                entry_list = dblp_entry_scraper.scrape_entries(venue, year)

                if entry_list != []:
                    bibtex_list = [dblp_bibtex_scraper.scrape_bibtex(entry) for entry in tqdm(entry_list, total=len(entry_list))]
                    bibtex_string = dblp_bibtex_scraper.generate_bibtex_string(entry_list, bibtex_list)

                    venue_year_directory = dblp_bibtex_scraper.output_directory + sep + venue + sep + str(year)
                    bib_filepath = venue_year_directory + sep + venuetype + "-" + venue + "-" + str(year) + ".bib"

                    if not exists(venue_year_directory):
                        makedirs(venue_year_directory)
                    if exists(bib_filepath):
                        print("Bibtex file for venue " + venue + " and year " + str(year) + " already exists!")
                    else:
                        with open(bib_filepath, "w") as file:
                            file.write(bibtex_string)

            except:
                dblp_logger.log(traceback.format_exc())
                with open(dblp_logger.output_directory + sep + "failed.json", "w") as file:
                    if venue not in fails:
                        fails[venue] = []
                    fails[venue].append(year)
                    dump({"venuetype":venuetype,"venues":fails}, file)

        dblp_logger.log("="*100)
