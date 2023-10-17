import bibtexparser
from getpass import getuser
from datetime import datetime
from shutil import copyfile
from glob import glob
from os.path import dirname, exists, sep
from csv import writer
from os import makedirs
from tqdm import tqdm

ir_anthology_root = "../" #"/media/" + getuser() + "/Ceph/data-in-production/ir-anthology/"

now = datetime.now()
start = (str(now.year) + "-" + str(now.month) + "-" + (str(now.day).rjust(2,"0")) + "_" +
         str(now.hour) + "-" + str(now.minute))

venuetype = ["conferences","journals"][1]

log_file_path = "copy_pdfs_" + venuetype + "_" + start + ".csv"

bibfilepaths = sorted(glob(ir_anthology_root + venuetype + "/*/*/*.bib"))

entry_count = 0
pdf_count = 0

DRY_RUN = True

# CSV FORMAT: VENUE, YEAR, BIBKEY, DOI, WLGC, WCSP15

for bibfilepath in tqdm(bibfilepaths, total=len(bibfilepaths)):
    with open(bibfilepath) as bibfile:
            
        entries = bibtexparser.load(bibfile).entries
        
        for entry in entries:
            entry_count += 1

            ID = entry["ID"].split("-", 2)
            
            venue = ID[0]
            year = ID[1]
            
            pdf_dst_path = dirname(bibfilepath) + sep + entry["ID"] + ".pdf"
                
            if "doi" in entry:
                
                pdf_src_path_wlgc = ir_anthology_root + "sources/wlgc/papers-by-doi/" + entry["doi"] + ".pdf"
                
                if exists(pdf_src_path_wlgc):
                    wlgc = True
                    if not exists(pdf_dst_path):
                        if not DRY_RUN:
                            copyfile(pdf_src_path_wlgc, pdf_dst_path)
                else:
                    wlgc = False

                if True in [wlgc]:
                    pdf_count += 1
                    
                with open(log_file_path, "a") as csv_file:
                    csv_writer = writer(csv_file, delimiter=",")
                    csv_writer.writerow([entry_count, venue, year, entry["ID"], entry["doi"], "wlgc" if wlgc else "", ""])
            else:
                with open(log_file_path, "a") as csv_file:
                    csv_writer = writer(csv_file, delimiter=",")
                    csv_writer.writerow([entry_count, venue, year, entry["ID"], "", "", ""])
                        
with open("copy_pdfs_" + venuetype + "_" + start + ".txt", "w") as logfile:
    logfile.write("\nPDFs: " + str(pdf_count) + "\n")
    logfile.write("PDFs: " + str(entry_count) + "\n")
