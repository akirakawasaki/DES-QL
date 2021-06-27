### Standard libraries
import queue
import sys

### Third-party libraries
import numpy as np
import pandas as pd
from wx.core import EXPAND
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
plt.rcParams["figure.subplot.bottom"] = 0.07    # Bottom
plt.rcParams["figure.subplot.top"]    = 0.99    # Top
plt.rcParams["figure.subplot.left"]   = 0.15    # Left
plt.rcParams["figure.subplot.right"]  = 0.97    # Right
plt.rcParams["figure.subplot.hspace"] = 0.05    # Height Margin between subplots


#
#   Top-level window
#
class frmMain(wx.Frame):
    #
    #   Class constants
    #

    #    
    WINDOW_CAPTION = 'Telemetry Data Quick Look for Detonation Engine System'
    
    # input file pathes
    FPATH_CONFIG = './config_tlm.xlsx'
    

    # def __init__(self, g_state, g_lval, q_msg_smt, q_msg_pcm):
    def __init__(self, g_state, g_lval):
        super().__init__(None, wx.ID_ANY, self.WINDOW_CAPTION)

        # shere arguments within the class
        self.g_state = g_state
        self.g_lval = g_lval

        # self.q_msg_smt = q_msg_smt
        # self.q_msg_pcm = q_msg_pcm

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


        #
        #   Lay out frm Main
        #

        # "Window" hierarchy
        # frmMain - Sizer: layout
        #               + pnlPlotter
        #               + Sizer: sublayout1
        #                   + pnlControl
        #                   + pnlDigitalIndicator

        # frmMain (Frame)
        #   parent  : N/A
        #   chidren : pnlPlotter, pnlControl, pnlDigitalIndicator
        ###
        # - generate Window instance
        # done in "gui_handler" function
        # - add the Window to the parent Sizer
        # N/A
        # - generate associated Sizer to lay out this Window
        layout = wx.BoxSizer(wx.HORIZONTAL)
        # - set a Sizer to the Window
        self.SetSizer(layout)

        # Plotter Pane for Time History Plots (Panel)
        #   parent  : frmMain
        #   chidren : N/A
        ###
        # - generate Window instance
        self.pnlPlotter = pnlPlotter(parent=self, g_state=self.g_state)                     # 
        # - add the Window to the parent Sizer
        layout.Add(window=self.pnlPlotter, proportion=0, flag=wx.ALIGN_BOTTOM)
        # - generate associated Sizer to lay out this Window
        # N/A
        # - set a Sizer to the Window
        # N/A

        # Sub-Lay-Out (Sizer)
        #   parent   : frmMain
        #   children : pnlControl, pnlDigitalIndicator
        ###
        # - generate Sizer instance
        sublayout1 = wx.BoxSizer(wx.VERTICAL)
        # - add the Sizer to the parent Sizer
        layout.Add(sizer=sublayout1, proportion=1, flag=wx.EXPAND | wx.ALL, border=15)

        # Controller Pane (Panel)
        #   parent  : Sub-Lay-Out
        #   chidren : N/A
        ###
        # - generate Window instance
        self.pnlController = pnlController(parent=self, g_state=self.g_state)
        # - add the Window to the parent Sizer
        sublayout1.Add(window=self.pnlController, proportion=0, flag=wx.EXPAND | wx.BOTTOM, border=15)
        # - generate associated Sizer to lay out this Window
        # N/A
        # - set a Sizer to the Window
        # N/A

        # Digital Indicator Pane for Current Values (Panel)
        #   parent  : Sub-Lay-Out
        #   chidren : N/A
        ###
        # - generate Window instance
        self.pnlDigitalIndicator = pnlDigitalIndicator(parent=self, g_state=self.g_state)
        # - add the Window to the parent Sizer
        sublayout1.Add(window=self.pnlDigitalIndicator, proportion=1, flag=wx.EXPAND)
        # - generate associated Sizer to lay out this Window
        # N/A
        # - set a Sizer to the Window
        # N/A
        

        #
        #   Bind events
        #
        
        # close
        self.Bind(wx.EVT_CLOSE, self.OnClose)
                
        # timer to fetch latest telemeter data
        self.tmrFetchTelemeterData = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnFetchLatestValues, self.tmrFetchTelemeterData)
        self.tmrFetchTelemeterData.Start(RATE_FETCH_LATEST_VALUES)


    # Event handler: EVT_CLOSE
    def OnClose(self, event):
        # stop timers
        self.tmrFetchTelemeterData.Stop()
        self.pnlPlotter.tmrRefresh.Stop()
        self.pnlDigitalIndicator.tmrRefresh.Stop()
        
        self.Destroy()


    # Event handler: EVT_TIMER
    def OnFetchLatestValues(self, event):
        # print('GUI FTC: fetched tlm data')
        
        # break off when tlm data not exist
        if len(self.g_lval['smt']) == 0 or len(self.g_lval['pcm']) == 0:
            print('GUI FTC: awaiting SMT and/or PCM data')
            self.F_TLM_IS_ACTIVE = False
            return None
        
        # fetch latest values
        self.dictTlmLatestValues.update( self.g_lval['smt'] )
        self.dictTlmLatestValues.update( self.g_lval['pcm'] )

        #
        #   Specialized Feature: Last Error Latch
        #
        if self.g_state['last_error'] != 0:
            self.dictTlmLatestValues['Error Code'] = self.g_state['last_error']
        ###

        self.F_TLM_IS_ACTIVE = True


# 
#   Plotter Pane for Time-history (Panel)
# 
class pnlPlotter(wx.Panel):
    #
    #   Class constants
    #

    N_PLOTTER = 5
    # __T_RANGE = 30    # [s]
    __T_RANGE = 31    # [s]

    __PLOT_SKIP = 9    ### T.B.REFAC. ###
    # __PLOT_SKIP = 39    ### T.B.REFAC. ###


    def __init__(self, parent, g_state):
        super().__init__(parent, wx.ID_ANY)
        
        # shere arguments within the class
        self.parent = parent
        self.g_state = g_state

        self.__PLOT_COUNT = self.__PLOT_SKIP   ### T.B.REFAC. ###

        # handle exception
        # self.N_PLOTTER = max(1, min(5, self.N_PLOTTER))

        self.loadConfig()

        self.configure()

        ### 
        layout = wx.BoxSizer()
        # layout = wx.GridBagSizer()
        layout.Add(self.canvas, proportion=0, flag=wx.ALIGN_BOTTOM)
        # layout.Add(self.canvas, proportion=0, flag=wx.SHAPED | wx.ALIGN_CENTER)
        # layout.Add(self.canvas, proportion=1, flag=wx.EXPAND)
        # layout.Add(self.canvas, proportion=0, flag=wx.EXPAND | wx.ALL, border=5)
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
        dpi = matplotlib.rcParams['figure.dpi']
        w_window, h_window = self.parent.GetClientSize()

        h_fig = 1.00 * h_window * 0.97 / float(dpi)
        w_fig = 0.65 * h_window * 0.97 / float(dpi)

        # self.fig = Figure()
        self.fig = Figure(figsize=(w_fig, h_fig))
        # self.fig = Figure(figsize=(6.5, 10))
        
        # register Figure with matplotlib Canvas
        self.canvas = FigureCanvasWxAgg(self, wx.ID_ANY, self.fig)

        ### prepare axes
        # - generate subplots containing axes in Figure
        # NOTE: axes become iterrable hereafter
        self.axes = []
        for i in range(self.N_PLOTTER):
            self.axes.append(self.fig.add_subplot(self.N_PLOTTER, 1, i+1))

            # - set limit for x axis
            t_min = -self.__T_RANGE
            t_max = 0.0
            self.axes[i].set_xlim([t_min, t_max])

            # - set label for x axis
            self.axes[i].set_xlabel('time [s]')

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
#   Control Pane (Panel)
#
class pnlController(wx.Panel):
    
    def __init__(self, parent, g_state):
        super().__init__(parent, wx.ID_ANY)

        # shere arguments within the class
        self.parent = parent
        self.g_state = g_state

        self.layoutPane()

        ### bind Events
        # - Reset Button
        self.btnReset.Bind(wx.EVT_BUTTON, self.OnClickResetButton)


    def OnClickResetButton(self, event):
        ### Specialized Feature: Last Error Latch ###
        # reset last error
        self.g_state['last_error'] = 0
        ####


    def layoutPane(self):

        # "Window" hierarchy
        # Pane - Sizer: lytPane
        #         + Reset Button


        # Pane (Panel)
        #   parent  : Frame
        #   chidren : 
        ###
        # - generate Window instance
        # done in the frmMain class
        # - add the Window to the parent Sizer
        # ???
        # - generate associated Sizer to lay out this Window
        lytPane = wx.GridSizer(rows=1, cols=6, gap=(10,0))
        # lytPane = wx.BoxSizer(wx.HORIZONTAL)
        # - set a Sizer to the Window
        self.SetSizer(lytPane)

        # Reset Button (Button)
        #   parent   : Pane
        #   children : N/A
        ###
        # - generate Window instance
        self.btnReset = wx.Button(self, wx.ID_ANY, label='RESET')
        self.btnReset.SetFont(
            wx.Font(70, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL) )     # 70 is a　magic # in wx
        # - add the Window to the parent Sizer
        lytPane.Add(self.btnReset, proportion=0, flag=wx.EXPAND)


# 
#   Digital Indicator Pane for Latest values (Panel)
# 
class pnlDigitalIndicator(wx.Panel):
    
    def __init__(self, parent, g_state):
        super().__init__(parent, wx.ID_ANY)
        
        # shere arguments within the class
        self.parent = parent
        self.g_state = g_state

        self.loadConfig()

        self.layoutPane()

        self.configurePane()

        # bind events
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
            
            # - sweep grid within each group
            for i in range( self.dictGroupAttr[strGroupName]['rows'] * self.dictGroupAttr[strGroupName]['cols'] ) :
                
                #
                #   Refresh indicators
                #
                strItemName = self.dictIndID2Item[strGroupName][i]

                # skip brank cell
                if strItemName == '':   continue        

                # get instance from iterator
                stxtInidicator = next(iterIndicator)
                tbtnLabel = next(iterLabel)

                val_float = self.parent.dictTlmLatestValues[strItemName]

                # rounding
                deci = self.parent.dictTlmItemAttr[strItemName]['decimal']
                val_rounded =      str( round( val_float ) ) if (deci <= 0) \
                              else str( round( val_float, deci ) )

                # refresh indicator
                stxtInidicator.SetLabel( val_rounded )

                #
                #   Judge Green/Red
                #
                lim_l = float(self.parent.dictTlmItemAttr[strItemName]['alert_lim_l'])
                lim_u = float(self.parent.dictTlmItemAttr[strItemName]['alert_lim_u'])

                if (val_float < lim_l) or (val_float > lim_u):
                    stxtInidicator.SetBackgroundColour('MAROON')
                else: 
                    stxtInidicator.SetBackgroundColour('NullColour')

                stxtInidicator.Refresh()

                # if self.parent.dictTlmItemAttr[strItemName]['type'] == 'bool':
                #     # - OFF
                #     if int(self.parent.dictTlmLatestValues[strItemName]) == 0:
                #         stxtInidicator.SetBackgroundColour('NullColour')
                #         # stxtInidicator.SetBackgroundColour('NAVY')
                #         tbtnLabel.SetForegroundColour('NullColour')
                #     # - ON
                #     else:
                #         stxtInidicator.SetBackgroundColour('MAROON')
                #         # stxtInidicator.SetBackgroundColour('NAVY')
                #         # stxtInidicator.SetBackgroundColour('GREY')
                #         tbtnLabel.SetForegroundColour('RED')
                #         # tbtnLabel.SetForegroundColour('BLUE')

                #     stxtInidicator.Refresh()


    # Load configurations
    def loadConfig(self):
        ### T.B.REFAC.: TEMPORALLY DESIGNATED BY LITERALS ###
        N_ITEM_PER_ROW = 6
        self.dictGroupAttr = {
            'Time':          {'gidx': 0, 'rows': 1, 'cols': N_ITEM_PER_ROW},
            'DES State':     {'gidx': 1, 'rows': 3, 'cols': N_ITEM_PER_ROW+2},
            'Pressure':      {'gidx': 2, 'rows': 2, 'cols': N_ITEM_PER_ROW},
            'Temperature':   {'gidx': 3, 'rows': 2, 'cols': N_ITEM_PER_ROW},
            'IMU':           {'gidx': 4, 'rows': 3, 'cols': N_ITEM_PER_ROW},
            'House Keeping': {'gidx': 5, 'rows': 3, 'cols': N_ITEM_PER_ROW}
        }

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


    # Lay out Pane
    def layoutPane(self):

        # "Window" hierarchy
        # Pane - Sizer: lytPane
        #         + sboxIndGroup1 - Sizer: sboxSizer
        #         |                   + pnlIndGroup - Sizer: lytIndGroup
        #         |                                       + pnlIndPair1 - Sizer: lytIndPair
        #         |                                       |                   + sbtnLabel
        #         |                                       |                   + stxtIndicator
        #         |                                       + pnlIndPair2 ...
        #         + sboxIndGroup2 ...


        self.sboxIndGroup = []      
        self.sboxSizer = []

        self.pnlIndGroup = []       # group of Indicators
        self.lytIndGroup = [] 
                
        self.pnlIndPair = []        # pair of Indicator & its Label
        self.lytIndPair = []

        self.tbtnLabel = []
        self.stxtIndicator = []

        # Pane (Panel)
        #   parent  : Frame
        #   chidren : sboxIndGroups
        ###
        # - generate Window instance
        # done in the frmMain class
        # - add the Window to the parent Sizer
        # ???
        # - generate associated Sizer to lay out this Window
        lytPane = wx.BoxSizer(wx.VERTICAL)
        # - set a Sizer to the Window
        self.SetSizer(lytPane)


        # loop for sboxIndGroups
        for strGroupName in self.dictGroupAttr:
            i = self.dictGroupAttr[strGroupName]['gidx']
            rows = self.dictGroupAttr[strGroupName]['rows']


            # sboxIndGroup (StaticBox), as an envelope of an Indicator Group
            #   parent   : Pane
            #   children : 1 Indicator Group
            ###
            # - generate Widow instance
            self.sboxIndGroup.append( wx.StaticBox(self, wx.ID_ANY, strGroupName) )
            self.sboxIndGroup[-1].SetForegroundColour('WHITE')
            # self.sboxIndGroup[-1].SetFont( 
            #   wx.Font(15, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL) )
            self.sboxIndGroup[-1].SetFont( 
                wx.Font(70, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL) )      # 70 is a magic # in wx
            # - generate associated Sizer to lay out this Window
            self.sboxSizer.append( wx.StaticBoxSizer(self.sboxIndGroup[-1]) )
            # - add the Window to the parent Sizer
            lytPane.Add(self.sboxSizer[-1], proportion=rows, flag=wx.EXPAND)


            # Indicator Group (Panel)
            #   parent   : StaticBox
            #   children : Indicator Pairs
            ###
            # - generate Window instance
            self.pnlIndGroup.append( wx.Panel(self.sboxIndGroup[-1], wx.ID_ANY) )
            # - add the Window to the parent Sizer
            self.sboxSizer[-1].Add(self.pnlIndGroup[-1], proportion=1, flag=wx.EXPAND)
            # - generate associated Sizer to lay out this Window
            self.lytIndGroup.append(
                wx.GridSizer(   rows=self.dictGroupAttr[strGroupName]['rows'], 
                                cols=self.dictGroupAttr[strGroupName]['cols'], 
                                gap=(10,5)) )
            # - set a Sizer to the Window
            self.pnlIndGroup[-1].SetSizer(self.lytIndGroup[-1])


            # loop for Indicator Pairs
            for j, strItemName in self.dictIndID2Item[strGroupName].items():
                # exception handling for blank cell
                if strItemName == '':
                    self.lytIndGroup[-1].AddStretchSpacer()
                    continue
                
                # Indicator Pair (Panel)
                #   parent   : Indicator Group
                #   children : Label & Digital Indicator
                ###
                # - generate Window instance
                self.pnlIndPair.append( wx.Panel(self.pnlIndGroup[-1], wx.ID_ANY) )
                # - add the Window to the parent Sizer
                self.lytIndGroup[-1].Add(self.pnlIndPair[-1], proportion=1, flag=wx.EXPAND)
                # - generate associated Sizer to lay out this Window
                self.lytIndPair.append( wx.BoxSizer(wx.VERTICAL) )
                # - set a Sizer to the Window
                self.pnlIndPair[-1].SetSizer(self.lytIndPair[-1])


                # Item Label (ToggleButton) 
                #   parent   : Indicator Pair
                #   children : N/A
                ###
                # - generate Window instance
                unit = str( self.parent.dictTlmItemAttr[strItemName]['unit'] )
                label =     (strItemName + ' [' + unit + ']')   if (unit != 'nan') \
                       else strItemName
                self.tbtnLabel.append( wx.ToggleButton(self.pnlIndPair[-1], wx.ID_ANY, label=label) )
                # self.tbtnLabel[-1].SetFont(
                #   wx.Font(13, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL) )
                self.tbtnLabel[-1].SetFont(
                    wx.Font(70, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL) )     # 70 is a　magic # in wx
                # - add the Window to the parent Sizer
                self.lytIndPair[-1].Add(self.tbtnLabel[-1], proportion=1, flag=wx.EXPAND)


                # Digital Indicator (StaticText)
                #   parent   : Indicator Pair
                #   children : N/A
                ###
                # - generate Window instance
                self.stxtIndicator.append(
                    wx.StaticText(self.pnlIndPair[-1], wx.ID_ANY, label=str(i*100 + j), style=wx.ALIGN_CENTRE | wx.ST_NO_AUTORESIZE))
                self.stxtIndicator[-1].SetFont(
                    wx.Font(15, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL) )     ### T.B.REFAC. ###
                # self.stxtIndicator[-1].SetFont(
                #   wx.Font(70, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL) )     # 70 is a　magic # in wx
                self.stxtIndicator[-1].SetBackgroundColour('BLACK')
                self.stxtIndicator[-1].SetForegroundColour('GREEN')
                # - add the Window to the parent Sizer
                self.lytIndPair[-1].Add(self.stxtIndicator[-1], proportion=1, flag=wx.EXPAND)


    # Configure Pane
    def configurePane(self):
        pass

        # set states for ToggleButton
        # for i in range(pnlPlotter.N_PLOTTER):
        #     self.tbtnLabel[self.PlotterAttr[i]['idx_item']].SetValue(True)


