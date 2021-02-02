### Standard libraries
# import time
import concurrent.futures
import sys

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
REFLESH_RATE_PLOTTER           = 20     # ms/cycle
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
        super().__init__(None, wx.ID_ANY, 'Telemetry Data Quick Look for Detonation Engine System')
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
    __IDX_TIME = 1

    __PLOT_SKIP = 20    ### TBREFAC. ###

    def __init__(self, parent, tlm_latest_data):
        super().__init__(parent, wx.ID_ANY)

        ### initialize
        self.tlm_latest_data = tlm_latest_data      # receive instance of shared variables
        self.__F_TLM_IS_ACTIVE = False
        self.dfTlm = pd.DataFrame()
        self.__PLOT_COUNT = self.__PLOT_SKIP   ### TBREFAC. ###
        
        ### load configurations from external files
        # - smt&pcm config
        # self.df_cfg_smt = pd.read_excel('./config_tlm.xlsx', sheet_name='smt').dropna(how='all')
        # self.df_cfg_pcm = pd.read_excel('./config_tlm.xlsx', sheet_name='pcm').dropna(how='all')

        # self.df_cfg_smt.reset_index()
        # self.df_cfg_pcm.reset_index()

        # - smt
        try: 
            df_cfg_smt = pd.read_excel('./config_tlm_2.xlsx', 
                                        sheet_name='smt', header=0, index_col=None).dropna(how='all')
        except:
            print('Error TLM: "config_tlm.xlsx"!')
            print(self.TLM_TYPE)
            sys.exit()

        self.TlmItemList_smt = df_cfg_smt['item'].values.tolist()
        self.TlmItemAttr_smt = df_cfg_smt.to_dict(orient='index')
        self.N_ITEM_SMT = len(self.TlmItemList_smt)

        # - pcm
        try: 
            df_cfg_pcm = pd.read_excel('./config_tlm_2.xlsx', 
                                        sheet_name='pcm', header=0, index_col=None).dropna(how='all')
        except:
            print('Error TLM: "config_tlm.xlsx"!')
            print(self.TLM_TYPE)
            sys.exit()

        self.TlmItemList_pcm = df_cfg_pcm['item'].values.tolist()
        self.TlmItemAttr_pcm = df_cfg_pcm.to_dict(orient='index')
        self.N_ITEM_PCM = len(self.TlmItemList_pcm)

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
        self.layout.Add(self.IndicatorPane, flag=wx.ALIGN_CENTER_HORIZONTAL)    # digital indicators
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
        if ( len(self.tlm_latest_data.df_smt.index) == 0 or
             len(self.tlm_latest_data.df_pcm.index) == 0 ):
            print('GUI awaiting SMT and/or PCM data')
            # print('GUI awaiting smt data')
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
        self.dfTlm_smt = self.tlm_latest_data.df_smt
        self.dfTlm_pcm = self.tlm_latest_data.df_pcm
        # self.dfTlm = self.tlm_latest_data.df_smt
        ### TBREFAC.: should be thread safe

    # Event handler: EVT_TIMER
    def OnRefreshDigitalIndicator(self, event):
        if self.__F_TLM_IS_ACTIVE == False: return None     # skip refresh
        
        # obtain time slice of dfTlm to avoid unexpected rewrite during refresh
        df_smt_tmp = self.dfTlm_smt.copy()
        df_pcm_tmp = self.dfTlm_pcm.copy()
        # df_tmp = self.dfTlm.copy()
        
        # refresh indicators
        for i in self.GroupAttr.keys():
            ### T.B.REFAC ###
            for ii in range(self.GroupAttr[i]['rows'] * self.GroupAttr[i]['cols']):
                # initialize
                j = -1

                # search throughout smt items
                for iii in range(self.N_ITEM_SMT):
                    if ( self.TlmItemAttr_smt[iii]['group'] == self.GroupAttr[i]['label'] and
                         self.TlmItemAttr_smt[iii]['item order'] == ii ) :
                        j = iii
                        break    
                print(f'GUI IND: j = {j}')

                # assign items in grids
                if j != -1:
                    print('Im here')
                    self.stxtIndicator[j].SetLabel(str(np.round(df_smt_tmp.iloc[-1, j], 2)))
                    continue

                # search throughout pcm items
                for iii in range(self.N_ITEM_PCM):
                    if ( self.TlmItemAttr_pcm[iii]['group'] == self.GroupAttr[i]['label'] and
                         self.TlmItemAttr_pcm[iii]['item order'] == ii ) :
                        j = iii + self.N_ITEM_SMT
                        break
                print(f'GUI IND: j = {j}')

                # assign items in grids
                if j != -1:
                    self.stxtIndicator[j].SetLabel(str(np.round(df_pcm_tmp.iloc[-1, j-self.N_ITEM_SMT], 2)))
                    
        # refresh display
        # for i_sensor in range(len(self.df_cfg_smt['item'])):
        #     self.stxtIndicator[i_sensor].SetLabel(str(np.round(df_tmp.iloc[-1, i_sensor], 2)))
            
    # Event handler: EVT_TIMER
    def OnRefreshPlotter(self, event):
        if self.__F_TLM_IS_ACTIVE == False: return None     # skip refresh
        # for debug
        # print("GUI PLT: F_TLM_IS_ACTIVE = {}".format(self.__F_TLM_IS_ACTIVE))

        ###
        ### update data set for plot
        # - obtain time slice of dfTlm by deep copy to avoid unexpected rewrite during refresh
        df_smt_tmp = self.dfTlm_smt.copy()
        df_pcm_tmp = self.dfTlm_pcm.copy()
        # df_tmp = self.dfTlm.copy()
        df_tmp = pd.concat([df_smt_tmp, df_pcm_tmp], axis=1)

        # - update plot points by appending latest values
        self.x_series = np.append(self.x_series, df_tmp.iloc[-1,self.__IDX_TIME])
        for i in range(self.__N_PLOTTER):
            self.y_series = np.append(self.y_series, df_tmp.iloc[-1,self.index_plot[i]])
        # self.x_series = np.append(self.x_series, df_smt_tmp.iloc[-1,self.__IDX_TIME])
        # for i in range(self.__N_PLOTTER):
        #     self.y_series = np.append(self.y_series, df_smt_tmp.iloc[-1,self.index_plot[i]])
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
        ### T.B.REFAC ###
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
            self.axes[i].set_ylim([self.PltAttr[i].y_min, self.PltAttr[i].y_max])

            # set label for y axis
            self.axes[i].set_ylabel(self.PltAttr[i].y_label)

            # update alert line
            self.axes[i].axhline(y=self.PltAttr[i].alart_lim_u, xmin=0, xmax=1, color='red')
            self.axes[i].axhline(y=self.PltAttr[i].alart_lim_u, xmin=0, xmax=1, color='red')
        
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
        self.GroupAttr = {
            0: {'idx': 0, 'label': 'Time',          'rows': 1, 'cols' : 6},
            1: {'idx': 1, 'label': 'DES State',     'rows': 5, 'cols' : 6},
            2: {'idx': 2, 'label': 'Pressure',      'rows': 2, 'cols' : 6},
            3: {'idx': 3, 'label': 'Temperature',   'rows': 2, 'cols' : 6},
            4: {'idx': 4, 'label': 'IMU',           'rows': 2, 'cols' : 6},
            5: {'idx': 5, 'label': 'House Keeping', 'rows': 3, 'cols' : 6}
        }
        
        # self.sensor_type = ['Time [s]', 'Pressure [MPa]', 'Temperature [K]', 'IMU', 'House Keeping']
        # self.col_value = [6, 6, 6, 6, 6]
        # self.col_value = [6, 8, 8, 9, 8]

        # self.GroupName = ['Time', 'DES State', 'Pressure', 'Temperature', 'IMU', 'House Keeping']
        # self.GroupName = {0:'Time', 1:'DES State', 2:'Pressure', 3:'Temperature', 4:'IMU', 5:'House Keeping'}

        # Load digital indicator appearance config
        # self.df_cfg_sensor = (pd.read_excel('./config_sensor.xlsx', sheet_name='smt')).dropna(how='all')

        # self.id_time = self.df_cfg_sensor[self.df_cfg_sensor['group'] == 'Time [s]']['ID'].astype(int)
        # self.id_p = self.df_cfg_sensor[self.df_cfg_sensor['group'] == 'P [MPa]']['ID'].astype(int)
        # self.id_T = self.df_cfg_sensor[self.df_cfg_sensor['group'] == 'T [K]']['ID'].astype(int)
        # self.id_imu = self.df_cfg_sensor[self.df_cfg_sensor['group'] == 'IMU']['ID'].astype(int)
        # self.id_hk = self.df_cfg_sensor[self.df_cfg_sensor['group'] == 'House Keeping']['ID'].astype(int)

        # self.id = [self.id_time, self.id_p, self.id_T, self.id_imu, self.id_hk]

        # self.TlmItemList_smt = df_cfg_smt['item'].values.tolist()
        # self.TlmItemAttr_smt = df_cfg_smt.to_dict(orient='index')

        # self.id_time = self.TlmItemList_smt
        # df_cfg_sensor[self.df_cfg_sensor['group'] == 'Time [s]']['ID'].astype(int)

    # Configure appearance for digital indicators to display current values
    # <hierarchy>
    #   IndicatorPane - lytSBoxGroup
    #                 - sboxGroup    - 
    #
    def configure_digital_indicator(self):
        self.IndicatorPane = wx.BoxSizer(wx.VERTICAL)

        ### generate containers to groupe indicators (StaticBox)
        self.SBoxGroup = []
        self.lytSBoxGroup = []
        # for name in self.sensor_type:
        # for strGroupName in self.GroupName:
        for i in self.GroupAttr.keys():
            # - generate an instance
            # self.sbox_type.append(wx.StaticBox(self, wx.ID_ANY, name))
            self.SBoxGroup.append(wx.StaticBox(self, wx.ID_ANY, self.GroupAttr[i]['label']))
            self.SBoxGroup[-1].SetForegroundColour('WHITE')
            self.SBoxGroup[-1].SetFont(wx.Font(15, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            
            # - lay out the instance
            self.lytSBoxGroup.append(wx.StaticBoxSizer(self.SBoxGroup[-1], wx.VERTICAL))

            self.IndicatorPane.Add(self.lytSBoxGroup[-1])
            # self.IndicatorPane.Add(self.lytSBoxGroup[self.GroupName.index(strGroupName)])

        # self.IndicatorPane.Add(self.lytSBoxGroup)

        ### generate indicators & their labels
        self.tbtnLabel = []
        self.stxtIndicator = []
        self.lytPair = []           # pair of Indicator & Label
        
        # smt items
        # for i in range(len(self.df_cfg_smt['item'])):
        for i in range(self.N_ITEM_SMT):
            # generate instance 
            # - item label (ToggleButton)
            self.tbtnLabel.append(
                wx.ToggleButton(self, wx.ID_ANY, self.TlmItemAttr_smt[i]['item'], size=(140,22)))
            
            # - digital indicator (StaticText)
            self.stxtIndicator.append(
                wx.StaticText(self, wx.ID_ANY, str(i), style=wx.ALIGN_CENTRE | wx.ST_NO_AUTORESIZE))
            self.stxtIndicator[-1].SetBackgroundColour('BLACK')
            self.stxtIndicator[-1].SetForegroundColour('GREEN')
            
            # - pair of item label & inidicator
            self.lytPair.append(wx.GridSizer(rows=2, cols=1, gap=(0,0)))
            self.lytPair[-1].Add(self.tbtnLabel[-1], flag=wx.EXPAND)
            self.lytPair[-1].Add(self.stxtIndicator[-1], flag=wx.EXPAND)

        # pcm items
        # for i in range(N_ITEM_SMT, N_ITEM_SMT + N_ITEM_PCM):
        for i in range(self.N_ITEM_PCM):
            # generate instance 
            # - item label (ToggleButton)
            self.tbtnLabel.append(
                wx.ToggleButton(self, wx.ID_ANY, self.TlmItemAttr_pcm[i]['item'], size=(120,22)))
            
            # - digital indicator (StaticText)
            self.stxtIndicator.append(
                wx.StaticText(self, wx.ID_ANY, str(i + self.N_ITEM_SMT), style=wx.ALIGN_CENTRE | wx.ST_NO_AUTORESIZE))
            self.stxtIndicator[-1].SetBackgroundColour('BLACK')
            self.stxtIndicator[-1].SetForegroundColour('GREEN')

            # - pair of item label & inidicator
            self.lytPair.append(wx.GridSizer(rows=2, cols=1, gap=(0,0)))
            self.lytPair[-1].Add(self.tbtnLabel[-1], flag=wx.EXPAND)
            self.lytPair[-1].Add(self.stxtIndicator[-1], flag=wx.EXPAND)

        # - ToggleButton: item labels for indicators
        # self.tbtnLabel = []
        # for index in self.df_cfg_smt['item']:
        #     self.tbtnLabel.append(wx.ToggleButton(self, wx.ID_ANY, index, size=(120,22)))

        ### lay out digital indicators
        # - containers by StaticBoxSizer
        # self.lytSBoxGroup = []
        # # for i in range(len(self.sensor_type)):
        # for i in range(len(self.GroupName)):
        #     self.lytSBoxGroup.append(wx.StaticBoxSizer(self.SBoxGroup[i], wx.VERTICAL))

        # - pairs of an item label & an inidicator by GridSizer
        # -- make pairs of an item label & an inidicator
        # self.lytPair = []
        # for i in range(len(self.df_cfg_smt['item'])):
        #     # self.layout_Set.append(wx.GridSizer(rows=2, cols=1, gap=(5,5)))
        #     self.lytPair.append(wx.GridSizer(rows=2, cols=1, gap=(0,0)))
        #     self.lytPair[i].Add(self.tbtnLabel[i], flag=wx.EXPAND)
        #     self.lytPair[i].Add(self.stxtIndicator[i], flag=wx.EXPAND)

        # lay out pairs of indicators & labels in the grouping SBoxes
        self.lytIndicator = []
        # for i in range(len(self.sensor_type)):
        for i in self.GroupAttr.keys():
            # generate grid in the grouping SBox
            self.lytIndicator.append(
                wx.GridSizer(rows=self.GroupAttr[i]['rows'], cols=self.GroupAttr[i]['cols'], gap=(10,5)))
            
            # place items in the grid
            for ii in range(self.GroupAttr[i]['rows'] * self.GroupAttr[i]['cols']):
                # initialize
                j = -1

                # search throughout smt items
                for iii in range(self.N_ITEM_SMT):
                    if ( self.TlmItemAttr_smt[iii]['group'] == self.GroupAttr[i]['label'] and
                         self.TlmItemAttr_smt[iii]['item order'] == ii ) :
                        j = iii
                        break    

                # search throughout pcm items
                for iii in range(self.N_ITEM_PCM):
                    if ( self.TlmItemAttr_pcm[iii]['group'] == self.GroupAttr[i]['label'] and
                         self.TlmItemAttr_pcm[iii]['item order'] == ii ) :
                        j = iii + self.N_ITEM_SMT
                        break    
                
                # assign items in grids
                if j == -1:
                    self.lytIndicator[i].Add((0,0))                         # empty cell
                    # self.lytIndicator[i].Add(wx.StaticText(self, -1, ''))   # empty cell
                else:
                    self.lytIndicator[i].Add(self.lytPair[j], flag=wx.EXPAND)
            
            # for sensor in self.id[i]:
            #     self.lytIndicator[i].Add(self.layout_Set[sensor], flag=wx.EXPAND)

            # snap
            self.lytSBoxGroup[i].Add(self.lytIndicator[i])

        # set states for ToggleButton
        for index in self.index_plot:
            self.tbtnLabel[index].SetValue(True)

        # for button in self.tbtnLabel:
        #     button.Bind(wx.EVT_TOGGLEBUTTON, self.graphTest)

    # Load configurations from external files
    def load_config_plotter(self):
        ### TBREFAC.: TEMPORALLY DESIGNATED BY LITERALS ###

        # Load plotter appearance config
        # self.df_cfg_plot = (pd.read_excel('./config_plot.xlsx', sheet_name='smt')).dropna(how='all')

        # self.index_plot = [self.df_cfg_plot['ID'][self.df_cfg_plot['plot_1'].astype(bool)].astype(int).iat[0],
        #                    self.df_cfg_plot['ID'][self.df_cfg_plot['plot_2'].astype(bool)].astype(int).iat[0],
        #                    self.df_cfg_plot['ID'][self.df_cfg_plot['plot_3'].astype(bool)].astype(int).iat[0],
        #                    self.df_cfg_plot['ID'][self.df_cfg_plot['plot_4'].astype(bool)].astype(int).iat[0],
        #                    self.df_cfg_plot['ID'][self.df_cfg_plot['plot_5'].astype(bool)].astype(int).iat[0]]

        # handle exception
        if self.__N_PLOTTER > 5: self.__N_PLOTTER = 5

        # load attributions
        self.index_plot =[]
        self.PltAttr = []
        # for i in range(self.__N_PLOTTER):
        #     str_tmp = 'plot_' + str(i+1)
        #     self.PltAttr.append(PltAttr(
        #         y_label = self.df_cfg_plot['item'][self.df_cfg_plot[str_tmp].astype(bool)].iat[0],
        #         y_unit = self.df_cfg_plot['unit'][self.df_cfg_plot[str_tmp].astype(bool)].iat[0],
        #         y_min = self.df_cfg_plot['y_min'][self.df_cfg_plot[str_tmp].astype(bool)].iat[0],
        #         y_max = self.df_cfg_plot['y_max'][self.df_cfg_plot[str_tmp].astype(bool)].iat[0],
        #         alart_lim_u = 10,
        #         alart_lim_l = 0.0))
        for i in range(self.__N_PLOTTER):
            # search throughout smt items
            for iii in range(self.N_ITEM_SMT):
                if self.TlmItemAttr_smt[iii]['plot #'] == i:
                    self.index_plot.append(iii)
                    self.PltAttr.append(PlotterAttributions(
                        y_label = self.TlmItemAttr_smt[iii]['item'],
                        y_unit = self.TlmItemAttr_smt[iii]['unit'],
                        y_min = float(self.TlmItemAttr_smt[iii]['y_min']),
                        y_max = float(self.TlmItemAttr_smt[iii]['y_max']),
                        alart_lim_l = float(self.TlmItemAttr_smt[iii]['alert_lim_l']),
                        alart_lim_u = float(self.TlmItemAttr_smt[iii]['alert_lim_u'])))
                    break
            else:
                # search throughout pcm items
                for iii in range(self.N_ITEM_PCM):
                    if self.TlmItemAttr_pcm[iii]['plot #'] == i:
                        self.index_plot.append(iii + self.__N_PLOTTER)
                        self.PltAttr.append(PlotterAttributions(
                            y_label = self.TlmItemAttr_pcm[iii]['item'],
                            y_unit = self.TlmItemAttr_pcm[iii]['unit'],
                            y_min = float(self.TlmItemAttr_pcm[iii]['y_min']),
                            y_max = float(self.TlmItemAttr_pcm[iii]['y_max']),
                            alart_lim_l = float(self.TlmItemAttr_pcm[iii]['alert_lim_l']),
                            alart_lim_u = float(self.TlmItemAttr_pcm[iii]['alert_lim_u'])))
                        break
            
            continue
        
        # for debug
        # print('GUI PLT: PltAttr')
        # print(self.PltAttr[0].y_min)
        # print(self.PltAttr[1].y_min)
        # print(self.PltAttr[2].y_min)
        # print(self.PltAttr[3].y_min)
        # print(self.PltAttr[4].y_min)

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
            self.axes[i].set_ylim([self.PltAttr[i].y_min, self.PltAttr[i].y_max])

            # - set label for y axis
            self.axes[i].set_ylabel(self.PltAttr[i].y_label + f' [{self.PltAttr[i].y_unit}]')

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
    #     for button in self.tbtnLabel:
    #         if button.GetValue():
    #             self.n_graph += 1
    #             self.parameter.append(button.GetLabel())

    #     print(self.n_graph)
    #     print(self.parameter)
    #     self.chartGenerator(self.n_graph)


# retain plotter attributions
class PlotterAttributions():
    def __init__(self, y_label="", y_unit="", 
                y_min=0.0, y_max=1.0, alart_lim_l=0.0, alart_lim_u=1.0) -> None:
        self.y_label = y_label
        self.y_unit = y_unit
        self.y_min = y_min
        self.y_max = y_max
        self.alart_lim_l = alart_lim_l
        self.alart_lim_u = alart_lim_u
