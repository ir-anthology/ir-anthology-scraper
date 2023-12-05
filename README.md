# IR-Anthology Scraper

This repository provides code to scrape dblp and download bibtex files for given venues and years.

The scraper requires a config file of the below format:

{"venuetype":"conf","venues":{"sigir":[1971],"www":[2021,2023]}}

venuetype can be either 'conf' or 'journals'.

The scraper will save the bibtex files to the output directory following the below structure:

output/[venuetype]/[venue]/[year]/venuetype-venue-year.bib

Running the scraper with the above config file will generate the following output:

└── conf<br>
              ├── dblp_bibtex_cache.txt<br>
              ├── _logs<br>
              │        └── 2023_12_05_16_57_34<br>
              │                    ├── config.json<br>
              │                    ├── dblp_json_results.csv<br>
              │                    └── log.txt<br>
              └── sigir<br>
              │        └── 1971<br>
              │                               └── conf-sigir-1971.bib<br>
              └── www<br>
                       ├── 2021<br>
                       │                      └── conf-www-2021.bib<br>
                       └── 2023<br>
                                              └── conf-www-2023.bib<br>

dblp_bibtex_cache.txt is a JSON lines document containing all bibtex strings successfully scraped from dblp, e.g.

`["https://dblp.org/rec/conf/sigir/C71", "@inproceedings{DBLP:conf/sigir/C71,\n..."]`

Each line is a list of two elements, the first one being a URL to the entry on dblp, the second being the bibtex string.

_logs contains a copy of the config.json with which the process was run, a simple log (log.txt) of the scraping process including any exceptions raised, and an overview of the number of JSON entries scraped from the dblp API (dblp_json_results.csv, e.g. `sigir,1971,21`).

### main.py

- main entry point

### test.sh

- shell script to run tests; run as `./test.sh`

### scripts

- dblp/entry_scraper.py: scrape JSON entries from the dblp API
- dblp/bibtex_scraper.py: scrape bibtex for JSON entries from the dblp page
- logger.py: a simple custom logger
- scraper.py: wrapper for scraping process

### tests

- test_entry_scraper.py: tests for dblp/entry_scraper.py
- test_bibtex_scraper.py: tests for dblp/bibtex_scraper.py
- test_scraper.py: tests for scraper.py

### utils

- utils.py: string conversion and GET request utility functions
- bibtex_dump_combiner.py: helper function to combine bibtex cache files
