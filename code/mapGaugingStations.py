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
import xlrd
import datetime
import sqlite3
import os
import logging

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

def mapGaugingStations(stationsXlsx, gridSquares):
    """Reads in gauging station list from Excel Workbook, calculates
       coordinates and precision, returns list of stations in format of
       [(station, name, precision, easting, northing)]."""

    stations = []

    # Read in gauging station list
    wb = xlrd.open_workbook(stationsXlsx)
    ws = wb.sheet_by_index(0)
    for i in range(1,ws.nrows):
        row = ws.row(i)
        station = int(row[0].value)
        name = str(row[1].value)
        ngr = str(row[2].value)

        # calculate coordinates and precision
        gridCode = ngr[:2]
        precision = 10 ** (5 - len(ngr[2:])/2) # Units: meters
        easting = gridSquares[gridCode][0] + int(ngr[2:len(ngr[2:])/2 + 2]) * precision
        northing = gridSquares[gridCode][1] + int(ngr[len(ngr[2:])/2 + 2:]) * precision

        # Add to stations list
        stations.append((station, name, precision, easting, northing))

    return stations
        

if __name__ == "__main__":

    # Set up logger
    logging.basicConfig(format="%(asctime)s|%(levelname)s|%(message)s", level=logging.INFO)

    # Input data paths
    stationsXlsx = "../data/2014-10-29/nrfa/WalesStations.xlsx"
    gridSquaresShp = "../data/2014-10-29/gb-grids_654971/100km_grid_region.shp"

    # Output paths
    outDir = "../results"
    outDb = os.path.join(outDir, "%s.sqlite" % datetime.datetime.now().strftime("%Y-%m-%dT%H%M"))
    
    # Calculate grid square min x and y coordinates
    logging.info("Calculating min x and y of grid squares")
    gridSquares = getGridSquareMinXY(gridSquaresShp)

    # Get station list with coordinates and precision
    logging.info("Get station list with coordinates and precision")
    stations =  mapGaugingStations(stationsXlsx, gridSquares)

    # Connect to output database
    logging.info("Connect to output database")
    db = sqlite3.connect(outDb)
    db.enable_load_extension(True)
    db.load_extension("mod_spatialite")
    cur = db.cursor()
    cur.execute("SELECT InitSpatialMetaData(1);")

    # Create gaugingStations table
    logging.info("Create gaugingStations table")
    cur.execute("""CREATE TABLE gaugingStations (
                   station INTEGER,
                   name TEXT,
                   precision INTEGER);""")
    cur.execute("""SELECT AddGeometryColumn (
                   'gaugingStations',
                   'geom',
                   27700,
                   'POINT');""")

    # Populate table
    logging.info("Populate table")
    cur.executemany("""INSERT INTO gaugingStations (station, name, precision, geom)
                    VALUES (?, ?, ?, MakePoint(?, ?, 27700));""", stations)

    # Commit changes and close database
    logging.info("Commit changes and close database")
    db.commit()
    db.close()

