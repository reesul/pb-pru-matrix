#!/usr/bin/python3
# Reese Grimsley 2025, MIT license
# Purpose is processing functions for audio signals to get a log-power and log-frequency vector
#  for and audio signal / buffer of samples. 
# Includes filtering, noise suppression, frequency binning, FFT itself etc. Mostly with numpy calls

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
    '''
    Test out audio-read from file, run some FFTs, and benchmark runtime
    '''
    with wave.open(wavefile_name, 'rb') as wave_file:

        samples = read_samples(wave_file, chunk_size)

        t1 = time.time()
        if use_real_fft:
            freq_domain = np.fft.rfft(samples)
        else: 
            freq_domain = np.fft.fft(samples)
        t2 = time.time()
        # print(f'{t2-t1} seconds to run FFT on {samples.shape[0]} points')

    return t2-t1, freq_domain


def get_real_fourier_power(chunk, eps=1e-8):
    '''
    Real signal, so take real FFT and convert to dB by power
    '''
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

    print('pull audio chunks...')
    with wave.open(wavefile_name, 'rb') as wave_file:

        while True:

            chunk = read_samples(wave_file, chunk_size)
            audio_chunks.append(chunk)

            if len(chunk) < chunk_size:
                #probably better ways to check this, like EOF..
                break
            

    return audio_chunks


def benchmark_fft():
    '''
    Try a bunch of FFT sizes and see how long it takes
    Will help dicatate upper limit on CPU speed relative to sample rate/buffer duration
    '''
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
    
    Did an experiment and started from copilot written algo, but it worked poorly and had some functional error
    This algo is a bit hacky, mainly when trying to map a new set of frequency bins that are logarithmically increasing
    -- Don't honestly understand well what I did, but new bins work well. Worth investigating in the future to check for skipped/under utilized frequencies
    -- I tried to make sure low bins (20, 30.. 100) each had their own value. From default settings, original FFT has ~9.7 Hz spacing

    Algo:
        trim frequency/power spectrum to min / max frequencies (default 18 <-> SR/2 --> SR was 20kS/s
        generate a set of bins over which to average power spectrum -- use log as basis
            - also ensure that no frequency bins are being ignored or rejected.. somewhat hard
        rebin power according to bin indices -- average power within joined frequency bins


    Returns the rebinned log-power spectrum and the indices of the trimmed signal used for each new bin (averaged across log-power between those indices) 
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

    #init
    rebin_power = np.zeros(num_bins) 

    start = end = 0
    # save the frequency bins that were used per bin
    bin_inds = np.zeros((num_bins,2))
    for i in range(0, num_bins): 
        start = max(int(new_bins[i]), end) 
        end = int(new_bins[i+1]) 
        if start >= end: 
            #means we've gotten ahead of the bin indices, which is likely at low frequencies. Give that frequency its own bin
            end = start+1
            #this may lead to the middle/upper having a poor mapping relative to low frequencies

        rebin_power[i] = np.mean(power_spectrum[start:end]) 
        bin_inds[i,:] = [start, end]

        # print(rebin_power[i])

    return rebin_power, bin_inds, freq


def mask_band(non_log_power, freq, HZ_TARGET=60):
    '''
    Try to mask a particular frequency band (still original linear frequencies) around a particular frequency target. 
    Mainly used to mask out some noise from power line / ground loop around 60 Hz (and maybe harmonics)    
    
    NOT optimized
    '''
    ind_lower = ind_higher = 0
    bin = -1
    for i, f in enumerate(freq):
        if f < HZ_TARGET and freq[i+1] => HZ_TARGET:
            # actually frequency of interest isn't going to be exactly in here, find the closest one
            bin = i
            break

    non_log_power[bin] = (non_log_power[bin-1] + non_log_power[bin+1]) / 2
    return non_log_power


def normalize_fft(fft_bins, MINIMUM_MAX=const.MIN_MAX_DB):
    '''
    Normalize the FFT bins, nominally on the post-processed, log-frequency 
    so less change of specific high frequencies running the scaling
    '''
    mm = np.min(fft_bins)
    MM = np.max(fft_bins)
    MM = max(MINIMUM_MAX, MM) # another upper limit to give more continuity between frames

    normalized = (fft_bins - mm) / (MM- mm)
    return normalized


def process_chunk(samples):
    '''
    Primary audio processing function, for some chunk of audio
    '''

    freq = get_frequencies(len(samples), const.SAMPLERATE)

    power_db = get_real_fourier_power(samples)

    # Have a nasty 60 Hz noise on all audio signal, so try to mask this (and 2nd harmonic)
    power_db = mask_band(power_db, freq, HZ_TARGET=60)
    power_db = mask_band(power_db, freq, HZ_TARGET=120)


    log_power_bins, new_bin_indices, log_freq = rebin_logarithmic(power_db, freq, min_freq=const.FREQ_MIN, max_freq=const.FREQ_MAX)
    # Not a mathmatically pure log-frequency mapping, but good enough

    normalized_log_fft_bins = normalize_fft(log_power_bins, MINIMUM_MAX=const.MIN_MAX_DB)

    return normalized_log_fft_bins


from scipy.ndimage import gaussian_filter
def spatial_smoothing(power_spectrum):
    '''
    Smoothing between adjacent frequencies
    '''
    
    if const.BIN_PIXEL_WIDTH == 2:
       filtered_specrogram = gaussian_filter(power_spectrum, sigma=0.75, truncate=3, mode='constant')
    elif const.BIN_PIXEL_WIDTH == 1:
        filtered_specrogram = gaussian_filter(power_spectrum, sigma=1.4, truncate=2, mode='constant')
    else:
        filtered_specrogram = power_spectrum


    return filtered_specrogram

def temporal_smoothing(power_spectrum):
    '''
    Temporal filter to smooth jittery look. 
    Current implementation is 1-tap IIR / alpha-filter. This could be improved quite a bit..

    Uses static variable/state attached to this function and initialized on first run
    '''
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



if __name__ == '__main__':
    _test_on_image_file()

