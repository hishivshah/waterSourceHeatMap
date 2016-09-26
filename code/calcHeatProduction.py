import sqlite3

# Connect to sqlite database
sqliteDb = "../results/results.sqlite"
db = sqlite3.connect(sqliteDb)
try:
    db.enable_load_extension(True)
    db.load_extension("mod_spatialite")
    cur = db.cursor()

    # Calculate mean monthly flow rate for last 5 years of data
    cur.execute("DROP TABLE IF EXISTS monthlyFlowRates;")
    cur.execute("""CREATE TABLE monthlyFlowRates AS
                   SELECT r.id AS riverId,
                          STRFTIME("%m", gmf.month||"-01") AS month,
                          AVG(gmf.flow) * r.upstreamLengthRatio AS flow,
                          AVG(gmf.flow) * r.upstreamLengthRatio * 8.36 AS heatMW,
                          ST_Length(r.geometry) * 0.02 AS limitMW
                   FROM nrfaStations s, nrfaData d, nrfaGmf gmf, riverEdges r
                   WHERE d.station = s.id
                   AND gmf.station = s.id
                   AND s.riverId = r.nearestGaugedEdge
                   AND DATE(first||"-01") <= DATE("2008-10-01")
                   AND last = "2013-09"
                   AND DATE(gmf.month||"-01")
                       BETWEEN DATE("2008-10-01")
                       AND DATE("2013-09-01")
                   GROUP BY r.id, STRFTIME("%m", gmf.month||"-01");""")

    # Calculate annual heat production in GWh per year
    cur.execute("DROP TABLE IF EXISTS annualHeat;")
    cur.execute("SELECT DisableSpatialIndex('annualHeat', 'geometry');")
    cur.execute("""CREATE TABLE annualHeat (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                            riverId TEXT,
                                            riverCode INTEGER,
                                            GWhPerYear REAL);""")
    cur.execute("""SELECT AddGeometryColumn('annualHeat',
                                            'geometry',
                                            27700,
                                            'LINESTRING');""")
    cur.execute("""INSERT INTO annualHeat (riverId, riverCode, GWhPerYear, geometry)
                   SELECT r.id, r.code, SUM(heatMW * 0.73), r.geometry
                   FROM riverEdges r, monthlyFlowRates mf
                   WHERE r.id = mf.riverId
                   GROUP BY r.id;""")
    cur.execute("SELECT CreateSpatialIndex('annualHeat', 'geometry');")

    # Calculate annual heat production for lakes
    cur.execute("DROP TABLE IF EXISTS annualHeatLakes;")
    cur.execute("""CREATE TABLE annualHeatLakes (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   identifier TEXT,
                   code INTEGER,
                   name TEXT,
                   GWhPerYear REAL);""")
    cur.execute("""SELECT AddGeometryColumn('annualHeatLakes',
                                            'geometry',
                                            27700,
                                            'POLYGON');""")
    cur.execute("""INSERT INTO annualHeatLakes (identifier, code, name,
                                                GWhPerYear, geometry)
                   SELECT l.identifier, l.code, l.name, MAX(h.GWhPerYear),
                          l.geometry
                   FROM osLakes l, annualheat h
                   WHERE h.riverCode = 6232
                   AND ST_Intersects(l.geometry, h.geometry)
                   AND l.ROWID IN
                   (SELECT ROWID
                   FROM SpatialIndex
                   WHERE f_table_name = 'osLakes'
                   AND search_frame = h.geometry)
                   GROUP BY l.id;""")
    cur.execute("SELECT CreateSpatialIndex('annualHeatLakes', 'geometry');")

finally:
    # Commit changes and close database
    db.commit()
    db.close()
