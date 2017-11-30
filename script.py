import time
import json
import sys
import subprocess
import os

process = subprocess.Popen(['/bin/bash'], shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,stderr=subprocess.STDOUT)

DIRECTORY_PATH = os.path.join(os.pardir,'Measurements')
if not os.path.exists(DIRECTORY_PATH):
    os.makedirs(DIRECTORY_PATH)

platform = ""
if len(sys.argv) > 1:
    platform = sys.argv[1]

# load config
with open('config.json') as config_file:
    configurations = json.load(config_file)

#dict that maps nodeid to a list of measurements
node_measurements = {}

def load_measurements(number_of_nodes):
    for i in range(1,number_of_nodes+1):
        filename = platform+"_"+str(i)
        try:
            with open(os.path.join(DIRECTORY_PATH,filename),'r') as measurement_file:
                node_measurements[str(i)] = json.load(measurement_file)
        except IOError:
            node_measurements[str(i)] = []

#checks if the input is script relevant by splitting at '$' and returning the split part
def get_untagged_input():
    line = process.stdout.readline()
    if '$' in line:
        sys.stdout.write(line.split('$')[1])
        return line.split('$')[1]
    else:
        return ""

sys.stdout.write("logging in\n")
process.stdin.write('make login\n')

#loop through configs and start described experiments
for config in configurations:
    sys.stdout.write("sending:"+config+"\n")
    process.stdin.write(config+"\n")
    number_of_nodes = int(config[0])
    first_round = True
    round_failed = False
    checklist = range(1,number_of_nodes+1)
    load_measurements(number_of_nodes)

    line = get_untagged_input()
    while not line == 'measurement finished\n':
        #who reports this link data set?
        if "," in line:
            node_id = line.split(',')[0]
            channel = line.split(',')[1]
            txpower = line.split(',')[2]
            if first_round and int(node_id) in checklist:
                checklist.remove(int(node_id))

        line = get_untagged_input()

        #bundle link data from this node
        while ":" in line:
            now = time.time()
            measurement = {}
            measurement["from"]    = line.split(":")[0]
            measurement["param"]   = line.split(":")[1]
            measurement["value"]   = line.split(":")[2].rstrip()
            measurement["time"]    = now
            measurement["channel"] = channel
            measurement["txpower"] = txpower

            #only add if link data already available (in round 1 or after fail data from nodes higher up not yet available, so drop measurement)
            if (not first_round and not round_failed) or not(node_id < measurement["from"]):
                node_measurements[str(node_id)].append(measurement)
                filename = platform+"_"+str(node_id)
                with open(os.path.join(DIRECTORY_PATH,filename),'w') as f:
                    json.dump(node_measurements[str(node_id)],f)

            line = get_untagged_input()

        if line == 'round finished\n':
            #first round is only complete if all nodes report back, so checklist has to be empty
            if first_round and not checklist:
                sys.stdout.write("first round ok. continuing\n")
                first_round = False
                process.stdin.write('continue\n')
            elif first_round and checklist:
                checklist = range(1,number_of_nodes+1)
                sys.stdout.write("resend first round\n")
                process.stdin.write('resend\n')

        if line == 'round failed\n':
            round_failed = True

sys.stdout.write(">Finished\n")
