#!/usr/bin/python3

from time import sleep, time
import math
import numpy as np
import hashlib
import os, mmap

import pb_audio.constants as const


MD5SUM_SIZE = 16

PRU_ADDR = 0x4A300000
PRU_SHAREDMEM  = 0x10000
PRU_SHAREDMEM_SIZE = 12000

PRU_SHARED_MEM_HASH_LOC = PRU_ADDR + PRU_SHAREDMEM
PRU_SHARED_MEM_IMAGE_LOC = PRU_ADDR + PRU_SHAREDMEM + MD5SUM_SIZE
EXTRA_OFFSET = 0
IMAGE_OFFSET = MD5SUM_SIZE + EXTRA_OFFSET

FPS_TARGET=30 # 24 #30 # 60
INTERFRAME_LATENCY = 1/FPS_TARGET


def read_test_image_file(filepath='Test_card.png'):
    print('Loading opencv2.. this can take a moment.')
    t1 = time()
    import cv2
    t2=time()
    print(f'Took {t2-t1} s to load')

    image = cv2.imread(filepath)
    print('read image at %s' % filepath)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image = cv2.flip(image, 0)
    image = image.astype(np.uint8)
    print(image.shape)
    image = cv2.resize(image, (64,32), interpolation=cv2.INTER_LINEAR)
    print(image.shape)
    image = np.transpose(image, (2,0,1))#CHW from HWC
    
    print(image.shape)
    image = image.copy(order='C')
    return image


def gen_white_image():
    print('generate a plain white test pattern')
    image = np.zeros((3,32,64), dtype=np.uint8)
    image[:,:,:] = 255
    print(image.shape)
    
    image = image.copy(order='C') #export for C style indexing so I can read w/i PRU
    return image

def transform_test_image_colorbits(image, cols=64, bits=8):
    '''
    Each column will have reduced color bits in chunks of 8 cols.
    Leftmost has all bits possible, right most has none
    Secondf rom left has lower 7 bits enabled. Next is 6, and so on
    
    '''

    col_bit_counter = 0
    for j in range(cols):
        col = image[:,:,j]
        bitmask = ( (2**8 - 1) )
        bitmask = bitmask >> (col_bit_counter)

        new_col = col & bitmask
        col_bit_counter = ( col_bit_counter + 1 ) % bits

        image[:,:,j] = new_col

    return image


def shift_image_cols(image, cols=64):
    '''
    image in CHW format
    '''
    first_col = image[:,:,0]
    for i in range(cols-1):
        image[:,:,i] = image[:,:,i+1]

    image[:,:,-1] = first_col

    return image

def open_pru_mem():

    print('Open /dev/mem/... requires SUDO')
    fmem = os.open('/dev/mem', os.O_RDWR | os.O_SYNC )
    print('Opened')
    pru_shared_mem = mmap.mmap(fmem, PRU_SHAREDMEM_SIZE, offset=PRU_ADDR+PRU_SHAREDMEM)
    return pru_shared_mem

def send_image_to_pru(pru_shared_mem, image):

    md5 = hashlib.md5(image).digest()

    pru_shared_mem.seek(0)
    pru_shared_mem.write(md5)

    pru_shared_mem.seek(IMAGE_OFFSET)
    pru_shared_mem.write(image.tobytes())


def _test_pru_send():

    pru_shared_mem = open_pru_mem()
    print("mapped PRU memory")
    i=0

    print('Generate test image')
    test_image_base = read_test_image_file()
    print('Generated.')

    
    NUM_ITER = 100000
    print(f'Starting to send; do {NUM_ITER} sends')
    t2 = time()
    t1 = time()
    test_image = test_image_base.copy()
    for i in range(NUM_ITER):
        print('send')
        

        test_image = shift_image_cols(test_image)

        
        ###traveling pixel up the side
        test_image[0,i%32,0] = 0x0
        # test_image[2,i%32,63] = 0xff

        send_image_to_pru(pru_shared_mem, test_image)

        t2=time()
        t_sleep = INTERFRAME_LATENCY - (t2-t1)
        if (t_sleep > 0):
            sleep(t_sleep)
        t1=time()
        i+=1

if __name__ == '__main__':
    _test_pru_send()