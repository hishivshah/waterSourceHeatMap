import sqlite3
import datetime

import ogr

# Catchments shapefile
catchmentsShp = "../data/2015-02-27/nrfa/NRFA Catchment Boundary Retrieval/NRFA Catchment Boundary Retrieval_Hishiv Shah.shp"
# Sqlite database
sqliteDb = "../results/2014-12-10.sqlite"

# Read catchments shapefile
dataSource = ogr.Open(catchmentsShp)
layer = dataSource.GetLayer()

# Connect to output database
db = sqlite3.connect(sqliteDb)
try:
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
