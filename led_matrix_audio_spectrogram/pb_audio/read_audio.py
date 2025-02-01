#!/usr/bin/python3
# Reese Grimsley 2025, MIT license

import wave
import os, sys, time
import pb_audio.constants as const
import numpy as np

TEST_DURATION = 35.0 #seconds
SAMPLERATE = 40000 #calc sampling rate from ADC DTS config
FLUSH_ITERATIONS=10 #collect buffers to dump data out of ADC queue
## buffer size will be from const.CHUNK_SIZE_BYTES

def write_to_wav(buffer, filename="sound1.wav"):
    '''
    Write buffer of audio data to file and test audibility, quality
    '''
    with wave.open(filename, "wb") as f:
        # 1 Channel.
        f.setnchannels(1)
        # 2 bytes per sample for 12-bit ADC
        f.setsampwidth(2)
        f.setframerate(const.SAMPLERATE)
        f.writeframes(buffer)

def read_buf(dev_file, chunk_size):
    '''
    read buffer of data from /dev/ audio iface
    '''
    buf = dev_file.read(chunk_size) #flush
    return buf

def read_all_available_bytes(dev_file):
    '''
    flush the whole file... probably useless function on /dev
    '''
    return dev_file.read()

def format_samples(sample_bytes):
    '''
    Convert data in from byte buffer to sample buffer 
    little endian int16
    '''
    samples_np = np.frombuffer(sample_bytes, dtype='<h')
    return samples_np
    

def open_audio(adc_dev_filename=const.DEV_ADC_FILEPATH, flush_iter=FLUSH_ITERATIONS):
    '''
    Open ADC to read audio samples from /dev interface

    Read buffers based on const.CHUNK_SIZE_BYTES, and may flush out N buffers upon opening to 'clear the queue'
    '''
    dev_file = None
    print('opening audio')
    try:
        dev_file = open(adc_dev_filename, 'rb') 
        if dev_file:
            print('Read %d chunks of audio to flush interface' % FLUSH_ITERATIONS)
            for j in range(FLUSH_ITERATIONS):
                read_buf(dev_file, chunk_size=const.CHUNK_SIZE_BYTES)

    
    except Exception as e:
        raise e
    
    return dev_file

def _test_main():
    buffers = []
    buffer = bytearray()

    dev_file = open_audio(const.DEV_ADC_FILEPATH)

    t1 = time.time()
    i = 0
    while (time.time() - t1 < TEST_DURATION):
        data = read_buf(dev_file, chunk_size=const.CHUNK_SIZE_BYTES)
        buffers.append(data)
        i += 1
    t2 = time.time()

    DEAD_SECONDS=0
    buffer = bytearray([0 for i in range(const.SAMPLERATE*2*DEAD_SECONDS)])
    for b in buffers:
        buffer.extend(b)
    print(f'{len(buffer)} samples')

    write_to_wav(buffer)

def read_speed_test():
    '''
    How fast can we read data through /dev/? 
    Depends on sample rate set from DTS
    '''
    dev_file = open_audio(const.DEV_ADC_FILEPATH)

    for i in range(100):
        read_buf(dev_file, chunk_size=2048)

    t_total = 0
    NUM_TEST=100
    CHUNK_SIZE = 2048
    for i in range(NUM_TEST):
        t1= time.time()
        read_buf(dev_file, chunk_size=CHUNK_SIZE)
        t2 = time.time()
        t_total += (t2-t1)

    print('Took %s to run %d iteratiosn of %d bytes (2samples/byte default)' % (t_total, NUM_TEST, CHUNK_SIZE))


if __name__ == '__main__':
    _test_main()