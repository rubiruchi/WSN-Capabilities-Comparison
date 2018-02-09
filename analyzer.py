import sys
import os
import matplotlib.pyplot as plot
import numpy as np
from collections import OrderedDict

indices = OrderedDict()
indices["0"] = 0 #RSSI
indices["1"] = 1 #LQI
indices["2"] = 2 #DROPPED
indices["time"] = 3
indices["lines"] = 4
indices["size"] = 5
indices["failed"] = 6
indices["packetlossrate"] = 7

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

def mean(array):
    mean = None
    array = [x for x in array if x is not None]
    if array:
        mean = sum(array)/float(len(array))

    return mean

def std(array):
    deviation = None
    array = [x for x in array if x is not None]
    if array:
        deviation = np.std(array)

    return deviation

def truncate(num):
    if num:
        return int(num)

def set_ylimits(parameter, function):
    avg = {"0":(-85,-38),
           "1":(80,110),
           "2":(0,160),
           "lines":(0,2000),
           "failed":(0,1400),
           "size":(None,None),
           "time":(None,None),
           "packetlossrate":(0,0.45)
          }

    dev = {"0":(0,15),
           "1":(0,12),
           "2":(20,110),
           "lines":(0,2000),
           "failed":(0,1400),
           "size":(None,None),
           "time":(None,None),
           "packetlossrate":(0,0.45)
          }

    if function and function == "deviation":
        return dev[parameter]
    elif not function or function == "average":
        return avg[parameter]

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
    params = ("RSSI","LQI","DRP","Time","Lines","Size","Failed")
    print "\t","\t".join(param for param in params)

    if stats:
        print "min\t" , "\t".join(str(truncate(val)) for val in stats["min"])
        print "max\t" , "\t".join(str(truncate(val)) for val in stats["max"])
        print "avg\t" , "\t".join(str(truncate(val)) for val in stats["avg"])
        print "dev\t" , "\t".join(str(truncate(val)) for val in stats["dev"])

def get_min_max_avg(relevant_files):
    rssi_values = []
    lqi_values = []
    dropped_values = []
    time_values = []
    size_values = []
    lines_values = []
    failed_values = []

    for filepath in relevant_files:
        with open(filepath,'r') as experiment_file:
            line_counter = 0
            size_values.append(os.path.getsize(filepath)/1000)
            failed_transmissions = 0
            for line in experiment_file:
                if line.startswith("{"):
                    measurement = eval(line)
                    if measurement["sender"] == "1" or measurement["receiver"] == "1":
                        line_counter += 1
                        if measurement["param"] == "RSSI" and measurement["value"] != "0":
                            rssi_values.append(int(measurement["value"]))

                        elif measurement["param"] == "LQI" and measurement["value"] != "0":
                            lqi_values.append(int(measurement["value"]))

                        elif measurement["param"] == "Dropped":
                            dropped_read = int(measurement["value"])
                            if dropped_read < 0:
                                dropped_read += 256
                            dropped_values.append(dropped_read)

                        if measurement["value"] == "0" and not measurement["param"] == "Dropped":
                            failed_transmissions += 1

                elif not line.startswith("Temp"):
                    #parse time in seconds
                    hms = [3600,60,1]
                    time_read = sum([a*b for a,b in zip(hms, map(int,line.split(':')))])
                    if time_read != 0:
                        time_values.append(time_read)
            failed_values.append(failed_transmissions)
            lines_values.append(line_counter)


    if relevant_files:
        stats = {}
        if not rssi_values:
            rssi_values.append(None)
        if not lqi_values:
            lqi_values.append(None)
        if not dropped_values:
            dropped_values.append(None)

        stats["min"] = [min(rssi_values),
                        min(lqi_values),
                        min(dropped_values),
                        min(time_values),
                        min(lines_values),
                        min(size_values),
                        min(failed_values)]
        stats["max"] = [max(rssi_values),
                        max(lqi_values),
                        max(dropped_values),
                        max(time_values),
                        max(lines_values),
                        max(size_values),
                        max(failed_values)]
        stats["avg"] = [mean(rssi_values),
                        mean(lqi_values),
                        mean(dropped_values),
                        mean(time_values),
                        mean(lines_values),
                        mean(size_values),
                        mean(failed_values)]
        stats["dev"] = [std(rssi_values),
                        std(lqi_values),
                        std(dropped_values),
                        std(time_values),
                        std(lines_values),
                        std(size_values),
                        std(failed_values)]
        stats["packetlossrate"] = stats["avg"][indices["failed"]]/float(stats["avg"][indices["lines"]])

    else:
        stats = None

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
    information["parameter"] = split_file_name[3]

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
                if filters["parameter"] and filters["parameter"] != info["parameter"] and (filters["parameter"] == "0" or filters["parameter"] == "1" or filters["parameter"] == "2"):
                    continue

                if os.path.getsize(os.path.join(root,name))/1000 > 50:
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
    global indices

    labels = ordered_dict.keys()
    tx_val_list_list = ordered_dict.values()          #list consisting of lists consisting of tuples.

    for parameter in indices.keys():
        # four subplots, unpack the axes array immediately
        f, pltlist = plot.subplots(1, 4, sharey=True)

        if not info["function"]:
            info["function"] = "average"
        plot.suptitle("Platform:{}\n{} {}".format(info["platform"],info["function"],readable_param(parameter)),fontsize=20)

        for i in range(0,4):
            my_labels = labels[i*4:i*4+4]             #reduce list of channels to the 4 relevant for the plot
            my_data = tx_val_list_list[i*4:i*4+4]     #reduce list of tx_value lists to the 4 correstponding to the channels
            chan_mean = []
            for tx_value_list in my_data:
                tx_value = tx_value_list[indices[parameter]]
                pltlist[i].plot(tx_value[0],tx_value[1],marker='o',linewidth=2.0)
                pltlist[i].legend(my_labels, loc='upper left')
                pltlist[i].grid()
                pltlist[i].set_xticks(tx_value[0])
                pltlist[i].set_ylabel(readable_param(parameter))
                pltlist[i].set_ylim(*set_ylimits(parameter,info["function"]))
                pltlist[i].set_xlabel("Transmission powers")
                chan_mean.append(mean(tx_value[1]))

            plot_mean =  [mean(chan_mean)]*len(my_data[0][0][0])
            pltlist[i].plot(my_data[0][0][0],plot_mean, linestyle='--')

        f.set_size_inches(30, 10)
        plot.subplots_adjust(left=0.03, bottom=0.10, right=0.99, top=0.90,
                    wspace=0.04, hspace=0.20)


        path = os.path.join(os.pardir,"Plots/Line/{}".format(info["function"]))
        if not os.path.exists(path):
            os.makedirs(path)
        if info["platform"] == "openmote-2538":
            info["platform"] = "openmote"
        if info["platform"] == "srf06-cc26xx":
            info["platform"] = "sensortag"
        filename = readable_param(parameter)+" "+info["platform"]

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

def parse_arguments():
    arguments = {}
    #default args
    arguments["platform"] = None
    arguments["orientation"] = None
    arguments["channel"] = None
    arguments["txpower"] = None
    arguments["parameter"] = None
    arguments["function"] = None

    for arg in sys.argv:
        if "=" in arg:
            arguments[arg.split("=")[0]] = arg.split("=")[1]

    return arguments



if len(sys.argv) > 1 and sys.argv[1] == "boxplots":
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
    stats = get_min_max_avg(relevant_files)
    print_stats_table(stats)


elif len(sys.argv) > 1 and sys.argv[1] == "ranges":
    print_ranges()

elif len(sys.argv) > 1 and sys.argv[1] == "dbm":
    print("Converting sky/z1 files to dbm")
    convert_to_dbm()

elif len(sys.argv) > 1 and sys.argv[1] == "lineplots":
    arguments = parse_arguments()

    txpowers = {}
    txpowers["openmote-cc2538"] = [5,3,1,0,-1,-3,-5,-7,-15]
    txpowers["srf06-cc26xx"] = [5,3,1,0,-3,-15]
    txpowers["z1"] = [0,-1,-3,-5,-7,-15]
    txpowers["sky"] = [0,-1,-3,-5,-7,-15]

    platforms = []
    if not arguments["platform"]:
        platforms = txpowers.keys()
    else:
        platforms.append(arguments["platform"])

    parameters = []
    if not arguments["parameter"]:
        parameters = indices.keys()
    else:
        parameters.append(arguments["parameter"])

    channel_to_txval = OrderedDict()                                                                            # an ordered dict {"channel":[([txpowers],[values])]}

    for platform in platforms:
        arguments["platform"] = platform

        for channel in range(11,27):
            arguments["channel"] = str(channel)
            channel_to_txval[arguments["channel"]] = []
            for i in range(len(indices.keys())):
                channel_to_txval[arguments["channel"]].append((txpowers[arguments["platform"]],[]))        # mapping channels to lists containing tuples for each parameter

            for txpower in txpowers[arguments["platform"]]:                                                 #connecting a list of txpowers
                arguments["txpower"] = str(txpower)
                print arguments["platform"],arguments["channel"],arguments["txpower"]
                stats = get_min_max_avg(get_files_by(arguments))

                for parameter in indices.keys():
                    index = indices[parameter]
                    #print "parameter", parameter
                    #print "index", index
                    if stats:
                        if parameter == "packetlossrate":
                            channel_to_txval[arguments["channel"]][index][1].append(stats["packetlossrate"])
                        else:
                            if arguments["function"] and arguments["function"]  == "deviation":
                                channel_to_txval[arguments["channel"]][index][1].append(stats["dev"][index])
                            else:
                                #print "appending", stats["avg"][index]
                                channel_to_txval[arguments["channel"]][index][1].append(stats["avg"][index])

                        #print channel_to_txval[arguments["channel"]][index]
                        #print channel_to_txval[arguments["channel"]]

                    else:
                        #print channel_to_txval[arguments["channel"]]
                        channel_to_txval[arguments["channel"]][index][1].append(None)


        create_lineplot(channel_to_txval,arguments)

print("Finished")
