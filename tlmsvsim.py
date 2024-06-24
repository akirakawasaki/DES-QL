### Standard libraries
import socket
import sys
import time

### Third-party libraries
# n/a

### Local libraries
from src import common


def tlmsvsim(dist_host, dist_port, file_path, slp_time, start_time):
    # parameters of ISAS/JAXA telemeters
    NUM_OF_FRAMES = 8       # number of Frames in a Major Frame
    LEN_HEADER  = 4         # length of Frame header in words
    LEN_PAYLOAD = 64        # length of Frame payload in words
    BPW = 2                 # bytes per word
    LEN_MF = BPW * (LEN_HEADER + LEN_PAYLOAD) * NUM_OF_FRAMES       # 1088 bytes

    with open(file_path, 'rb') as f:
        nnn = 0
        while True:
            data_mf = f.read(LEN_MF)
            #print(len(data_mf))

            if len(data_mf) < LEN_MF:
                print('end of file')
                break


            # byte index of the head of the frame (without header)
            byte_idx_head = BPW * LEN_HEADER

            # calc byte index of datum within the datagram
            byte_idx =  byte_idx_head + BPW * (-4)

            byte_length = BPW * (3)
            byte_string = data_mf[byte_idx:byte_idx+byte_length]

            decoded_value =   (byte_string[1] & 0x0F) * 10  * 3600  \
                            + (byte_string[2] >> 4  ) * 1   * 3600  \
                            + (byte_string[2] & 0x0F) * 10  * 60    \
                            + (byte_string[3] >> 4  ) * 1   * 60    \
                            + (byte_string[3] & 0x0F) * 10          \
                            + (byte_string[4] >> 4  ) * 1           \
                            + (byte_string[4] & 0x0F) * 100 * 0.001 \
                            + (byte_string[5] >> 4  ) * 10  * 0.001 \
                            + (byte_string[5] & 0x0F) * 1   * 0.001

            gse_time = decoded_value
            
            if (gse_time >= start_time) and (gse_time < 86400.0):
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.sendto(data_mf, (dist_host, dist_port))
                    
                #if NNN % 1 == 0:
                # if nnn % 100 == 0:
                if nnn % 1000 == 0:
                    print(f'data sent: gse time = {gse_time}')

                time.sleep(slp_time)    

                nnn += 1


if __name__ == "__main__":

    try:
        tlm_type = sys.argv[1]
    except IndexError:
        print("ERROR: TLM_TYPE is NOT designated!")
        sys.exit()

    try:
        start_time = float(sys.argv[2])
    except IndexError:
        print("ERROR: START_TIME is NOT designated!")
        sys.exit()

    dist_host = socket.gethostbyname(socket.gethostname())
    
    if tlm_type == 'smt':
        dist_port = common.CommonConstants.DIST_PORT_SMT
        # dist_port = 60142
        # dist_port = 49157       # old

        # slp_time = 0.005        # 
        slp_time = 0.01         # real-time mode
        # slp_time = 0.04         # safe mode

        # n_lb = 0                # 20210205 full sequence
        # n_lb = 67000            # 20201020 shortened sequence
    elif tlm_type == 'pcm':
        dist_port = common.CommonConstants.DIST_PORT_PCM
        # dist_port = 60140
        # dist_port = 49158       # old

        # slp_time = 0.0025       # 
        slp_time = 0.005        # real-time mode
        # slp_time = 0.02         # safe mode

        # n_lb = 0                # 20210205 full sequence
        # n_lb = 135000           # 20201020 shortened sequence
    else:
        print("ERROR: TLM_TYPE is wrong!")
        sys.exit()

    file_path = './dat-in/' + tlm_type + '.bin'

    tlmsvsim(dist_host, dist_port, file_path, 0.8 * slp_time, start_time)



