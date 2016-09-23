import sqlite3


# Database path
sqliteDb = "../results/2015-03-10.sqlite"

# Connect to database
with sqlite3.connect(sqliteDb) as db:
    db.enable_load_extension(True)
    db.load_extension("mod_spatialite")
    cur = db.cursor()
    cur.execute("SELECT InitSpatialMetaData();")

    # Create table for river edges
    cur.execute("DROP TABLE IF EXISTS riverEdges;")
    cur.execute("""CREATE TABLE riverEdges (
                   id TEXT PRIMARY KEY,
                   code INTEGER,
                   startNodeId INTEGER,
                   endNodeId INTEGER,
                   nearestGaugedEdge TEXT,
                   upstreamLengthRatio NUMERIC);""")
    cur.execute("""SELECT AddGeometryColumn('riverEdges',
                                            'geometry',
                                            27700,
                                            'LINESTRING');""")
    cur.execute("""WITH RECURSIVE
                   results(identifier, code, geometry) AS
                   (SELECT r.identifier, r.code, r.geometry
                   FROM osRivers r, wales w
                   WHERE ST_INTERSECTS(r.geometry, w.geometry)
                   AND r.ROWID IN
                   (SELECT ROWID
                   FROM SpatialIndex
                   WHERE f_table_name = 'osRivers'
                   AND search_frame = w.geometry)
                   UNION
                   SELECT r.identifier, r.code, r.geometry
                   FROM osRivers r, results s
                   WHERE ST_INTERSECTS(r.geometry, s.geometry)
                   AND r.ROWID IN
                   (SELECT ROWID
                   FROM SpatialIndex
                   WHERE f_table_name = 'osRivers'
                   AND search_frame = s.geometry))
                   INSERT INTO riverEdges (id, code, geometry)
                   SELECT identifier, code,
                          CastToLineString(ST_LineMerge(ST_Collect(geometry)))
                   FROM results
                   GROUP BY identifier, code;""")
    cur.execute("SELECT CreateSpatialIndex('riverEdges', 'geometry');")

    # Create table for river nodes
    cur.execute("DROP TABLE IF EXISTS riverNodes;")
    cur.execute("""CREATE TABLE riverNodes (
                   id INTEGER PRIMARY KEY);""")
    cur.execute("""SELECT AddGeometryColumn('riverNodes',
                                            'geometry',
                                            27700,
                                            'POINT');""")

    # Create nodes where coastline intersects rivers
    cur.execute("""INSERT INTO riverNodes (geometry)
                   SELECT ST_Intersection(e.geometry, c.geometry)
                   FROM riverEdges e, osCoastline c
                   WHERE ST_Intersects(e.geometry, c.geometry)
                   AND c.ROWID IN
                   (SELECT ROWID
                   FROM SpatialIndex
                   WHERE f_table_name = 'osCoastline'
                   AND search_frame = e.geometry)
                   GROUP BY e.geometry;""")
    cur.execute("SELECT CreateSpatialIndex('riverNodes', 'geometry');")


    while cur.execute("""SELECT count(e.id)
                         FROM riverEdges e, riverNodes n
                         WHERE e.endNodeId IS NULL
                         AND ST_Touches(e.geometry, n.geometry)
                         AND e.ROWID IN
                         (SELECT ROWID
                         FROM SpatialIndex
                         WHERE f_table_name = 'riverEdges'
                         AND search_frame = n.geometry);""").fetchone()[0] > 0:

        print cur.execute("""SELECT count(e.id)
                         FROM riverEdges e, riverNodes n
                         WHERE e.endNodeId IS NULL
                         AND ST_Touches(e.geometry, n.geometry)
                         AND e.ROWID IN
                         (SELECT ROWID
                         FROM SpatialIndex
                         WHERE f_table_name = 'riverEdges'
                         AND search_frame = n.geometry);""").fetchone()[0]

        # Reverse incorrectly orientated linestrings
        cur.execute("""UPDATE riverEdges
                       SET geometry = ST_Reverse(geometry)
                       WHERE id IN
                       (SELECT e.id
                       FROM riverEdges e, riverNodes n
                       WHERE e.endNodeId IS NULL
                       AND ST_Intersects(n.geometry,
                                         ST_StartPoint(e.geometry))
                       AND n.ROWID IN
                       (SELECT ROWID
                       FROM SpatialIndex
                       WHERE f_table_name = 'riverNodes'
                       AND search_frame = e.geometry));""")

        # Set riverEdge endNodeId attribute
        cur.execute("""UPDATE riverEdges
                       SET endNodeId = (SELECT n.id
                       FROM riverNodes n
                       WHERE ST_Intersects(ST_EndPoint(riverEdges.geometry), n.geometry)
                       AND n.ROWID IN
                       (SELECT ROWID
                       FROM SpatialIndex
                       WHERE f_table_name = 'riverNodes'
                       AND search_frame = riverEdges.geometry))
                       WHERE endNodeId IS NULL;""")

        # Create nodes at first vertex of riverEdge
        cur.execute("""INSERT INTO riverNodes (geometry)
                       SELECT ST_StartPoint(e.geometry)
                       FROM riverEdges e
                       WHERE e.startNodeId IS NULL
                       AND e.endNodeId IS NOT NULL;""")

        # Set riverEdge startNodeId attribute
        cur.execute("""UPDATE riverEdges
                       SET startNodeId = (SELECT n.id
                       FROM riverNodes n
                       WHERE ST_Intersects(ST_StartPoint(riverEdges.geometry), n.geometry)
                       AND n.ROWID IN
                       (SELECT ROWID
                       FROM SpatialIndex
                       WHERE f_table_name = 'riverNodes'
                       AND search_frame = riverEdges.geometry))
                       WHERE startNodeId IS NULL
                       AND endNodeId IS NOT NULL;""")


    # Commit changes
    db.commit()
