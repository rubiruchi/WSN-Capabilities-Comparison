import sys
import os
import matplotlib.pyplot as plot
import numpy as np
from collections import OrderedDict

def print_stats_table(stats):
    print("\tRSSI\tLQI\tDRP\tTime")
    print("min\t" + str(stats["rssi_min"]) + "\t" + str(stats["lqi_min"]) + "\t" + str(stats["dropped_min"]) + "\t" + str(stats["time_min"]))
    print("max\t" + str(stats["rssi_max"]) + "\t" + str(stats["lqi_max"]) + "\t" + str(stats["dropped_max"]) + "\t" + str(stats["time_max"]))
    print("avg\t" + str(stats["rssi_avg"]) + "\t" + str(stats["lqi_avg"]) + "\t" + str(stats["dropped_avg"]) + "\t" + str(stats["time_avg"]))

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

def get_min_max_avg(relevant_files):
    rssi_values = []
    lqi_values = []
    dropped_values = []
    time_values = []

    for filepath in relevant_files:
        with open(filepath,'r') as experiment_file:
            for line in experiment_file:
                if line.startswith("{"):
                    measurement = eval(line)
                    if measurement["param"] == "RSSI" and measurement["value"] != "0":
                        rssi_values.append(int(measurement["value"]))

                    elif measurement["param"] =="LQI" and measurement["value"] != "0":
                        lqi_values.append(int(measurement["value"]))

                    elif measurement["param"] =="Dropped" and measurement["value"] != "0":
                        dropped_read = int(measurement["value"])
                        if dropped_read < 0:
                            dropped_read += 256
                        dropped_values.append(dropped_read)

                elif not line.startswith("Temp"):
                    #parse time in seconds
                    hms = [3600,60,1]
                    time_read = sum([a*b for a,b in zip(hms, map(int,line.split(':')))])
                    if time_read != 0:
                        time_values.append(time_read)

    #TODO standard deviation
    stats = {}
    stats["rssi_min"]    = min(rssi_values)
    stats["rssi_max"]    = max(rssi_values)
    stats["rssi_avg"]    = sum(rssi_values)/len(rssi_values)
    stats["lqi_min"]     =  min(lqi_values)
    stats["lqi_max"]     =  max(lqi_values)
    stats["lqi_avg"]     =  sum(lqi_values)/len(lqi_values)
    stats["dropped_min"] = min(dropped_values)
    stats["dropped_max"] = max(dropped_values)
    stats["dropped_avg"] = sum(dropped_values)/len(dropped_values)
    stats["time_min"]    = min(time_values)
    stats["time_max"]    = max(time_values)
    stats["time_avg"]    = sum(time_values)/len(time_values)

    return stats

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
                if filters["param"] and filters["param"] != info["param"]:
                    continue

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
        if platform == "openmote-2538":
            platform = "openmote"
        if platform == "srf06-cc26xx":
            platform = "sensortag"
        filename = platform+","+readable_channel(channel)+","+readable_txpower(txpower)+","+readable_param(param)
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
                information["temp"] = split_line[0][-3:-1]
                information["hum"]  = split_line[1][-3:-1]

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
    arguments["param"] = None
    arguments["platform"] = None
    arguments["orientation"] = None
    arguments["channel"] = None
    arguments["txpower"] = None

    for arg in sys.argv:
        if "=" in arg:
            arguments[arg.split("=")[0]] = arg.split("=")[1]

    relevant_files = get_files_by(arguments)

    print(len(relevant_files))

    stats = get_min_max_avg(relevant_files)

    print_stats_table(stats)

elif len(sys.argv) > 1 and sys.argv[1] == "ranges":
    print_ranges()

print("Finished")
