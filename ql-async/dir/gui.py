### Standard libraries
#import asyncio
#import decimal
#import math
#import socket
#import sys
import time

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
FETCH_RATE_LATEST_VALUES = 200          # ms/cycle
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
    def __init__(self, latest_values):
        super().__init__(None, wx.ID_ANY, 'Rocket System Information App')

        # receive instance of shared variables
        #self.latest_values = latest_values

        # maxmize GUI window size
        self.Maximize(True)

        self.SetBackgroundColour('Dark Grey')
        #self.SetBackgroundColour('Black')

        # generate Main Graphic
        root_panel = wx.Panel(self, wx.ID_ANY)

        # ??? System panel : Show the feeding system status
        self.chart_panel = ChartPanel(root_panel, latest_values)

        # set layout of panels
        root_layout = wx.GridBagSizer()
        root_layout.Add(self.chart_panel, pos=wx.GBPosition(0,0), flag=wx.EXPAND | wx.ALL, border=10)

        root_panel.SetSizer(root_layout)
        root_layout.Fit(root_panel)

        # bind events
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        # show
        self.Show()


    # Event handler: EVT_CLOSE
    def OnClose(self, event):
        # dig = wx.MessageDialog(self,
        #                        "Do you really want to close this application?",
        #                        "Confirm Exit",
        #                        wx.OK | wx.CANCEL | wx.ICON_QUESTION)
        # result = dig.ShowModal()
        # dig.Destroy()
        # if result == wx.ID_OK:  self.Destroy()
        self.Destroy()

"""
Time History Plots & Current Value Indicators
"""
class ChartPanel(wx.Panel):
    index_x = 1
    __T_RANGE = 30    # [s]

    n_plot = 5

    sensor_type = ['Time [s]', 'P [MPa]', 'T [K]', 'IMU', 'House Keeping']
    col_value = [6, 8, 8, 9, 8]

    def __init__(self, parent, latest_values):
        super().__init__(parent, wx.ID_ANY)

        ### initialize
        self.latest_values = latest_values      # receive instance of shared variables
        self.__F_TLM_IS_ACTIVE = False
        self.dfTlm = pd.DataFrame()
        
        ### load configurations from external files
        # - smt&pcm config
        #self.df_cfg_tlm = th_smt.smt.df_cfg.copy()
        self.df_cfg_tlm = pd.read_excel('./config_tlm.xlsx', sheet_name='smt').dropna(how='all')
        #self.df_cfg_smt = pd.read_excel('./config_tlm.xlsx', sheet_name='smt')
        self.df_cfg_pcm = pd.read_excel('./config_tlm.xlsx', sheet_name='pcm').dropna(how='all')

        self.df_cfg_tlm.reset_index()
        #self.df_cfg_smt.reset_index()
        self.df_cfg_pcm.reset_index()

        # - digital indicator config
        self.load_config_digital_indicator()

        # - plotter config
        self.load_config_plotter()

        ### configure appearance
        self.configure_digital_indicator()
        self.configure_plotter()

        ### layout 
        self.layout = wx.FlexGridSizer(rows=1, cols=2, gap=(20, 0))
        self.layout.Add(self.canvas, flag=wx.EXPAND)                            # plotter
        self.layout.Add(self.layout_Value, flag=wx.ALIGN_CENTER_HORIZONTAL)     # digital indicators
        self.SetSizer(self.layout)

        ### bind events
        # - set timer to fetch latest telemeter data
        self.tmrFetchTelemeterData = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnFetchLatestValues, self.tmrFetchTelemeterData)
        self.tmrFetchTelemeterData.Start(FETCH_RATE_LATEST_VALUES)

        # - set timer to refresh current-value pane
        self.tmrRefreshDigitalIndicator = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnRefreshDigitalIndicator, self.tmrRefreshDigitalIndicator)
        self.tmrRefreshDigitalIndicator.Start(REFLESH_RATE_DIGITAL_INDICATOR)

        # - set timer to refresh time-history pane
        self.tmrRefreshPlotter = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnRefreshPlotter, self.tmrRefreshPlotter)
        self.tmrRefreshPlotter.Start(REFLESH_RATE_PLOTTER)

    # Event handler: EVT_TIMER
    def OnFetchLatestValues(self, event):
        # break off when tlm data not exist
        if len(self.latest_values.df_smt.index) == 0:
            print("GUI awaiting tlm data")
            self.__F_TLM_IS_ACTIVE = False
            return None
        
        # for debug
        # print("GUI FTC: df.index length = %i" % len(self.latest_values.df_smt.index))
        # print(self.latest_values.df_smt) 

        self.__F_TLM_IS_ACTIVE = True

        # fetch current values & store
        self.dfTlm = self.latest_values.df_smt
        # TBREFAC.: should be thread-safe

    # Event handler: EVT_TIMER
    def OnRefreshDigitalIndicator(self, event):
        if self.__F_TLM_IS_ACTIVE == False: return None     # skip refresh
        
        # obtain time slice of dfTlm to avoid unexpected rewrite during refresh
        df_tmp = self.dfTlm.copy()
        
        # refresh display
        for i_sensor in range(len(self.df_cfg_tlm['item'])):
            self.SensorValue[i_sensor].SetLabel(str(np.round(df_tmp.iloc[-1, i_sensor], 2)))
            
    # Event handler: EVT_TIMER
    def OnRefreshPlotter(self, event):
        if self.__F_TLM_IS_ACTIVE == False: return None     # skip refresh

        # for debug
        # print("GUI PLT: F_TLM_IS_ACTIVE = {}".format(self.__F_TLM_IS_ACTIVE))

        ### update data set for plot
        # - obtain time slice of dfTlm by deep copy to avoid unexpected rewrite during refresh
        df_tmp = self.dfTlm.copy()

        # - append latest values
        #print("GUI: append latest values {}".format(df_tmp.iloc[-1,self.index_x]))       # debug
        self.x_series = np.append(self.x_series, df_tmp.iloc[-1,self.index_x])
        # print("GUI PLT: x_series = {}".format(self.x_series))
        # print(self.x_series)

        # self.y_series = np.append(self.y_series, df_tmp.iloc[-1,self.index_x])
        for i in range(self.n_plot):
            self.y_series = np.append(self.y_series, df_tmp.iloc[-1,self.index_plot[i]])
            # self.y_series[i] = np.append(self.y_series[i], df_tmp.iloc[-1,self.index_plot[i]])
            # self.y_series[i][0] = np.append(self.y_series[i][0], df_tmp.iloc[-1,self.index_plot[i]])
        # print("GUI PLT: y_series = {}".format(self.y_series))
        # print(self.y_series)
        # tmp_list = []
        # for i in range(self.n_plot):
        #     # tmp_list = tmp_list.append(df_tmp.iloc[-1,self.index_plot[i]])
        #     tmp_list.append(float(df_tmp.iloc[-1,self.index_x]))
        # self.y_series_not_np.append(tmp_list)
        # print("GUI PLT: y_series_not_np")
        # print(self.y_series_not_np)

        # - determine time max & min
        t_max = self.x_series[-1]
        t_min = t_max - self.__T_RANGE
        # print("t_max = {}, t_min = {}".format(t_max, t_min))

        # - delete items out of the designated time range
        while self.x_series[0] < t_min:
            print("GUI PLT: a member of 'x_series' is out of the range")
            self.x_series = np.delete(self.x_series, 0)
            self.y_series = np.delete(self.y_series, self.n_plot)

        ### refresh plotter
        # TBREFAC.: for-loops should be merged?
        # - clear axes
        for i in range(self.n_plot):
            self.axes[i].cla()

        # - delete x axis and lines by restroring canvas
        # for i in range(self.n_plot):
        #     self.canvas.restore_region(self.backgrounds[i])     

        # - set limit for y axis 
        for i in range(self.n_plot):
            self.axes[i].set_ylim([self.y_min_plot[i], self.y_max_plot[i]])

        # - set label for y axis
        for i in range(self.n_plot):
            self.axes[i].set_ylabel(self.item_plot[i] + ' [{}]'.format(self.unit_plot[i]))

        # - update limit for x axis (time axis)
        for i in range(self.n_plot):
            self.axes[i].set_xlim([t_min, t_max])
        
        # - update alert line
        self.axes[0].axhline(y=1.0, xmin=0, xmax=1, color='red')
        # self.axes[1].axhline(y=500.0, xmin=0, xmax=1, color='red')
        # self.axes[2].axhline(y=500.0, xmin=0, xmax=1, color='red')

        # - update lines
        self.lines = []
        for i in range(self.n_plot):
            # self.lines[i].set_data(self.x_series, self.y_series[i])
            # self.lines[i].set_data(self.x_series, self.y_series[i::self.n_plot])
            # self.lines[i].set_data(self.x_series, np.array(self.y_series_not_np[i::self.n_plot]))
            self.lines.append(self.axes[i].plot(self.x_series, self.y_series[i::self.n_plot])[0])

        # - prepare drawing of new lines
        for i in range(self.n_plot):
            self.axes[i].draw_artist(self.lines[i])             

        # - redraw canvas by blitting
        for i in range(self.n_plot):
            self.fig.canvas.blit(self.axes[i].bbox)

        self.fig.canvas.flush_events()
        print("GUI PLT: redraw plots...")    

    # Load configurations from external files
    def load_config_digital_indicator(self):
        # Load digital indicator appearance config
        self.df_cfg_sensor = (pd.read_excel('./config_sensor.xlsx', sheet_name='smt')).dropna(how='all')

        self.id_time = self.df_cfg_sensor[self.df_cfg_sensor['group'] == 'Time [s]']['ID'].astype(int)
        self.id_p = self.df_cfg_sensor[self.df_cfg_sensor['group'] == 'P [MPa]']['ID'].astype(int)
        self.id_T = self.df_cfg_sensor[self.df_cfg_sensor['group'] == 'T [K]']['ID'].astype(int)
        self.id_imu = self.df_cfg_sensor[self.df_cfg_sensor['group'] == 'IMU']['ID'].astype(int)
        self.id_hk = self.df_cfg_sensor[self.df_cfg_sensor['group'] == 'House Keeping']['ID'].astype(int)

        self.id = [self.id_time, self.id_p, self.id_T, self.id_imu, self.id_hk]


    # Load configurations from external files
    def load_config_plotter(self):  
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
        # initialize
        #self.data_plot = np.ndarray()
        self.x_series = np.empty(0)
        self.y_series = np.empty(0)
        # self.y_series_not_np = []
        # self.lines = np.empty(0)
        # self.lines_not_np = []
        # for i in range(self.n_plot):
        #     self.y_series[i] = np.empty(0)
        #     self.lines[i] = np.empty(0)
        # self.x_series = []
        # self.y_series = []
        # self.lines = []
        
        # prepare empty matplotlib Fugure
        self.fig = Figure(figsize=(6, 8))

        # register Figure with matplotlib Canvas
        self.canvas = FigureCanvasWxAgg(self, -1, self.fig)

        # prepare axes
        self.axes = []

        # - add subplots containing axes to Figure
        for i in range(self.n_plot):
            self.axes.append(self.fig.add_subplot(self.n_plot, 1, i+1))        

        # - set limit for y axis 
        for i in range(self.n_plot):
            self.axes[i].set_ylim([self.y_min_plot[i], self.y_max_plot[i]])

        # - set label for y axis
        for i in range(self.n_plot):
            self.axes[i].set_ylabel(self.item_plot[i] + ' [{}]'.format(self.unit_plot[i]))

        # - set limit for x axis
        # self.t_left = 0
        # for i in range(self.n_plot):
        #     self.axes[i].set_xlim([self.t_left, self.t_left + self.t_range])
        ### "DYNAMIC" X AXIS IS TO BE PREPARED UPON UPDATE ###

        # tentatively draw chart without x axis and plots
        # self.canvas.draw()                                            

        # save empty chart format as background
        # self.backgrounds = []
        # for i in range(self.n_plot):
        #     self.backgrounds.append(self.canvas.copy_from_bbox(self.axes[i].bbox))  


    # def graphTest(self, event):
    #     self.n_graph = 0
    #     self.parameter = []
    #     for button in self.DataButton:
    #         if button.GetValue():
    #             self.n_graph += 1
    #             self.parameter.append(button.GetLabel())

    #     print(self.n_graph)
    #     print(self.parameter)
    #     self.chartGenerator(self.n_graph)


