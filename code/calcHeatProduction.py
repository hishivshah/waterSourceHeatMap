'''Calculates the annual heat production in GWh for each river, based
   on its flow rate. The calculations used are described in more detail
   in "../docs/heatOutputCalculations.docx".'''

import sqlite3

# Connect to sqlite database
sqliteDb = "../results/2014-12-10.sqlite"
db = sqlite3.connect(sqliteDb)
try:
    db.enable_load_extension(True)
    db.load_extension("spatialite")
    cur = db.cursor()

    # Create lookup table matching river IDs to NRFA station IDs
    cur.execute("DROP TABLE IF EXISTS nrfaRiverLookup;")
    cur.execute("""CREATE TABLE nrfaRiverLookup AS
                   SELECT station, river FROM
                   (SELECT s.id AS station,
                    r.id AS river,
                    MIN(ST_Distance(ST_Intersection(ST_Boundary(c.geom),
                                                    r.geom),
                                    s.geom)) AS minDist
                    FROM osRivers r, nrfaCatchments c, nrfaStations s
                    WHERE ST_Intersects(ST_Boundary(c.geom), r.geom)
                    AND s.id = c.id
                    GROUP BY s.id)
                    WHERE minDist <= 1500;""")

    # Calculate mean monthly flow rate for last 5 years of data
    cur.execute("DROP TABLE IF EXISTS monthlyFlowRates;")
    cur.execute("""CREATE TABLE monthlyFlowRates AS
                   SELECT r.id AS riverId,
                          STRFTIME("%m", gmf.month||"-01") AS month,
                          AVG(gmf.flow) AS flow,
                          AVG(gmf.flow) * 8.36 AS heatMW,
                          ST_Length(r.geom) * 0.02 AS limitMW
                   FROM nrfaRiverLookup l, nrfaData d, nrfaGmf gmf, osRivers r
                   WHERE d.station = l.station
                   AND gmf.station = l.station
                   AND l.river = r.id
                   AND DATE(first||"-01") <= DATE("2008-10-01")
                   AND last = "2013-09"
                   AND DATE(gmf.month||"-01")
                       BETWEEN DATE("2008-10-01")
                       AND DATE("2013-09-01")
                   GROUP BY r.id, STRFTIME("%m", gmf.month||"-01");""")

    # Calculate annual heat production in GWh per year
    cur.execute("DROP TABLE IF EXISTS annualHeat;")
    cur.execute("""CREATE TABLE annualHeat (riverId INTEGER PRIMARY KEY,
                                          GWhPerYear REAL);""")
    cur.execute("""SELECT AddGeometryColumn('annualHeat',
                                            'geom',
                                            27700,
                                            'LINESTRING');""")
    cur.execute("""INSERT INTO annualHeat
                   SELECT r.id, SUM(MIN(heatMW, limitMW) * 0.73), r.geom
                   FROM osRivers r, monthlyFlowRates mf
                   WHERE r.id = mf.riverId
                   GROUP BY r.id;""")

finally:
    # Commit changes and close database
    db.commit()
    db.close()
