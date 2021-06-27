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

    print(f'MAIN: {tlm_type} Data Handler Closed.')


#
#   Graphical User Interface (GUI) Handler
#
def gui_handler(g_state, g_lval, q_msg_smt, q_msg_pcm):
    print('MAIN: Invoking GUI...')
    
    # create wx app
    app = wx.App()

    # create main window & show
    frame = gui.frmMain(g_state, g_lval)
    # frame = gui.frmMain(g_state, g_lval, q_msg_smt, q_msg_pcm)
    frame.Show()

    # launch event loop for GUI <BLOCKING>
    app.MainLoop()


    ### After frmMain Closed ###

    # quit telemeter handlers
    q_msg_smt.put_nowait('stop')
    q_msg_pcm.put_nowait('stop')

    # block until the queue tasks processed
    q_msg_smt.join()
    q_msg_pcm.join()

    # quit data handlers
    g_state['smt']['Tlm_Server_Is_Active'] = False
    g_state['pcm']['Tlm_Server_Is_Active'] = False

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

    ### define
    g_state = { 'smt': {'Tlm_Server_Is_Active': True, 'Data_Save_Is_Active': False}, 
                'pcm': {'Tlm_Server_Is_Active': True, 'Data_Save_Is_Active': False},
                'last_error': 0 }
    g_lval = {  'smt': {}, 
                'pcm': {}   }

    # generate FIFO queues for inter-process communication
    # - control message
    q_msg_smt = mp.JoinableQueue()          # From GUI To SMT Server
    q_msg_pcm = mp.JoinableQueue()          # From GUI To SMT Server
    # - datagram
    q_dgram_smt = mp.JoinableQueue()        # From SMT Server To SMT Data Handler
    q_dgram_pcm = mp.JoinableQueue()        # From PCM Server To SMT Data Handler

    ### Launch handlers
    # data handler in other threads concurrently <NON-BLOCKING>
    executor = concurrent.futures.ThreadPoolExecutor()
    future_smt = executor.submit(data_handler_wrapper, 'smt', g_state, g_lval, q_dgram_smt)
    future_pcm = executor.submit(data_handler_wrapper, 'pcm', g_state, g_lval, q_dgram_pcm)

    # UDP communication handler in other processes <NON-BLOCKING>
    # - smt
    p_smt = mp.Process(target=telemeter_handler_wrapper, args=('smt', q_msg_smt, q_dgram_smt))
    p_smt.start()
    # - pcm
    p_pcm = mp.Process(target=telemeter_handler_wrapper, args=('pcm', q_msg_pcm, q_dgram_pcm))
    p_pcm.start()

    # GUI handler in the main process/thread <BLOCKING>
    gui_handler(g_state, g_lval, q_msg_smt, q_msg_pcm)

    ### Wait for GUI to Be Closed ###

    # wait for UDP communication handler
    p_smt.join()    
    p_pcm.join()

    print('MAIN: Processes joined.')

    # wait for futures
    while True:
        if future_smt.done() and future_pcm.done(): break

    # quit data handlers
    executor.shutdown(wait=True, cancel_futures=False)

    # for debug
    print('MAIN: Executor shut down.')

    if mode == 'debug':
        sp_smt.terminate()
        sp_pcm.terminate()

    print('DES-QL quitted normally ...')




