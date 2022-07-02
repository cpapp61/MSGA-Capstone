# -------------------------------------------------------------------------------
# Name:        Land_Use_Mix
# Purpose: The purpose of this script is to calculate the land use mix sub metric,
# which is calculated using Shannon's Diversity Index. Shannon's Evenness Index
# is a measure of the evenness of land uses within a geographical unit. While this
# metric is usually measured based on a raster layer, this specific sub metric
# measures land use diversity based on polygon land use tax lots.
#
# Steps
# Step 1: Spatially join land use polygons and census tract polygons.
# Step 2: Summarize joined feature class by census tract id and land use designation to get area by land use and census tract.
# this step is required for calculating proportion of land use by census tract.
# Step 3: Summarize same joined feature class by just census tract id to get total area by census tract. This is different from
# census tract area because it only includes the area of the land use polygons within the census tracts and not the roads or bodies of water.
# Step 4: Join summary tables from steps 2 and 3. Needed to calculate land use proportion by census tract.
# Step 5: Calculate proportion of each land use by census tract.
# Step 6: Calculate Land Use Mix metric max value normalization.
#
# Author:      Christopher Papp
#
# Created:     5/27/2022
# Copyright:   (c) Christopher Papp

# -------------------------------------------------------------------------------


import os
import arcpy
import time
import math
timestart = time.time()
arcpy.env.workspace = data = fr"C:\MSGA_Capstone\capstone_data"
arcpy.env.overwriteOutput = True


def main():
    #
    #input parameters
    #
    land_use_file = arcpy.GetParameterAsText(0)
    land_use_area = arcpy.GetParameterAsText(1)
    land_uses = arcpy.GetParameterAsText(2)
    geographical_units = arcpy.GetParameterAsText(3)
    geographic_field = arcpy.GetParameterAsText(4)
    gdb = arcpy.GetParameterAsText(5)
    arcpy.AddMessage(land_use_area)
    arcpy.AddMessage("Calculating Land Use Mix Metric...")
    #
    # file locations
    #
    land_use_geographical_units = fr"{gdb}\census_tract_land_use"
    summary_land_use = fr"{gdb}\summary_land_use"
    summary_census_tract = fr"{gdb}\summary_census_tract"
    land_use_summation = fr"{gdb}\land_use_summation"
    final_land_use_summation = fr"{gdb}\final_land_use_summation"
    arcpy.AddMessage("Spatially joining land use and zonal geometry feature classes.")
    # Step 1: Spatially join land use polygons and census tract polygons.
    #
    # joining zonal geometry to land use polygons to have a single feature class with land use, tax lot areas and census tract ID's
    #
    arcpy.SpatialJoin_analysis(land_use_file, geographical_units, land_use_geographical_units, match_option="LARGEST_OVERLAP")
    arcpy.AddMessage("Summarizing land use and census tract id fields.")
    # Step 2: Summarize joined feature class by census tract id and land use designation to get area by land use and census tract.
    # this step is required for calculating proportion of land use by census tract.
    arcpy.SummarizeAttributes_gapro(land_use_geographical_units, summary_land_use, [land_uses, geographic_field], [[land_use_area, "SUM"]])
    # Step 3: Summarize same joined feature class by just census tract id to get total area by census tract. This is different from
    # census tract area because it only includes the area of the land use polygons within the census tracts and not the roads or bodies of water.
    arcpy.SummarizeAttributes_gapro(summary_land_use, summary_census_tract, [geographic_field], [[fr"SUM_{land_use_area}", "SUM"]])
    arcpy.AddMessage("Joining area by census tract to area by land use for each census tract.")
    # Step 4: Join summary tables from steps 2 and 3. Needed to calculate land use proportion by census tract.
    # join the two summarized tables to get a table with total area by census tract and area by land use for each census tract.
    land_use_joined_table = arcpy.AddJoin_management(summary_land_use, geographic_field, summary_census_tract, geographic_field, "KEEP_ALL", "NO_INDEX_JOIN_FIELDS")
    arcpy.SelectLayerByAttribute_management(land_use_joined_table, "NEW_SELECTION", "summary_land_use.ct_id > 0")
    arcpy.TableToTable_conversion(land_use_joined_table, gdb, "land_use_summation", "LandUse IS NOT NULL")
    # calculate shannon's diversity index. This index is defined as the summation of the proportion of the proportion of each land use
    # multiplied by the log of the proportion of each land use. This sum is multiplied by -1 and divided by the log of the number
    # of land uses to obtain the land use diversity of each census tract.
    # Step 5: Calculate proportion of each land use by census tract.
    arcpy.AddField_management(land_use_summation, "proportion", "DOUBLE")
    arcpy.CalculateField_management(land_use_summation, "proportion", fr"!SUM_{land_use_area}!/!SUM_SUM_{land_use_area}!")
    # Step 6: Calculate Land Use Mix metric and max value normalization.
    arcpy.AddField_management(land_use_summation, "sha_num", "DOUBLE")
    arcpy.CalculateField_management(land_use_summation, "sha_num", "-!proportion! * math.log(!proportion!)")
    arcpy.SummarizeAttributes_gapro(land_use_summation, final_land_use_summation, [geographic_field], [["sha_num", "SUM"]])
    count = arcpy.GetCount_management(final_land_use_summation)
    arcpy.AddField_management(final_land_use_summation, "shannon", "DOUBLE")
    max_value = 0.00000001
    # Determining maximum shannon value for max value normalization.
    with arcpy.da.SearchCursor(final_land_use_summation, ["SUM_sha_num"]) as cur:
        for row in cur:
            if row[0] is not None:
                if row[0] > max_value:
                    max_value = row[0]
    land_use_dict = {}
    land_use_number = 0
    # Determining the number of unique land use classes within the study area.
    with arcpy.da.SearchCursor(summary_land_use, ["LandUse"]) as cur3:
        for row in cur3:
            key = row[0]
            if key not in land_use_dict.keys() and row[0] is not None:
                land_use_dict[key] = key
                land_use_number += 1
    # Calculating the normalized shannon's diversity value based on the maximum shannon's value within the study area.
    with arcpy.da.UpdateCursor(final_land_use_summation, ["SUM_sha_num", "shannon"]) as cur2:
        for row in cur2:
            if row[0] is not None:
                row[1] = (row[0]/math.log(land_use_number))/(max_value/math.log(land_use_number))
                cur2.updateRow(row)
            else:
                row[0] = 0
                row[1] = 0
                cur2.updateRow(row)


if __name__ == '__main__':
    main()
    timeend = time.time()
    timetotal = round((timeend - timestart) / 60, 4)
    print(f"This script took {timetotal} minutes to run.")
