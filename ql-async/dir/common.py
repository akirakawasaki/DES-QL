### Standard libraries
# n/a

### Third-party libraries
import pandas as pd

### Local libraries
# n/a


#
# Common Constants
#


#
# Shared Variables
#
class TlmLatestData:
    def __init__(self):
        self.df_smt = pd.DataFrame()
        self.df_pcm = pd.DataFrame()

class InternalFlags:
    def __init__(self):
        self.GUI_TASK_IS_DONE = False
        self.FILE_SAVE_IS_ACTIVE = False

        