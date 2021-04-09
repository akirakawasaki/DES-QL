### Standard libraries
import asyncio
import concurrent.futures
import sys
import time

### Third-party libraries
import wx

### Local libraries
from src import asynctlm
from src import gui
from src import common
    
#
#   Socket Communication (UDP/IP) Handler
#
def tlm_handler_wrapper(internal_flags, tlm_latest_data):
    print('MAIN: Invoking UDP Communication Handlers...')

    # define wrapper for tlm_handler (co-routine)   ### T.B.REFAC.? ###
    async def tlm_handlers(internal_flags, tlm_latest_values):
        await asyncio.gather(
            asynctlm.tlm_hundler("smt", internal_flags, tlm_latest_values),
            asynctlm.tlm_hundler("pcm", internal_flags, tlm_latest_values))
        
    asyncio.run(tlm_handlers(internal_flags, tlm_latest_data))
    
    print('Closing TLM...')

#
#   Graphical User Interface Handler
#
def gui_handler(internal_flags, tlm_latest_data):
    print('MAIN: Invoking GUI...')
    
    app = wx.App()

    # generate instance of the main window
    gui.frmMain(internal_flags, tlm_latest_data)
    
    # launch event loop for GUI
    app.MainLoop()

    print('Closing GUI...')

#
#   Main
#
if __name__ == "__main__":
    # print(f"GIL switching interval: {sys.getswitchinterval()}")
    # set GIL switching time to a vlaue other than the default [s]
    # sys.setswitchinterval(0.001)
    # print(f"GIL switching interval: {sys.getswitchinterval()}")
    
    # initialize variables shared among threads
    internal_flags = common.InternalFlags()
    tlm_latest_data = common.TlmLatestData()
    
    # launch UDP communication handler concurrently in sub-threads
    executor = concurrent.futures.ThreadPoolExecutor()
    # executor = concurrent.futures.ProcessPoolExecutor()
    executor.submit(tlm_handler_wrapper, internal_flags, tlm_latest_data)

    # launch GUI handler in Main thread
    gui_handler(internal_flags, tlm_latest_data)
    
    # time.sleep(3600)    # only for debug

    # shut down UDP communication handler
    executor.shutdown()

    print('DES-QL quitted normally ...')





