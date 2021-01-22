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
from usrmod import asynctlm
from usrmod import gui
from usrmod import shared_variables


#
# Telemetry Data Handler
#
async def tlm_handler(type):
    print("Starting UDP server for %s" % type)

    # initialize
    HOST = socket.gethostbyname(socket.gethostname())
    PORT = 0

    if type == 'smt':
        PORT = 49157
    elif type == 'pcm':
        PORT = 49158
    else :
        print('Error: Type of the telemeter is wrong!')
        sys.exit()

    # Get a reference to the event loop as we plan to use low-level APIs.
    loop = asyncio.get_running_loop()

    # One protocol instance will be created to serve all client requests.
    #transport, protocol = await loop.create_datagram_endpoint(
    await loop.create_datagram_endpoint(
        lambda: asynctlm.DatagramServerProtocol(type),
        local_addr=(HOST,PORT))

    #try:
    #    await asyncio.sleep(3600)  # Serve for 1 hour.
    #finally:
    #    transport.close()


#
# GUI Handler
#
def gui_handler():
    print('Starting GUI')
    
    app = wx.App()

    gui.frmMain()
    app.MainLoop()


#
# Main
#
if __name__ == "__main__":
    # Asyncio uses event loops to manage its operation
    loop = asyncio.get_event_loop()

    # multi-thread executor 
    executor = concurrent.futures.ThreadPoolExecutor()
    loop.set_default_executor(executor)

    # Create coroutines for three asyncronous tasks
    gathered_coroutines = asyncio.gather(
        tlm_handler("smt"),
        tlm_handler("pcm"),
        loop.run_in_executor(None, gui_handler))

    # This is the entry from synchronous to asynchronous code
    # It will block until the coroutine passed in has completed
    loop.run_until_complete(gathered_coroutines)
    
    # We're done with the event loop
    loop.close()

    print('... DES-QL quitted normally')
