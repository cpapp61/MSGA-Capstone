# -------------------------------------------------------------------------------
# Name:        Population_Density
# Purpose: The purpose of this script is to calculate the commercial density sub metric.
# This metric is the density of commercial land use per census tract in square feet.
# The coordinate system is NAD_1983_StatePlane_New_York_Long_Island_FIPS_3104_Feet.
#
# Steps
# Step 1: Joining census tracts to land use polygons to have a single feature class with land use, tax lot areas and census tract ID's.
# Step 2: Summarize with census tract id field and land use field to get area by land use and by census tract.
# Step 3: Summarize same joined feature class by just census tract id to get total area by census tract. This is different from
# census tract area because it only includes the area of the land use polygons within the census tracts and not the roads or bodies of water.
# Step 4: Join summary tables from steps 2 and 3. Needed to calculate land use proportion by census tract.
# Step 5: Calculating unnormalized commercial density metric.
# Step 6: Max value normalization of commercial density metric field.
#
# Author:      Christopher Papp
#
# Created:     6/3/2022
# Copyright:   (c) Christopher Papp

# -------------------------------------------------------------------------------


import arcpy
import time
timestart = time.time()
arcpy.env.workspace = data = fr"C:\MSGA_Capstone\capstone_data"
arcpy.env.overwriteOutput = True


def main():
    # Tool inputs.
    land_use_file = arcpy.GetParameterAsText(0)
    geographic_area_field = arcpy.GetParameterAsText(1)
    commercial_area = arcpy.GetParameterAsText(2)
    land_uses = arcpy.GetParameterAsText(3)
    geographical_units = arcpy.GetParameterAsText(4)
    geographic_id_field = arcpy.GetParameterAsText(5)
    gdb = arcpy.GetParameterAsText(6)
    arcpy.AddMessage("Calculating Commercial Density Metric...")
    #
    # file locations
    #
    land_use_geographical_units = fr"{gdb}\census_tract_land_use"
    summary_commercial = fr"{gdb}\summary_commercial"
    summary_com_census_tract = fr"{gdb}\summary_com_census_tract"
    commercial_summation = fr"{gdb}\commercial_summation"
    #
    # Step 1: Joining census tracts to land use polygons to have a single feature class with land use, tax lot areas and census tract ID's.
    #
    arcpy.SpatialJoin_analysis(land_use_file, geographical_units, land_use_geographical_units, match_option="LARGEST_OVERLAP")
    # Step 2: Summarize with census tract id field and land use field to get area by land use and by census tract.
    arcpy.SummarizeAttributes_gapro(land_use_geographical_units, summary_commercial, [land_uses, geographic_id_field], [[commercial_area, "SUM"]])
    # Step 3: Summarize same joined feature class by just census tract id to get total area by census tract. This is different from
    # census tract area because it only includes the area of the land use polygons within the census tracts and not the roads or bodies of water.
    arcpy.SummarizeAttributes_gapro(land_use_geographical_units, summary_com_census_tract, [geographic_id_field], [[geographic_area_field, "SUM"]])
    # Step 4: Join summary tables from steps 2 and 3. Needed to calculate land use proportion by census tract.
    # Converting land use and census tract feature classes into table views, which is required for joining them.
    commercial_joined_table = arcpy.AddJoin_management(summary_commercial, geographic_id_field, summary_com_census_tract, geographic_id_field)
    # Table to table conversion is the only way to make the add join operations result permanent.
    arcpy.SelectLayerByAttribute_management(commercial_joined_table, "NEW_SELECTION", "summary_commercial.ct_id > 0")
    arcpy.TableToTable_conversion(commercial_joined_table, gdb, "commercial_summation", fr"SUM_{geographic_area_field} IS NOT NULL")
    # Step 5: Calculating unnormalized commercial density metric.
    arcpy.AddField_management(commercial_summation, "bn_com_sum", "DOUBLE")
    # Calculating the commercial density without normalization.
    arcpy.CalculateField_management(commercial_summation, "bn_com_sum", fr"!SUM_{commercial_area}!/!SUM_{geographic_area_field}!")
    max_value = 0.00000001
    # Step 6: Max value normalization of commercial density metric field.
    # Searching for the highest commercial density in order to max normalize the commercial density field.
    with arcpy.da.SearchCursor(commercial_summation, ["bn_com_sum"]) as cur:
        for row in cur:
            if row[0] is not None:
                if row[0] > max_value:
                    max_value = row[0]
    where = "bn_com_sum IS NULL"
    with arcpy.da.UpdateCursor(commercial_summation, ["bn_com_sum"], where) as cur2:
        for row in cur2:
            row[0] = 0
            cur2.updateRow(row)
    # Normalizing commercial density field using maximum value normalization.
    arcpy.AddField_management(commercial_summation, "com_sum", "DOUBLE")
    arcpy.CalculateField_management(commercial_summation, "com_sum", f"!bn_com_sum!/{max_value}")


if __name__ == '__main__':
    main()
    timeend = time.time()
    timetotal = round((timeend - timestart) / 60, 4)
    print(f"This script took {timetotal} minutes to run.")
