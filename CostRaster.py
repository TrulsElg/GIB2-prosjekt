# -*- coding: cp1252 -*-
import time
start = time.time()
import arcpy

from arcpy import env
import os
import xlrd
import math
arcpy.env.overwriteOutput = True
arcpy.env.cellSize = 0.5

env.workspace = "C:/Users/sindr/Documents/NTNU\V2018/TBA4250 - GIB/GIB2-Prosjekt/Test"

arealsymboler = "Shape/VikåsenReppesåsen290817_ar.shp"
linjesymboler = "Shape/VikåsenReppesåsen290817_ln.shp"

hoydekurver = arcpy.Select_analysis(linjesymboler,"hoydekurver.shp",'("SYMBOL"=101 OR "SYMBOL"=102)')
upasserbartL = arcpy.Select_analysis(linjesymboler,"upasserbartL",'("SYMBOL"=201 OR "SYMBOL"=524 OR "SYMBOL"=515 OR "SYMBOL"=509)')
upasserbartF = arcpy.Select_analysis(arealsymboler,"upasserbartF",'("SYMBOL"=202 OR "SYMBOL"=301 OR "SYMBOL"=307 OR "SYMBOL"=410 OR "SYMBOL"=526 OR "SYMBOL"=527 OR "SYMBOL"=528)')
kartutsnitt = arcpy.Select_analysis(arealsymboler,"Kartutsnitt",'"SYMBOL"=601.001')

#Tar inn tabell med løpshastigheter på forskjellige underlag
hastighetInn = "../Data/Hastighet2.xlsx"
tabellUt = "../Kladd/lopshastighet.gdb"
arcpy.ExcelToTable_conversion(hastighetInn, tabellUt, "hastArk")

#Velger ut hvit skog i en fil (FOREST405) og annet i en (NOTFOREST405). Reparerer så overlapp
Forest405 = arcpy.Select_analysis(arealsymboler, "Forest405", '("SYMBOL"=405)')
NotForest405 = arcpy.Select_analysis(arealsymboler, "NotForest405", '("SYMBOL"=211 OR "SYMBOL"=212 OR "SYMBOL"=301 OR "SYMBOL"=301.001 OR "SYMBOL"=302 OR "SYMBOL"=302.001 OR "SYMBOL"=401 OR "SYMBOL"=402 OR "SYMBOL"=402.001 OR "SYMBOL"=402.002 OR "SYMBOL"=403 OR "SYMBOL"=403.001 OR "SYMBOL"=404.001 OR "SYMBOL"=404.002 OR "SYMBOL"=406 OR "SYMBOL"=407 OR "SYMBOL"=408 OR "SYMBOL"=409 OR "SYMBOL"=410 OR "SYMBOL"=410.001 OR "SYMBOL"=411 OR "SYMBOL"=411.001 OR "SYMBOL"=411.002 OR "SYMBOL"=412 OR "SYMBOL"=413 OR "SYMBOL"=415 OR "SYMBOL"=415.001 OR "SYMBOL"=526 OR "SYMBOL"=527 OR "SYMBOL"=527.001 OR "SYMBOL"=528 OR "SYMBOL"=529 OR "SYMBOL"=529.003)')
Forest405 = arcpy.RepairGeometry_management(Forest405)
NotForest405 = arcpy.RepairGeometry_management(NotForest405)
Forest = arcpy.Erase_analysis(kartutsnitt,NotForest405,"Forest")
features = arcpy.UpdateCursor(Forest)
for feature in features:
    feature.SYMBOL = 405
    features.updateRow(feature)
del feature, features
NotForest405 = arcpy.Erase_analysis(NotForest405,Forest405,"NotForest")


#Lager bredde på linjesymbolene så de kommer med i rasteranalysen
linjebredde = arcpy.AddField_management(linjesymboler, "Bredde", "DOUBLE")

features = arcpy.UpdateCursor(linjesymboler)
for feature in features:
    if feature.SYMBOL == 502 or feature.SYMBOL == 502.001 or feature.SYMBOL == 503 or feature.SYMBOL == 503.001 or feature.SYMBOL == 504 or feature.SYMBOL == 505:
        feature.Bredde = 5
    elif feature.SYMBOL == 506 or feature.SYMBOL == 507 or feature.SYMBOL == 507.001 or feature.SYMBOL == 508 or feature.SYMBOL == 508.001 or feature.SYMBOL == 509 or feature.SYMBOL == 509.001:
        feature.Bredde = 3
    elif feature.SYMBOL == 201 or feature.SYMBOL ==201.001 or feature.SYMBOL == 201.002 or feature.SYMBOL == 203 or feature.SYMBOL == 203.002:
        feature.Bredde = 1
    #Disse påvirker ikke noe og settes bredde lik 0
    elif feature.SYMBOL == 301.002 or feature.SYMBOL == 414 or feature.SYMBOL == 516 or feature.SYMBOL == 517:
        feature.Bredde = 0
    else:
        feature.Bredde = 0
    feature.SYMBOL = math.floor(feature.SYMBOL)
    features.updateRow(feature)
del feature, features

#Lager buffer rundt alle linjesymboler som er like stor som feltet den har
linjebuffer = arcpy.Buffer_analysis(linjebredde, "linjebuffer", "Bredde","FULL", "FLAT", "LIST", "SYMBOL")

#Legger sammen skog og annet og så buffer og alle arealer
AllAreaSymbols = arcpy.Update_analysis(NotForest405,Forest,"AllArea")
AllSymbols = arcpy.Update_analysis(AllAreaSymbols, linjebuffer, "All")

#Lager kostnadsraster
arcpy.AddField_management(AllSymbols,"MOTSTAND","DOUBLE")

features = arcpy.UpdateCursor(AllSymbols)
for feature in features:
    speeds = arcpy.UpdateCursor("../Kladd/lopshastighet.dbf")
    for speed in speeds:
        if feature.SYMBOL == speed.SYMBOLnr:
            feature.MOTSTAND = speed.hastighet
        speeds.updateRow(speed)
    del speed, speeds
    features.updateRow(feature)
del features, feature

#Illegal = arcpy.Select_analysis(AllSymbols,"Illegal",'"MOTSTAND" = 0')
#arcpy.Erase_analysis(AllSymbols,Illegal,"FinisedDataset")

arcpy.FeatureToRaster_conversion(AllSymbols,"MOTSTAND","skog3CostARC_hvit.tif",0.5)


end = time.time()
print(end-start)
