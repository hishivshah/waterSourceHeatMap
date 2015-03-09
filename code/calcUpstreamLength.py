import sqlite3
import logging

import networkx
import shapely
import shapely.wkt

# Logging set-up
logging.basicConfig(format="%(asctime)s|%(levelname)s|%(message)s",
                    level=logging.INFO)

# Database path
sqliteDb = "../results/2015-03-09.sqlite"

# Create Directed Graph with multiple edges
logging.info("Creating graph object")
G = networkx.MultiDiGraph()

# Connect to database
logging.info("Connecting to database")
with sqlite3.connect(sqliteDb) as db:
    db.enable_load_extension(True)
    db.load_extension("spatialite")
    cur = db.cursor()
    cur.execute("SELECT InitSpatialMetaData(1);")
    
    # Add river nodes to graph
    logging.info("Adding river nodes to graph")
    cur.execute("SELECT id, ST_ASText(geometry) from riverNodes;")
    for row in cur:
        id = row[0]
        geometry = shapely.wkt.loads(row[1])
        
        G.add_node(id, geometry=geometry)
        
    # Add river edges to graph
    logging.info("Adding river edges to graph")
    cur.execute("""SELECT id, startNodeId, endNodeId, ST_ASText(geometry)
                   FROM riverEdges
                   WHERE startNodeId IS NOT NULL
                   and endNodeId IS NOT NULL;""")
    for row in cur:
        id = row[0]
        startNodeId = row[1]
        endNodeId = row[2]
        geometry = shapely.wkt.loads(row[3])
        
        G.add_edge(startNodeId, endNodeId, key=id, geometry=geometry)
        
    # Calculate upstream river length
    logging.info("Calculating upstream river lengths")
    for startNode, endNode, key, attr in G.edges_iter(data=True, keys=True):
        
        preNodes = networkx.ancestors(G, startNode)
        preEdges = G.edges(preNodes, keys=True, data=True)
        upstreamLength = attr["geometry"].length \
                         + sum([e[3]["geometry"].length for e in preEdges])
       
        cur.execute("""UPDATE riverEdges
                      SET upstreamLength = '%s'
                      WHERE id = '%s';""" % (upstreamLength, key))
                      
    # Commit changes
    db.commit()
        
        