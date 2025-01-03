#!/usr/bin/python3
import wave
import os, sys, time
import struct
import numpy as np
import cv2

MAT_SIZE_W = 64
MAT_SIZE_H = 32
BIN_PIXEL_WIDTH = 2

BUF_SIZE = 1024
ELEMENT_SIZE = 2 #uint16 containers
CHUNK_SIZE = BUF_SIZE * ELEMENT_SIZE
TEST_DURATION = 35.0 #seconds
SAMPLERATE = 40000
NUM_OUTPUT_BINS = int(MAT_SIZE_W / BIN_PIXEL_WIDTH)


def read_samples(wave_file, num_samples):
    sample_bytes = wave_file.readframes(num_samples)
    samples_np = np.frombuffer(sample_bytes, dtype='<h')
    return samples_np


def run_fft_test(wavefile_name='sound1.wav', chunk_size=CHUNK_SIZE, use_real_fft=True):
    with wave.open(wavefile_name, 'rb') as wave_file:
        # wave_file.setnchannels(1)
        # 2 bytes per sample.
        # wave_file.setsampwidth(2)
        # wave_file.setframerate(SAMPLERATE)

        samples = read_samples(wave_file, chunk_size)
        # samples2 = read_samples(wave_file, chunk_size) #like a sliding window..
        # samples = np.concatenate((samples1, samples2))

        t1 = time.time()
        if use_real_fft:
            freq_domain = np.fft.rfft(samples)
        else: 
            freq_domain = np.fft.fft(samples)
        t2 = time.time()
        # print(f'{t2-t1} seconds to run FFT on {samples.shape[0]} points')

    return t2-t1, freq_domain


def run_fft_rfft_test(wavefile_name='sound1.wav', chunk_size=CHUNK_SIZE):
    with wave.open(wavefile_name, 'rb') as wave_file:
        # wave_file.setnchannels(1)
        # 2 bytes per sample.
        # wave_file.setsampwidth(2)
        # wave_file.setframerate(SAMPLERATE)

        samples = read_samples(wave_file, chunk_size)
        # samples2 = read_samples(wave_file, chunk_size) #like a sliding window..
        # samples = np.concatenate((samples1, samples2))

        t1 = time.time()
        freq_domain = np.fft.fft(samples)
        print(freq_domain.shape)
        rfreq_domain = np.fft.rfft(samples)
        print(rfreq_domain.shape)

        # print(f'{t2-t1} seconds to run FFT on {samples.shape[0]} points')
        power = np.abs(freq_domain)**2
        r_power = np.abs(rfreq_domain)**2

        diff = power[0:len(r_power)] - r_power

    return freq_domain, rfreq_domain

def get_real_fourier_power(chunk):
    freq_domain = np.fft.rfft(chunk)
    power = np.abs(freq_domain)**2
    power_db = 10 * np.log10(power)
    return power_db


def pull_one_chunk(wavefile_name='sound1.wav', chunk_size=CHUNK_SIZE):
    with wave.open(wavefile_name, 'rb') as wave_file:
        samples = read_samples(wave_file, chunk_size)
    return samples

def pull_all_chunks(wavefile_name='sound1.wav', chunk_size=CHUNK_SIZE):
    audio_chunks = []
    i=0
    print('pull audio chunks...')
    with wave.open(wavefile_name, 'rb') as wave_file:
        while True:
            chunk = read_samples(wave_file, chunk_size)
            if len(chunk) < chunk_size:
                break
            audio_chunks.append(chunk)
            i += 1
    return audio_chunks

def benchmark_fft():
    buf_sizes = [128, 256, 512, 1024, 2048, 4096]
    for bs in buf_sizes:
        chunk_s = bs
        num_tests = 50
        total_latency = 0
        for i in range(num_tests):
            latency, fft = run_fft_test(chunk_size=chunk_s)
            total_latency += latency
        print(' %0.3f ms to run FFT on %d points or %0.1f ms of audio' % (total_latency/num_tests*1000, chunk_s, chunk_s/SAMPLERATE*1000))



def get_frequencies(num_points, sample_rate):
    ind = np.asarray(range((num_points // 2) + 1))
    frequencies = sample_rate * ind / num_points 

    #alternatively, frequencies = np.fft.rfftfreq(buf_size, 1/SAMPLERATE)


    return frequencies

def rebin_logarithmic(power_spectrum, num_bins=NUM_OUTPUT_BINS, log_base=2): 
    """ Re-bin the power spectrum into a specified number of logarithmically spaced bins 
        provided by copilot... gives NAN values, which seems.. .wrong   
    """ 
    length = len(power_spectrum) 
    # print(power_spectrum)
    new_bins = np.logspace(0, np.log(length)/np.log(log_base), num_bins+1, base=log_base) 
    # print(new_bins)

    rebin_power = np.zeros(num_bins) 
    rebin_power[0] = power_spectrum[0] #0th bin is DC; we should handle differently

    start = end = 1
    bin_inds = np.zeros((num_bins,2))
    for i in range(1, num_bins): 
        start = max(int(new_bins[i]), end) 
        end = int(new_bins[i+1]) 
        if start >= end: 
            end = start+1

        # print('%d:%d' % (start, end) )
        rebin_power[i] = np.mean(power_spectrum[start:end]) 
        bin_inds[i,:] = [start, end]

        # print(rebin_power[i])


    return rebin_power, bin_inds

def generate_spectrogram_image(fft_bins, image_shape=(MAT_SIZE_H, MAT_SIZE_W, 3), bin_width=BIN_PIXEL_WIDTH):
    COLOR_WHITE = [255,255,255]
    COLOR_RED = [0,0,255]
    COLOR_GREEN = [0,255,0]
    COLOR_BLUE = [255,0,0]

    QUAD_WHITE=[0,MAT_SIZE_H//4] # TOP, BOTTOM
    QUAD_RED=[MAT_SIZE_H//4,MAT_SIZE_H//2]
    QUAD_GREEN=[MAT_SIZE_H//2,MAT_SIZE_H*3//4]
    QUAD_BLUE=[MAT_SIZE_H*3//4,MAT_SIZE_H]

    image = np.zeros(image_shape, dtype=np.uint8)

    bin_heights = (fft_bins * MAT_SIZE_H).astype(dtype=np.uint8)
    bin_pixel_height = MAT_SIZE_H - bin_heights #flip up-down since pixels start from upper left

    num_bins = fft_bins.shape[0]

    def color_bin_quadrant(bin, color, bin_value, quadrant_top, quadrant_bottom, bin_height=MAT_SIZE_H, bin_width=BIN_PIXEL_WIDTH):

        if bin_value > quadrant_bottom:
            pass #remain as zeros
        if bin_value < quadrant_top:
            bin[quadrant_top:quadrant_bottom,:,:] = color
        else:
            bin[bin_value:quadrant_bottom,:,:] = color

        return bin


    for i in range(num_bins):
        bin_height = bin_pixel_height[i]
        cols = (i*2,(i+1)*2)

        image[:,cols[0]:cols[1],:] = color_bin_quadrant(image[:, cols[0]:cols[1],:], COLOR_WHITE, bin_height, QUAD_WHITE[0], QUAD_WHITE[1])
        image[:,cols[0]:cols[1],:] = color_bin_quadrant(image[:, cols[0]:cols[1],:], COLOR_RED, bin_height, QUAD_RED[0], QUAD_RED[1])
        image[:,cols[0]:cols[1],:] = color_bin_quadrant(image[:, cols[0]:cols[1],:], COLOR_GREEN, bin_height, QUAD_GREEN[0], QUAD_GREEN[1])
        image[:,cols[0]:cols[1],:] = color_bin_quadrant(image[:, cols[0]:cols[1],:], COLOR_BLUE, bin_height, QUAD_BLUE[0], QUAD_BLUE[1])



    return image

def normalize_fft(fft_bins):
    mm = np.min(fft_bins)
    MM = np.max(fft_bins)

    normalized = (fft_bins - mm) / (MM- mm)
    return normalized

def process_chunk(samples, chunk_size=CHUNK_SIZE, filename='output_images/waveform.png'):


    freq = get_frequencies(chunk_size, SAMPLERATE)

    power_db = get_real_fourier_power(samples)

    power_db[0] = np.min(power_db)

    log_power_bins, new_bin_indices = rebin_logarithmic(power_db)

    normalized_log_fft_bins = normalize_fft(log_power_bins)

    image = generate_spectrogram_image(normalized_log_fft_bins)

    cv2.imwrite(filename, image)



if __name__ == '__main__':

    buf_size = 4096 ## 4096 -> 100ms chunk, 1024 --> 25ms approx
    # buf_size = 256
    # samples = pull_one_chunk(wavefile_name='sound_song_endlessly_noisy.wav', chunk_size=buf_size)
    audio_samples = pull_all_chunks(wavefile_name='sound_song_endlessly_noisy.wav', chunk_size=buf_size)
    t_start = time.time()
    freq = get_frequencies(buf_size, SAMPLERATE)
    
    print('process audio chunks')
    for i, samples in enumerate(audio_samples):
        output_filename = 'output_images/matrix_image_%03d.png' % i
        process_chunk(samples, chunk_size=buf_size, filename=output_filename)

    # benchmark_fft()
    # freq_domain, rfreq_domain = run_fft_rfft_test(chunk_size=buf_size)

