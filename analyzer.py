import sys
import os
import matplotlib.pyplot as plot
import numpy as np

if len(sys.argv) < 4:
    sys.exit("please define TARGET, value parameter, and orientation.\n eg.: python analyzer.py sky 0 2 (opt. channel) (opt. txpower)\n")

platform = sys.argv[1]
param = sys.argv[2]
orientation  = sys.argv[3]

try:
    chan = sys.argv[4]
    if int(chan) < 11 or int(chan) > 26:
        chan = None
except IndexError:
    chan = None

try:
    txpow = sys.argv[5]
except IndexError:
    txpow = None

DIRECTORY_PATH = ""
link_data = {}
relevant_files = []
times = []

def human_readable():
    global chan
    global txpow
    global param

    if not chan:
        chan = "all"
    if not txpow:
        txpow = "all"
    if param == "0":
        param = "RSSI"
    if param == "1":
        param = "LQI"
    if param == "2":
        param = "dropped packages"

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
    #see if folder with specific orientation is present
    experiment_folder = filter(lambda x: x.endswith('-'+orientation), os.listdir(DIRECTORY_PATH))
    if not experiment_folder or len(experiment_folder) > 1:
        sys.exit("Error: Need exactly one folder ending with -"+orientation)

    DIRECTORY_PATH = os.path.join(DIRECTORY_PATH,experiment_folder[0])

def main(platform, param, chan =None, txpow =None):
    global link_data
    global relevant_files
    global DIRECTORY_PATH
    global times
    make_directory()

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

main(platform,param,chan,txpow)
if param != "time":
    data = link_data.values()
    #data = [range(20),range(10,30)]
    labels = link_data.keys()

    for link in link_data:
        print(link,":",sum(link_data[link]) / float(len(link_data[link])))

    human_readable()
    plot.boxplot(data,vert=True,labels=labels)
    plot.ylabel(param)
    plot.xlabel("Links")
    #plot.yaxis.grid(True)
    plot.title("Average {}\nchannel:{} , txpower:{}".format(param,chan,txpow))
    plot.show()
else:
    print("Avg Time:",sum(times) / float(len(times)))
