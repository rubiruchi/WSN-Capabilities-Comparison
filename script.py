import time
import json

DIRECTORY_PATH = os.path.join(os.pardir,'Measurements')

# load config
with open('config.json') as config_file:
    configurations = json.load(config_file)

#dict that maps nodeid to a list of measurements
node_measurements = {}
def create_lists(number_of_nodes):
    for i in range(1,number_of_nodes+1):
        node_measurements[str(i)] = []

#loop through configs and start described experiments
for config in configurations:
    print(config)
    number_of_nodes = int(config[0])
    create_lists(number_of_nodes)
    max_rounds = config.split(',')[4]
    curr_round = 1
    print("num o nodes "+str(number_of_nodes))
    print("rounds "+ max_rounds)
    checklist = range(1,number_of_nodes+1)
    print(checklist)
    row = raw_input()

    while not row == 'measurement finished':


        #who reports this link data set?
        if "," in row:
            now = int(time.time())
            node_id = row.split(',')[0]
            channel = row.split(',')[1]
            txpower = row.split(',')[2]
            if curr_round == 1:
                checklist.remove(int(node_id))
                print(checklist)

        row = raw_input()
        #bundle link data from this node
        while ":" in row:
            measurement = {}
            measurement["from"]    = row.split(":")[0]
            measurement["param"]   = row.split(":")[1]
            measurement["value"]   = row.split(":")[2]
            measurement["time"]    = now
            measurement["channel"] = channel
            measurement["txpower"] = txpower
            node_measurements[node_id].append(measurement)
            row = raw_input()

        #delete data gathered in incomplete round
        if row == 'round failed':
            for i in range(1,number_of_nodes+1):
                if len(node_measurements[str(i)]) is curr_round:
                    del(node_measurements[str(i)][curr_round-1])

        #firts round must complete with all nodes reporting back, so checklist has to be 0
        if row == 'round finished':
            if (round != 1) and (not checklist):
                curr_round = curr_round +1
            else:
                checklist = range(1,number_of_nodes+1)


if not os.path.exists(DIRECTORY):
    os.makedirs(DIRECTORY)

for node in node_measurements:
    filename = "Node"+str()
