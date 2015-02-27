import os
import sqlite3

import pyodbc

# Connect to input Access database
mdb = "../data/2015-02-27/waterTempArchive/EA_WaterTempArchive_WA.mdb"
drv = "{Microsoft Access Driver (*.mdb, *.accdb)}"
dbIn = pyodbc.connect("Driver=%s;Dbq=%s" % (drv, mdb))
try:

    # Connect to output sqlite database
    outFile = "../results/2014-12-03.sqlite"
    dbOut = sqlite3.connect(outFile)
    try:
        dbOut.enable_load_extension(True)
        dbOut.load_extension("spatialite")
        dbOut.execute("SELECT InitSpatialMetaData(1);")

        # Create cursors
        curIn = dbIn.cursor()
        curOut = dbOut.cursor()

        # Create tables
        curOut.execute("DROP TABLE IF EXISTS eaSites;")
        curOut.execute("""CREATE TABLE eaSites (
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
        curOut.execute("""SELECT AddGeometryColumn ('eaSites',
                                                    'geom',
                                                    27700,
                                                    'POINT');""")

        curOut.execute("DROP TABLE IF EXISTS eaTemperatures;")
        curOut.execute("""CREATE TABLE eaTemperatures (
                          siteId TEXT,
                          year TEXT,
                          month TEXT,
                          detCode INTEGER,
                          meanTemp REAL,
                          sourceCode TEXT,
                          FOREIGN KEY(siteId) REFERENCES eaSites(siteId));""")

        # Read in sites data
        curIn.execute("""SELECT s.*,
                         m.startDate,
                         m.endDate,
                         m.dataCount,
                         m.detCode,
                         m.sourceCode
                         FROM tbl_siteInfo s, tbl_metaData m
                         WHERE s.siteID = m.siteID
                         AND m.EA_REGION = 'WA'
                         AND NOT (s.siteX = 0 AND s.siteY = 0)
                         AND NOT (s.siteX = 100000 AND s.siteY = 200000)""")

        # Insert sites data into sqlite table
        for r in curIn:
            curOut.execute("""INSERT INTO eaSites VALUES
                              (?,?,?,?,?,?,?,?,?,?, MakePoint(?,?, 27700));""",
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
                            r.siteY))

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
                         AND m.EA_REGION = 'WA'
                         AND NOT (s.siteX = 0 AND s.siteY = 0)
                         AND NOT (s.siteX = 100000 AND s.siteY = 200000)) a
                         ON a.siteID = d.siteID
                         AND a.sourceCode = d.sourceCode
                         GROUP BY d.siteID,
                         YEAR(d.sampleDate),
                         MONTH(d.sampleDate),
                         d.detCode,
                         d.sourceCode;""")

        # Insert temperature data into sqlite table
        for r in curIn:
            curOut.execute("""INSERT INTO eaTemperatures
                               VALUES (?, ?, ?, ?, ?, ?);""", r)

        # Create spatial index
        curOut.execute("SELECT CreateSpatialIndex('eaSites', 'geom');")

    finally:
        # Commit changes and close sqlite connection
        dbOut.commit()
        dbOut.close()
finally:
    # Close Access database connection
    dbIn.close()
