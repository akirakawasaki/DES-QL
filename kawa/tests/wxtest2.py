### Standard libraries
import math
import random
# import sys
# import threading
# import time

### Third-party libraries
import numpy as np
import pandas as pd

import wx
import wx.lib
import wx.lib.plot as plot

### Local libraries
# n/a


### wxPython configurations
REFLESH_RATE_PLOTTER = 20       # ms/cycle
# REFLESH_RATE_PLOTTER = 500      # ms/cycle
# REFLESH_RATE_PLOTTER = 2000     # ms/cycle

### Matplotlib configuration
# plt.style.use('dark_background')

# Plotter margins
# plt.rcParams["figure.subplot.bottom"] = 0.03    # Bottom
# plt.rcParams["figure.subplot.top"]    = 0.99    # Top
# plt.rcParams["figure.subplot.left"]   = 0.15    # Left
# plt.rcParams["figure.subplot.right"]  = 0.97    # Right
# plt.rcParams["figure.subplot.hspace"] = 0.05    # Height Margin between subplots


#
# Time-series data generatiton for test
#

# served as time in [s]
x_val = list(map(lambda y: y/1.0, range(10000)))

# pseudo-data (series 1: sinusoidal)    # 0 < y < 4
y1_val = list(map(lambda y: 2.0 * (math.sin(y/5.0) + 1.0), x_val))      

# pseudo-data (series 2: random)        # 0 < y < 3
y2_val = list(map(lambda y: 3.0 * random.random(), x_val))              

# pseudo-data (series 3: random)        # 0 < y < 4
y3_val = list(map(lambda y: 2.0 * (math.cos(2.0 * math.pi * random.random()) + 1.0), x_val))          

# pseudo-data (series 4: random)        # 0 < y < 1
y4_val = list(map(lambda y: 1.0 * random.random(), x_val))              

# pseudo-data (series 5: random)        # 0 < y < 1.5
y5_val = list(map(lambda y: 1.5 * random.random(), x_val))              


#
# Main Frame
# 
class frmMain(wx.Frame):
    def __init__(self):
        # inherit super class
        super().__init__(parent=None, id=wx.ID_ANY, title='DES Quick Look', size=(800,800))

        # self.SetBackgroundColour('Dark Grey')
        self.SetBackgroundColour('BLACK')

        # generate panel
        self.pnlMain = MainPanel(self)
        
        # bind events
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        
        # make frmMain visible at first
        self.Show()
        
    # Event handler: EVT_CLOSE
    def OnClose(self, event):
        self.Destroy()

#
# Time History Plots & Current Value Indicators
#
class MainPanel(wx.Panel):
    __T_RANGE = 30      # [s]
    __N_PLOTTER = 1
    # __N_PLOTTER = 5

    def __init__(self, parent):
        super().__init__(parent, wx.ID_ANY)

        # USED ONLY IN TEST
        self.y_val = [y1_val, y2_val, y3_val, y4_val, y5_val]

        # initialize variables
        self.NNN = 0
        self.__N_PLOTTER = max(1, min(5, self.__N_PLOTTER))
        
        # load initial attributions
        self.load_plotter_attributions()
        
        # configure appearanc
        self.configure_plotter()

        # layout elements
        # self.layout = wx.FlexGridSizer(rows=1, cols=1, gap=(0, 0))
        # self.layout.Add(self.canvas, flag=wx.EXPAND)
        # self.SetSizer(self.layout)

        # bind events
        # - set timer to refresh time-history pane
        self.tmrRefreshPlotter = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnRefreshPlotter, self.tmrRefreshPlotter)
        self.tmrRefreshPlotter.Start(REFLESH_RATE_PLOTTER)
            
    # Event handler: EVT_TIMER
    def OnRefreshPlotter(self, event):
        return None     # for debug

        ###
        ### update data set to plot
        # - update plot points by appending latest values
        self.x_series.append(x_val[self.NNN])
        for i in range(self.__N_PLOTTER):
            self.y_series.append(self.y_val[i][self.NNN])

        # - determine time max & min
        self.t_max = self.x_series[-1]
        self.t_min = self.t_max - self.__T_RANGE
        # print("GUI PLT: t_max = {}, t_min = {}".format(t_max, t_min))

        # - delete plot points out of the designated time range
        # while self.x_series[0] < self.t_min:
        while self.x_series[0] < (self.t_min - 0.2 * self.__T_RANGE):
            del self.x_series[0]
            del self.y_series[0:self.__N_PLOTTER]
            # print('GUI PLT: a member of 'x_series' is out of the range')
            # print(f'GUI PLT: length x: {len(self.x_series)}, y: {len(self.y_series)}')
        
        ###
        ### refresh plotter
        i = 0

        # - data set
        line = plot.PolyLine(list(zip(self.x_series, self.y_series[i::self.__N_PLOTTER])))
        self.graphic = plot.PlotGraphics([line])
        # self.graphic = plot.PlotGraphics([line], xLabel='UTC time, s', yLabel=self.PlotterAttr[i]['y_label'])
        self.graphic.xLabel = 'UTC time, s'
        self.graphic.yLabel = self.PlotterAttr[i]['y_label']

        # - axes
        self.plotter.xSpec = (self.t_min, self.t_max)
        self.plotter.ySpec = (self.PlotterAttr[i]['y_min'], self.PlotterAttr[i]['y_max'])
        # self.plotter.enableXAxisLabel = True
        # self.plotter.enableYAxisLabel = True

        # self.axes[i].axhline(y=self.PlotterAttr[i]['alart_lim_l'], xmin=0, xmax=1, color='FIREBRICK')
        # self.axes[i].axhline(y=self.PlotterAttr[i]['alart_lim_u'], xmin=0, xmax=1, color='FIREBRICK')

        # - refresh plotter
        self.plotter.Draw(self.graphic)
        print("GUI PLT: redraw plots...")

        # USED ONLY IN TEST
        # incriment pseudo-time for the next timer event 
        self.NNN += 1
        if self.NNN == len(x_val):  self.NNN = 0   # reset pseudo-time

    # Load configurations from external files
    def load_plotter_attributions(self):          
        # NOTE: temporally designated by literals in test

        self.PlotterAttr = {}

        # attributions for plotter 1
        i = 0
        dict_tmp = {}
        dict_tmp['idx_item']    = i
        dict_tmp['y_label']     = "Series 1"
        dict_tmp['y_unit']      = 'unit'
        dict_tmp['y_min']       = 0.0
        dict_tmp['y_max']       = 4.0
        dict_tmp['alart_lim_l'] = 1.0
        dict_tmp['alart_lim_u'] = 3.0
        self.PlotterAttr[i] = dict_tmp

        # attributions for plotter 2
        i = 1
        dict_tmp = {}
        dict_tmp['idx_item']    = i
        dict_tmp['y_label']     = "Series 2"
        dict_tmp['y_unit']      = 'unit'
        dict_tmp['y_min']       = 0.0
        dict_tmp['y_max']       = 3.0
        dict_tmp['alart_lim_l'] = 0.5
        dict_tmp['alart_lim_u'] = 2.5
        self.PlotterAttr[i] = dict_tmp

        # attributions for plotter 3
        i = 2
        dict_tmp = {}
        dict_tmp['idx_item']    = i
        dict_tmp['y_label']     = "Series 3"
        dict_tmp['y_unit']      = 'unit'
        dict_tmp['y_min']       = 0.0
        dict_tmp['y_max']       = 3.0
        dict_tmp['alart_lim_l'] = 0.5
        dict_tmp['alart_lim_u'] = 2.5
        self.PlotterAttr[i] = dict_tmp

        # attributions for plotter 4
        i = 3
        dict_tmp = {}
        dict_tmp['idx_item']    = i
        dict_tmp['y_label']     = "Series 4"
        dict_tmp['y_unit']      = 'unit'
        dict_tmp['y_min']       = 0.0
        dict_tmp['y_max']       = 3.0
        dict_tmp['alart_lim_l'] = 0.5
        dict_tmp['alart_lim_u'] = 2.5
        self.PlotterAttr[i] = dict_tmp

        # attributions for plotter 5
        i = 4
        dict_tmp = {}
        dict_tmp['idx_item']    = i
        dict_tmp['y_label']     = "Series 5"
        dict_tmp['y_unit']      = 'unit'
        dict_tmp['y_min']       = 0.0
        dict_tmp['y_max']       = 3.0
        dict_tmp['alart_lim_l'] = 0.5
        dict_tmp['alart_lim_u'] = 2.5
        self.PlotterAttr[i] = dict_tmp

    # Configure appearance for plotters to display time histories
    def configure_plotter(self):      
        ### initialize
        # - data set
        self.x_series = []
        self.y_series = []
        # print("GUI PLT: x_series = {}".format(self.x_series))
        # print("GUI PLT: y_series = {}".format(self.y_series))

        # - plotter
        self.plotter = plot.PlotCanvas(self, wx.ID_ANY)
        # self.plotter = plt.PlotCanvas(self, wx.ID_ANY, size=(400, 400))
        # self.plotter.SetEnableZoom(True)

        # return None     # for debug

        ### configure
        i = 0

        # - data set
        # line = plot.PolyLine([(0.0, 0.0)])
        line = plot.PolyLine(list(zip(self.x_series, self.y_series)))
        self.graphic = plot.PlotGraphics([line])
        # self.graphic = plot.PlotGraphics([line], 'title', 'UTC time, s', self.PlotterAttr[i]['y_label'])
        # self.graphic = plot.PlotGraphics([line], xLabel='UTC time, s', yLabel=self.PlotterAttr[i]['y_label'])

        self.graphic.xLabel = 'UTC time, s'
        self.graphic.yLabel = self.PlotterAttr[i]['y_label']

        # - axes
        t_min = 0.0
        
        self.plotter.ForegroundColour('BLACK')
        self.plotter.xSpec = (t_min, t_min + self.__T_RANGE)
        self.plotter.ySpec = (self.PlotterAttr[i]['y_min'], self.PlotterAttr[i]['y_max'])
        # self.plotter.enableXAxisLabel = True
        # self.plotter.enableYAxisLabel = True

        print(f'GUI PLT: graphic.xLabel = {self.graphic.xLabel}')
        print(f'GUI PLT: plotter.enableXAxisLabel = {self.plotter.enableXAxisLabel}')

        # - draw tentatively
        self.plotter.Draw(self.graphic)
        # self.plotter.Draw(self.graphic, xAxis=(0.0, 30.0), yAxis=(0.0, 4.0))

        sizer = wx.GridSizer(1, 1, gap=(0, 0))
        sizer.Add(self.plotter, proportion=1, flag=wx.EXPAND)
        # sizer = wx.BoxSizer(wx.VERTICAL)
        # sizer.Add(self.plotter)
        
        self.SetSizer(sizer)

        # self.Fit()

#
# Main
#
if __name__ =="__main__":
    app = wx.App()
    
    frmMain()
    print('wxPython Launched!')
    
    app.MainLoop()

    print('... DES QL quitted normally')