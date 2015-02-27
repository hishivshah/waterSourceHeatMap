'''Dissolves and merges Welsh district boundaries with welsh catchment
   boundaries, to create a WKT polygon that can be used to clip other
   data sets to the study area.'''

import ogr
import shapely
import shapely.wkt
import shapely.ops

def readWelshDistricts(districtsShp, districtNames):
    ''' Read in list of district names and shapefile of district
        boundaries. Returns list of WKT geometries.'''

    dataSource = ogr.Open(districtsShp)
    layer = dataSource.GetLayer()
    layer.SetAttributeFilter("NAME IN ('%s')" % "','".join(districtNames))

    geoms = []
    for feature in layer:
        geom = feature.GetGeometryRef().ExportToWkt()
        geoms.append(geom)

    return geoms

def readCatchments(catchmentsShp):
    ''' Read in catchments shapefiles. Returns list of WKT geometries.'''

    dataSource = ogr.Open(catchmentsShp)
    layer = dataSource.GetLayer()

    geoms = []
    for feature in layer:
        geom = feature.GetGeometryRef().ExportToWkt()
        geoms.append(geom)

    return geoms

if __name__ == "__main__":

    # District shapefile path
    dstShp = "../data/2015-02-27/meridian2_national_841398/district_region.shp"
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
    # Catchments shapefile
    catchmentsShp = "../data/2015-02-27/nrfa/NRFA Catchment Boundary Retrieval/NRFA Catchment Boundary Retrieval_Hishiv Shah.shp"
    # Output file
    clipperWkt = "../results/clipper.wkt"

    # Read in district and catchment geometry
    districts = readWelshDistricts(dstShp, districtNames)
    catchments = readCatchments(catchmentsShp)

    # Dissolve district and catchment polygons to create clipper geometry
    polys = [shapely.wkt.loads(wktGeom) for wktGeom in (districts + catchments)]
    clipper = shapely.ops.unary_union(polys).wkt

    # Write wkt string to file
    with open(clipperWkt, "w") as f:
        f.write(clipper)
