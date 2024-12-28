# Pocket Beagle PRU Matrix

This repo is for a personal project, in which I use a 64x32 LED matrix for audio spectrogram visualization. 

I am using the PocketBeagle as the hardware platform due to its small size and set of readily available IO. A large part of my decision to use this devboard is that the AM335x includes PRU (programmable real time unit) cores for fast IO. I'll be using those to quickly send control signals to the LED matrix. I will also be attaching a microphone / audio signal interface (3.5mm jack) so that the A-cores on the beagle board can capture audio and run an FFT. I'll display that FFT on the LED matrix

First version of this project is complete as of 2024 EoY. This includes:
* Custom cape (PCB that beagle board attaches to) that provides audio input and output signalling to the matrix panel
   * Revisions needed to reduce analog noise, reduce pinout/external connection, etc.
* PRU code that reads an image from shared memory, and manages output pins for the matrix such that we visualize an 8-bit, 32x64 pixel image. 
   * Framerate is >30 FPS and looks about as smooth as such a low-res screen can provide
* Updated device tree overlay for setting ADC configuartion (20kS/s) (see [dtb](./dtb/) files)
   * Data arrives through IIO driver and read with sysfs
   * I noted that bb-overlay repo (origin of these DTS) has an ./install.sh that doesn't work. I had to look in /boot/uEnv.txt to apply the DTBO file (name_overlays)
* A bunch of python code to do the audio capture, processing (FFTs and such), and image generation
   * I cheated the signalling to the PRU to just open /dev/mem and write to PRU's shared SRAM. Images too big for rpmsg anyway
   * Buffer sizes, sampling rates, and processing code are tuned to be snappy -- audio sync tests look visually acceptable (<200ms). Image processing at >30fps

The fact that this works with Python code and limited optimizations shows that AM335x is still a plenty beefy processor. That said, I really want a new revision of pocket beagle with a more modern (probably TI) processor, so long as there's a PRU.

The actual code itself for this application is under [](./led_matrix_audio_spectrogram/). There's a main runner script that will turn off the PRU, rebuild firmware, start PRU, apply sysfs settings for ADC capture, and kick off the audio processing + image generation
* My WIP code was put under [](./initial-learning-sandbox/), and I don't really plan to reorganize this :) 


I haven't yet uploaded the v1 files for the PCB (Eagle format), but that'll be part of tne next step

The set of improvements from here is not too high, but relies on improved hardware solution. Sometime in the future, I'll also try to document the whole process of building this, since I have extensive notes on the challenges and solutions.