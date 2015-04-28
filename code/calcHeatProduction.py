import sqlite3

# Connect to sqlite database
sqliteDb = "../results/2015-03-10.sqlite"
db = sqlite3.connect(sqliteDb)
try:
    db.enable_load_extension(True)
    db.load_extension("spatialite")
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
    cur.execute("""CREATE TABLE annualHeat (id TEXT PRIMARY KEY,
                                            GWhPerYear REAL);""")
    cur.execute("""SELECT AddGeometryColumn('annualHeat',
                                            'geometry',
                                            27700,
                                            'LINESTRING');""")
    cur.execute("""INSERT INTO annualHeat
                   SELECT r.id, SUM(heatMW * 0.73), r.geometry
                   FROM riverEdges r, monthlyFlowRates mf
                   WHERE r.id = mf.riverId
                   GROUP BY r.id;""")
    cur.execute("SELECT CreateSpatialIndex('annualHeat', 'geometry');")

finally:
    # Commit changes and close database
    db.commit()
    db.close()
