### Standard libraries
#import asyncio
#import decimal
#import math
#import socket
#import sys
#import concurrent.futures

### Third-party libraries
import numpy as np
import pandas as pd
import wx
#import wx.lib
#import wx.lib.plot as plt

import matplotlib
matplotlib.use('WxAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.figure import Figure

### Local libraries
# n/a


"""
wxPython configurations
"""
#REFLESH_RATE_PLOTTER = 20               # ms/cycle
REFLESH_RATE_PLOTTER = 1000             # ms/cycle
REFLESH_RATE_DIGITAL_INDICATOR = 450    # ms/cycle

"""
Matplotlib configuration
"""
plt.style.use('dark_background')

#plt.rcParams["figure.subplot.bottom"] = 0.07    # Bottom Margin
plt.rcParams["figure.subplot.top"] = 0.97       # Top Margin
#plt.rcParams["figure.subplot.left"] = 0.1       # Left Margin
plt.rcParams["figure.subplot.right"] = 0.97     # Right Margin

plt.rcParams["figure.subplot.hspace"] = 0.30    # Height Margin between subplots

"""
Top Level Window
"""
class frmMain(wx.Frame):
    def __init__(self):
        super().__init__(None, wx.ID_ANY, 'Rocket System Information App')

        self.Maximize(True)     # Maxmize GUI window size

        self.SetBackgroundColour('Dark Grey')
        #self.SetBackgroundColour('Black')

        # Making Main Graphic
        root_panel = wx.Panel(self, wx.ID_ANY)

        # System panel : Show the feeding system status
        self.chart_panel = ChartPanel(root_panel)

        # Set layout of panels
        root_layout = wx.GridBagSizer()
        root_layout.Add(self.chart_panel, pos=wx.GBPosition(0,0), flag=wx.EXPAND | wx.ALL, border=10)

        root_panel.SetSizer(root_layout)
        root_layout.Fit(root_panel)

        # Bind events
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    # Event handler: EVT_CLOSE
    def OnClose(self, event):
        dig = wx.MessageDialog(self,
                               "Do you really want to close this application?",
                               "Confirm Exit",
                               wx.OK | wx.CANCEL | wx.ICON_QUESTION)
        result = dig.ShowModal()
        dig.Destroy()
        if result == wx.ID_OK:  self.Destroy()

"""
Time History Plots & Current Value Indicators
"""
class ChartPanel(wx.Panel):
    index_x = 1
    t_range = 30    # [s]

    n_plot = 5

    sensor_type = ['Time [s]', 'P [MPa]', 'T [K]', 'IMU', 'House Keeping']
    col_value = [6, 8, 8, 9, 8]

    def __init__(self, parent):
        super().__init__(parent, wx.ID_ANY)

        # load configurations from external files
        self.load_configurations()
        #self.flag_temp = True

        # configure appearance
        self.configure_digital_indicator()
        self.configure_plotter()

        # layout plotters and digital indicators
        self.layout = wx.FlexGridSizer(rows=1, cols=2, gap=(20, 0))
        self.layout.Add(self.canvas, flag=wx.EXPAND)                            # plotter
        self.layout.Add(self.layout_Value, flag=wx.ALIGN_CENTER_HORIZONTAL)     # digital indicators
        self.SetSizer(self.layout)

        # bind events
        # set refresh timer for current value pane
        self.tmrRefreshDigitalIndicator = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnRefreshDigitalIndicator, self.tmrRefreshDigitalIndicator)
        self.timer_reload_value.Start(REFLESH_RATE_DIGITAL_INDICATOR)

        # set refresh timer for time history pane
        self.tmrRefreshPlotter = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnRefreshPlotter, self.tmrRefreshPlotter)
        self.tmrRefreshPlotter.Start(REFLESH_RATE_PLOTTER)

    # Event handler: EVT_TIMER
    def OnRefreshDigitalIndicator(self, event):
        # fetch current values
        dfCurrentValues = 

        # refresh display
        for i_sensor in range(len(self.df_cfg_tlm['item'])):
            self.SensorValue[i_sensor].SetLabel(str(np.round(dfCurrentValues.iloc[-1, i_sensor], 2)))

    # Event handler: EVT_TIMER
    def OnRefreshPlotter(self, event):
        # fetch current values

        
        try:
            self.data_past
        except AttributeError:
            self.data_plot = self.df.values
        else:
            self.data_plot = np.append(self.data_past, self.df.values, axis=0)

        t_temp = self.df.iloc[-1, self.index_x]
        if t_temp >= self.t_left + self.t_range:
            self.lines = []

            for i in range(self.n_plot):
                self.axes[i].cla()

            self.t_left = t_temp - self.t_range / 3
            for i in range(self.n_plot):
                self.axes[i].set_xlim([self.t_left, self.t_left + self.t_range])

            for i in range(self.n_plot):
                self.axes[i].set_ylim([self.y_min_plot[i], self.y_max_plot[i]])

            # draw alert line
            self.axes[0].axhline(y=1.0, xmin=0, xmax=1, color='red')
            """
            self.axes[1].axhline(y=500.0, xmin=0, xmax=1, color='red')
            self.axes[2].axhline(y=500.0, xmin=0, xmax=1, color='red')
            """

            for i in range(self.n_plot):
                self.axes[i].set_ylabel(self.item_plot[i] + ' [{}]'.format(self.unit_plot[i]))

            self.canvas.draw()
            for i in range(self.n_plot):
                self.backgrounds[i] = self.canvas.copy_from_bbox(self.axes[i].bbox)  # Save Empty Chart Format as Background

            for i in range(self.n_plot):
                self.lines.append(self.axes[i].plot(self.data_plot[::2, self.index_x],
                                                    self.data_plot[::2, self.index_plot[i]])[0])

        else:
            for i in range(self.n_plot):
                self.lines[i].set_data(self.data_plot[::2, self.index_x],
                                       self.data_plot[::2, self.index_plot[i]])
            #print(self.df.shape)

        # Re-draw plotter
        # MARKED TO BE REFACTOR #
        for i in range(self.n_plot):
            self.canvas.restore_region(self.backgrounds[i])     # Re-plot Background (i.e. Delete line)

        for i in range(self.n_plot):
            self.axes[i].draw_artist(self.lines[i])             # Set new data in ax

        for i in range(self.n_plot):
            self.fig.canvas.blit(self.axes[i].bbox)             # Plot New data

    # Load configurations from external files
    def load_configurations(self):
        # Load smt&pcm config
        #self.df_cfg_tlm = th_smt.smt.df_cfg.copy()
        self.df_cfg_smt = pd.read_excel('./config_tlm.xlsx', sheet_name='smt')
        self.df_cfg_pcm = pd.read_excel('./config_tlm.xlsx', sheet_name='pcm')

        self.df_cfg_smt.reset_index()
        self.df_cfg_pcm.reset_index()

        # Load plotter appearance config
        self.df_cfg_plot = (pd.read_excel('./config_plot.xlsx', sheet_name='smt')).dropna(how='all')

        self.index_plot = [self.df_cfg_plot['ID'][self.df_cfg_plot['plot_1'].astype(bool)].astype(int).iat[0],
                           self.df_cfg_plot['ID'][self.df_cfg_plot['plot_2'].astype(bool)].astype(int).iat[0],
                           self.df_cfg_plot['ID'][self.df_cfg_plot['plot_3'].astype(bool)].astype(int).iat[0],
                           self.df_cfg_plot['ID'][self.df_cfg_plot['plot_4'].astype(bool)].astype(int).iat[0],
                           self.df_cfg_plot['ID'][self.df_cfg_plot['plot_5'].astype(bool)].astype(int).iat[0]]
        #print(self.index_plot)
        
        self.item_plot = [self.df_cfg_plot['item'][self.df_cfg_plot['plot_1'].astype(bool)].iat[0],
                          self.df_cfg_plot['item'][self.df_cfg_plot['plot_2'].astype(bool)].iat[0],
                          self.df_cfg_plot['item'][self.df_cfg_plot['plot_3'].astype(bool)].iat[0],
                          self.df_cfg_plot['item'][self.df_cfg_plot['plot_4'].astype(bool)].iat[0],
                          self.df_cfg_plot['item'][self.df_cfg_plot['plot_5'].astype(bool)].iat[0]]
        #print(self.item_plot)
        
        self.unit_plot = [self.df_cfg_plot['unit'][self.df_cfg_plot['plot_1'].astype(bool)].iat[0],
                          self.df_cfg_plot['unit'][self.df_cfg_plot['plot_2'].astype(bool)].iat[0],
                          self.df_cfg_plot['unit'][self.df_cfg_plot['plot_3'].astype(bool)].iat[0],
                          self.df_cfg_plot['unit'][self.df_cfg_plot['plot_4'].astype(bool)].iat[0],
                          self.df_cfg_plot['unit'][self.df_cfg_plot['plot_5'].astype(bool)].iat[0]]
        #print(self.unit_plot)
        
        self.y_min_plot = [self.df_cfg_plot['y_min'][self.df_cfg_plot['plot_1'].astype(bool)].iat[0],
                           self.df_cfg_plot['y_min'][self.df_cfg_plot['plot_2'].astype(bool)].iat[0],
                           self.df_cfg_plot['y_min'][self.df_cfg_plot['plot_3'].astype(bool)].iat[0],
                           self.df_cfg_plot['y_min'][self.df_cfg_plot['plot_4'].astype(bool)].iat[0],
                           self.df_cfg_plot['y_min'][self.df_cfg_plot['plot_5'].astype(bool)].iat[0]]
        #print(self.y_min_plot)
        
        self.y_max_plot = [self.df_cfg_plot['y_max'][self.df_cfg_plot['plot_1'].astype(bool)].iat[0],
                           self.df_cfg_plot['y_max'][self.df_cfg_plot['plot_2'].astype(bool)].iat[0],
                           self.df_cfg_plot['y_max'][self.df_cfg_plot['plot_3'].astype(bool)].iat[0],
                           self.df_cfg_plot['y_max'][self.df_cfg_plot['plot_4'].astype(bool)].iat[0],
                           self.df_cfg_plot['y_max'][self.df_cfg_plot['plot_5'].astype(bool)].iat[0]]
        #print(self.y_max_plot)

        # Load sensor config
        self.df_cfg_sensor = (pd.read_excel('./config_sensor.xlsx', sheet_name='smt')).dropna(how='all')

        self.id_time = self.df_cfg_sensor[self.df_cfg_sensor['group'] == 'Time [s]']['ID'].astype(int)
        self.id_p = self.df_cfg_sensor[self.df_cfg_sensor['group'] == 'P [MPa]']['ID'].astype(int)
        self.id_T = self.df_cfg_sensor[self.df_cfg_sensor['group'] == 'T [K]']['ID'].astype(int)
        self.id_imu = self.df_cfg_sensor[self.df_cfg_sensor['group'] == 'IMU']['ID'].astype(int)
        self.id_hk = self.df_cfg_sensor[self.df_cfg_sensor['group'] == 'House Keeping']['ID'].astype(int)

        self.id = [self.id_time, self.id_p, self.id_T, self.id_imu, self.id_hk]

    # Update df
    '''
    def dfReloder(self):
        try:
            self.df
        except AttributeError:  # In the case of wxpython is not opened
            pass
        else:
            if th_smt.df_ui.shape[0] < self.df.shape[0]:
                if self.flag_temp:
                    self.data_past = self.df.values
                    self.flag_temp = False
                else:
                    self.data_past = np.append(self.data_past[-200:], self.df.values, axis=0)
                print('Reload data_plot : ' + str(self.data_past.shape))
        self.df = th_smt.df_ui.copy()
    '''

    # Configure appearance for digital indicators to display current values
    def configure_digital_indicator(self):
        # generate DataButton instances
        self.DataButton = []
        for index in self.df_cfg_tlm['item']:
            self.DataButton.append(wx.ToggleButton(self, wx.ID_ANY, index))

        # set presentation of values
        self.SensorValue = []
        for i in range(len(self.df_cfg_tlm['item'])):
            self.SensorValue.append(wx.StaticText(self, wx.ID_ANY, str(i+1), style=wx.ALIGN_CENTRE | wx.ST_NO_AUTORESIZE))
            self.SensorValue[-1].SetBackgroundColour('BLACK')
            self.SensorValue[-1].SetForegroundColour('GREEN')

        # layout digital indicators
        self.layout_Value = wx.BoxSizer(wx.VERTICAL)

        self.sbox_type = []
        self.sbox_font = wx.Font(15, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        for name in self.sensor_type:
            self.sbox_type.append(wx.StaticBox(self, wx.ID_ANY, name))
            self.sbox_type[-1].SetFont(self.sbox_font)
            self.sbox_type[-1].SetForegroundColour('WHITE')

        self.layout_type = []
        for i in range(len(self.sensor_type)):
            self.layout_type.append(wx.StaticBoxSizer(self.sbox_type[i], wx.VERTICAL))

        self.layout_Data = []
        for i in range(len(self.sensor_type)):
            self.layout_Data.append(wx.GridSizer(rows=len(self.id[i])//self.col_value[i]+1,
                                                 cols=self.col_value[i], gap=(10,5)))

        self.layout_Set = []
        for i in range(len(self.df_cfg_tlm['item'])):
            self.layout_Set.append(wx.GridSizer(rows=2, cols=1, gap=(5,5)))

        for i in range(len(self.df_cfg_tlm['item'])):
            self.layout_Set[i].Add(self.DataButton[i], flag=wx.EXPAND)
            self.layout_Set[i].Add(self.SensorValue[i], flag=wx.EXPAND)

        # Set Data Button and Sensor Value
        for i in range(len(self.sensor_type)):
            for sensor in self.id[i]:
                self.layout_Data[i].Add(self.layout_Set[sensor], flag=wx.EXPAND)

        for i in range(len(self.sensor_type)):
            self.layout_type[i].Add(self.layout_Data[i])
        for i in range(len(self.sensor_type)):
            self.layout_Value.Add(self.layout_type[i])

        for index in self.index_plot:
            self.DataButton[index].SetValue(True)

        # for button in self.DataButton:
        #     button.Bind(wx.EVT_TOGGLEBUTTON, self.graphTest)

    # Configure appearance for plotters to display time histories
    def configure_plotter(self):
        self.fig = Figure(figsize=(6, 8))
        
        self.axes = []
        for i in range(self.n_plot):
            self.axes.append(self.fig.add_subplot(self.n_plot, 1, i+1))
        
        self.canvas = FigureCanvasWxAgg(self, -1, self.fig)

        for i in range(self.n_plot):
            self.axes[i].set_ylim([self.y_min_plot[i], self.y_max_plot[i]])

        for i in range(self.n_plot):
            self.axes[i].set_ylabel(self.item_plot[i] + ' [{}]'.format(self.unit_plot[i]))

        self.t_left = 0
        for i in range(self.n_plot):
            self.axes[i].set_xlim([self.t_left, self.t_left + self.t_range])

        # Plot Empty Chart
        self.canvas.draw()                                            

        # Save Empty Chart Format as Background
        self.backgrounds = []
        for i in range(self.n_plot):
            self.backgrounds.append(self.canvas.copy_from_bbox(self.axes[i].bbox))  

    '''
    def graphTest(self, event):
        self.n_graph = 0
        self.parameter = []
        for button in self.DataButton:
            if button.GetValue():
                self.n_graph += 1
                self.parameter.append(button.GetLabel())

        print(self.n_graph)
        print(self.parameter)
        self.chartGenerator(self.n_graph)
    '''

