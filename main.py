# -------------------------------------------------------------------------------
# Name:        Papp_Christopher_CrimeCode
# Purpose: The purpose of this script is to determine how many landfills are
# within 500 yards of a river. The scope of this will be the 11th pllanning
# district in Virginia.
#
# Author:      Christopher Papp
#
# Created:     10/23/20
# Copyright:   (c) Christopher Papp

# -------------------------------------------------------------------------------



import os
import arcpy
import time
timestart = time.time()
arcpy.env.workspace = data = fr"C:\python\pythonProject"
arcpy.env.overwriteOutput = True
def main():



if __name__ == '__main__':
    main()
    timeend = time.time()
    timetotal = round((timeend - timestart) / 60, 4)
    print(f"This script took {timetotal} minutes to run.")
