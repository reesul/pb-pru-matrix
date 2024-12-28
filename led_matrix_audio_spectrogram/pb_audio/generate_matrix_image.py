import numpy as np
import copy
from pb_audio import constants as const

VAL = const.IMAGE_MAX_VAL #TODO make arg

COLOR_WHITE = np.asarray([VAL,VAL,VAL])[..., np.newaxis, np.newaxis]
COLOR_RED = np.asarray([VAL,0,0])[..., np.newaxis, np.newaxis]
COLOR_GREEN = np.asarray([0,VAL,0])[...,np.newaxis, np.newaxis]
COLOR_BLUE = np.asarray([0,0,VAL])[...,np.newaxis, np.newaxis]

'''
Images are C,H,W ordered, so need some transpose before/after any opencv functions
origin (0,0) is bottom-left of image. OpenCV uses upper left
'''

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
def baseline_image(height,width, max_val=255, invert_map=True, norm_factor=const.IMAGE_NORM_FACTOR):
    '''
    Generate the background image
    Each column will look the same -- a gradient 
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
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    
    img = np.transpose(img, (2,0,1))#CHW from HWC
    img = (img / norm_factor).astype(np.uint8)
    img = img.copy(order='C')

    return img

def mask_baseline_image(baseline, fft_bins, bin_width=const.BIN_PIXEL_WIDTH):

    #create a boolean mask for which pixels to set to zero
    mask = np.full(baseline.shape[1:3], False)
    img = copy.copy(baseline)

    C,H,W = img.shape
    
    bin_pixel_height = (fft_bins * H).astype(dtype=np.uint8)
    num_bins = fft_bins.shape[0]

    for bin in range(0,num_bins):
        col = bin * bin_width
        col_mask = np.zeros((H))
        bin_height = bin_pixel_height[bin]

        col_mask[bin_height:] = True
        mask[:,col:col+bin_width] = col_mask[:,np.newaxis]
    
    #mask the pixels that shouldn't be on
    img[:, mask] = 0

    return img




if __name__ == '__main__' :

    print('No main for ' + __file__)