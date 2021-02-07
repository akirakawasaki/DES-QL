import socket
#import struct
import sys
import time

import numpy as np


W2B = 2

NUM_OF_FRAMES = 8
LEN_HEADER  = 4
LEN_PAYLOAD = 64
LEN_MF = W2B * (LEN_HEADER + LEN_PAYLOAD) * NUM_OF_FRAMES       # 1088 bytes

# initialize
HOST = socket.gethostbyname(socket.gethostname())
PORT = 0
FILE_NAME = ''
N_LB = 0
SLP_TIME = 0

TLM_TYPE = sys.argv[1]
if TLM_TYPE == 'smt':
    PORT = 49157
    FILE_NAME = 'smt.bin'
    N_LB = 0                # smt 20210205 full sequence
    # N_LB = 67000            # smt 20201020 shortened sequence
    SLP_TIME = 0.01         # smt
    SLP_TIME = 0.04         # smt (safe mode)
elif TLM_TYPE == 'pcm':
    PORT = 49158
    FILE_NAME = 'pcm.bin'
    N_LB = 0                # pcm 20210205 full sequence
    # N_LB = 135000           # pcm 20201020 shortened sequence
    # SLP_TIME = 0.005        # pcm
    SLP_TIME = 0.02         # pcm (safe mode)
else :
    print("ERROR: TLM_TYPE is wrong!")
    sys.exit()

with open(FILE_NAME, 'rb') as f:
    NNN = 1
    while True:
        data_mf = f.read(LEN_MF)
        #print(len(data_mf))

        if len(data_mf) < LEN_MF:
            print('end of file')
            break

        # for debug
        '''
        for i in range(NUM_OF_FRAMES):
            adrs_tmp = i * W2B * (LEN_HEADER + LEN_PAYLOAD)

            # header
            print(f"message {i}-H: ",end='') 
            for k in range(W2B * LEN_HEADER): 
                print(hex(data_mf[k + adrs_tmp]).zfill(4), end=' ')
            print('')

            # payload
            for j in range(4):
                print(f"message {i}-{j}: ",end='')
                for k in range(W2B * int(LEN_PAYLOAD / 4)): 
                    print(hex(data_mf[k + adrs_tmp + W2B * (LEN_HEADER + j * int(LEN_PAYLOAD / 4))]).zfill(4), end=' ')
                print('')
        print('')
        '''

        #if NNN > 0:
        #if NNN > 67000:     # smt 20201020 shortened sequence
        #if NNN > 135000:    # pcm 20201020 shortened sequence
        #if NNN > 55000:     # smt 20201021 full sequence
        #if NNN > 112000:    # pcm 20201021 full sequence
        #if NNN > 600 and NNN < 1000:
        if NNN > N_LB:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.sendto(data_mf, (HOST, PORT))
                
            #if NNN % 1 == 0:
            if NNN % 100 == 0:
                print(f'data sent: NNN = {NNN}')

            time.sleep(SLP_TIME)    
            #time.sleep(0.01)    # pcm
            #time.sleep(0.02)    # smt
            #time.sleep(0.02)    # pcm safe mode
            #time.sleep(0.04)    # smt safe mode


        NNN += 1






