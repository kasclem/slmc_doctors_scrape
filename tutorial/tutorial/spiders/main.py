from scrapy import cmdline
import os

FILE_NAME = "doctors.json"
#have to remove because python appends if existing
try:
    os.remove(FILE_NAME)
except FileNotFoundError:
    pass
f = open(FILE_NAME, "w")
f.close()
cmdline.execute(("scrapy crawl doctors -o "+FILE_NAME).split())
