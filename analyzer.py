import sys
import os
import matplotlib.pyplot as plot
import numpy as np
from collections import OrderedDict

def convert_to_dbm():
    d_path = get_measurement_directory_path()
    for root, dirs, files in os.walk(d_path, topdown=False):
        for name in files:
            if ("z1" in root or "sky" in root) and name.endswith("200"):
                split_name = name.split(",")
                split_name[2] = readable_txpower(split_name[2])

                new_name = ",".join(split_name)
                print(name)
                print(new_name)
                os.rename(os.path.join(root,name),os.path.join(root,new_name))

def readable_channel(channel):
    r_chan = channel
    if not r_chan:
        r_chan = "all"

    return r_chan

def readable_param(param):
    if param == "0":
        r_param = "RSSI"
    elif param == "1":
        r_param = "LQI"
    elif param == "2":
        r_param = "dropped packages"
    else:
        r_param = param

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

def print_file_sizes(relevant_files):
    for filepath in relevant_files:
        print filepath+"\t", os.path.getsize(filepath)/1000

def print_stats_table(stats):
    params = ("RSSI","LQI","DRP","Time","Lines","Size")
    print "\t","\t".join(param for param in params)

    print "min\t" , "\t".join(str(val) for val in stats["min"])
    print "max\t" , "\t".join(str(val) for val in stats["max"])
    print "avg\t" , "\t".join(str(val) for val in stats["avg"])
    print "\nFailed:\t",str(stats["failed_transmissions"])

def get_min_max_avg(relevant_files):
    rssi_values = []
    lqi_values = []
    dropped_values = []
    time_values = []
    size_values = []
    lines_values = []
    failed_transmissions = 0

    for filepath in relevant_files:
        with open(filepath,'r') as experiment_file:
            line_counter = 0
            size_values.append(os.path.getsize(filepath)/1000)
            for line in experiment_file:
                if line.startswith("{"):
                    line_counter += 1
                    measurement = eval(line)
                    if measurement["sender"] == "1" or measurement["receiver"] == "1":
                        if measurement["param"] == "RSSI" and measurement["value"] != "0":
                            rssi_values.append(int(measurement["value"]))

                        elif measurement["param"] == "LQI" and measurement["value"] != "0":
                            lqi_values.append(int(measurement["value"]))

                        elif measurement["param"] == "Dropped" and measurement["value"] != "0":
                            dropped_read = int(measurement["value"])
                            if dropped_read < 0:
                                dropped_read += 256
                            dropped_values.append(dropped_read)

                        if measurement["value"] == "0":
                            failed_transmissions += 1

                elif not line.startswith("Temp"):
                    #parse time in seconds
                    hms = [3600,60,1]
                    time_read = sum([a*b for a,b in zip(hms, map(int,line.split(':')))])
                    if time_read != 0:
                        time_values.append(time_read)

            lines_values.append(line_counter)
    #TODO standard deviation
    stats = {}
    stats["min"] = [min(rssi_values),
                    min(lqi_values),
                    min(dropped_values),
                    min(time_values),
                    min(lines_values),
                    min(size_values)]
    stats["max"] = [max(rssi_values),
                    max(lqi_values),
                    max(dropped_values),
                    max(time_values),
                    max(lines_values),
                    max(size_values)]
    stats["avg"] = [sum(rssi_values)/len(rssi_values),
                    sum(lqi_values)/len(lqi_values),
                    sum(dropped_values)/len(dropped_values),
                    sum(time_values)/len(time_values),
                    sum(lines_values)/len(lines_values),
                    sum(size_values)/len(size_values)]
    stats["failed_transmissions"] = failed_transmissions

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

                relevant_files.append(os.path.join(root,name))

    return relevant_files

def create_boxplot(information):
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
        plot.grid()
        plot.title("Average {} channel:{} txpower:{}dBm\nMeasurements:{} Temperature:{}C Humidity:{}% Duration:{}s".format(readable_param(param),
                                                                                                                                       readable_channel(channel),
                                                                                                                                       readable_txpower(txpower),
                                                                                                                                       measurement_count,
                                                                                                                                       temp,
                                                                                                                                       hum,
                                                                                                                                       time))

        plot.savefig(os.path.join(path,filename))
        plot.close()

def create_lineplot(ordered_dict,info):
    # four subplots, unpack the axes array immediately
    f, pltlist = plot.subplots(1, 4, sharey=True)

    labels = ordered_dict.keys()
    data = ordered_dict.values()

    plot.suptitle("Platform:{}\nAverage {}".format(info["platform"],readable_param(info["parameter"])),fontsize=20)

    for i in range(0,4):
        my_labels = labels[i*4:i*4+4]
        my_data = data[i*4:i*4+4]
        chan_mean = []
        for tx_value in my_data:
            pltlist[i].plot(tx_value[0],tx_value[1],marker='o',linewidth=2.0)
            pltlist[i].legend(my_labels, loc='upper left')
            pltlist[i].grid()
            pltlist[i].set_xticks(data[0][0])
            pltlist[i].set_ylabel(readable_param(info["parameter"]))
            pltlist[i].set_xlabel("Transmission powers")
            chan_mean.append([np.mean(tx_value[1])])

        plot_mean =  [np.mean(chan_mean)]*len(tx_value[0])
        pltlist[i].plot(my_data[0][0],plot_mean, linestyle='--')

    f.set_size_inches(30, 10)
    plot.subplots_adjust(left=0.03, bottom=0.10, right=0.99, top=0.90,
                wspace=0.04, hspace=0.20)

    path = os.path.join(os.pardir,"Plots/Line")
    if not os.path.exists(path):
        os.makedirs(path)
    if info["platform"] == "openmote-2538":
        info["platform"] = "openmote"
    if info["platform"] == "srf06-cc26xx":
        info["platform"] = "sensortag"
    filename = info["platform"]+" "+readable_param(info["parameter"])

    plot.savefig(os.path.join(path,filename))

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

def parse_arguments():
    arguments = {}
    #default args
    arguments["platform"] = None
    arguments["orientation"] = None
    arguments["channel"] = None
    arguments["txpower"] = None
    arguments["sizes"] = None
    arguments["parameter"] = None

    for arg in sys.argv:
        if "=" in arg:
            arguments[arg.split("=")[0]] = arg.split("=")[1]

    return arguments



if len(sys.argv) > 1 and sys.argv[1] == "allboxplots":
    relevant_files = get_all_files()

    for file_path in relevant_files:
        print(file_path)
        info = parse_file(file_path)
        if info:
            create_boxplot(info)

elif len(sys.argv) > 1 and sys.argv[1] == "table":
    arguments = parse_arguments()
    relevant_files = get_files_by(arguments)
    print "Number of relevant files:",len(relevant_files)

    if not arguments["sizes"]:
        stats = get_min_max_avg(relevant_files)
        print_stats_table(stats)
    else:
        print_file_sizes(relevant_files)

elif len(sys.argv) > 1 and sys.argv[1] == "ranges":
    print_ranges()

elif len(sys.argv) > 1 and sys.argv[1] == "dbm":
    print("Converting sky/z1 files to dbm")
    convert_to_dbm()

elif len(sys.argv) > 1 and sys.argv[1] == "lineplot":
    arguments = parse_arguments()
    txpowers = {}
    txpowers["openmote-cc2538"] = [5,3,1,0,-1,-3,-5,-7,-15]
    txpowers["srf06-cc26xx"] = [5,3,1,0,-3,-15]
    txpowers["z1"] = [0,-1,-3,-5,-7,-15]
    txpowers["sky"] = [0,-1,-3,-5,-7,-15]

    indices = {}
    indices["0"] = 0
    indices["1"] = 1
    indices["2"] = 2
    indices["time"] = 3
    indices["lines"] = 4
    indices["size"] = 5

    channel_to_txval = OrderedDict()
    for channel in range(11,27):
        arguments["channel"] = str(channel)
        channel_to_txval[channel] = ([],[])
        for txpower in txpowers[arguments["platform"]]:
            channel_to_txval[channel][0].append(txpower)
            arguments["txpower"] = str(txpower)
            stats = get_min_max_avg(get_files_by(arguments))
            if arguments["parameter"] == "failed":
                channel_to_txval[channel][1].append(stats["failed_transmissions"])
            else:
                index = indices[arguments["parameter"]]
                channel_to_txval[channel][1].append(stats["avg"][index])


    create_lineplot(channel_to_txval,arguments)

print("Finished")
