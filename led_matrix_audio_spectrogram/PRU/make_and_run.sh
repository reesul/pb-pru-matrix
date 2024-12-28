#!/bin/bash

CURRENT_DIR=${PWD##*/}  
PRU_PROJ_NAME=${CURRENT_DIR} #same as makefile

echo "stop" > /sys/class/remoteproc/remoteproc1/state
echo PRU state: `cat /sys/class/remoteproc/remoteproc1/state`

./config-pins-for-matrix.sh >> /dev/null

make 

if [[  $? -eq 0 ]]
then
   
        cp ./gen/${PRU_PROJ_NAME}.out /lib/firmware/am335x-pru0-fw #PRU.out is because that is ''

    echo "start" >> /sys/class/remoteproc/remoteproc1/state
    echo PRU state: `cat /sys/class/remoteproc/remoteproc1/state`
else
    echo "did not copy FW or start PRU"
fi

