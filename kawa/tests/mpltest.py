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
import matplotlib
matplotlib.use('WxAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.figure import Figure

### Local libraries
# from usrmod import tlm


### wxPython configurations
REFLESH_RATE_PLOTTER = 200
# REFLESH_RATE_PLOTTER = 1000
# REFLESH_RATE_DIGITAL_INDICATOR = 450

### Matplotlib configuration
plt.style.use('dark_background')

# plt.rcParams["figure.subplot.bottom"] = 0.07    # Bottom Margin
plt.rcParams["figure.subplot.top"] = 0.97       # Top Margin
# plt.rcParams["figure.subplot.left"] = 0.1       # Left Margin
plt.rcParams["figure.subplot.right"] = 0.97     # Right Margin

plt.rcParams["figure.subplot.hspace"] = 0.30    # Height Margin between subplots


#
# Time-series data generatiton for test
#

# served as time in [s]
x_val = list(map(lambda y: y/1.0, range(10000)))

# pseudo-data (series 1: sinusoidal)
y1_val = list(map(lambda y: 2.0 * math.sin(y/5.0) + 2.0, x_val))    # 0 < y < 4
# xy1_val = list(zip(x_val, y1_val))

# pseudo-data (series 2: random)
y2_val = list(map(lambda y: 3.0 * random.random(), x_val))          # 0 < y < 3
# xy2_val = list(zip(x_val, y2_val))


#
# Main Frame
# 
class frmMain(wx.Frame):
    def __init__(self):
        # inherit super class
        super().__init__(parent=None, id=wx.ID_ANY, title='DES Quick Look', size=(800,800))

        # maxmize GUI window size
        # self.Maximize(True)

        self.SetBackgroundColour('Dark Grey')

        # generate panel
        self.pnlMain = MainPanel(self)

        # layout panels
        #lytRoot = wx.GridBagSizer()
        #lytRoot.Add(self.pnlMain, pos=wx.GBPosition(0,0), flag=wx.EXPAND | wx.ALL, border=10)

        #self.pnlMain.SetSizer(lytRoot)
        #lytRoot.Fit(self.pnlMain)
        
        # bind events
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        
        # print("I'm here !")     # for debug

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
    # __N_PLOTTER = 1
    __N_PLOTTER = 2   

    # index_x = 1    
    # sensor_type = ['Time [s]', 'P [MPa]', 'T [K]', 'IMU', 'House Keeping']
    # col_value = [6, 8, 8, 9, 8]

    def __init__(self, parent):
        super().__init__(parent, wx.ID_ANY)

        ### initialize
        self.NNN = 0
        # self.__F_TLM_IS_ACTIVE = False
        # self.dfTlm = pd.DataFrame()
        
        # - plotter config
        self.load_config_plotter()

        ### configure appearanc
        self.configure_plotter()

        ### layout elements
        self.layout = wx.FlexGridSizer(rows=1, cols=1, gap=(0, 0))
        self.layout.Add(self.canvas, flag=wx.EXPAND)
        self.SetSizer(self.layout)

        ### bind events
        # - set timer to refresh time-history pane
        self.tmrRefreshPlotter = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnRefreshPlotter, self.tmrRefreshPlotter)
        self.tmrRefreshPlotter.Start(REFLESH_RATE_PLOTTER)
            
    # Event handler: EVT_TIMER
    def OnRefreshPlotter(self, event):
        # return None     # for debug

        # update plot points by appending latest values
        self.x_series = np.append(self.x_series, x_val[self.NNN])
        # self.y1_series = np.append(self.y1_series, y1_val[self.NNN])
        # self.y2_series = np.append(self.y2_series, y2_val[self.NNN])
        for i in range(self.__N_PLOTTER):
            self.y_series = np.append(self.y_series, self.y_val[i][self.NNN])

        # pseudo-time incriment USED ONLY IN TEST
        self.NNN += 1
        if self.NNN == len(x_val):  self.NNN = 0   # reset pseudo-time

        # update time range to plot
        t_max = self.x_series[-1]
        t_min = t_max - self.__T_RANGE
        # print("t_max = {}, t_min = {}".format(t_max, t_min))

        # delete plot points out of the designated time range
        while self.x_series[0] < t_min:
            print("GUI PLT: a member of 'x_series' is out of the range")
            self.x_series = np.delete(self.x_series, 0)
            self.y_series = np.delete(self.y_series, np.s_[0:self.__N_PLOTTER])
            # self.y1_series = np.delete(self.y1_series, 0)
            # self.y2_series = np.delete(self.y2_series, 0)
            # self.y_series = np.delete(self.y_series, self.__N_PLOT)

            print("GUI PLT: length x: {}, y: {}".format(len(self.x_series),len(self.y_series)))

        for i in range(self.__N_PLOTTER):
            # delete x axis and lines by restroring canvas
            self.canvas.restore_region(self.backgrounds[i])

        for i in range(self.__N_PLOTTER):
            # clear axes
            self.axes[i].cla()

        for i in range(self.__N_PLOTTER):
            # update limit for x axis
            self.axes[i].set_xlim([t_min, t_max])

        for i in range(self.__N_PLOTTER):
            # set limit for y axis
            self.axes[i].set_ylim([self.y_min[i], self.y_max[i]])

        for i in range(self.__N_PLOTTER):
            # set label for y axis
            self.axes[i].set_ylabel(self.y_label[i])

        for i in range(self.__N_PLOTTER):
            # update alert line
            self.axes[i].axhline(y=self.alart_lim_u[i], xmin=0, xmax=1, color='red')
            self.axes[i].axhline(y=self.alart_lim_l[i], xmin=0, xmax=1, color='red')
            # self.axes[1].axhline(y=500.0, xmin=0, xmax=1, color='red')

        # tentative draw
        #self.canvas.draw()

        # save the empty canvas as background
        #self.backgrounds[0] = self.canvas.copy_from_bbox(self.axes[0].bbox)
        
        # update lines by prepared axes
        # NOTE: lines become iterrable hereafter
        self.lines = []
        for i in range(self.__N_PLOTTER):
            self.lines.append(self.axes[i].plot(self.x_series, self.y_series[i::self.__N_PLOTTER])[0])
     
        for i in range(self.__N_PLOTTER):
            # reflect updates in lines
            self.axes[i].draw_artist(self.lines[i])

        for i in range(self.__N_PLOTTER):
            # redraw and show updated canvas
            self.fig.canvas.blit(self.axes[i].bbox)
        
        # self.fig.canvas.flush_events()
        print("GUI PLT: redraw plots...")

    # Load configurations from external files
    def load_config_plotter(self):          
        self.y_label = ["Series 1", "Series 2"]
        self.y_min = [0.0, 0.0]
        self.y_max = [4.0, 3.0]
        self.alart_lim_u = [3.0, 2.5]
        self.alart_lim_l = [1.0, 0.5]
        
        # self.item_plot = [self.df_cfg_plot['item'][self.df_cfg_plot['plot_1'].astype(bool)].iat[0],
        #                   self.df_cfg_plot['item'][self.df_cfg_plot['plot_2'].astype(bool)].iat[0]]

    # Configure appearance for plotters to display time histories
    def configure_plotter(self):      
        # initialize data set
        self.x_series = np.empty(0)
        self.y_series = np.empty(0)
        # self.y1_series = np.empty(0)
        # self.y2_series = np.empty(0)
        # print("GUI PLT: x_series = {}".format(self.x_series))
        # print("GUI PLT: y_series = {}".format(self.y_series))

        # USED ONLY IN TEST
        self.y_val = [y1_val, y2_val]   

        # prepare empty matplotlib Fugure
        self.fig = Figure(figsize=(8, 8))
        
        # register Figure with matplotlib Canvas
        self.canvas = FigureCanvasWxAgg(self, wx.ID_ANY, self.fig)

        # return None     # for debug

        ### prepare axes
        # - generate subplots containing axes in Figure
        # NOTE: axes become iterrable hereafter
        self.axes = []
        for i in range(self.__N_PLOTTER):
            self.axes.append(self.fig.add_subplot(self.__N_PLOTTER, 1, i+1))

            # - set limit for x axis
            t_min = 0
            self.axes[i].set_xlim([t_min, t_min + self.__T_RANGE])

            # - set limit for y axis
            self.axes[i].set_ylim([self.y_min[i], self.y_max[i]])

            # - set label for y axis
            self.axes[i].set_ylabel(self.y_label[i])


        # tentatively draw canvas without plot points to save as background
        self.canvas.draw()                                            

        # save the empty canvas as background
        # NOTE: backgrounds become iterrable hereafter
        self.backgrounds = []
        for i in range(self.__N_PLOTTER):
            self.backgrounds.append(self.canvas.copy_from_bbox(self.axes[i].bbox))


if __name__ =="__main__":
    app = wx.App()
    
    frmMain()
    print('wxPython Launched!')
    
    app.MainLoop()

    print('... DES QL quitted normally')