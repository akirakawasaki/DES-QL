### Standard libraries
import asyncio
#import decimal
#import math
import socket
import sys
import concurrent.futures

### Third-party libraries
#import numpy as np
#import pandas as pd
import wx
#import wx.lib
#import wx.lib.plot as plt

#import matplotlib
#matplotlib.use('WxAgg')
#import matplotlib.pyplot as plt
#from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
#from matplotlib.figure import Figure

### Local libraries
from dir import asynctlm
from dir import gui
from dir import common


### TBREFAC.: TO BE MOVED TO ASYNCTLM.PY ###
async def tlm(tlm_type, internal_flags, tlm_latest_data):
    # print('Starting {} handlar...'.format(tlm_type))
    
    # initialize
    # HOST = ''
    # HOST = '192.168.1.4'
    HOST = '192.168.1.255'                                  # mac
    # HOST = socket.gethostbyname(socket.gethostname())       # windows / mac(debug)
    PORT = 0

    ### TBREFAC. ###
    if tlm_type == 'smt':
        PORT = 49157
    elif tlm_type == 'pcm':
        PORT = 49158
    else :
        print('Error: Type of the telemeter is wrong!')
        return

    # Get a reference to the event loop as we plan to use low-level APIs.
    loop = asyncio.get_running_loop()

    # One protocol instance will be created to serve all client requests.
    transport, protocol = await loop.create_datagram_endpoint(
                                    lambda: asynctlm.DatagramServerProtocol(tlm_type, tlm_latest_data),
                                    local_addr=(HOST,PORT))

    ### TBREFAC.: MUST FIGURE OUT HOW TO KILL THE TASK AFTER CLOSING GUI ###
    while internal_flags.GUI_TASK_IS_DONE != True:
        await asyncio.sleep(2)

    # try:
    #    await asyncio.sleep(3600)  # *Serve for 1 hour*
    # finally:
    #     transport.close()

    return (transport, protocol)



#
# Telemetry Data Handler (co-routine)
#
async def tlm_handler(internal_flags, tlm_latest_values):
    # print('Starting TLM handler...')

    gatherd_tasks = await asyncio.gather(
        tlm("smt", internal_flags, tlm_latest_values),
        tlm("pcm", internal_flags, tlm_latest_values))



#
# GUI Handler
#
def gui_handler(internal_flags, tlm_latest_data):
    print('Starting GUI...')
    
    app = wx.App()

    # launche main window
    gui.frmMain(internal_flags, tlm_latest_data)
    
    # handle event loop for GUI
    app.MainLoop()

    print('Closing GUI...')


#
# Main
#
if __name__ == "__main__":
    # Variables shared among threads
    internal_flags = common.InternalFlags()
    tlm_latest_data = common.TlmLatestData()

    # wrapper for tlm_handler co-routine
    def tlm_handler_wrapper(internal_flags, tlm_latest_data):
        asyncio.run(tlm_handler(internal_flags, tlm_latest_data))
        print('Closing TLM...')

    # run tlm_handler concurrently in other threads
    executor = concurrent.futures.ThreadPoolExecutor()
    executor.submit(tlm_handler_wrapper, internal_flags, tlm_latest_data)

    # launch GUI
    gui_handler(internal_flags, tlm_latest_data)

    # 
    # executor.shutdown(wait=True)
    # executor.shutdown(wait=True, cancel_futures=True)  # valid after Python 3.9

    print('DES-QL quitted normally ...')
