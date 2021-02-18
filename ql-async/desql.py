### Standard libraries
import asyncio
import concurrent.futures

### Third-party libraries
import wx

### Local libraries
from src import asynctlm
from src import gui
from src import common

### T.B.REFAC.: TO BE MOVED TO ASYNCTLM.PY ###
# async def tlm(tlm_type, internal_flags, tlm_latest_data):
#     # print('Starting {} handlar...'.format(tlm_type))
    
#     # initialize
#     # HOST = ''
#     HOST = '192.168.1.255'                                  # mac
#     # HOST = socket.gethostbyname(socket.gethostname())       # windows / mac(debug)
#     PORT = 0

#     ### TBREFAC. ###
#     if tlm_type == 'smt':
#         PORT = 49157
#     elif tlm_type == 'pcm':
#         PORT = 49158
#     else :
#         print('Error: Type of the telemeter is wrong!')
#         return

#     # create datagram listner in the running event loop
#     loop = asyncio.get_running_loop()
#     transport, protocol = await loop.create_datagram_endpoint(
#                                     lambda: asynctlm.DatagramServerProtocol(tlm_type, tlm_latest_data),
#                                     local_addr=(HOST,PORT))

#     # psotpone quitting until GUI task is done
#     while internal_flags.GUI_TASK_IS_DONE == False:
#         await asyncio.sleep(2)

#     # quit
#     return (transport, protocol)

# #
# # Socket Communication (UDP/IP) Handler (co-routine)
# #
# async def tlm_handler(internal_flags, tlm_latest_values):
#     # print('Starting TLM handler...')
#
#     # gatherd_tasks = await asyncio.gather(
#     await asyncio.gather(
#         tlm("smt", internal_flags, tlm_latest_values),
#         tlm("pcm", internal_flags, tlm_latest_values))
    
#
# Socket Communication (UDP/IP) Handler
#
def tlm_handler_wrapper(internal_flags, tlm_latest_data):
    print('MAIN: Invoking UDP Communication Handlers...')

    # define wrapper for tlm_handler (co-routine)   ### T.B.REFAC.? ###
    async def tlm_handler(internal_flags, tlm_latest_values):
        await asyncio.gather(
            asynctlm.tlm("smt", internal_flags, tlm_latest_values),
            asynctlm.tlm("pcm", internal_flags, tlm_latest_values))
        
    asyncio.run(tlm_handler(internal_flags, tlm_latest_data))
    print('Closing TLM...')

#
# Graphical User Interface Handler
#
def gui_handler(internal_flags, tlm_latest_data):
    print('MAIN: Invoking GUI...')
    
    app = wx.App()

    # generate main window
    gui.frmMain(internal_flags, tlm_latest_data)
    
    # launch event loop for GUI
    app.MainLoop()

    print('Closing GUI...')

#
# Main
#
if __name__ == "__main__":
    # initialize variables shared among threads
    internal_flags = common.InternalFlags()
    tlm_latest_data = common.TlmLatestData()

    # define wrapper for tlm_handler co-routine   ### T.B.REFAC.? ###
    # def tlm_handler_wrapper(internal_flags, tlm_latest_data):
    #     asyncio.run(tlm_handler(internal_flags, tlm_latest_data))
    #     print('Closing TLM...')

    # launch UDP communication handler concurrently in sub-threads
    executor = concurrent.futures.ThreadPoolExecutor()
    executor.submit(tlm_handler_wrapper, internal_flags, tlm_latest_data)

    # launch GUI handler in Main thread
    gui_handler(internal_flags, tlm_latest_data)

    # shutdown UDP communication handler
    executor.shutdown()

    print('DES-QL quitted normally ...')





