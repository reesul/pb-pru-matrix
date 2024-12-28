#!/usr/bin/python3

from time import sleep
import math
import numpy as np
import hashlib

PRU_ADDR = 0x4A300000
PRU_SHAREDMEM  = 0x10000
PRU_SHAREDMEM_SIZE = 12000
PRU_SHARED_MEM_HASH_LOC = PRU_ADDR + PRU_SHAREDMEM
PRU_SHARED_MEM_IMAGE_LOC = PRU_ADDR + PRU_SHAREDMEM + 16

fo = open("/dev/rpmsg_pru30", "wb", 0)
fmem = open("/dev/mem", "wb", 0)

def gen_test_image(shape=[3,32,64]):
    image = np.zeros(shape, dtype=np.uint8)

    RED_IND = 0
    GREEN_IND = 1
    BLUE_IND = 2

    for row in len(image.shape[2]):

        if row % 4 ==  0:
            image[RED_IND,i,:] = 0xff
            image[GREEN_IND,i,:32] = 0xff
            image[GREEN_IND,i,32:] = 0

            
        if row % 4 ==  1:
            image[RED_IND,i,:32] = 0xff
            image[RED_IND,i,32:] = 0
            image[GREEN_IND,i,:] = 0xff

        if row % 4 ==  2:
            image[RED_IND,i,:16] = 0xff
            image[RED_IND,i,16:] = 0
            image[GREEN_IND,i,:16] = 0x0
            image[GREEN_IND,i,16:] = 0xff
            image[BLUE_IND,i,:] = 0xff

    return image

i=0
while i<128:
    print('send')
    
    test_image = gen_test_image()
    md5 = hashlib.md5(test_image) + i
    fmem.seek(PRU_SHARED_MEM_HASH_LOC)
    fmem.write(md5.digest())
    fmem.seek(PRU_SHARED_MEM_IMAGE_LOC)
    fmem.write(test_image.tobytes())

    fo.write(bytes([i]));
    print('sleep...')
    sleep(3)

fake_tiny_image = [[[1,2,3], [4,5,6], [7,8,9], [10,11,12]], [[13,14,15], [16,17,18], [19,20,21],[22,23,24]]]
fake_tiny_image = np.asarray(fake_tiny_image, dtype=np.uint8)
# Close opened file
fo.close()