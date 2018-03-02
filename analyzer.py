import sys
import os
import matplotlib.pyplot as plot
import numpy as np
from collections import OrderedDict
from datastorage import DataStorage
from math import pi

indices = OrderedDict()
indices["0"] = 0 #RSSI
indices["1"] = 1 #LQI
indices["lines"] = 2
indices["failed"] = 3
indices["packetlossrate"] = 4

txpowers = {}
txpowers["openmote-cc2538"] = [5,3,1,0,-1,-3,-5,-7,-15]
txpowers["srf06-cc26xx"] = [5,3,1,0,-3,-15]
txpowers["z1"] = [0,-1,-3,-5,-7,-15]
txpowers["sky"] = [0,-1,-3,-5,-7,-15]

platforms = txpowers.keys()
parameters = indices.keys()
functions = ["avg","dev","min","max"]

#basis is orientation 5
def equalize_node_ids(node_id,orientation):
    if int(node_id) <= 5:
        num = int(node_id)+(5-int(orientation))
        if num > 5:
            return (num%6)+2
        else:
            return num

    else:
        num = int(node_id)+(5-int(orientation))
        if num > 9:
            return (num%10)+6
        else:
            return num

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
    if not r_chan or r_chan == "None":
        r_chan = "all"

    return r_chan

def readable_param(parameter):
    if parameter == "0":
        r_param = "RSSI"
    elif parameter == "1":
        r_param = "LQI"
    elif parameter == "2":
        r_param = "dropped packages"
    else:
        r_param = parameter

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

    if not r_txpow or r_txpow == "None":
        r_txpow = "all"

    if not r_txpow == "all" and int(r_txpow) > 5:
        r_txpow = cc2420_to_dbm[r_txpow]

    return r_txpow

def readable_orientation(orientation):
    if not orientation or orientation == "None":
        orientation = "all"
    return orientation

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
        if num > 1:
            return int(num)
        else:
            return float(str(num)[:4])

def set_ylimits(parameter, function):
    avg = {"0":(-90,-30),
           "1":(50,118),
           "lines":(0,3600),
           "failed":(0,1400),
           "packetlossrate":(0,0.75)
          }

    dev = {"0":(0,15),
           "1":(0,12),
           "lines":(0,2000),
           "failed":(0,1400),
           "packetlossrate":(0,0.75)
          }

    if function and function == "dev":
        return dev[parameter]
    elif not function or function == "avg":
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
    parameters = ("RSSI","LQI","Lines","Failed","PLR")
    print "\t","\t".join(parameter for parameter in parameters)

    if stats:
        print "min\t" , "\t".join(str(truncate(val)) for val in stats["min"])
        print "max\t" , "\t".join(str(truncate(val)) for val in stats["max"])
        print "avg\t" , "\t".join(str(truncate(val)) for val in stats["avg"])
        print "dev\t" , "\t".join(str(truncate(val)) for val in stats["dev"])

def get_min_max_avg(relevant_files):
    rssi_values = []
    lqi_values = []
    lines_values = []
    failed_values = []
    plr_values = []

    for filepath in relevant_files:
        with open(filepath,'r') as experiment_file:
            line_counter = 0
            failed_transmissions = 0
            for line in experiment_file:
                if line.startswith("{"):

                    measurement = eval(line)
                    if (measurement["sender"] == "1" or measurement["receiver"] == "1") and (measurement["param"] == "RSSI" or measurement["param"] == "LQI"):
                        line_counter += 1
                        if measurement["param"] == "RSSI" and measurement["value"] != "0":
                            rssi_values.append(int(measurement["value"]))

                        elif measurement["param"] == "LQI" and measurement["value"] != "0":
                            lqi_values.append(int(measurement["value"]))

                        if measurement["value"] == "0":
                            failed_transmissions += 1

                # elif not line.startswith("Temp"):
                #     #parse time in seconds
                #     hms = [3600,60,1]
                #     time_read = sum([a*b for a,b in zip(hms, map(int,line.split(':')))])
                #     if time_read != 0:
                #         time_values.append(time_read)
            failed_values.append(failed_transmissions)
            lines_values.append(line_counter)
            plr_values.append(failed_transmissions/float(line_counter))

    if relevant_files:
        stats = {}
        if not rssi_values:
            rssi_values.append(None)
        if not lqi_values:
            lqi_values.append(None)

        stats["min"] = [min(rssi_values),
                        min(lqi_values),
                        min(lines_values),
                        min(failed_values),
                        min(plr_values)]
        stats["max"] = [max(rssi_values),
                        max(lqi_values),
                        max(lines_values),
                        max(failed_values),
                        max(plr_values)]
        stats["avg"] = [mean(rssi_values),
                        mean(lqi_values),
                        mean(lines_values),
                        mean(failed_values),
                        mean(plr_values)]
        stats["dev"] = [std(rssi_values),
                        std(lqi_values),
                        std(lines_values),
                        std(failed_values),
                        std(plr_values)]
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
            if name.endswith("0,200") or name.endswith("1,200"):
                relevant_files.append(os.path.join(root, name))

    return relevant_files

def get_files_by(filters):
    relevant_files = []
    d_path = get_measurement_directory_path()

    for root, dirs, files in os.walk(d_path, topdown=False):
        for name in files:
            if name.endswith("0,200") or name.endswith("1,200"):
                info = get_information_by_path(os.path.join(root,name))

                if filters["platform"] and filters["platform"] != info["platform"]:
                    continue
                if filters["orientation"] and filters["orientation"] != info["orientation"]:
                    continue
                if filters["channel"] and filters["channel"] != info["channel"]:
                    continue
                if filters["txpower"] and filters["txpower"] != info["txpower"]:
                    continue
                if filters["parameter"] and filters["parameter"] != info["parameter"] and (filters["parameter"] == "0" or filters["parameter"] == "1"):
                    continue

                if os.path.getsize(os.path.join(root,name))/1000 > 50:
                    relevant_files.append(os.path.join(root,name))

    return relevant_files

def draw_boxplot(link_data,information):
    channel = information["channel"]
    txpower = information["txpower"]
    orientation = information["orientation"]
    parameter = information["parameter"]
    measurement_count = information["measurement_count"]
    platform = information["platform"]
    packetlossrate = information["packetlossrate"]

    data = link_data.values()
    labels = link_data.keys()

    if data:
        path = os.path.join(os.pardir,"Plots/Box/{}/{}".format(readable_channel(channel),readable_txpower(txpower)))
        if not os.path.exists(path):
            os.makedirs(path)
        if platform == "openmote-2538":
            platform = "openmote"
        if platform == "srf06-cc26xx":
            platform = "sensortag"
        filename = platform+","+readable_channel(channel)+","+readable_txpower(txpower)+","+readable_param(parameter)

        plot.boxplot(data,vert=True,labels=labels)
        plot.ylabel(parameter)
        if parameter == "0":
            plot.ylim(-95,-20)
        elif parameter == "1":
            plot.ylim(50,118)
        plot.xlabel("Links")
        plot.grid()
        plot.title("Average {} channel:{} txpower:{}dBm\nMeasurements:{} Packetlossrate:{}%".format(readable_param(parameter),
                                                                                                    readable_channel(channel),
                                                                                                    readable_txpower(txpower),
                                                                                                    measurement_count,
                                                                                                    packetlossrate))

        plot.savefig(os.path.join(path,filename))
        plot.close()

def draw_lineplot(storage):
    global platforms
    global parameters
    global functions
    global txpowers
    functions.remove("dev")

    for platform in platforms:
        for function in functions:
            for parameter in parameters: #plotting one figure
                print "plotting", platform, parameter
                f, pltlist = plot.subplots(1, 4, sharey=True)
                if function == "avg":
                    plot.suptitle("Platform:{}\n Average {} with standard deviation".format(platform,readable_param(parameter)),fontsize=20)
                else:
                    plot.suptitle("Platform:{}\n {} {}".format(platform,function,readable_param(parameter)),fontsize=20)
                labels = range(11,27)

                for i in range(0,4): #plotting the four graphs making up one figure
                    four_labels = labels[i*4:i*4+4]
                    curr_channels = storage.get(function, platform)[i*4:i*4+4]
                    dev_channels = storage.get("dev", platform)[i*4:i*4+4]
                    chan_mean = []
                    for j in range(0,4): #plotting the individual lines in a graph
                        txpwrs = curr_channels[j][parameter][0]
                        values = curr_channels[j][parameter][1]
                        error = dev_channels[j][parameter][1]

                        if  function != "avg":
                            pltlist[i].plot(txpwrs,values,marker='o',linewidth=3.0)
                        else:
                            pltlist[i].errorbar(txpwrs,values,yerr=error,marker='o',linewidth=3.0)

                        pltlist[i].legend(four_labels, loc='upper left')
                        pltlist[i].grid()
                        pltlist[i].set_xticks([8]+txpwrs+[-18])
                        pltlist[i].set_ylabel(readable_param(parameter))
                        pltlist[i].set_ylim(*set_ylimits(parameter,"avg"))
                        pltlist[i].set_xlabel("Transmission powers")
                        chan_mean.append(mean(values))

                    plot_mean =  [mean(chan_mean)]*len(txpowers[platform])
                    pltlist[i].plot(txpowers[platform],plot_mean, linestyle='--')

                f.set_size_inches(30, 10)
                plot.subplots_adjust(left=0.03, bottom=0.10, right=0.99, top=0.90,
                            wspace=0.04, hspace=0.20)

                platform_r = platform

                path = os.path.join(os.pardir,"Plots/Line")
                if not os.path.exists(path):
                    os.makedirs(path)

                if platform == "openmote-2538":
                    platform_r = "openmote"
                if platform == "srf06-cc26xx":
                    platform_r = "sensortag"

                filename = function+" "+readable_param(parameter)+" "+platform_r

                plot.savefig(os.path.join(path,filename))
                plot.close()

def draw_radarchart(link_data,information):
    # Plots a radar chart.

    channel = information["channel"]
    txpower = information["txpower"]
    orientation = information["orientation"]
    parameter = information["parameter"]
    measurement_count = information["measurement_count"]
    platform = information["platform"]
    packetlossrate = information["packetlossrate"]

    # Set data
    xlabels = link_data.keys()
    values = []
    for measurements in link_data.values():
        values.append(mean(measurements))

    N = len(xlabels)

    x_as = [n / float(N) * 2 * pi for n in range(N)]

    # Because our chart will be circular we need to append a copy of the first
    # value of each list at the end of each list with data
    values += values[:1]
    x_as += x_as[:1]


    # Set color of axes
    plot.rc('axes', linewidth=0.5, edgecolor="#888888")


    # Create polar plot
    ax = plot.subplot(111, polar=True)


    # Set clockwise rotation. That is:
    ax.set_theta_offset(pi / 2)
    ax.set_theta_direction(-1)


    # Set position of y-labels
    ax.set_rlabel_position(0)


    # Set color and linestyle of grid
    ax.xaxis.grid(True, color="#888888", linestyle='solid', linewidth=0.5)
    ax.yaxis.grid(True, color="#888888", linestyle='solid', linewidth=0.5)


    # Set number of radial axes and remove labels
    plot.xticks(x_as[:-1], xlabels)

    # Set yticks
    plot.yticks([-30, -40, -50, -60, -70, -80, -90], ["-30", "-40", "-50", "-60", "-70", "-80", "-90"])

    # Plot data
    ax.plot(x_as, values, linewidth=0, linestyle='solid', zorder=3)

    # Fill area
    ax.fill(x_as, values, 'b', alpha=0.3)


    # Set axes limits
    plot.ylim(-30, -100)


    # Draw ytick labels to make sure they fit properly
    for i in range(N):
        angle_rad = i / float(N) * 2 * pi

        if angle_rad == 0:
            ha, distance_ax = "center", 10
        elif 0 < angle_rad < pi:
            ha, distance_ax = "left", 1
        elif angle_rad == pi:
            ha, distance_ax = "center", 1
        else:
            ha, distance_ax = "right", 1

        ax.text(angle_rad, 100 + distance_ax, xlabels[i], size=10, horizontalalignment=ha, verticalalignment="center")

        path = os.path.join(os.pardir,"Plots/Radar/{}/{}".format(readable_channel(channel),readable_txpower(txpower)))
        if not os.path.exists(path):
            os.makedirs(path)
        if platform == "openmote-2538":
            platform = "openmote"
        if platform == "srf06-cc26xx":
            platform = "sensortag"
        filename = platform+","+readable_channel(channel)+","+readable_txpower(txpower)+","+readable_param(parameter)

        #plot.ylabel(parameter)
        plot.xlabel("Links")
        #plot.figure(figsize=(10,10))

    plot.title("Average {}\nChannel: {}  txpower: {}dBm\n".format(readable_param(parameter),
                                                                                                readable_channel(channel),
                                                                                                readable_txpower(txpower)),
                                                                                                size='large',
                                                                                                position=(0, 1),
                                                                                                horizontalalignment='center',
                                                                                                verticalalignment='center')

    plot.savefig(os.path.join(path,filename))
    plot.close()

def parse_file_by_link(file_path):
    information = get_information_by_path(file_path)

    information["measurement_count"] = 0
    information["temp"] = 0
    information["hum"] = 0

    #init dict (link : list)
    information["link_data"] = OrderedDict()
    for i in range(2,int(information["number_of_nodes"])+1):
        information["link_data"]["1-"+str(i)] = []

    with open(file_path,'r') as experiment_file:
        for line in experiment_file:
            #evaluate measurement and add measured value to list
            if line.startswith("{"):
                information["measurement_count"] += 1
                measurement = eval(line)
                if int(measurement["value"]) > 0:
                    if int(measurement["sender"]) == 1:
                        information["link_data"][measurement["sender"]+"-"+measurement["receiver"]].append(int(measurement["value"]))
                    elif int(measurement["receiver"]) == 1:
                        information["link_data"][measurement["receiver"]+"-"+measurement["sender"]].append(int(measurement["value"]))

            elif line.startswith("Temp"):
                line.replace(" ", "")
                split_line = line.split("|")
                information["temp"] = split_line[0][-3:-1]
                information["hum"]  = split_line[1][-3:-1]


    if information["measurement_count"] >= 250:
        return information
    else:
        return None

def parse_files_by_link(relevant_files,arguments):
    information = arguments
    if information["platform"] == "sky" or information["platform"] == "srf06-cc26xx":
        information["number_of_nodes"] = "9"
    else:
        information["number_of_nodes"] = "5"

    information["measurement_count"] = 0
    information["temp"] = None
    information["hum"] = None
    information["packetlossrate"] = None

    failed_values = 0
    link_data = OrderedDict()
    #init dict (link : list)
    if information["number_of_nodes"] == "5":
        link_data["1-2"] = []
        link_data["1-3"] = []
        link_data["1-4"] = []
        link_data["1-5"] = []
    elif information["number_of_nodes"] == "9" :
        link_data["1-2"] = []
        link_data["1-6"] = []
        link_data["1-3"] = []
        link_data["1-7"] = []
        link_data["1-4"] = []
        link_data["1-8"] = []
        link_data["1-5"] = []
        link_data["1-9"] = []

    for file_path in relevant_files:
        with open(file_path,'r') as experiment_file:
            orientation = int(get_information_by_path(file_path)["orientation"])
            for line in experiment_file:
                #evaluate measurement and add measured value to list
                if line.startswith("{"):
                    measurement = eval(line)
                    if  measurement["value"] != "0":
                        information["measurement_count"] += 1
                        #only links with sink node
                        if measurement["sender"] == "1":
                            receiver = equalize_node_ids(measurement["receiver"],orientation)
                            link_data[measurement["sender"]+"-"+str(receiver)].append(int(measurement["value"]))
                        elif measurement["receiver"] == "1":
                            sender = equalize_node_ids(measurement["sender"],orientation)
                            link_data[measurement["receiver"]+"-"+str(sender)].append(int(measurement["value"]))
                    else:
                        failed_values += 1

    if information["measurement_count"]:
        information["packetlossrate"] = int((failed_values/float(information["measurement_count"]))*100)
    draw_boxplot(link_data,information)
    draw_radarchart(link_data,information)

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



if len(sys.argv) > 1 and sys.argv[1] == "linkplots":
    arguments = parse_arguments()

    relevant_parameters = ["0","1","packetlossrate"] #TODO finish
    for platform in platforms:
        arguments["platform"] = platform

        for channel in map(str,range(11,27))+[None]:
            arguments["channel"] = channel

            for txpower in map(str,txpowers[arguments["platform"]])+[None]:                                                 #connecting a list of txpowers
                arguments["txpower"] = txpower

                for parameter in range(2):
                    arguments["parameter"] = str(parameter)
                    relevant_files = get_files_by(arguments)
                    print platform,channel,txpower,parameter,len(relevant_files)
                    parse_files_by_link(relevant_files,arguments)




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
    storage = DataStorage()                                                                           # an ordered dict {"channel":[([txpowers],[values])]}

    for platform in platforms:
        arguments["platform"] = platform

        for channel in range(11,27):
            arguments["channel"] = str(channel)

            for txpower in txpowers[arguments["platform"]]:                                                 #connecting a list of txpowers
                arguments["txpower"] = str(txpower)
                print arguments["platform"],arguments["channel"],arguments["txpower"]

                for parameter in indices.keys():
                    arguments["parameter"] = parameter
                    index = indices[parameter]
                    stats = get_min_max_avg(get_files_by(arguments))
                    if stats:
                        # if parameter == "packetlossrate":
                        #     arguments["function"] = "avg"
                        #     storage.store(arguments, stats["packetlossrate"],txpower)
                        # else:
                            for function in functions:
                                arguments["function"] = function
                                if not stats[function][index] is None:
                                    storage.store(arguments, stats[function][index], txpower)

    draw_lineplot(storage)

elif len(sys.argv) > 1 and sys.argv[1] == "id":
    print equalize_node_ids(sys.argv[2],sys.argv[3])

print("Finished")
