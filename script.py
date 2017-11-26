import time
import json
import sys
import subprocess
import os

process = subprocess.Popen(['/bin/bash'], shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,stderr=subprocess.STDOUT)

DIRECTORY_PATH = os.path.join(os.pardir,'Measurements')

# load config
with open('config.json') as config_file:
    configurations = json.load(config_file)

#dict that maps nodeid to a list of measurements
node_measurements = {}
def create_lists(dictionary,number_of_nodes):
    for i in range(1,number_of_nodes+1):
        dictionary[str(i)] = []

def get_untagged_input():
    line = process.stdout.readline()
    if '$' in line:
        sys.stdout.write(line.split('$')[1])
        return line.split('$')[1]
    else:
        sys.stdout.write("rejected line: "+line)
        return ""

sys.stdout.write("logging in\n")
process.stdin.write('make login\n')

#loop through configs and start described experiments
for config in configurations:
    sys.stdout.write("sending:"+config+"\n")
    process.stdin.write(config+"\n") #send conf to sink
    number_of_nodes = int(config[0])
    create_lists(node_measurements,number_of_nodes)
    first_round = True
    checklist = range(1,number_of_nodes+1)
    line = get_untagged_input()
    while not line == 'measurement finished':

        #who reports this link data set?
        if "," in line:
            now = int(time.time())
            node_id = line.split(',')[0]
            channel = line.split(',')[1]
            txpower = line.split(',')[2]
            if first_round and int(node_id) in checklist:
                checklist.remove(int(node_id))

        line = get_untagged_input()

        #bundle link data from this node
        while ":" in line:
            measurement = {}
            measurement["from"]    = line.split(":")[0]
            measurement["param"]   = line.split(":")[1]
            measurement["value"]   = line.split(":")[2]
            measurement["time"]    = now
            measurement["channel"] = channel
            measurement["txpower"] = txpower

            #only add if link data already available
            #(in round 1 data from nodes higher up not yet available, so drop measurement)
            if not first_round or not(node_id < measurement["from"]):
                node_measurements[str(node_id)].append(measurement)

            line = get_untagged_input()

        if line == 'round finished\n':
            #first round is only complete if all nodes report back, so checklist has to be empty
            if (first_round and not checklist) or not first_round:
                sys.stdout.write("first round ok. continuing\n")
                first_round = False
                process.stdin.write('continue\n')
            else:
                checklist = range(1,number_of_nodes+1)
                sys.stdout.write("resend first round\n")
                process.stdin.write('resend\n')


sys.stdout.write("MEASUREMENT FINISHED\n")

if not os.path.exists(DIRECTORY):
    os.makedirs(DIRECTORY)

for node in node_measurements:
    sys.stdout.write(node)
    #filename = "Node "+str(node)
