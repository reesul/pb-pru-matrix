#!/bin/bash
## This is to be run on pocketbeagle. There should be an audio-preamp sending a signal to AIN5 (3.3V rail that is voltage divided to <1.8V input to the pin)
#
#Test audio capture with: 
#  cat /sys/bus/iio/devices/iio:device0/in_voltage5_raw
#
#We will only use a single input. Assuming we can sample at 200kS/s, we'll go for ~5ms chunks with 1024 samples/buffer

#should be default, but confirm setting. Pin is shared with GPIO and must be configured as input
config-pin P2_35 gpio_input

#enable AIN5 as an input; all others should be 0
echo 1 > /sys/bus/iio/devices/iio\:device0/scan_elements/in_voltage5_en

# Set the buffer to capture 1024 elements at a time --> 5.12 ms
echo 1024 > /sys/bus/iio/devices/iio\:device0/buffer/length

# enable the driver to capture continuously and store within buffers
echo 1 > /sys/bus/iio/devices/iio\:device0/buffer/enable

## read data from CLI
#hexdump -e '"iio0 :" 8/2 "%04x " "\n"' /dev/iio:device0
