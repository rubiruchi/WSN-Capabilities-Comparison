import json
import sys
import subprocess
import os
import signal
import smtplib
from time import gmtime,strftime,time
from email.mime.text import MIMEText


if len(sys.argv) < 2:
    sys.exit("please define TARGET.\n eg.: python script.py sky\n")

platform = sys.argv[1]

#if stick is present:use stick. if not, use pardir
DIRECTORY_PATH = os.path.join('/media/nevin/D29077E29077CB8B'.format(platform))
if not os.path.exists(DIRECTORY_PATH):
    DIRECTORY_PATH = os.path.join(os.pardir,'Measurements/{}'.format(platform))
    if not os.path.exists(DIRECTORY_PATH):
        os.makedirs(DIRECTORY_PATH)
else:
    DIRECTORY_PATH = os.path.join(DIRECTORY_PATH,'/Measurements/{}'.format(platform))
    if not os.path.exists(DIRECTORY_PATH):
        os.makedirs(DIRECTORY_PATH)

# load config
with open(os.path.join(DIRECTORY_PATH,'config.json')) as config_file:
    configurations = json.load(config_file)

today = strftime("%d,%m,%y %H:%M:%S",time())
DIRECTORY_PATH = os.path.join(DIRECTORY_PATH,'/today')

subprocesses = []

number_of_nodes = 0
current_round = 0
round_failed = False
recently_reset = True
checklist = range(1,number_of_nodes+1)
broken_lines_counter = 0
same_round_counter = 0
last_round = -1
filename = ""

#sends mail to emails specified in the config
def sendMail(message):
    msg = MIMEText(message)
    msg['Subject'] = 'Experiment Status'
    msg['From'] = 'DoorMonitoringSystem@gmail.com'
    msg['To'] = "nevin.allwood@yahoo.de"

    s = smtplib.SMTP_SSL('smtp.gmail.com',465)
    s.login("DoorMonitoringSystem@gmail.com","WSN-Project17")
    s.sendmail("DoorMonitoringSystem@gmail.com",to,msg.as_string())
    s.quit()

#handles Ctrl+C termination
def signal_handler(signum,frame):
    print(">exiting process")
    for process in subprocesses:
        process.kill()
    sys.exit(0)

#only works for single sink setup as of now
def reboot_sink():
    print(">rebooting sink")
    # trigger watchdog reset in sink node(s)
    write_to_subprocesses("reboot\n")
    while(get_untagged_input != 'Booted\n'):
        print("...")
        write_to_subprocesses("reboot\n")
        time.sleep(0.5) #to give device time to reboot

    print(">Sink rebooted")

#checks if the input is script relevant by splitting at '$' and returning the split part
def get_untagged_input():
    global broken_lines_counter

    for process in subprocesses:
        line = process.stdout.readline()
        if line.startswith('NODE$'):
            return line.split('$')[1]
        elif '$' in line:
            sys.stdout.write(">line broken: "+line)
            broken_lines_counter += 1
            return ""
        else:
            return ""

#sends a string to all registered subprocesses
def write_to_subprocesses(str):
    for process in subprocesses:
        process.stdin.write(str)

#prints round/saves measurement/verifies round depending on input line
def handle_line(line):
    global checklist
    global round_failed
    global current_round
    global recently_reset
    global broken_lines_counter
    global last_round
    global same_round_counter
    global filename

    if line == "":
        return

    if line.startswith('Round=') and len(line) < 11:     #additional check to make script more robust in case lines are broken
        broken_lines_counter = 0;
        sys.stdout.write(line)
        current_round = int(line.split('=')[1].rstrip())
        if current_round == last_round:
            same_round_counter += 1
        else:
            same_round_counter = 0
            last_round = current_round

    #bundle link data from a node
    elif ':' in line:
        if len(line.split(':')) is 6:
            broken_lines_counter = 0
            now = time()
            measurement = {}
            node_id = line.split(':')[0]
            channel = line.split(':')[1]
            txpower = line.split(':')[2]

            if (current_round == 0 or recently_reset) and int(node_id) in checklist:
                checklist.remove(int(node_id))

            measurement["from"]    = line.split(":")[3]
            measurement["param"]   = line.split(":")[4]
            measurement["value"]   = line.split(":")[5].rstrip()
            measurement["time"]    = now
            measurement["channel"] = channel
            measurement["txpower"] = txpower

            #only add if not init round and link data already available (in round 1 or after fail data from nodes higher up not yet available, so drop measurement)
            if ((current_round > 1) and not round_failed and not recently_reset) or (int(node_id) > int(measurement["from"])):
                with open(os.path.join(DIRECTORY_PATH,filename),'a') as f:
                    f.write(str(measurement)+'\n')
        else:
            sys.stdout.write(">line broken: "+line)
            broken_lines_counter += 1


    elif line == 'round finished\n':
        broken_lines_counter = 0
        round_failed = False
        #initial round or rounds after reset only complete if all nodes report back, so checklist has to be empty
        if (current_round == 0 or recently_reset) and not checklist:
            sys.stdout.write(">round ok. continuing\n")
            write_to_subprocesses('continue\n')
            recently_reset = False
        elif (current_round == 0 or recently_reset) and checklist:
            checklist = range(1,number_of_nodes+1)
            sys.stdout.write(">resend round\n")
            write_to_subprocesses('resend\n')

    elif line == 'round failed\n':
        round_failed = True

    elif line == 'reset\n':
        broken_lines_counter = 0
        sys.stdout.write(">All nodes must report back again\n")
        checklist = range(1,number_of_nodes+1)
        recently_reset = True

    elif line == 'measurement complete\n':
        broken_lines_counter = 0
        return

    else:
        sys.stdout.write(">line broken: "+line)
        broken_lines_counter +=1

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
        process = subprocess.Popen(['/bin/bash'], shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        if device.startswith('ttyUSB'):
            sys.stdout.write('>make login TARGET={} MOTES=/dev/{}\n'.format(platform, device))
            process.stdin.write('make login TARGET={} MOTES=/dev/{}\n'.format(platform, device))
        elif device.startswith('ttyACM'):
            sys.stdout.write('>make login TARGET={} BOARD=sensortag/cc2650 PORT=/dev/{}\n'.format(platform, device))
            process.stdin.write('make login TARGET={} BOARD=sensortag/cc2650 PORT=/dev/{}\n'.format(platform, device))
        subprocesses.append(process)

devices = filter(lambda x: x.startswith('ttyUSB') or x.startswith('ttyACM'), os.listdir('/dev'))
throw_out_debugger()
subprocess_init()
signal.signal(signal.SIGINT, signal_handler)

#loop through configs and start described experiments
#sendMail("Expermient with {} started".format(platform))
experimentstart = time()
for config in configurations:
    number_of_nodes = int(config[0])
    current_round = 0
    round_failed = False
    same_round_counter = 0
    last_round = -1
    checklist = range(1,number_of_nodes+1)
    filename = config

    sys.stdout.write(">sending:"+config+"\n")
    write_to_subprocesses(config+"\n")

    starttime = time()
    line = get_untagged_input()
    handle_line(line);
    while line != 'measurement complete\n':
        #if 4 lines in a row couldn't be read because they are broken
        if broken_lines_counter > 4:
            print(">broken lines reset.")
            print(">last config was:"+config)
            reboot_sink()
            # adjust rounds of current config
            config.rstrip('200')
            config = config + str(200 - current_round)
            write_to_subprocesses(config+"\n")

        #if the same round is being send more than 12 times either channel or tx power isn't working, so skip measurement next time sink is waiting for validation
        if same_round_counter > 12:
            print(">Skipping this config")
            reboot_sink()
            break

        line = get_untagged_input()
        handle_line(line)



    elapsed_time = time() -starttime
    print(">"+strftime("%H:%M:%S",gmtime(elapsed_time)))

#sendMail(">Experiment with {} took: ".format(platform) + strftime("%H:%M:%S",gmtime(elapsed_time)))
sys.stdout.write(">Finished\n")
print(">Experiment took: "+strftime("%H:%M:%S",gmtime(elapsed_time)))
