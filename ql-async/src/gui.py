### Standard libraries
# import concurrent.futures
import queue
import sys
# import time

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
FETCH_RATE_LATEST_VALUES       = 25     # ms/cycle
REFLESH_RATE_DIGITAL_INDICATOR = 800    # ms/cycle
REFLESH_RATE_PLOTTER           = 100    # ms/cycle

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
    #
    WINDOW_CAPTION = 'Telemetry Data Quick Look for Detonation Engine System'
    
    # input file pathes
    FPATH_CONFIG = './config_tlm_4.xlsx'
    # FPATH_CONFIG = './config_tlm_3.xlsx'
    # FPATH_CONFIG = './config_tlm_2.xlsx'
    
    def __init__(self, q_msg_smt, q_msg_pcm, q_data_smt, q_data_pcm):
        super().__init__(None, wx.ID_ANY, self.WINDOW_CAPTION)
        
        # receive instance of shared variables
        self.q_msg_smt = q_msg_smt      # sending ONLY (to TLM)
        self.q_msg_pcm = q_msg_pcm      # sending ONLY (to TLM)
        self.q_data_smt = q_data_smt    # receiving ONLY (from TLM)
        self.q_data_pcm = q_data_pcm    # receiving ONLY (from TLM)


        ### load configurations from an external file
        # - smt
        try: 
            # df_cfg_smt = pd.read_excel(self.FPATH_CONFIG, 
            #                             sheet_name='smt', header=0, index_col=0).dropna(how='all')
            df_cfg_smt = pd.read_excel(self.FPATH_CONFIG, 
                                        sheet_name='smt', header=0, index_col=None).dropna(how='all')
        except:
            print(f'Error GUI: Config file "{self.FPATH_CONFIG}" NOT exists! smt')
            sys.exit()

        self.TlmItemAttr_smt = df_cfg_smt.to_dict(orient='index')
        self.TlmItemList_smt = df_cfg_smt['item'].values.tolist()
        self.N_ITEM_SMT = len(self.TlmItemList_smt)

        # - pcm
        try: 
            # df_cfg_pcm = pd.read_excel(self.FPATH_CONFIG, 
            #                             sheet_name='pcm', header=0, index_col=0).dropna(how='all')
            df_cfg_pcm = pd.read_excel(self.FPATH_CONFIG, 
                                        sheet_name='pcm', header=0, index_col=None).dropna(how='all')
        except:
            print(f'Error GUI: Config file "{self.FPATH_CONFIG}" NOT exists! pcm')
            sys.exit()

        self.TlmItemAttr_pcm = df_cfg_pcm.to_dict(orient='index')
        self.TlmItemList_pcm = df_cfg_pcm['item'].values.tolist()
        self.N_ITEM_PCM = len(self.TlmItemList_pcm)

        ### T.B.REFAC. ###
        group_order = {'Time':0, 'DES State':1, 'Pressure':2, 'Temperature':3, 'IMU':4, 'House Keeping':5}

        # df_cfg = pd.concat([df_cfg_smt, df_cfg_pcm], axis=0)

        # df_cfg['group order'] = df_cfg['group'].apply(lambda x: group_order.index(x) if x in group_order else -1)
        # df_cfg_s = df_cfg.sort_values(['group','item order'])
        # print(df_cfg_s)

        # self.TlmItemAttr = df_cfg_s.to_dict(orient='index')


        ### initialize a dictionary to store latest values
        self.dictTlmLatestValues = {}

        self.dictTlmLatestValues_smt = dict.fromkeys(['Line# (smt)'] + self.TlmItemList_smt, np.nan)
        self.dictTlmLatestValues.update(self.dictTlmLatestValues_smt)
        # self.dfTlm_smt = pd.DataFrame.from_dict(self.dictTlm_smt, orient='index').T
        # self.dfTlm_smt = pd.DataFrame.from_dict(self.dictTlm_smt, orient='columns')
        self.dfTlm_smt = pd.DataFrame()

        self.dictTlmLatestValues_pcm = dict.fromkeys(['Line# (pcm)'] + self.TlmItemList_pcm, np.nan)
        self.dictTlmLatestValues.update(self.dictTlmLatestValues_pcm)
        # self.dfTlm_pcm = pd.DataFrame.from_dict(self.dictTlm_pcm, orient='index').T
        # self.dfTlm_pcm = pd.DataFrame.from_dict(self.dictTlm_pcm, orient='columns')
        self.dfTlm_pcm = pd.DataFrame()

        # for debug
        print(f'dictTlmLatestValues_smt = {self.dictTlmLatestValues_smt}')
        print(f'dictTlmLatestValues_pcm = {self.dictTlmLatestValues_pcm}')
        # print(f'dfTlm_smt = ')
        # print(self.dfTlm_smt)
        # print(f'dfTlm_pcm = ')
        # print(self.dfTlm_pcm)

        # check key duplication
        if (self.dictTlmLatestValues_smt.keys() & self.dictTlmLatestValues_pcm.keys()) != set():
            print(f'Error GUI: Keys are duplicated between SMT & PCM! Check CONFIG file.')
            sys.exit()


        self.F_TLM_IS_ACTIVE = False

        ### initialize attributions
        self.SetBackgroundColour('Black')
        # self.SetBackgroundColour('Dark Grey')
        self.Maximize(True)

        ### 
        # - Time History Plots & Current Value Indicators
        self.pnlPlotter = pnlPlotter(parent=self)
        self.pnlDigitalIndicator = pnlDigitalIndicator(parent=self)
        # self.chart_panel = ChartPanel(parent=self)
        # self.chart_panel = ChartPanel(parent=self, q_data_smt, q_data_pcm)

        # lay out panels by sizer
        layout = wx.FlexGridSizer(rows=1, cols=2, gap=(10, 10))
        layout.Add(self.pnlPlotter, flag=wx.EXPAND)                                  # plotter pane
        layout.Add(self.pnlDigitalIndicator, flag=wx.ALIGN_CENTER_HORIZONTAL)        # digital indicator pane
        self.SetSizer(layout)

        # layout = wx.GridBagSizer()
        # layout.Add(self.chart_panel, pos=wx.GBPosition(0,0), flag=wx.EXPAND | wx.ALL, border=10)
        # self.SetSizer(layout)
        # layout.Fit(self)
        # pnlRoot.SetSizer(layout)
        # layout.Fit(pnlRoot)

        ### bind events
        # - close
        self.Bind(wx.EVT_CLOSE, self.OnClose)
                
        # - timer to fetch latest telemeter data
        self.tmrFetchTelemeterData = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnFetchLatestValues, self.tmrFetchTelemeterData)
        self.tmrFetchTelemeterData.Start(FETCH_RATE_LATEST_VALUES)

    # Event handler: EVT_CLOSE
    def OnClose(self, event):
        # dig = wx.MessageDialog(self,
        #                        "Do you really want to close this application?",
        #                        "Confirm Exit",
        #                        wx.OK | wx.CANCEL | wx.ICON_QUESTION)
        # result = dig.ShowModal()
        # dig.Destroy()
        # if result == wx.ID_OK:  self.Destroy()
        
        # quit tlm handlers
        self.q_msg_smt.put_nowait('stop') 
        self.q_msg_pcm.put_nowait('stop') 
        # self.internal_flags.GUI_TASK_IS_DONE = True

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
                # self.dfTlm_smt.update( self.q_data_smt.get_nowait() )
            except queue.Empty:
                break
            # else:
            #     if self.q_data_smt.empty() == True:     break
        # - pcm
        while True:
            try:
                self.dfTlm_pcm = self.q_data_pcm.get_nowait()
                # self.dfTlm_pcm.update( self.q_data_pcm.get_nowait() )
            except queue.Empty:
                break
            # else:
            #     if self.q_data_pcm.empty() == True:     break

        # break off when tlm data not exist
        if len(self.dfTlm_smt.index) == 0 or len(self.dfTlm_pcm.index) == 0:
            print('GUI FTC: awaiting SMT and/or PCM data')
            self.F_TLM_IS_ACTIVE = False
            return None
        
        # for debug
        # print('GUI FTC: df.index length = {}'.format(len(self.tlm_latest_data.df_smt.index)))
        # print('self.dfTlm_smt = ')
        # print(self.dfTlm_smt)
        # print('self.dfTlm_pcm = ') 
        # print(self.dfTlm_pcm)
        # print(self.dfTlm_smt.columns)
        # print(self.dfTlm_smt.iloc[-1].to_list)

        # tmp = self.dfTlm_smt.to_dict(orient='index')
        # print(tmp[0])
        # print(tmp)

        self.dictTlmLatestValues.update( self.dfTlm_smt.to_dict(orient='index')[0] )
        self.dictTlmLatestValues.update( self.dfTlm_pcm.to_dict(orient='index')[0] )

        # self.dictTlmLatestValues.update( dict(zip(self.dfTlm_pcm.columns, self.dfTlm_pcm[-1])) )
        # dictTlm_pcm = self.dfTlm_pcm.to_dict
        # dictTlm_pcm = self.dfTlm_pcm.T.to_dict
        # self.dictTlmLatestValues.update(dictTlm_pcm)

        self.F_TLM_IS_ACTIVE = True


# 
#   Panel: Plotter Pane (Time-history plot)
# 
class pnlPlotter(wx.Panel):
    N_PLOTTER = 5
    __T_RANGE = 30    # [s]

    # __IDX_TIME = 1
    __IDX_TIME = 2      # tentative

    __PLOT_SKIP = 9    ### T.B.REFAC. ###
    # __PLOT_SKIP = 39    ### T.B.REFAC. ###

    def __init__(self, parent):
        super().__init__(parent, wx.ID_ANY)
        
        self.parent = parent

        self.__PLOT_COUNT = self.__PLOT_SKIP   ### T.B.REFAC. ###

        self.load_config_plotter()

        self.configure_plotter()

        ### 
        layout = wx.GridBagSizer()
        layout.Add(self.canvas, pos=(0,0))                            # plotter pane
        self.SetSizer(layout)

        ### bind events
        # - set timer to refresh time-history pane
        self.tmrRefreshPlotter = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnRefreshPlotter, self.tmrRefreshPlotter)
        self.tmrRefreshPlotter.Start(REFLESH_RATE_PLOTTER)

    # Event handler: EVT_TIMER
    def OnRefreshPlotter(self, event):
        # skip refresh when TLM NOT active
        if self.parent.F_TLM_IS_ACTIVE == False:    return None
        # print(f'GUI PLT: F_TLM_IS_ACTIVE = {self.parent.F_TLM_IS_ACTIVE}')      # for debug

        ### update data set for plot
        # df_tmp = pd.concat([self.parent.dfTlm_smt, self.parent.dfTlm_pcm], axis=1)      ### T.B.REFAC. ###
        
        # - update plot points by appending latest values
        self.x_series = np.append(self.x_series, self.parent.dictTlmLatestValues['GSE time'])
        # self.x_series = np.append(self.x_series, df_tmp.iloc[-1,self.__IDX_TIME])
        for i in range(self.N_PLOTTER):
            self.y_series = np.append(self.y_series, self.parent.dictTlmLatestValues[self.PlotterAttr[i]['item']])
            # self.y_series = np.append(self.y_series, df_tmp.iloc[-1,self.PlotterAttr[i]['idx_item']])
            # self.y_series = np.append(self.y_series, df_tmp.iloc[-1,self.PlotterAttr[i]['idx_item']+1])     # tentative

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
    def load_config_plotter(self):
        # handle exception
        # if self.N_PLOTTER > 5: self.N_PLOTTER = 5
        self.N_PLOTTER = max(1, min(5, self.N_PLOTTER))

        self.PlotterAttr = {}
        for i in range(self.N_PLOTTER):  
            dict_tmp = {}

            # search throughout smt items
            for iii in range(self.parent.N_ITEM_SMT):
                if self.parent.TlmItemAttr_smt[iii]['plot #'] != i: continue       # skip
      
                dict_tmp['idx_item']    = iii
                dict_tmp['item']        = str(self.parent.TlmItemAttr_smt[iii]['item'])
                dict_tmp['y_label']     = str(self.parent.TlmItemAttr_smt[iii]['item'])
                dict_tmp['y_unit']      = str(self.parent.TlmItemAttr_smt[iii]['unit'])
                dict_tmp['y_min']       = float(self.parent.TlmItemAttr_smt[iii]['y_min'])
                dict_tmp['y_max']       = float(self.parent.TlmItemAttr_smt[iii]['y_max'])
                dict_tmp['alart_lim_l'] = float(self.parent.TlmItemAttr_smt[iii]['alert_lim_l'])
                dict_tmp['alart_lim_u'] = float(self.parent.TlmItemAttr_smt[iii]['alert_lim_u'])

                break
            
            else:
                # search throughout pcm items
                for iii in range(self.parent.N_ITEM_PCM):
                    if self.parent.TlmItemAttr_pcm[iii]['plot #'] != i: continue   # skip

                    dict_tmp['idx_item']    = iii + self.parent.N_ITEM_SMT
                    dict_tmp['item']        = str(self.parent.TlmItemAttr_pcm[iii]['item'])
                    dict_tmp['y_label']     = str(self.parent.TlmItemAttr_pcm[iii]['item'])
                    dict_tmp['y_unit']      = str(self.parent.TlmItemAttr_pcm[iii]['unit'])
                    dict_tmp['y_min']       = float(self.parent.TlmItemAttr_pcm[iii]['y_min'])
                    dict_tmp['y_max']       = float(self.parent.TlmItemAttr_pcm[iii]['y_max'])
                    dict_tmp['alart_lim_l'] = float(self.parent.TlmItemAttr_pcm[iii]['alert_lim_l'])
                    dict_tmp['alart_lim_u'] = float(self.parent.TlmItemAttr_pcm[iii]['alert_lim_u'])

                    break

            # append attibutions for i-th plotter 
            self.PlotterAttr[i] = dict_tmp

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
        for i in range(self.N_PLOTTER):
            self.axes.append(self.fig.add_subplot(self.N_PLOTTER, 1, i+1))

            # - set limit for x axis
            t_min = 0
            self.axes[i].set_xlim([t_min, t_min + self.__T_RANGE])

            # - set limit for y axis
            self.axes[i].set_ylim([self.PlotterAttr[i]['y_min'], self.PlotterAttr[i]['y_max']])

            # - set label for y axis
            self.axes[i].set_ylabel(self.PlotterAttr[i]['y_label'])
            # self.axes[i].set_ylabel(self.PlotterAttr[i]['y_label'] + f' [{self.PlotterAttr[i]['y_unit']}]')

        # tentatively draw canvas without plot points to save as background
        self.canvas.draw()                                            

        # save the empty canvas as background
        # NOTE: backgrounds become iterrable hereafter
        self.backgrounds = []
        for i in range(self.N_PLOTTER):
            self.backgrounds.append(self.canvas.copy_from_bbox(self.axes[i].bbox))


# 
#   Panel: Digital Indicator Pane
# 
class pnlDigitalIndicator(wx.Panel):
    
    def __init__(self, parent):
        super().__init__(parent, wx.ID_ANY)
        
        self.parent = parent

        self.load_config_digital_indicator()

        self.configure_digital_indicator()

        ### 
        layout = wx.GridBagSizer()
        layout.Add(self.IndicatorPane, pos=(0,0))    # digital indicator pane
        self.SetSizer(layout)

        ### bind events
        # - set timer to refresh current-value pane
        self.tmrRefreshDigitalIndicator = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnRefreshDigitalIndicator, self.tmrRefreshDigitalIndicator)
        self.tmrRefreshDigitalIndicator.Start(REFLESH_RATE_DIGITAL_INDICATOR)

    # Event handler: EVT_TIMER
    def OnRefreshDigitalIndicator(self, event):
        # skip refresh when TLM NOT active
        if self.parent.F_TLM_IS_ACTIVE == False:    return None
        
        ### refresh indicators
        # - sweep groups
        for strGroupName in self.GroupAttr.keys():
            # - seep items belong each group    ### T.B.REFAC. ###
            for ii in range(self.GroupAttr[strGroupName]['rows'] * self.GroupAttr[strGroupName]['cols']):
                # search throughout smt items
                for iii in range(self.parent.N_ITEM_SMT):
                    # skip
                    if (   self.parent.TlmItemAttr_smt[iii]['group']      != strGroupName
                        or self.parent.TlmItemAttr_smt[iii]['item order'] != ii ):
                        continue

                    # refresh indicator
                    self.stxtIndicator[iii].SetLabel(str(np.round(self.parent.dfTlm_smt.iloc[-1, iii], 2)))
                    # self.stxtIndicator[iii].SetLabel(str(np.round(df_smt_tmp.iloc[-1, iii], 2)))

                    # accentuate indicator by colors
                    if self.parent.TlmItemAttr_smt[iii]['type'] == 'bool':
                        # - OFF
                        # if int(df_smt_tmp.iloc[-1, iii]) == 0:
                        if int(self.parent.dfTlm_smt.iloc[-1, iii]) == 0:
                            self.tbtnLabel[iii].SetForegroundColour('NullColour')
                            self.stxtIndicator[iii].SetBackgroundColour('NullColour')
                            # self.stxtIndicator[iii].SetBackgroundColour('NAVY')
                        # - ON
                        else:
                            self.tbtnLabel[iii].SetForegroundColour('RED')
                            # self.tbtnLabel[iii].SetForegroundColour('BLUE')
                            # self.stxtIndicator[iii].SetBackgroundColour('GREY')
                            self.stxtIndicator[iii].SetBackgroundColour('MAROON')
                            # self.stxtIndicator[iii].SetBackgroundColour('NAVY')
                        
                        self.stxtIndicator[iii].Refresh()

                    break
                
                else:
                    # search throughout pcm items
                    for iii in range(self.parent.N_ITEM_PCM):
                        # skip
                        if (   self.parent.TlmItemAttr_pcm[iii]['group']      != strGroupName 
                            or self.parent.TlmItemAttr_pcm[iii]['item order'] != ii ) :
                            continue

                        # refresh indicator
                        self.stxtIndicator[iii+self.parent.N_ITEM_SMT].SetLabel(str(np.round(self.parent.dfTlm_pcm.iloc[-1, iii], 2)))
                        
                        break

    # Load configurations from external files
    def load_config_digital_indicator(self):
        ### T.B.REFAC.: TEMPORALLY DESIGNATED BY LITERALS ###
        N_ITEM_PER_ROW = 6

        self.GroupAttr = {
            'Time':          {'gidx': 0, 'rows': 1, 'cols': N_ITEM_PER_ROW},
            'DES State':     {'gidx': 1, 'rows': 5, 'cols': N_ITEM_PER_ROW},
            'Pressure':      {'gidx': 2, 'rows': 2, 'cols': N_ITEM_PER_ROW},
            'Temperature':   {'gidx': 3, 'rows': 2, 'cols': N_ITEM_PER_ROW},
            'IMU':           {'gidx': 4, 'rows': 2, 'cols': N_ITEM_PER_ROW},
            'House Keeping': {'gidx': 5, 'rows': 3, 'cols': N_ITEM_PER_ROW}
        }

    # Configure appearance for digital indicators to display current values
    def configure_digital_indicator(self):
        self.IndicatorPane = wx.BoxSizer(wx.VERTICAL)

        ### generate containers to groupe indicators (StaticBox)
        self.SBoxGroup = []
        self.lytSBoxGroup = []
        for strGroupName in self.GroupAttr.keys():
            # - generate an instance
            self.SBoxGroup.append(wx.StaticBox(self, wx.ID_ANY, strGroupName))
            self.SBoxGroup[-1].SetForegroundColour('WHITE')
            self.SBoxGroup[-1].SetFont(wx.Font(15, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            
            # - lay out the instance
            self.lytSBoxGroup.append(wx.StaticBoxSizer(self.SBoxGroup[-1], wx.VERTICAL))
            self.IndicatorPane.Add(self.lytSBoxGroup[-1])

        ### generate indicators & their labels
        self.tbtnLabel = []
        self.stxtIndicator = []
        self.lytPair = []           # pair of Indicator & Label
        
        # smt items
        for i in range(self.parent.N_ITEM_SMT):
            # generate instance 
            # - item label (ToggleButton)
            self.tbtnLabel.append(
                wx.ToggleButton(self, wx.ID_ANY, self.parent.TlmItemAttr_smt[i]['item'], size=(140,22)))
            
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
        for i in range(self.parent.N_ITEM_PCM):
            # generate instance 
            # - item label (ToggleButton)
            self.tbtnLabel.append(
                wx.ToggleButton(self, wx.ID_ANY, self.parent.TlmItemAttr_pcm[i]['item'], size=(140,22)))
            
            # - digital indicator (StaticText)
            self.stxtIndicator.append(
                wx.StaticText(self, wx.ID_ANY, str(i + self.parent.N_ITEM_SMT), style=wx.ALIGN_CENTRE | wx.ST_NO_AUTORESIZE))
            self.stxtIndicator[-1].SetBackgroundColour('BLACK')
            self.stxtIndicator[-1].SetForegroundColour('GREEN')

            # - pair of item label & inidicator
            self.lytPair.append(wx.GridSizer(rows=2, cols=1, gap=(0,0)))
            self.lytPair[-1].Add(self.tbtnLabel[-1], flag=wx.EXPAND)
            self.lytPair[-1].Add(self.stxtIndicator[-1], flag=wx.EXPAND)

        ### lay out pairs of indicators & labels in the grouping SBoxes
        self.lytIndicator = []
        for strGroupName in self.GroupAttr.keys():
            i = self.GroupAttr[strGroupName]['gidx']
            
            # generate grid in the grouping SBox
            self.lytIndicator.append(
                wx.GridSizer(rows=self.GroupAttr[strGroupName]['rows'], cols=self.GroupAttr[strGroupName]['cols'], gap=(10,5)))
            
            # place items in the grid
            for ii in range(self.GroupAttr[strGroupName]['rows'] * self.GroupAttr[strGroupName]['cols']):
                # initialize
                j = -1

                # search throughout smt items
                for iii in range(self.parent.N_ITEM_SMT):
                    if (    self.parent.TlmItemAttr_smt[iii]['group'] == strGroupName 
                        and self.parent.TlmItemAttr_smt[iii]['item order'] == ii ) :
                        j = iii
                        break    
                else:
                    # search throughout pcm items
                    for iii in range(self.parent.N_ITEM_PCM):
                        if (    self.parent.TlmItemAttr_pcm[iii]['group'] == strGroupName 
                            and self.parent.TlmItemAttr_pcm[iii]['item order'] == ii ) :
                            j = iii + self.parent.N_ITEM_SMT
                            break

                # assign items in grids
                if j == -1:
                    self.lytIndicator[i].Add((0,0))                         # empty cell
                    # self.lytIndicator[i].Add(wx.StaticText(self, -1, ''))   # empty cell
                else:
                    self.lytIndicator[i].Add(self.lytPair[j], flag=wx.EXPAND)
            
            # snap
            self.lytSBoxGroup[i].Add(self.lytIndicator[i])

        # set states for ToggleButton
        # for i in range(pnlPlotter.N_PLOTTER):
        #     self.tbtnLabel[self.PlotterAttr[i]['idx_item']].SetValue(True)

        # for button in self.tbtnLabel:
        #     button.Bind(wx.EVT_TOGGLEBUTTON, self.graphTest)


# 
#   Panel for Time History Plots & Current Value Indicators
# 
class ChartPanel(wx.Panel):
    __N_PLOTTER = 5
    __T_RANGE = 30    # [s]

    # __IDX_TIME = 1
    __IDX_TIME = 2      # tentative

    __PLOT_SKIP = 9    ### T.B.REFAC. ###
    # __PLOT_SKIP = 39    ### T.B.REFAC. ###

    # def __init__(self, parent, q_data_smt, q_data_pcm):
    def __init__(self, parent):
        super().__init__(parent, wx.ID_ANY)

        ### initialize
        self.parent = parent

        self.__PLOT_COUNT = self.__PLOT_SKIP   ### T.B.REFAC. ###

        # - digital indicator config
        self.load_config_digital_indicator()

        # - plotter config
        self.load_config_plotter()

        ### configure appearance
        self.configure_digital_indicator()
        self.configure_plotter()

        ### lay out panes
        layout = wx.FlexGridSizer(rows=1, cols=2, gap=(20, 0))
        layout.Add(self.canvas, flag=wx.EXPAND)                            # plotter pane
        layout.Add(self.IndicatorPane, flag=wx.ALIGN_CENTER_HORIZONTAL)    # digital indicator pane
        self.SetSizer(layout)

        ### bind events
        # - set timer to refresh current-value pane
        self.tmrRefreshDigitalIndicator = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnRefreshDigitalIndicator, self.tmrRefreshDigitalIndicator)
        self.tmrRefreshDigitalIndicator.Start(REFLESH_RATE_DIGITAL_INDICATOR)

        # - set timer to refresh time-history pane
        self.tmrRefreshPlotter = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnRefreshPlotter, self.tmrRefreshPlotter)
        self.tmrRefreshPlotter.Start(REFLESH_RATE_PLOTTER)

    # Event handler: EVT_TIMER
    def OnRefreshDigitalIndicator(self, event):
        # skip refresh when TLM NOT active
        if self.parent.F_TLM_IS_ACTIVE == False:    return None
        
        ### refresh indicators
        # - sweep groups
        for strGroupName in self.GroupAttr.keys():
            # - seep items belong each group    ### T.B.REFAC. ###
            for ii in range(self.GroupAttr[strGroupName]['rows'] * self.GroupAttr[strGroupName]['cols']):
                # search throughout smt items
                for iii in range(self.parent.N_ITEM_SMT):
                    # skip
                    if (   self.parent.TlmItemAttr_smt[iii]['group']      != strGroupName
                        or self.parent.TlmItemAttr_smt[iii]['item order'] != ii ):
                        continue

                    # refresh indicator
                    self.stxtIndicator[iii].SetLabel(str(np.round(self.parent.dfTlm_smt.iloc[-1, iii], 2)))
                    # self.stxtIndicator[iii].SetLabel(str(np.round(df_smt_tmp.iloc[-1, iii], 2)))

                    # accentuate indicator by colors
                    if self.parent.TlmItemAttr_smt[iii]['type'] == 'bool':
                        # - OFF
                        # if int(df_smt_tmp.iloc[-1, iii]) == 0:
                        if int(self.parent.dfTlm_smt.iloc[-1, iii]) == 0:
                            self.tbtnLabel[iii].SetForegroundColour('NullColour')
                            self.stxtIndicator[iii].SetBackgroundColour('NullColour')
                            # self.stxtIndicator[iii].SetBackgroundColour('NAVY')
                        # - ON
                        else:
                            self.tbtnLabel[iii].SetForegroundColour('RED')
                            # self.tbtnLabel[iii].SetForegroundColour('BLUE')
                            # self.stxtIndicator[iii].SetBackgroundColour('GREY')
                            self.stxtIndicator[iii].SetBackgroundColour('MAROON')
                            # self.stxtIndicator[iii].SetBackgroundColour('NAVY')
                        
                        self.stxtIndicator[iii].Refresh()

                    break
                
                else:
                    # search throughout pcm items
                    for iii in range(self.parent.N_ITEM_PCM):
                        # skip
                        if (   self.parent.TlmItemAttr_pcm[iii]['group']      != strGroupName 
                            or self.parent.TlmItemAttr_pcm[iii]['item order'] != ii ) :
                            continue

                        # refresh indicator
                        self.stxtIndicator[iii+self.parent.N_ITEM_SMT].SetLabel(str(np.round(self.parent.dfTlm_pcm.iloc[-1, iii], 2)))
                        
                        break

        # - sweep groups
        # for i in self.GroupAttr.keys():
        #     # - seep items belong each group    ### T.B.REFAC. ###
        #     for ii in range(self.GroupAttr[i]['rows'] * self.GroupAttr[i]['cols']):
        #         # search throughout smt items
        #         for iii in range(self.parent.N_ITEM_SMT):
        #             # skip
        #             if (   self.parent.TlmItemAttr_smt[iii]['group']      != self.GroupAttr[i]['label']
        #                 or self.parent.TlmItemAttr_smt[iii]['item order'] != ii ):
        #                 continue

        #             # refresh indicator
        #             self.stxtIndicator[iii].SetLabel(str(np.round(self.parent.dfTlm_smt.iloc[-1, iii], 2)))
        #             # self.stxtIndicator[iii].SetLabel(str(np.round(df_smt_tmp.iloc[-1, iii], 2)))

        #             # accentuate indicator by colors
        #             if self.parent.TlmItemAttr_smt[iii]['type'] == 'bool':
        #                 # - OFF
        #                 # if int(df_smt_tmp.iloc[-1, iii]) == 0:
        #                 if int(self.parent.dfTlm_smt.iloc[-1, iii]) == 0:
        #                     self.tbtnLabel[iii].SetForegroundColour('NullColour')
        #                     self.stxtIndicator[iii].SetBackgroundColour('NullColour')
        #                     # self.stxtIndicator[iii].SetBackgroundColour('NAVY')
        #                 # - ON
        #                 else:
        #                     self.tbtnLabel[iii].SetForegroundColour('RED')
        #                     # self.tbtnLabel[iii].SetForegroundColour('BLUE')
        #                     # self.stxtIndicator[iii].SetBackgroundColour('GREY')
        #                     self.stxtIndicator[iii].SetBackgroundColour('MAROON')
        #                     # self.stxtIndicator[iii].SetBackgroundColour('NAVY')
                        
        #                 self.stxtIndicator[iii].Refresh()

        #             break
                
        #         else:
        #             # search throughout pcm items
        #             for iii in range(self.parent.N_ITEM_PCM):
        #                 # skip
        #                 if ( self.parent.TlmItemAttr_pcm[iii]['group']      != self.GroupAttr[i]['label'] or
        #                      self.parent.TlmItemAttr_pcm[iii]['item order'] != ii ) :
        #                     continue

        #                 # refresh indicator
        #                 self.stxtIndicator[iii+self.parent.N_ITEM_SMT].SetLabel(str(np.round(self.parent.dfTlm_pcm.iloc[-1, iii], 2)))
                        
        #                 break

    # Event handler: EVT_TIMER
    def OnRefreshPlotter(self, event):
        # skip refresh when TLM NOT active
        if self.parent.F_TLM_IS_ACTIVE == False:    return None
        # print(f'GUI PLT: F_TLM_IS_ACTIVE = {self.parent.F_TLM_IS_ACTIVE}')      # for debug

        ### update data set for plot
        df_tmp = pd.concat([self.parent.dfTlm_smt, self.parent.dfTlm_pcm], axis=1)      ### T.B.REFAC. ###
        
        # - update plot points by appending latest values
        self.x_series = np.append(self.x_series, df_tmp.iloc[-1,self.__IDX_TIME])
        for i in range(self.__N_PLOTTER):
            self.y_series = np.append(self.y_series, df_tmp.iloc[-1,self.PlotterAttr[i]['idx_item']])
            # self.y_series = np.append(self.y_series, df_tmp.iloc[-1,self.PlotterAttr[i]['idx_item']+1])     # tentative

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
            self.y_series = np.delete(self.y_series, np.s_[0:self.__N_PLOTTER])
            # print('GUI PLT: a member of 'x_series' is out of the range')

        ### T.B.REFAC. ###
        # skip redraw
        if self.__PLOT_COUNT != self.__PLOT_SKIP:
            self.__PLOT_COUNT += 1
            return None
        self.__PLOT_COUNT = 0

        ### refresh plotter
        self.lines = []
        for i in range(self.__N_PLOTTER):
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
            self.lines.append(self.axes[i].plot(self.x_series, self.y_series[i::self.__N_PLOTTER], color='LIME')[0])
     
            # reflect updates in lines
            self.axes[i].draw_artist(self.lines[i])

        # redraw and show updated canvas
        for i in range(self.__N_PLOTTER):
            self.fig.canvas.blit(self.axes[i].bbox)

        # redraw and show updated canvas
        # self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        
        # print("GUI PLT: redraw plots...")

    # Load configurations from external files
    def load_config_digital_indicator(self):
        ### T.B.REFAC.: TEMPORALLY DESIGNATED BY LITERALS ###
        N_ITEM_PER_ROW = 6

        self.GroupAttr = {
            'Time':          {'gidx': 0, 'rows': 1, 'cols': N_ITEM_PER_ROW},
            'DES State':     {'gidx': 1, 'rows': 5, 'cols': N_ITEM_PER_ROW},
            'Pressure':      {'gidx': 2, 'rows': 2, 'cols': N_ITEM_PER_ROW},
            'Temperature':   {'gidx': 3, 'rows': 2, 'cols': N_ITEM_PER_ROW},
            'IMU':           {'gidx': 4, 'rows': 2, 'cols': N_ITEM_PER_ROW},
            'House Keeping': {'gidx': 5, 'rows': 3, 'cols': N_ITEM_PER_ROW}
        }
        # self.GroupAttr = {
        #     0: {'idx': 0, 'label': 'Time',          'rows': 1, 'cols': 6},
        #     1: {'idx': 1, 'label': 'DES State',     'rows': 5, 'cols': 6},
        #     2: {'idx': 2, 'label': 'Pressure',      'rows': 2, 'cols': 6},
        #     3: {'idx': 3, 'label': 'Temperature',   'rows': 2, 'cols': 6},
        #     4: {'idx': 4, 'label': 'IMU',           'rows': 2, 'cols': 6},
        #     5: {'idx': 5, 'label': 'House Keeping', 'rows': 3, 'cols': 6}
        # }
        
    # Configure appearance for digital indicators to display current values
    def configure_digital_indicator(self):
        self.IndicatorPane = wx.BoxSizer(wx.VERTICAL)

        ### generate containers to groupe indicators (StaticBox)
        self.SBoxGroup = []
        self.lytSBoxGroup = []
        for strGroupName in self.GroupAttr.keys():
            # - generate an instance
            self.SBoxGroup.append(wx.StaticBox(self, wx.ID_ANY, strGroupName))
            self.SBoxGroup[-1].SetForegroundColour('WHITE')
            self.SBoxGroup[-1].SetFont(wx.Font(15, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            
            # - lay out the instance
            self.lytSBoxGroup.append(wx.StaticBoxSizer(self.SBoxGroup[-1], wx.VERTICAL))
            self.IndicatorPane.Add(self.lytSBoxGroup[-1])

        # for i in self.GroupAttr.keys():
        #     # - generate an instance
        #     self.SBoxGroup.append(wx.StaticBox(self, wx.ID_ANY, self.GroupAttr[i]['label']))
        #     self.SBoxGroup[-1].SetForegroundColour('WHITE')
        #     self.SBoxGroup[-1].SetFont(wx.Font(15, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            
        #     # - lay out the instance
        #     self.lytSBoxGroup.append(wx.StaticBoxSizer(self.SBoxGroup[-1], wx.VERTICAL))
        #     self.IndicatorPane.Add(self.lytSBoxGroup[-1])

        ### generate indicators & their labels
        self.tbtnLabel = []
        self.stxtIndicator = []
        self.lytPair = []           # pair of Indicator & Label
        
        # smt items
        for i in range(self.parent.N_ITEM_SMT):
            # generate instance 
            # - item label (ToggleButton)
            self.tbtnLabel.append(
                wx.ToggleButton(self, wx.ID_ANY, self.parent.TlmItemAttr_smt[i]['item'], size=(140,22)))
            
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
        for i in range(self.parent.N_ITEM_PCM):
            # generate instance 
            # - item label (ToggleButton)
            self.tbtnLabel.append(
                wx.ToggleButton(self, wx.ID_ANY, self.parent.TlmItemAttr_pcm[i]['item'], size=(120,22)))
            
            # - digital indicator (StaticText)
            self.stxtIndicator.append(
                wx.StaticText(self, wx.ID_ANY, str(i + self.parent.N_ITEM_SMT), style=wx.ALIGN_CENTRE | wx.ST_NO_AUTORESIZE))
            self.stxtIndicator[-1].SetBackgroundColour('BLACK')
            self.stxtIndicator[-1].SetForegroundColour('GREEN')

            # - pair of item label & inidicator
            self.lytPair.append(wx.GridSizer(rows=2, cols=1, gap=(0,0)))
            self.lytPair[-1].Add(self.tbtnLabel[-1], flag=wx.EXPAND)
            self.lytPair[-1].Add(self.stxtIndicator[-1], flag=wx.EXPAND)

        ### lay out pairs of indicators & labels in the grouping SBoxes
        # self.lytIndicator = []
        # for i in self.GroupAttr.keys():
        #     # generate grid in the grouping SBox
        #     self.lytIndicator.append(
        #         wx.GridSizer(rows=self.GroupAttr[i]['rows'], cols=self.GroupAttr[i]['cols'], gap=(10,5)))
            
        #     # place items in the grid
        #     for ii in range(self.GroupAttr[i]['rows'] * self.GroupAttr[i]['cols']):
        #         # initialize
        #         j = -1

        #         # search throughout smt items
        #         for iii in range(self.parent.N_ITEM_SMT):
        #             if ( self.parent.TlmItemAttr_smt[iii]['group'] == self.GroupAttr[i]['label'] and
        #                  self.parent.TlmItemAttr_smt[iii]['item order'] == ii ) :
        #                 j = iii
        #                 break    
        #         else:
        #             # search throughout pcm items
        #             for iii in range(self.parent.N_ITEM_PCM):
        #                 if ( self.parent.TlmItemAttr_pcm[iii]['group'] == self.GroupAttr[i]['label'] and
        #                      self.parent.TlmItemAttr_pcm[iii]['item order'] == ii ) :
        #                     j = iii + self.parent.N_ITEM_SMT
        #                     break

        self.lytIndicator = []
        for strGroupName in self.GroupAttr.keys():
            i = self.GroupAttr[strGroupName]['gidx']
            
            # generate grid in the grouping SBox
            self.lytIndicator.append(
                wx.GridSizer(rows=self.GroupAttr[strGroupName]['rows'], cols=self.GroupAttr[strGroupName]['cols'], gap=(10,5)))
            
            # place items in the grid
            for ii in range(self.GroupAttr[strGroupName]['rows'] * self.GroupAttr[strGroupName]['cols']):
                # initialize
                j = -1

                # search throughout smt items
                for iii in range(self.parent.N_ITEM_SMT):
                    if (    self.parent.TlmItemAttr_smt[iii]['group'] == strGroupName 
                        and self.parent.TlmItemAttr_smt[iii]['item order'] == ii ) :
                        j = iii
                        break    
                else:
                    # search throughout pcm items
                    for iii in range(self.parent.N_ITEM_PCM):
                        if (    self.parent.TlmItemAttr_pcm[iii]['group'] == strGroupName 
                            and self.parent.TlmItemAttr_pcm[iii]['item order'] == ii ) :
                            j = iii + self.parent.N_ITEM_SMT
                            break

                # assign items in grids
                if j == -1:
                    self.lytIndicator[i].Add((0,0))                         # empty cell
                    # self.lytIndicator[i].Add(wx.StaticText(self, -1, ''))   # empty cell
                else:
                    self.lytIndicator[i].Add(self.lytPair[j], flag=wx.EXPAND)
            
            # snap
            self.lytSBoxGroup[i].Add(self.lytIndicator[i])

        # set states for ToggleButton
        for i in range(self.__N_PLOTTER):
            self.tbtnLabel[self.PlotterAttr[i]['idx_item']].SetValue(True)
        # for index in self.index_plot:
            # self.tbtnLabel[index].SetValue(True)

        # for button in self.tbtnLabel:
        #     button.Bind(wx.EVT_TOGGLEBUTTON, self.graphTest)

    # Load configurations from external files
    def load_config_plotter(self):
        # handle exception
        # if self.__N_PLOTTER > 5: self.__N_PLOTTER = 5
        self.__N_PLOTTER = max(1, min(5, self.__N_PLOTTER))

        self.PlotterAttr = {}
        for i in range(self.__N_PLOTTER):  
            dict_tmp = {}

            # search throughout smt items
            for iii in range(self.parent.N_ITEM_SMT):
                if self.parent.TlmItemAttr_smt[iii]['plot #'] != i: continue       # skip
      
                dict_tmp['idx_item']    = iii
                dict_tmp['y_label']     = str(self.parent.TlmItemAttr_smt[iii]['item'])
                dict_tmp['y_unit']      = str(self.parent.TlmItemAttr_smt[iii]['unit'])
                dict_tmp['y_min']       = float(self.parent.TlmItemAttr_smt[iii]['y_min'])
                dict_tmp['y_max']       = float(self.parent.TlmItemAttr_smt[iii]['y_max'])
                dict_tmp['alart_lim_l'] = float(self.parent.TlmItemAttr_smt[iii]['alert_lim_l'])
                dict_tmp['alart_lim_u'] = float(self.parent.TlmItemAttr_smt[iii]['alert_lim_u'])

                break
            
            else:
                # search throughout pcm items
                for iii in range(self.parent.N_ITEM_PCM):
                    if self.parent.TlmItemAttr_pcm[iii]['plot #'] != i: continue   # skip

                    dict_tmp['idx_item']    = iii + self.parent.N_ITEM_SMT
                    dict_tmp['y_label']     = str(self.parent.TlmItemAttr_pcm[iii]['item'])
                    dict_tmp['y_unit']      = str(self.parent.TlmItemAttr_pcm[iii]['unit'])
                    dict_tmp['y_min']       = float(self.parent.TlmItemAttr_pcm[iii]['y_min'])
                    dict_tmp['y_max']       = float(self.parent.TlmItemAttr_pcm[iii]['y_max'])
                    dict_tmp['alart_lim_l'] = float(self.parent.TlmItemAttr_pcm[iii]['alert_lim_l'])
                    dict_tmp['alart_lim_u'] = float(self.parent.TlmItemAttr_pcm[iii]['alert_lim_u'])

                    break

            # append attibutions for i-th plotter 
            self.PlotterAttr[i] = dict_tmp

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
            self.axes[i].set_ylim([self.PlotterAttr[i]['y_min'], self.PlotterAttr[i]['y_max']])

            # - set label for y axis
            self.axes[i].set_ylabel(self.PlotterAttr[i]['y_label'])
            # self.axes[i].set_ylabel(self.PlotterAttr[i]['y_label'] + f' [{self.PlotterAttr[i]['y_unit']}]')

        # tentatively draw canvas without plot points to save as background
        self.canvas.draw()                                            

        # save the empty canvas as background
        # NOTE: backgrounds become iterrable hereafter
        self.backgrounds = []
        for i in range(self.__N_PLOTTER):
            self.backgrounds.append(self.canvas.copy_from_bbox(self.axes[i].bbox))






