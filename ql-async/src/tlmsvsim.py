### Standard libraries
import socket
#import struct
import sys
import time

### Third-party libraries
# import numpy as np

### Local libraries
# import common


def tlmsvsim(dist_host, dist_port, file_path, n_lb, slp_time):
    # parameters of ISAS/JAXA telemeters
    W2B = 2                 # conversion coefficient from Word to Byte
    NUM_OF_FRAMES = 8       # number of Frames in a Major Frame
    LEN_HEADER  = 4         # length of Frame header in words
    LEN_PAYLOAD = 64        # length of Frame payload in words
    LEN_MF = W2B * (LEN_HEADER + LEN_PAYLOAD) * NUM_OF_FRAMES       # 1088 bytes

    with open(file_path, 'rb') as f:
        nnn = 1
        while True:
            data_mf = f.read(LEN_MF)
            #print(len(data_mf))

            if len(data_mf) < LEN_MF:
                print('end of file')
                break

            # for debug
            # for i in range(NUM_OF_FRAMES):
            #     adrs_tmp = i * W2B * (LEN_HEADER + LEN_PAYLOAD)

            #     # header
            #     print(f"message {i}-H: ",end='') 
            #     for k in range(W2B * LEN_HEADER): 
            #         print(hex(data_mf[k + adrs_tmp]).zfill(4), end=' ')
            #     print('')

            #     # payload
            #     for j in range(4):
            #         print(f"message {i}-{j}: ",end='')
            #         for k in range(W2B * int(LEN_PAYLOAD / 4)): 
            #             print(hex(data_mf[k + adrs_tmp + W2B * (LEN_HEADER + j * int(LEN_PAYLOAD / 4))]).zfill(4), end=' ')
            #         print('')
            # print('')
            
            if nnn > n_lb:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.sendto(data_mf, (dist_host, dist_port))
                    
                #if NNN % 1 == 0:
                if nnn % 100 == 0:
                    print(f'data sent: NNN = {nnn}')

                time.sleep(slp_time)    

            nnn += 1

if __name__ == "__main__":
    tlm_type = sys.argv[1]

    # error trap
    if tlm_type == '':
        print("ERROR: TLM_TYPE is NOT designated!")
        sys.exit()
    elif tlm_type != 'smt' and tlm_type != 'pcm':
        print("ERROR: TLM_TYPE is wrong!")
        sys.exit()

    dist_host = socket.gethostbyname(socket.gethostname())
    
    if tlm_type == 'smt':
        dist_port = 49157
        file_path = '../dat/' + 'smt.bin'
        n_lb = 0                # 20210205 full sequence
        # n_lb = 67000            # 20201020 shortened sequence
        slp_time = 0.01         # 
        # slp_time = 0.04         # safe mode
    elif tlm_type == 'pcm':
        dist_port = 49158
        file_path = '../dat/' + 'pcm.bin'
        n_lb = 0                # 20210205 full sequence
        # n_lb = 135000           # 20201020 shortened sequence
        slp_time = 0.005        # 
        # slp_time = 0.02         # safe mode

    tlmsvsim(dist_host, dist_port, file_path, n_lb, slp_time)



