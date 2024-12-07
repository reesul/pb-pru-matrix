#!/usr/bin/python3
import wave
import os, sys, time
import pb_audio.constants as const

TEST_DURATION = 35.0 #seconds
SAMPLERATE = 40000 #calc sampling rate from ADC DTS config#8192 #guess?
FLUSH_ITERATIONS=10

def write_to_wav(buffer, filename="sound1.wav"):
    with wave.open(filename, "wb") as f:
        # 1 Channel.
        f.setnchannels(1)
        # 2 bytes per sample.
        f.setsampwidth(2)
        f.setframerate(const.SAMPLERATE)
        f.writeframes(buffer)

def read_buf(dev_file, chunk_size):
    buf = dev_file.read(chunk_size) #flush
    return buf

def _test_main():
    buffers = []
    buffer = bytearray()

    #data elements are likely read in LE byte order
    with open(const.DEV_ADC_FILEPATH, 'rb') as dev_file:
        for j in range(FLUSH_ITERATIONS):
            data = read_buf(dev_file, chunk_size=const.CHUNK_SIZE)
        t1 = time.time()
        i = 0
        while (time.time() - t1 < TEST_DURATION):
            data = read_buf(dev_file, chunk_size=const.CHUNK_SIZE)
            buffers.append(data)
            i += 1
        t2 = time.time()

    DEAD_SECONDS=0
    buffer = bytearray([0 for i in range(const.SAMPLERATE*2*DEAD_SECONDS)])
    for b in buffers:
        buffer.extend(b)
    print(f'{len(buffer)} samples')

    write_to_wav(buffer)

if __name__ == '__main__':
    _test_main()