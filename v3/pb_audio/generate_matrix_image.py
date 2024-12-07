import numpy as np
from pb_audio import constants as const

def generate_spectrogram_image(fft_bins, image_shape=(const.MAT_SIZE_H, const.MAT_SIZE_W, 3), bin_width=const.BIN_PIXEL_WIDTH):
    COLOR_WHITE = [255,255,255]
    COLOR_RED = [0,0,255]
    COLOR_GREEN = [0,255,0]
    COLOR_BLUE = [255,0,0]

    QUAD_WHITE=[0,const.MAT_SIZE_H//4] # TOP, BOTTOM
    QUAD_RED=[const.MAT_SIZE_H//4, const.MAT_SIZE_H//2]
    QUAD_GREEN=[const.MAT_SIZE_H//2, const.MAT_SIZE_H*3//4]
    QUAD_BLUE=[const.MAT_SIZE_H*3//4, const.MAT_SIZE_H]

    image = np.zeros(image_shape, dtype=np.uint8)

    bin_heights = (fft_bins * const.MAT_SIZE_H).astype(dtype=np.uint8)
    bin_pixel_height = const.MAT_SIZE_H - bin_heights #flip up-down since pixels start from upper left

    num_bins = fft_bins.shape[0]


    for i in range(num_bins):
        bin_height = bin_pixel_height[i]
        cols = (i*2,(i+1)*2)
        col_start = i*const.BIN_PIXEL_WIDTH
        col_end = col_start + const.BIN_PIXEL_WIDTH

        image[:,col_start:col_end] = color_bin_quadrant(image[:, col_start:col_end], COLOR_WHITE, bin_height, QUAD_WHITE[0], QUAD_WHITE[1])
        image[:,col_start:col_end] = color_bin_quadrant(image[:, col_start:col_end], COLOR_RED, bin_height, QUAD_RED[0], QUAD_RED[1])
        image[:,col_start:col_end] = color_bin_quadrant(image[:, col_start:col_end], COLOR_GREEN, bin_height, QUAD_GREEN[0], QUAD_GREEN[1])
        image[:,col_start:col_end] = color_bin_quadrant(image[:, col_start:col_end], COLOR_BLUE, bin_height, QUAD_BLUE[0], QUAD_BLUE[1])

    return image

def color_bin_quadrant(bin, color, bin_value, quadrant_top, quadrant_bottom, bin_height=const.MAT_SIZE_H, bin_width=const.BIN_PIXEL_WIDTH):

    if bin_value > quadrant_bottom:
        pass #remain as zeros
    if bin_value < quadrant_top:
        bin[quadrant_top:quadrant_bottom,:,:] = color
    else:
        bin[bin_value:quadrant_bottom,:,:] = color

    return bin