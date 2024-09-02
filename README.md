# Pocket Beagle PRU Matrix

This repo is for a personal project, in which I'm aiming to use a 64x32 LED matrix for audio spectrogram visualization. 

I am using the PocketBeagle as the hardware platform due to its small size and set of readily available IO. A large part of my decision to use this devboard is that the AM335x includes PRU (programmable real time unit) cores for fast IO. I'll be using those to quickly send control signals to the LED matrix. I will also be attaching a microphone / audio signal interface (3.5mm jack) so that the A-cores on the beagle board can capture audio and run an FFT. I'll display that FFT on the LED matrix

To complete this project, a few things are required:
* A PCB fitted to the pocket beagle that breaks out PRU->LED matrix signals (w/ voltage shift) and incorporates audio input. It is a simple PCB, but will also aid the mechanical mounting of this solution, since the PB doesn't not otherwise adhere easily to the matrix panel (no adhesives!)
* An audio signal chain and processing algorithm to convert incoming audio chunks into an FFT that can be visualized. I'll need to read up on typical spectrograms here, since there may be some binning/nonlinear transforms necessary like melspectrogram (logarithmic frequency). Needs to be fast enough so visualization changes in accordance with audio recognition. I foresee this piece being somewhat difficult
* Visualization PRU firmware to accept a new arbitrary image and convert this for the matrix panel. The panel displays singular rows at a time, and has to switch between rows quickly enough to seem like a static image to our eyes. This requires some fast switching. The same is true for getting more color depth -- flash the LEDs longer for more intese color.. shorter for less. This may limit how many bits of color depth are achievable
  
I'm running this on whatever free time I'm willing to throw at it, so slow progress is expected. 
