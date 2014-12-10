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

import subprocess
import logging
import tempfile
import os
import shutil

import ogr

# Logging config
logging.basicConfig(format="%(asctime)s|%(levelname)s|%(message)s",
                    level=logging.INFO)
# Make temp dir
tmpdir = tempfile.mkdtemp()
try:

    #Inputs
    dem = "../results/osTerrain50.tif"
    clipper = "../results/clipper.wkt"
    #Outputs
    clipperJson = os.path.join(tmpdir, "clipper.json")
    filledDEM = os.path.join(tmpdir, "filledDEM.tif")
    clippedFilledDEM = os.path.join(tmpdir, "clippedFilledDEM.tif")
    flowDir = os.path.join(tmpdir, "flowDir.tif")
    clippedFlowDir = os.path.join(tmpdir, "clippedFlowDir.tif")
    slopes = os.path.join(tmpdir, "slopes.tif")
    contribArea = os.path.join(tmpdir, "sca.tif")
    clippedContribArea = os.path.join(tmpdir, "clippedSca.tif")
    streamRast = os.path.join(tmpdir, "streams.tif")
    clippedStreams = os.path.join(tmpdir, "clippedStreams.tif")
    strahler = "../results/strahler.tif"
    streamVect = "../results/streams.shp"
    treefile = "../results/treefile.dat"
    coordfile = "../results/coordfile.dat"
    watersheds = "../results/watersheds.tif"

    # get clipper.wkt contents
    with open(clipper, "r") as clipperFile:
        clipperWkt = clipperFile.read()
    # Write to geojson
    geojson = ogr.CreateGeometryFromWkt(clipperWkt).ExportToJson()
    with open(clipperJson, "w") as jsonFile:
        jsonFile.write(geojson)

    try:
        # Call TauDEM tools
        logging.info(subprocess.check_output(["mpiexec",
                                              "-n", "8",
                                              "PitRemove",
                                              "-z", dem,
                                              "-fel", filledDEM]))
        logging.info(subprocess.check_output(["mpiexec",
                                              "-n", "8",
                                              "D8FlowDir",
                                              "-fel", filledDEM,
                                              "-p", flowDir,
                                              "-sd8", slopes]))
        logging.info(subprocess.check_output(["mpiexec",
                                              "-n", "8",
                                              "AreaD8",
                                              "-p", flowDir,
                                              "-ad8", contribArea]))
        logging.info(subprocess.check_output(["mpiexec",
                                              "-n", "8",
                                              "Threshold",
                                              "-ssa", contribArea,
                                              "-src", streamRast,
                                              "-thresh", "10000"]))

        # Clip rasters using GDAL
        logging.info(subprocess.check_output(["gdalwarp",
                                              "-cutline", clipperJson,
                                              "-crop_to_cutline",
                                              "-dstnodata", "-9999",
                                              filledDEM,
                                              clippedFilledDEM]))
        logging.info(subprocess.check_output(["gdalwarp",
                                              "-cutline", clipperJson,
                                              "-crop_to_cutline",
                                              "-dstnodata", "-9999",
                                              flowDir,
                                              clippedFlowDir]))
        logging.info(subprocess.check_output(["gdalwarp",
                                              "-cutline", clipperJson,
                                              "-crop_to_cutline",
                                              "-dstnodata", "-9999",
                                              contribArea,
                                              clippedContribArea]))
        logging.info(subprocess.check_output(["gdalwarp",
                                              "-cutline", clipperJson,
                                              "-crop_to_cutline",
                                              "-dstnodata", "-9999",
                                              streamRast,
                                              clippedStreams]))

        # Call TauDEM StreamNet tool
        logging.info(subprocess.check_output(["mpiexec",
                                              "-n", "8",
                                              "StreamNet",
                                              "-fel", clippedFilledDEM,
                                              "-p", clippedFlowDir,
                                              "-ad8", clippedContribArea,
                                              "-src", clippedStreams,
                                              "-ord", strahler,
                                              "-tree", treefile,
                                              "-coord", coordfile,
                                              "-w", watersheds,
                                              "-net", streamVect]))

    except subprocess.CalledProcessError as e:
        logging.error(e.output)

finally:
    # Remove temp dir
    shutil.rmtree(tmpdir)
