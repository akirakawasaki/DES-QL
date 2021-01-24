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
REFLESH_RATE_PLOTTER = 500
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
y1_val = list(map(lambda y: 2.0 * (math.sin(y/5.0) + 1.0), x_val))    # 0 < y < 4
# xy1_val = list(zip(x_val, y1_val))

# pseudo-data (series 2: random)
y2_val = list(map(lambda y: 3.0 * random.random(), x_val))          # 0 < y < 3
# xy2_val = list(zip(x_val, y2_val))

# pseudo-data (series 3: random)
y3_val = list(map(lambda y: 2.0 * (math.cos(2.0 * math.pi * random.random()) + 1.0), x_val))          # 0 < y < 4

# pseudo-data (series 4: random)
y4_val = list(map(lambda y: 1.0 * random.random(), x_val))          # 0 < y < 1

# pseudo-data (series 5: random)
y5_val = list(map(lambda y: 1.5 * random.random(), x_val))          # 0 < y < 1.5


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
    __N_PLOTTER = 5

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
        # print("GUI PLT: t_max = {}, t_min = {}".format(t_max, t_min))

        # delete plot points out of the designated time range
        while self.x_series[0] < t_min:
            print("GUI PLT: a member of 'x_series' is out of the range")
            self.x_series = np.delete(self.x_series, 0)
            self.y_series = np.delete(self.y_series, np.s_[0:self.__N_PLOTTER])
            # self.y1_series = np.delete(self.y1_series, 0)
            # self.y2_series = np.delete(self.y2_series, 0)
            # self.y_series = np.delete(self.y_series, self.__N_PLOT)

            # print("GUI PLT: length x: {}, y: {}".format(len(self.x_series),len(self.y_series)))

        # prepare redraw
        self.lines = []
        for i in range(self.__N_PLOTTER):
            # delete x axis and lines by restroring canvas
            self.canvas.restore_region(self.backgrounds[i])

            # clear axes
            self.axes[i].cla()

            # update limit for x axis
            self.axes[i].set_xlim([t_min, t_max])

            # set limit for y axis
            self.axes[i].set_ylim([self.plt_attr[i].y_min, self.plt_attr[i].y_max])

            # set label for y axis
            self.axes[i].set_ylabel(self.plt_attr[i].y_label)

            # update alert line
            self.axes[i].axhline(y=self.plt_attr[i].alart_lim_u, xmin=0, xmax=1, color='red')
            self.axes[i].axhline(y=self.plt_attr[i].alart_lim_u, xmin=0, xmax=1, color='red')
        
            # update plot
            # NOTE: lines become iterrable hereafter
            self.lines.append(self.axes[i].plot(self.x_series, self.y_series[i::self.__N_PLOTTER])[0])
     
            # reflect updates in lines
            self.axes[i].draw_artist(self.lines[i])

            # # redraw and show updated canvas
            # self.fig.canvas.blit(self.axes[i].bbox)

        # redraw and show updated canvas
        self.fig.canvas.draw()
        # self.fig.canvas.flush_events()
        print("GUI PLT: redraw plots...")

    # Load configurations from external files
    def load_config_plotter(self):          
        ### TBREFAC.: TEMPORALLY DESIGNATED BY LITERALS ###
        plt_attr_1 = PltAttr(
            y_label =  "Series 1",
            y_min = 0.0,
            y_max = 4.0,
            alart_lim_u = 3.0,
            alart_lim_l = 1.0
        )
        plt_attr_2 = PltAttr(
            y_label =  "Series 2",
            y_min = 0.0,
            y_max = 3.0,
            alart_lim_u = 2.5,
            alart_lim_l = 0.5,
        )
        plt_attr_3 = PltAttr(
            y_label =  "Series 3",
            y_min = 0.0,
            y_max = 3.0,
            alart_lim_u = 2.5,
            alart_lim_l = 0.5,
        )
        plt_attr_4 = PltAttr(
            y_label =  "Series 4",
            y_min = 0.0,
            y_max = 3.0,
            alart_lim_u = 2.5,
            alart_lim_l = 0.5,
        )
        plt_attr_5 = PltAttr(
            y_label =  "Series 5",
            y_min = 0.0,
            y_max = 3.0,
            alart_lim_u = 2.5,
            alart_lim_l = 0.5,
        )

        self.plt_attr = []
        self.plt_attr.append(plt_attr_1)
        if self.__N_PLOTTER <= 1: return

        self.plt_attr.append(plt_attr_2)
        if self.__N_PLOTTER <= 2: return

        self.plt_attr.append(plt_attr_3)
        if self.__N_PLOTTER <= 3: return

        self.plt_attr.append(plt_attr_4)
        if self.__N_PLOTTER <= 4: return

        self.plt_attr.append(plt_attr_5)
        if self.__N_PLOTTER <= 5: return
        else: self.__N_PLOTTER == 5

        # self.y_label = [, "Series 2"]
        # self.y_min = [0.0, 0.0]
        # self.y_max = [4.0, 3.0]
        # self.alart_lim_u = [3.0, 2.5]
        # self.alart_lim_l = [1.0, 0.5]
        
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
        self.y_val = [y1_val, y2_val, y3_val, y4_val, y5_val]   

        # generate empty matplotlib Fugure
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
            self.axes[i].set_ylim([self.plt_attr[i].y_min, self.plt_attr[i].y_max])

            # - set label for y axis
            self.axes[i].set_ylabel(self.plt_attr[i].y_label)


        # tentatively draw canvas without plot points to save as background
        self.canvas.draw()                                            

        # save the empty canvas as background
        # NOTE: backgrounds become iterrable hereafter
        self.backgrounds = []
        for i in range(self.__N_PLOTTER):
            self.backgrounds.append(self.canvas.copy_from_bbox(self.axes[i].bbox))


# retain plotter attributions
class PltAttr():
    def __init__(self, 
                y_label="", y_unit="", 
                y_min=0.0, y_max=1.0, 
                alart_lim_l=0.0, alart_lim_u=1.0) -> None:
        self.y_label = y_label
        self.y_unit = y_unit
        self.y_min = y_min
        self.y_max = y_max
        self.alart_lim_l = alart_lim_l
        self.alart_lim_u = alart_lim_u


if __name__ =="__main__":
    app = wx.App()
    
    frmMain()
    print('wxPython Launched!')
    
    app.MainLoop()

    print('... DES QL quitted normally')