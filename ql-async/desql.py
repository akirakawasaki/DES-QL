### Standard libraries
import asyncio
# import concurrent.futures
import multiprocessing
# import queue
# import sys
# import time

### Third-party libraries
import wx

### Local libraries
# from src import asynctlm
from src import asynctlm2
from src import gui
# from src import common
    
#
#   Socket Communication (UDP/IP) Handler
#
def tlm_handler_wrapper(tlm_type, q_msg, q_data):
    print(f'MAIN: Invoking UDP Communication Handler Wrapper for {tlm_type}...')

    tlm = asynctlm2.TelemeterHandler(tlm_type, q_msg, q_data)

    asyncio.run( tlm.handler() )
    
    print('Closing TLM...')

# def tlm_handler_wrapper(internal_flags, tlm_latest_data):
#     print('MAIN: Invoking UDP Communication Handlers...')

#     # define wrapper for tlm_handler (co-routine)   ### T.B.REFAC.? ###
#     async def tlm_handlers(internal_flags, tlm_latest_values):
#         await asyncio.gather(
#             asynctlm.tlm_hundler("smt", internal_flags, tlm_latest_values),
#             asynctlm.tlm_hundler("pcm", internal_flags, tlm_latest_values))
        
#     asyncio.run(tlm_handlers(internal_flags, tlm_latest_data))
    
#     print('Closing TLM...')


#
#   Graphical User Interface Handler
#
def gui_handler(q_msg_smt, q_msg_pcm, q_data_smt, q_data_pcm):
    print('MAIN: Invoking GUI...')
    
    app = wx.App()

    # generate instance of the main window
    gui.frmMain(q_msg_smt, q_msg_pcm, q_data_smt, q_data_pcm)
    
    # launch event loop for GUI
    app.MainLoop()

    print('Closing GUI...')

# def gui_handler(internal_flags, tlm_latest_data):
#     print('MAIN: Invoking GUI...')
    
#     app = wx.App()

#     # generate instance of the main window
#     gui.frmMain(internal_flags, tlm_latest_data)
    
#     # launch event loop for GUI
#     app.MainLoop()

#     print('Closing GUI...')


#
#   Main
#
if __name__ == "__main__":
    # queues for smt
    q_msg_smt = multiprocessing.JoinableQueue()
    q_data_smt = multiprocessing.JoinableQueue()

    # queues for pcm
    q_msg_pcm = multiprocessing.JoinableQueue()
    q_data_pcm = multiprocessing.JoinableQueue()

    # launch UDP communication handler in another process for SMT
    p_smt = multiprocessing.Process(target=tlm_handler_wrapper, args=('smt', q_msg_smt, q_data_smt))
    p_smt.start()
    
    # launch UDP communication handler in another process for PCM
    p_pcm = multiprocessing.Process(target=tlm_handler_wrapper, args=('pcm', q_msg_pcm, q_data_pcm))
    p_pcm.start()

    # launch GUI handler in Main thread
    gui_handler(q_msg_smt, q_msg_pcm, q_data_smt, q_data_pcm)
    
    q_msg_smt.join()
    # q_data_smt.join()
    p_smt.join()

    q_msg_pcm.join()
    # q_data_smt.join()
    p_pcm.join()

    print('DES-QL quitted normally ...')

# if __name__ == "__main__":
#     # print(f"GIL switching interval: {sys.getswitchinterval()}")
#     # set GIL switching time to a vlaue other than the default [s]
#     # sys.setswitchinterval(0.001)
#     # print(f"GIL switching interval: {sys.getswitchinterval()}")
    
#     # initialize variables shared among threads
#     internal_flags = common.InternalFlags()
#     tlm_latest_data = common.TlmLatestData()
    
#     # launch UDP communication handler concurrently in sub-threads
#     executor = concurrent.futures.ThreadPoolExecutor()
#     # executor = concurrent.futures.ProcessPoolExecutor()
#     executor.submit(tlm_handler_wrapper, internal_flags, tlm_latest_data)

#     # launch GUI handler in Main thread
#     gui_handler(internal_flags, tlm_latest_data)
    
#     # time.sleep(3600)    # only for debug

#     # shut down UDP communication handler
#     executor.shutdown()

#     print('DES-QL quitted normally ...')





