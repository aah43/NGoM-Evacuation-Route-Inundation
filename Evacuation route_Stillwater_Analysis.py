##--------------------------------------------------------------------------------
## Evacuation route_Stillwater_Analysis.py
## Analyze evacuation route line data for the Northern Gulf
## by extracting values from EESLR-NGOM stillwater storm surge raster data
##
## Created: February 2018
## Author: Amber Halstead <amber.halstead@duke.edu>
##--------------------------------------------------------------------------------
# Import necessary modules
import sys, os, arcpy
from arcpy import env
from arcpy.sa import *


# Check out necessary arcpy extensions
arcpy.CheckOutExtension("Spatial")
arcpy.CheckOutExtension("GeoStats")

#Set relative path
os.chdir("..")

# Define environmental settings
arcpy.env.workspace = os.path.abspath(os.curdir) + "\\Data\\EESLR_Stillwater\\1pc_IDAG" 
arcpy.env.overwriteOutput = True #False = does not allow files to be overwritten
arcpy.env.scratchWorkspace = os.path.abspath(os.curdir) + "\\Scratch"
outputDir = os.path.abspath(os.curdir) + "\\Data\\ModelOutputs"




arcpy.env.workspace = os.path.abspath(os.curdir) + "\\Data"
evacRoutes = str(arcpy.env.workspace) + "\\Hurricane_Evacuation_Routes.shp"

#----Clip Evacuation Roads to Region Boundary-----------------------------------------------------------------------------------------------
# Set local variables
in_features = evacRoutes
clip_features = arcpy.env.workspace + "\\EESLR_Stillwater\\RegionBoundaries\\Boundary.shp"
evacClip = arcpy.env.scratchWorkspace + "/EvacRoutesClip.shp"
# Execute Clip
arcpy.Clip_analysis(in_features, clip_features, evacClip, "")
#----Buffer Evacuation Routes ---------------------------------------------------------------------------------------------
# Set local variables
in_Features = evacClip
evacBuffer = arcpy.env.scratchWorkspace + "\\Evac_Buffer"
bufferDist = "4 Meters"

# Execute Buffer
EvacBuffer = arcpy.Buffer_analysis(in_Features, evacBuffer, bufferDist,"FULL", "ROUND", "NONE", "", "PLANAR")


#--------work with IDAG polygon files-----------------------

# Re-Define environmental settings
arcpy.env.workspace = os.path.abspath(os.curdir) + "\\Data\\EESLR_Stillwater\\1pc_IDAG"


# Create Binned Multipart Polygon for each prediction raster (Regions already mosaiced) 
files = arcpy.ListRasters()
for filename in files:
        if filename.endswith('.tif'):
                x = filename.split('.')
                print "\n processing " + x[0] + " file"

                #extracting out what SLR scenario and stillwater percent 1pc or 0.2pct
                z = x[0].split('_')
                scenario = z[1]
                percent = z[2]

                #----Depth Raster to Polygon---------------------------------------------------------------------------------
                # Set local variables
                inRaster = arcpy.env.scratchWorkspace +"/reclass" +  filename
                outPolygons = arcpy.env.scratchWorkspace + "/" + scenario +  "_" + percent + "_" +"Poly"
                field = "VALUE"
                # Execute RasterToPolygon
                raster2poly = arcpy.RasterToPolygon_conversion(inRaster, outPolygons, "SIMPLIFY", field)
                #----Dissolve Depth Polygon into Multipart Polygon------------------------------------------------------------------------------------------
                # Set local variables
                #inFeatures = outPolygons +".shp"
                outFeatureClass = outputDir  + "\\" + scenario +  "_" + percent +"_"+ "Multipart_Depth_Poly_"
                dissolveField = "gridcode"
                # Execute Dissolve
                dissolvePoly = arcpy.Dissolve_management(raster2poly, outFeatureClass, dissolveField, "", "MULTI_PART", "DISSOLVE_LINES")

                print("\t merging stillwater and road layers")
                #assign depths to buffered roads
                identity_features = dissolvePoly
                OutputFeature = arcpy.env.scratchWorkspace + "\\Poly_" +x[0] + "_RoadDepth"
                #Execute Intersect
                RoadDepth = arcpy.Identity_analysis(EvacBuffer, identity_features, OutputFeature, "NO_FID")

                print("\t updating road water depth values ")
                arcpy.AddField_management(RoadDepth, "Depth", "TEXT")
                arcpy.AddField_management(RoadDepth, 'Scenario', "TEXT")
                arcpy.AddField_management(RoadDepth, 'AnnualPct', "TEXT")

                cur = arcpy.UpdateCursor(RoadDepth)
                field = "GRIDCODE"
                for row in cur:
                        row.setValue('Scenario', scenario)
                        row.setValue('AnnualPct', percent)

                        gridValue = row.getValue(field)
                        if gridValue == 0:
                                row.setValue('Depth', 'No Inundation')
                        elif gridValue == 1:
                                row.setValue('Depth', '< 1ft')
                        elif gridValue == 2:
                                row.setValue('Depth', '1 - 2ft' )
                        elif gridValue == 3:
                                row.setValue('Depth', '2 - 3ft' )
                        elif gridValue == 4:
                                row.setValue('Depth', '3 - 4ft')
                        elif gridValue == 5:
                                row.setValue('Depth', '4 - 5ft')
                        elif gridValue == 6:
                                row.setValue('Depth', '5 - 6ft')
                        elif gridValue == 7:
                                row.setValue('Depth', '6 - 7ft' )
                        elif gridValue == 8:
                                row.setValue('Depth', '7 - 8ft' )
                        elif gridValue == 9:
                                row.setValue('Depth', '8 - 9ft')
                        elif gridValue == 10:
                                row.setValue('Depth', '9 - 10ft')
                        elif gridValue == 11:
                                row.setValue('Depth', '> 10ft')
                        else:
                                row.setValue('Depth','UNDEFINED')
                        cur.updateRow(row)

                print ("finished with {0}".format(x[0]) )                

del cur

# Re-Define environmental settings
arcpy.env.workspace = os.path.abspath(os.curdir) + "\\Scratch"

files = arcpy.ListFeatureClasses()
for filename in files:
        if filename.endswith('RoadDepth.shp'):
                x = filename.replace('_', '.')
                y = x.split('.')
                z = y[2] + y[3] + y[4] + y[5]
                identity_features = filename
                OutputFeature = outputDir + "\\Line_" + z
                #Execute Intersect
                RoadDepth = arcpy.Identity_analysis(evacClip, identity_features, OutputFeature, "NO_FID")


print "Processing Complete"
