import json
import sys
import subprocess
import os
import signal
import smtplib
from time import gmtime,strftime,time,sleep
from email.mime.text import MIMEText
from nbstreamreader import NonBlockingStreamReader as NBSR

if len(sys.argv) < 2:
    sys.exit("please define TARGET.\n eg.: python script.py sky\n")

platform = sys.argv[1]

DIRECTORY_PATH = ""

subprocesses = []
streamreaders = []
configurations = []

number_of_nodes = 0
current_round = 0
round_failed = False
recently_reset = True
rebooted = False
complete = False
checklist = range(1,number_of_nodes+1)
same_round_counter = 0
last_round = -1
filename = ""

#creates directory in which measurements are saved in case it doesn't exist yet
def make_directory():
    global DIRECTORY_PATH
    global configurations

    #if stick is present:use stick. if not, use pardir
    DIRECTORY_PATH = '/media/pi/Experiments'
    if not os.path.exists(DIRECTORY_PATH):
        DIRECTORY_PATH = os.path.join(os.pardir,'Measurements/{}'.format(platform))
        if not os.path.exists(DIRECTORY_PATH):
            os.makedirs(DIRECTORY_PATH)
    else:
        DIRECTORY_PATH = os.path.join(DIRECTORY_PATH,'Measurements/{}'.format(platform))
        if not os.path.exists(DIRECTORY_PATH):
            os.makedirs(DIRECTORY_PATH)

    # load config
    with open(os.path.join(DIRECTORY_PATH,'config.json')) as config_file:
        configurations = json.load(config_file)

    today = strftime("%d,%m,%y_%H-%M",gmtime(time()))
    DIRECTORY_PATH = os.path.join(DIRECTORY_PATH,today)
    if not os.path.exists(DIRECTORY_PATH):
        os.makedirs(DIRECTORY_PATH)

#sends mail to emails specified in the config
def sendMail(message):
    msg = MIMEText(message)
    msg['Subject'] = 'Experiment Status'
    msg['From'] = 'DoorMonitoringSystem@gmail.com'
    msg['To'] = "nevin.allwood@yahoo.de"

    s = smtplib.SMTP_SSL('smtp.gmail.com',465)
    s.login("DoorMonitoringSystem@gmail.com","WSN-Project17")
    s.sendmail("DoorMonitoringSystem@gmail.com","nevin.allwood@yahoo.de",msg.as_string())
    s.quit()

#handles Ctrl+C termination
def signal_handler(signum,frame):
    print(strftime("%H:%M:%S",gmtime(time())) + ">exiting process")
    sys.exit(0)

#own isdigit function because std function can not handle negative numbers
def is_digit(n):
    try:
        int(n)
        return True
    except ValueError:
        return  False

#checks if the input is script relevant by splitting at '$' and returning the split part
def get_untagged_input():
    for reader in streamreaders:
        line = reader.getline()
        if line:
            handle_line(line)

#sends a string to all registered subprocesses
def write_to_subprocesses(msg):
    for process in subprocesses:
        #sys.stdout.write(strftime("%H:%M:%S",gmtime(time())) +"writing: "+msg)
        process.stdin.write(msg)

#prints round/saves measurement/verifies round depending on input line
def handle_line(line):
    global checklist
    global round_failed
    global current_round
    global recently_reset
    global last_round
    global same_round_counter
    global filename
    global rebooted
    global complete

    if line == "":
        return

    if line == 'Booted\n':
        #sys.stdout.write(strftime("%H:%M:%S",gmtime(time())) + line)
        rebooted = True

    elif line.startswith('Temp@') and len(line) < 20: #additional check is to make script more robust in case lines are broken
        with open(os.path.join(DIRECTORY_PATH,filename),'a+') as f:
            f.write(line)

    elif line.startswith('Round=') and len(line) < 11:
        try:
            current_round = int(line.split('=')[1].rstrip())
        except ValueError:
            return

        if current_round == last_round:
            same_round_counter += 1
        else:
            same_round_counter = 0
            last_round = current_round

    #bundle link data from a node
    elif ':' in line:
        #broken line check
        if len(line.split(':')) is 6:
            now = time()
            measurement = {}
            node_id = line.split(':')[0]

            # to check if all nodes have received inital message
            if (current_round == 0 or recently_reset) and int(node_id) in checklist:
                checklist.remove(int(node_id))

            measurement["receiver"] = node_id
            measurement["time"]    = now

            #broken line check
            for i in range(1,5):
                if not is_digit(line.split(':')[i]):
                    return

            measurement["channel"] = line.split(':')[1]
            measurement["txpower"] = line.split(':')[2]
            measurement["sender"]  = line.split(":")[3]
            measurement["value"]   = line.split(":")[4]
            measurement["param"]   = line.split(":")[5].rstrip()

            #only add if not init round and link data already available (in round 1 or after fail data from nodes higher up not yet available, so drop measurement)
            if ((current_round > 1) and not round_failed and not recently_reset) or (int(node_id) > int(measurement["sender"])):
                #also only add if channels actually match
                if config_channel == measurement["channel"]:
                    with open(os.path.join(DIRECTORY_PATH,filename),'a+') as f:
                        f.write(str(measurement)+'\n')

    elif line == 'round finished\n':
        round_failed = False
        #print(strftime("%H:%M:%S",gmtime(time())) + ">Round "+str(current_round)+" finished")
        #initial round or rounds after reset only complete if all nodes report back, so checklist has to be empty
        if (current_round == 0 or recently_reset) and not checklist:
            #sys.stdout.write(strftime("%H:%M:%S",gmtime(time())) +">round ok. continuing\n")
            write_to_subprocesses('continue\n')
            recently_reset = False
        elif (current_round == 0 or recently_reset) and checklist:
            checklist = range(1,number_of_nodes+1)
            #sys.stdout.write(strftime("%H:%M:%S",gmtime(time())) +">resend round\n")
            write_to_subprocesses('resend\n')

    elif line == 'round failed\n':
        #sys.stdout.write(strftime("%H:%M:%S",gmtime(time())) + line)
        print(strftime("%H:%M:%S",gmtime(time()))+"round "+str(current_round)+" failed")
        round_failed = True

    elif line == 'reset\n':
        sys.stdout.write(strftime("%H:%M:%S",gmtime(time())) + line)
        #print(strftime("%H:%M:%S",gmtime(time())) + ">reset. all nodes must report back again")
        checklist = range(1,number_of_nodes+1)
        recently_reset = True

    elif line == 'measurement complete\n':
        #print(strftime("%H:%M:%S",gmtime(time())) + ">measurement complete")
        complete = True


#throws the debugger board of the sensortags out of the devices list in case it is present
def throw_out_debugger():
    highest = 0
    for device in devices:
        if device.startswith('ttyACM') and int(device[-1:]) > highest:
            highest = int(device[-1:])
    if highest != 0:
        devices.remove('ttyACM'+str(highest))

#goes through devices list andstarts a bash subprocess. then performs login
def subprocess_init():
    for device in devices:
        process = subprocess.Popen(['/bin/bash'], shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        if device.startswith('ttyUSB'):
            sys.stdout.write('>make login TARGET={} MOTES=/dev/{}\n'.format(platform, device))
            process.stdin.write('make login TARGET={} MOTES=/dev/{}\n'.format(platform, device))
        elif device.startswith('ttyACM'):
            sys.stdout.write('>make login TARGET={} BOARD=sensortag/cc2650 PORT=/dev/{}\n'.format(platform, device))
            process.stdin.write('make login TARGET={} BOARD=sensortag/cc2650 PORT=/dev/{}\n'.format(platform, device))

        subprocesses.append(process)
        sr = NBSR(process.stdout)
        streamreaders.append(sr)


make_directory()
devices = filter(lambda x: x.startswith('ttyUSB') or x.startswith('ttyACM'), os.listdir('/dev'))
throw_out_debugger()
subprocess_init()
signal.signal(signal.SIGINT, signal_handler)

#loop through configs and start described experiments
sendMail("Expermient with {} started".format(platform))
experimentstart = time()
for config in configurations:
    number_of_nodes = int(config[0])
    config_channel = config.split(',')[1]
    current_round = 0
    round_failed = False
    same_round_counter = 0
    last_round = -1
    checklist = range(1,number_of_nodes+1)
    filename = config
    complete = False

    sys.stdout.write(strftime("%H:%M:%S",gmtime(time())) +">sending:"+config+"\n")
    write_to_subprocesses(config+"\n")

    starttime = time()
    line = get_untagged_input()
    while not complete:
        #if the sink reboots either channel or tx power isn't working, so skip measurement
        if rebooted:
            rebooted = False
            print(strftime("%H:%M:%S",gmtime(time())) + ">Sink rebooted")
            sleep(0.2)
            break

        line = get_untagged_input()

    elapsed_time = time() -starttime
    print(strftime("%H:%M:%S",gmtime(time())) + ">Measurement finished "+strftime("%H:%M:%S",gmtime(elapsed_time)))
    with open(os.path.join(DIRECTORY_PATH,filename),'a+') as f:
        f.write(strftime("%H:%M:%S",gmtime(elapsed_time))+'\n')

elapsed_time = time() -experimentstart
sendMail(">Experiment with {} took: ".format(platform) + strftime("%H:%M:%S",gmtime(elapsed_time)))
print(strftime("%H:%M:%S",gmtime(time())) +">Finished")
print(strftime("%H:%M:%S",gmtime(time())) + ">Experiment took: "+strftime("%H:%M:%S",gmtime(elapsed_time)))
