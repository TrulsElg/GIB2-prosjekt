import time
startTime = time.time()
import arcpy
import math
from arcpy import env
from arcpy.sa import *
from CostRasterSampleFile import addFileToArcMap
import os

# Activate spatial analyst extension
if arcpy.CheckExtension("Spatial") == "Available":
    arcpy.CheckOutExtension("Spatial")

arcpy.env.overwriteOutput = True
arcpy.env.cellSize = 5

global mxd
env.workspace = "C:/Users/sindr/Documents/NTNU\V2018/TBA4250 - GIB/GIB2-Prosjekt/GIB2-prosjekt"

inRaster = r"C:\Users\sindr\Documents\NTNU\V2018\TBA4250 - GIB\GIB2-Prosjekt\GIB2-prosjekt\CostRaster.tif"

mxd = arcpy.mapping.MapDocument(r"C:\Users\sindr\Documents\NTNU\V2018\TBA4250 - GIB\GIB2-Prosjekt\GIB2-prosjekt\ArcMap\SampleMap.mxd")

ar = arcpy.Copy_management(r"Shape/SampleCourse_ar.shp", None)
ln = arcpy.Copy_management(r"Shape/SampleCourse_ln.shp", None)
pt = arcpy.Copy_management(r"Shape/SampleCourse_pt.shp", None)

#Lage geodatabase
#gdb = "geodatabase.gdb"
#if arcpy.exists(gdb):
#    arcpy.Delete_management(gdb)

def getStart(pt):
    try:
        start = arcpy.Select_analysis(pt, "start", '"SYMBOL" = 701 AND "ANGLE" = 0')
        arcpy.AddXY_management(start)
    except:
        print("Failed to getStart()")
    return start

def getFinish(pt):
    try:
        finish = arcpy.Select_analysis(pt,"destination",'"SYMBOL" = 706')
        arcpy.AddXY_management(finish)
    except:
        print("Failed to getStart()")
    return finish

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
    #Should make a new shapefile for the maskPoints
    #arcpy.Copy_management(start,r"C:/Users/sindr/Documents/NTNU\V2018/TBA4250 - GIB/GIB2-Prosjekt/GIB2-prosjekt/maskPoints.shp")
    maskPoints = arcpy.Copy_management(r"start.shp", "maskPoints.shp")
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
    mask = arcpy.MinimumBoundingGeometry_management(maskPoints, "mask", "RECTANGLE_BY_WIDTH")
    return mask

def createNewPointFile(name):
    out_path = "C:/Users/sindr/Documents/NTNU\V2018/TBA4250 - GIB/GIB2-Prosjekt/GIB2-prosjekt"
    geometry_type = "POINT"
    res = arcpy.CreateFeatureclass_management(out_path, name, geometry_type)
    return res

start = getStart(pt)
destination = getFinish(pt)
mask = setMask(start,destination)

arcpy.env.mask = r"C:/Users/sindr/Documents/NTNU\V2018/TBA4250 - GIB/GIB2-Prosjekt/GIB2-prosjekt/mask.shp"
cdr = arcpy.sa.CostDistance(start,inRaster)
cbr = arcpy.sa.CostBackLink(start,inRaster)
cp = arcpy.sa.CostPath(destination,cdr,cbr,"EACH_CELL")
cp.save(r"C:/Users/sindr/Documents/NTNU\V2018/TBA4250 - GIB/GIB2-Prosjekt/GIB2-prosjekt/costPath")


end = time.time()
print(end-startTime)