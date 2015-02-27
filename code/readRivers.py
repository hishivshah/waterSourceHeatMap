import sqlite3

import ogr
import shapely
import shapely.wkt
import shapely.ops

def readRivers(riversShp):
    '''Read medium and large river lines from shapefile, return list of wkt
       geometries.'''

    dataSource = ogr.Open(riversShp)
    layer = dataSource.GetLayer()
    layer.SetAttributeFilter("CODE IN (6224, 6225)")

    data = []
    for feature in layer:
        geom = feature.GetGeometryRef().ExportToWkt()
        data.append(geom)

    return data

def mergeRiverLines(geomList):
    '''Reads list of wkt line geometries. Merges continous lines. Returns list
       of wkt geometries.'''

    lines = [shapely.wkt.loads(geom) for geom in geomList]
    mergedLines = [line.wkt for line in shapely.ops.linemerge(lines)]

    return mergedLines

if __name__ == "__main__":

    # Inputs
    riversShp = "../data/2015-02-27/meridian2_national_653496/river_polyline.shp"

    # Outputs
    sqliteDb = "../results/2014-12-10.sqlite"

    # Read in rivers
    rivers = readRivers(riversShp)

    # Merge river lines
    mergedRivers = mergeRiverLines(rivers)

    # Connect to output database
    db = sqlite3.connect(sqliteDb)
    try:
        db.enable_load_extension(True)
        db.load_extension("spatialite")
        cur = db.cursor()
        cur.execute("SELECT InitSpatialMetaData(1);")

        # Create temp table
        cur.execute("DROP TABLE IF EXISTS osRivers;")
        cur.execute("""CREATE TABLE osRivers
                       (id INTEGER PRIMARY KEY AUTOINCREMENT);""")
        cur.execute("""SELECT AddGeometryColumn('osRivers',
                                                'geom',
                                                27700,
                                                'LINESTRING');""")
        # Insert features
        cur.executemany("""INSERT INTO osRivers (geom)
                           VALUES (GeomFromText(?, 27700));""",
                        [(geom,) for geom in mergedRivers])

        # Create spatial index
        cur.execute("SELECT CreateSpatialIndex('osRivers', 'geom');")


    finally:
        # Commit changes
        db.commit()
        # Close database
        db.close()
