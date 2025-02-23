#!/bin/bash

echo "Start"

echo "setup audio cap"
./pb_audio/setup_audio_adc_capture.sh

echo "make and run matrix-PRU code"
cd PRU
source ./make_and_run.sh
PRU_SUCCESS=$?
cd ..

if [ $PRU_SUCCESS -ge "0" ] 
then
    echo "Start actual python app"
    python3 main.py
else
    echo "failed to setup PRU driver; not starting python"
fi