### Standard libraries
import asyncio
import multiprocessing as mp
import queue
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
def telemeter_handler_wrapper(tlm_type, q_msg, q_datagram):
    print(f'MAIN: Invoking UDP Communication Handler Wrapper for {tlm_type}...')

    tlm = telemeter.TelemeterHandler(tlm_type, q_msg, q_datagram)

    # asyncio.run( tlm.ttelemeter_handler() )
    asyncio.run( tlm.telemeter_handler(), debug=True )      # for debug

    print(f'Closing {tlm_type}...')


#
#   Data Handler
#
def data_handler(tlm_type, q_datagram):
    print(f'MAIN: Invoking Data Hundler Wrapper for {tlm_type}...')
    
    tlm = data.DataHandler(tlm_type, q_datagram)

    # asyncio.run( tlm.tlm_handler() )
    asyncio.run( tlm.tlm_handler(), debug=True )      # for debug

    q_datagram.join()

    print(f'Closing {tlm_type} Data Handler...')


#
#   Graphical User Interface (GUI) Handler
#
def gui_handler(q_msg_smt, q_msg_pcm, q_data_smt, q_data_pcm):
    print('MAIN: Invoking GUI...')
    
    # create the wx app
    app = wx.App()

    # create the main window & show
    frame = gui.frmMain(q_msg_smt, q_msg_pcm, q_data_smt, q_data_pcm)
    frame.Show()

    # launch event loop for GUI <BLOCKING>
    app.MainLoop()

    # dump leftover queue tasks
    # - smt
    q_msg_smt.join()
    while True:
        try:
            q_data_smt.get_nowait()
        except queue.Empty:
            break
        else:
            q_data_smt.task_done()

    # - pcm
    q_msg_pcm.join()
    while True:
        try:
            q_data_pcm.get_nowait()
        except queue.Empty:
            break
        else:
            q_data_pcm.task_done()

    print('Closing GUI...')


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

    # generate FIFO queues for inter-process communication
    # - SMT/GUI
    q_msg_smt = mp.JoinableQueue()
    q_data_smt = mp.JoinableQueue()
    # - PCM/GUI
    q_msg_pcm = mp.JoinableQueue()
    q_data_pcm = mp.JoinableQueue()

    # launch UDP communication handler in other processes <NON-BLOCKING>
    # - smt
    p_smt = mp.Process(target=telemeter_handler_wrapper, args=('smt', q_msg_smt, q_data_smt))
    p_smt.start()
    # - pcm
    p_pcm = mp.Process(target=telemeter_handler_wrapper, args=('pcm', q_msg_pcm, q_data_pcm))
    p_pcm.start()

    # launch GUI handler in the main process/thread <BLOCKING>
    gui_handler(q_msg_smt, q_msg_pcm, q_data_smt, q_data_pcm)
    
    # end processing
    p_smt.join()    
    p_pcm.join()

    if mode == 'debug':
        sp_smt.terminate()
        sp_pcm.terminate()

    print('DES-QL quitted normally ...')




