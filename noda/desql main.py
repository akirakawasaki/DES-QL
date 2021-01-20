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

from stl import mesh
from mpl_toolkits import mplot3d

"""
Local libraries
"""
from usrmod import tlm_copy as tlm

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
    t_range = 30

    n_time = 3
    index_plot1 = 11   # Pple,o(8+3)
    index_plot2 = 2  # Tth,rde(18+3)
    index_plot3 = 22  # Tcpde(19+3)

    sensor_type = ['Time [s]', 'P [MPa]', 'T [K]', 'IMU', 'House Keeping']
    n_type = np.array([3, 10, 2, 10, 6, 6, 5, 16, 6, 2])
    # n_type = np.array([3, 10, 2, 10, 6, 6, 5, 16, 6, 2])

    def __init__(self, parent, reflesh_time_graph, reflesh_time_value):
        super().__init__(parent, wx.ID_ANY)

        self.configReader()
        self.flag_temp = False

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

        self.df_cfg_plot = pd.read_excel('./config_plot.xlsx', sheet_name='smt')
        self.df_cfg_sensor = pd.read_excel('./config_sensor.xlsx', sheet_name='smt')

        self.id_time = self.df_cfg_sensor[self.df_cfg_sensor['group'] == 'Time [s]']['ID'].astype(int)
        self.id_p = self.df_cfg_sensor[self.df_cfg_sensor['group'] == 'P [MPa]']['ID'].astype(int)
        self.id_T = self.df_cfg_sensor[self.df_cfg_sensor['group'] == 'T [K]']['ID'].astype(int)
        self.id_imu = self.df_cfg_sensor[self.df_cfg_sensor['group'] == 'IMU']['ID'].astype(int)
        self.id_hk = self.df_cfg_sensor[self.df_cfg_sensor['group'] == 'House Keeping']['ID'].astype(int)

        self.id = [self.id_time, self.id_p, self.id_T, self.id_imu, self.id_hk]

    def dfReloder(self):
        self.df = th_smt.df_ui.copy()

    def chartGenerator(self):
        ''' Time history plots '''
        self.fig = Figure(figsize=(6, 8))
        self.ax1 = self.fig.add_subplot(311)
        self.ax2 = self.fig.add_subplot(312)
        self.ax3 = self.fig.add_subplot(313)
        self.canvas = FigureCanvasWxAgg(self, -1, self.fig)

        self.ax1.set_ylim([0.0, 1.5])
        self.ax2.set_ylim([0.0, 100000.0])
        self.ax3.set_ylim([200.0, 600.0])

        self.t_left = 0
        self.ax1.set_xlim([self.t_left, self.t_left + self.t_range])
        self.ax2.set_xlim([self.t_left, self.t_left + self.t_range])
        self.ax3.set_xlim([self.t_left, self.t_left + self.t_range])

        self.canvas.draw()                                            # Plot Empty Chart
        self.background1 = self.canvas.copy_from_bbox(self.ax1.bbox)  # Save Empty Chart Format as Background
        self.background2 = self.canvas.copy_from_bbox(self.ax2.bbox)  # Save Empty Chart Format as Background
        self.background3 = self.canvas.copy_from_bbox(self.ax3.bbox)  # Save Empty Chart Format as Background

    def valueGenerator(self):
        ''' Current value indicators '''
        self.col_value = [5, 8, 8, 9, 8]

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

        # for button in self.DataButton:
        #     button.Bind(wx.EVT_TOGGLEBUTTON, self.graphTest)

    def graphReloader(self, event):
        t_temp = self.df.iloc[-1, self.index_x]

        if t_temp >= self.t_left+self.t_range:

            self.i_left = self.df.shape[0]
            self.lines1 = []
            self.lines2 = []
            self.lines3 = []

            self.ax1.cla()
            self.ax2.cla()
            self.ax3.cla()

            self.t_left = self.df.iloc[-1, self.index_x]
            self.ax1.set_xlim([self.t_left, self.t_left + self.t_range])
            self.ax2.set_xlim([self.t_left, self.t_left + self.t_range])
            self.ax3.set_xlim([self.t_left, self.t_left + self.t_range])

            self.ax1.set_ylim([-1.0, 1.5])
            self.ax2.set_ylim([0.0, 100000.0])
            self.ax3.set_ylim([200.0, 600.0])

            # draw alert line
            self.ax1.axhline(y=1.0, xmin=0, xmax=1, color='red')
            """
            self.ax2.axhline(y=500.0, xmin=0, xmax=1, color='red')
            self.ax3.axhline(y=500.0, xmin=0, xmax=1, color='red')
            """

            self.ax1.set_ylabel('Pple,o [MPa]')
            self.ax2.set_ylabel('Tth,rde [K]')
            self.ax3.set_ylabel('Tcpde [K]')

            self.canvas.draw()
            self.background1 = self.canvas.copy_from_bbox(self.ax1.bbox)  # Save Empty Chart Format as Background
            self.background2 = self.canvas.copy_from_bbox(self.ax2.bbox)  # Save Empty Chart Format as Background
            self.background3 = self.canvas.copy_from_bbox(self.ax3.bbox)  # Save Empty Chart Format as Background

            # plot Pple,o histories
            self.lines1 = self.ax1.plot(self.df.iloc[self.i_left::2, self.index_x],
                                        self.df.iloc[self.i_left::2, self.index_plot1])[0]

            # plot Tth,rde histories
            self.lines2.append(self.ax2.plot(self.df.iloc[self.i_left::2, self.index_x],
                                             self.df.iloc[self.i_left::2, self.index_plot2])[0])

            # plot Tcpde histories
            self.lines3.append(self.ax3.plot(self.df.iloc[self.i_left::2, self.index_x],
                                             self.df.iloc[self.i_left::2, self.index_plot3])[0])

        else:
            # reflesh Pple,o histories plot
            self.lines1.set_data(self.df.iloc[self.i_left::2, self.index_x],
                                           self.df.iloc[self.i_left::2, self.index_plot1])

            # reflesh Tth,rde histories plot
            for i_T_line in range(len(self.lines2)):
                self.lines2[i_T_line].set_data(self.df.iloc[self.i_left::2, self.index_x],
                                               self.df.iloc[self.i_left::2, self.index_plot2])

            # reflesh Tcpde histories plot
            for i_T_line in range(len(self.lines3)):
                self.lines3[i_T_line].set_data(self.df.iloc[self.i_left::2, self.index_x],
                                               self.df.iloc[self.i_left::2, self.index_plot3])

        self.canvas.restore_region(self.background1)                 # Re-plot Background (i.e. Delete line)
        self.canvas.restore_region(self.background2)                 # Re-plot Background (i.e. Delete line)
        self.canvas.restore_region(self.background3)                 # Re-plot Background (i.e. Delete line)

        self.ax1.draw_artist(self.lines1)                              # Set new data in ax

        for line in self.lines2:
            self.ax2.draw_artist(line)                              # Set new data in ax

        for line in self.lines3:
            self.ax3.draw_artist(line)                              # Set new data in ax

        self.fig.canvas.blit(self.ax1.bbox)                          # Plot New data
        self.fig.canvas.blit(self.ax2.bbox)                          # Plot New data
        self.fig.canvas.blit(self.ax3.bbox)                          # Plot New data

    def valueReloader(self, event):
        # update current values
        for i_sensor in range(len(self.df_cfg_tlm['item'])):
            self.SensorValue[i_sensor].SetLabel(str(np.round(self.df.iloc[-1, i_sensor], 2)))

        print('frame counter delay = ' + str(th_smt.df_ui.iloc[-1, 2] - self.df.iloc[-1, 2]))
        print('Time delay from udp [s] = ' + str(time.time() - th_smt.time_ui))
        if self.flag_temp:
            print('Time delay of Reload sensor value [s] = ' + str(time.time() - self.time_sensor))
        self.flag_temp = True
        self.time_sensor = time.time()

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
        flag_temp = False

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
                    if flag_temp:
                        print('Time of DataFrame Reload [s] = ' + str(time.time()-self.time_ui))
                    flag_temp = True
                    self.time_ui = time.time()
                    try:
                        GUI_Frame.chart_panel.df
                    except AttributeError:
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
