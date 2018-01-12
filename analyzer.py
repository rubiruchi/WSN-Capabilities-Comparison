import sys
import os
import matplotlib.pyplot as plot
import numpy as np
from collections import OrderedDict

# if len(sys.argv) < 4:
#     sys.exit("please define TARGET, value parameter, and orientation.\n eg.: python analyzer.py sky 0 2 (opt. channel) (opt. txpower)\n")
#
# platform = sys.argv[1]
# param = sys.argv[2]
# orientation  = sys.argv[3]
#
# try:
#     chan = sys.argv[4]
#     if int(chan) < 11 or int(chan) > 26:
#         chan = None
# except IndexError:
#     chan = None
#
# try:
#     txpow = sys.argv[5]
# except IndexError:
#     txpow = None

DIRECTORY_PATH = ""
link_data = {}
times = []

def readable_chan():
    r_chan = chan
    if not chan:
        r_chan = "all"

    return r_chan

def readable_param():
    if param == "0":
        r_param = "RSSI"
    if param == "1":
        r_param = "LQI"
    if param == "2":
        r_param = "dropped packages"

    return r_param

def readable_txpow():
    r_txpow = txpow
    if not txpow:
        r_txpow = "all"

    return r_txpow


def make_directory():
    global DIRECTORY_PATH
    global configurations

    #if stick not present use pardir
    DIRECTORY_PATH = '/media/pi/Experiments'
    if not os.path.exists(DIRECTORY_PATH):
        DIRECTORY_PATH = os.path.join(os.pardir,'Measurements/{}'.format(platform))
        if not os.path.exists(DIRECTORY_PATH):
            sys.exit("Error: Measurement directory not found.")
    #if stick is present:use stick.
    else:
        DIRECTORY_PATH = os.path.join(DIRECTORY_PATH,'Measurements/{}'.format(platform))
        if not os.path.exists(DIRECTORY_PATH):
            sys.exit("Error: Measurement directory not found.")


def analyze(platform, param, orientation, chan =None, txpow =None):
    global link_data
    global DIRECTORY_PATH
    global times

    relevant_files = []

    print("platform:",platform," param:", param," orient:", orientation," chan:", chan,"tx ", txpow)

    make_directory()
    #see if folder with specific orientation is present
    experiment_folder = filter(lambda x: x.endswith('-'+orientation), os.listdir(DIRECTORY_PATH))
    #if not experiment_folder or len(experiment_folder) > 1:
        #sys.exit("Error: Need exactly one folder ending with -"+orientation)
    DIRECTORY_PATH = os.path.join(DIRECTORY_PATH,experiment_folder[0])
    if not os.path.exists(DIRECTORY_PATH):
        raise OSError("File not found")

    print(DIRECTORY_PATH)

    """Gather files containing relevant information"""
    for filename in os.listdir(DIRECTORY_PATH):
        split_file = filename.split(',')
        experiment_numofnodes = int(split_file[0])
        experiment_chan  = split_file[1]
        experiment_txpow = split_file[2]
        experiment_param = split_file[3]

        if chan and chan != experiment_chan:
            continue
        if txpow and txpow != experiment_txpow:
            continue
        if param == "time" or param == experiment_param:
            relevant_files.append(filename)

    if param != "time":
        """init dict (link : list)"""
        for i in range(2,experiment_numofnodes+1):
            link_data["1-"+str(i)] = []

    for experiment in relevant_files:
        with open(os.path.join(DIRECTORY_PATH,experiment),'r') as experiment_file:
            for line in experiment_file:
                if param != "time":
                    """evaluate measurement and add measured value to list"""
                    if line.startswith("{"):
                        measurement = eval(line)
                        if int(measurement["sender"]) == 1:
                            link_data[measurement["sender"]+"-"+measurement["receiver"]].append(int(measurement["value"]))
                        elif int(measurement["receiver"]) == 1:
                            link_data[measurement["receiver"]+"-"+measurement["sender"]].append(int(measurement["value"]))

                elif not line.startswith("Temp") and not line.startswith("{"):
                    """parse time in seconds"""
                    hms = [3600,60,1]
                    measurement_time = sum([a*b for a,b in zip(hms, map(int,line.split(':')))])
                    times.append(measurement_time)

# """parse temperature"""
# elif(line.startswith("Temp")):
#     measurement_temp =
#     measurement_hum  =
#

def get_txpowers(platform):
    opn_txpowers = map(str,[5,3,1,0,-1,-3,-5,-7,-15])
    stg_txpowers = map(str,[5,3,1,0,-3,-15])
    msp_txpowers = map(str,[31,27,23,19,15,7])
    txpowers = []

    if platform == "sky" or platform == "z1":
        txpowers = msp_txpowers
    elif platform == "openmote-cc2538":
        txpowers = opn_txpowers
    elif platform == "srf06-cc26xx":
        txpowers = stg_txpowers

    txpowers.append(None)

    return txpowers

def get_orientations(platform):
    orientations = []

    if platform == "openmote-cc2538":
        orientations = map(str,range(2,6))
    else:
        orientations = map(str,range(2,10))

    return orientations


platforms = ["openmote-cc2538","sky","z1","srf06-cc26xx"]
parameters = map(str,range(3))
channels = map(str,range(11,27))
channels.append(None)

orientations= []

for platform in platforms:
    for param in parameters:
        for chan in channels:
            for txpow in get_txpowers(platform):
                for orientation in get_orientations(platform):
                    try:
                        analyze(platform,param, orientation, chan,txpow)
                    except OSError:
                        continue

                    if param != "time":
                        od = OrderedDict(sorted(link_data.items()))
                        data = od.values()
                        labels = od.keys()

                        # for link in link_data:
                        #     print(link,":",sum(link_data[link]) / float(len(link_data[link])))
                        if data:
                            plot.boxplot(data,vert=True,labels=labels)
                            plot.ylabel(param)
                            plot.ylim(-100,0)
                            plot.xlabel("Links")
                            plot.title("Average {}\nchannel:{} , txpower:{}".format(readable_param(),readable_chan(),readable_txpow()))
                            path = os.path.join(os.pardir,"Plots/{}/{}/{}".format(orientation,readable_chan(),readable_txpow()))
                            if not os.path.exists(path):
                                os.makedirs(path)
                            filename = platform+","+readable_chan()+","+readable_txpow()+","+readable_param()+"->"+orientation
                            plot.savefig(os.path.join(path,filename))
                            plot.close()

                    else:
                        print("Avg Time:",sum(times) / float(len(times)))

print("Finished")
