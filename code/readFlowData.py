""" Reads in data from Gauged Monthly Flow csv files. Outputs to sqlite
    database. """

# The MIT License (MIT) 

# Copyright (c) 2014 Hishiv Shah 

# Permission is hereby granted, free of charge, to any person obtaining a 
# copy of this software and associated documentation files (the 
# "Software"), to deal in the Software without restriction, including 
# without limitation the rights to use, copy, modify, merge, publish, 
# distribute, sublicense, and/or sell copies of the Software, and to 
# permit persons to whom the Software is furnished to do so, subject to 
# the following conditions: 

# The above copyright notice and this permission notice shall be included 
# in all copies or substantial portions of the Software. 

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS 
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF 
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. 
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY 
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, 
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE 
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import csv
import collections
import os
import glob
import datetime
import sqlite3

def readGmfCsv(gmfCsv):
    """ Read in Gauged Monthly Flows csv file. Returns dictionaries of
        data and metadata."""

    d = collections.defaultdict(dict)
    with open(gmfCsv, "rb") as f:
        reader = csv.reader(f)
        for row in reader:
            if row[0] in ("file", "database", "station", "dataType", "data"):
                d[row[0]].update({row[1] : row[2]})
            else:
                d["gmf"].update({row[0] : row[1]})

    return d

if __name__ == "__main__":

    # Input paths
    csvDir  = "../data/2014-10-29/nrfa/NRFA Flow Data Retrieval"

    # Output paths
    outDir = "../results"
    outDb = os.path.join(outDir,
                         "%s.sqlite" \
                         % datetime.datetime.now().strftime("%Y-%m-%dT%H%M"))

    # Connect to output database
    db = sqlite3.connect(outDb)
    db.enable_load_extension(True)
    db.load_extension("mod_spatialite")
    cur = db.cursor()
    cur.execute("SELECT InitSpatialMetaData(1);")

    # Create tables
    cur.execute("""CREATE TABLE IF NOT EXISTS stations (
                   id INTEGER PRIMARY KEY,
                   name TEXT,
                   gridReference TEXT,
                   stationComment TEXT,
                   catchmentComment TEXT);""")
    cur.execute("""CREATE TABLE IF NOT EXISTS dataTypes (
                   id TEXT PRIMARY KEY ON CONFLICT IGNORE,
                   name TEXT,
                   parameter TEXT,
                   units TEXT,
                   period TEXT,
                   measurementType TEXT);""")
    cur.execute("""CREATE TABLE IF NOT EXISTS data (
                   station INTEGER,
                   dataType TEXT,
                   first TEXT,
                   last TEXT,
                   FOREIGN KEY(station) REFERENCES stations(id),
                   FOREIGN KEY(dataType) REFERENCES dataTypes(id));""")
    cur.execute("""CREATE TABLE IF NOT EXISTS gmf (
                   station INTEGER,
                   dataType TEXT,
                   month TEXT,
                   flow REAL,
                   FOREIGN KEY(station) REFERENCES stations(id),
                   FOREIGN KEY(dataType) REFERENCES dataTypes(id));""")


    # Read data from csv files
    for csvFile in glob.iglob(os.path.join(csvDir, "*.csv")):
        data = readGmfCsv(csvFile)

        # Insert data into tables
        cur.execute("""INSERT INTO stations VALUES (?, ?, ?, ?, ?);""",
                    (data["station"].get("id"),
                     data["station"].get("name"),
                     data["station"].get("gridReference"),
                     data["station"].get("stationComment"),
                     data["station"].get("catchmentComment")))
        cur.execute("""INSERT INTO dataTypes VALUES (?, ?, ?, ?, ?, ?);""",
                    (data["dataType"].get("id"),
                     data["dataType"].get("name"),
                     data["dataType"].get("parameter"),
                     data["dataType"].get("units"),
                     data["dataType"].get("period"),
                     data["dataType"].get("measurementType")))
        cur.execute("""INSERT INTO data VALUES (?, ?, ?, ?);""",
                    (data["station"].get("id"),
                     data["dataType"].get("id"),
                     data["data"].get("first"),
                     data["data"].get("last")))
        cur.executemany("""INSERT INTO gmf VALUES (?, ?, ?, ?);""",
                    [(data["station"].get("id"),
                      data["dataType"].get("id"),
                      k,
                      v)
                     for k, v in data["gmf"].iteritems()])

    # Commit changes and close database
    db.commit()
    db.close()
