# -------------------------------------------------------------------------------
# Name:        Sidewalk_Density_Index
# Purpose: The purpose of this script is to calculate the sidewalk density index, which is measured
# as the sidewalk area by census tract. Sidewalk area is measured in square feet, since the projection
# is NAD_1983_StatePlane_New_York_Long_Island_FIPS_3104_Feet.
#
# Steps
# Step 1: Apportion polygon to find sidewalk area in square feet per census tract.
# Step 2: Calculate unnormalized sidewalk density.
# Step 3: Max normalization of sidewalk density field.
#
# Author:      Christopher Papp
#
# Created:     6/13/2022
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
    # Sidewalk polygons feature class.
    sidewalks = arcpy.GetParameterAsText(0)
    # Area field of the sidewalk feature class.
    sidewalk_area_field = arcpy.GetParameterAsText(1)
    # Census tracts feature class.
    geographical_units = arcpy.GetParameterAsText(2)
    # Area field of census tract feature class.
    geographic_area_field = arcpy.GetParameterAsText(3)
    # Input geodatabase.
    gdb = arcpy.GetParameterAsText(4)
    arcpy.env.workspace = gdb

    #
    # file locations
    #
    sidewalk_apportion = fr"{gdb}\sidewalk_apportion"

    # Step 1: Apportion polygon to find sidewalk area in square feet per census tract.
    arcpy.ApportionPolygon_analysis(sidewalks, sidewalk_area_field, geographical_units, sidewalk_apportion, "AREA")

    # Step 2: Calculate unnormalized sidewalk density.
    arcpy.AddField_management(sidewalk_apportion, "bn_sidewalk_density", "DOUBLE")
    arcpy.CalculateField_management(sidewalk_apportion, "bn_sidewalk_density", f"!{sidewalk_area_field}!/!{geographic_area_field}!")

    # Step 3: Max normalization of sidewalk density field.
    max_value = 0.000000000000000001
    with arcpy.da.UpdateCursor(sidewalk_apportion, ["bn_sidewalk_density"]) as cursor:
        for row in cursor:
            if row[0] is None:
                row[0] = 0
                cursor.updateRow(row)
            elif row[0] > max_value:
                max_value = row[0]

    arcpy.AddField_management(sidewalk_apportion, "sidewalk_density", "DOUBLE")
    arcpy.CalculateField_management(sidewalk_apportion, "sidewalk_density", f"!bn_sidewalk_density!/{max_value}")


if __name__ == '__main__':
    main()
    timeend = time.time()
    timetotal = round((timeend - timestart) / 60, 4)
    print(f"This script took {timetotal} minutes to run.")