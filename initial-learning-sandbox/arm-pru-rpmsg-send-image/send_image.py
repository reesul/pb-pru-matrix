import numpy as np
import cv as cv
import os, sys, time

pru_file = '/dev/rpmsg_pru30'

MAGIC_VALUE = b'\xde\xad\xbe\xef'

HEIGHT=32
WIDTH=64

def setup_image(path='Test_card.png'):

    img_og = cv2.imread(path)

    img = cv2.resize(img_og, (HEIGHT, WIDTH), interpolation=cv.INTER_LINEAR)
    img = img.astype(np.uint8)

    #shuffle to RGB
    img[:,:, 0], img[:,:, 2] = img[:,:, 2], img[:,:, 0]
    #shuffle to from HWC to CHW
    img = img.transpose(2,0,1)

    return img

def send_image(img):
    '''
    Assume IMG to be in BGR
    '''
    with open(pru_file, 'wb') as pru_pipe:
        for r in range(HEIGHT//2):
            data = bytearray(b'')
            data.append(MAGIC_VALUE)
            data.append(bytes(int(r))
            row_lower = img[:,r,:]
            data.append(row_upper.tobytes)
            row_upper = img[:,r+HEIGHT//2,:]
            data.append(row_upper.tobytes)

            pru_pipe.write(data)



if __name__ == '__main__':
    print('start')
    img = setup_image()

    send_image

