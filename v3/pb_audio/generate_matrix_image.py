import numpy as np
from pb_audio import constants as const

VAL = const.IMAGE_MAX_VAL #TODO make arg

COLOR_WHITE = np.asarray([VAL,VAL,VAL])[..., np.newaxis, np.newaxis]
COLOR_RED = np.asarray([VAL,0,0])[..., np.newaxis, np.newaxis]
COLOR_GREEN = np.asarray([0,VAL,0])[...,np.newaxis, np.newaxis]
COLOR_BLUE = np.asarray([0,0,VAL])[...,np.newaxis, np.newaxis]

def generate_spectrogram_image(fft_bins, image_shape=(const.MAT_NUM_CHANNEL, const.MAT_SIZE_H, const.MAT_SIZE_W), bin_width=const.BIN_PIXEL_WIDTH):

    C,H,W = image_shape

    QUAD_BLUE =  [0,H//4] # BOTTOM, TOP
    QUAD_GREEN = [H//4, H//2]
    QUAD_RED =   [H//2, H*3//4]
    QUAD_WHITE = [H*3//4, H]


    image = np.zeros(image_shape, dtype=np.uint8)

    bin_pixel_height = (fft_bins * H).astype(dtype=np.uint8)
    # bin_pixel_height = H - bin_pixel_height #flip up-down since pixels start from upper left

    num_bins = fft_bins.shape[0]
    # print('num bins %d' % num_bins)
    # print(image.shape)

    for i in range(num_bins):
        # print(f'bin {i}')
        bin_height = bin_pixel_height[i]
        # print(f'bin height {bin_height}')
        col_start = i * bin_width
        col_end = col_start + bin_width
        # print('%d:%d' % (col_start, col_end))

        # print(image[:,:,col_start:col_end])

        #### Map bin heights to color pixels
        #TODO; make a cooler color map, and actually MAP that function here
        # print('blue')
        image[:,:,col_start:col_end] = color_bin_quadrant(image[:,:,col_start:col_end], COLOR_BLUE, bin_height, QUAD_BLUE[0], QUAD_BLUE[1])
        # print('green')
        image[:,:,col_start:col_end] = color_bin_quadrant(image[:,:,col_start:col_end], COLOR_GREEN, bin_height, QUAD_GREEN[0], QUAD_GREEN[1])
        # print('red')
        image[:,:,col_start:col_end] = color_bin_quadrant(image[:,:,col_start:col_end], COLOR_RED, bin_height, QUAD_RED[0], QUAD_RED[1])
        # print('white')
        image[:,:,col_start:col_end] = color_bin_quadrant(image[:, :, col_start:col_end], COLOR_WHITE, bin_height, QUAD_WHITE[0], QUAD_WHITE[1])
        # print(image[:,:,col_start:col_end])


    return image

def color_bin_quadrant(bin, color, bin_value, quadrant_bottom, quadrant_top, bin_height=const.MAT_SIZE_H, bin_width=const.BIN_PIXEL_WIDTH):

    if bin_value <= quadrant_bottom:
        pass #remain as zeros
    elif bin_value >= quadrant_top:
        bin[:,quadrant_bottom:quadrant_top,:] = color
    else:
        bin[:,quadrant_bottom:bin_value,:] = color

    return bin

import cv2 #slow, may try pickleizing baseline image
def baseline_image(height,width):
    # cv2.colormap
    np.ones((height,width, 3))
    pass


if __name__ == '__main__' :

    print('No main for ' + __file__)