import time
import json
import sys
import subprocess
import os

DIRECTORY_PATH = os.path.join(os.pardir,'Measurements')
if not os.path.exists(DIRECTORY_PATH):
    os.makedirs(DIRECTORY_PATH)

if len(sys.argv) < 2:
    sys.exit("please define TARGET.\n eg.: python script.py sky\n")

platform = sys.argv[1]

# load config
with open('config.json') as config_file:
    configurations = json.load(config_file)

#dict that maps nodeid to a list of measurements
node_measurements = {}
subprocesses = []

number_of_nodes = 0
first_round = True
round_failed = False
checklist = range(1,number_of_nodes+1)

for i in range(1,number_of_nodes+1):
    load_node_measurement(i)

# handles Ctrl+C termination
def signal_handler(signum,frame):
    print("exiting process")
    log.write(strftime("%Y-%m-%d %H:%M:%S", gmtime()) + ": " +
    "System Stopped\n\n")
    log.close()
    copy_to_permalog()
    sys.exit(0)

def load_node_measurements():
    for node_id in range(1,number_of_nodes+1):
        filename = platform+"_"+str(node_id)
        try:
            with open(os.path.join(DIRECTORY_PATH,filename),'r') as measurement_file:
                node_measurements[str(node_id)] = json.load(measurement_file)
        except IOError:
            node_measurements[str(node_id)] = []

#checks if the input is script relevant by splitting at '$' and returning the split part
def get_untagged_input():
    for process in subprocesses:
        line = process.stdout.readline()
        if '$' in line:
            sys.stdout.write(line.split('$')[1])
            handle_line(line.split('$')[1])
            return line.split('$')[1]
        else:
            return ""

def write_to_subprocesses(str):
    for process in subprocesses:
        process.stdin.write(str)

def handle_line(line):
    global first_round
    global checklist
    global round_failed
    global node_measurements

    #bundle link data from a node
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
                node_measurements[str(node_id)].append(measurement)
                filename = platform+"_"+str(node_id)
                with open(os.path.join(DIRECTORY_PATH,filename),'w') as f:
                    json.dump(node_measurements[str(node_id)],f)
        else:
            sys.stdout.write(">line broken\n")

    if line == 'round finished\n':
        #first round is only complete if all nodes report back, so checklist has to be empty
        if first_round and not checklist:
            sys.stdout.write(">first round ok. continuing\n")
            first_round = False
            write_to_subprocesses('continue\n')
        elif first_round and checklist:
            checklist = range(1,number_of_nodes+1)
            sys.stdout.write(">resend first round\n")
            write_to_subprocesses('resend\n')

    if line == 'round failed\n':
        round_failed = True

    if line == 'reset\n':
        first_round = True
        checklist = range(1,number_of_nodes+1)


devices = filter(lambda x: x.startswith('ttyUSB') or x.startswith('ttyACM'), os.listdir('/dev'))
for device in devices:
    process = subprocess.Popen(['/bin/bash'], shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if device.startswith('ttyUSB'):
        sys.stdout.write('>make login TARGET={} MOTES=/dev/{}\n'.format(platform, device))
        process.stdin.write('make login TARGET={} MOTES=/dev/{}\n'.format(platform, device))
    elif device.startswith('ttyACM'):
        sys.stdout.write('>make login TARGET={} PORT=/dev/{}\n'.format(platform, device))
        process.stdin.write('make login TARGET={} PORT=/dev/{}\n'.format(platform, device))
    subprocesses.append(process)

#loop through configs and start described experiments
for config in configurations:
    number_of_nodes = int(config[0])
    first_round = True
    round_failed = False
    checklist = range(1,number_of_nodes+1)
    load_node_measurements()

    sys.stdout.write(">sending:"+config+"\n")
    write_to_subprocesses(config+"\n")

    line = get_untagged_input()
    while line != 'measurement finished\n':
        line = get_untagged_input()


sys.stdout.write(">Finished\n")
