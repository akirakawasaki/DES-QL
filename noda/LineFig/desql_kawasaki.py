# standard libraries
#import decimal
#import math
#import socket

# third-party libraries
#import numpy as np
#import pandas as pd

# local libraries
from usrmod import tlm


'''
Main Funcition
'''
def main():
    print('DES-QL Launched!')
    print('')

    ### STEP 0: initialize
    smt = tlm.tlm('smt')
    #smt = tlm.tlm('pcm')
    #pcm = tlm.tlm('pcm')

    df_ui = smt.df_mf

    NNN = 0
    while True:

        ### STEP 1: data receive
        smt.receive()

        # for debug
        '''
        print(f"From: {smt.addr}")
        print(f"To  : {socket.gethostbyname(smt.HOST)}")
        print('')
        '''

        '''
        for i in range(smt.NUM_OF_FRAMES):
            adrs_tmp = i * smt.W2B * (smt.LEN_HEADER + smt.LEN_PAYLOAD)
            # header
            print(f"message {i}-H: ",end='')
            for k in range(smt.W2B * smt.LEN_HEADER):
                print(hex(smt.data[k + adrs_tmp]).zfill(4), end=' ')
            print('')
            # payload
            for j in range(4):
                print(f"message {i}-{j}: ",end='')
                for k in range(smt.W2B * int(smt.LEN_PAYLOAD / 4)):
                    print(hex(smt.data[k + adrs_tmp + smt.W2B * (smt.LEN_HEADER + j * int(smt.LEN_PAYLOAD / 4))]).zfill(4), end=' ')
                print('')
        print('')
        '''

        #for k in range(smt.BUFSIZE):
        #    print(hex(smt.data[k]))

        #print(f"SUP_COM: {smt.SUP_COM}")
        #print('')


        ### STEP 2: data reshape
        smt.reshape()

        # for debug
        #print(smt.df)


        ### STEP 3: data save
        smt.append_to_file()


        ### STEP 4: data display
        if NNN % 10 == 0:
            df_ui = smt.append_to_dataframe(df_ui)


        #if NNN == 0:
        #if NNN >= 500:
        #if NNN >= 10000:    # smt 20201020 shortened sequence
        #if NNN >= 26000:    # pcm 20201020 shortened sequence
        if NNN >= 20000:    # smt 20201021 full sequence
        #if NNN >= 45000:    # pcm 20201021 full sequence
            break

        NNN += 1


    # for debug
    '''
    print(smt.uv2k(-1.0,'K')+273.15)
    print(smt.uv2k(1.0,'K')+273.15)
    print(smt.uv2k(20643.0,'K')+273.15)
    print(smt.uv2k(20645.0,'K')+273.15)
    print('')
    print(smt.k2uv(-1.0-273.15,'K'))
    print(smt.k2uv(1.0-273.15,'K'))
    print(smt.k2uv(500.0-273.15,'K'))
    '''

    ### STEP F: finalize
    # N/A


if __name__ == '__main__':
    main()
