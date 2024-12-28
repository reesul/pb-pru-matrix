#!/bin/bash
## This is to be run on pocketbeagle. There should be an audio-preamp sending a signal to AIN5 (3.3V rail that is voltage divided to <1.8V input to the pin)
#
#Test audio capture with: 
#  cat /sys/bus/iio/devices/iio:device0/in_voltage5_raw
#
#We will only use a single input. Assuming we can sample at 40kS/s, we'll go for ~51.2ms chunks with 2048 samples/buffer

#should be default, but confirm setting. Pin is shared with GPIO and must be configured as input
config-pin P2_35 gpio_input

#disable so we can reconfigure
echo 0 > /sys/bus/iio/devices/iio\:device0/buffer/enable

#enable AIN5 as an input; all others should be 0
# echo 0 > /sys/bus/iio/devices/iio\:device0/scan_elements/in_voltage*_en
echo 1 > /sys/bus/iio/devices/iio\:device0/scan_elements/in_voltage5_en

# Set the buffer to capture 2048 elements at a time --> 51.2 ms
BUF_SIZE=8192
echo $BUF_SIZE > /sys/bus/iio/devices/iio\:device0/buffer/length

# enable the driver to capture continuously and store within buffers
echo 1 > /sys/bus/iio/devices/iio\:device0/buffer/enable

## read data from CLI
#hexdump -e '"iio0 :" 8/2 "%04x " "\n"' /dev/iio:device0
