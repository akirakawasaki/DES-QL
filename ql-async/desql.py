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


#
# Telemetry Data Handler
#
async def tlm_handler(tlm_type, tlm_latest_values):
    print("Starting UDP server for %s" % tlm_type)

    # initialize
    HOST = socket.gethostbyname(socket.gethostname())
    PORT = 0

    if tlm_type == 'smt':
        PORT = 49157
    elif tlm_type == 'pcm':
        PORT = 49158
    else :
        print('Error: Type of the telemeter is wrong!')
        sys.exit()

    # Get a reference to the event loop as we plan to use low-level APIs.
    loop = asyncio.get_running_loop()

    # One protocol instance will be created to serve all client requests.
    transport, protocol = await loop.create_datagram_endpoint(
                                    lambda: asynctlm.DatagramServerProtocol(tlm_type, tlm_latest_values),
                                    local_addr=(HOST,PORT))

    return (transport, protocol)

    #try:
    #    await asyncio.sleep(3600)  # Serve for 1 hour.
    #finally:
    #    transport.close()


#
# GUI Handler
#
def gui_handler(latest_values):
    print('Starting GUI...')
    
    app = wx.App()

    # launche main window
    gui.frmMain(latest_values)
    
    # handle event loop for GUI
    app.MainLoop()


#
# Main
#
if __name__ == "__main__":
    # Variables shared among threads
    latest_values = common.LatestValues()
    
    # Asyncio uses event loops to manage its operation
    loop = asyncio.get_event_loop()

    # multi-thread executor 
    #executor = concurrent.futures.ThreadPoolExecutor()
    #loop.set_default_executor(executor)

    # Create coroutines for three asyncronous tasks
    # gathered_coroutines = asyncio.gather(
    #     tlm_handler("smt", latest_values),
    #     tlm_handler("pcm", latest_values),
    #     loop.run_in_executor(None, gui_handler, latest_values))
    
    # for debug of TLM handler
    gathered_coroutines = asyncio.gather(
        tlm_handler("smt", latest_values),
        tlm_handler("pcm", latest_values))
    loop.run_until_complete(gathered_coroutines)

    # for debug of GUI handler
    gui_handler(latest_values)

    # This is the entry from synchronous to asynchronous code
    # It will block until the coroutine passed in has completed
    # loop.run_until_complete(gathered_coroutines)
    
    # We're done with the event loop
    loop.close()

    print('... DES-QL quitted normally')
