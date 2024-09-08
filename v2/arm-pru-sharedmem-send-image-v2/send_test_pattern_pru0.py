#!/usr/bin/python3

from time import sleep, time
import math
import numpy as np
import hashlib
import os, mmap

print('Loading opencv2.. this can take a moment.')
t1 = time()
import cv2
t2=time()
print(f'Took {t2-t1} s to load')

PRU_ADDR = 0x4A300000
PRU_SHAREDMEM  = 0x10000
PRU_SHAREDMEM_SIZE = 12000
PRU_SHARED_MEM_HASH_LOC = PRU_ADDR + PRU_SHAREDMEM
PRU_SHARED_MEM_IMAGE_LOC = PRU_ADDR + PRU_SHAREDMEM + 16
IMAGE_OFFSET = 16 + 0

FPS_TARGET=60
INTERFRAME_LATENCY = 1/FPS_TARGET

# fo = open("/dev/rpmsg_pru30", "wb", 0)
# fmem = open("/dev/mem", "wb", 0)
print('Open /dev/mem/')
fmem = os.open('/dev/mem', os.O_RDWR | os.O_SYNC )
print('Opened')
pru_shared_mem = mmap.mmap(fmem, PRU_SHAREDMEM_SIZE, offset=PRU_ADDR+PRU_SHAREDMEM)
print("mapped PRU memory")

def gen_test_image(shape=[3,32,64], rowswapper=0):
    image = np.zeros(shape, dtype=np.uint8)

    RED_IND = 0
    GREEN_IND = 1
    BLUE_IND = 2
    
    print(image.shape)
    for row in range(image.shape[1]):
        if (row+rowswapper) % 4 ==  0:
            # image[RED_IND,row,:] = 0xff
            # image[GREEN_IND,row,:] = 0
            # image[BLUE_IND,row,:] = 0xff
            image[RED_IND,row,:] = 0xff
            image[GREEN_IND,row,:] = 0
            image[BLUE_IND,row,:] = 0
            # image[GREEN_IND,row,:32] = 0xff
            # image[BLUE_IND,row,:32] = 0
            
        if (row+rowswapper) % 4 ==  1:
            # image[RED_IND,row,:] = 0x0
            # image[GREEN_IND,row,:] = 0
            # image[BLUE_IND,row,:] = 0xff
            image[RED_IND,row,:] = 0x0
            image[GREEN_IND,row,:] = 0
            image[BLUE_IND,row,:] = 0xff
            # image[RED_IND,row,:32] = 0xff
            # image[RED_IND,row,32:] = 0
            # image[GREEN_IND,row,:] = 0xff
            # image[BLUE_IND,row,32:] = 0xff
            # image[BLUE_IND,row,:32] = 0

        if (row+rowswapper) % 4 ==  2:
            # image[RED_IND,row,:] = 0x0
            # image[GREEN_IND,row,:] = 0xff
            # image[BLUE_IND,row,:] = 0xff
            image[RED_IND,row,:] = 0x0
            image[GREEN_IND,row,:] = 0xff
            image[BLUE_IND,row,:] = 0x0
            # image[RED_IND,row,:16] = 0xff
            # image[RED_IND,row,16:] = 0
            # image[GREEN_IND,row,:16] = 0x0
            # image[GREEN_IND,row,16:] = 0xff
            # image[BLUE_IND,row,:] = 0xff
        
        if (row+rowswapper) % 4 ==  3:
            # image[RED_IND,row,ac] = 0xff
            # image[GREEN_IND,row,:] = 0xff
            # image[BLUE_IND,row,:] = 0x0
            image[RED_IND,row,:] = 0xff
            image[GREEN_IND,row,:] = 0xff
            image[BLUE_IND,row,:] = 0xff


    return image

def gen_test_image_column(shape=[3,32,64], rowswapper=0, active_col=0):
    image = np.zeros(shape, dtype=np.uint8)

    RED_IND = 0
    GREEN_IND = 1
    BLUE_IND = 2
    
    print(image.shape)
    for row in range(image.shape[1]):
        
        # image[RED_IND,row,ac] = 0xff
        # image[GREEN_IND,row,:] = 0xff
        # image[BLUE_IND,row,:] = 0x0
        image[RED_IND,row,active_col] = 0xff
        # image[GREEN_IND,row,active_col] = 0xff
        # image[BLUE_IND,row,active_col] = 0xff


    return image

def read_test_image_file(filepath='Test_card.png'):
    image = cv2.imread(filepath)
    print('read image at %s' % filepath)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image = cv2.flip(image, 0)
    image = image.astype(np.uint8)
    print(image.shape)
    image = cv2.resize(image, (64,32))
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
        print(f'col bit counter {col_bit_counter}')
        col = image[:,:,j]
        print(col)
        bitmask = ( (2**8 - 1) )
        print('bitmask %s' % hex(bitmask))
        bitmask = bitmask >> (col_bit_counter)
        print('reduced bitmask %s' % hex(bitmask))

        new_col = col & bitmask
        col_bit_counter = ( col_bit_counter + 1 ) % bits

        print(new_col)
        image[:,:,j] = new_col

    return image


def shift_cols(image, cols=64):
    '''
    image in CHW format
    '''
    first_col = image[:,:,0]
    for i in range(cols-1):
        image[:,:,i] = image[:,:,i+1]

    image[:,:,-1] = first_col

    return image

i=0

print('Generate test image')
# test_image_base = read_test_image_file()
test_image_base = gen_white_image()
print('Generated.')
test_image_base = transform_test_image_colorbits(test_image_base)

# sleep(5)
 
NUM_ITER = 100000
print(f'Starting to send; do {NUM_ITER} sends')
t2 = time()
t1 = time()
test_image = test_image_base.copy()
for i in range(NUM_ITER):
    print('send')
    
    # test_image = gen_test_image_column(rowswapper=0, active_col=i%64)

    test_image = shift_cols(test_image)

    #start from static image each time
    # test_image = test_image_base.copy()
    #traveling pixel up the side
    # test_image[0,i%32,0] = 0xff
    # test_image[2,i%32,63] = 0xff

    #static pixel for localizing
    # test_image[2,1,1] = 255
    # test_image[2,16,32] = 255
    #test_image[2,27:30,:] = 255

    # print(test_image[:,0,:])


    md5 = hashlib.md5(test_image).digest()
    pru_shared_mem.seek(0)
    pru_shared_mem.write(md5)
    pru_shared_mem.seek(IMAGE_OFFSET)
    pru_shared_mem.write(test_image.tobytes())

    #fo.write(bytes([i]));
    print('sleep...')
    t2=time()
    t_sleep = INTERFRAME_LATENCY - (t2-t1)
    if (t_sleep > 0):
        sleep(t_sleep)
    t1=time()
    i+=1

