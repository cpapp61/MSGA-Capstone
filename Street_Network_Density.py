# -------------------------------------------------------------------------------
# Name:        Street_Network_density
# Purpose: The purpose of this script is to calculate the street network density, which covers for the street
# intersection metric is areas without intersections. This is calculated as the area of roads divided by the
# area of each census tract.
#
# Steps
# Step 1: Buffer roads using the street width field.
# Step 2: Apportion polygons to find street area in square feet per census tract.
# Step 3: Calculate unnormalized street network density and max normalization.
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
    # Roads line feature class.
    roads = arcpy.GetParameterAsText(0)
    # Area field of the roads feature class.
    roads_area_field = arcpy.GetParameterAsText(1)
    # Census tracts feature class.
    geographical_units = arcpy.GetParameterAsText(2)
    # Census tract id field.
    geographic_id_field = arcpy.GetParameterAsText(3)
    # Census tract area field.
    geographic_area_field = arcpy.GetParameterAsText(4)
    gdb = arcpy.GetParameterAsText(5)

    #
    # file locations
    #
    roads_buffer = fr"{gdb}\roads_buffer"
    road_apportion = fr"{gdb}\road_apportion"

    # Step 1: Buffer roads using the street width field.
    arcpy.AddField_management(roads, "width", "DOUBLE")
    arcpy.CalculateField_management(roads, "width", f"!{roads_area_field}!/2")
    arcpy.Buffer_analysis(roads, roads_buffer, "width", dissolve_option="ALL")

    # Step 2: Apportion polygons to find street area in square feet per census tract.
    arcpy.AddGeometryAttributes_management(roads_buffer, "AREA", Area_Unit="Square feet (United States)")
    arcpy.ApportionPolygon_analysis(roads_buffer, "POLY_AREA", geographical_units, road_apportion, "AREA")

    # Step 3: Calculate unnormalized street network density and max normalization.
    arcpy.AddField_management(road_apportion, "bn_network_density", "DOUBLE")
    arcpy.CalculateField_management(road_apportion, "bn_network_density", f"!POLY_AREA!/!{geographic_area_field}!")
    max_value = 0
    with arcpy.da.UpdateCursor(road_apportion, ["bn_network_density"]) as cursor:
        for row in cursor:
            if row[0] is None:
                row[0] = 0
                cursor.updateRow(row)
            elif max_value < row[0]:
                max_value = row[0]
    arcpy.AddField_management(road_apportion, "network_density", "DOUBLE")
    arcpy.CalculateField_management(road_apportion, "network_density", f"!bn_network_density!/{max_value}")


if __name__ == '__main__':
    main()
    timeend = time.time()
    timetotal = round((timeend - timestart) / 60, 4)
    print(f"This script took {timetotal} minutes to run.")