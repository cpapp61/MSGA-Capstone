# -------------------------------------------------------------------------------
# Name:        Final_PEI
# Purpose: The purpose of this script is to calculate the first enhanced Pedestrian Environment Index, which combines
# the land use diversity, population density, commercial density and intersection density sub metrics just like with
# the original. It also adds the sidewalk density metric as an enhancer to the PEI. Effectively, this script combines
# the code from the Land Use Mix, Population Density, Commercial Density, Intersection Density, and sidewalk density
# scripts.
#
# Steps
# Step 1: Calculate Land Use Mix metric.
# Step 1.1: Spatially join land use polygons and census tract polygons.
# Step 1.2: Summarize joined feature class by census tract id and land use designation to get area by land use and census tract.
# this step is required for calculating proportion of land use by census tract.
# Step 1.3: Summarize same joined feature class by just census tract id to get total area by census tract. This is different from
# census tract area because it only includes the area of the land use polygons within the census tracts and not the roads or bodies of water.
# Step 1.4: Join summary tables from steps 2 and 3. Needed to calculate land use proportion by census tract.
# Step 1.5: Calculate proportion of each land use by census tract.
# Step 1.6: Calculate Land Use Mix metric and max value normalization.
# Step 2: Calculate Population Density metric.
# Step 2.1: Calculating population density metric by adding a new field and dividing the population field by the area field.
# Step 2.2: Max value normalization of population density metric.
# Step 3: Calculate Commercial Density metric.
# Step 3.1: Summarize joined table from step 1.1 to get area by commercial area by land use and census tract id.
# Step 3.2: Summarize joined table from step 1.2 to get area by census tract id alone.
# Step 3.3: Join summary tables from steps 3.1 and 3.2.
# Step 3.4: Calculating unnormalized commercial density metric.
# Step 4: Calculate Intersection Density metric.
# Step 4.1: Interest street network with itself to identify street intersections, which are displayed as points.
# Step 4.2: Spatially joining street intersection feature class to itself to determine the number of lines that are conected to each intersection.
# Step 4.3: Removing intersections where fewer than 3 roads intersect.
# Step 4.4: Converting multipoints into single points using dissolve with the x and y centroid coordinates used as the dissolve fields.
# Step 4.5: Summarizing intersection points within each census tract, with a 3 way intersection equaling 3 and 4 way intersection equaling 4, and so on.
# Step 4.6: Calculating unnormalized intersection density metric.
# Step 4.7: Max value normalization of Intersection Density metric field.
# Step 5: Calculate Sidewalk Density metric.
# Step 5.1: Apportion polygon to find sidewalk area in square feet per census tract.
# Step 5.2: Calculate unnormalized sidewalk density.
# Step 5.3: Max normalization of sidewalk density field.
# Step 6: Calculate Access to Public Transportation metric.
# Step 6.1: Create census tract centroids.
# Step 6.2: Create lines between all census tract centroids and transportation points.
# Step 6.3: Summarize selected lines based on transportation point ID.
# Step 6.4: Join summarized table from steps 2 and 3 with the lines layer based on transportation location unique id.
# Step 6.5: Summarize lines feature class from step 4 based on census tract ID to derive sum of ratios, which is the
# final accessibility score.
# Step 7: Calculate Access to Parks metric.
# Step 7.1: Create census tract centroids.
# Step 7.2: Create lines between all census tract centroids and transportation points.
# Step 7.3: Summarize selected lines based on transportation point ID.
# Step 7.4: Join summarized table from steps 2 and 3 with the lines layer based on transportation location unique id.
# Step 7.5: Summarize lines feature class from step 4 based on census tract ID to derive sum of ratios, which is the
# final accessibility score.
# Step 8: Calculate Street Network Density metric.
# Step 8.1: Buffer roads using the street width field.
# Step 8.2: Apportion polygons to find street area in square feet per census tract.
# Step 8.3: Calculate unnormalized street network density and max normalization.
# Step 9: Combine metrics to calculate Pedestrian Environment Index.
#
# Author:      Christopher Papp
#
# Created:     6/20/2022
# Copyright:   (c) Christopher Papp

# -------------------------------------------------------------------------------

import arcpy
import time
import math

timestart = time.time()
arcpy.env.workspace = data = fr"C:\MSGA_Capstone\capstone_data"
arcpy.env.overwriteOutput = True


def main():
    #
    # input parameters
    #
    # Land use polygons feature class.
    land_use_file = arcpy.GetParameterAsText(0)
    # Area field of land use polygons feature class.
    land_use_area = arcpy.GetParameterAsText(1)
    # Commercial area field for land use feature class representing commercial area per tax lot.
    commercial_area = arcpy.GetParameterAsText(2)
    # Land use classification field of land use polygons feature class.
    land_uses = arcpy.GetParameterAsText(3)
    # Census tracts feature class.
    geographical_units = arcpy.GetParameterAsText(4)
    # Census tract id field.
    geographic_id_field = arcpy.GetParameterAsText(5)
    # Population field of census tract feature class.
    population_field = arcpy.GetParameterAsText(6)
    # Area field of census tract feature class.
    geographic_area_field = arcpy.GetParameterAsText(7)
    # Street network feature class.
    street_network = arcpy.GetParameterAsText(8)
    # Area field of the roads feature class.
    roads_area_field = arcpy.GetParameterAsText(9)
    # Sidewalk polygons feature class.
    sidewalks = arcpy.GetParameterAsText(10)
    # Area field of the sidewalk feature class.
    sidewalk_area_field = arcpy.GetParameterAsText(11)
    # Points feature class representing transportation (metro and bus) stops.
    transportation_points = arcpy.GetParameterAsText(12)
    # Unique ID of transportation (subway and bus) points.
    transportation_id_field = arcpy.GetParameterAsText(13)
    # Parks polygon feature class.
    parks = arcpy.GetParameterAsText(14)
    # Input geodatabase.
    gdb = arcpy.GetParameterAsText(15)
    output = arcpy.GetParameterAsText(16)
    arcpy.env.workspace = gdb

    #
    # file locations
    #
    land_use_geographical_units = fr"{gdb}\census_tract_land_use"
    summary_land_use = fr"{gdb}\summary_land_use"
    summary_census_tract = fr"{gdb}\summary_census_tract"
    land_use_summation = fr"{gdb}\land_use_summation"
    final_land_use_summation = fr"{gdb}\final_land_use_summation"
    summary_commercial = fr"{gdb}\summary_commercial"
    summary_com_census_tract = fr"{gdb}\summary_com_census_tract"
    commercial_summation = fr"{gdb}\commercial_summation"
    PEI_step_2 = fr"{gdb}\PEI_step_2"
    PEI_step_3 = fr"{gdb}\PEI_step_3"
    street_intersect = fr"{gdb}\street_intersect"
    street_street_join = fr"{gdb}\street_street_join"
    street_intersection_points = fr"{gdb}\street_intersection_points"
    street_dissolve = fr"{gdb}\street_dissolve"
    single_street = fr"{gdb}\single_street"
    street_summarize = fr"{gdb}\street_summarize"
    final_commercial_sum = fr"{gdb}\final_commercial_sum"
    sidewalk_apportion = fr"{gdb}\sidewalk_apportion"
    geographical_centroids = fr"{gdb}\geographical_centroids"
    census_tract_transportation = fr"{gdb}\census_tract_transportation"
    ctt_lines = fr"{gdb}\ctt_lines"
    transportation_summarize = fr"{gdb}\transportation_summarize"
    view_lines = fr"{gdb}\view_lines"
    ratio_transportation = fr"{gdb}\ratio_transportation"
    transportation_accessibility = fr"{gdb}\transportation_accessibility"
    sidewalks_distance = fr"{gdb}\sidewalks_distance"
    distance_reclass = fr"{gdb}\distance_reclass"
    parks_FeatureToPoint = fr"C:\MSGA_Capstone\capstone_data\parks_FeatureToPoint.shp"
    parks_raster = fr"{gdb}\parks_raster"
    parks_access = fr"{gdb}\parks_access"
    roads_buffer = fr"{gdb}\roads_buffer"
    road_apportion = fr"{gdb}\road_apportion"

    arcpy.AddMessage("Calculating Land Use Mix Metric...")


    # Step 1: Calculating land use mix metric.

    # Step 1.1: Spatially join land use polygons and census tract polygons.
    #
    # joining zonal geometry to land use polygons to have a single feature class with land use, tax lot areas and census tract ID's
    #

    arcpy.SpatialJoin_analysis(land_use_file, geographical_units, land_use_geographical_units,
                               match_option="HAVE_THEIR_CENTER_IN")

    # Step 1.2: Summarize joined feature class by census tract id and land use designation to get area by land use and census tract.
    # this step is required for calculating proportion of land use by census tract.
    arcpy.SummarizeAttributes_gapro(land_use_geographical_units, summary_land_use, [land_uses, geographic_id_field],
                                    [[land_use_area, "SUM"]])

    # Step 1.3: Summarize same joined feature class by just census tract id to get total area by census tract. This is different from
    # census tract area because it only includes the area of the land use polygons within the census tracts and not the roads or bodies of water.
    arcpy.SummarizeAttributes_gapro(summary_land_use, summary_census_tract, [geographic_id_field],
                                    [[fr"SUM_{land_use_area}", "SUM"]])

    # Step 1.4: Join summary tables from steps 2 and 3. Needed to calculate land use proportion by census tract.
    land_use_joined_table = arcpy.AddJoin_management(summary_land_use, geographic_id_field, summary_census_tract,
                                                     geographic_id_field, "KEEP_ALL", "NO_INDEX_JOIN_FIELDS")

    arcpy.SelectLayerByAttribute_management(land_use_joined_table, "NEW_SELECTION", "summary_land_use.ct_id > 0")
    arcpy.TableToTable_conversion(land_use_joined_table, gdb, "land_use_summation", "LandUse IS NOT NULL")
    # calculate shannon's diversity index. This index is defined as the summation of the proportion of the proportion of each land use
    # multiplied by the log of the proportion of each land use. This sum is multiplied by -1 and divided by the log of the number
    # of land uses to obtain the land use diversity of each census tract.

    # Step 1.5: Calculate proportion of each land use by census tract.
    arcpy.AddField_management(land_use_summation, "proportion", "DOUBLE")
    arcpy.CalculateField_management(land_use_summation, "proportion",
                                    fr"!SUM_{land_use_area}!/!SUM_SUM_{land_use_area}!")

    # Step 1.6: Calculate Land Use Mix metric and max value normalization.
    arcpy.AddField_management(land_use_summation, "sha_num", "DOUBLE")
    arcpy.CalculateField_management(land_use_summation, "sha_num", "-!proportion! * math.log(!proportion!)")
    arcpy.SummarizeAttributes_gapro(land_use_summation, final_land_use_summation, [geographic_id_field],
                                    [["sha_num", "SUM"]])

    arcpy.AddField_management(final_land_use_summation, "shannon", "DOUBLE")
    max_value = 0.000000000000000001
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
            if key not in land_use_dict.keys():
                land_use_dict['key'] = key
                land_use_number += 1

    # Calculating the normalized shannon's diversity value based on the maximum shannon's value within the study area.
    max_value = max_value / math.log(land_use_number)
    with arcpy.da.UpdateCursor(final_land_use_summation, ["SUM_sha_num", "shannon"]) as cur2:
        for row in cur2:
            if row[0] is not None:
                row[1] = (row[0] / math.log(land_use_number)) / max_value
                cur2.updateRow(row)
            else:
                row[0] = 0
                row[1] = 0
                cur2.updateRow(row)


    # Step 2: Calculating Population Density metric.

    # Step 2.1: Calculating population density metric by adding a new field and dividing the population field by the area field.
    arcpy.AddMessage("Calculating Population Density metric...")
    arcpy.AddField_management(geographical_units, "bn_pop_density", "DOUBLE")
    arcpy.CalculateField_management(geographical_units, "bn_pop_density",
                                    f"!{population_field}!/!{geographic_area_field}!")

    # Step 2.2: Max value normalization of population density metric.
    max_value = 0.000000000000000001
    with arcpy.da.SearchCursor(geographical_units, ["bn_pop_density"]) as cur:
        for row in cur:
            if row[0] is not None:
                if row[0] > max_value:
                    max_value = row[0]

    with arcpy.da.UpdateCursor(geographical_units, ["bn_pop_density"]) as cur:
        for row in cur:
            if row[0] is None:
                row[0] = 0
                cur.updateRow(row)

    arcpy.AddField_management(geographical_units, "pop_density", "DOUBLE")
    arcpy.CalculateField_management(geographical_units, "pop_density", f"!bn_pop_density!/{max_value}")
    land_use_population_density_table = arcpy.AddJoin_management(geographical_units, geographic_id_field,
                                                                 final_land_use_summation, geographic_id_field,
                                                                 "KEEP_ALL", "NO_INDEX_JOIN_FIELDS")
    arcpy.SelectLayerByAttribute_management(land_use_population_density_table, "NEW_SELECTION",
                                            "final_land_use_summation.ct_id > 0")
    arcpy.TableToTable_conversion(land_use_population_density_table, gdb, "PEI_step_2")

    with arcpy.da.UpdateCursor(PEI_step_2, ["SUM_sha_num", "shannon"]) as cur4:
        for row in cur4:
            if row[0] is None:
                row[0] = 0
                row[1] = 0
                cur4.updateRow(row)


    # Step 3: Calculating Commercial Density metric.

    # Step 3.1: Summarize joined table from step 1.1 to get area by commercial area by land use and census tract id.
    arcpy.AddMessage("Calculating Commercial Density metric...")
    arcpy.SummarizeAttributes_gapro(land_use_geographical_units, summary_commercial, [land_uses, geographic_id_field],
                                    [[commercial_area, "SUM"]])

    # Step 3.2: Summarize joined table from step 1.2 to get area by census tract id alone.
    arcpy.SummarizeAttributes_gapro(land_use_geographical_units, summary_com_census_tract, [geographic_id_field],
                                    [[geographic_area_field, "SUM"]])

    # Step 3.3: Join summary tables from steps 3.1 and 3.2. Needed to calculate land use proportion by census tract.
    commercial_joined_table = arcpy.AddJoin_management(summary_commercial, geographic_id_field,
                                                       summary_com_census_tract,
                                                       geographic_id_field)
    # Table to table conversion is the only way to make the add join operations result permanent.
    arcpy.SelectLayerByAttribute_management(commercial_joined_table, "NEW_SELECTION", "summary_commercial.ct_id > 0")
    arcpy.TableToTable_conversion(commercial_joined_table, gdb, "commercial_summation",
                                  fr"SUM_{geographic_area_field} IS NOT NULL")

    # Step 3.4: Calculating unnormalized commercial density metric.
    arcpy.AddField_management(commercial_summation, "bn_com_sum", "DOUBLE")
    # Calculating the commercial density without normalization.
    arcpy.CalculateField_management(commercial_summation, "bn_com_sum",
                                    fr"!SUM_{commercial_area}!/!SUM_{geographic_area_field}!")
    arcpy.SummarizeAttributes_gapro(commercial_summation, final_commercial_sum, [geographic_id_field],
                                    [[fr"bn_com_sum", "SUM"]])
    max_value = 0.000000000000000001

    # Step 3.5: Max value normalization of commercial density metric field.
    # Searching for the highest commercial density in order to max normalize the commercial density field.
    with arcpy.da.SearchCursor(final_commercial_sum, ["SUM_bn_com_sum"]) as cur:
        for row in cur:
            if row[0] is not None:
                if row[0] > max_value:
                    max_value = row[0]
    where = "SUM_bn_com_sum IS NULL"
    with arcpy.da.UpdateCursor(final_commercial_sum, ["SUM_bn_com_sum"], where) as cur2:
        for row in cur2:
            if row[0] is None:
                row[0] = 0
                cur2.updateRow(row)
    # Normalizing commercial density field using maximum value normalization.
    arcpy.AddField_management(final_commercial_sum, "com_sum", "DOUBLE")
    arcpy.CalculateField_management(final_commercial_sum, "com_sum", f"!SUM_bn_com_sum!/{max_value}")
    land_use_population_commercial_density_table = arcpy.AddJoin_management(PEI_step_2, geographic_id_field,
                                                                            final_commercial_sum,
                                                                            geographic_id_field,
                                                                            "KEEP_ALL", "NO_INDEX_JOIN_FIELDS")
    arcpy.SelectLayerByAttribute_management(land_use_population_commercial_density_table, "NEW_SELECTION",
                                            "PEI_step_2.ct_id > 0")
    arcpy.TableToTable_conversion(land_use_population_commercial_density_table, gdb, "PEI_step_3")


    # Step 4: Calculating Intersection Density metric.

    # Step 4.1: Intersect street network with itself to identify street intersections, which are displayed as points.
    arcpy.AddMessage("Calculating Intersection Density metric...")
    arcpy.Intersect_analysis(street_network, street_intersect, "ALL", None, "POINT")

    # Step 4.2: Spatially joining street intersection feature class to itself to determine the number of lines that are conected to each intersection.
    arcpy.SpatialJoin_analysis(street_intersect, street_intersect, street_street_join)

    # Step 4.3: Removing intersections where fewer than 3 roads intersect.
    select_street = arcpy.SelectLayerByLocation_management(street_street_join, 'INTERSECT', geographical_units, 0,
                                                           'NEW_SELECTION')
    arcpy.SelectLayerByAttribute_management(select_street, 'NEW_SELECTION', '"Join_Count" > 2')
    arcpy.CopyFeatures_management(select_street, street_intersection_points)

    # Step 4.4: Converting multipoints into single points using dissolve with the x and y centroid coordinates used as the dissolve fields.
    arcpy.AddGeometryAttributes_management(street_intersection_points, "CENTROID", "FEET_US", "SQUARE_FEET_US")
    arcpy.Dissolve_management(street_intersection_points, street_dissolve, "CENTROID_X;CENTROID_Y", "Join_Count MEAN",
                              "MULTI_PART", "DISSOLVE_LINES")
    arcpy.MultipartToSinglepart_management(street_dissolve, single_street)

    # Step 4.5: Summarizing intersection points within each census tract, with a 3 way intersection equaling 3 and 4 way intersection equaling 4, and so on.
    arcpy.SummarizeWithin_gapro(single_street, street_summarize, "POLYGON", '', None, geographical_units, "ADD_SUMMARY",
                                '', "MEAN_Join_Count SUM")

    # Step 4.6: Calculating unnormalized intersection density metric.
    arcpy.AddField_management(street_summarize, "bn_intersection", "DOUBLE")
    arcpy.CalculateField_management(street_summarize, "bn_intersection",
                                    fr"!SUM_MEAN_Join_Count!/(!{geographic_area_field}!*10.764)")
    arcpy.AddField_management(street_summarize, "intersection", "DOUBLE")

    # Step 4.7: Max value normalization of Intersection Density metric field.
    # Determining max intersection density value for max value normalization.
    max_value = 0.000000000000000001
    with arcpy.da.SearchCursor(street_summarize, ["bn_intersection"]) as cursor:
        for row in cursor:
            if row[0] is not None:
                if row[0] > max_value:
                    max_value = row[0]

    with arcpy.da.UpdateCursor(street_summarize, ["bn_intersection"]) as cursor:
        for row in cursor:
            if row[0] is None:
                row[0] = 0
                cursor.updateRow(row)
    # Max value normalization.
    arcpy.CalculateField_management(street_summarize, "intersection", fr"!bn_intersection!/{max_value}")
    final_density_table = arcpy.AddJoin_management(PEI_step_3, geographic_id_field,
                                                   street_summarize,
                                                   geographic_id_field,
                                                   "KEEP_ALL", "NO_INDEX_JOIN_FIELDS")
    arcpy.SelectLayerByAttribute_management(final_density_table, "NEW_SELECTION", "PEI_step_3.ct_id > 0")
    arcpy.TableToTable_conversion(final_density_table, gdb, output)
    with arcpy.da.UpdateCursor(output, ["intersection"]) as cur5:
        for row in cur5:
            if row[0] is None:
                row[0] = 0
                cur5.updateRow(row)


    # Step 5: Calculate Sidewalk Density metric.
    arcpy.AddMessage("Calculating Sidewalk Density metric...")

    # Step 5.1: Apportion polygon to find sidewalk area in square feet per census tract.
    arcpy.ApportionPolygon_analysis(sidewalks, sidewalk_area_field, geographical_units, sidewalk_apportion, "AREA")

    # Step 5.2: Calculate unnormalized sidewalk density.
    arcpy.AddField_management(sidewalk_apportion, "bn_sidewalk_density", "DOUBLE")
    arcpy.CalculateField_management(sidewalk_apportion, "bn_sidewalk_density",
                                    f"!{sidewalk_area_field}!/!{geographic_area_field}!")
    # Step 5.3: Max normalization of sidewalk density field.
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

    sidewalk_density = {}

    with arcpy.da.SearchCursor(sidewalk_apportion, ["ct_id", "sidewalk_density"]) as cursor:
        for row in cursor:
            sidewalk_density[row[0]] = row[1]


    # Step 6: Calculate Public Transportation Access metric.
    arcpy.AddMessage("Calculating Access to Public Transportation metric...")

    # Step 6.1: Create census tract centroids.
    arcpy.FeatureToPoint_management(geographical_units, geographical_centroids)

    # Step 6.2: Create lines between all census tract centroids and transportation points.
    arcpy.AddGeometryAttributes_management(geographical_centroids, "POINT_X_Y_Z_M", "FEET_US")
    arcpy.AddGeometryAttributes_management(transportation_points, "POINT_X_Y_Z_M", "FEET_US")
    arcpy.AddField_management(transportation_points, "XCoord", "DOUBLE")
    arcpy.AddField_management(transportation_points, "YCoord", "DOUBLE")
    arcpy.CalculateField_management(transportation_points, "XCoord", "!POINT_X!")
    arcpy.CalculateField_management(transportation_points, "YCoord", "!POINT_Y!")
    arcpy.SpatialJoin_analysis(geographical_centroids, transportation_points, census_tract_transportation,
                               "JOIN_ONE_TO_MANY", "KEEP_ALL", match_option="WITHIN_A_DISTANCE",
                               search_radius="10000 feet")
    arcpy.XYToLine_management(census_tract_transportation, ctt_lines, "POINT_X", "POINT_Y", "XCoord", "YCoord",
                              "Geodesic", geographic_id_field, attributes="ATTRIBUTES")
    arcpy.AddGeometryAttributes_management(ctt_lines, "Length", "Feet (United States)")

    # Step 6.3: Summarize selected lines based on transportation point ID and calculate ratio field.
    arcpy.SummarizeAttributes_gapro(ctt_lines, transportation_summarize, [transportation_id_field],
                                    [[population_field, "SUM"]])
    arcpy.AddField_management(transportation_summarize, "ratio", "DOUBLE")
    arcpy.CalculateField_management(transportation_summarize, "ratio", f"1/!SUM_{population_field}!")

    # Step 6.4: Join summarized table from steps 2 and 3 with the lines layer based on transportation location unique id.
    arcpy.MakeFeatureLayer_management(ctt_lines, view_lines)
    lines_table = arcpy.AddJoin_management(view_lines, transportation_id_field, transportation_summarize,
                                           transportation_id_field)
    arcpy.TableToTable_conversion(lines_table, gdb, "ratio_transportation")

    # Step 6.5: Summarize lines feature class from step 4 based on census tract ID to derive sum of ratios, which is the
    # final accessibility score.
    arcpy.SummarizeAttributes_gapro(ratio_transportation, transportation_accessibility, [geographic_id_field],
                                    [["ratio", "SUM"]])
    transportation_accessibility = fr"{gdb}\transportation_accessibility"
    transportation_access = {}
    with arcpy.da.SearchCursor(transportation_accessibility, ["ct_id", "SUM_ratio"]) as cursor:
        for row in cursor:
            transportation_access[row[0]] = row[1]


    # Step 7: Calculate Access to Parks metric.
    arcpy.AddMessage("Calculating Access to Parks metric...")

    # Step 7.1: Calculate euclidean distance raster for distance from sidewalk polygons.
    with arcpy.EnvManager(mask=geographical_units):
        out_distance_raster = arcpy.sa.EucDistance(sidewalks, None, 10, None, "PLANAR", None, None)
        out_distance_raster.save(sidewalks_distance)

    # Step 7.2: Reclassify euclidean distance from sidewalks raster to create cost surface.
    arcpy.Reclassify_3d(sidewalks_distance, "VALUE",
                        "0 100 1;100 200 2;200 400 3;400 800 4;800 1600 5;1600 84892.132812 6", distance_reclass,
                        "DATA")

    # Step 7.3: Convert park polygons into points.
    arcpy.FeatureToPoint_management(parks, parks_FeatureToPoint)

    # Step 7.4: Select census tracts that intersect with park points.
    arcpy.SelectLayerByLocation_management(geographical_units, "INTERSECT", parks_FeatureToPoint, None,
                                           "NEW_SELECTION", "NOT_INVERT")

    # Step 7.5: Calculate cost distance using parks points and cost surface from steps 4 and 2, respectively.
    out_distance_raster = arcpy.sa.CostDistance(parks_FeatureToPoint, distance_reclass)
    out_distance_raster.save(parks_raster)

    # Step 7.6: Calculate zonal statistics to obtain all the summary statistics of the cost distance raster from step 5 by census tract.
    arcpy.ia.ZonalStatisticsAsTable(geographical_units, "GEOID", parks_raster, parks_access, "DATA", "ALL",
                                    "CURRENT_SLICE", 90, "AUTO_DETECT")
    arcpy.AddField_management(parks_access, "br_ct_id", "DOUBLE")
    arcpy.CalculateField_management(parks_access, "br_ct_id", "!GEOID!")
    arcpy.AddField_management(parks_access, "ct_id", "DOUBLE")
    arcpy.CalculateField_management(parks_access, "ct_id", "round(!br_ct_id!,0)")
    min_value = 1000000

    # Step 7.7: Calculate park access field and normalize it using max value normalization.
    with arcpy.da.SearchCursor(parks_access, ["MEDIAN"]) as cursor:
        for row in cursor:
            if min_value > row[0]:
                min_value = row[0]
    arcpy.AddField_management(parks_access, "park_access", "DOUBLE")
    arcpy.CalculateField_management(parks_access, "park_access", fr"(1/!MEDIAN!)/(1/{min_value})")
    access_to_parks = {}
    with arcpy.da.SearchCursor(parks_access, ["ct_id", "park_access"]) as cursor:
        for row in cursor:
            access_to_parks[math.floor(row[0])] = row[1]


    # Step 8: Calculate Street Network Density metric.
    arcpy.AddMessage("Calculating Street Network Density...")

    # Step 8.1: Buffer roads using the street width field.
    arcpy.AddField_management(street_network, "width", "DOUBLE")
    arcpy.CalculateField_management(street_network, "width", f"!{roads_area_field}!/2")
    arcpy.Buffer_analysis(street_network, roads_buffer, "width", dissolve_option="ALL")

    # Step 8.2: Apportion polygons to find street area in square feet per census tract.
    arcpy.AddGeometryAttributes_management(roads_buffer, "AREA", Area_Unit="Square feet (United States)")
    arcpy.ApportionPolygon_analysis(roads_buffer, "POLY_AREA", geographical_units, road_apportion, "AREA")

    # Step 8.3: Calculate unnormalized street network density and max normalization.
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

    street_network_density = {}
    with arcpy.da.SearchCursor(road_apportion, ["ct_id", "network_density"]) as cursor:
        for row in cursor:
            street_network_density[row[0]] = row[1]
    arcpy.Delete_management(summary_census_tract)
    arcpy.Delete_management(land_use_summation)
    arcpy.Delete_management(summary_land_use)
    arcpy.Delete_management(final_land_use_summation)
    arcpy.Delete_management(land_use_geographical_units)
    arcpy.Delete_management(summary_com_census_tract)
    arcpy.Delete_management(summary_commercial)
    arcpy.Delete_management(commercial_summation)
    arcpy.Delete_management(final_commercial_sum)
    arcpy.Delete_management(PEI_step_2)
    arcpy.Delete_management(street_intersect)
    arcpy.Delete_management(street_street_join)
    arcpy.Delete_management(street_intersection_points)
    arcpy.Delete_management(street_dissolve)
    arcpy.Delete_management(single_street)
    arcpy.Delete_management(street_summarize)
    arcpy.Delete_management(PEI_step_3)
    arcpy.Delete_management(sidewalk_apportion)
    arcpy.Delete_management(geographical_centroids)
    arcpy.Delete_management(census_tract_transportation)
    arcpy.Delete_management(view_lines)
    arcpy.Delete_management(transportation_summarize)
    arcpy.Delete_management(ctt_lines)
    arcpy.Delete_management(ratio_transportation)
    arcpy.Delete_management(transportation_accessibility)
    arcpy.Delete_management(sidewalks_distance)
    arcpy.Delete_management(parks_FeatureToPoint)
    arcpy.Delete_management(distance_reclass)
    arcpy.Delete_management(parks_raster)
    arcpy.Delete_management(parks_access)
    arcpy.Delete_management(roads_buffer)
    arcpy.Delete_management(road_apportion)

    # Step 9: Combine metrics to calculate Pedestrian Environment Index.
    arcpy.AddMessage("Combining metrics to calculate Pedestrian Environment Index.")

    arcpy.AddField_management(geographical_units, "land_use_diversity", "DOUBLE")
    arcpy.AddField_management(geographical_units, "commercial_density", "DOUBLE")
    arcpy.AddField_management(geographical_units, "intersection_density", "DOUBLE")
    arcpy.AddField_management(geographical_units, "sidewalk_density", "DOUBLE")
    arcpy.AddField_management(geographical_units, "transportation_access", "DOUBLE")
    arcpy.AddField_management(geographical_units, "parks_access", "DOUBLE")
    arcpy.AddField_management(geographical_units, "sn_density", "DOUBLE")
    arcpy.AddField_management(geographical_units, output, "DOUBLE")

    with arcpy.da.UpdateCursor(geographical_units, ["ct_id", "sidewalk_density", "transportation_access", "parks_access", "sn_density"]) as cursor:
        for row in cursor:
            row[1] = sidewalk_density[row[0]]
            del sidewalk_density[row[0]]
            row[2] = transportation_access[row[0]]
            del transportation_access[row[0]]
            if row[0] in access_to_parks.keys():
                row[3] = access_to_parks[math.floor(row[0])]
                del access_to_parks[math.floor(row[0])]
            else:
                row[3] = 0
            row[4] = street_network_density[row[0]]
            del street_network_density[row[0]]
            cursor.updateRow(row)

    land_use_diversity = {}
    commercial_density = {}
    intersection_density = {}

    with arcpy.da.SearchCursor(output, ["ct_id", "shannon", "com_sum", "intersection"]) as cur6:
        for row in cur6:
            land_use_diversity[row[0]] = row[1]
            commercial_density[row[0]] = row[2]
            intersection_density[row[0]] = row[3]

    with arcpy.da.UpdateCursor(geographical_units, ["ct_id", "land_use_diversity", "commercial_density", "intersection_density"]) as cursor:
        for row in cursor:
            row[1] = land_use_diversity[row[0]]
            row[2] = commercial_density[row[0]]
            row[3] = intersection_density[row[0]]
            cursor.updateRow(row)

    arcpy.CalculateField_management(geographical_units, output, f"((1 + !land_use_diversity!) * (1 + !pop_density!) * "
                                                                f"(1 + !commercial_density!) * (1 + !intersection_density!) "
                                                                f"* (1 + !sidewalk_density!) * (1 + !transportation_access!) "
                                                                f"* (1 + !parks_access!) * (1 + !sn_density!))/256")


if __name__ == '__main__':
    main()
    timeend = time.time()
    timetotal = round((timeend - timestart) / 60, 4)
    print(f"This script took {timetotal} minutes to run.")
