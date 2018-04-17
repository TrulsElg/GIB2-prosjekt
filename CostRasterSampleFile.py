import time
start = time.time()
import arcpy
import os
import xlrd
import math
from arcpy import env

arcpy.env.overwriteOutput = True
arcpy.env.cellSize = 1

global mxd, SlopeL, SlopeL2, ImpCliff, ImpCliffBase, GigBoulder, ImpWater, ImpMarsh, ImpVeg, ImpLand, ImpRail, ImpWall, ImpFence, ImpLine, ImpLine2, ImpBuilding, ImpSettlement, ImpOB
env.workspace = "C:/Users/sindr/Documents/NTNU\V2018/TBA4250 - GIB/GIB2-Prosjekt/GIB2-prosjekt"

arealsymboler = arcpy.Copy_management(r"Shape/SampleCourse_ar.shp", None)
linjesymboler = arcpy.Copy_management(r"Shape/SampleCourse_ln.shp", None)
punktsymboler = arcpy.Copy_management(r"Shape/SampleCourse_pt.shp", None)

SlopeL = 101.000
SlopeL2 = 102.000

ImpCliff = 201.000
ImpCliffBase = 201.001
GigBoulder = 202.000
ImpWater = 301.000
ImpMarsh = 309.000
ImpVeg = -1
ImpLand = 415.000
ImpRail = 515.000
ImpWall = -1
ImpFence = -1
ImpLine = -1
ImpLine2 = 707.000
ImpBuilding = 526.000
ImpSettlement = 527.000
ImpOB = 528.000

def getExtentOfMap(linjesymboler):
    try:
        hoydekurver = arcpy.Select_analysis(linjesymboler, None, '"SYMBOL"=' + str(SlopeL) + ' OR "SYMBOL"=' + str(SlopeL2))
        utsnitt1 = arcpy.MinimumBoundingGeometry_management(hoydekurver, None, "CONVEX_HULL")
        arcpy.AddField_management(utsnitt1, "UTSNITT", "DOUBLE")
        features = arcpy.UpdateCursor(utsnitt1)
        for feature in features:
            feature.UTSNITT = 1
            features.updateRow(feature)
        del feature, features
        dissolved = arcpy.Dissolve_management(utsnitt1, None, "UTSNITT")
        return arcpy.MinimumBoundingGeometry_management(dissolved, "utsnitt", "CONVEX_HULL")
    except:
        print("Tried to get extent of OCAD-map but failed")


def addFileToArcMap(filepathFile):
    try:
        df = arcpy.mapping.ListDataFrames(mxd, "*")[0]
        newlayer = arcpy.mapping.Layer(filepathFile)
        arcpy.mapping.AddLayer(df, newlayer, "BOTTOM")
        mxd.save()
    except:
        print("Tried but failed to add file to MXD")

def getImpassableLineSymbols(ln):
    try:
        lnImp = arcpy.Select_analysis(ln,"lnImp",'"SYMBOL"=' + str(ImpCliff) + ' OR "SYMBOL"=' + str(ImpCliffBase) + ' OR "SYMBOL"=' + str(ImpRail) + ' OR "SYMBOL"=' + str(ImpWall) + ' OR "SYMBOL"=' + str(ImpFence) + ' OR "SYMBOL"=' + str(ImpLine) + ' OR "SYMBOL"=' + str(ImpLine2))
        arcpy.RepairGeometry_management(lnImp)
        return lnImp
    except:
        print("Tried but failed to get impassable symbols")

def getImpassableAreaSymbols(ar):
    try:
        arImp = arcpy.Select_analysis(ar, "arImp", '"SYMBOL"=' + str(GigBoulder) + ' OR "SYMBOL"=' + str(
            ImpWater) + ' OR "SYMBOL"=' + str(ImpMarsh) + ' OR "SYMBOL"=' + str(ImpVeg) + ' OR "SYMBOL"=' + str(
            ImpLand) + ' OR "SYMBOL"=' + str(ImpSettlement) + ' OR "SYMBOL"=' + str(
            ImpBuilding) + ' OR "SYMBOL"=' + str(ImpOB))
        arcpy.RepairGeometry_management(arImp)
        return arImp
    except:
        print("Tried but failed to get impassable symbols")

def getPassableLineSymbols(ln):
    try:
        lnRes = arcpy.Select_analysis(ln,"lnRes",'"SYMBOL"=' + str(106.000) + 'OR "SYMBOL"=' + str(106.001))
        arcpy.RepairGeometry_management(lnRes)
    except:
        print("Tried but failed to get passable line symbols")

def getPassableAreaSymbols(ar):
    try:
        arP = arcpy.Select_analysis(ar, "arP",
                                    '"SYMBOL"=' + str(211.000) + ' OR "SYMBOL"=' + str(212.000) + ' OR "SYMBOL"=' + str(
                                        302.000) + ' OR "SYMBOL"=' + str(310.000) + ' OR "SYMBOL"=' + str(
                                        311.000) + ' OR "SYMBOL"=' + str(401.000) + ' OR "SYMBOL"=' + str(
                                        402.000) + ' OR "SYMBOL"=' + str(403.000) + ' OR "SYMBOL"=' + str(
                                        404.000) + ' OR "SYMBOL"=' + str(406.000) + ' OR "SYMBOL"=' + str(
                                        408.000) + ' OR "SYMBOL"=' + str(410.000) + ' OR "SYMBOL"=' + str(529.000))
        arcpy.RepairGeometry_management(arP)
        return arP
    except:
        print("Tried but failed to get passable area symbols")

def FieldExists(fc, fi):
    fieldnames = [field.name for field in arcpy.ListFields(fc)]
    if fi in fieldnames:
        return True
    else:
        return False

def LineWidth(ln, symbols, width):
    if not FieldExists(ln, "WIDTH"):
        arcpy.AddField_management(ln,"WIDTH","DOUBLE")
    features = arcpy.UpdateCursor(ln)
    for feature in features:
        if feature.SYMBOL in symbols:
            n = symbols.index(feature.SYMBOL)
            feature.WIDTH = width[n]
        features.updateRow(feature)
    del n, feature, features

def makeBuffer(ln):
    return arcpy.Buffer_analysis(ln, None, "WIDTH","FULL", "FLAT", "LIST", "SYMBOL")

def Forest(utsnitt, ar):
    try:
        arP = getPassableAreaSymbols(ar)
        arImp = getImpassableAreaSymbols(ar)
        area = arcpy.Update_analysis(arP,arImp,"area")
        forest = arcpy.Erase_analysis(utsnitt, area, "forest")
        arcpy.AddField_management(forest,"SYMBOL","DOUBLE")
        features = arcpy.UpdateCursor(forest)
        for feature in features:
            feature.SYMBOL = 405
            features.updateRow(feature)
        del feature, features
        return forest
    except:
        print("Tried but failed to extract forest areas")

def getArea(ar):
    try:
        arP = getPassableAreaSymbols(ar)
        arImp = getImpassableAreaSymbols(ar)
        arPass = arcpy.Erase_analysis(arP,arImp,"arPass")
        area = arcpy.Update_analysis(arPass,arImp)
        return area
    except:
        print("Tried but failed to create all area symbols")

def addTable(excel_file, table_out_file, sheetName):
    hastighetInn = "../Data/Hastighet2.xlsx"
    tabellUt = "../Kladd/lopshastighet.gdb"
    arcpy.ExcelToTable_conversion(hastighetInn, tabellUt, "hastArk")

def setCost(fc, dbPath):
    try:
        arcpy.AddField_management(fc, "COST", "DOUBLE")
        features = arcpy.UpdateCursor(fc)
        for feature in features:
            costs = arcpy.UpdateCursor(dbPath)
            for cost in costs:
                if math.floor(feature.SYMBOL) == cost.SYMBOLnr:
                    feature.COST = cost.hastighet
                costs.updateRow(cost)
            del cost, costs
            features.updateRow(feature)
        del feature, features
    except:
        print("Tried but failed to set cost")

mxd = arcpy.mapping.MapDocument(r"C:\Users\sindr\Documents\NTNU\V2018\TBA4250 - GIB\GIB2-Prosjekt\GIB2-prosjekt\ArcMap\SampleMap.mxd")

utsnitt = getExtentOfMap(linjesymboler)
forest = Forest(utsnitt,arealsymboler)
area = getArea(arealsymboler)
areaP = getPassableAreaSymbols(arealsymboler)
allPArea = arcpy.Update_analysis(area, forest, "allPArea")
allPArea = arcpy.RepairGeometry_management(allPArea)
impArea = getImpassableAreaSymbols(arealsymboler)
allArea = arcpy.Erase_analysis(allPArea,impArea,"allArea")

LineWidth(linjesymboler, [106.000,106.001,201.000,201.001,203.000,203.000,305.000,306.000,502.000,503.000,504.000,505.000,506.000,507.000],[2,2,4,4,4,4,1,0.5,6,4,3,2.5,2,2])
ln_buff = makeBuffer(linjesymboler)

it2 = arcpy.Erase_analysis(allArea,ln_buff,"it2")
allSymbols = arcpy.Update_analysis(it2, ln_buff, "allSymbols")

addFileToArcMap(r"C:\Users\sindr\Documents\NTNU\V2018\TBA4250 - GIB\GIB2-Prosjekt\GIB2-prosjekt\allSymbols.shp")

arcpy.CreateFileGDB_management(r"C:\Users\sindr\Documents\NTNU\V2018\TBA4250 - GIB\GIB2-Prosjekt\GIB2-prosjekt\Data","outgdb.gdb")

hastighetInn = r"C:\Users\sindr\Documents\NTNU\V2018\TBA4250 - GIB\GIB2-Prosjekt\GIB2-prosjekt\Data\Hastighet.xlsx"
tabellUt = r"C:\Users\sindr\Documents\NTNU\V2018\TBA4250 - GIB\GIB2-Prosjekt\GIB2-prosjekt\Data\outgdb.gdb"
arcpy.ExcelToTable_conversion(hastighetInn, tabellUt, "hastArk")

setCost(allSymbols,r"C:\Users\sindr\Documents\NTNU\V2018\TBA4250 - GIB\GIB2-Prosjekt\GIB2-prosjekt\Data\outgdb.dbf")

arcpy.FeatureToRaster_conversion(allSymbols,"COST","CostRaster.tif",1)


addFileToArcMap(r"C:\Users\sindr\Documents\NTNU\V2018\TBA4250 - GIB\GIB2-Prosjekt\GIB2-prosjekt\CostRaster.tif")


end = time.time()
print(end-start)