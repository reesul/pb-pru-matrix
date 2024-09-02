#!/usr/bin/python3

from time import sleep
import math

fo = open("/dev/rpmsg_pru30", "wb", 0)

while True:
    print('send')
    fo.write(b"11111111111111111111111111111111111111111111");
    print('sleep...')
    sleep(3)

# Close opened file
fo.close()