### Standard libraries
import copy
import math
import random
#import sys
#import threading
#import time

### Third-party libraries
#import numpy as np
#import pandas as pd

import wx
import wx.lib
import wx.lib.plot as plt
#import matplotlib
#matplotlib.use('WxAgg')
#import matplotlib.pyplot as plt
#from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
#from matplotlib.figure import Figure

### Local libraries
# n/a


"""
wxPython configurations
"""
REFLESH_RATE_PLOTTER = 20
#REFLESH_RATE_PLOTTER = 1000
REFLESH_RATE_DIGITAL_INDICATOR = 450

"""
Matplotlib configurations
"""
#plt.style.use('dark_background')
##plt.rcParams["figure.subplot.bottom"] = 0.07    # Bottom Margin
#plt.rcParams["figure.subplot.top"] = 0.97       # Top Margin
##plt.rcParams["figure.subplot.left"] = 0.1       # Left Margin
#plt.rcParams["figure.subplot.right"] = 0.97     # Right Margin
#plt.rcParams["figure.subplot.hspace"] = 0.30    # Height Margin between subplots

"""
Test data generatiton
"""
x1_val = list(range(10000))
#y1_val = map(lambda y: math.sin(y), x1_val)     # -1 < y < 1
y1_val = map(lambda y: math.sin(y/100), x1_val)     # -1 < y < 1
xy1_val = list(zip(x1_val, y1_val))

x2_val = list(range(10000))
y2_val = map(lambda y: random.random(), x2_val)   # 0 < y < 1
xy2_val = list(zip(x2_val, y2_val))

"""
Main Frame
"""
class frmMain(wx.Frame):
    def __init__(self, parent=None, id=-1, title='DES Quick Look', size=(1000,1000)):
        # inherit super class
        super().__init__(parent, id, title, size)
        #super().__init__(parent=None, id=-1, title='DES Quick Look',size=(500,500))

        self.SetBackgroundColour('Dark Grey')
        #self.Maximize(True)
        
        #
        # Parts on frmMain
        #
        # panel
        pnlMain = wx.Panel(self,-1)
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
        pass


"""
Time History Plots & Current Value Indicators
"""
'''
class ChartPanel(wx.Panel):
    index_x = 1
    t_range = 30    # [s]

    n_plot = 5

    sensor_type = ['Time [s]', 'P [MPa]', 'T [K]', 'IMU', 'House Keeping']
    col_value = [6, 8, 8, 9, 8]

    def __init__(self, parent, reflesh_time_graph, reflesh_time_value):
        super().__init__(parent, wx.ID_ANY)

        self.configReader()
        self.flag_temp = True

        self.valueGenerator()
        self.chartGenerator()

        # layout time history pane
        self.layout = wx.FlexGridSizer(rows=1, cols=2, gap=(20, 0))
        self.layout.Add(self.canvas, flag=wx.EXPAND)
        self.layout.Add(self.layout_Value, flag=wx.ALIGN_CENTER_HORIZONTAL)
        self.SetSizer(self.layout)

        # set refresh timer for time history pane
        self.timer_reload_graph = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.graphReloader, self.timer_reload_graph)
        self.timer_reload_graph.Start(reflesh_time_graph)

        # set refresh timer for current value pane
        self.timer_reload_value = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.valueReloader, self.timer_reload_value)
        self.timer_reload_value.Start(reflesh_time_value)
'''


if __name__ =="__main__":
    #app = wx.App()
    #frame = wx.Frame(None, -1, 'Hello,World!',size=(500,500))
    #frame.Show()
    #app.MainLoop()

    #flag_GUI = True

    app = wx.App()
    
    #frame = frmMain()
    frmMain()
    print('wxPytho Launched!')
    
    app.MainLoop()

    #flag_GUI = False

    print('... DES QL quitted normally')