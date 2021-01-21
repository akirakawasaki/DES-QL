"""
Standard libraries
"""
import sys
import threading
import time

"""
Third-party libraries
"""
import numpy as np
import pandas as pd

import wx
import matplotlib
matplotlib.use('WxAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.figure import Figure

"""
Local libraries
"""
from usrmod import tlm

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
Top Level Window Class
"""
class MainWindow(wx.Frame):
    def __init__(self, reflesh_time_chart, reflesh_time_value):

        super().__init__(None, wx.ID_ANY, 'Rocket System Information App')

        self.Maximize(True)     # Maxmize GUI window size

        self.SetBackgroundColour('Dark Grey')
        #self.SetBackgroundColour('Black')

        # Making Main Graphic
        root_panel = wx.Panel(self, wx.ID_ANY)

        # System panel : Show the feeding system status
        self.chart_panel = ChartPanel(root_panel, reflesh_time_chart, reflesh_time_value)

        # Set layout of panels
        root_layout = wx.GridBagSizer()
        root_layout.Add(self.chart_panel, pos=wx.GBPosition(0,0), flag=wx.EXPAND | wx.ALL, border=10)

        root_panel.SetSizer(root_layout)
        root_layout.Fit(root_panel)

        # Enable Close Event
        self.Bind(wx.EVT_CLOSE, self.onClose)

    def onClose(self, event):
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

    def __init__(self, parent, reflesh_time_graph, reflesh_time_value):
        super().__init__(parent, wx.ID_ANY)

        self.configReader()
        self.flag_temp = True

        self.valueGenerator()
        self.chartGenerator()

        # layout time history pane
        self.layout = wx.FlexGridSizer(rows=1, cols=2, gap=(20, 0))
        self.layout.Add(self.canvas, flag=wx.EXPAND)
        self.layout.Add(self.layout_Value, flag=wx.ALIGN_CENTER_HORIZONTAL)
        self.SetSizer(self.layout)

        # set refresh timer for time history pane
        self.timer_reload_graph = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.graphReloader, self.timer_reload_graph)
        self.timer_reload_graph.Start(reflesh_time_graph)

        # set refresh timer for current value pane
        self.timer_reload_value = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.valueReloader, self.timer_reload_value)
        self.timer_reload_value.Start(reflesh_time_value)

    def configReader(self):
        # load smt data config
        self.df_cfg_tlm = th_smt.smt.df_cfg.copy()
        self.df_cfg_tlm.reset_index()

        df_cfg_plot_tmp = pd.read_excel('./config_plot.xlsx', sheet_name='smt')
        self.df_cfg_plot = df_cfg_plot_tmp.dropna(how='all')

        self.index_plot = [self.df_cfg_plot['ID'][self.df_cfg_plot['plot_1'].astype(bool)].astype(int).iat[0],
                          self.df_cfg_plot['ID'][self.df_cfg_plot['plot_2'].astype(bool)].astype(int).iat[0],
                          self.df_cfg_plot['ID'][self.df_cfg_plot['plot_3'].astype(bool)].astype(int).iat[0],
                          self.df_cfg_plot['ID'][self.df_cfg_plot['plot_4'].astype(bool)].astype(int).iat[0],
                          self.df_cfg_plot['ID'][self.df_cfg_plot['plot_5'].astype(bool)].astype(int).iat[0]]
        print(self.index_plot)
        self.item_plot = [self.df_cfg_plot['item'][self.df_cfg_plot['plot_1'].astype(bool)].iat[0],
                          self.df_cfg_plot['item'][self.df_cfg_plot['plot_2'].astype(bool)].iat[0],
                          self.df_cfg_plot['item'][self.df_cfg_plot['plot_3'].astype(bool)].iat[0],
                          self.df_cfg_plot['item'][self.df_cfg_plot['plot_4'].astype(bool)].iat[0],
                          self.df_cfg_plot['item'][self.df_cfg_plot['plot_5'].astype(bool)].iat[0]]
        print(self.item_plot)
        self.unit_plot = [self.df_cfg_plot['unit'][self.df_cfg_plot['plot_1'].astype(bool)].iat[0],
                          self.df_cfg_plot['unit'][self.df_cfg_plot['plot_2'].astype(bool)].iat[0],
                          self.df_cfg_plot['unit'][self.df_cfg_plot['plot_3'].astype(bool)].iat[0],
                          self.df_cfg_plot['unit'][self.df_cfg_plot['plot_4'].astype(bool)].iat[0],
                          self.df_cfg_plot['unit'][self.df_cfg_plot['plot_5'].astype(bool)].iat[0]]
        print(self.unit_plot)
        self.y_min_plot = [self.df_cfg_plot['y_min'][self.df_cfg_plot['plot_1'].astype(bool)].iat[0],
                          self.df_cfg_plot['y_min'][self.df_cfg_plot['plot_2'].astype(bool)].iat[0],
                          self.df_cfg_plot['y_min'][self.df_cfg_plot['plot_3'].astype(bool)].iat[0],
                          self.df_cfg_plot['y_min'][self.df_cfg_plot['plot_4'].astype(bool)].iat[0],
                          self.df_cfg_plot['y_min'][self.df_cfg_plot['plot_5'].astype(bool)].iat[0]]
        print(self.y_min_plot)
        self.y_max_plot = [self.df_cfg_plot['y_max'][self.df_cfg_plot['plot_1'].astype(bool)].iat[0],
                          self.df_cfg_plot['y_max'][self.df_cfg_plot['plot_2'].astype(bool)].iat[0],
                          self.df_cfg_plot['y_max'][self.df_cfg_plot['plot_3'].astype(bool)].iat[0],
                          self.df_cfg_plot['y_max'][self.df_cfg_plot['plot_4'].astype(bool)].iat[0],
                          self.df_cfg_plot['y_max'][self.df_cfg_plot['plot_5'].astype(bool)].iat[0]]
        print(self.y_max_plot)


        df_cfg_sensor_tmp = pd.read_excel('./config_sensor.xlsx', sheet_name='smt')
        self.df_cfg_sensor = df_cfg_sensor_tmp.dropna(how='all')

        self.id_time = self.df_cfg_sensor[self.df_cfg_sensor['group'] == 'Time [s]']['ID'].astype(int)
        self.id_p = self.df_cfg_sensor[self.df_cfg_sensor['group'] == 'P [MPa]']['ID'].astype(int)
        self.id_T = self.df_cfg_sensor[self.df_cfg_sensor['group'] == 'T [K]']['ID'].astype(int)
        self.id_imu = self.df_cfg_sensor[self.df_cfg_sensor['group'] == 'IMU']['ID'].astype(int)
        self.id_hk = self.df_cfg_sensor[self.df_cfg_sensor['group'] == 'House Keeping']['ID'].astype(int)

        self.id = [self.id_time, self.id_p, self.id_T, self.id_imu, self.id_hk]

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

    def chartGenerator(self):
        ''' Time history plots '''
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

        self.canvas.draw()                                            # Plot Empty Chart

        self.backgrounds = []
        for i in range(self.n_plot):
            self.backgrounds.append(self.canvas.copy_from_bbox(self.axes[i].bbox))  # Save Empty Chart Format as Background

    def valueGenerator(self):
        ''' Current value indicators '''
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

        # layout current value panel
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

    def graphReloader(self, event):
        # Set Plot Data
        try:
            self.data_past
        except AttributeError:
            self.data_plot = self.df.values
        else:
            self.data_plot = np.append(self.data_past, self.df.values, axis=0)

        t_temp = self.df.iloc[-1, self.index_x]

        if t_temp >= self.t_left+self.t_range:
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

        for i in range(self.n_plot):
            self.canvas.restore_region(self.backgrounds[i])                 # Re-plot Background (i.e. Delete line)

        for i in range(self.n_plot):
            self.axes[i].draw_artist(self.lines[i])                              # Set new data in ax

        for i in range(self.n_plot):
            self.fig.canvas.blit(self.axes[i].bbox)                          # Plot New data

    def valueReloader(self, event):
        # update current values
        for i_sensor in range(len(self.df_cfg_tlm['item'])):
            self.SensorValue[i_sensor].SetLabel(str(np.round(self.df.iloc[-1, i_sensor], 2)))

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

"""
SMT
"""
class smt_thread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

        # STEP 0: initialize
        self.smt = tlm.tlm('smt')
        #self.smt = tlm.tlm('pcm')
        #self.pcm = tlm.tlm('pcm')

        self.DATA_SAVE_INTERVAL = 500
        self.df_ui = self.smt.df_mf

    def run(self):
        print('SMT Thread Launched!')

        self.NNN = 1
        while flag_GUI:
            # STEP 1: data receive
            self.smt.receive()

            # STEP 2: data reshape
            self.smt.reshape()

            # STEP 3: data save
            #self.smt.append_to_file()

            # STEP 4: data display
            try:
                GUI_Frame
            except NameError:
                if self.NNN % 50 == 0:  print('Generating GUI ...')
                pass
            else:
                if self.NNN % 10 == 0:
                    self.df_ui = self.smt.append_to_dataframe(self.df_ui)
                    try:
                        GUI_Frame.chart_panel.df
                    except AttributeError:  # In the case of wxpython is not opened
                        GUI_Frame.chart_panel.dfReloder()
                    else:
                        wx.CallAfter(GUI_Frame.chart_panel.dfReloder)

            # incliment counter
            self.NNN += 1

        if self.NNN == 1:   print('Error : UDP program stopped')


if __name__ == "__main__":
    print('DES QL Launched!')

    th_smt = smt_thread()
    th_smt.setDaemon(True)

    """
    th_pcm = pcm_thread()
    th_pcm.setDaemon(True)
    """

    flag_GUI = True

    th_smt.start()
    # th_pcm.start()

    time.sleep(1)
    while True:
        if th_smt.smt.df_mf.empty:
            print("UDP port received no data...")
            time.sleep(2)
        else:
            print("UDP port received data!")
            break

    app = wx.App()
    GUI_Frame = MainWindow(reflesh_time_chart=1000,
                           reflesh_time_value=450)
    while True:
        try:
            GUI_Frame.chart_panel.df
            print('GUI Thread Launched!')
            GUI_Frame.Show()
            break
        except AttributeError:
            pass

    app.MainLoop()

    flag_GUI = False

    print('... DES QL quitted normally')
