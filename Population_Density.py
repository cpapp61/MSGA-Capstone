# -------------------------------------------------------------------------------
# Name:        Population_Density
# Purpose: The purpose of this script is to calculate the population density sub metric.
# This metric is measured in population per square feet, since the coordinate system is
# NAD_1983_StatePlane_New_York_Long_Island_FIPS_3104_Feet. This metric is measured at the
# census tract level.
#
# Steps
# Step 1: Calculating population density metric by adding a new field and dividing the population field by the area field.
# Step 2: Max value normalization of population density metric.
#
# Author:      Christopher Papp
#
# Created:     6/3/2022
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
    # Tool inputs.
    census_tract = arcpy.GetParameterAsText(0)
    population_field = arcpy.GetParameterAsText(1)
    area_field = arcpy.GetParameterAsText(2)
    arcpy.AddMessage("Calculating Population Density Metric...")

    # Step 1: Calculating population density metric by adding a new field and dividing the population field by the area field.
    arcpy.AddField_management(census_tract, "bn_pop_density", "DOUBLE")
    arcpy.CalculateField_management(census_tract, "bn_pop_density", f"!{population_field}!/!{area_field}!")
    max_value = 0

    # Step 2: Max value normalization of population density metric.
    # Searching for the highest population density in order to max normalize the population density field.
    with arcpy.da.SearchCursor(census_tract, ["bn_pop_density"]) as cur:
        for row in cur:
            if row[0] is not None:
                if row[0] > max_value:
                    max_value = row[0]
    with arcpy.da.UpdateCursor(census_tract, ["bn_pop_density"]) as cur:
        for row in cur:
            if row[0] is None:
                row[0] = 0
                cur.updateRow(row)

    # Normalizing population density by maximum value normalization.
    arcpy.AddField_management(census_tract, "pop_density", "DOUBLE")
    arcpy.CalculateField_management(census_tract, "pop_density", f"!bn_pop_density!/{max_value}")


if __name__ == '__main__':
    main()
    timeend = time.time()
    timetotal = round((timeend - timestart) / 60, 4)
    print(f"This script took {timetotal} minutes to run.")
