##The MIT License (MIT)
##
##Copyright (c) 2014 Hishiv Shah
##
##Permission is hereby granted, free of charge, to any person obtaining a copy
##of this software and associated documentation files (the "Software"), to deal
##in the Software without restriction, including without limitation the rights
##to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
##copies of the Software, and to permit persons to whom the Software is
##furnished to do so, subject to the following conditions:
##
##The above copyright notice and this permission notice shall be included in
##all copies or substantial portions of the Software.
##
##THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
##IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
##FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
##AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
##LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
##OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
##THE SOFTWARE.

import ogr
import xlrd
import datetime
import arcpy
import os

def mapGaugingStations(stationsXlsx, gridSquaresShp, outGdb):

    # Read in grid squares, create dictionary in format of {gridSquareCode:(minX,minY)}
    dataSource = ogr.Open(gridSquaresShp)
    layer = dataSource.GetLayer()
    gridSquares = {}
    for feature in layer:
        gridSq = feature.GetField("GRIDSQ")
        geom = feature.GetGeometryRef()
        minX, maxX, minY, maxY = geom.GetEnvelope()
        gridSquares[gridSq] = (minX, minY)

    # Create output feature class
    arcpy.CreateFeatureclass_management(outGdb, "gaugingStations", "POINT")
    arcpy.AddField_management(outGdb + "/gaugingStations", "station", "LONG")
    arcpy.AddField_management(outGdb + "/gaugingStations", "name", "TEXT")
    arcpy.AddField_management(outGdb + "/gaugingStations", "precision", "SHORT")

    with arcpy.da.InsertCursor(outGdb + "/gaugingStations", ["station", "name", "precision", "SHAPE@X", "SHAPE@Y"]) as cur:
        
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

            # Write row to feature class
            cur.insertRow((station, name, precision, easting, northing))
        

if __name__ == "__main__":

    # Input data paths
    stationsXlsx = "../data/2014-10-29/nrfa/WalesStations.xlsx"
    gridSquaresShp = "../data/2014-10-29/gb-grids_654971/100km_grid_region.shp"

    # Output paths
    outDir = "../results"
    outGdb = "%s.gdb" % datetime.datetime.now().strftime("%Y-%m-%dT%H%M")

    # Create output database
    arcpy.CreateFileGDB_management(outDir, outGdb)

    # Call function
    mapGaugingStations(stationsXlsx, gridSquaresShp, os.path.join(outDir, outGdb))
    

