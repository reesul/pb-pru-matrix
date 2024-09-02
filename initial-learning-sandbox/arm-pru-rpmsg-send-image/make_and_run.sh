#!/bin/bash
./config-pins-for-matrix.sh >> /dev/null

echo "stop" >> /sys/class/remoteproc/remoteproc1/state
echo PRU state: `cat /sys/class/remoteproc/remoteproc1/state`

make 

if [[  $? -eq 0 ]]
then
   
    cp ./gen/arm-pru-comm-test.out /lib/firmware/am335x-pru0-fw

    echo "start" >> /sys/class/remoteproc/remoteproc1/state
    echo PRU state: `cat /sys/class/remoteproc/remoteproc1/state`
else
echo "did not copy FW or start PRU"
fi

