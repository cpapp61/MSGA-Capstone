# -------------------------------------------------------------------------------
# Name:        Public_Transportation_Access_Index
# Purpose: The purpose of this script is to calculate the public transportation access index.
# This index uses the 2-Step Floating Catchment Area (2SFCA) methodology, originally used to measure
# healthcare access, to measure public transportation access.
#
# Steps
# Step 1: Create census tract centroids.
# Step 2: Create lines between all census tract centroids and transportation points.
# Step 3: Summarize selected lines based on transportation point ID.
# Step 4: Join summarized table from steps 2 and 3 with the lines layer based on transportation location unique id.
# Step 5: Summarize lines feature class from step 4 based on census tract ID to derive sum of ratios, which is the
# final accessibility score.
#
# Author:      Christopher Papp
#
# Created:     6/16/2022
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
    # Points feature class representing transportation (metro and bus) stops.
    transportation_points = arcpy.GetParameterAsText(0)
    # Unique ID of transportation (subway and bus) points.
    transportation_id_field = arcpy.GetParameterAsText(1)
    # Census tracts feature class.
    geographical_units = arcpy.GetParameterAsText(2)
    # Census tract id field.
    geographic_id_field = arcpy.GetParameterAsText(3)
    # Population field of census tract feature class.
    population_field = arcpy.GetParameterAsText(4)
    # Input geodatabase.
    gdb = arcpy.GetParameterAsText(5)

    #
    # file locations
    #
    geographical_centroids = fr"{gdb}\geographical_centroids"
    census_tract_transportation = fr"{gdb}\census_tract_transportation"
    ctt_lines = fr"{gdb}\ctt_lines"
    transportation_summarize = fr"{gdb}\transportation_summarize"
    view_lines = fr"{gdb}\view_lines"
    ratio_transportation = fr"{gdb}\ratio_transportation"
    transportation_accessibility = fr"{gdb}\transportation_accessibility"

    # Step 1: Create census tract centroids.
    arcpy.FeatureToPoint_management(geographical_units, geographical_centroids)

    # Step 2: Create lines between all census tract centroids and transportation points.
    arcpy.AddGeometryAttributes_management(geographical_centroids, "POINT_X_Y_Z_M", "FEET_US")
    arcpy.AddGeometryAttributes_management(transportation_points, "POINT_X_Y_Z_M", "FEET_US")
    arcpy.AddField_management(transportation_points, "XCoord", "DOUBLE")
    arcpy.AddField_management(transportation_points, "YCoord", "DOUBLE")
    arcpy.CalculateField_management(transportation_points, "XCoord", "!POINT_X!")
    arcpy.CalculateField_management(transportation_points, "YCoord", "!POINT_Y!")
    arcpy.SpatialJoin_analysis(geographical_centroids, transportation_points, census_tract_transportation, "JOIN_ONE_TO_MANY", "KEEP_ALL", match_option="WITHIN_A_DISTANCE", search_radius="10000 feet")
    arcpy.XYToLine_management(census_tract_transportation, ctt_lines, "POINT_X", "POINT_Y", "XCoord", "YCoord", "Geodesic", geographic_id_field, attributes="ATTRIBUTES")
    arcpy.AddGeometryAttributes_management(ctt_lines, "Length", "Feet (United States)")

    # Step 3: Summarize selected lines based on transportation point ID and calculate ratio field.
    arcpy.SummarizeAttributes_gapro(ctt_lines, transportation_summarize, [transportation_id_field], [[population_field, "SUM"]])
    arcpy.AddField_management(transportation_summarize, "ratio", "DOUBLE")
    arcpy.CalculateField_management(transportation_summarize, "ratio", f"1/!SUM_{population_field}!")

    # Step 4: Join summarized table from steps 2 and 3 with the lines layer based on transportation location unique id.
    arcpy.MakeFeatureLayer_management(ctt_lines, view_lines)
    lines_table = arcpy.AddJoin_management(view_lines, transportation_id_field, transportation_summarize, transportation_id_field)
    arcpy.TableToTable_conversion(lines_table, gdb, "ratio_transportation")

    # Step 5: Summarize lines feature class from step 4 based on census tract ID to derive sum of ratios, which is the
    # final accessibility score.
    arcpy.SummarizeAttributes_gapro(ratio_transportation, transportation_accessibility, [geographic_id_field], [["ratio", "SUM"]])
    arcpy.AddField_management(transportation_accessibility, "transportation_access", "DOUBLE")
    max_value = 0
    with arcpy.da.SearchCursor(transportation_accessibility, ["SUM_ratio"]) as cur:
        for row in cur:
            if row[0] is not None:
                if row[0] > max_value:
                    max_value = row[0]
    arcpy.CalculateField_management(transportation_accessibility, "transportation_access", fr"!SUM_ratio!/{max_value}")


if __name__ == '__main__':
    main()
    timeend = time.time()
    timetotal = round((timeend - timestart) / 60, 4)
    print(f"This script took {timetotal} minutes to run.")
