import sqlite3
import logging

import networkx
import shapely
import shapely.wkt

def searchUpOrDownStream(graph, startNode, gaugedEdgeId, gaugedEdgeUpLen, searchDirection):

    if searchDirection == "upstream":
        # Find upstream edges
        searchNodes = graph.predecessors(startNode)
    elif searchDirection == "downstream":
        # Find downstream edges
        searchNodes = graph.successors(startNode)

    searchEdges = graph.edges(searchNodes, keys=True, data=True)
    for sEdge in searchEdges:
        if sEdge[3].get("nearestGaugedEdge") == None:
            sEdge[3]["nearestGaugedEdge"] = gaugedEdgeId
            sEdge[3]["upstreamLengthRatio"] = sEdge[3]["upstreamLength"] / gaugedEdgeUpLen

            searchUpOrDownStream(graph, sEdge[0], gaugedEdgeId, gaugedEdgeUpLen, searchDirection)

if __name__ == "__main__":

    # Logging set-up
    logging.basicConfig(format="%(asctime)s|%(levelname)s|%(message)s",
                        level=logging.INFO)

    # Database path
    sqliteDb = "../results/results.sqlite"

    # Create Directed Graph with multiple edges
    logging.info("Creating graph object")
    G = networkx.MultiDiGraph()

    # Connect to database
    logging.info("Connecting to database")
    with sqlite3.connect(sqliteDb) as db:
        db.enable_load_extension(True)
        db.load_extension("mod_spatialite")
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
                       AND endNodeId IS NOT NULL;""")
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
            G.edge[startNode][endNode][key]["upstreamLength"] = upstreamLength

        # Find river reaches with gauging station
        cur.execute("""SELECT id
                       FROM riverEdges e
                       WHERE e.id IN
                       (SELECT riverId FROM nrfaStations)
                       AND startNodeId IS NOT NULL
                       AND endNodeId IS NOT NULL;""")
        gEdgeIds = [row[0] for row in cur.fetchall()]
        gEdges = [edge for edge in G.edges(keys=True, data=True) if edge[2] in gEdgeIds]

        for gEdge in gEdges:
            gEdge[3]["nearestGaugedEdge"] = gEdge[2]
            gEdge[3]["upstreamLengthRatio"] = 1

        # Find upstream edges for each gauged edge
        for gEdge in gEdges:
            gEdgeStart = gEdge[0]
            gEdgeId = gEdge[2]
            gEdgeUpLen = gEdge[3]["upstreamLength"]

            searchUpOrDownStream(G, gEdgeStart, gEdgeId, gEdgeUpLen, "upstream")

        # Find downstream edges for each gauged edge
        for gEdge in gEdges:
            gEdgeStart = gEdge[0]
            gEdgeId = gEdge[2]
            gEdgeUpLen = gEdge[3]["upstreamLength"]

            searchUpOrDownStream(G, gEdgeStart, gEdgeId, gEdgeUpLen, "downstream")

        # Update riverEdges tables
        for e in G.edges_iter(data=True, keys=True):
            if e[3].get("nearestGaugedEdge") is not None:
                cur.execute("""UPDATE riverEdges
                              SET nearestGaugedEdge = '%s',
                              upstreamLengthRatio = %s
                              WHERE id = '%s';"""
                              % (e[3].get("nearestGaugedEdge"),
                                 e[3].get("upstreamLengthRatio"),
                                 e[2]))


        # Commit changes
        db.commit()
