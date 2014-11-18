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
import shapely
import shapely.wkt
import shapely.ops
import os
import glob
import zipfile
import tempfile
import sys
import shutil
import subprocess

def readWelshDistricts(districtsShp, districtNames):
    ''' Read in list of district names and shapefile of district
        boundaries. Returns list of WKT geometries.'''

    dataSource = ogr.Open(districtsShp)
    layer = dataSource.GetLayer()
    layer.SetAttributeFilter("NAME IN ('%s')" % "','".join(districtNames))

    geoms = []
    for feature in layer:
        geom = feature.GetGeometryRef().ExportToWkt()
        geoms.append(geom)

    return geoms

def readCatchments(catchmentsShp):
    ''' Read in catchments shapefiles. Returns list of WKT geometries.'''

    dataSource = ogr.Open(catchmentsShp)
    layer = dataSource.GetLayer()

    geoms = []
    for feature in layer:
        geom = feature.GetGeometryRef().ExportToWkt()
        geoms.append(geom)

    return geoms


def readGrid(gridShp, clipper):
    ''' Reads in grid squares. Returns list of tile names.'''

    dataSource = ogr.Open(gridShp)
    layer = dataSource.GetLayer()
    layer.SetSpatialFilter(ogr.CreateGeometryFromWkt(clipper))

    tiles = []

    for feature in layer:
        tileName = feature.GetField("TILE_NAME")
        tiles.append(tileName)

    return tiles

def createDtmTiff(asciiDir, tileList, outTiff):
    '''Extracts ESRI ASCII GRID files for specified tiles, merges and
       outputs to specified tiff file.'''

    # Extract DTM ascii files to temporary directory
    tmpDir = tempfile.mkdtemp()
    try:
        for tile in tileList:
            zipPath = glob.glob(os.path.join(asciiDir,
                                   "%s" % tile[:2].lower(),
                                   "%s*.zip" % tile.lower()))[0]
            with zipfile.ZipFile(zipPath) as zFile:
                zFile.extractall(tmpDir)

        # Run gdal merge
        subprocess.check_call(["python", "C:/OSGeo4W64/bin/gdal_merge.py",
                               "-o", outTiff,
                               "-a_nodata", "-9999",
                               "-co", "COMPRESS=LZW"] \
                              + glob.glob(os.path.join(tmpDir, "*.asc")))

    finally:
        # Delete temporary directory
        shutil.rmtree(tmpDir)

if __name__ == "__main__":

    # District shapefile path
    dstShp = "../data/2014-11-14/meridian2_national_653496/district_region.shp"
    # Welsh district names
    districtNames = ['GWYNEDD - GWYNEDD',
                     'SIR Y FFLINT - FLINTSHIRE',
                     'CASNEWYDD - NEWPORT',
                     'SIR YNYS MON - ISLE OF ANGLESEY',
                     'MERTHYR TUDFUL - MERTHYR TYDFIL',
                     'SIR BENFRO - PEMBROKESHIRE',
                     'BRO MORGANNWG - THE VALE OF GLAMORGAN',
                     'WRECSAM - WREXHAM',
                     'TOR-FAEN - TORFAEN',
                     'CASTELL-NEDD PORT TALBOT - NEATH PORT TALBOT',
                     'SIR FYNWY - MONMOUTHSHIRE',
                     'CAERFFILI - CAERPHILLY',
                     'PEN-Y-BONT AR OGWR - BRIDGEND',
                     'BLAENAU GWENT - BLAENAU GWENT',
                     'POWYS - POWYS',
                     'CONWY - CONWY',
                     'SIR DDINBYCH - DENBIGHSHIRE',
                     'RHONDDA CYNON TAF - RHONDDA CYNON TAF',
                     'SIR GAERFYRDDIN - CARMARTHENSHIRE',
                     'SIR CEREDIGION - CEREDIGION',
                     'ABERTAWE - SWANSEA',
                     'CAERDYDD - CARDIFF']
    # Catchments shapefile
    catchmentsShp = "../data/2014-11-14/nrfa/NRFA Catchment Boundary Retrieval/NRFA Catchment Boundary Retrieval_Hishiv Shah.shp"
    # Grid squares shapefile
    gridShp = "../data/2014-11-14/gb-grids_654971/10km_grid_region.shp"
    # DTM data folder
    dtmDir = "../data/2014-11-14/terr50_gagg_gb/data"
    # Out tiff
    outTiff = "../results/osTerrain50.tif"

    # Read in district and catchment geometry
    districts = readWelshDistricts(dstShp, districtNames)
    catchments = readCatchments(catchmentsShp)

    # Dissolve district and catchment polygons to create clipper geometry
    polys = [shapely.wkt.loads(wktGeom) for wktGeom in (districts + catchments)]
    clipper = shapely.ops.unary_union(polys).wkt

    # Read tile names
    tiles = readGrid(gridShp, clipper)

    # Merge DTM tiles, output to tiff file
    createDtmTiff(dtmDir, tiles, outTiff)
