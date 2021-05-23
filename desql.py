### Standard libraries
import asyncio
import concurrent.futures
import multiprocessing as mp
import pandas as pd
import queue                        # Only for exception handling
import socket
import subprocess
import sys

### Third-party libraries
import wx

### Local libraries
from src import telemeter
from src import data
from src import gui
# from src import common


#
#   Socket Communication (UDP/IP) Handler
#
def telemeter_handler_wrapper(tlm_type, q_msg, q_dgram):
    print(f'MAIN: Invoking UDP Communication Handler Wrapper for {tlm_type}...')

    # datagram server
    # HOST = '172.20.140.255'                                # mac
    HOST = socket.gethostbyname(socket.gethostname())      # windows / mac(debug)
    PORT =      60142 if (tlm_type == 'smt') \
           else 60140

    tlm = telemeter.TelemeterHandler(tlm_type, HOST, PORT, q_msg, q_dgram)

    asyncio.run( tlm.telemeter_handler() )
    # asyncio.run( tlm.telemeter_handler(), debug=True )      # for debug

    print(f'MAIN: {tlm_type} Communication Handler Closed.')


#
#   Data Handler
#
def data_handler_wrapper(tlm_type, g_state, g_lval, q_dgram):
    print(f'MAIN: Invoking Data Handler Wrapper for {tlm_type}...')
    
    tlm = data.DataHandler(tlm_type, g_state, g_lval, q_dgram)

    asyncio.run( tlm.data_handler() )
    # asyncio.run( tlm.data_handler(), debug=True )      # for debug

    # wait for queue to be fully processed
    # q_dgram.join()  

    print(f'MAIN: {tlm_type} Data Handler Closed.')


#
#   Graphical User Interface (GUI) Handler
#
def gui_handler(g_state, g_lval, q_msg_smt, q_msg_pcm):
    print('MAIN: Invoking GUI...')
    
    # create the wx app
    app = wx.App()

    # create the main window & show
    frame = gui.frmMain(g_state, g_lval)
    frame.Show()

    # launch event loop for GUI <BLOCKING>
    app.MainLoop()

    # quit telemeter handlers
    q_msg_smt.put_nowait('stop')
    q_msg_pcm.put_nowait('stop')

    # quit data handlers
    g_state['smt']['Tlm_Server_Is_Active'] == False
    g_state['pcm']['Tlm_Server_Is_Active'] == False

    # wait
    q_msg_smt.join()
    q_msg_pcm.join()

    print('MAIN: GUI Closed.')


#
#   Main
#
if __name__ == "__main__":
    mp.freeze_support()                     # for generation of executable on Windows
    mp.set_start_method('spawn', True)      
    
    if len(sys.argv) == 2:
        mode = sys.argv[1]
    else:
        mode = None

    if mode == 'debug':
        print('----- DEBUG MODE -----')
        sp_smt = subprocess.Popen(['python', './tlmsvsim.py', 'smt'], stdout=subprocess.DEVNULL)
        sp_pcm = subprocess.Popen(['python', './tlmsvsim.py', 'pcm'], stdout=subprocess.DEVNULL)

    g_state = { 'smt': {'Tlm_Server_Is_Active': True}, 
                'pcm': {'Tlm_Server_Is_Active': True}   }
    # g_lval = {  'smt': {}, 
    #             'pcm': {}   }
    g_lval = {  'smt': pd.DataFrame(), 
                'pcm': pd.DataFrame()   }

    # generate FIFO queues for inter-process communication
    # - From SMT SERVER To SMT DATA HANDLER
    q_dgram_smt = mp.JoinableQueue()
    # - From GUI To SMT SERVER
    q_msg_smt = mp.JoinableQueue()
    # - From PCM SERVER To SMT DATA HANDLER
    q_dgram_pcm = mp.JoinableQueue()
    # - From GUI To SMT SERVER
    q_msg_pcm = mp.JoinableQueue()

    # launch data handler in other threads concurrently
    executor = concurrent.futures.ThreadPoolExecutor()
    future_smt = executor.submit(data_handler_wrapper, 'smt', g_state, g_lval, q_dgram_smt)
    future_pcm = executor.submit(data_handler_wrapper, 'pcm', g_state, g_lval, q_dgram_pcm)

    # launch UDP communication handler in other processes <NON-BLOCKING>
    # - smt
    p_smt = mp.Process(target=telemeter_handler_wrapper, args=('smt', q_msg_smt, q_dgram_smt))
    p_smt.start()
    # - pcm
    p_pcm = mp.Process(target=telemeter_handler_wrapper, args=('pcm', q_msg_pcm, q_dgram_pcm))
    p_pcm.start()

    # launch GUI handler in the main process/thread <BLOCKING>
    gui_handler(g_state, g_lval, q_msg_smt, q_msg_pcm)
    
    # dump leftover queue tasks
    # - smt
    # while True:
    #     try:
    #         _ = q_dgram_smt.get_nowait()
    #     except queue.Empty:
    #         break
        
    #     q_dgram_smt.task_done()

    # - pcm
    # while True:
    #     try:
    #         _ = q_dgram_pcm.get_nowait()
    #     except queue.Empty:
    #         break

    #     q_dgram_pcm.task_done()
    
    # wait UDP communication handler
    p_smt.join()    
    p_pcm.join()

    # quit data handlers
    executor.shutdown(wait=True, cancel_futures=True)

    if mode == 'debug':
        sp_smt.terminate()
        sp_pcm.terminate()

    print('DES-QL quitted normally ...')




