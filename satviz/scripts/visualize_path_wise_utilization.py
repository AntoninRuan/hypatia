# MIT License
#
# Copyright (c) 2020 Debopam Bhattacherjee
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import math
import ephem
import pandas as pd

try:
    from . import util
except (ImportError, SystemError):
    import util

# For specific end-end paths, visualize link utilization at a specific time instance

EARTH_RADIUS = 6378135.0 # WGS72 value; taken from https://geographiclib.sourceforge.io/html/NET/NETGeographicLib_8h_source.html

# CONSTELLATION GENERATION GENERAL CONSTANTS
ECCENTRICITY = 0.0000001  # Circular orbits are zero, but pyephem does not permit 0, so lowest possible value
ARG_OF_PERIGEE_DEGREE = 0.0
PHASE_DIFF = True
EPOCH = "2000-01-01 00:00:00"
UTIL_INTERVAL = 100

# CONSTELLATION SPECIFIC PARAMETERS
"""
# STARLINK 550
NAME = "starlink_550"

################################################################
# The below constants are taken from Starlink's FCC filing as below:
# [1]: https://fcc.report/IBFS/SAT-MOD-20190830-00087
################################################################

MEAN_MOTION_REV_PER_DAY = 15.19  # Altitude ~550 km
ALTITUDE_M = 550000  # Altitude ~550 km
SATELLITE_CONE_RADIUS_M = 940700 # From https://fcc.report/IBFS/SAT-MOD-20181108-00083/1569860.pdf (minimum angle of elevation: 25 deg)
MAX_GSL_LENGTH_M = math.sqrt(math.pow(SATELLITE_CONE_RADIUS_M, 2) + math.pow(ALTITUDE_M, 2))
MAX_ISL_LENGTH_M = 2 * math.sqrt(math.pow(EARTH_RADIUS + ALTITUDE_M, 2) - math.pow(EARTH_RADIUS + 80000, 2)) # ISLs are not allowed to dip below 80 km altitude in order to avoid weather conditions
NUM_ORBS = 72
NUM_SATS_PER_ORB = 22
INCLINATION_DEGREE = 53
"""

# # KUIPER 630
# NAME = "kuiper_630"

# ################################################################
# # The below constants are taken from Kuiper's FCC filing as below:
# # [1]: https://www.itu.int/ITU-R/space/asreceived/Publication/DisplayPublication/8716
# ################################################################

# MEAN_MOTION_REV_PER_DAY = 14.80  # Altitude ~630 km
# ALTITUDE_M = 630000  # Altitude ~630 km
# SATELLITE_CONE_RADIUS_M = ALTITUDE_M / math.tan(math.radians(30.0))  # Considering an elevation angle of 30 degrees; possible values [1]: 20(min)/30/35/45
# MAX_GSL_LENGTH_M = math.sqrt(math.pow(SATELLITE_CONE_RADIUS_M, 2) + math.pow(ALTITUDE_M, 2))
# MAX_ISL_LENGTH_M = 2 * math.sqrt(math.pow(EARTH_RADIUS + ALTITUDE_M, 2) - math.pow(EARTH_RADIUS + 80000, 2))  # ISLs are not allowed to dip below 80 km altitude in order to avoid weather conditions
# NUM_ORBS = 34
# NUM_SATS_PER_ORB = 34
# INCLINATION_DEGREE = 51.9

# TELESAT
NAME = "Telesat"
SHELL_CNTR = 2

MEAN_MOTION_REV_PER_DAY = [None]*SHELL_CNTR
ALTITUDE_M = [None]*SHELL_CNTR
NUM_ORBS = [None]*SHELL_CNTR
NUM_SATS_PER_ORB = [None]*SHELL_CNTR
INCLINATION_DEGREE = [None]*SHELL_CNTR
BASE_ID = [None]*SHELL_CNTR
ORB_WISE_IDS = [None]*SHELL_CNTR

MEAN_MOTION_REV_PER_DAY[0] = 13.66  # Altitude ~1015 km
ALTITUDE_M[0] = 1015000  # Altitude ~1015 km
NUM_ORBS[0] = 27
NUM_SATS_PER_ORB[0] = 13
INCLINATION_DEGREE[0] = 98.98
BASE_ID[0] = 0
ORB_WISE_IDS[0] = []

MEAN_MOTION_REV_PER_DAY[1] = 12.84  # Altitude ~1325 km
ALTITUDE_M[1] = 1325000  # Altitude ~1325 km
NUM_ORBS[1] = 40
NUM_SATS_PER_ORB[1] = 33
INCLINATION_DEGREE[1] = 50.88
BASE_ID[1] = 351
ORB_WISE_IDS[1] = []

# General files needed to generate visualizations; Do not change for different simulations
topFile = "../static_html/top.html"
bottomFile = "../static_html/bottom.html"
city_detail_file = "../../paper/satellite_networks_state/input_data/ground_stations_cities_sorted_by_estimated_2025_pop_top_1000.basic.txt"

# Time in ms for which visualization will be generated
GEN_TIME=10000  #ms

# Input data files; Generated during simulation
# City IDs are available in the city_detail_file.
# If city ID is X (for Paris X = 24) and constellation is Starlink_550 (1584 satellites),
# then offset ID is 1584 + 24 = 1608.
path_file = "../../paper/satgenpy_analysis/data/telesat_1015_isls_plus_grid_ground_stations_top_100_algorithm_free_one_only_over_isls/100ms_for_200s/manual/data/networkx_path_351_to_373.txt"
IN_UTIL_FILE = "../../paper/ns3_experiments/traffic_matrix/runs/run_general_tm_pairing_kuiper_isls_moving/logs_ns3/isl_utilization.csv"

# Output directory for creating visualization html files
OUT_DIR = "../viz_output/"
OUT_HTML_FILE = OUT_DIR + NAME + "_path_wise_util"

sat_objs = []
city_details = {}
paths_over_time = []
time_wise_util = {}


def generate_utilization_at_time():
    """
    Generates link utilization for a specific end-end path at specified time
    :return: HTML formatted string for visualization
    """
    viz_string = ""
    global src_GS
    global dst_GS
    global paths_over_time
    global OUT_HTML_FILE
    lines = [line.rstrip('\n') for line in open(path_file)]
    for i in range(len(lines)):
        val = lines[i].split(",")
        nodes = val[1].split("-")
        paths_over_time.append((int(val[0]), nodes))
    paths_over_time.append((0, nodes))
    SEL_PATH_TIME = 0
    SEL_PATH = []
    for i in range(len(paths_over_time)):
        start_ms = round((paths_over_time[i][0]) / 1000000)
        start_next = 99999999999
        try:
            start_next = round((paths_over_time[i + 1][0]) / 1000000)
        except:
            None
        print(start_ms, GEN_TIME)
        if GEN_TIME >= start_ms and GEN_TIME < start_next:
            SEL_PATH_TIME = paths_over_time[i][0]
            SEL_PATH = paths_over_time[i][1]
            break
    print(SEL_PATH_TIME, SEL_PATH)

    global time_wise_util
    lines = [line.rstrip('\n') for line in open(IN_UTIL_FILE)]
    for i in range(len(lines)):
        val = lines[i].split(",")
        src = int(val[0])
        dst = int(val[1])
        start_ms = round(int(val[2]) / 1000000)
        end_ms = round(int(val[3]) / 1000000)
        utilization = float(val[4])
        if utilization > 1.0:
            SystemError("Util exceeded 1.0")
        interval = 0  # millisecond
        while interval < end_ms - start_ms:
            time_wise_util[src, dst, start_ms + interval, start_ms + interval + UTIL_INTERVAL] = utilization
            interval += UTIL_INTERVAL

    shifted_epoch = (pd.to_datetime(EPOCH) + pd.to_timedelta(GEN_TIME, unit='ms')).strftime(format='%Y/%m/%d %H:%M:%S.%f')
    print(shifted_epoch)

    for i in range(len(sat_objs)):
        sat_objs[i]["sat_obj"].compute(shifted_epoch)
        viz_string += "var redSphere = viewer.entities.add({name : '', position: Cesium.Cartesian3.fromDegrees(" \
                     + str(math.degrees(sat_objs[i]["sat_obj"].sublong)) + ", " \
                     + str(math.degrees(sat_objs[i]["sat_obj"].sublat)) + ", "+str(sat_objs[i]["alt_km"]*1000)+"), "\
                     + "ellipsoid : {radii : new Cesium.Cartesian3(20000.0, 20000.0, 20000.0), "\
                     + "material : Cesium.Color.BLACK.withAlpha(1),}});\n"

    orbit_links = util.find_orbit_links(sat_objs, NUM_ORBS, NUM_SATS_PER_ORB)
    for key in orbit_links:
        sat1 = orbit_links[key]["sat1"]
        sat2 = orbit_links[key]["sat2"]
        viz_string += "viewer.entities.add({name : '', polyline: { positions: Cesium.Cartesian3.fromDegreesArrayHeights([" \
                      + str(math.degrees(sat_objs[sat1]["sat_obj"].sublong)) + "," \
                      + str(math.degrees(sat_objs[sat1]["sat_obj"].sublat)) + "," \
                      + str(sat_objs[sat1]["alt_km"] * 1000) + "," \
                      + str(math.degrees(sat_objs[sat2]["sat_obj"].sublong)) + "," \
                      + str(math.degrees(sat_objs[sat2]["sat_obj"].sublat)) + "," \
                      + str(sat_objs[sat2]["alt_km"] * 1000) + "]), " \
                      + "width: 0.1, arcType: Cesium.ArcType.NONE, " \
                      + "material: new Cesium.PolylineOutlineMaterialProperty({ " \
                      + "color: Cesium.Color.GREY.withAlpha(0.2), outlineWidth: 0, outlineColor: Cesium.Color.BLACK})}});"
    for p in range(len(SEL_PATH)):
        if p == 0 or p == len(SEL_PATH) - 1:
            GS = int(SEL_PATH[p]) - NUM_ORBS*NUM_SATS_PER_ORB
            print(city_details[GS]["name"])
            OUT_HTML_FILE += "_"+city_details[GS]["name"] + "_" +str(SEL_PATH[p])
        if 0 < p < len(SEL_PATH) - 2:
            #print(SEL_PATH[p], SEL_PATH[p+1])
            sat1 = int(SEL_PATH[p])
            sat2 = int(SEL_PATH[p+1])
            util_1 = time_wise_util[sat1, sat2, GEN_TIME - UTIL_INTERVAL, GEN_TIME]
            util_2 = time_wise_util[sat2, sat1, GEN_TIME - UTIL_INTERVAL, GEN_TIME]
            utilization = util_1
            if util_2 > utilization:
                utilization = util_2
            link_width = 1 + 5 * utilization
            if utilization >= 0.5:
                red_weight = 255
                green_weight = 0 + round(255 * (1 - utilization) / 0.5)
            else:
                green_weight = 255
                red_weight = 255 - round(255 * (0.5 - utilization) / 0.5)
            hex_col = '%02x%02x%02x' % (red_weight, green_weight, 0)
            #print(sat1, sat2, util, hex_col)
            viz_string += "viewer.entities.add({name : '', polyline: { positions: Cesium.Cartesian3.fromDegreesArrayHeights([" \
                          + str(math.degrees(sat_objs[sat1]["sat_obj"].sublong)) + "," \
                          + str(math.degrees(sat_objs[sat1]["sat_obj"].sublat)) + "," \
                          + str(sat_objs[sat1]["alt_km"] * 1000) + "," \
                          + str(math.degrees(sat_objs[sat2]["sat_obj"].sublong)) + "," \
                          + str(math.degrees(sat_objs[sat2]["sat_obj"].sublat)) + "," \
                          + str(sat_objs[sat2]["alt_km"] * 1000) + "]), " \
                          + "width: " + str(link_width) + ", arcType: Cesium.ArcType.NONE, " \
                          + "material: new Cesium.PolylineOutlineMaterialProperty({ " \
                          + "color: Cesium.Color.fromCssColorString('#" + str(
                hex_col) + "'), outlineWidth: 0, outlineColor: Cesium.Color.BLACK})}});"

    OUT_HTML_FILE += "_" + str(GEN_TIME) + ".html"
    return viz_string


city_details = util.read_city_details(city_details, city_detail_file)
sat_objs = util.generate_sat_obj_list(
    NUM_ORBS,
    NUM_SATS_PER_ORB,
    EPOCH,
    PHASE_DIFF,
    INCLINATION_DEGREE,
    ECCENTRICITY,
    ARG_OF_PERIGEE_DEGREE,
    MEAN_MOTION_REV_PER_DAY,
    ALTITUDE_M
)
viz_string = generate_utilization_at_time()
util.write_viz_files(viz_string, topFile, bottomFile, OUT_HTML_FILE)
