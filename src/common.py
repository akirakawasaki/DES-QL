### Standard libraries
# n/a

### Third-party libraries
import pandas as pd

### Local libraries
# n/a


#
# Common Constants
#
class CommonConstants:
    W2B = 2                     # conversion coefficient from Word to Byte
    
    NUM_OF_FRAMES = 8           # number of Frames in a Major Frame
    LEN_HEADER  = 4             # length of Frame header in words
    LEN_PAYLOAD = 64            # length of Frame payload in words

    # length of a Major Frame
    LEN_MF = W2B * NUM_OF_FRAMES * (LEN_HEADER + LEN_PAYLOAD)       # 1088 bytes

    DIST_PORT_SMT = 52011       # port number to receive SMT datagram
    DIST_PORT_PCM = 52010       # port number to receive PCM datagram

#
# Shared Variables
#
class TlmLatestData:
    def __init__(self):
        self.df_smt = pd.DataFrame()
        self.df_pcm = pd.DataFrame()

class InternalFlags:
    def __init__(self):
        self.DESQL_SHOULD_QUIT = False
        self.GUI_TASK_IS_DONE = False
        self.FILE_SAVE_IS_ACTIVE = False

        