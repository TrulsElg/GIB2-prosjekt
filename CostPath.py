import time
start = time.time()
import arcpy
import math
from arcpy import env
from arcpy.sa import *
import os

arcpy.env.overwriteOutput = True
env.workspace = "C:/Users/sindr/Documents/NTNU\V2018/TBA4250 - GIB/GIB2-Prosjekt/Test"


inRaster = "skogCostARC_hvit.tif"

#Lage geodatabase
gdb = "geodatabase.gdb"
if arcpy.exists(gdb):
    arcpy.Delete_management(gdb)

