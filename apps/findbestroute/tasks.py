from celery import shared_task
from time import sleep

from apps.findbestroute.models import *
from PIL import Image as pilImage

import time
import arcpy
import math
from arcpy import env
from arcpy.sa import *
import os
from arcpy import mapping
from django.conf import settings


@shared_task
def test_task():
    secs = 10
    print('Starting background task {}'.format(secs))
    print "Test"
    sleep(secs)
    print "finished"
    print "Completed waiting for {} seconds".format(secs)


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

#def addTable(excel_file, table_out_file, sheetName):
#    hastighetInn = "../../Data/Hastighet2.xlsx"
#    tabellUt = "../../Kladd/lopshastighet.gdb"
#    arcpy.ExcelToTable_conversion(hastighetInn, tabellUt, "hastArk")

def floorSymbols(fc):
    features = arcpy.UpdateCursor(fc)
    for feature in features:
        feature.SYMBOL = math.floor(feature.SYMBOL)
        features.updateRow(feature)
    del feature, features

#def setCost(fc, dbPath):
def setCost(fc):
    try:
        arcpy.AddField_management(fc, "COST", "DOUBLE")
        features = arcpy.UpdateCursor(fc)
        #import xlrd funker ikke. Neste to linjer er en annen losning.
        costs = [106, 201, 202, 203, 211, 212, 301, 302, 304, 305, 306, 307, 308, 309, 310, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 412, 413, 415, 502, 503, 504, 505, 506, 507, 508, 509, 526, 527, 528, 529]
        hastighet = [5, -1, -1, 5, 0.4, 0.25, -1, -1, 1, 1, 1, -1, 0.25, 1, 0.28, 0.22, 0.25, 0.28, 0.35, 0.3, 0.45, 0.45, 0.7, 0.7, 1, -1, -1, -1, 0.19, 0.19, 0.19, 0.19, 0.2, 0.22, 0.24, 0.28, -1, -1, -1, 0.19]
        for feature in features:
            #costs = arcpy.UpdateCursor(dbPath)
            if int(math.floor(feature.SYMBOL)) in costs:
                feature.COST = hastighet[costs.index(int(math.floor(feature.SYMBOL)))]
            features.updateRow(feature)
        del feature, features
    except:
        print("Tried but failed to set cost")

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

    global basePath
    basePath =  r"C:\Users\Truls\PycharmProjects\GIB2-prosjekt\apps\findbestroute\workfiles" #os.path.join(os.getcwd(), r"workfiles")
    env.workspace = basePath
    mxd = arcpy.mapping.MapDocument(os.path.join(basePath, r"mapDocument.mxd"))

    arealsymboler = os.path.join(basePath, r"inData", r"Skog_ar.shp")
    linjesymboler = os.path.join(basePath, r"inData", r"Skog_ln.shp")
    punktsymboler = os.path.join(basePath, r"inData", r"Skog_pt.shp")

    start = getStart(punktsymboler)
    destination = getDestination(punktsymboler)
    mask = setMask(start,destination)

    arcpy.env.mask = os.path.join(basePath, r"Trash", r"mask.shp")


    utsnitt = getExtentOfMap(linjesymboler)

    hoydedata = arcpy.Clip_analysis(in_features= os.path.join(basePath, r"Trondheim5m", r"Trondheim5m.shp"), clip_features= utsnitt, out_feature_class= os.path.join(basePath, r"Trash", r"hoydedata.shp"), cluster_tolerance="")

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

    #Hente inn hastighetstabell
    #arcpy.CreateFileGDB_management(out_folder_path= basePath, out_name= "outgdb.gdb")
    #hastighetInn = os.path.join(basePath, r"\hasightet2.xlsx")
    #tabellUt = os.path.join(basePath, r"\outgdb.gdb")
    #arcpy.ExcelToTable_conversion(hastighetInn, tabellUt, "hastArk")

    #Sette kostnad paa alle flater
    setCost(mapped)

    costRaster = arcpy.FeatureToRaster_conversion(mapped,"COST",os.path.join(basePath, r"Results", r"CostRaster.tif"))

    #Lage sloperaster

    #create a TIN of the area
    tin = arcpy.CreateTin_3d(out_tin= os.path.join(basePath, r"Results", r"TIN"), spatial_reference= "#", in_features= os.path.join(basePath, r"Trash", r"hoydedata.shp") +" HOEYDE masspoints")
    #para_in = "hoydedata.shp" + " " + "HOEYDE" + " Mass_Points <None>;" + "mask.shp" + " " + "<None>" + " Soft_Clip <None>"
    #tin = arcpy.CreateTin_3d (out_tin= os.path.join(basePath, r"Results", r"TIN"), spatial_reference= "", in_features= para_in, constrained_delaunay="DELAUNAY")


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

    #Klippe kartbilde
    #klipp = arcpy.MinimumBoundingGeometry_management(mask, os.path.join(basePath, r"Trash", r"klipp"), "ENVELOPE")
    #kart = arcpy.Clip_management(in_raster= os.path.join(basePath, r"inData", r"VikaasenReppesaasen290817.jpg"), rectangle= klipp, out_raster= os.path.join(basePath, r"inData", r"kart.jpg"))

    #Legge til i ArcMap
    templateLayer = arcpy.mapping.Layer(os.path.join(basePath, r"colorTemplate.lyr"))
    df = arcpy.mapping.ListDataFrames(mxd, "*")[0]
    newlayer = arcpy.mapping.Layer(os.path.join(basePath, r"Results", r"LCP.shp"))
    newlayer.transparency = 50
    #arcpy.ApplySymbologyFromLayer_management(in_layer=newlayer, in_symbology_layer= templateLayer)
    #layerExtent = newlayer.getExtent()
    arcpy.mapping.AddLayer(df, newlayer, "BOTTOM")
    mxd.save()
    #addFileToArcMap(os.path.join(basePath, r"Results", r"LCP.shp"), mxd)
    addFileToArcMap(os.path.join(basePath, r"inData", r"vikaasenReppesaasen290817.jpg"), mxd)

    #Skrive ut bilde av veivalg
    df = arcpy.mapping.ListDataFrames(mxd)[0]
    B = df.extent.XMax - df.extent.XMin
    H = df.extent.YMax - df.extent.YMin

    out_path = os.path.join(basePath, r"Results", r"MapLCP.png")
    arcpy.mapping.ExportToPNG(map_document= mxd, out_png= out_path, data_frame= df, df_export_width= int(3*B), df_export_height= int(3*H), resolution=225)
    print "Finished making image"

    image = Image()
    image.uploader = PathUser.objects.get(pk=uploaderpk)
    print "Saving image to model/database"
    image.bilde = pilImage.open(out_path)
    image.save()
    print "Saved"


    end = time.time()
    print(end-startTime)