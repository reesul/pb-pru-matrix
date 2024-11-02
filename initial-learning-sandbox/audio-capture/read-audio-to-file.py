#!/usr/bin/python3
import wave
import os, sys, time


dev_filepath = '/dev/iio:device0'
BUF_SIZE = 256
ELEMENT_SIZE = 2 #uint16 containers
CHUNK_SIZE = BUF_SIZE * ELEMENT_SIZE
TEST_DURATION = 15.0 #seconds
SAMPLERATE = 7692 #calc sampling rate from ADC DTS config#8192 #guess?
FLUSH_ITERATIONS=25

buffers = []
buffer = bytearray()

#data elements are likely read in LE byte order
with open(dev_filepath, 'rb') as dev_file:
    print('flushing... ')
    for j in range(FLUSH_ITERATIONS):
        data = dev_file.read(CHUNK_SIZE) #flush
    print('start recording')
    t1 = time.time()
    i = 0
    while (time.time() - t1 < TEST_DURATION):
        data = dev_file.read(CHUNK_SIZE)
        buffers.append(data)
        i += 1
    print("read %d buffers" % i)
    t2 = time.time()

print('test duration %f s' % (t2-t1))
print(len(buffers))
for b in buffers:
    buffer.extend(b)
print(len(buffer))

# print(buffers)
print(len(buffer))

# exit()
with wave.open("sound1.wav", "wb") as f:
    # 2 Channels.
    f.setnchannels(1)
    # 2 bytes per sample.
    f.setsampwidth(2)
    f.setframerate(SAMPLERATE)
    f.writeframes(buffer)