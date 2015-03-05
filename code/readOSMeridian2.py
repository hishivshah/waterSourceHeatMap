import sqlite3
import os

import ogr

# Inputs
osMeridian2Dir = "../data/2015-02-27/meridian2_national_841398"
districtsShp = os.path.join(osMeridian2Dir, "district_region.shp")
riversShp = os.path.join(osMeridian2Dir, "river_polyline.shp")
coastShp = os.path.join(osMeridian2Dir, "coast_ln_polyline.shp")

# Database path
sqliteDb = "../results/2015-03-05.sqlite"

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

# Connect to database
with sqlite3.connect(sqliteDb) as db:
    db.enable_load_extension(True)
    db.load_extension("spatialite")
    cur = db.cursor()
    cur.execute("SELECT InitSpatialMetaData(1);")
    
    # Create districts table
    cur.execute("DROP TABLE IF EXISTS osDistricts;")
    cur.execute("""CREATE TABLE osDistricts (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT);""")
    cur.execute("""SELECT AddGeometryColumn('osDistricts',
                                            'geometry',
                                            27700,
                                            'POLYGON');""")

    # Create rivers table
    cur.execute("DROP TABLE IF EXISTS osRivers;")
    cur.execute("""CREATE TABLE osRivers (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   identifier TEXT,
                   code INTEGER,
                   name TEXT);""")
    cur.execute("""SELECT AddGeometryColumn('osRivers',
                                            'geometry',
                                            27700,
                                            'LINESTRING');""")
                                            
    # Create coastline table
    cur.execute("DROP TABLE IF EXISTS osCoastline;")
    cur.execute("""CREATE TABLE osCoastline (
                   id INTEGER PRIMARY KEY AUTOINCREMENT);""")
    cur.execute("""SELECT AddGeometryColumn('osCoastline',
                                            'geometry',
                                            27700,
                                            'LINESTRING');""")                            
                                            
    # Read districts from shape
    dataSource = ogr.Open(districtsShp)
    layer = dataSource.GetLayer()
    layer.SetAttributeFilter("NAME IN ('%s')" % "','".join(districtNames))
    
    for feature in layer:
        geometry = feature.GetGeometryRef().ExportToWkt()
        name = feature.GetField("NAME")
        
        # Insert data into osDistricts table
        cur.execute("""INSERT INTO osDistricts (name, geometry)
                       VALUES (?, ST_GeomFromText(?, 27700));""",
                    (name, geometry))

    # Read rivers from shape
    dataSource = ogr.Open(riversShp)
    layer = dataSource.GetLayer()
    layer.SetAttributeFilter("CODE IN (6223, 6224, 6225, 6230, 6232)")
    
    for feature in layer:
        geometry = feature.GetGeometryRef().ExportToWkt()
        identifier = feature.GetField("IDENTIFIER")
        code = feature.GetField("CODE")
        name = feature.GetField("NAME")
        
        # Insert data into osRivers table
        cur.execute("""INSERT INTO osRivers (identifier, code, name, geometry)
                       VALUES (?, ?, ?, ST_GeomFromText(?, 27700));""",
                    (identifier, code, name, geometry))
                    
    # Read coastlines from shape
    dataSource = ogr.Open(coastShp)
    layer = dataSource.GetLayer()
    
    for feature in layer:
        geometry = feature.GetGeometryRef().ExportToWkt()
        
        # Insert data into osCoastline table
        cur.execute("""INSERT INTO osCoastline (geometry)
                       VALUES (ST_GeomFromText(?, 27700));""",
                    (geometry,))
                    
    # Build spatial indexes
    cur.execute("SELECT CreateSpatialIndex('osDistricts', 'geometry');")
    cur.execute("SELECT CreateSpatialIndex('osRivers', 'geometry');")
    cur.execute("SELECT CreateSpatialIndex('osCoastline', 'geometry');")
    
    # Dissolve welsh districts to single polygon
    cur.execute("DROP TABLE IF EXISTS wales;")
    cur.execute("""CREATE TABLE wales (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT);""")
    cur.execute("""SELECT AddGeometryColumn('Wales',
                                            'geometry',
                                            27700,
                                            'MULTIPOLYGON');""")
    cur.execute("""INSERT INTO wales (name, geometry)
                   SELECT 'Wales', ST_UNION(geometry)
                   FROM osDistricts;""")
    cur.execute("SELECT CreateSpatialIndex('wales', 'geometry');")    
  
    # Commit changes to database
    db.commit()
