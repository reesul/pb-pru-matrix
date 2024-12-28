#!/usr/bin/python3
import wave
import os, sys, time
import struct
import numpy as np

import pb_audio.constants as const
import pb_audio.generate_matrix_image as generate_matrix_image


def read_samples(wave_file, num_samples):
    sample_bytes = wave_file.readframes(num_samples)
    samples_np = np.frombuffer(sample_bytes, dtype='<h')
    return samples_np


def run_fft_test(wavefile_name='sound1.wav', chunk_size=const.CHUNK_SIZE_BYTES, use_real_fft=True):
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


def run_fft_rfft_test(wavefile_name='sound1.wav', chunk_size=const.CHUNK_SIZE_BYTES):
    with wave.open(wavefile_name, 'rb') as wave_file:


        samples = read_samples(wave_file, chunk_size)

        t1 = time.time()
        freq_domain = np.fft.fft(samples)
        t2 = time.time()
        print(freq_domain.shape)
        rfreq_domain = np.fft.rfft(samples)
        print(rfreq_domain.shape)

        print(f'{t2-t1} seconds to run FFT on {samples.shape[0]} points')
        power = np.abs(freq_domain)**2
        r_power = np.abs(rfreq_domain)**2

        diff = power[0:len(r_power)] - r_power

    return freq_domain, rfreq_domain

def get_real_fourier_power(chunk, eps=1e-8):
    freq_domain = np.fft.rfft(chunk)
    power = np.abs(freq_domain)**2
    power_db = 10 * np.log10(power + eps)
    return power_db


def pull_one_chunk_from_file(wavefile_name='sound1.wav', chunk_size=const.CHUNK_SIZE_BYTES):
    with wave.open(wavefile_name, 'rb') as wave_file:
        samples = read_samples(wave_file, chunk_size)
    return samples

def pull_all_chunks_from_file(wavefile_name='sound1.wav', chunk_size=const.CHUNK_SIZE_BYTES):
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

def rebin_logarithmic(power_spectrum, freq, num_bins=const.NUM_OUTPUT_BINS, log_base=2, min_freq=const.FREQ_MIN, max_freq=const.FREQ_MAX): 
    """ 
    Re-bin the power spectrum into a specified number of logarithmically spaced bins 
        provided by copilot...  

    Algo:
        trim frequency/power spectrum to min / max frequencies
        generate a set of bins over which to average power spectrum -- use log as basis
            - also ensure that no frequency bins are being ignored or rejected.. somewhat hard
        rebin power according to bin indices -- average power within joined frequency bins
    """ 
          
    #filter to min and max frequencies
    keep_indices = np.logical_and(freq > min_freq, freq < max_freq) 

    power_spectrum = power_spectrum[keep_indices]
    freq = freq[keep_indices]

    length = len(power_spectrum) 
    
    #for num_bin power bins, we need num_bin+1 indices that separate each bin
    new_bins = np.logspace(0, np.log(length)/np.log(log_base), num_bins+1, base=log_base)   # OG
    # new_bins = np.logspace(0, length, num_bins+1, base=log_base)  
    new_bins = new_bins - 1 #otherwise 0th bin is ignored
    # print(new_bins)
    # print(new_bins[0:10])

    rebin_power = np.zeros(num_bins) 

    start = end = 0
    bin_inds = np.zeros((num_bins,2))
    for i in range(0, num_bins): 
        start = max(int(new_bins[i]), end) 
        end = int(new_bins[i+1]) 
        if start >= end: 
            #means we've gotten ahead of the bin indices, which is likely at low frequencies
            end = start+1

        if i<8:
            # print(freq[start:end] )
            pass
        rebin_power[i] = np.mean(power_spectrum[start:end]) 
        bin_inds[i,:] = [start, end]

        # print(rebin_power[i])


    return rebin_power, bin_inds

def mask_band(non_log_power, freq, HZ_TARGET=60):

    ind_lower = ind_higher = 0
    bin = -1
    for i, f in enumerate(freq):
        if f < HZ_TARGET and freq[i+1] > HZ_TARGET:
            bin = i
            break

    non_log_power[bin] = (non_log_power[bin-1] + non_log_power[bin+1]) / 2
    return non_log_power


def normalize_fft(fft_bins, MINIMUM_MAX=const.MIN_MAX_DB):
    mm = np.min(fft_bins)
    MM = np.max(fft_bins)
    MM = max(MINIMUM_MAX, MM)

    normalized = (fft_bins - mm) / (MM- mm)
    return normalized

def process_chunk(samples, chunk_size=const.BUF_SIZE_SAMPLES):

    freq = get_frequencies(len(samples), const.SAMPLERATE)

    power_db = get_real_fourier_power(samples)

    power_db = mask_band(power_db, freq, HZ_TARGET=60)
    power_db = mask_band(power_db, freq, HZ_TARGET=120)

    # power_db[0] = np.min(power_db)

    log_power_bins, new_bin_indices = rebin_logarithmic(power_db, freq, min_freq=const.FREQ_MIN, max_freq=const.FREQ_MAX)
    # freq_bins = freq[new_bin_indices] #incorrect code, probably needs lambda func
    # log_power_bins[0] = np.min(log_power_bins)

    normalized_log_fft_bins = normalize_fft(log_power_bins, MINIMUM_MAX=const.MIN_MAX_DB)

    return normalized_log_fft_bins


from scipy.ndimage import gaussian_filter
def spatial_smoothing(power_spectrum):
    #try other types of filters. Want something a bit sharper
    filtered_specrogram = power_spectrum
    
    if const.BIN_PIXEL_WIDTH == 2:
       filtered_specrogram = gaussian_filter(power_spectrum, sigma=0.75, truncate=3, mode='constant')
    elif const.BIN_PIXEL_WIDTH == 1:
        filtered_specrogram = gaussian_filter(power_spectrum, sigma=1.4, truncate=2, mode='constant')


    return filtered_specrogram

def temporal_smoothing(power_spectrum):
    
    
    # 0 to 1, with 1 being only current value and 0 being only most recent
    alpha = 0.65 
    if temporal_smoothing.last_power_spectrum is None:
        temporal_smoothing.last_power_spectrum = power_spectrum

    cur_power_spectrum = power_spectrum

    power_spectrum = alpha * (power_spectrum) + (1-alpha) *  temporal_smoothing.last_power_spectrum

    temporal_smoothing.last_power_spectrum = cur_power_spectrum
    return power_spectrum

temporal_smoothing.last_power_spectrum = None


def _test_on_image_file(filename='sound_song_endlessly_noisy.wav', buf_size=const.BUF_SIZE_SAMPLES):
    import cv2

    audio_samples = pull_all_chunks_from_file(wavefile_name=filename, chunk_size=buf_size)
    t_start = time.time()
    freq = get_frequencies(buf_size, const.SAMPLERATE)
    
    print('process audio chunks')
    for i, samples in enumerate(audio_samples):
        normalized_log_fft_bins = process_chunk(samples, chunk_size=buf_size, filename=output_filename)

        image = generate_matrix_image.generate_spectrogram_image(normalized_log_fft_bins)

        output_filename = 'output_images/matrix_image_%05d.png' % i
        cv2.imwrite(output_filename, image)

    # benchmark_fft()
    # freq_domain, rfreq_domain = run_fft_rfft_test(chunk_size=buf_size)


if __name__ == '__main__':
    _test_on_image_file()

