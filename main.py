from os.path import dirname, exists, sep
from os import makedirs
from shutil import copyfile
from json import load

from scripts.scraper import Scraper


if __name__ == "__main__":

    venuetype = "conf"
    output_directory = "output"
    config_filepath = "config.json"
    bibtex_cache_filepath = None#"output/conf/dblp_bibtex_cache.txt"

    with open(config_filepath) as file:
        config = load(file)
        assert venuetype == config["venuetype"]

    scraper = Scraper(venuetype, output_directory, bibtex_cache_filepath)

    copyfile(config_filepath, scraper.logger.logger_directory + sep + "config.json")

    for venue, years in config["venues"].items():

        for year in years:

            entry_list, bibtex_list = scraper.scrape_entries_and_bibtex(venue, year)
            
            if entry_list:
                bibtex_string = scraper.generate_bibtex_string(entry_list, bibtex_list)

                bib_filepath = sep.join([output_directory,
                                         venuetype,
                                         venue,
                                         str(year),
                                         (venuetype + "-" + venue + "-" + str(year) + ".bib")])

                if not exists(dirname(bib_filepath)):
                    makedirs(dirname(bib_filepath))
                if exists(bib_filepath):
                    print("Bibtex file for venue " + venue + " and year " + str(year) + " already exists!")
                else:
                    with open(bib_filepath, "w") as file:
                        file.write(bibtex_string)
