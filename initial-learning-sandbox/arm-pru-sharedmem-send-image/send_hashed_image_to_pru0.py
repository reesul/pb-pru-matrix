#!/usr/bin/python3

from time import sleep
import math
import numpy as np
import hashlib
import os, mmap
import cv2

PRU_ADDR = 0x4A300000
PRU_SHAREDMEM  = 0x10000
PRU_SHAREDMEM_SIZE = 12000
PRU_SHARED_MEM_HASH_LOC = PRU_ADDR + PRU_SHAREDMEM
PRU_SHARED_MEM_IMAGE_LOC = PRU_ADDR + PRU_SHAREDMEM + 16
IMAGE_OFFSET = 16 + 0

# fo = open("/dev/rpmsg_pru30", "wb", 0)
# fmem = open("/dev/mem", "wb", 0)
fmem = os.open('/dev/mem', os.O_RDWR | os.O_SYNC )
pru_shared_mem = mmap.mmap(fmem, PRU_SHAREDMEM_SIZE, offset=PRU_ADDR+PRU_SHAREDMEM)

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

def gen_test_image_file(filepath='Test_card.png'):
    image = cv2.imread(filepath)
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

i=0

test_image_base = gen_test_image_file()
 
while i<4096:
    print('send')
    
    # test_image = gen_test_image_column(rowswapper=0, active_col=i%64)
    test_image = test_image_base.copy()

    print(test_image)
    test_image[0,i%32,0] = 0xff
    test_image[2,i%32,63] = 0xff

    test_image[2,1,1] = 255
    test_image[2,16,32] = 255

    print(test_image[2,27:31,:])


    md5 = hashlib.md5(test_image).digest()
    print(md5)
    pru_shared_mem.seek(0)
    pru_shared_mem.write(md5)
    pru_shared_mem.seek(IMAGE_OFFSET)
    pru_shared_mem.write(test_image.tobytes())
    print(len(test_image.tobytes()))

    #fo.write(bytes([i]));
    print('sleep...')
    sleep(0.5)
    i+=1

