### Standard libraries
# import glob
import sys
import os

### Third-party libraries
import numpy as np
import pandas as pd

### Local libraries
# n/a

'''
Settings
'''
__FNAME_SMT = 'data_smt.csv'
__FNAME_PCM = 'data_pcm.csv'


def postprocess(src_dir) -> None:
    src_path_smt = os.path.join(src_dir, __FNAME_SMT)
    print(f'Source path (SMT): {src_path_smt}')
    df_smt = pd.read_csv(src_path_smt, header=0)
    
    src_path_pcm = os.path.join(src_dir, __FNAME_PCM)
    print(f'Source path (PCM): {src_path_pcm}')
    df_pcm = pd.read_csv(src_path_pcm, header=0)

    


if __name__ == "__main__":
    
    try:
        src_dir_tail = sys.argv[1]
    except IndexError:
        print("ERROR: DATE_TIME is NOT designated!")
        print("Command 'python postprocess.py DATE_TIME'")
        sys.exit()

    src_dir_head = os.getcwd()
    src_dir = os.path.join(src_dir_head, src_dir_tail)

    print(f'Source directory: {src_dir}')

    postprocess(src_dir)



