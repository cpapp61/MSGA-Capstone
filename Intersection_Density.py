# -------------------------------------------------------------------------------
# Name:        Intersection_Density
# Purpose: The purpose of this script is to calculate the intersection density sub metric.
# This metric is the density of intersections in each census tract and is measured in squared feet. The coordinate
# system used is NAD_1983_StatePlane_New_York_Long_Island_FIPS_3104_Feet.
#
# Steps
# Step 1: Interest street network with itself to identify street intersections, which are displayed as points.
# Step 2: Spatially joining street intersection feature class to itself to determine the number of lines that are conected to each intersection.
# Step 3: Removing intersections where fewer than 3 roads intersect.
# Step 4: Converting multipoints into single points using dissolve with the x and y centroid coordinates used as the dissolve fields and the Multipart to
# Singlepart tool.
# Step 5: Summarizing intersection points within each census tract, with a 3 way intersection equaling 3 and 4 way intersection equaling 4, and so on.
# Step 6: Calculating unnormalized intersection density metric.
# Step 7: Max value normalization of Intersection Density metric field.
#
# Author:      Christopher Papp
#
# Created:     6/8/2022
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
    street_network = arcpy.GetParameterAsText(0)
    geographical_units = arcpy.GetParameterAsText(1)
    land_area_field = arcpy.GetParameterAsText(2)
    gdb = arcpy.GetParameterAsText(3)
    #
    # file locations
    #
    street_intersect = fr"{gdb}\street_intersect"
    street_street_join = fr"{gdb}\street_street_join"
    street_intersection_points = fr"{gdb}\street_intersection_points"
    street_dissolve = fr"{gdb}\street_dissolve"
    single_street = fr"{gdb}\single_street"
    street_summarize = fr"{gdb}\street_summarize"
    # Step 1: Interest street network with itself to identify street intersections, which are displayed as points.
    arcpy.Intersect_analysis(street_network, street_intersect, "ALL", None, "POINT")
    # Step 2: Spatially joining street intersection feature class to itself to determine the number of lines that are conected to each intersection.
    arcpy.SpatialJoin_analysis(street_intersect, street_intersect, street_street_join)
    # Step 3: Removing intersections where fewer than 3 roads intersect.
    select_street = arcpy.SelectLayerByLocation_management(street_street_join, 'INTERSECT', geographical_units, 0, 'NEW_SELECTION')
    arcpy.SelectLayerByAttribute_management(select_street, 'NEW_SELECTION', '"Join_Count" > 2')
    arcpy.CopyFeatures_management(select_street, street_intersection_points)
    # Step 4: Converting multipoints into single points using dissolve with the x and y centroid coordinates used as the dissolve fields.
    arcpy.AddGeometryAttributes_management(street_intersection_points, "CENTROID", "FEET_US", "SQUARE_FEET_US")
    arcpy.Dissolve_management(street_intersection_points, street_dissolve, "CENTROID_X;CENTROID_Y", "Join_Count MEAN", "MULTI_PART", "DISSOLVE_LINES")
    arcpy.MultipartToSinglepart_management(street_dissolve, single_street)
    # Step 5: Summarizing intersection points within each census tract, with a 3 way intersection equaling 3 and 4 way intersection equaling 4, and so on.
    arcpy.SummarizeWithin_gapro(single_street, street_summarize, "POLYGON", '', None, geographical_units, "ADD_SUMMARY", '', "MEAN_Join_Count SUM")
    # Step 6: Calculating unnormalized intersection density metric.
    arcpy.AddField_management(street_summarize, "bn_intersection", "DOUBLE")
    arcpy.CalculateField_management(street_summarize, "bn_intersection", fr"!SUM_MEAN_Join_Count!/(!{land_area_field}!*10.764)")
    arcpy.AddField_management(street_summarize, "intersection", "DOUBLE")
    # Step 7: Max value normalization of Intersection Density metric field.
    # Determining max intersection density value for max value normalization.
    max_value = 0
    with arcpy.da.SearchCursor(street_summarize, ["bn_intersection"]) as cursor:
        for row in cursor:
            if row[0] is not None:
                if row[0] > max_value:
                    max_value = row[0]
    # Max value normalization.
    arcpy.CalculateField_management(street_summarize, "intersection", fr"!bn_intersection!/{max_value}")


if __name__ == '__main__':
    main()
    timeend = time.time()
    timetotal = round((timeend - timestart) / 60, 4)
    print(f"This script took {timetotal} minutes to run.")
