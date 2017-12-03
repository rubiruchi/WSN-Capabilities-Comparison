import time
import json
import sys
import subprocess
import os

process = subprocess.Popen(['/bin/bash'], shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,stderr=subprocess.STDOUT)

DIRECTORY_PATH = os.path.join(os.pardir,'Measurements')
if not os.path.exists(DIRECTORY_PATH):
    os.makedirs(DIRECTORY_PATH)

if len(sys.argv) < 3:
    sys.exit("please define USB port and TARGET.\n eg.: python script.py /dev/ttyUSB0 sky\n")

usbport = sys.argv[1]
platform = sys.argv[2]

# load config
with open('config.json') as config_file:
    configurations = json.load(config_file)

#dict that maps nodeid to a list of measurements
node_measurements = {}

def load_node_measurement(node_id):
    filename = platform+"_"+str(node_id)
    try:
        with open(os.path.join(DIRECTORY_PATH,filename),'r') as measurement_file:
            node_measurements[str(node_id)] = json.load(measurement_file)
    except IOError:
        node_measurements[str(node_id)] = []

#checks if the input is script relevant by splitting at '$' and returning the split part
def get_untagged_input():
    line = process.stdout.readline()
    if '$' in line:
        sys.stdout.write(line.split('$')[1])
        return line.split('$')[1]
    else:
        return ""

sys.stdout.write('make login TARGET={} MOTES={}\n'.format(platform, usbport))
process.stdin.write('make login TARGET={} MOTES={}\n'.format(platform, usbport))

#loop through configs and start described experiments
for config in configurations:
    sys.stdout.write(">sending:"+config+"\n")
    process.stdin.write(config+"\n")
    number_of_nodes = int(config[0])
    first_round = True
    round_failed = False
    checklist = range(1,number_of_nodes+1)
    for i in range(1,number_of_nodes+1):
        load_node_measurement(i)
    line = get_untagged_input()
    while not line == 'measurement finished\n':

        #bundle link data from this node
        if ":" in line:
            if len(line.split(':')) is 6:
                now = time.time()
                measurement = {}
                node_id = line.split(':')[0]
                channel = line.split(':')[1]
                txpower = line.split(':')[2]

                if first_round and int(node_id) in checklist:
                    checklist.remove(int(node_id))

                measurement["from"]    = line.split(":")[3]
                measurement["param"]   = line.split(":")[4]
                measurement["value"]   = line.split(":")[5].rstrip()
                measurement["time"]    = now
                measurement["channel"] = channel
                measurement["txpower"] = txpower

                #only add if link data already available (in round 1 or after fail data from nodes higher up not yet available, so drop measurement)
                if (not first_round and not round_failed) or not(node_id < measurement["from"]):

                    load_node_measurement(node_id)#lock before??
                    node_measurements[str(node_id)].append(measurement)
                    filename = platform+"_"+str(node_id)
                    with open(os.path.join(DIRECTORY_PATH,filename),'w') as f:
                        json.dump(node_measurements[str(node_id)],f)
            else:
                sys.stdout.write(">line broken\n")

        line = get_untagged_input()

        if line == 'round finished\n':
            #first round is only complete if all nodes report back, so checklist has to be empty
            if first_round and not checklist:
                sys.stdout.write(">first round ok. continuing\n")
                first_round = False
                process.stdin.write('continue\n')
            elif first_round and checklist:
                checklist = range(1,number_of_nodes+1)
                sys.stdout.write(">resend first round\n")
                process.stdin.write('resend\n')

        if line == 'round failed\n':
            round_failed = True

        if line == 'reset\n':
            first_round = True
            checklist = range(1,number_of_nodes+1)

sys.stdout.write(">Finished\n")
