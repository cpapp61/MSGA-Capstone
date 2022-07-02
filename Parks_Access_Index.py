# -------------------------------------------------------------------------------
# Name:        Parks_Access_Index
# Purpose: The purpose of this script is to calculate the access to parks metric. This metric is defined
# as the median zonal statistic of the cost distance from the parks raster using the reclassified distance to the
# sidewalks as the cost surface raster.
#
# Steps
# Step 1: Calculate euclidean distance raster for distance from sidewalk polygons.
# Step 2: Reclassify euclidean distance from sidewalks raster to create cost surface.
# Step 3: Convert park polygons into points.
# Step 4: Select census tracts that intersect with park points.
# Step 5: Calculate cost distance using parks points and cost surface from steps 4 and 2, respectively.
# Step 6: Calculate zonal statistics to obtain all the summary statistics of the cost distance raster from step 5 by census tract.
# Step 7: Calculate park access field and normalize it using max value normalization.
#
# Author:      Christopher Papp
#
# Created:     6/17/2022
# Copyright:   (c) Christopher Papp

# -------------------------------------------------------------------------------

import arcpy
import time

timestart = time.time()
arcpy.env.workspace = data = fr"C:\MSGA_Capstone\capstone_data"
arcpy.env.overwriteOutput = True


def main():
    #
    # input parameters
    #
    # Parks polygon feature class.
    parks = arcpy.GetParameterAsText(0)
    # Sidewalk polygons feature class.
    sidewalks = arcpy.GetParameterAsText(1)
    # Census tracts feature class.
    geographical_units = arcpy.GetParameterAsText(2)
    # Input geodatabase.
    gdb = arcpy.GetParameterAsText(3)

    #
    # file locations
    #
    sidewalks_distance = fr"{gdb}\sidewalks_distance"
    distance_reclass = fr"{gdb}\distance_reclass"
    near_roads = fr"{gdb}\near_roads"
    parks_FeatureToPoint = fr"C:\MSGA_Capstone\capstone_data\parks_FeatureToPoint.shp"
    parks_raster = fr"{gdb}\parks_raster"
    parks_access = fr"{gdb}\parks_access"

    # Step 1: Calculate euclidean distance raster for distance from sidewalk polygons.
    with arcpy.EnvManager(mask=geographical_units):
        out_distance_raster = arcpy.sa.EucDistance(sidewalks, None, 10, None, "PLANAR", None, None)
        out_distance_raster.save(sidewalks_distance)
    # Step 2: Reclassify euclidean distance from sidewalks raster to create cost surface.
    arcpy.Reclassify_3d(sidewalks_distance, "VALUE", "0 100 1;100 200 2;200 400 3;400 800 4;800 1600 5;1600 84892.132812 6", distance_reclass, "DATA")
    # Step 3: Convert park polygons into points.
    arcpy.FeatureToPoint_management(parks, parks_FeatureToPoint)
    # Step 4: Select census tracts that intersect with park points.
    arcpy.SelectLayerByLocation_management(geographical_units, "INTERSECT", parks_FeatureToPoint, None, "NEW_SELECTION", "NOT_INVERT")
    arcpy.CopyFeatures_management(geographical_units, near_roads)
    # Step 5: Calculate cost distance using parks points and cost surface from steps 4 and 2, respectively.
    out_distance_raster = arcpy.sa.CostDistance(parks_FeatureToPoint, distance_reclass)
    out_distance_raster.save(parks_raster)
    # Step 6: Calculate zonal statistics to obtain all the summary statistics of the cost distance raster from step 5 by census tract.
    arcpy.ia.ZonalStatisticsAsTable(geographical_units, "GEOID", parks_raster, parks_access, "DATA", "ALL", "CURRENT_SLICE", 90, "AUTO_DETECT")
    min_value = 1000000
    # Step 7: Calculate park access field and normalize it using max value normalization.
    with arcpy.da.SearchCursor(parks_access, ["MEDIAN"]) as cursor:
        for row in cursor:
            if min_value > row[0]:
                min_value = row[0]
    arcpy.AddField_management(parks_access, "park_access", "DOUBLE")
    arcpy.CalculateField_management(parks_access, "park_access", fr"(1/!MEDIAN!)/(1/{min_value})")


if __name__ == '__main__':
    main()
    timeend = time.time()
    timetotal = round((timeend - timestart) / 60, 4)
    print(f"This script took {timetotal} minutes to run.")