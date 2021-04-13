### Standard libraries
import asyncio
import multiprocessing

### Third-party libraries
import wx

### Local libraries
from src import asynctlm
from src import gui
# from src import common


#
#   Socket Communication (UDP/IP) Handler
#
def tlm_handler_wrapper(tlm_type, q_msg, q_data):
    print(f'MAIN: Invoking UDP Communication Handler Wrapper for {tlm_type}...')

    tlm = asynctlm.TelemeterHandler(tlm_type, q_msg, q_data)

    asyncio.run( tlm.tlm_handler(), debug=True )
    # asyncio.run( tlm.tlm_handler() )
    
    print('Closing TLM...')


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

    print('Closing GUI...')


#
#   Main
#
if __name__ == "__main__":
    # generate FIFO queues for inter-process communication
    # - SMT/GUI
    q_msg_smt = multiprocessing.JoinableQueue()
    q_data_smt = multiprocessing.JoinableQueue()
    # - PCM/GUI
    q_msg_pcm = multiprocessing.JoinableQueue()
    q_data_pcm = multiprocessing.JoinableQueue()

    # launch UDP communication handler in other processes <NON-BLOCKING>
    # - smt
    p_smt = multiprocessing.Process(target=tlm_handler_wrapper, args=('smt', q_msg_smt, q_data_smt))
    p_smt.start()
    # - pcm
    p_pcm = multiprocessing.Process(target=tlm_handler_wrapper, args=('pcm', q_msg_pcm, q_data_pcm))
    p_pcm.start()

    # launch GUI handler in the main process/thread <BLOCKING>
    gui_handler(q_msg_smt, q_msg_pcm, q_data_smt, q_data_pcm)
    
    # end processing
    # - smt
    q_msg_smt.join()
    # q_data_smt.join()
    p_smt.join()
    # - pcm
    q_msg_pcm.join()
    # q_data_smt.join()
    p_pcm.join()

    print('DES-QL quitted normally ...')




