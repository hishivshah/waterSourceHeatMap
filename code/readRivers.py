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

def readRivers(riversShp, clipper):
    '''Read riverlines from shapefile, output data as list of tuples.'''

    dataSource = ogr.Open(riversShp)
    layer = dataSource.GetLayer()
    layer.SetSpatialFilter(ogr.CreateGeometryFromWkt(clipper))
    layer.SetAttributeFilter("CODE IN (6223, 6224, 6225, 6230, 6232)")

    data = []
    for feature in layer:
        code = feature.GetField("CODE")
        identifier = feature.GetField("IDENTIFIER")
        name = feature.GetField("NAME")
        geom = feature.GetGeometryRef().ExportToWkt()
        data.append((code, identifier, name, geom))

    return data

if __name__ == "__main__":    

    # Inputs
    riversShp = "../data/2014-11-14/meridian2_national_653496/river_polyline.shp"
    clipperWkt = "../results/clipper.wkt"

    # Outputs
    sqliteDb = "../results/2014-11-24.sqlite"

    # Read in clipper
    with open(clipperWkt, "r") as f:
        clipper = f.read()

    # Read in rivers
    rivers = readRivers(riversShp, clipper)

# Connect to output database
try:
    db = sqlite3.connect(sqliteDb)
    db.enable_load_extension(True)
    db.load_extension("spatialite")
    cur = db.cursor()
    cur.execute("SELECT InitSpatialMetaData(1);")

    # Create temp table
    cur.execute("DROP TABLE IF EXISTS osRiversTmp;")
    cur.execute("""CREATE TABLE osRiversTmp (code INTEGER,
                                           id TEXT,
                                           name TEXT);""")
    cur.execute("""SELECT AddGeometryColumn('osRiversTmp',
                                            'geom',
                                            27700,
                                            'LINESTRING');""")
    # Insert features
    cur.executemany("""INSERT INTO osRiversTmp (code, id, name, geom)
                       VALUES (?, ?, ?, GeomFromText(?, 27700));""",
                    rivers)
    
    # Create final table
    cur.execute("DROP TABLE IF EXISTS osRivers;")
    cur.execute("""CREATE TABLE osRivers (code INTEGER,
                                        id TEXT PRIMARY KEY,
                                        name TEXT);""")
    cur.execute("""SELECT AddGeometryColumn('osRivers',
                                            'geom',
                                            27700,
                                            'LINESTRING');""")
    cur.execute("""INSERT INTO osRivers
                   SELECT code, id, name, ST_LineMerge(ST_Union(geom)) AS geom
                   FROM osRiversTmp
                   GROUP BY id;""")

    # Drop temp table
    cur.execute("DROP TABLE osRiversTmp;")
    
finally:
    # Commit changes
    db.commit()
    # Close database
    db.close()

