import time
import json

# load config
with open('config.json') as config:
    configList = json.load(config)

number_of_nodes = configList[0]
measurements = configList[1]

def create_log_file():


for measurement in measurements:
    print(line)
    row = raw_input()
    while row not 'measurement finished':
        now = int(time.time())
        node_id = row.split(',')[0]  #add list to check with size if all nodes reported in at end of round if first round.
        channel = row.split(',')[1]
        txpower = row.split(',')[2]
        row = raw_input()
        while "," not in row:
            from_node_id = row.split(":")[0]
            link_param = row.split(":")[1]
            value = row.split(":")[2]
            row = raw_input()
