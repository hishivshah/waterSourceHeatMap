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

import ogr
import sqlite3
import datetime

# Catchments shapefile
catchmentsShp = "../data/2014-11-14/nrfa/NRFA Catchment Boundary Retrieval/NRFA Catchment Boundary Retrieval_Hishiv Shah.shp"
# Sqlite database
sqliteDb = "../results/2014-11-25.sqlite"

# Read catchments shapefile
dataSource = ogr.Open(catchmentsShp)
layer = dataSource.GetLayer()

# Connect to output database
try:
    db = sqlite3.connect(sqliteDb)
    db.enable_load_extension(True)
    db.load_extension("spatialite")
    cur = db.cursor()
    cur.execute("SELECT InitSpatialMetaData(1);")

    # Create table
    cur.execute("DROP TABLE IF EXISTS nrfaCatchments;")
    cur.execute("""CREATE TABLE nrfaCatchments (
                   id INTEGER PRIMARY KEY,
                   exported TEXT,
                   source TEXT,
                   version REAL);""")
    cur.execute("""SELECT AddGeometryColumn(
                   'nrfaCatchments',
                   'geom',
                   27700,
                   'POLYGON');""")

    # Insert features into table
    for feature in layer:
        _id = feature.GetField("ID")
        exported = datetime.datetime.strptime(feature.GetField("EXPORTED"),
                                              "%Y/%m/%d").date().isoformat()
        source = feature.GetField("SOURCE")
        version = feature.GetField("VERSION")
        geom = feature.GetGeometryRef().ExportToWkt()

        cur.execute("""INSERT INTO nrfaCatchments
                       (id, exported, source, version, geom)
                       VALUES (?, ?, ?, ?, GeomFromText(?, 27700));""",
                    (_id, exported, source, version, geom))

    # Create spatial index
    cur.execute("SELECT CreateSpatialIndex('nrfaCatchments', 'geom');")

finally:
    # Commit changes
    db.commit()
    # Close database
    db.close()

