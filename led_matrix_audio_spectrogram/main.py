#!/usr/bin/python3
# Reese Grimsley 2025, MIT license

# Main python application for the led matrix - audio spectrogram project. 
# Captures audio, processes audio, generates an image to visualize frequency spectrum, and sends to PRU
# PRU will be running a driver to run the LED matrix itself with whatever image arrives
# PRU is signalled by writing data to shared memory -- nominally mem-mapped PRU SRAM, but could be DDR too..

import time
from pb_audio import constants as const
from pb_audio import read_audio, pru_transfer, generate_matrix_image, process_audio
import numpy as np
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-v', '--verbose', action="store_true", default=False)
args = parser.parse_args()

PRINT_PROFILING=args.verbose
PRINT_PROFILE_FREQ = 40


def sliding_window(old_audio, new_audio, output_buf_size=const.PROCESSING_CHUNK_SIZE):
    '''
    Best efforts sliding window, we'll keep as much of the old audio as we need to, prioritizing new data
    '''
    new_len = len(new_audio)

    keep_bytes = output_buf_size - new_len
    old_audio = old_audio[-keep_bytes:] # take the last set of bytes here; those will be the start of the new buffer

    audio = np.concatenate((old_audio,new_audio))

    return audio


def main():
    '''
    The glue ;) most of the magic is all the separate functions. Half of this is just profiling code
    '''
    print('Start Pocketbeagle audio-visualizer')

    #v2 approach to generating images; make a good starting point and mask pixels that aren't needed
    baseline_image = generate_matrix_image.baseline_image(const.MAT_SIZE_H, const.MAT_SIZE_W, max_val=const.IMAGE_MAX_VAL)
    
    #setup comms to PRU (i.e. open /dev/mem)
    pru_shared_mem = pru_transfer.open_pru_mem()

    print("Setup and start audio capture")
    audio_dev_file =read_audio.open_audio(adc_dev_filename=const.DEV_ADC_FILEPATH)
    #setup audio capture
    audio_buffer_newest = None

    sample_bytes = read_audio.read_buf(dev_file=audio_dev_file, chunk_size=const.CHUNK_SIZE_BYTES)
    audio_buffer_oldest = read_audio.format_samples(sample_bytes)
    try:
        print('Start main loop')
        iteration = 0
        while True:

            for i in range(const.FLUSH_ITER):
                read_audio.read_buf(audio_dev_file, chunk_size=const.FLUSH_BUF_SIZE)
            
            # read newest set of samples
            t_read_start = time.time()
            sample_bytes = read_audio.read_buf(dev_file=audio_dev_file, chunk_size=const.CHUNK_SIZE_BYTES)

            t_read_end = time.time()
            audio_buffer_newest = read_audio.format_samples(sample_bytes)

            #combine to produce sliding window
            audio_buffer = sliding_window(audio_buffer_oldest, audio_buffer_newest, const.PROCESSING_CHUNK_SIZE)

            t_create_buffer = time.time()
            #  process chunk
            norm_log_fft_bins = process_audio.process_chunk(audio_buffer)

            # smooth audio
            norm_log_fft_bins = process_audio.spatial_smoothing(norm_log_fft_bins)
            norm_log_fft_bins = process_audio.temporal_smoothing(norm_log_fft_bins)
            t_process_audio = time.time()

            #  generate image - follow standard 
            image = generate_matrix_image.mask_baseline_image(baseline_image, norm_log_fft_bins) # v2 approach
            # image = generate_matrix_image.generate_spectrogram_image(norm_log_fft_bins, image_shape=[const.MAT_NUM_CHANNEL, const.MAT_SIZE_H, const.MAT_SIZE_W], bin_width=const.BIN_PIXEL_WIDTH) # v1 approach

            t_gen_image = time.time()

            #  send image to PRU
            pru_transfer.send_image_to_pru(pru_shared_mem, image)
            t_sent_image = time.time()

            #  profiling/benchmarking
            if PRINT_PROFILING and iteration % PRINT_PROFILE_FREQ == 0:
                print('\nProfiling')
                print('Time to read audio: \t\t%01.3f ms' % (1000*(t_read_end - t_read_start)))
                print('Create audio buffer: \t\t%01.3f ms' % (1000*(t_create_buffer - t_read_end)))
                print('Proc audio: \t\t\t%01.3f ms' % (1000*(t_process_audio - t_create_buffer)))
                print('gen image: \t\t\t%01.3f ms' % (1000*(t_gen_image - t_process_audio)))
                print('send image: \t\t\t%01.3f ms' % (1000*(t_sent_image - t_gen_image)))
                print('**Total time**: \t\t%01.3f ms' % (1000*(t_sent_image - t_read_start)))

            # time.sleep(0.005)

            #prepare for next iter
            audio_buffer_oldest = audio_buffer_newest
            iteration += 1

    except KeyboardInterrupt:
        print('KB interrupt caught; exiting')
    except Exception as e:
        raise e

if __name__ == '__main__':
    main()