from apps.findbestroute.models import *
import time
import arcpy
import math
from arcpy import env
from arcpy.sa import *
from celery import shared_task
from apps.userregistration.models import PathUser
from apps.findbestroute.models import UploadedFile
from time import sleep
from django.conf import settings
import models
import os, shutil
import psutil

"""
LOCKS AND UNLOCKING THEM:
    CURSORS cause them. E.g. arcpy.SearchCursor, arcpy.da.SearchCursor.

    Use them in conjunction with "with" statements to ensure unlocking,
    or use reset() on the cursor.

"""


@shared_task() # last resort, other methods.
def delete_user_uploads(uploaderpk):
    print("Deleting user uploads...")
    sleep(2)

    arcpy.ClearWorkspaceCache_management()
    try:
        UploadedFile.objects.filter(uploader=PathUser.objects.get(pk=uploaderpk)).delete()
        Image.objects.filter(uploader=uploaderpk)

        folder = os.path.join(settings.PROJECT_PATH, 'files', 'user_' + str(uploaderpk))  # directly entering.

        for file in os.listdir(folder):
            filepath = os.path.join(folder, file)
            arcpy.ClearWorkspaceCache_management(filepath) # some attempt to unlock files directly
            try:
                if not arcpy.TestSchemaLock(filepath):
                    print("Can't proceed - feature class is locked")
                elif os.path.isfile(filepath):
                    os.remove(filepath)
                elif os.path.isdir(filepath):
                    shutil.rmtree(filepath)
                else:
                    arcpy.Delete_management(filepath)
            except Exception as e:
                print(e)

    except Exception as e:
        print(e)
    print("delete_user_upload finished")
    sleep(2)


@shared_task() # Crude deletion method, as though deleting from explorer
def clean_cache():
    print("Clearing cache...")
    sleep(2)
    basePath = os.path.join(settings.PROJECT_PATH, 'apps', 'findbestroute', 'workfiles')

    """CostBac_ and CostDis_ tif files to be deleted"""
    folder = basePath
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
                # elif os.path.isdir(file_path): shutil.rmtree(file_path)
        except Exception as e:
            print(e)

    folder = os.path.join(basePath, r"Trash")
    for file in os.listdir(folder):
        filepath = os.path.join(folder, file)
        try:
            if os.path.isfile(filepath):
#                print("Removing "+filepath)
                os.remove(filepath)
            elif os.path.isdir(filepath):
#                print("Removing "+filepath)
                shutil.rmtree(filepath)
        except Exception as e:
            print(e)

    folder = os.path.join(basePath, r"Results")
    for file in os.listdir(folder):
        filepath = os.path.join(folder, file)
        try:
            if os.path.isfile(filepath):
#                print("Removing " + filepath)
                os.remove(filepath)
            elif os.path.isdir(filepath):
#                print("Removing " + filepath)
                shutil.rmtree(filepath)
        except Exception as e:
            print(e)
    print("clean_cache finished")
    sleep(2)



def getStart(pt):
    """
    conversion from arcpy.<x>Cursor to arcpy.da.<x>Cursor:
        parameter change: field_names --> *; keep all rows.
    """
    try:
        start = arcpy.Select_analysis(in_features=pt, out_feature_class= os.path.join(basePath, r"Trash", r"start.shp"),
                                      where_clause= '"SYMBOL" = 701 AND "ANGLE" = 0')
        arcpy.AddXY_management(start)
        return start
    except:
        print("Failed to getStart()")


def getDestination(pt):
    try:
        destination = arcpy.Select_analysis(in_features=pt , out_feature_class=os.path.join(basePath, r"Trash", r"destination.shp"),
                                            where_clause='"SYMBOL" = 706')
        arcpy.AddXY_management(destination)
        return destination
    except:
        print("Failed to getStart()")


def setMask(start, finish):
    """
    startX = None
    startY = None
    destinationX = None
    destinationY = None
    """
#    searchCursor = arcpy.SearchCursor(start)
    with arcpy.da.SearchCursor(start, 'SHAPE@XY') as sc:
        for feature in sc:
            startX, startY = feature[0]
        sc.reset()
    del sc
    fid = None
#    searchCursor = arcpy.SearchCursor(finish)
    with arcpy.da.SearchCursor(finish, ['FID', 'SHAPE@XY']) as sc:
        for feature in sc:
            destinationX, destinationY = feature[1]
            fid = feature[0]
    del sc

    length = (math.sqrt(math.pow(destinationX-startX,2)+math.pow(destinationY-startY,2)))
    directionX = (destinationX - startX) / (math.sqrt(math.pow(destinationX-startX,2)+math.pow(destinationY-startY,2)))
    directionY = (destinationY - startY) / (math.sqrt(math.pow(destinationX-startX,2)+math.pow(destinationY-startY,2)))

    maskPoints = arcpy.Copy_management(start, os.path.join(basePath, r"Trash", r"maskpoints.shp"))

#    cursor = arcpy.da.InsertCursor(maskPoints,("fid","SHAPE@XY"))
    with arcpy.da.InsertCursor(maskPoints,["fid","SHAPE@XY"]) as IC:
        #Insert point back left for leg direction
        IC.insertRow((fid + 1, (startX - (directionY * length / 2) - (directionX * length / 5),
                           startY + (directionX * length / 2) - (directionY * length / 5))))

        #Insert point for back right for leg direction
        IC.insertRow((fid + 2, (startX + (directionY * length / 2) - (directionX * length / 5),
                           startY - (directionX * length / 2) - (directionY * length / 5))))

        #Insert point for front left for leg direction
        IC.insertRow((fid + 3, (destinationX - (directionY * length / 2) + (directionX * length / 5),
                           destinationY + (directionX * length / 2) + (directionY * length / 5))))

        #Insert point for front right for leg direction
        IC.insertRow((fid + 4, (destinationX + (directionY * length / 2) + (directionX * length / 5),
                           destinationY - (directionX * length / 2) + (directionY * length / 5))))
    mask = arcpy.MinimumBoundingGeometry_management(maskPoints, os.path.join(basePath, r"Trash", r"mask.shp"), "RECTANGLE_BY_WIDTH")
#    del IC, maskPoints, directionX, directionY, length, startX, startY, destinationX, destinationY, start, finish
    return mask


def geometryType(infiles):
    polygon = None
    line = None
    point = None
    hasPolygon = False
    hasPolyline = False
    hasPoint = False
    breakBoolean = True
    for file in infiles:
        desc = arcpy.Describe(file)
        geometry = desc.shapeType

        if (geometry.lower() == "Polygon".lower()):
            polygon = file
            hasPolygon = True
        elif (geometry.lower() == "Polyline".lower()):
            line = file
            hasPolyline = True
        elif (geometry.lower() == "Point".lower()):
            point = file
            hasPoint = True
    if hasPolygon and hasPolyline and hasPoint:
        breakBoolean = False
    return polygon, line, point, breakBoolean


def getExtentOfMap(linjesymboler, SlopeL = 101.000, SlopeL2 = 102.000):
    try:
        hoydekurver = arcpy.Select_analysis(linjesymboler, os.path.join(basePath, r"Trash", r"a1"), '"SYMBOL"=' + str(SlopeL) + ' OR "SYMBOL"=' + str(SlopeL2))
        utsnitt1 = arcpy.MinimumBoundingGeometry_management(hoydekurver, os.path.join(basePath, r"Trash", r"a2"), "CONVEX_HULL")
        arcpy.AddField_management(utsnitt1, "UTSNITT", "DOUBLE")
#        features = arcpy.UpdateCursor(utsnitt1)
        with arcpy.da.UpdateCursor(utsnitt1,'UTSNITT') as features:
            for feature in features:
                feature.UTSNITT = 1
                features.updateRow(feature)
            features.reset()
        del feature, features
        dissolved = arcpy.Dissolve_management(utsnitt1, os.path.join(basePath, r"Trash", r"a3"), "UTSNITT")
        return arcpy.MinimumBoundingGeometry_management(dissolved, os.path.join(basePath, r"Trash", r"a4"), "CONVEX_HULL")
    except:
        print("Tried to get extent of OCAD-map but failed")


def addFileToArcMap(filepathFile, mxd):
    #try:
        df = arcpy.mapping.ListDataFrames(mxd, "*")[0]
        newlayer = arcpy.mapping.Layer(filepathFile)
        arcpy.mapping.AddLayer(df, newlayer, "BOTTOM")
        mxd.save()
    #except:
    #    print("Tried but failed to add file to MXD")


def floorSymbols(fc):
#    features = arcpy.UpdateCursor(fc)
    with arcpy.da.UpdateCursor(fc ,'SYMBOL') as features:
        for feature in features:
            feature[0] = math.floor(feature[0])
            features.updateRow(feature)
        features.reset()
    del feature, features


def setCost(fc):
    try:
        arcpy.AddField_management(fc, "COST", "DOUBLE")
        """
        SKAL ENDRES
        """
        costs = [106, 201, 202, 203, 211, 212, 301, 302, 304, 305, 306, 307, 308, 309, 310, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 412, 413, 415, 502, 503, 504, 505, 506, 507, 508, 509, 526, 527, 528, 529]
        hastighet = [5, -1, -1, 5, 0.4, 0.25, -1, -1, 1, 1, 1, -1, 0.25, 1, 0.28, 0.22, 0.25, 0.28, 0.35, 0.3, 0.45, 0.45, 0.7, 0.7, 1, -1, -1, -1, 0.19, 0.19, 0.19, 0.19, 0.2, 0.22, 0.24, 0.28, -1, -1, -1, 0.19]
#        features = arcpy.UpdateCursor(fc)
        with arcpy.da.UpdateCursor(fc, ['SYMBOL', 'COST']) as features:
            for feature in features:
                if int(math.floor(feature[0])) in costs:
                    feature[1] = hastighet[costs.index(int(math.floor(feature[0])))]
                features.updateRow(feature)
            features.reset()
        del feature, features, costs, hastighet
    except:
        print("Tried but failed to set cost")

"""
NOT NEEDED FOR GEOREFERRED FILES, DO NOT USE !!!
def geoProcess(in_data1, destination_data):
    # basePath = .../apps/findbestroute/workfiles/
    print('pleaaaase   ' + basePath)
    arcpy.MinimumBoundingGeometry_management(in_features=destination_data,
                                             out_feature_class=os.path.join(basePath, "Trash", "box"),
                                             geometry_type="ENVELOPE")
    # original box over
    box = os.path.join(basePath, "Trash", "box.shp")

    #    fields = arcpy.ListFields(boxobj)
    #    for field in fields:
    #        print(field.name)

    arcpy.AddGeometryAttributes_management(Input_Features=box, Geometry_Properties="EXTENT")

    #    # arcpy.AddGeometryAttributes_management(Input_Features=os.path.join(basePath, "Trash", "box.shp"), Geometry_Properties="EXTENT")
    #    fields2 = arcpy.ListFields(boxobj)
    #    for field2 in fields2:
    #        print(field2.name)

    #    for field in arcpy.ListFields(dataset=box):
    #        print(field.__str__())

    raster = arcpy.Raster(in_data1)

    inXMax = raster.extent.XMax
    inYMax = raster.extent.YMax
    inXMin = raster.extent.XMin
    inYMin = raster.extent.YMin

    XminValues = [row[0] for row in arcpy.da.SearchCursor(box, "EXT_MIN_X")]
    YMinValues = [row[0] for row in arcpy.da.SearchCursor(box, "EXT_MIN_Y")]
    XMaxValues = [row[0] for row in arcpy.da.SearchCursor(box, "EXT_MAX_X")]
    YMaxValues = [row[0] for row in arcpy.da.SearchCursor(box, "EXT_MAX_Y")]

    destXMin = min(XminValues)
    destYMin = min(YMinValues)
    destXMax = max(XMaxValues)
    destYMax = max(YMaxValues)

    sourceCP = "'" + str(inXMax) + " " + str(inYMax) + "';'" + str(inXMax) + " " + str(inYMin) + "';'" + str(inXMin) + " " + str(inYMax) + "';'" + str(inXMin) + " " + str(inYMin) + "'"
    targetCP = "'" + str(destXMax) + " " + str(destYMax) + "';'" + str(destXMax) + " " + str(destYMin) + "';'" + str(destXMin) + " " + str(destYMax) + "';'" + str(destXMin) + " " + str(destYMin) + "'"

    del XminValues, XMaxValues, YMinValues, YMaxValues
    del inXMax, inYMax, inXMin, inYMin
    del destXMax, destXMin, destYMax, destYMin
    return arcpy.Warp_management(raster, sourceCP, targetCP, os.path.join(basePath, r"Results", "basemap", r"geoKart.jpg"),
                                 "POLYORDER1")
"""




"""
HERE BE MAGIC

"with" statements using arcpy.da.<Cursor>: doesn't release locks.
Splitting the entire script into subroutines: also doesn't release locks.
arcpy.ClearWorkspaceCache_management() also doesn't release locks.

Neither of the deletion methods handle locks at all.

"""
@shared_task
def runScript(uploaderpk):

    print("Starting script")
    startTime = time.time()

    arcpy.env.overwriteOutput = True
    arcpy.env.cellSize = 1
    # Activate spatial analyst extension
    if arcpy.CheckExtension("Spatial") == "Available":
        arcpy.CheckOutExtension("Spatial")

    if arcpy.CheckExtension("3D") == "Available":
        arcpy.CheckOutExtension("3D")

    # basePath = .../apps/findbestroute/workfiles/
    global basePath
    basePath = os.path.join(settings.PROJECT_PATH, 'apps', 'findbestroute', 'workfiles')
    env.workspace = basePath

    mxd = arcpy.mapping.MapDocument(os.path.join(basePath, "mapdoc", r'mapdocument.mxd'))

    """APPARENTLY, MODULES IS A GOOD THING, AND ONE OF THE OTHER FEW WAYS TO ENSURE LOCK REMOVAL."""


    onlyfiles = []
    kart_path = ""  # MUST BE A GEOREF'D MAP OF THE SAME AREA

    for file in os.listdir(os.path.join(settings.PROJECT_PATH, r"files", r"user_" + str(uploaderpk))):
        if file.endswith(".shp"):
            onlyfiles.append(os.path.join(settings.PROJECT_PATH, r"files", r"user_" + str(uploaderpk), file))
        elif file.endswith(".jpg"):
            kart_path = os.path.join(settings.PROJECT_PATH, r"files", r"user_" + str(uploaderpk), file)

    for el in onlyfiles:
        print("File: " + el.__str__())
    print("Map file: " + kart_path.__str__())
    arealsymboler, linjesymboler, punktsymboler, breakBoolean = geometryType(onlyfiles)
    if (breakBoolean):
        print("Datafiles not containing all shapefiles( either point, polyline or polygon)")
        return
    del onlyfiles

    # DO NOT USE #
    #    kart = os.path.join(settings.PROJECT_PATH, r"apps", r"findbestroute", r"workfiles", r"inData", r"kart.jpg") #
    # kart = geoProcess(kart_path, arealsymboler)

    start = getStart(punktsymboler)
    destination = getDestination(punktsymboler)
    mask = setMask(start, destination)

    arcpy.env.mask = os.path.join(basePath, r"Trash", r"mask.shp")

    # Klipper til symbolene etter mask
    ar = arcpy.Clip_analysis(in_features=arealsymboler, clip_features=mask,
                             out_feature_class=os.path.join(basePath, r"Trash", r"a5"), cluster_tolerance="")
    ln = arcpy.Clip_analysis(in_features=linjesymboler, clip_features=mask,
                             out_feature_class=os.path.join(basePath, r"Trash", r"a6"), cluster_tolerance="")
    pt = arcpy.Clip_analysis(in_features=punktsymboler, clip_features=mask,
                             out_feature_class=os.path.join(basePath, r"Trash", r"a7"), cluster_tolerance="")

    # Runde ned alle symboler
    floorSymbols(ar)
    floorSymbols(ln)
    floorSymbols(pt)

    # Lage buffer paa linjer som er lik bredden de skal ha
    fieldnames = [field.name for field in arcpy.ListFields(ln)]
    if not "WIDTH" in fieldnames:
        arcpy.AddField_management(in_table=ln, field_name="WIDTH", field_type="DOUBLE")

#        del fieldnames

    symbols = [106, 107, 201, 203, 304, 305, 307, 502, 503, 504, 505, 506, 507, 508, 509]
    width = [2, 2, 4, 4, 2, 2, 1, 6, 4, 3, 2.5, 2, 2, 2, 2]
    #    cursor = arcpy.UpdateCursor(ln)
    with arcpy.da.UpdateCursor(ln, ['SYMBOL', 'WIDTH']) as cursor:
        for feature in cursor:
            if feature[0] in symbols:
                n = symbols.index(feature[0])
                feature[1] = width[n]
            cursor.updateRow(feature)
        cursor.reset()
#        del feature, cursor, n
    ln_buff = arcpy.Buffer_analysis(in_features=ln, out_feature_class=os.path.join(basePath, r"Trash", r"a8"),
                                    buffer_distance_or_field="WIDTH", line_side="FULL", line_end_type="FLAT",
                                    dissolve_option="LIST", dissolve_field="SYMBOL")
#       del line

    # Hente ut alle forbudte symboler
    forbiddenArea = arcpy.Select_analysis(in_features=arealsymboler, out_feature_class=os.path.join(basePath, r"Trash", r"a9"),
                                          where_clause='"SYMBOL" = 202 OR "SYMBOL" = 211 OR "SYMBOL" = 301 OR "SYMBOL" = 302 OR "SYMBOL" = 307 OR "SYMBOL" = 415 OR "SYMBOL" = 526 OR "SYMBOL" = 527 OR "SYMBOL" = 528 OR "SYMBOL" = 709')
    forbiddenLineBuff = arcpy.Select_analysis(in_features=ln_buff,
                                              out_feature_class=os.path.join(basePath, r"Trash", r"b1"),
                                              where_clause='"SYMBOL" = 201 OR "SYMBOL" = 307 OR "SYMBOL" = 521 OR "SYMBOL" = 524 OR "SYMBOL" = 528 OR "SYMBOL" = 534 OR "SYMBOL" = 709')

    # Hente ut alle passerbare symboler
    passableArea = arcpy.Select_analysis(in_features=arealsymboler, out_feature_class=os.path.join(basePath, r"Trash", r"b2"),
                                         where_clause='"SYMBOL" <> 202 AND "SYMBOL" <> 211 AND "SYMBOL" <> 301 AND "SYMBOL" <> 302 AND "SYMBOL" <> 307 AND "SYMBOL" <> 415 AND "SYMBOL" <> 526 AND "SYMBOL" <> 527 AND "SYMBOL" <> 528 AND "SYMBOL" <> 601 AND "SYMBOL" <> 709')
    passableLineBuff = arcpy.Select_analysis(in_features=ln_buff,
                                             out_feature_class=os.path.join(basePath, r"Trash", r"b3"),
                                             where_clause='"SYMBOL" <> 201 AND "SYMBOL" <> 307 AND "SYMBOL" <> 521 AND "SYMBOL" <> 524 AND "SYMBOL" <> 528 AND "SYMBOL" <> 534 AND "SYMBOL" <> 709')
#        del area

    # Lage skogflater
    area = arcpy.Update_analysis(in_features=passableArea, update_features=forbiddenArea,
                                 out_feature_class=os.path.join(basePath, r"Trash", r"b4"))
    forest = arcpy.Erase_analysis(in_features=mask, erase_features=area,
                                  out_feature_class=os.path.join(basePath, r"Trash", r"b5"))
    arcpy.AddField_management(in_table=forest, field_name="SYMBOL", field_type="DOUBLE")
    #    cursor = arcpy.UpdateCursor(forest)
    with arcpy.da.UpdateCursor(forest, 'SYMBOL') as cursor:
        for feature in cursor:
            feature[0] = 405
            cursor.updateRow(feature)
        cursor.reset()
#        del feature, cursor, mask

    # Lage kartet i ArcMap
    area1 = arcpy.Erase_analysis(in_features=passableArea, erase_features=forbiddenArea,
                                 out_feature_class=os.path.join(basePath, r"Trash", r"b6"))
    area2 = arcpy.Erase_analysis(in_features=area1, erase_features=forbiddenLineBuff,
                                 out_feature_class=os.path.join(basePath, r"Trash", r"b7"))
    passable1 = arcpy.Update_analysis(in_features=area2, update_features=forest,
                                      out_feature_class=os.path.join(basePath, r"Trash", r"b8"))
    mapped = arcpy.Update_analysis(in_features=passable1, update_features=passableLineBuff,
                                   out_feature_class=os.path.join(basePath, r"Trash", r"b9"))

#        del forbiddenArea, forbiddenLineBuff, forest, area, passable1, passableArea, passableLineBuff, ln_buff

    # Sette kostnad paa alle flater
    setCost(mapped)
    print('hey')
    costRaster = arcpy.FeatureToRaster_conversion(mapped, "COST",
                                                  os.path.join(basePath, r"Results", r"CostRaster.tif"))

    # Rasterkalkulator som lager raster som tar hensyn til hoyde i kostnadsrasteret
    finalCostRaster = Raster(os.path.join(basePath, r"Results", r"CostRaster.tif"))

    # Regne ut leastcostpath
    cdr = arcpy.sa.CostDistance(start, finalCostRaster)
    cdr.save(os.path.join(basePath, r"Results", r"costdist"))
    cbr = arcpy.sa.CostBackLink(start, finalCostRaster)
    cbr.save(os.path.join(basePath, r"Results", r"costback"))
    cp = arcpy.sa.CostPath(destination, cdr, cbr, "EACH_CELL")
    cp.save(os.path.join(basePath, r"Results", r"costpath"))

#        del cdr, cbr, cp

    # Gjore om PATH polygon med litt bredde
    arcpy.RasterToPolygon_conversion(in_raster=os.path.join(basePath, r"Results", r"costpath"),
                                     out_polygon_features=os.path.join(basePath, r"Results", r"cpPoly.shp"),
                                     simplify="SIMPLIFY")
    arcpy.Buffer_analysis(in_features=os.path.join(basePath, r"Results", r"cpPoly.shp"),
                          out_feature_class=os.path.join(basePath, r"Results", r"LCP.shp"),
                          buffer_distance_or_field="2", line_side="FULL", line_end_type="FLAT",
                          dissolve_option="LIST")

    df = arcpy.mapping.ListDataFrames(mxd, "*")[0]

    """DELETE LAYERS, NECESSARY ALSO FOR WORKING LOCALLY"""
    for lyr in arcpy.mapping.ListLayers(mxd, "", df):
        arcpy.mapping.RemoveLayer(df, lyr)
    print("Deleted lyr's in mxd")

    # Lage postsirkler og linje og legge til dette i ArcGIS
    points = arcpy.CreateFeatureclass_management(out_path=os.path.join(basePath, r"Trash"),
                                                 out_name="points",
                                                 geometry_type="POINT")
#        del endPoint
    startPt = getStart(pt)
    endPoint = getDestination(pt)
#        del pt
    #    cursor = arcpy.SearchCursor(start)
    startX, startY, destX, destY = 0, 0, 0, 0

    with arcpy.da.SearchCursor(startPt, 'SHAPE@XY') as cursor:
        for feature in cursor:
            startX, startY = feature[0]
        cursor.reset()
#        del cursor, startPt

    #    cursor = arcpy.SearchCursor(destination)
    with arcpy.da.SearchCursor(endPoint, 'SHAPE@XY') as cursor:
        for feature in cursor:
            destX, destY = feature[0]
        cursor.reset()
#        del endPoint, cursor

    #    cursor = arcpy.da.InsertCursor(points, ("fid", "SHAPE@XY"))
    with arcpy.da.InsertCursor(points, ("fid", "SHAPE@XY")) as cursor:
        cursor.insertRow((1, (startX, startY)))
        cursor.insertRow((2, (destX, destY)))
#        del cursor

    outerCircle = arcpy.CreateFeatureclass_management(out_path=os.path.join(basePath, r"Trash"),
                                                      out_name="circles1.shp",
                                                      geometry_type="POLYGON")
    innerCircle = arcpy.CreateFeatureclass_management(out_path=os.path.join(basePath, r"Trash"),
                                                      out_name="circles2.shp",
                                                      geometry_type="POLYGON")
    circle = arcpy.CreateFeatureclass_management(out_path=os.path.join(basePath, r"Trash"),
                                                 out_name="circles.shp",
                                                 geometry_type="POLYGON",
                                                 )
    arcpy.Buffer_analysis(points, outerCircle, 40)
    arcpy.Buffer_analysis(points, innerCircle, 35)
#        del points
    arcpy.Erase_analysis(outerCircle, innerCircle, circle)
#       del innerCircle, outerCircle

    # Lage postlinje
    lines = arcpy.CreateFeatureclass_management(out_path=os.path.join(basePath, r"Trash"),
                                                out_name="line.shp",
                                                geometry_type="POLYGON")
    directionX = (destX - startX) / (math.sqrt(math.pow(destX - startX, 2) + math.pow(destY - startY, 2)))
    directionY = (destY - startY) / (math.sqrt(math.pow(destX - startX, 2) + math.pow(destY - startY, 2)))
    featureset = []
    featureset.append(arcpy.Polyline(arcpy.Array([arcpy.Point(startX + 45 * directionX, startY + 45 * directionY),
                                                  arcpy.Point(destX - 45 * directionX, destY - 45 * directionY)])))
#        del directionX, directionY
    lineFeat = arcpy.CopyFeatures_management(featureset, os.path.join(basePath, r"Trash", r"lines.shp"))
    arcpy.Buffer_analysis(in_features=lineFeat, out_feature_class=lines, buffer_distance_or_field=2.5,
                          line_end_type="FLAT")
#       del featureset

    # Legge til i ArcMap
    data = arcpy.mapping.ListDataFrames(mxd, "*")[0]

    """ NEDERSTE LAG HERREGUD DETTA SKAL LIKSOM BLI BAKGRUNNEN """
    arcpy.MakeRasterLayer_management(in_raster=kart_path,
                                     out_rasterlayer=os.path.join(basePath, r"Results", r"rasterkart"))
    mapLayer = arcpy.mapping.Layer(os.path.join(basePath, r"Results", r"rasterkart"))
    pathLayer = arcpy.mapping.Layer(os.path.join(basePath, r"Results", r"LCP.shp"))
    pathLayer.transparency = 30
    lineLayer = arcpy.mapping.Layer(os.path.join(basePath, r"Trash", r"line.shp"))
    circleLayer = arcpy.mapping.Layer(os.path.join(basePath, r"Trash", r"circles.shp"))
    """ COLOURING LAYERS """
    fixColour = False
    if fixColour:
        symLayer = arcpy.mapping.Layer(os.path.join(basePath, r"Template", r"color2.lyr"))
        templateLayer = arcpy.mapping.Layer(os.path.join(basePath, r"Template", r"colorTemplate.lyr"))
        arcpy.ApplySymbologyFromLayer_management(in_layer=pathLayer,
                                                 in_symbology_layer=templateLayer)
        #                                             in_symbology_layer = os.path.join(basePath, r"Template", r"colorTemplate.lyr")) #alternative
        arcpy.ApplySymbologyFromLayer_management(in_layer=lineLayer, in_symbology_layer=symLayer)
        arcpy.ApplySymbologyFromLayer_management(in_layer=circleLayer, in_symbology_layer=symLayer)
#            del symLayer, templateLayer

    arcpy.mapping.AddLayer(data_frame=data, add_layer=circleLayer, add_position="TOP")
    arcpy.mapping.AddLayer(data_frame=data, add_layer=lineLayer, add_position="TOP")
    arcpy.mapping.AddLayer(data_frame=data, add_layer=pathLayer, add_position="TOP")
    arcpy.mapping.AddLayer(data_frame=data, add_layer=mapLayer, add_position="BOTTOM")

#        del lineLayer, circleLayer, pathLayer, mapLayer

    mxd.save()
    # Skrive ut bilde av veivalg
    B = df.extent.XMax - df.extent.XMin
    H = df.extent.YMax - df.extent.YMin

    filename = str(uploaderpk) + "_" + time.strftime("%d-%m-%Y") + "_" + time.strftime("%H-%M-%S") + ".png"
    relative_path_string = os.path.join(r"Dump", filename)
    print("hurr  " + settings.PROJECT_PATH)
    print("durr " + relative_path_string)
    out_path = os.path.join(settings.PROJECT_PATH, "files", r"Dump", filename)
    print(out_path)
    arcpy.mapping.ExportToPNG(map_document=mxd, out_png=out_path, data_frame=df,
                              df_export_width=int(3 * B), df_export_height=int(3 * H), resolution=225)
    print("Finished making image")

    # relative_path = os.path.join(r"Dump", "MapLCP.png")
    img = Image()
    img.uploader = PathUser.objects.get(pk=uploaderpk)
    img.bilde = relative_path_string
    img.save()

    arcpy.ClearWorkspaceCache_management()

    # use numbers to keep ensure usage of the latest possible vars.



    print("Deletion coming up...")
    sleep(2)

    end = time.time()
    print("FINISH TIME:    " + str(end-startTime))
