### Standard libraries
import asyncio
import concurrent.futures
#import decimal
import math
import socket
import sys
import time

### Third-party libraries
import numpy as np
import pandas as pd

import wx
import wx.lib
import wx.lib.plot as plt

### Local libraries
#n/a


'''
Global Variables
'''
#F_GUI_TERMINATED = False
#dfSmtData = pd.DataFrame()
#dfPcmData = pd.DataFrame()

'''
Constant Definition
'''
W2B = 2
NUM_OF_FRAMES = 8
LEN_HEADER  = 4
LEN_PAYLOAD = 64
BUFSIZE = W2B * (LEN_HEADER + LEN_PAYLOAD) * NUM_OF_FRAMES       # 1088 bytes


class DatagramServerProtocol:
    def __init__(self, type, sData):
        self.type = type
        self.sData = sData
        #self.dfTlmData = pd.DataFrame()
        self.NNN = 0
    
    def connection_made(self,transport):
        self.transport = transport
        print("connected")

    def connection_lost(self,exec):
        print("disconnected")

    def datagram_received(self,data,addr):
        #print("Received a datagram from %s" % self.type)

        #DATA_PATH = ''
        if self.type == 'smt':
            #DATA_PATH = './data_smt.csv'
            self.sData.dfSmtData = pd.DataFrame(columns=['User_ID', str(self.NNN), self.type], index=['a', 'b', 'c'])
        elif self.type == 'pcm':
            #DATA_PATH = './data_pcm.csv'
            self.sData.dfPcmData = pd.DataFrame(columns=['User_ID', str(self.NNN), self.type], index=['a', 'b', 'c'])
        else :
            print('Error: Type of the telemeter is wrong!')

        '''
        for k in range(W2B * LEN_HEADER):   # header
            print(hex(data[k]).zfill(4), end=' ')
        print('')   # linefeed
        for j in range(4):                  # payload
            print(f"message {0}-{j}: ",end='')
            for k in range(W2B * int(LEN_PAYLOAD / 4)): 
                print(hex(data[k + W2B * (LEN_HEADER + j * int(LEN_PAYLOAD / 4))]).zfill(4), end=' ')
            print('')   # linefeed
        print('')   # linefeed
        '''

        self. NNN += 1
        #self.dfTlmData = pd.DataFrame(columns=['User_ID', str(self.NNN), self.type], index=['a', 'b', 'c'])


async def tlm(type, sData):
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
    transport, protocol = await loop.create_datagram_endpoint(
                                    lambda: DatagramServerProtocol(type, sData),
                                    local_addr=(HOST,PORT))

    '''
    while True:
        if type == 'smt':
            dfSmtData = protocol.dfTlmData
        elif type == 'pcm':
            dfPcmData = protocol.dfTlmData
        
        await asyncio.sleep(0.1)
    '''

    #return protocol.dfTlmData
    return (transport, protocol)

    #try:
    #    await asyncio.sleep(3600)  # Serve for 1 hour.
    #finally:
    #    transport.close()


"""
wxPython configurations
"""
REFLESH_RATE_PLOTTER = 20
#REFLESH_RATE_PLOTTER = 1000
REFLESH_RATE_DIGITAL_INDICATOR = 2000

"""
Test data generatiton
"""
x1_val = list(range(10000))
#y1_val = map(lambda y: math.sin(y), x1_val)     # -1 < y < 1
y1_val = map(lambda y: math.sin(y/100), x1_val)     # -1 < y < 1
xy1_val = list(zip(x1_val, y1_val))

#x2_val = list(range(10000))
#y2_val = map(lambda y: random.random(), x2_val)   # 0 < y < 1
#xy2_val = list(zip(x2_val, y2_val))

"""
Main Frame
"""
class frmMain(wx.Frame):
    def __init__(self, sData):
        # inherit super class
        #super().__init__(parent, id, title, size)
        super().__init__(parent=None, id=-1, title='DES Quick Look',size=(800,800))

        self.sData = sData

        self.SetBackgroundColour('Dark Grey')
        #self.Maximize(True)
        
        #
        # Parts on frmMain
        #
        # panel
        wx.Panel(self,-1)
        #pnlMain = wx.Panel(self,-1)
        #pnlMain = wx.Panel(self,id=wx.ID_ANY,pos=wx.DefaultPosition,size=wx.DefaultSize)

        #
        # Parts on pnlMain?
        #
        # plotter initialize
        self.plotter = plt.PlotCanvas(self,wx.ID_ANY)
        # - content
        line = plt.PolyLine(xy1_val)
        gc = plt.PlotGraphics([line])
        self.plotter.Draw(gc)
        # - position and size
        sizer = wx.GridSizer(1, 1, gap=(0, 0))
        sizer.Add(self.plotter, flag=wx.EXPAND)
        self.SetSizer(sizer)
        # - initialize
        self.xx_val = 0.0
        self.plot_data = [[0.0,0.0]]
        self.plotter.xSpec = (0,100)

        #
        # Events generated in frmMain
        #
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        self.tmrRefreshPlotter = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnRefreshPlotter, self.tmrRefreshPlotter)
        self.tmrRefreshPlotter.Start(REFLESH_RATE_PLOTTER)

        self.tmrRefreshDigitalIndicator = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnRefreshDigitalIndicator, self.tmrRefreshDigitalIndicator)
        self.tmrRefreshDigitalIndicator.Start(REFLESH_RATE_DIGITAL_INDICATOR)

        #
        # switch frmMain to visible state after prepalation
        #
        self.Show()

    # event handler: EVT_CLOSE
    def OnClose(self, event):
        self.Destroy()
        '''
        diagConfirm = wx.MessageDialog(
                        self,
                        "Do you really want to close this application?",
                        "Confirm Exit",
                        wx.OK | wx.CANCEL | wx.ICON_QUESTION)
        retval = diagConfirm.ShowModal()
        diagConfirm.Destroy()
        
        if retval == wx.ID_OK:  self.Destroy()
        '''

        #F_GUI_TERMINATED = True

    # event handler: EVT_TIMER1
    def OnRefreshPlotter(self, event):
        # update plot data
        self.xx_val += 1.0
        yy_val = math.sin(self.xx_val/10.0)
        self.plot_data += [[self.xx_val, yy_val]]
        if len(self.plot_data) > 100:
            #self.plot_data = copy.deepcopy(self.plot_data[-100:-1])
            self.plotter.xSpec = (self.plot_data[-100][0],self.plot_data[-1][0])

        # prepare drawing
        line = plt.PolyLine(self.plot_data, legend='sample', colour='red', width=2)
        gc = plt.PlotGraphics([line], 'RealTimePlot', 'xaxis', 'yaxis')
        self.plotter.Draw(gc)

    # event handler: EVT_TIMER2
    def OnRefreshDigitalIndicator(self, event):
        print(self.sData.dfSmtData)
        print(self.sData.dfPcmData)
        
        #pass


def gui_main(sData):
    #flag_GUI = True
   
    app = wx.App()
    #frmMain(dfSmtData, dfPcmData)
    frmMain(sData)
    print('wxPytho Launched!')
    app.MainLoop()

    #flag_GUI = False


class sharedData:
    def __init__(self):
        self.dfSmtData = pd.DataFrame()
        self.dfPcmData = pd.DataFrame()


if __name__ == "__main__":
    sData = sharedData()

    #asyncio uses event loops to manage its operation
    loop = asyncio.get_event_loop()

    # multi-thread executor 
    #executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    #executor = concurrent.futures.ThreadPoolExecutor(max_workers=None)
    #loop.set_default_executor(executor)

    # Create coroutines for three asyncronous tasks
    gathered_coroutines = asyncio.gather(
        tlm("smt", sData),
        tlm("pcm", sData),
        loop.run_in_executor(None, gui_main, sData))
    # gui_main(sData)

    # This is the entry from synchronous to asynchronous code
    # It will block until the coroutine passed in has completed
    results = loop.run_until_complete(gathered_coroutines)
    print(results)

    # We're done with the event loop
    loop.close()

    print('... DES QL quitted normally')