#!/usr/bin/python3
import wave
import os, sys, time


BUF_SIZE = 1024
ELEMENT_SIZE = 2 #uint16 containers
CHUNK_SIZE = BUF_SIZE * ELEMENT_SIZE
TEST_DURATION = 5.0 #seconds
SAMPLERATE = 40000

with wave.open('sound-background.wav', 'rb') as wave_file:
    bytes = wave_file.readframes(CHUNK_SIZE)
    print(bytes[0:16])
    