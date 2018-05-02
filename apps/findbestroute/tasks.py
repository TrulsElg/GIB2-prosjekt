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
import os
"""
PASSED FROM views.py: request.user; now named user.

CURRENTLY BUGGED AT: line 154; trying to extract extents after they are added.
Extents are not added properly...?
"""


@shared_task
def local_test(number, user):
    for i in range(number):
        print('hurr durr  ' + str((pow(i, 2))))
    sleep(10)
    UploadedFile.objects.filter(uploader=PathUser.objects.get(username=user)).delete()

    return


# FIXME
@shared_task
def find_best_route(user):
    """
    :param user = request.user, from views.last_opp_filer(request)
    :return:
    """
    files = UploadedFile.objects.filter(uploader=user)
    # fetches ALL the uploads belonging to the user. includes shape, jpg...
    # see valid file__types in models or forms

    print('Finding best route...')
    do_analysis(files, user)

    for i in range(3):
        print('Sleeping for '+ str(3-i) + ' seconds...')
        sleep(1)

    delete_user_uploads(uploader=user)
    print('Filene har blitt slettet. Ferdig med analyse.')


# FIXME return the image file with the optimal path
@shared_task
def do_analysis(files, user):
    print('Doing analysis...')
    # legg inn: mappenavn i rekkefolge, deretter filnavn (og -type)
    path = os.path.join('test_files', "images.png")
    print(path)
#    f = open(path, 'r')
#    file = File(f)
    image_object = models.Image()
    image_object.bilde = path
    image_object.uploader = user
    image_object.save()


"""
    result_object = models.ResultFile()
    result_object.owner = user
    result_object.file = img
    result_object.save()
"""


@shared_task
def delete_user_uploads(uploader):
    UploadedFile.objects.filter(uploader=uploader).delete()


def getStart(pt):
    try:
        start = arcpy.Select_analysis(pt, os.path.join(basePath, r"Trash", r"start.shp"), '"SYMBOL" = 701 AND "ANGLE" = 0')
        arcpy.AddXY_management(start)
    except:
        print("Failed to getStart()")
    return start


def getDestination(pt):
    try:
        destination = arcpy.Select_analysis(pt,os.path.join(basePath, r"Trash", r"destination.shp"),'"SYMBOL" = 706')
        arcpy.AddXY_management(destination)
    except:
        print("Failed to getStart()")
    return destination


def setMask(start, finish):
    features = arcpy.UpdateCursor(start)
    for feature in features:
        startX = feature.POINT_X
        startY = feature.POINT_Y
    del feature, features
    features = arcpy.UpdateCursor(finish)
    for feature in features:
        destinationX = feature.POINT_X
        destinationY = feature.POINT_Y
        fid = feature.FID
    del feature, features
    length = (math.sqrt(math.pow(destinationX-startX,2)+math.pow(destinationY-startY,2)))
    directionX = (destinationX - startX) / (math.sqrt(math.pow(destinationX-startX,2)+math.pow(destinationY-startY,2)))
    directionY = (destinationY - startY) / (math.sqrt(math.pow(destinationX-startX,2)+math.pow(destinationY-startY,2)))

    maskPoints = arcpy.Copy_management(start, os.path.join(basePath, r"Trash", r"maskpoints.shp"))
    cursor = arcpy.da.InsertCursor(maskPoints,("fid","SHAPE@XY"))

    #Insert point back left for leg direction
    cursor.insertRow((fid + 1, (startX - (directionY * length / 2) - (directionX * length / 5),
                       startY + (directionX * length / 2) - (directionY * length / 5))))

    #Insert point for back right for leg direction
    cursor.insertRow((fid + 2, (startX + (directionY * length / 2) - (directionX * length / 5),
                       startY - (directionX * length / 2) - (directionY * length / 5))))

    #Insert point for front left for leg direction
    cursor.insertRow((fid + 3, (destinationX - (directionY * length / 2) + (directionX * length / 5),
                       destinationY + (directionX * length / 2) + (directionY * length / 5))))

    #Insert point for front right for leg direction
    cursor.insertRow((fid + 4, (destinationX + (directionY * length / 2) + (directionX * length / 5),
                       destinationY - (directionX * length / 2) + (directionY * length / 5))))
    del cursor
    mask = arcpy.MinimumBoundingGeometry_management(maskPoints, os.path.join(basePath, r"Trash", r"mask.shp"), "RECTANGLE_BY_WIDTH")
    return mask


def geoProcess(in_data1, destination_data):
    # basePath = .../apps/findbestroute/workfiles/
    print('pleaaaase   ' + basePath)
    box = arcpy.MinimumBoundingGeometry_management(destination_data, os.path.join(basePath, "Trash", "box.shp"),
                                                   "ENVELOPE")
    arcpy.AddGeometryAttributes_management(Input_Features=box, Geometry_Properties="EXTENT")
#    # arcpy.AddGeometryAttributes_management(Input_Features=os.path.join(basePath, "Trash", "box.shp"), Geometry_Properties="EXTENT")

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

    sourceCP = "'" + str(inXMax) + " " + str(inYMax) + "';'" + str(inXMax) + " " + str(inYMin) + "';'" + str(
        inXMin) + " " + str(inYMax) + "';'" + str(inXMin) + " " + str(inYMin) + "'"
    targetCP = "'" + str(destXMax) + " " + str(destYMax) + "';'" + str(destXMax) + " " + str(destYMin) + "';'" + str(
        destXMin) + " " + str(destYMax) + "';'" + str(destXMin) + " " + str(destYMin) + "'"

    return arcpy.Warp_management(raster, sourceCP, targetCP, os.path.join(basePath, r"Results", r"geoKart.jpg"),
                                 "POLYORDER1")


def geometryType(infiles):
    polygon = None
    line = None
    point = None
    for file in infiles:
        desc = arcpy.Describe(file)
        geometry = desc.shapeType

        if (geometry.lower() == "Polygon".lower()):
            polygon = file
        elif (geometry.lower() == "Polyline".lower()):
            line = file
        elif (geometry.lower() == "Point".lower()):
            point = file
    return polygon, line, point

def getExtentOfMap(linjesymboler, SlopeL = 101.000, SlopeL2 = 102.000):
    try:
        hoydekurver = arcpy.Select_analysis(linjesymboler, os.path.join(basePath, r"Trash", r"a1"), '"SYMBOL"=' + str(SlopeL) + ' OR "SYMBOL"=' + str(SlopeL2))
        utsnitt1 = arcpy.MinimumBoundingGeometry_management(hoydekurver, os.path.join(basePath, r"Trash", r"a2"), "CONVEX_HULL")
        arcpy.AddField_management(utsnitt1, "UTSNITT", "DOUBLE")
        features = arcpy.UpdateCursor(utsnitt1)
        for feature in features:
            feature.UTSNITT = 1
            features.updateRow(feature)
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
    features = arcpy.UpdateCursor(fc)
    for feature in features:
        feature.SYMBOL = math.floor(feature.SYMBOL)
        features.updateRow(feature)
    del feature, features


def setCost(fc):
    try:
        arcpy.AddField_management(fc, "COST", "DOUBLE")
        features = arcpy.UpdateCursor(fc)
        """
        SKAL ENDRES
        """
        costs = [106, 201, 202, 203, 211, 212, 301, 302, 304, 305, 306, 307, 308, 309, 310, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 412, 413, 415, 502, 503, 504, 505, 506, 507, 508, 509, 526, 527, 528, 529]
        hastighet = [5, -1, -1, 5, 0.4, 0.25, -1, -1, 1, 1, 1, -1, 0.25, 1, 0.28, 0.22, 0.25, 0.28, 0.35, 0.3, 0.45, 0.45, 0.7, 0.7, 1, -1, -1, -1, 0.19, 0.19, 0.19, 0.19, 0.2, 0.22, 0.24, 0.28, -1, -1, -1, 0.19]
        for feature in features:
            if int(math.floor(feature.SYMBOL)) in costs:
                feature.COST = hastighet[costs.index(int(math.floor(feature.SYMBOL)))]
            features.updateRow(feature)
        del feature, features
    except:
        print("Tried but failed to set cost")

"""

HER BE MAGIC

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
    sleep(2)
    basePath = os.path.join(settings.PROJECT_PATH, 'apps', 'findbestroute', 'workfiles')
    env.workspace = basePath
    sleep(2)

    mxd = arcpy.mapping.MapDocument(os.path.join(basePath, r'mapdocument.mxd'))

    inputShape = [os.path.join(basePath, r"inData", r"Skog_ar.shp"),
                  os.path.join(basePath, r"inData", r"Skog_ln.shp"),
                  os.path.join(basePath, r"inData", r"Skog_pt.shp")]
    arealsymboler, linjesymboler, punktsymboler = geometryType(inputShape)
    kart = geoProcess(os.path.join(basePath, r"indata", r"kart.jpg"), arealsymboler)

    start = getStart(punktsymboler)
    destination = getDestination(punktsymboler)
    mask = setMask(start, destination)

    arcpy.env.mask = os.path.join(basePath, r"Trash", r"mask.shp")


    utsnitt = getExtentOfMap(linjesymboler)

    hoydedata = arcpy.Clip_analysis(in_features= os.path.join(basePath, r"hoydeData", r"trondheiml.shp"),
                                    clip_features= utsnitt,
                                    out_feature_class= os.path.join(basePath, r"Trash", r"hoydedata.shp"),
                                    cluster_tolerance="")

    #Klipper til symbolene etter mask
    ar = arcpy.Clip_analysis(in_features=arealsymboler, clip_features=mask,out_feature_class=os.path.join(basePath, r"Trash", r"a5"),cluster_tolerance="")
    ln = arcpy.Clip_analysis(in_features=linjesymboler, clip_features=mask,out_feature_class=os.path.join(basePath, r"Trash", r"a6"),cluster_tolerance="")
    pt = arcpy.Clip_analysis(in_features=punktsymboler, clip_features=mask,out_feature_class=os.path.join(basePath, r"Trash", r"a7"),cluster_tolerance="")

    #Runde ned alle symboler
    floorSymbols(ar)
    floorSymbols(ln)
    floorSymbols(pt)

    #Lage buffer paa linjer som er lik bredden de skal ha
    fieldnames = [field.name for field in arcpy.ListFields(ln)]
    if not "WIDTH" in fieldnames:
        arcpy.AddField_management(in_table=ln, field_name="WIDTH", field_type="DOUBLE")
    symbols = [106, 107, 201, 203, 304, 305, 307, 502, 503, 504, 505, 506, 507, 508, 509]
    width = [2,2,4,4,2,2,1,6,4,3,2.5,2,2,2,2]
    features = arcpy.UpdateCursor(ln)
    for feature in features:
        if feature.SYMBOL in symbols:
            n = symbols.index(feature.SYMBOL)
            feature.WIDTH = width[n]
        features.updateRow(feature)
    del feature, features, n
    ln_buff = arcpy.Buffer_analysis(in_features=ln, out_feature_class=os.path.join(basePath, r"Trash", r"a8"), buffer_distance_or_field= "WIDTH", line_side="FULL", line_end_type="FLAT", dissolve_option="LIST", dissolve_field="SYMBOL")

    #Hente ut alle forbudte symboler
    forbiddenArea = arcpy.Select_analysis(in_features= ar, out_feature_class=os.path.join(basePath, r"Trash", r"a9"),where_clause= '"SYMBOL" = 202 OR "SYMBOL" = 211 OR "SYMBOL" = 301 OR "SYMBOL" = 302 OR "SYMBOL" = 307 OR "SYMBOL" = 415 OR "SYMBOL" = 526 OR "SYMBOL" = 527 OR "SYMBOL" = 528 OR "SYMBOL" = 709')
    forbiddenLineBuff = arcpy.Select_analysis(in_features= ln_buff, out_feature_class= os.path.join(basePath, r"Trash", r"b1"), where_clause= '"SYMBOL" = 201 OR "SYMBOL" = 307 OR "SYMBOL" = 521 OR "SYMBOL" = 524 OR "SYMBOL" = 528 OR "SYMBOL" = 534 OR "SYMBOL" = 709')

    #Hente ut alle passerbare symboler
    passableArea = arcpy.Select_analysis(in_features= ar, out_feature_class= os.path.join(basePath, r"Trash", r"b2"), where_clause= '"SYMBOL" <> 202 AND "SYMBOL" <> 211 AND "SYMBOL" <> 301 AND "SYMBOL" <> 302 AND "SYMBOL" <> 307 AND "SYMBOL" <> 415 AND "SYMBOL" <> 526 AND "SYMBOL" <> 527 AND "SYMBOL" <> 528 AND "SYMBOL" <> 601 AND "SYMBOL" <> 709')
    passableLineBuff = arcpy.Select_analysis(in_features= ln_buff, out_feature_class= os.path.join(basePath, r"Trash", r"b3"), where_clause= '"SYMBOL" <> 201 AND "SYMBOL" <> 307 AND "SYMBOL" <> 521 AND "SYMBOL" <> 524 AND "SYMBOL" <> 528 AND "SYMBOL" <> 534 AND "SYMBOL" <> 709')

    #Lage skogflater
    area = arcpy.Update_analysis(in_features=passableArea, update_features=forbiddenArea,out_feature_class=os.path.join(basePath, r"Trash", r"b4"))
    forest = arcpy.Erase_analysis(in_features=mask, erase_features=area, out_feature_class=os.path.join(basePath, r"Trash", r"b5"))
    arcpy.AddField_management(in_table=forest, field_name="SYMBOL",field_type="DOUBLE")
    features = arcpy.UpdateCursor(forest)
    for feature in features:
        feature.SYMBOL = 405
        features.updateRow(feature)
    del feature, features

    #Lage kartet i ArcMap
    area1 = arcpy.Erase_analysis(in_features= passableArea, erase_features= forbiddenArea, out_feature_class= os.path.join(basePath, r"Trash", r"b6"))
    area2 = arcpy.Erase_analysis(in_features= area1, erase_features= forbiddenLineBuff, out_feature_class= os.path.join(basePath, r"Trash", r"b7"))
    passable1 = arcpy.Update_analysis(in_features= area2, update_features=forest, out_feature_class=os.path.join(basePath, r"Trash", r"b8"))
    mapped = arcpy.Update_analysis(in_features=passable1, update_features=passableLineBuff, out_feature_class=os.path.join(basePath, r"Trash", r"b9"))

    #Sette kostnad paa alle flater
    setCost(mapped)

    costRaster = arcpy.FeatureToRaster_conversion(mapped,"COST",os.path.join(basePath, r"Results", r"CostRaster.tif"))

    #Lage sloperaster

    #create a TIN of the area
    tin = arcpy.CreateTin_3d(out_tin= os.path.join(basePath, r"Results", r"TIN"), spatial_reference= "#", in_features= os.path.join(basePath, r"Trash", r"hoydedata.shp") +" HOEYDE masspoints")

    # Replace a layer/table view name with a path to a dataset (which can be a layer file) or create the layer/table view within the script
    # The following inputs are layers or table views: "hoydeTIN"
    tinRaster = arcpy.TinRaster_3d(in_tin=os.path.join(basePath, r"Results", r"TIN"), out_raster=os.path.join(basePath, r"Results", "hRaster"), data_type="FLOAT", method="LINEAR", sample_distance="CELLSIZE 1", z_factor="1")

    # Replace a layer/table view name with a path to a dataset (which can be a layer file) or create the layer/table view within the script
    # The following inputs are layers or table views: "hraster"
    slope = arcpy.Slope_3d(in_raster=os.path.join(basePath, r"Results", r"hRaster"), out_raster=os.path.join(basePath, r"Results", r"slope"), output_measurement="DEGREE", z_factor="1")

    # Reklassifisering av slope
    reMapRange = RemapRange([[0, 0.5, 100], [0.5, 1, 101], [1, 2, 102], [2, 3, 103], [3, 4, 104], [4, 5, 105], [5, 6, 106], [6, 7, 107],[7, 8, 108], [8, 9, 109], [9, 10, 110], [10, 11, 111], [11, 12, 112], [12, 13, 113], [13, 14, 114], [14, 15, 115], [15, 16, 116], [16, 17, 117], [17, 18, 118], [18, 19, 119], [19, 20, 120], [20, 90, 150]])
    slope_reclass = Reclassify(in_raster= os.path.join(basePath, r"Results", r"slope"), reclass_field= "VALUE", remap= reMapRange)
    slope_reclass.save(os.path.join(basePath, r"Results", r"slopeReclass"))

    # Rasterkalkulator som lager raster som tar hensyn til hoyde i kostnadsrasteret
    finalCostRaster = Raster(os.path.join(basePath, r"Results", r"CostRaster.tif")) * (Raster(os.path.join(basePath, r"Results", r"slopeReclass")) / 100)

    #Regne ut leastcostpath
    cdr = arcpy.sa.CostDistance(start,finalCostRaster)
    cdr.save(os.path.join(basePath, r"Results", r"costDistance"))
    cbr = arcpy.sa.CostBackLink(start,finalCostRaster)
    cbr.save(os.path.join(basePath, r"Results", r"Costback"))
    cp = arcpy.sa.CostPath(destination,cdr,cbr,"EACH_CELL")
    cp.save(os.path.join(basePath, r"Results", r"costpath"))

    #Gjore om til polygon med litt bredde
    arcpy.RasterToPolygon_conversion(in_raster= os.path.join(basePath, r"Results", r"costpath"), out_polygon_features= os.path.join(basePath, r"Results", r"cpPoly.shp"), simplify="SIMPLIFY")
    arcpy.Buffer_analysis(in_features=os.path.join(basePath, r"Results", r"cpPoly.shp"), out_feature_class= os.path.join(basePath, r"Results", r"LCP.shp"), buffer_distance_or_field= "2", line_side="FULL", line_end_type="FLAT", dissolve_option="LIST")

    #Legge til i ArcMap
    templateLayer = arcpy.mapping.Layer(os.path.join(basePath, r"Template",  r"colorTemplate.lyr"))
    df = arcpy.mapping.ListDataFrames(mxd, "*")[0]
    newlayer = arcpy.mapping.Layer(os.path.join(basePath, r"Results", r"LCP.shp"))
    newlayer.transparency = 50
    arcpy.ApplySymbologyFromLayer_management(in_layer=newlayer, in_symbology_layer=templateLayer)
    arcpy.mapping.AddLayer(df, newlayer, "BOTTOM")
    arcpy.MakeRasterLayer_management(in_raster=kart, out_rasterlayer=os.path.join(basePath, r"Trash", r"kart"))
    mapLayer = arcpy.mapping.Layer(os.path.join(basePath, r"Trash", r"kart"))
    arcpy.mapping.AddLayer(df, mapLayer, "BOTTOM")

    # Lage postsirkler og linje og legge til dette i ArcMap
    points = arcpy.CreateFeatureclass_management(out_path=os.path.join(basePath, r"Trash"),
                                                 out_name="points",
                                                 geometry_type="POINT")
    start = getStart(pt)
    destination = getDestination(pt)
    features = arcpy.UpdateCursor(start)
    for feature in features:
        startX = feature.POINT_X
        startY = feature.POINT_Y
    features = arcpy.UpdateCursor(destination)
    for feature in features:
        destX = feature.POINT_X
        destY = feature.POINT_Y
    cursor = arcpy.da.InsertCursor(points, ("fid", "SHAPE@XY"))
    cursor.insertRow((1, (startX, startY)))
    cursor.insertRow((2, (destX, destY)))

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
    arcpy.Erase_analysis(outerCircle, innerCircle, circle)
    symLayer = arcpy.mapping.Layer(os.path.join(basePath, r"Template", r"color2.lyr"))
    circleLayer = arcpy.mapping.Layer(os.path.join(basePath, r"Trash", r"circles.shp"))
    arcpy.ApplySymbologyFromLayer_management(in_layer=circleLayer, in_symbology_layer=symLayer)
    arcpy.mapping.AddLayer(data_frame=df, add_layer=circleLayer, add_position="TOP")

    # Lage postlinje
    lines = arcpy.CreateFeatureclass_management(out_path=os.path.join(basePath, r"Trash"),
                                                out_name="line.shp",
                                                geometry_type="POLYGON")
    directionX = (destX - startX) / (math.sqrt(math.pow(destX - startX, 2) + math.pow(destY - startY, 2)))
    directionY = (destY - startY) / (math.sqrt(math.pow(destX - startX, 2) + math.pow(destY - startY, 2)))
    features = []
    features.append(arcpy.Polyline(arcpy.Array([arcpy.Point(startX + 45 * directionX, startY + 45 * directionY),
                                                arcpy.Point(destX - 45 * directionX, destY - 45 * directionY)])))
    lineFeat = arcpy.CopyFeatures_management(features, os.path.join(basePath, r"Trash", r"lines.shp"))
    arcpy.Buffer_analysis(in_features=lineFeat, out_feature_class=lines, buffer_distance_or_field=2.5,
                          line_end_type="FLAT")
    lineLayer = arcpy.mapping.Layer(os.path.join(basePath, r"Trash", r"line.shp"))
    arcpy.ApplySymbologyFromLayer_management(in_layer=lineLayer, in_symbology_layer=symLayer)
    arcpy.mapping.AddLayer(data_frame=df, add_layer=lineLayer, add_position="TOP")

    mxd.save()


    #Skrive ut bilde av veivalg
    B = df.extent.XMax - df.extent.XMin
    H = df.extent.YMax - df.extent.YMin

    relative_path_string = os.path.join(r"Dump", r"MapLCP.png")
    print("hurr  " + settings.PROJECT_PATH)
    print("durr " + relative_path_string)
    out_path = os.path.join(settings.PROJECT_PATH, "files", r"Dump", r"MapLCP.png")
    print(out_path)
    arcpy.mapping.ExportToPNG(map_document= mxd, out_png= out_path, data_frame= df,
                              df_export_width= int(3*B), df_export_height= int(3*H), resolution=225)
    print("Finished making image")

    relative_path = os.path.join(r"Dump", "MapLCP.png")
    img = Image()
    img.uploader = PathUser.objects.get(pk=uploaderpk)
    img.bilde = relative_path
    img.save()


    end = time.time()
    print(end-startTime)