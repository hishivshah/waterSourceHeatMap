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

import pyodbc
import sqlite3
import os
from datetime import datetime

# Connect to input Access database
mdb = "../data/2014-11-04/waterTempArchive/EA_WaterTempArchive_WA.mdb"
drv = "{Microsoft Access Driver (*.mdb, *.accdb)}"
dbIn = pyodbc.connect("Driver=%s;Dbq=%s" % (drv, mdb))
curIn = dbIn.cursor()

# Connect to output sqlite database
outDir = "../results"
outFile = os.path.join(outDir,
                     "%s.sqlite" % datetime.now().strftime("%Y-%m-%dT%H%M"))
dbOut = sqlite3.connect(outFile)
dbOut.enable_load_extension(True)
dbOut.load_extension("mod_spatialite")
curOut = dbOut.cursor()
curOut.execute("SELECT InitSpatialMetaData(1);")

# Create tables
curOut.execute("""CREATE TABLE sites (
                  siteId TEXT PRIMARY KEY,
                  siteName TEXT,
                  operatorCode TEXT,
                  siteType TEXT,
                  siteComment TEXT,
                  startDate TEXT,
                  endDate TEXT,
                  dataCount INTEGER,
                  detCode INTEGER,
                  sourceCode INTEGER);""")
curOut.execute("SELECT AddGeometryColumn ('sites', 'geom', 27700, 'POINTZ');")
curOut.execute("""CREATE TABLE temperatures (
                  siteId TEXT,
                  year TEXT,
                  month TEXT,
                  detCode INTEGER,
                  meanTemp REAL,
                  sourceCode TEXT,
                  FOREIGN KEY(siteId) REFERENCES sites(siteId));""")

# Read in sites data
curIn.execute("""SELECT s.*,
                 m.startDate,
                 m.endDate,
                 m.dataCount,
                 m.detCode,
                 m.sourceCode
                 FROM tbl_siteInfo s, tbl_metaData m
                 WHERE s.siteID = m.siteID
                 AND m.EA_REGION = 'WA';""")

# Insert sites data into sqlite table
for r in curIn:
    curOut.execute("""INSERT INTO sites VALUES
                      (?,?,?,?,?,?,?,?,?,?, MakePointZ(?,?,?, 27700));""",
                   (r.siteID,
                    r.siteName,
                    r.operatorCode,
                    r.siteType,
                    r.siteComment,
                    r.startDate,
                    r.endDate,
                    r.dataCount,
                    r.detCode,
                    r.sourceCode,
                    r.siteX,
                    r.siteY,
                    r.siteZ))

# Read in temerature data
curIn.execute("""SELECT d.siteID,
                 YEAR(d.sampleDate) AS year,
                 MONTH(d.sampleDate) AS month,
                 d.detCode,
                 avg(d.detResult) as meanTemp,
                 d.sourceCode
                 FROM data0 d
                 INNER JOIN
                 (SELECT s.siteID, m.sourceCode
                 FROM tbl_siteInfo AS s, tbl_metadata AS m
                 WHERE s.siteID = m.siteID
                 AND m.EA_REGION = 'WA') a
                 ON a.siteID = d.siteID
                 AND a.sourceCode = d.sourceCode
                 GROUP BY d.siteID,
                 YEAR(d.sampleDate),
                 MONTH(d.sampleDate),
                 d.detCode,
                 d.sourceCode;""")

# Insert temperature data into sqlite table
for r in curIn:
    curOut.execute("INSERT INTO temperatures VALUES (?, ?, ?, ?, ?, ?);", r)

# Close Access database connection
dbIn.close()

# Commit changes and close sqlite connection
dbOut.commit()
dbOut.close()
