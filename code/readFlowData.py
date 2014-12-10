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
import sqlite3
import ogr

def getGridSquareMinXY(gridSquaresShp):
    """Reads in grid square shapefiles, returns dictionary in format of
       {gridSquareCode:(minX,minY)."""

    dataSource = ogr.Open(gridSquaresShp)
    layer = dataSource.GetLayer()
    gridSquares = {}
    for feature in layer:
        gridSq = feature.GetField("GRIDSQ")
        geom = feature.GetGeometryRef()
        minX, maxX, minY, maxY = geom.GetEnvelope()
        gridSquares[gridSq] = (minX, minY)

    return gridSquares

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

def calcStationCoords(station, gridSquares):
    """ Calculates easting, northing and coordinate precision from the
        station grid reference. Returns dictionary with the additional
        keys."""

    # calculate coordinates and precision
    gridRef = station["gridReference"]
    gridCode = gridRef[:2]
    station["precision"] = 10 ** (5 - len(gridRef[2:])/2) # Units: meters
    station["easting"] = gridSquares[gridCode][0] \
                         + int(gridRef[2:len(gridRef[2:])/2 + 2]) \
                         * station["precision"]
    station["northing"] = gridSquares[gridCode][1] \
                          + int(gridRef[len(gridRef[2:])/2 + 2:]) \
                          * station["precision"]

    return station


if __name__ == "__main__":

    # Input paths
    csvDir  = "../data/2014-11-14/nrfa/NRFA Flow Data Retrieval"
    gridSquaresShp = "../data/2014-11-14/gb-grids_654971/100km_grid_region.shp"

    # Output paths
    outDb = "../results/2014-12-10.sqlite"

    # Calculate grid square min x and y coordinates
    gridSquares = getGridSquareMinXY(gridSquaresShp)

    # Connect to output database
    db = sqlite3.connect(outDb)
    try:
        db.enable_load_extension(True)
        db.load_extension("spatialite")
        cur = db.cursor()
        cur.execute("SELECT InitSpatialMetaData(1);")

        # Create tables
        cur.execute("DROP TABLE IF EXISTS nrfaStations;")
        cur.execute("""CREATE TABLE nrfaStations (
                       id INTEGER PRIMARY KEY,
                       name TEXT,
                       stationComment TEXT,
                       catchmentComment TEXT,
                       geomPrecision INTEGER);""")
        cur.execute("""SELECT AddGeometryColumn (
                       'nrfaStations',
                       'geom',
                       27700,
                       'POINT');""")

        cur.execute("DROP TABLE IF EXISTS nrfaDataTypes;")
        cur.execute("""CREATE TABLE nrfaDataTypes (
                       id TEXT PRIMARY KEY ON CONFLICT IGNORE,
                       name TEXT,
                       parameter TEXT,
                       units TEXT,
                       period TEXT,
                       measurementType TEXT);""")

        cur.execute("DROP TABLE IF EXISTS nrfaData;")
        cur.execute("""CREATE TABLE nrfaData (
                       station INTEGER,
                       dataType TEXT,
                       first TEXT,
                       last TEXT,
                       FOREIGN KEY(station) REFERENCES nrfaStations(id),
                       FOREIGN KEY(dataType) REFERENCES nrfaDataTypes(id));""")

        cur.execute("DROP TABLE IF EXISTS nrfaGmf;")
        cur.execute("""CREATE TABLE nrfaGmf (
                       station INTEGER,
                       dataType TEXT,
                       month TEXT,
                       flow REAL,
                       FOREIGN KEY(station) REFERENCES nrfaStations(id),
                       FOREIGN KEY(dataType) REFERENCES nrfaDataTypes(id));""")


        # Read data from csv files
        for csvFile in glob.iglob(os.path.join(csvDir, "*.csv")):
            data = readGmfCsv(csvFile)

            # Calculate station coordinates
            data["station"] = calcStationCoords(data["station"], gridSquares)

            # Insert data into tables
            cur.execute("""INSERT INTO nrfaStations
                           VALUES (?, ?, ?, ?, ?, MakePoint(?, ?, 27700));""",
                        (data["station"].get("id"),
                         data["station"].get("name"),
                         data["station"].get("stationComment"),
                         data["station"].get("catchmentComment"),
                         data["station"].get("precision"),
                         data["station"].get("easting"),
                         data["station"].get("northing")))
            cur.execute("""INSERT INTO nrfaDataTypes
                           VALUES (?, ?, ?, ?, ?, ?);""",
                        (data["dataType"].get("id"),
                         data["dataType"].get("name"),
                         data["dataType"].get("parameter"),
                         data["dataType"].get("units"),
                         data["dataType"].get("period"),
                         data["dataType"].get("measurementType")))
            cur.execute("""INSERT INTO nrfaData VALUES (?, ?, ?, ?);""",
                        (data["station"].get("id"),
                         data["dataType"].get("id"),
                         data["data"].get("first"),
                         data["data"].get("last")))
            cur.executemany("""INSERT INTO nrfaGmf VALUES (?, ?, ?, ?);""",
                        [(data["station"].get("id"),
                          data["dataType"].get("id"),
                          k,
                          v)
                         for k, v in data["gmf"].iteritems()])

        # Create spatial index
        cur.execute("SELECT CreateSpatialIndex('nrfaStations', 'geom');")

    finally:
        # Commit changes and close database
        db.commit()
        db.close()
