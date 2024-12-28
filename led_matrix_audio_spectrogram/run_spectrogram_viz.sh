#!/bin/bash

echo "Start"

echo "setup audio cap"
./pb_audio/setup_audio_adc_capture.sh

echo "make and run matrix-PRU code"
cd PRU
./make_and_run.sh
cd ..

echo "Start actual python app"
python3 main.py
