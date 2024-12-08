#!/usr/bin/python3

import time
from pb_audio import constants as const
from pb_audio import read_audio, pru_transfer, generate_matrix_image, process_audio
import numpy as np

PRINT_PROFILING=False

def main():
    print('Start Pocketbeagle audio-visualizer')
    
    #setup comms to PRU
    pru_shared_mem = pru_transfer.open_pru_mem()

    print("Setup and start audio capture")
    audio_dev_file =read_audio.open_audio(adc_dev_filename=const.DEV_ADC_FILEPATH)
    #setup audio capture
    audio_buffer_newest = None

    sample_bytes = read_audio.read_buf(dev_file=audio_dev_file, chunk_size=const.CHUNK_SIZE_BYTES)
    audio_buffer_oldest = read_audio.format_samples(sample_bytes)
    try:
        print('Start main loop')
        while True:
            
            # read newest set of samples
            t_read_start = time.time()
            sample_bytes = read_audio.read_buf(dev_file=audio_dev_file, chunk_size=const.CHUNK_SIZE_BYTES)

            t_read_end = time.time()
            audio_buffer_newest = read_audio.format_samples(sample_bytes)


            #combine to produce sliding window
            #FIXME - is this right? oldest-newest or newest-oldest? depends on sample order
            #FIXME - will this introduce pops? any LPF over the samples here between the buffers?
            # audio_buffer = np.concatenate((audio_buffer_oldest, audio_buffer_newest))
            audio_buffer = np.concatenate((audio_buffer_newest, audio_buffer_oldest))
            # audio_buffer = audio_buffer_newest

            t_create_buffer = time.time()
            #  process chunk
            norm_log_fft_bins = process_audio.process_chunk(audio_buffer, chunk_size=audio_buffer.shape[0])

            t_process_audio = time.time()

            #  generate image - follow standard 
            #TODO: fix image dimension layout to follow CHW natively, so no change and copy is needed

            image = generate_matrix_image.generate_spectrogram_image(norm_log_fft_bins, image_shape=[const.MAT_NUM_CHANNEL, const.MAT_SIZE_H, const.MAT_SIZE_W], bin_width=const.BIN_PIXEL_WIDTH)

            t_gen_image = time.time()

            #  send image
            pru_transfer.send_image_to_pru(pru_shared_mem, image)
            t_sent_image = time.time()

            #  profiling/benchmarking

            if PRINT_PROFILING:
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

    except KeyboardInterrupt:
        print('KB interrupt caught; exiting')
    except Exception as e:
        raise e

if __name__ == '__main__':
    main()