import sys
import os
import matplotlib.pyplot as plot
import numpy as np
from collections import OrderedDict
from datastorage import DataStorage
from math import pi
from copy import deepcopy
import platform as host_platform

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
    if not num is None:
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
        print(filepath+"\t", os.path.getsize(filepath)/1000)

def print_stats_table(stats):
    parameters = ("RSSI","LQI","Lines","Failed","PLR")
    print("\t","\t".join(parameter for parameter in parameters))

    if stats:
        print("min\t" , "\t".join(str(truncate(val)) for val in stats["min"]))
        print("max\t" , "\t".join(str(truncate(val)) for val in stats["max"]))
        print("avg\t" , "\t".join(str(truncate(val)) for val in stats["avg"]))
        print("dev\t" , "\t".join(str(truncate(val)) for val in stats["dev"]))

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

    if host_platform.system() == "Linux":
        split_file_path = file_path.split("/")
    elif host_platform.system() == "Windows":
        split_file_path = file_path.split("\\")

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
    #init dict (link : list)
    link_data = OrderedDict()
    link_data["1-2"] = []
    link_data["1-6"] = []
    link_data["1-3"] = []
    link_data["1-7"] = []
    link_data["1-4"] = []
    link_data["1-8"] = []
    link_data["1-5"] = []
    link_data["1-9"] = []

    link_pdr = OrderedDict()
    link_pdr["1-2"] = [0,0,0] # pdr, failed , total
    link_pdr["1-6"] = [0,0,0]
    link_pdr["1-3"] = [0,0,0]
    link_pdr["1-7"] = [0,0,0]
    link_pdr["1-4"] = [0,0,0]
    link_pdr["1-8"] = [0,0,0]
    link_pdr["1-5"] = [0,0,0]
    link_pdr["1-9"] = [0,0,0]

    plat_to_ld = {}
    for platform in platforms:
        plat_to_ld[platform] = deepcopy(link_data)

    plat_to_lpdr = {}
    for platform in platforms:
        plat_to_lpdr[platform] = deepcopy(link_pdr)

    for file_path in relevant_files:
        with open(file_path,'r') as experiment_file:

            information = get_information_by_path(file_path)
            platform = information["platform"]
            orientation = int(information["orientation"])

            information["measurement_count"] = 0
            information["packetlossrate"] = []
            failed_values = 0

            for line in experiment_file:
                #evaluate measurement and add measured value to list
                if line.startswith("{"):
                    measurement = eval(line)
                    if  measurement["value"] != "0":
                        information["measurement_count"] += 1
                        #only links with sink node
                        if measurement["sender"] == "1":
                            receiver = equalize_node_ids(measurement["receiver"],orientation)
                            #plat_to_ld[platform][measurement["sender"]+"-"+str(receiver)].append(int(measurement["value"]))
                            plat_to_lpdr[platform][measurement["sender"]+"-"+str(receiver)][2] +=1
                        elif measurement["receiver"] == "1":
                            sender = equalize_node_ids(measurement["sender"],orientation)
                            #plat_to_ld[platform][measurement["receiver"]+"-"+str(sender)].append(int(measurement["value"]))
                            plat_to_lpdr[platform][measurement["receiver"]+"-"+str(sender)][2] +=1
                    else:
                        if measurement["sender"] == "1":
                            receiver = equalize_node_ids(measurement["receiver"],orientation)
                            plat_to_lpdr[platform][measurement["sender"]+"-"+str(receiver)][1] +=1
                        elif measurement["receiver"] == "1":
                            sender = equalize_node_ids(measurement["sender"],orientation)
                            plat_to_lpdr[platform][measurement["receiver"]+"-"+str(sender)][1] +=1

    #if information["measurement_count"]:
        #information["packetlossrate"].append(truncate(failed_values/float(information["measurement_count"])))
    for platform in platforms:
        for link in link_pdr.keys():
            if plat_to_lpdr[platform][link][2] != 0:
                plat_to_lpdr[platform][link][0] = 1-truncate(plat_to_lpdr[platform][link][1]/float(plat_to_lpdr[platform][link][2]))
                if plat_to_lpdr[platform][link][0] == 0:
                    plat_to_lpdr[platform][link][0] = 1

    #draw_boxplot(link_data,information)
    information["channel"] = arguments["channel"]
    information["txpower"] = arguments["txpower"]
    draw_radarchart(plat_to_lpdr,information)

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
                print("plotting", platform, parameter)
                f, pltlist = plot.subplots(2, 2, sharey=True)
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
                            pltlist[int(i/2)][i%2].plot(txpwrs,values,marker='o',linewidth=3.0)
                        else:
                            pltlist[int(i/2)][i%2].errorbar(txpwrs,values,yerr=error,marker='o',linewidth=3.0)

                        pltlist[int(i/2)][i%2].legend(four_labels, loc='upper left')
                        pltlist[int(i/2)][i%2].grid()
                        pltlist[int(i/2)][i%2].set_xticks([8]+txpwrs+[-18])
                        pltlist[int(i/2)][i%2].set_ylabel(readable_param(parameter))
                        pltlist[int(i/2)][i%2].set_ylim(*set_ylimits(parameter,"avg"))
                        chan_mean.append(mean(values))

                    plot_mean =  [mean(chan_mean)]*len(txpowers[platform])
                    pltlist[int(i/2)][i%2].plot(txpowers[platform],plot_mean, linestyle='--')

                f.set_size_inches(17, 15)
                plot.subplots_adjust(left=0.05, bottom=0.10, right=0.99, top=0.90,
                            wspace=0.04, hspace=0.20)

                platform_r = platform

                path = os.path.join(os.pardir,"Plots/Line")
                if not os.path.exists(path):
                    os.makedirs(path)

                if platform == "openmote-2538":
                    platform_r = "openmote"
                if platform == "srf06-cc26xx":
                    platform_r = "sensortag"

                filename = function+"_"+readable_param(parameter)+"_"+platform_r

                #plot.setp([a.get_xticklabels() for a in pltlist[0, :]], visible=False)
                #plot.setp([a.get_yticklabels() for a in pltlist[:, 1]], visible=False)
                pltlist[1][0].set_xlabel("Transmission powers (dBm)")
                pltlist[1][1].set_xlabel("Transmission powers (dBm)")

                plot.savefig(os.path.join(path,filename))
                plot.close()

def draw_lineplot_reduced(storage):
    global platforms
    global parameters
    global functions
    global txpowers
    functions.remove("dev")

    for function in functions:
        for parameter in parameters: #plotting one figure
            print("plotting", platform, parameter)
            f, pltlist = plot.subplots(2, 2, sharey=True)
            if function == "avg":
                plot.suptitle("Average {} with standard deviation".format(readable_param(parameter)),fontsize=20)
            else:
                plot.suptitle("{} {}".format(function,readable_param(parameter)),fontsize=20)
            labels = ["12","18","25","26"]

            i = 0
            for platform in platforms: #plotting the four graphs making up one figure
                curr_channels = [storage.get(function, platform,x) for x in labels]
                dev_channels = [storage.get("dev", platform,x) for x in labels]
                chan_mean = []
                for j in range(0,4): #plotting the individual lines in a graph
                    txpwrs = curr_channels[j][parameter][0]
                    values = curr_channels[j][parameter][1]
                    error = dev_channels[j][parameter][1]

                    if  function != "avg":
                        pltlist[int(i/2)][i%2].plot(txpwrs,values,marker='o',linewidth=3.0)
                    else:
                        pltlist[int(i/2)][i%2].errorbar(txpwrs,values,yerr=error,marker='o',linewidth=3.0)

                    pltlist[int(i/2)][i%2].legend(four_labels, loc='upper left')
                    pltlist[int(i/2)][i%2].grid()
                    pltlist[int(i/2)][i%2].set_xticks([8]+txpwrs+[-18])
                    pltlist[int(i/2)][i%2].set_ylabel(readable_param(parameter))
                    pltlist[int(i/2)][i%2].set_ylim(*set_ylimits(parameter,"avg"))
                    pltlist[int(i/2)][i%2].set_title(platform)
                    chan_mean.append(mean(values))

                plot_mean =  [mean(chan_mean)]*len(txpowers[platform])
                pltlist[int(i/2)][i%2].plot(txpowers[platform],plot_mean, linestyle='--')
                i += 1

            f.set_size_inches(17, 15)
            plot.subplots_adjust(left=0.05, bottom=0.10, right=0.99, top=0.90,
                        wspace=0.04, hspace=0.20)

            platform_r = platform

            path = os.path.join(os.pardir,"Plots/Line_r")
            if not os.path.exists(path):
                os.makedirs(path)

            if platform == "openmote-2538":
                platform_r = "openmote"
            if platform == "srf06-cc26xx":
                platform_r = "sensortag"

            filename = function+"_"+readable_param(parameter)

            #plot.setp([a.get_xticklabels() for a in pltlist[0, :]], visible=False)
            #plot.setp([a.get_yticklabels() for a in pltlist[:, 1]], visible=False)
            pltlist[1][0].set_xlabel("Transmission powers (dBm)")
            pltlist[1][1].set_xlabel("Transmission powers (dBm)")

            plot.savefig(os.path.join(path,filename))
            plot.close()

def draw_radarchart(plat_to_ld,information):
    # Plots a radar chart.

    channel = information["channel"]
    print("plotting", channel)
    txpower = information["txpower"]
    parameter = information["parameter"]

    for plt in plat_to_ld.keys():
        for link in plat_to_ld[plt].keys():
            #if not plat_to_ld[plt][link]:
            if not plat_to_ld[plt][link][0]:
                #print plat_to_ld[plt]
                del plat_to_ld[plt][link]
            if not plat_to_ld[plt]:
                del plat_to_ld[plt]

    xlabels0 = ["1-2","1-6","1-3","1-7","1-4","1-8","1-5","1-9"]
    xlabels1 = ["1-2","1-3","1-4","1-5"]
    plot0_platforms = ["sky","srf06-cc26xx"]
    plot0_platforms = filter(lambda x: x in plat_to_ld.keys(), plot0_platforms)
    plot1_platforms = ["openmote-cc2538","z1"]
    plot1_platforms = filter(lambda x: x in plat_to_ld.keys(), plot1_platforms)


    N0 = len(xlabels0)
    x_as0 = [n / float(N0) * 2 * pi for n in range(N0)]
    x_as0 += x_as0[:1]
    # Set color of axes
    plot.rc('axes', linewidth=0.5, edgecolor="#888888")
    # Create polar plots
    ax0 = plot.subplot(121, polar=True)
    # Set clockwise rotation. That is:
    ax0.set_theta_offset(pi / 2)
    ax0.set_theta_direction(-1)
    # Set position of y-labels
    ax0.set_rlabel_position(22)
    # Set color and linestyle of grid
    ax0.xaxis.grid(True, color="#888888", linestyle='solid', linewidth=0.5)
    ax0.yaxis.grid(True, color="#888888", linestyle='solid', linewidth=0.5)
    # Set number of radial axes and set labels
    plot.xticks(x_as0[:-1], xlabels0)
    # Set yticks
    #plot.yticks([-30, -40, -50, -60, -70, -80, -90], ["-30", "-40", "-50", "-60", "-70", "-80", "-90"])
    plot.yticks([1,0.875,0.75,0.625,0.5,0.375,0.25,0.125,0], ["1","0.875","0.75","0.625","0.5","0.375","0.25","0.125","0"])
    ax0.tick_params(axis='y', which='major', labelsize=9)

    platform_to_color = dict(zip(platforms,['b','r','g','m']))
    for platform in plot0_platforms:
        #Set values
        values = []
        link_data = plat_to_ld[platform]
        for measurements in link_data.values():
            #values.append(mean(measurements))
            values.append(measurements[0])

        print(platform,xlabels0)
        print(platform,values)

        values += values[:1]
        #values = map(lambda x :  x if x is not None else  1, values)

        if values:
            plot.plot(x_as0, values, platform_to_color[platform], linewidth=1, linestyle='solid', zorder=3)
            plot.fill(x_as0, values, platform_to_color[platform], alpha=0.25)
            legend = ax0.legend(plot0_platforms, loc=(0.2, -0.3),labelspacing=0.1, fontsize='small')


    # Set axes limits
    #plot.ylim(-30, -100)
    plot.ylim(0, 1)
    plot.xlabel("Links")

    # # Draw ytick labels to make sure they fit properly
    # for i in range(N0):
    #     angle_rad = i / float(N0) * 2 * pi
    #
    #     if angle_rad == 0:
    #         ha, distance_ax = "center", 10
    #     elif 0 < angle_rad < pi:
    #         ha, distance_ax = "left", 1
    #     elif angle_rad == pi:
    #         ha, distance_ax = "center", 1
    #     else:
    #         ha, distance_ax = "right", 1
    #
    #     ax0.text(angle_rad, 100 + distance_ax, xlabels0[i], size=10, horizontalalignment=ha, verticalalignment="center")



    N1 = len(xlabels1)
    x_as1 = [n / float(N1) * 2 * pi for n in range(N1)]
    x_as1 += x_as1[:1]
    # Set color of axes
    plot.rc('axes', linewidth=0.5, edgecolor="#888888")
    # Create polar plots
    ax1 = plot.subplot(122, polar=True)
    # Set clockwise rotation. That is:
    ax1.set_theta_offset(pi / 2)
    ax1.set_theta_direction(-1)
    # Set position of y-labels
    ax1.set_rlabel_position(22)
    # Set color and linestyle of grid
    ax1.xaxis.grid(True, color="#888888", linestyle='solid', linewidth=0.5)
    ax1.yaxis.grid(True, color="#888888", linestyle='solid', linewidth=0.5)
    # Set number of radial axes and set labels
    plot.xticks(x_as1[:-1], xlabels1)
    # Set yticks
    #plot.yticks([-30, -40, -50, -60, -70, -80, -90], ["-30", "-40", "-50", "-60", "-70", "-80", "-90"])
    plot.yticks([1,0.875,0.75,0.625,0.5,0.375,0.25,0.125,0], ["1","0.875","0.75","0.625","0.5","0.375","0.25","0.125","0"])
    ax1.tick_params(axis='y', which='major', labelsize=9)

    for platform in plot1_platforms:
        #Set values
        values = []
        link_data = plat_to_ld[platform]
        for measurements in link_data.values():
            #values.append(mean(measurements))
            values.append(measurements[0])
        values += values[:1]
        values = map(lambda x :  x if x is not None else  0   , values)
        #print platform,x_as0,values,platform_to_color[platform]

        if values:
            plot.plot(x_as1, values, platform_to_color[platform], linewidth=1, linestyle='solid', zorder=3)
            plot.fill(x_as1, values, platform_to_color[platform], alpha=0.25)
            legend = ax1.legend(plot1_platforms, loc=(0.2, -0.3), labelspacing=0.1, fontsize='small')


    # Set axes limits
    #plot.ylim(-30, -100)
    plot.ylim(0, 1)
    plot.xlabel("Links")

    # # Draw ytick labels to make sure they fit properly
    # for i in range(N1):
    #     angle_rad = i / float(N1) * 2 * pi
    #
    #     if angle_rad == 0:
    #         ha, distance_ax = "center", 10
    #     elif 0 < angle_rad < pi:
    #         ha, distance_ax = "left", 1
    #     elif angle_rad == pi:
    #         ha, distance_ax = "center", 1
    #     else:
    #         ha, distance_ax = "right", 1
    #
    #     ax1.text(angle_rad, 100 + distance_ax, xlabels1[i], size=10, horizontalalignment=ha, verticalalignment="center")


    path = os.path.join(os.pardir,"Plots/Radar/PDR/{}".format(readable_channel(channel)))
    if not os.path.exists(path):
        os.makedirs(path)
    filename = readable_channel(channel)+","+readable_txpower(txpower)+","+readable_param(parameter)

    plot.tight_layout()
    plot.title("Average {}\nChannel: {}  txpower: {}dBm\n".format("PDR",
                                                                                                readable_channel(channel),
                                                                                                readable_txpower(txpower)),
                                                                                                size='large',
                                                                                                position=(-0.1, 1.2),
                                                                                                horizontalalignment='center',
                                                                                                verticalalignment='center')

    plot.savefig(os.path.join(path,filename))
    plot.close()

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
    arguments["platform"] = None
    arguments["parameter"] = "0"
    chn = ["25","18","12",None]
    tx = ["0","-3","-7","-15",None]

    for channel in chn:
        arguments["channel"] = channel

        for txpower in tx:                                                 #connecting a list of txpowers
            arguments["txpower"] = txpower
            relevant_files = get_files_by(arguments)
            print(channel,txpower,"RSSI",len(relevant_files))
            parse_files_by_link(relevant_files,arguments)

elif len(sys.argv) > 1 and sys.argv[1] == "table":
    arguments = parse_arguments()
    relevant_files = get_files_by(arguments)
    print("Number of relevant files:",len(relevant_files))
    stats = get_min_max_avg(relevant_files)
    print_stats_table(stats)

elif len(sys.argv) > 1 and sys.argv[1] == "tables":
    arguments = parse_arguments()
    chn = ["25","18","12",None]
    tx = [None]
    for platform in platforms:
        arguments["platform"] = platform
        for channel in chn:
            arguments["channel"] = channel
            for txpwr in tx:
                arguments["txpower"] = txpwr
                print(platform, channel, txpwr)
                relevant_files = get_files_by(arguments)
                print("Number of relevant files:",len(relevant_files))
                stats = get_min_max_avg(relevant_files)
                print_stats_table(stats)

elif len(sys.argv) > 1 and sys.argv[1] == "ranges":
    print_ranges()

elif len(sys.argv) > 1 and sys.argv[1] == "dbm":
    print("Converting sky/z1 files to dbm")
    convert_to_dbm()

elif len(sys.argv) > 1 and sys.argv[1] == "id":
    print(equalize_node_ids(sys.argv[2],sys.argv[3]))

else:
    arguments = parse_arguments()
    storage = DataStorage()                                                                           # an ordered dict {"channel":[([txpowers],[values])]}

    for platform in platforms:
        arguments["platform"] = platform

        for channel in range(11,27):
            arguments["channel"] = str(channel)

            for txpower in txpowers[arguments["platform"]]:                                                 #connecting a list of txpowers
                arguments["txpower"] = str(txpower)
                print(arguments["platform"],arguments["channel"],arguments["txpower"])

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

    #draw_lineplot(storage)
    draw_lineplot_reduced(storage)

print("Finished")
