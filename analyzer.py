import sys
import os
import matplotlib.pyplot as plot
import numpy as np
from collections import OrderedDict

def readable_channel(channel):
    r_chan = channel
    if not r_chan:
        r_chan = "all"

    return r_chan

def readable_param(param):
    if param == "0":
        r_param = "RSSI"
    if param == "1":
        r_param = "LQI"
    if param == "2":
        r_param = "dropped packages"

    return r_param

def readable_txpower(txpower):
    r_txpow = txpower

    cc2420_to_dbm = {
    "31":"0",
    "27":"-1",
    "23":"-3",
    "19":"-5",
    "15":"-7",
    "7":"-15"
    }

    if not r_txpow:
        r_txpow = "all"

    if not r_txpow == "all" and int(r_txpow) > 5:
        r_txpow = cc2420_to_dbm[r_txpow]

    return r_txpow

def get_measurement_directory_path():
    directory_path = '/media/pi/Experiments'
    #if stick not present use pardir
    if not os.path.exists(directory_path):
        directory_path = os.path.join(os.pardir,'Measurements')
        if not os.path.exists(directory_path):
            sys.exit("Error: Measurement directory not found.")
    #if stick is present:use stick.
    else:
        directory_path = os.path.join(directory_path,'Measurements')
        if not os.path.exists(directory_path):
            sys.exit("Error: Measurement directory not found.")

    return directory_path

def print_ranges():
    rssi_min = 0
    rssi_max = -100
    lqi_min = 255
    lqi_max = 0
    dropped_min = 255
    dropped_max = 0
    relevant_files = get_all_files()

    for filepath in relevant_files:
        with open(filepath,'r') as experiment_file:
            for line in experiment_file:
                if line.startswith("{"):
                    measurement = eval(line)
                    if measurement["param"] == "RSSI":
                        rssi_read = int(measurement["value"])
                        if rssi_read > rssi_max and rssi_read != 0:
                            rssi_max = rssi_read
                        if rssi_read < rssi_min:
                            rssi_min = rssi_read

                    elif measurement["param"] =="LQI":
                        lqi_read = int(measurement["value"])
                        if lqi_read > lqi_max:
                            lqi_max = lqi_read
                        if lqi_read < lqi_min and lqi_read != 0:
                            lqi_min = lqi_read

                    elif measurement["param"] =="Dropped":
                        dropped_read = int(measurement["value"])
                        if dropped_read < 0:
                            dropped_read += 256
                        if dropped_read > dropped_max:
                            dropped_max = dropped_read
                        if dropped_read < dropped_min:
                            dropped_min = dropped_read

    print("Min rssi:{}".format(rssi_min))
    print("Max rssi:{}".format(rssi_max))
    print("Min lqi:{}".format(lqi_min))
    print("Max lqi:{}".format(lqi_max))
    print("Min dropped:{}".format(dropped_min))
    print("Max dropped:{}".format(dropped_max))

def get_information_by_path(file_path):
    information = {}
    information["link_data"] = {}

    split_file_path = file_path.split("/")
    #to make pathing work no matter where the directory is mounted use length as offset
    path_len = len(split_file_path)
    split_file_name = split_file_path[path_len-1].split(",")

    information["platform"] = split_file_path[path_len-3]
    information["orientation"] = split_file_path[path_len-2][-1:]
    information["number_of_nodes"] = split_file_name[0]
    information["channel"] = split_file_name[1]
    information["txpower"] = split_file_name[2]
    information["param"] = split_file_name[3]

    return information

def get_all_files():
    relevant_files = []
    d_path = get_measurement_directory_path()

    for root, dirs, files in os.walk(d_path, topdown=False):
        for name in files:
            if name.endswith("200"):
                relevant_files.append(os.path.join(root, name))

    return relevant_files

def get_files_by(filters):
    relevant_files = []
    d_path = get_measurement_directory_path()

    for root, dirs, files in os.walk(d_path, topdown=False):
        for name in files:
            if name.endswith("200"):
                info = get_information_by_path(os.path.join(root,name))

                if filters["platform"] and filters["platform"] != info["platform"]:
                    continue
                if filters["orientation"] and filters["orientation"] != info["orientation"]:
                    continue
                if filters["channel"] and filters["channel"] != info["channel"]:
                    continue
                if filters["txpower"] and filters["txpower"] != info["txpower"]:
                    continue
                if filters["param"] == "time" or filters["param"] == info["param"]:
                    relevant_files.append(os.path.join(root,name))

    return relevant_files

def create_graph(information):
    link_data         = information["link_data"]
    channel           = information["channel"]
    txpower           = information["txpower"]
    orientation       = information["orientation"]
    param             = information["param"]
    measurement_count = information["measurement_count"]
    temp              = information["temp"]
    hum               = information["hum"]
    time              = information["time"]
    platform          = information["platform"]

    od = OrderedDict(sorted(link_data.items()))
    data = od.values()
    labels = od.keys()

    if data:
        path = os.path.join(os.pardir,"Plots/{}/{}/{}".format(orientation,readable_channel(channel),readable_txpower(txpower)))
        if not os.path.exists(path):
            os.makedirs(path)
        filename = platform+","+readable_channel(channel)+","+readable_txpower(txpower)+","+readable_param(param)+"->"+orientation
        if os.path.isfile(os.path.join(path,filename+".png")):
            return

        plot.boxplot(data,vert=True,labels=labels)
        plot.ylabel(param)
        if param == "0":
            plot.ylim(-100,0)
        elif param == "1":
            plot.ylim(0,255)
        elif param == "2":
            plot.ylim(0,255)
        plot.xlabel("Links")
        plot.title("Average {} channel:{} txpower:{}dBm\nMeasurements:{} Temperature:{}C Humidity:{}% Duration:{}s".format(readable_param(param),
                                                                                                                                       readable_channel(channel),
                                                                                                                                       readable_txpower(txpower),
                                                                                                                                       measurement_count,
                                                                                                                                       temp,
                                                                                                                                       hum,
                                                                                                                                       time))

        plot.savefig(os.path.join(path,filename))
        plot.close()

def parse_file(file_path):
    information = get_information_by_path(file_path)

    information["measurement_count"] = 0
    information["temp"] = 0
    information["hum"] = 0
    information["time"] = 0

    #init dict (link : list)
    for i in range(2,int(information["number_of_nodes"])+1):
        information["link_data"]["1-"+str(i)] = []

    with open(file_path,'r') as experiment_file:
        for line in experiment_file:
            #evaluate measurement and add measured value to list
            if line.startswith("{"):
                information["measurement_count"] += 1
                measurement = eval(line)
                if information["param"] != "2" or (information["param"] == "2" and int(measurement["value"]) > 0):
                    if int(measurement["sender"]) == 1:
                        information["link_data"][measurement["sender"]+"-"+measurement["receiver"]].append(int(measurement["value"]))
                    elif int(measurement["receiver"]) == 1:
                        information["link_data"][measurement["receiver"]+"-"+measurement["sender"]].append(int(measurement["value"]))

                #conversion signed to unsigned
                else:
                    if int(measurement["sender"]) == 1 and int(measurement["value"]) < 0:
                        information["link_data"][measurement["sender"]+"-"+measurement["receiver"]].append(int(measurement["value"])+256)
                    elif int(measurement["receiver"]) == 1 and int(measurement["value"]) < 0:
                        information["link_data"][measurement["receiver"]+"-"+measurement["sender"]].append(int(measurement["value"])+256)

            elif line.startswith("Temp"):
                line.replace(" ", "")
                split_line = line.split("|")
                information["temp"] = split_line[0][-2:-1]
                information["hum"]  = split_line[1][-2:-1]

            else:
                #parse time in seconds
                hms = [3600,60,1]
                information["time"] = sum([a*b for a,b in zip(hms, map(int,line.split(':')))])

    if information["measurement_count"] >= 150:
        return information
    else:
        return None

if len(sys.argv) > 1 and sys.argv[1] == "all":
    relevant_files = get_all_files()

    for file_path in relevant_files:
        print(file_path)
        info = parse_file(file_path)
        if info:
            create_graph(info)


elif len(sys.argv) > 2:
    arguments = {}
    #default args
    arguments["param"] = "time"
    arguments["platform"] = None
    arguments["orientation"] = None
    arguments["channel"] = None
    arguments["txpower"] = None

    for arg in sys.argv:
        if "=" in arg:
            arguments[arg.split("=")[0]] = arg.split("=")[1]

    relevant_files = get_files_by(arguments)
    #TODO

elif len(sys.argv) > 1 and sys.argv[1] == "ranges":
    print_ranges()

print("Finished")
