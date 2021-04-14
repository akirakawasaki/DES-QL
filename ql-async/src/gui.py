### Standard libraries
import queue
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
RATE_FETCH_LATEST_VALUES       = 25     # ms/cycle
RATE_REFLESH_DIGITAL_INDICATOR = 800    # ms/cycle
RATE_REFLESH_PLOTTER           = 100    # ms/cycle

"""
Matplotlib configuration
"""
plt.style.use('dark_background')

# Plotter margins
plt.rcParams["figure.subplot.bottom"] = 0.03    # Bottom
plt.rcParams["figure.subplot.top"]    = 0.99    # Top
plt.rcParams["figure.subplot.left"]   = 0.15    # Left
plt.rcParams["figure.subplot.right"]  = 0.97    # Right
plt.rcParams["figure.subplot.hspace"] = 0.05    # Height Margin between subplots


#
#   Top-level window
#
class frmMain(wx.Frame):
    ### Class constants
    
    #
    WINDOW_CAPTION = 'Telemetry Data Quick Look for Detonation Engine System'
    
    # input file pathes
    FPATH_CONFIG = './config_tlm.xlsx'
    
    def __init__(self, q_msg_smt, q_msg_pcm, q_data_smt, q_data_pcm):
        super().__init__(None, wx.ID_ANY, self.WINDOW_CAPTION)

        # shere arguments within the class
        self.q_msg_smt = q_msg_smt      # sending ONLY (to TLM)
        self.q_msg_pcm = q_msg_pcm      # sending ONLY (to TLM)
        self.q_data_smt = q_data_smt    # receiving ONLY (from TLM)
        self.q_data_pcm = q_data_pcm    # receiving ONLY (from TLM)

        ### Initialize data
        # - load configurations from an external file
        # smt
        try: 
            df_cfg_smt = pd.read_excel(self.FPATH_CONFIG, 
                                        sheet_name='smt', header=0, index_col=0).dropna(how='all')
        except:
            print(f'Error GUI: Config file "{self.FPATH_CONFIG}" NOT exists! smt')
            sys.exit()

        dictTlmItemAttr_smt = df_cfg_smt.to_dict(orient='index')

        # pcm
        try: 
            df_cfg_pcm = pd.read_excel(self.FPATH_CONFIG, 
                                        sheet_name='pcm', header=0, index_col=0).dropna(how='all')
        except:
            print(f'Error GUI: Config file "{self.FPATH_CONFIG}" NOT exists! pcm')
            sys.exit()

        dictTlmItemAttr_pcm = df_cfg_pcm.to_dict(orient='index')

        # check key duplication
        if (dictTlmItemAttr_smt.keys() & dictTlmItemAttr_pcm.keys()) != set():
            print(f'Error GUI: Keys are duplicated between SMT & PCM! Check CONFIG file.')
            sys.exit()

        # prepare hash: Item name -> {Item attributions}
        self.dictTlmItemAttr = {}
        self.dictTlmItemAttr.update(dictTlmItemAttr_smt)
        self.dictTlmItemAttr.update(dictTlmItemAttr_pcm)

        # - initialize a dictionary to store latest values
        self.dictTlmLatestValues = {}

        self.dictTlmLatestValues_smt = dict.fromkeys(['Line# (smt)'] + list(dictTlmItemAttr_smt.keys()), np.nan)
        self.dictTlmLatestValues.update(self.dictTlmLatestValues_smt)
        self.dfTlm_smt = pd.DataFrame()

        self.dictTlmLatestValues_pcm = dict.fromkeys(['Line# (pcm)'] + list(dictTlmItemAttr_pcm.keys()), np.nan)
        self.dictTlmLatestValues.update(self.dictTlmLatestValues_pcm)
        self.dfTlm_pcm = pd.DataFrame()

        ###
        self.F_TLM_IS_ACTIVE = False

        ### configure GUI appearance 
        # - initialize attributions
        self.SetBackgroundColour('Black')
        # self.SetBackgroundColour('Dark Grey')
        self.Maximize(True)

        # - 
        self.pnlPlotter = pnlPlotter(parent=self)                       # Time History Plots
        self.pnlDigitalIndicator = pnlDigitalIndicator(parent=self)     # Current Value Indicators

        # - lay out panels by using sizer
        # layout = wx.FlexGridSizer(rows=1, cols=2, gap=(0,0))
        layout = wx.BoxSizer(wx.HORIZONTAL)
        layout.Add(window=self.pnlPlotter, proportion=0, flag=wx.ALL | wx.EXPAND, border=20)            # plotter pane
        layout.Add(window=self.pnlDigitalIndicator, proportion=0, flag=wx.ALL | wx.EXPAND, border=20)   # digital indicator pane
        self.SetSizer(layout)

        ### Bind events
        # - close
        self.Bind(wx.EVT_CLOSE, self.OnClose)
                
        # - timer to fetch latest telemeter data
        self.tmrFetchTelemeterData = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnFetchLatestValues, self.tmrFetchTelemeterData)
        self.tmrFetchTelemeterData.Start(RATE_FETCH_LATEST_VALUES)

    # Event handler: EVT_CLOSE
    def OnClose(self, event):
        # quit tlm handlers
        self.q_msg_smt.put_nowait('stop') 
        self.q_msg_pcm.put_nowait('stop')

        self.Destroy()

    # Event handler: EVT_TIMER
    def OnFetchLatestValues(self, event):
        # print('GUI FTC: fetched tlm data')
        
        self.dfTlm_smt = pd.DataFrame()
        self.dfTlm_pcm = pd.DataFrame()

        ### fetch current values
        # - smt
        while True:
            try:
                self.dfTlm_smt = self.q_data_smt.get_nowait()
            except queue.Empty:
                break
            else:
                self.q_data_smt.task_done()
        # - pcm
        while True:
            try:
                self.dfTlm_pcm = self.q_data_pcm.get_nowait()
            except queue.Empty:
                break
            else:
                self.q_data_pcm.task_done()

        # break off when tlm data not exist
        if len(self.dfTlm_smt.index) == 0 or len(self.dfTlm_pcm.index) == 0:
            print('GUI FTC: awaiting SMT and/or PCM data')
            self.F_TLM_IS_ACTIVE = False
            return None
        
        # for debug
        # print('self.dfTlm_smt = ')
        # print(self.dfTlm_smt)
        # print('self.dfTlm_pcm = ') 
        # print(self.dfTlm_pcm)

        self.dictTlmLatestValues.update( self.dfTlm_smt.to_dict(orient='index')[0] )
        self.dictTlmLatestValues.update( self.dfTlm_pcm.to_dict(orient='index')[0] )

        self.F_TLM_IS_ACTIVE = True


# 
#   Panel: Plotter Pane (Time-history plot)
# 
class pnlPlotter(wx.Panel):
    ### Class constants
    N_PLOTTER = 5
    __T_RANGE = 30    # [s]

    __PLOT_SKIP = 9    ### T.B.REFAC. ###
    # __PLOT_SKIP = 39    ### T.B.REFAC. ###

    def __init__(self, parent):
        super().__init__(parent, wx.ID_ANY)
        
        # shere arguments within the class
        self.parent = parent

        self.__PLOT_COUNT = self.__PLOT_SKIP   ### T.B.REFAC. ###

        # handle exception
        # self.N_PLOTTER = max(1, min(5, self.N_PLOTTER))

        self.loadConfig()

        self.configure()

        ### 
        layout = wx.GridBagSizer()
        layout.Add(window=self.canvas, pos=(0,0), border=10)
        self.SetSizer(layout)

        ### Bind events
        # - timer to refresh time-history pane
        self.tmrRefresh = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimerRefresh, self.tmrRefresh)
        self.tmrRefresh.Start(RATE_REFLESH_PLOTTER)

    # Event handler: EVT_TIMER
    def OnTimerRefresh(self, event):
        # skip refresh when TLM NOT active
        if self.parent.F_TLM_IS_ACTIVE == False:    return None

        ### update data set for plot
        # - update plot points by appending latest values
        self.x_series = np.append(self.x_series, self.parent.dictTlmLatestValues['GSE time'])
        for i in range(self.N_PLOTTER):
            self.y_series = np.append(self.y_series, self.parent.dictTlmLatestValues[self.dictPlotterAttr[i]['item']])

        # for debug
        # print(f'GUI PLT: append latest values {df_tmp.iloc[-1,self.index_x]}')
        # print(f'GUI PLT: x_series = {self.x_series}')
        # print(f'GUI PLT: y_series = {self.y_series}')

        # - determine time max & min
        self.t_max = self.x_series[-1]
        self.t_min = self.t_max - self.__T_RANGE
        # print(f'GUI PLT: t_max = {self.t_max}, t_min = {self.t_min}')

        # - delete plot points out of the designated time range
        while self.x_series[0] < self.t_min:
            self.x_series = np.delete(self.x_series, 0)
            self.y_series = np.delete(self.y_series, np.s_[0:self.N_PLOTTER])
            # print('GUI PLT: a member of 'x_series' is out of the range')

        ### T.B.REFAC. ###
        # skip redraw
        if self.__PLOT_COUNT != self.__PLOT_SKIP:
            self.__PLOT_COUNT += 1
            return None
        self.__PLOT_COUNT = 0

        ### refresh plotter
        self.lines = []
        for i in range(self.N_PLOTTER):
            # delete x axis and lines by restroring canvas
            self.canvas.restore_region(self.backgrounds[i])

            # clear axes
            # self.axes[i].cla()

            # update axex attributions
            self.axes[i].set_xlim([self.t_min, self.t_max])
            # self.axes[i].set_ylim([self.PlotterAttr[i]['y_min'], self.PlotterAttr[i]['y_max']])
            # self.axes[i].set_ylabel(self.PlotterAttr[i]['y_label'])
            # self.axes[i].axhline(y=self.PlotterAttr[i]['alart_lim_l'], xmin=0, xmax=1, color='FIREBRICK')
            # self.axes[i].axhline(y=self.PlotterAttr[i]['alart_lim_u'], xmin=0, xmax=1, color='FIREBRICK')
            # self.axes[i].axhline(y=self.PlotterAttr[i]['alart_lim_l'], xmin=0, xmax=1, color='RED')
            # self.axes[i].axhline(y=self.PlotterAttr[i]['alart_lim_u'], xmin=0, xmax=1, color='RED')
        
            # update plot
            # NOTE: lines become iterrable hereafter
            self.lines.append(self.axes[i].plot(self.x_series, self.y_series[i::self.N_PLOTTER], color='LIME')[0])
     
            # reflect updates in lines
            self.axes[i].draw_artist(self.lines[i])

        # redraw and show updated canvas
        for i in range(self.N_PLOTTER):
            self.fig.canvas.blit(self.axes[i].bbox)

        # redraw and show updated canvas
        # self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        
        # print("GUI PLT: redraw plots...")

    # Load configurations from external files
    def loadConfig(self):

        # Prepare hash: Plotter# -> {Plotter Attributions}
        self.dictPlotterAttr = {}
        for i in range(self.N_PLOTTER):  
            dict_tmp = {}

            # search throughout items
            for strItemName in self.parent.dictTlmItemAttr:
                # skip
                if self.parent.dictTlmItemAttr[strItemName]['plot #'] != i:     continue
                
                dict_tmp['item']        = strItemName
                dict_tmp['unit']        = str(self.parent.dictTlmItemAttr[strItemName]['unit'])
                dict_tmp['y_label']     = dict_tmp['item'] + ' [' + dict_tmp['unit'] + ']'
                dict_tmp['y_min']       = float(self.parent.dictTlmItemAttr[strItemName]['y_min'])
                dict_tmp['y_max']       = float(self.parent.dictTlmItemAttr[strItemName]['y_max'])
                dict_tmp['alart_lim_l'] = float(self.parent.dictTlmItemAttr[strItemName]['alert_lim_l'])
                dict_tmp['alart_lim_u'] = float(self.parent.dictTlmItemAttr[strItemName]['alert_lim_u'])

                break

            self.dictPlotterAttr[i] = dict_tmp

    # Configure appearance for plotters to display time histories
    def configure(self):
        # initialize data set for plot
        self.x_series = np.empty(0)
        self.y_series = np.empty(0)
        
        # generate empty matplotlib Fugure
        # self.fig = Figure()
        self.fig = Figure(figsize=(6, 9))
        
        # register Figure with matplotlib Canvas
        self.canvas = FigureCanvasWxAgg(self, wx.ID_ANY, self.fig)

        ### prepare axes
        # - generate subplots containing axes in Figure
        # NOTE: axes become iterrable hereafter
        self.axes = []
        for i in range(self.N_PLOTTER):
            self.axes.append(self.fig.add_subplot(self.N_PLOTTER, 1, i+1))

            # - set limit for x axis
            t_min = 0
            self.axes[i].set_xlim([t_min, t_min + self.__T_RANGE])

            # - set limit for y axis
            self.axes[i].set_ylim([self.dictPlotterAttr[i]['y_min'], self.dictPlotterAttr[i]['y_max']])

            # - set label for y axis
            self.axes[i].set_ylabel(self.dictPlotterAttr[i]['y_label'])

        # tentatively draw canvas without plot points to save as background
        self.canvas.draw()                                            

        # save the empty canvas as background
        # NOTE: backgrounds become iterrable hereafter
        self.backgrounds = []
        for i in range(self.N_PLOTTER):
            self.backgrounds.append(self.canvas.copy_from_bbox(self.axes[i].bbox))


# 
#   Panel: Digital Indicator Pane (Latest-value indicate)
# 
class pnlDigitalIndicator(wx.Panel):
    
    def __init__(self, parent):
        super().__init__(parent, wx.ID_ANY)
        
        self.parent = parent

        self.loadConfig()

        self.configure()

        ### 
        layout = wx.GridBagSizer()
        layout.Add(self.IndicatorPane, pos=(0,0))
        self.SetSizer(layout)

        ### bind events
        # - set timer to refresh current-value pane
        self.tmrRefresh = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimerRefresh, self.tmrRefresh)
        self.tmrRefresh.Start(RATE_REFLESH_DIGITAL_INDICATOR)

        # - toggle button
        # for button in self.tbtnLabel:
        #     button.Bind(wx.EVT_TOGGLEBUTTON, self.graphTest)

    # Event handler: EVT_TIMER
    def OnTimerRefresh(self, event):
        # skip refresh when TLM NOT active
        if self.parent.F_TLM_IS_ACTIVE == False:    return None
        
        ### refresh indicators
        # - prepare iterator
        iterIndicator = iter( self.stxtIndicator )
        iterLabel = iter( self.tbtnLabel )
        
        # - sweep groups
        for strGroupName in self.dictGroupAttr.keys():
            # - seep items belong each group
            for i in range( self.dictGroupAttr[strGroupName]['rows'] * self.dictGroupAttr[strGroupName]['cols']) :
                strItemName = self.dictIndID2Item[strGroupName][i]
                if strItemName == '':   continue        # skip brank cell

                # get instance from iterator
                stxtInidicator = next(iterIndicator)
                tbtnLabel = next(iterLabel)

                # refresh indicator
                stxtInidicator.SetLabel( 
                    str( np.round(self.parent.dictTlmLatestValues[strItemName], 2)) )

                # accentuate indicator by colors
                if self.parent.dictTlmItemAttr[strItemName]['type'] == 'bool':
                    # - OFF
                    if int(self.parent.dictTlmLatestValues[strItemName]) == 0:
                        stxtInidicator.SetBackgroundColour('NullColour')
                        # stxtInidicator.SetBackgroundColour('NAVY')
                        tbtnLabel.SetForegroundColour('NullColour')
                    # - ON
                    else:
                        stxtInidicator.SetBackgroundColour('MAROON')
                        # stxtInidicator.SetBackgroundColour('NAVY')
                        # stxtInidicator.SetBackgroundColour('GREY')
                        tbtnLabel.SetForegroundColour('RED')
                        # tbtnLabel.SetForegroundColour('BLUE')

                    stxtInidicator.Refresh()

    # Load configurations from external files
    def loadConfig(self):
        ### T.B.REFAC.: TEMPORALLY DESIGNATED BY LITERALS ###
        N_ITEM_PER_ROW = 6

        self.dictGroupAttr = {
            'Time':          {'gidx': 0, 'rows': 1, 'cols': N_ITEM_PER_ROW},
            'DES State':     {'gidx': 1, 'rows': 5, 'cols': N_ITEM_PER_ROW},
            'Pressure':      {'gidx': 2, 'rows': 2, 'cols': N_ITEM_PER_ROW},
            'Temperature':   {'gidx': 3, 'rows': 2, 'cols': N_ITEM_PER_ROW},
            'IMU':           {'gidx': 4, 'rows': 2, 'cols': N_ITEM_PER_ROW},
            'House Keeping': {'gidx': 5, 'rows': 3, 'cols': N_ITEM_PER_ROW}
        }

        ### T.B.REFAC. ###
        # group_order = {'Time':0, 'DES State':1, 'Pressure':2, 'Temperature':3, 'IMU':4, 'House Keeping':5}

        # Prepare hash: Group name -> {Item order -> Item name}
        self.dictIndID2Item = {}
        for strGroupName in self.dictGroupAttr.keys():
            dict_temp = {}
            for i in range(self.dictGroupAttr[strGroupName]['rows'] * self.dictGroupAttr[strGroupName]['cols']):
                item = ''
                for strItemName, dictItemAttr in self.parent.dictTlmItemAttr.items():
                    # detect
                    if dictItemAttr['group'] == strGroupName and dictItemAttr['item order'] == i:
                        item = strItemName  
                        break

                dict_temp[i] = item

            self.dictIndID2Item[strGroupName] = dict_temp

    # Configure appearance for digital indicators to display current values
    def configure(self):
        self.IndicatorPane = wx.BoxSizer(wx.VERTICAL)

        ### generate containers to groupe indicators (StaticBox)
        ### generate indicators & their labels
        ### lay out pairs of indicators & labels in the grouping SBoxes
        
        self.SBoxGroup = []
        self.lytSBoxGroup = []        
        
        self.tbtnLabel = []
        self.stxtIndicator = []
        self.lytPair = []           # pair of Indicator & Label

        self.lytIndicator = []

        for strGroupName in self.dictGroupAttr:
            i = self.dictGroupAttr[strGroupName]['gidx']

            # - generate an instance
            self.SBoxGroup.append(wx.StaticBox(self, wx.ID_ANY, strGroupName))
            self.SBoxGroup[-1].SetForegroundColour('WHITE')
            self.SBoxGroup[-1].SetFont(wx.Font(15, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            
            # - lay out the instance
            self.lytSBoxGroup.append(wx.StaticBoxSizer(self.SBoxGroup[-1], wx.VERTICAL))
            self.IndicatorPane.Add(self.lytSBoxGroup[-1])

            # generate grid in the grouping SBox
            self.lytIndicator.append(
                wx.GridSizer(   rows=self.dictGroupAttr[strGroupName]['rows'], 
                                cols=self.dictGroupAttr[strGroupName]['cols'], 
                                gap=(10,5)) )
            
            # place items in the grid
            for j, strItemName in self.dictIndID2Item[strGroupName].items():
                # handle blank cell
                if strItemName == '':
                    self.lytIndicator[i].Add((0,0))
                    continue

                # generate instance 
                # - item label (ToggleButton)
                self.tbtnLabel.append(
                    wx.ToggleButton(self, wx.ID_ANY, label=strItemName, size=(140,22)))
                
                # - digital indicator (StaticText)
                self.stxtIndicator.append(
                    wx.StaticText(self, wx.ID_ANY, label=str(i*100 + j), style=wx.ALIGN_CENTRE | wx.ST_NO_AUTORESIZE))
                self.stxtIndicator[-1].SetBackgroundColour('BLACK')
                self.stxtIndicator[-1].SetForegroundColour('GREEN')

                # - pair of item label & inidicator
                self.lytPair.append(wx.GridSizer(rows=2, cols=1, gap=(0,0)))
                self.lytPair[-1].Add(self.tbtnLabel[-1], flag=wx.EXPAND)
                self.lytPair[-1].Add(self.stxtIndicator[-1], flag=wx.EXPAND)
                
                self.lytIndicator[i].Add(self.lytPair[-1], flag=wx.EXPAND)
            
            # snap
            self.lytSBoxGroup[i].Add(self.lytIndicator[i])

        # set states for ToggleButton
        # for i in range(pnlPlotter.N_PLOTTER):
        #     self.tbtnLabel[self.PlotterAttr[i]['idx_item']].SetValue(True)





