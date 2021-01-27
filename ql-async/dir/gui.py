### Standard libraries
# import time
import concurrent.futures

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
FETCH_RATE_LATEST_VALUES       = 20     # ms/cycle
# FETCH_RATE_LATEST_VALUES       = 200     # ms/cycle
REFLESH_RATE_PLOTTER           = 100    # ms/cycle
REFLESH_RATE_DIGITAL_INDICATOR = 350    # ms/cycle


"""
Matplotlib configuration
"""
plt.style.use('dark_background')

# Margin
plt.rcParams["figure.subplot.bottom"] = 0.03    # Bottom
plt.rcParams["figure.subplot.top"]    = 0.99    # Top
plt.rcParams["figure.subplot.left"]   = 0.15    # Left
plt.rcParams["figure.subplot.right"]  = 0.97    # Right
plt.rcParams["figure.subplot.hspace"] = 0.1     # Height Margin between subplots


"""
Top Level Window
"""
class frmMain(wx.Frame):
    def __init__(self, internal_flags, tlm_latest_data):
        super().__init__(None, wx.ID_ANY, 'Rocket System Information App')
        # receive instance of shared variables
        self.internal_flags = internal_flags
        #self.latest_values = latest_values

        # maxmize GUI window size
        self.Maximize(True)

        self.SetBackgroundColour('Dark Grey')
        #self.SetBackgroundColour('Black')

        # generate Main Graphic
        root_panel = wx.Panel(self, wx.ID_ANY)

        # ??? System panel : Show the feeding system status
        self.chart_panel = ChartPanel(root_panel, tlm_latest_data)

        # lay out panels by sizer
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
        self.internal_flags.GUI_TASK_IS_DONE = True

"""
Time History Plots & Current Value Indicators
"""
class ChartPanel(wx.Panel):
    __N_PLOTTER = 5
    __T_RANGE = 30    # [s]
    __IND_TIME = 1

    __PLOT_SKIP = 50    ### TBREFAC. ###

    sensor_type = ['Time [s]', 'Pressure [MPa]', 'Temperature [K]', 'IMU', 'House Keeping']
    col_value = [6, 6, 6, 6, 6]
    # col_value = [6, 8, 8, 9, 8]

    def __init__(self, parent, tlm_latest_data):
        super().__init__(parent, wx.ID_ANY)

        ### initialize
        self.tlm_latest_data = tlm_latest_data      # receive instance of shared variables
        self.__F_TLM_IS_ACTIVE = False
        self.dfTlm = pd.DataFrame()
        self.__PLOT_COUNT = self.__PLOT_SKIP   ### TBREFAC. ###
        
        ### load configurations from external files
        # - smt&pcm config
        self.df_cfg_smt = pd.read_excel('./config_tlm.xlsx', sheet_name='smt').dropna(how='all')
        self.df_cfg_pcm = pd.read_excel('./config_tlm.xlsx', sheet_name='pcm').dropna(how='all')

        self.df_cfg_smt.reset_index()
        self.df_cfg_pcm.reset_index()

        # - digital indicator config
        self.load_config_digital_indicator()

        # - plotter config
        self.load_config_plotter()

        ### configure appearance
        self.configure_digital_indicator()
        self.configure_plotter()

        ### lay out GUI elements by sizer 
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
        # print('GUI FTC: fetched tlm data')
        
        # break off when tlm data not exist
        if len(self.tlm_latest_data.df_smt.index) == 0:
            print('GUI awaiting smt data')
            self.__F_TLM_IS_ACTIVE = False
            return None
        
        # for debug
        # print('GUI FTC: df.index length = {}'.format(len(self.tlm_latest_data.df_smt.index)))
        # print(self.tlm_latest_data.df_smt) 

        self.__F_TLM_IS_ACTIVE = True

        # if self.dfTlm == self.tlm_latest_data.df_smt:
        #     print('GUI FTC: TLM data has NOT been updated!')
        #     return None
        
        # fetch current values & store
        self.dfTlm = self.tlm_latest_data.df_smt
        ### TBREFAC.: should be thread safe

    # Event handler: EVT_TIMER
    def OnRefreshDigitalIndicator(self, event):
        if self.__F_TLM_IS_ACTIVE == False: return None     # skip refresh
        
        # obtain time slice of dfTlm to avoid unexpected rewrite during refresh
        df_tmp = self.dfTlm.copy()
        
        # refresh display
        for i_sensor in range(len(self.df_cfg_smt['item'])):
            self.SensorValue[i_sensor].SetLabel(str(np.round(df_tmp.iloc[-1, i_sensor], 2)))
            
    # Event handler: EVT_TIMER
    def OnRefreshPlotter(self, event):
        if self.__F_TLM_IS_ACTIVE == False: return None     # skip refresh
        # for debug
        # print("GUI PLT: F_TLM_IS_ACTIVE = {}".format(self.__F_TLM_IS_ACTIVE))

        ###
        ### update data set for plot
        # - obtain time slice of dfTlm by deep copy to avoid unexpected rewrite during refresh
        df_tmp = self.dfTlm.copy()

        # - update plot points by appending latest values
        self.x_series = np.append(self.x_series, df_tmp.iloc[-1,self.__IND_TIME])        
        for i in range(self.__N_PLOTTER):
            self.y_series = np.append(self.y_series, df_tmp.iloc[-1,self.index_plot[i]])
        # print("GUI: append latest values {}".format(df_tmp.iloc[-1,self.index_x]))
        # print("GUI PLT: x_series = {}".format(self.x_series))
        # print("GUI PLT: y_series = {}".format(self.y_series))

        # - determine time max & min
        self.t_max = self.x_series[-1]
        self.t_min = self.t_max - self.__T_RANGE
        # print("t_max = {}, t_min = {}".format(self.t_max, self.t_min))

        # - delete plot points out of the designated time range
        while self.x_series[0] < self.t_min:
            print("GUI PLT: a member of 'x_series' is out of the range")
            self.x_series = np.delete(self.x_series, 0)
            self.y_series = np.delete(self.y_series, np.s_[0:self.__N_PLOTTER])

        # skip redraw
        ### TBREFAC. ###
        if self.__PLOT_COUNT != self.__PLOT_SKIP:
            self.__PLOT_COUNT += 1
            return None
        self.__PLOT_COUNT = 0

    #     # run tlm_handler concurrently in other threads
    #     executor = concurrent.futures.ThreadPoolExecutor()
    #     # executor = concurrent.futures.ProcessPoolExecutor()
    #     executor.submit(self.__redraw_plotter_pane)

    # def __redraw_plotter_pane(self):
        ###
        ### refresh plotter
        self.lines = []
        for i in range(self.__N_PLOTTER):
            # delete x axis and lines by restroring canvas
            self.canvas.restore_region(self.backgrounds[i])

            # clear axes
            self.axes[i].cla()

            # update limit for x axis
            self.axes[i].set_xlim([self.t_min, self.t_max])

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
        ### TBREFAC.: TEMPORALLY DESIGNATED BY LITERALS ###

        # Load plotter appearance config
        self.df_cfg_plot = (pd.read_excel('./config_plot.xlsx', sheet_name='smt')).dropna(how='all')

        self.index_plot = [self.df_cfg_plot['ID'][self.df_cfg_plot['plot_1'].astype(bool)].astype(int).iat[0],
                           self.df_cfg_plot['ID'][self.df_cfg_plot['plot_2'].astype(bool)].astype(int).iat[0],
                           self.df_cfg_plot['ID'][self.df_cfg_plot['plot_3'].astype(bool)].astype(int).iat[0],
                           self.df_cfg_plot['ID'][self.df_cfg_plot['plot_4'].astype(bool)].astype(int).iat[0],
                           self.df_cfg_plot['ID'][self.df_cfg_plot['plot_5'].astype(bool)].astype(int).iat[0]]

        # handle exception
        if self.__N_PLOTTER > 5: self.__N_PLOTTER = 5

        # load attributions
        self.plt_attr = []
        for i in range(self.__N_PLOTTER):
            str_tmp = 'plot_' + str(i+1)
            self.plt_attr.append(PltAttr(
                y_label = self.df_cfg_plot['item'][self.df_cfg_plot[str_tmp].astype(bool)].iat[0],
                y_unit = self.df_cfg_plot['unit'][self.df_cfg_plot[str_tmp].astype(bool)].iat[0],
                y_min = self.df_cfg_plot['y_min'][self.df_cfg_plot[str_tmp].astype(bool)].iat[0],
                y_max = self.df_cfg_plot['y_max'][self.df_cfg_plot[str_tmp].astype(bool)].iat[0],
                alart_lim_u = 10,
                alart_lim_l = 0.0))

    # Configure appearance for digital indicators to display current values
    def configure_digital_indicator(self):
        ### generate instances        
        # - StaticText: digital indicators
        self.SensorValue = []
        for i in range(len(self.df_cfg_smt['item'])):
            self.SensorValue.append(wx.StaticText(self, wx.ID_ANY, str(i+1), style=wx.ALIGN_CENTRE | wx.ST_NO_AUTORESIZE))
            self.SensorValue[-1].SetBackgroundColour('BLACK')
            self.SensorValue[-1].SetForegroundColour('GREEN')

        # - ToggleButton: item labels for indicators
        self.DataButton = []
        for index in self.df_cfg_smt['item']:
            self.DataButton.append(wx.ToggleButton(self, wx.ID_ANY, index, size=(120,22)))

        # - StaticBox: container grouping labels and indicators
        self.sbox_font = wx.Font(15, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.sbox_type = []
        for name in self.sensor_type:
            self.sbox_type.append(wx.StaticBox(self, wx.ID_ANY, name))
            self.sbox_type[-1].SetFont(self.sbox_font)
            self.sbox_type[-1].SetForegroundColour('WHITE')

        ### lay out digital indicators
        self.layout_Value = wx.BoxSizer(wx.VERTICAL)

        # - containers by StaticBoxSizer
        self.layout_type = []
        for i in range(len(self.sensor_type)):
            self.layout_type.append(wx.StaticBoxSizer(self.sbox_type[i], wx.VERTICAL))

        # - pairs of an item label & an inidicator by GridSizer
        # -- make pairs of an item label & an inidicator
        self.layout_Set = []
        for i in range(len(self.df_cfg_smt['item'])):
            # self.layout_Set.append(wx.GridSizer(rows=2, cols=1, gap=(5,5)))
            self.layout_Set.append(wx.GridSizer(rows=2, cols=1, gap=(0,0)))
            self.layout_Set[i].Add(self.DataButton[i], flag=wx.EXPAND)
            self.layout_Set[i].Add(self.SensorValue[i], flag=wx.EXPAND)

        # -- snap the pairs into grid
        self.layout_Data = []
        for i in range(len(self.sensor_type)):
            self.layout_Data.append(wx.GridSizer(rows=len(self.id[i])//self.col_value[i]+1,
                                                 cols=self.col_value[i], 
                                                 gap=(10,5)))
            for sensor in self.id[i]:
                self.layout_Data[i].Add(self.layout_Set[sensor], flag=wx.EXPAND)

            # snap
            self.layout_type[i].Add(self.layout_Data[i])
            
            self.layout_Value.Add(self.layout_type[i])

        # set states for ToggleButton
        for index in self.index_plot:
            self.DataButton[index].SetValue(True)

        # for button in self.DataButton:
        #     button.Bind(wx.EVT_TOGGLEBUTTON, self.graphTest)


    # Configure appearance for plotters to display time histories
    def configure_plotter(self):
        # initialize data set for plot
        self.x_series = np.empty(0)
        self.y_series = np.empty(0)
        
        # generate empty matplotlib Fugure
        self.fig = Figure(figsize=(6, 8))
        
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
            self.axes[i].set_ylabel(self.plt_attr[i].y_label + f' [{self.plt_attr[i].y_unit}]')

        # tentatively draw canvas without plot points to save as background
        self.canvas.draw()                                            

        # save the empty canvas as background
        # NOTE: backgrounds become iterrable hereafter
        self.backgrounds = []
        for i in range(self.__N_PLOTTER):
            self.backgrounds.append(self.canvas.copy_from_bbox(self.axes[i].bbox))

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
