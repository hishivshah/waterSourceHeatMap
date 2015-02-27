import csv

import numpy
import gdal
import osr

csvPath = "../data/2015-02-27/energyDemand2009/2009_base_data.csv"
cellSize = 1000
outTiff = "../results/heatDemand2009.tiff"

# Read easting and northing values
eastings = []
northings = []

with open(csvPath, "rb") as csvFile:
    reader = csv.reader(csvFile)
    reader.next() #  skip headers
    for row in reader:
        easting = round(float(row[5]))
        northing = round(float(row[6]))
        eastings.append(easting)
        northings.append(northing)

# Calculate min and max coordinates
minX = min(eastings) - cellSize/2
maxX = max(eastings) + cellSize/2
minY = min(northings) - cellSize/2
maxY = max(northings) + cellSize/2

# Calculate raster dimensions
dX = int((maxX - minX) / cellSize)
dY = int((maxY - minY) / cellSize)

# Create numpy array filled with nodata value
heatDemand = numpy.empty((dY, dX), numpy.float32)
heatDemand.fill(-1)

# Read DOM_HT and NONDOM_HT values, calculate total heat demand
with open(csvPath, "rb") as csvFile:
    reader = csv.reader(csvFile)
    reader.next() #  skip headers
    for row in reader:
        x = int(round(float(row[5])))/cellSize
        y = int(round(float(row[6])))/cellSize
        domHT = float(row[7])
        nonDomHT = float(row[9])
        heatDemand[y][x] = domHT + nonDomHT

# Write array out to geotiff
driver = gdal.GetDriverByName('GTiff')
raster = driver.Create(outTiff, dX, dY, 1, gdal.GDT_Float32)
raster.SetGeoTransform((minX, 1000, 0, minY, 0, 1000))
srs = osr.SpatialReference()
srs.ImportFromEPSG(27700)
raster.SetProjection(srs.ExportToWkt())
raster.GetRasterBand(1).WriteArray(heatDemand)
raster.GetRasterBand(1).SetNoDataValue(-1)
