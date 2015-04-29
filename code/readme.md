readFlowData.py
- reads NRFA Gauged Monthly Flow data from csv files
- loads data into spatialite database

readOSMeridian2.py
- reads OS Meridian 2 district polygons, river lines, and coast lines data from shapefiles
- loads data into spatialite database
- dissolves Welsh district polygons to create a Welsh national boundary polygon

buildRiverNetwork.py
- creates a network of nodes and edges from river line features
- assumes all rivers flow out to the coastline
- loops through river lines, starting with those that intersect the coastlines, then moving upstream
- tests whether line geometry is oriented in the direction of river flow and then reverses geometry if appropriate
- creates nodes at start and end of each river line

calcUpstreamLength.py
- traverses the river network using the networkX module
- for every edge, calculates the cumulative length of all upstream edges
- finds the nearest gauging station for every edge, calculates the cumulative length of all edges upstream of gauging station
- calculates ratio between cumulative upstream lengths of the edge and its nearest gauging station

calcHeatProduction.py
- calculates the annual heat production of each river reach
- based on flow rate at the nearest gauging station, and upstream river length ratio between station and reach
- assumes a river temperature change of 2 degrees Celsius
