import sys
import subprocess

filename = sys.argv[1]
process = subprocess.Popen(['/bin/bash'], shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,stderr=subprocess.STDOUT)

sys.stdout.write(">STARTED\n")

count = 0

process.stdin.write('make {}.upload\n'.format(filename))
while 1:
    line = process.stdout.readline()
    sys.stdout.write(line)
    if "An error occoured:" in line:
        sys.stdout.write(">FOUND ERROR\n")
        while "rm {}.ihex".format(filename) not in line:
            line = process.stdout.readline()
            sys.stdout.write(line)

        sys.stdout.write(">RETRYING\n")
        if count < 5:
            process.stdin.write('make {}.upload\n'.format(filename))
            count = count +1
        else:
            sys.stdout.write(">FAILED 5 TIMES\n")
            break

    elif "rm {}.ihex".format(filename) in line:
        sys.stdout.write(">FINISHED\n")
        break
