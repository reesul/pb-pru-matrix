#!/usr/bin/python3
# Reese Grimsley 2025, MIT license
# Purpose is generating images for audio-spectrum visualization
# First versions were just to show the bins' height for each column of the image. 
#   Was pretty slow to write each pixel manually
#   generate_spectrum_image()
# Second version generated a complete image, and used bin heights to 
#   mask unneeded parts of the image to black. This is WAY faster and allowed
#   a smaller bin-size per pixel
#   baseline_image() and mask_baseline_image()
# Future work could include other visualization or add some text-writing / BPM detection

import numpy as np
import copy
from pb_audio import constants as const

VAL = const.IMAGE_MAX_VAL

#some basic colors to start off of
COLOR_WHITE = np.asarray([VAL,VAL,VAL])[..., np.newaxis, np.newaxis]
COLOR_RED = np.asarray([VAL,0,0])[..., np.newaxis, np.newaxis]
COLOR_GREEN = np.asarray([0,VAL,0])[...,np.newaxis, np.newaxis]
COLOR_BLUE = np.asarray([0,0,VAL])[...,np.newaxis, np.newaxis]

'''
Images are C,H,W ordered, so need some transpose before/after any opencv functions
origin (0,0) is bottom-left of image. OpenCV uses upper left
Before sending to PRU via /dev/mem, image will need to be reordered to C style array
'''

def generate_spectrogram_image(fft_bins, image_shape=(const.MAT_NUM_CHANNEL, const.MAT_SIZE_H, const.MAT_SIZE_W), bin_width=const.BIN_PIXEL_WIDTH):
    '''
    Generate an image where the strength in the log-power log-frequency bin --> height of a vertical bar
    In ugly first version of this function, generate image one bin at a time. 
    May have multiple pixels per frequency bin (bin_width param)
    '''
    C,H,W = image_shape

    # separate image into 4 sections by height and color each differently
    QUAD_BLUE =  [0,H//4] # BOTTOM, TOP
    QUAD_GREEN = [H//4, H//2]
    QUAD_RED =   [H//2, H*3//4]
    QUAD_WHITE = [H*3//4, H]


    image = np.zeros(image_shape, dtype=np.uint8)

    bin_pixel_height = (fft_bins * H).astype(dtype=np.uint8)

    num_bins = fft_bins.shape[0]

    for i in range(num_bins):
        bin_height = bin_pixel_height[i]

        col_start = i * bin_width
        col_end = col_start + bin_width

        image[:,:,col_start:col_end] = color_bin_quadrant(image[:,:,col_start:col_end], COLOR_BLUE, bin_height, QUAD_BLUE[0], QUAD_BLUE[1])

        image[:,:,col_start:col_end] = color_bin_quadrant(image[:,:,col_start:col_end], COLOR_GREEN, bin_height, QUAD_GREEN[0], QUAD_GREEN[1])

        image[:,:,col_start:col_end] = color_bin_quadrant(image[:,:,col_start:col_end], COLOR_RED, bin_height, QUAD_RED[0], QUAD_RED[1])

        image[:,:,col_start:col_end] = color_bin_quadrant(image[:, :, col_start:col_end], COLOR_WHITE, bin_height, QUAD_WHITE[0], QUAD_WHITE[1])

    return image

def color_bin_quadrant(bin, color, bin_value, quadrant_bottom, quadrant_top):
    '''
    Not really a quadrant, more like a horizontal slice of the image
    bins are CHW formatted images
    We'll try to color as high within this section of the image as the bin height/power can fit.. maybe nothing, maybe partial, maybe full. 
    Everything here will be the same color, or left as black/zeros
    '''
    if bin_value <= quadrant_bottom:
        pass #remain as zeros
    elif bin_value >= quadrant_top:
        bin[:,quadrant_bottom:quadrant_top,:] = color
    else:
        bin[:,quadrant_bottom:bin_value,:] = color

    return bin


import cv2 #slow, may try pickleizing baseline image? 
def baseline_image(height,width, max_val=255, invert_map=True, norm_factor=const.IMAGE_NORM_FACTOR):
    '''
    Generate the background image
    Each column will look the same -- a gradient per opencv colormap
    '''
    grey_img = np.ones((height, width), dtype=np.uint8)
    if invert_map is True:
        col_values = np.asarray(range(height, 0, -1)) * (max_val / height)
    else:        
        col_values = np.asarray(range(height)) * (max_val / height)
    for j in range(width):
        grey_img[:,j] = col_values
    
    #HOT (INV), JET (meh, no INV), RAINBOW (INV), HSV (INV or no INV)
    img = cv2.applyColorMap(grey_img, cv2.COLORMAP_HSV)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) #default is BGR in opencv2... dummies

    
    img = np.transpose(img, (2,0,1))#CHW from HWC -- consistent with PRU LED-matrix driver
    img = (img / norm_factor).astype(np.uint8) # normalize to decrease overall brightness; based on const
    img = img.copy(order='C') # To convert img to byte-buffer, needs C-ordering

    return img

def mask_baseline_image(baseline, fft_bins, bin_width=const.BIN_PIXEL_WIDTH):
    '''
    Mask out  pixels to zero/black to match the power for each bin
    Does not change the baseline 
    '''
    #create a boolean mask for which pixels to set to zero
    mask = np.full(baseline.shape[1:3], False)
    img = copy.copy(baseline) #don't want to overwrite anything in the original

    C,H,W = img.shape
    
    # normalize FFT bin power to height of the image
    bin_pixel_height = (fft_bins * H).astype(dtype=np.uint8)
    num_bins = fft_bins.shape[0]

    for bin in range(0,num_bins):
        col = bin * bin_width
        #may have multiple columns; make one mask here
        col_mask = np.zeros((H))
        bin_height = bin_pixel_height[bin]

        col_mask[bin_height:] = True
        #Add the mask for this bin to all associated columns in the mask
        mask[:,col:col+bin_width] = col_mask[:,np.newaxis]
    
    #mask out pixels that shouldn't be on
    img[:, mask] = 0

    return img


if __name__ == '__main__' :

    print('No main for ' + __file__)