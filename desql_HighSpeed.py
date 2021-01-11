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

from PIL import Image, ImageDraw

"""
Local libraries
"""
from usrmod import tlm


"""
External file path
"""
# configuration
path_cfg_tlm = r'./config_tlm.xlsx'
df_cfg_img = r'./config_img.xlsx'

# image
path_FL = r'./LineFig/DES_Line/DES_FuelLine.bmp'
path_OL = r'./LineFig/DES_Line/DES_OxidizerLine.bmp'
path_NL = r'./LineFig/DES_Line/DES_N2Line.bmp'
path_output = r'./LineFig/output/'


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
Dummy Data
"""
stl_file_path = r'./RocketAttitude/STL_model/{}.stl'
dummy_csv_att = r'./RocketAttitude/sensor_data/sample.csv'
index_dummy_att = ['t', 'roll', 'pitch', 'yaw']


"""
Top Level Window Class
"""
class MainWindow(wx.Frame):
    def __init__(self, stl_data, data_attitude,
                 reflesh_time_chart, reflesh_time_value, reflesh_time_sys, reflesh_time_attitude):

        super().__init__(None, wx.ID_ANY, 'Rocket System Information App')

        self.Maximize(True)     # Maxmize GUI window size

        #self.SetBackgroundColour('Dark Grey')
        self.SetBackgroundColour('Black')

        # Setting Status Bar
        #self.CreateStatusBar()
        #self.SetStatusText('Function Correctly.')

        # Setting Menu Bar
        #self.SetMenuBar(AppMenu())

        # Making Main Graphic
        root_panel = wx.Panel(self, wx.ID_ANY)

        # Chart panel : Show time history plots and current value indicators
        self.chart_panel = ChartPanel(root_panel, reflesh_time_chart, reflesh_time_value)

        # System panel : Show the feeding system status
        #self.system_panel = SystemPanel(root_panel, reflesh_time_sys)

        # Attitude panel : Show the DES attitude
        #self.attitude_panel = AttitudePanel(root_panel, stl_data, data_attitude, reflesh_time_attitude)

        # Set layout of panels
        root_layout = wx.GridBagSizer()
        root_layout.Add(self.chart_panel, pos=wx.GBPosition(0,0), span=wx.GBSpan(2,1), flag=wx.EXPAND | wx.ALL, border=10)
        #root_layout.Add(self.system_panel, pos=wx.GBPosition(0,1), flag=wx.EXPAND | wx.ALL, border=10)
        #root_layout.Add(self.attitude_panel, pos=wx.GBPosition(1,1), flag=wx.EXPAND | wx.ALL, border=10)

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
Menu Bar
"""
class AppMenu(wx.MenuBar):
    def __init__(self):
        super().__init__()

        menu_file = wx.Menu()
        menu_file.Append(1, 'Open')
        menu_file.Append(2, 'Save')
        menu_file.Append(3, 'Exit')
        self.Append(menu_file, 'File')

        menu_edit = wx.Menu()
        menu_edit.Append(4, 'Reload')
        menu_edit.Append(5, 'Delete')
        self.Append(menu_edit, 'Edit')

        self.Bind(wx.EVT_MENU, self.onExit)

    def onExit(self, event):
        event_id = event.GetId()
        if event_id == 3:
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
    n_time = 3
    index_x = 1
    index_plot1 = 11   # Pple,o(8+3)
    index_plot2 = 2  # Tth,rde(18+3)
    index_plot3 = 22  # Tcpde(19+3)
    t_range = 20

    def __init__(self, parent, reflesh_time_graph, reflesh_time_value):
        super().__init__(parent, wx.ID_ANY)

        self.configReader()

        self.valueGenerator()

        self.chartGenerator()

        # layout time history pane
        layout = wx.FlexGridSizer(rows=2, cols=1, gap=(0, 20))
        layout.Add(self.canvas, flag=wx.EXPAND)
        layout.Add(self.layout_Data)
        self.SetSizer(layout)

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
        self.df_cfg_plot = th_smt.smt.df_cfg.copy()
        self.df_cfg_plot.reset_index()
        self.p_number = np.array(list(self.df_cfg_plot.query('type == "p"').index))
        self.T_number = np.array(list(self.df_cfg_plot.query('type == "T"').index))

    def chartGenerator(self):
        ''' Time history plots '''
        self.fig = Figure(figsize=(6, 4))
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
        self.row_value = 4
        self.col_value = 6

        # generate DataButton instances
        self.DataButton = []
        for index in th_smt.smt.df_mf.columns[self.p_number]:
            self.DataButton.append(wx.ToggleButton(self, wx.ID_ANY, index))
        self.DataButton.append(wx.ToggleButton(self, wx.ID_ANY, 'Pc,rde'))
        self.DataButton.append(wx.ToggleButton(self, wx.ID_ANY, 'Pc,pde'))

        for index in th_smt.smt.df_mf.columns[self.T_number]:
            self.DataButton.append(wx.ToggleButton(self, wx.ID_ANY, index))
        self.DataButton.append(wx.ToggleButton(self, wx.ID_ANY, 'n/a'))
        self.DataButton.append(wx.ToggleButton(self, wx.ID_ANY, 'n/a'))

        # set presentation of values
        self.SensorValue = []
        for i in range(self.row_value * self.col_value):
            self.SensorValue.append(wx.StaticText(self, wx.ID_ANY, str(i+1), style=wx.ALIGN_CENTRE | wx.ST_NO_AUTORESIZE))
            self.SensorValue[-1].SetBackgroundColour('BLACK')
            self.SensorValue[-1].SetForegroundColour('GREEN')
            #self.SensorValue[-1].SetFont(self.font)

        # layout current value pane
        self.layout_Data = wx.GridSizer(rows=self.row_value*2, cols=self.col_value, gap=(10,5))
        for k in range(self.row_value):
            for l in range(self.col_value):
                self.layout_Data.Add(self.DataButton[self.col_value*k+l], flag=wx.EXPAND)
            for n in range(self.col_value):
                self.layout_Data.Add(self.SensorValue[self.col_value*k+n], flag=wx.EXPAND)

        # enable plots by activating buttons
        self.DataButton[self.p_number[8]-self.p_number[0]].SetValue(True)                       # Pple,o(8)
        self.DataButton[self.T_number[6]-self.T_number[0]+len(self.p_number)+2].SetValue(True)  # Tth,rde(18)
        self.DataButton[self.T_number[7]-self.T_number[0]+len(self.p_number)+2].SetValue(True)  # Tcpde(19)

    def dfReloder(self):
        self.df = th_smt.df_ui.copy()

    def graphReloader(self, event):
        t_temp = self.df.iloc[-1, self.index_x]
        print(t_temp)

        # Alert of Pple,o (Threshold : 1.0 MPa)
        #if self.df.iloc[-1, self.p_number[8]] > 1.0:
        #    self.ax1.set_facecolor('red')
        #else:
        #    self.ax1.set_facecolor('black')

        # Alert of Tth,rde (Threshold : 500 K)
        #if self.df.iloc[-1, self.T_number[6]] > 500:
        #    self.ax2.set_facecolor('red')
        #else:
        #    self.ax2.set_facecolor('black')

        # Alert of Tc,pde (Threshold : 500 K)
        #if self.df.iloc[-1, self.T_number[7]] > 500:
        #    self.ax2.set_facecolor('red')
        #else:
        #    self.ax2.set_facecolor('black')

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
            self.lines1.append(self.ax1.plot(self.df.iloc[self.i_left::2, self.index_x],
                                             self.df.iloc[self.i_left::2, self.index_plot1])[0])

            # plot Tth,rde histories
            self.lines2.append(self.ax2.plot(self.df.iloc[self.i_left::2, self.index_x],
                                             self.df.iloc[self.i_left::2, self.index_plot2])[0])

            # plot Tcpde histories
            self.lines3.append(self.ax3.plot(self.df.iloc[self.i_left::2, self.index_x],
                                             self.df.iloc[self.i_left::2, self.index_plot3])[0])

        else:
            # reflesh Pple,o histories plot
            for i_p_line in range(len(self.lines1)):
                self.lines1[i_p_line].set_data(self.df.iloc[self.i_left::2, self.index_x],
                                               self.df.iloc[self.i_left::2, self.index_plot1])

            # reflesh Tth,rde histories plot
            for i_T_line in range(len(self.lines2)):
                self.lines2[i_T_line].set_data(self.df.iloc[self.i_left::2, self.index_x],
                                               self.df.iloc[self.i_left::2, self.index_plot2])
            
            # reflesh Tcpde histories plot
            for i_T_line in range(len(self.lines2)):
                self.lines3[i_T_line].set_data(self.df.iloc[self.i_left::2, self.index_x],
                                               self.df.iloc[self.i_left::2, self.index_plot3])

        self.canvas.restore_region(self.background1)                 # Re-plot Background (i.e. Delete line)
        self.canvas.restore_region(self.background2)                 # Re-plot Background (i.e. Delete line)
        self.canvas.restore_region(self.background3)                 # Re-plot Background (i.e. Delete line)

        for line in self.lines1:
            self.ax1.draw_artist(line)                              # Set new data in ax

        for line in self.lines2:
            self.ax2.draw_artist(line)                              # Set new data in ax

        for line in self.lines3:
            self.ax3.draw_artist(line)                              # Set new data in ax

        self.fig.canvas.blit(self.ax1.bbox)                          # Plot New data
        self.fig.canvas.blit(self.ax2.bbox)                          # Plot New data
        self.fig.canvas.blit(self.ax3.bbox)                          # Plot New data

    def valueReloader(self, event):
        # update current values
        for i_sensor in self.p_number:
            self.SensorValue[i_sensor-self.p_number[0]].SetLabel(str(np.round(self.df.iloc[-1, i_sensor], 2)))
        self.SensorValue[i_sensor-self.p_number[0]+1].SetLabel('0.10')
        self.SensorValue[i_sensor-self.p_number[0]+2].SetLabel('0.10')
        for i_sensor in self.T_number:
            self.SensorValue[i_sensor-self.T_number[0]+len(self.p_number)+2].SetLabel(str(int(self.df.iloc[-1, i_sensor])))
            #self.SensorValue[i_sensor-self.T_number[0]+len(self.p_number)+2].SetLabel(str(np.round(self.df.iloc[-1, i_sensor])))

        # Alert Pple,o (Threshold : 1.0 MPa)
        if self.df.iloc[-1, self.p_number[8]] > 1.0:
            self.SensorValue[self.p_number[8]-self.p_number[0]].SetForegroundColour('RED')
        else:
            self.SensorValue[self.p_number[8]-self.p_number[0]].SetForegroundColour('GREEN')

        # Alert Tth,rde (Threshold : 500 K)
        if self.df.iloc[-1, self.T_number[6]] > 500.0:
            self.SensorValue[self.T_number[6]-self.T_number[0]+len(self.p_number)].SetForegroundColour('RED')
        else:
            self.SensorValue[self.T_number[6]-self.T_number[0]+len(self.p_number)].SetForegroundColour('GREEN')

        # Alert Tc,pde (Threshold : 500 K)
        if self.df.iloc[-1, self.T_number[7]] > 500.0:
            self.SensorValue[self.T_number[7]-self.T_number[0]+len(self.p_number)].SetForegroundColour('RED')
        else:
            self.SensorValue[self.T_number[7]-self.T_number[0]+len(self.p_number)].SetForegroundColour('GREEN')


"""
Feeding System Status Display
"""
class SystemPanel(wx.Panel):
    img_FL_original = Image.open(path_FL)
    img_FL = img_FL_original.convert('RGB')

    img_blue = Image.new("RGB", img_FL.size, (0, 0, 255))
    img_red = Image.new("RGB", img_FL.size, (255, 0, 0))

    # Mask config
    flame_width = np.array([6, 6])
    flame_size = np.array([55, 70])

    # valve positions on image
    df_FL_config = pd.read_excel(df_cfg_img, sheet_name='Fuel', header=0, index_col=0)
    df_OL_config = pd.read_excel(df_cfg_img, sheet_name='Oxidizer', header=0, index_col=0)
    df_NL_config = pd.read_excel(df_cfg_img, sheet_name='N2', header=0, index_col=0)

    def __init__(self, parent, reflesh_time):
        super().__init__(parent, wx.ID_ANY)

        self.FL_status = pd.Series([True, False, True, False, True, False, True, False], index=self.df_FL_config.columns)
        # True : Open
        # False: Close

        self.FuelLine = wx.Bitmap(path_FL)
        self.StaticFL = wx.StaticBitmap(self, wx.ID_ANY, self.FuelLine)
        """
        self.OxidizerLine = wx.Bitmap(path_OL)
        self.StaticOL = wx.StaticBitmap(self, wx.ID_ANY, self.OxidizerLine)
        self.N2Line = wx.Bitmap(path_NL)
        self.StaticNL = wx.StaticBitmap(self, wx.ID_ANY, self.N2Line)
        """

        self.i = 0

        # layout feeding system status pane
        layout = wx.GridSizer(rows=1, cols=1, gap=(0,0))
        layout.Add(self.StaticFL, flag=wx.FIXED_MINSIZE)
        """
        layout.Add(self.StaticNL, flag=wx.FIXED_MINSIZE)
        layout.Add(self.StaticOL, flag=wx.FIXED_MINSIZE)
        """
        self.SetSizer(layout)

        # set refresh timer
        self.timer_reload = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.SysReloader, self.timer_reload)
        self.timer_reload.Start(reflesh_time)

    def SysReloader(self, event):
        self.i += 1

        self.FL_status = ~self.FL_status
        self.ImgReloader()

        self.FuelLine = wx.Bitmap(path_output + 'FuelLine_{}.bmp'.format(self.i%2))
        self.StaticFL.SetBitmap(self.FuelLine)

    def ImgReloader(self):
        mask_img_blue = Image.new('L', self.img_FL.size, 0)
        draw = ImageDraw.Draw(mask_img_blue)
        for Valve_FL in self.df_FL_config.loc[:, self.FL_status].columns:
            draw.rectangle(self.flame_func(self.df_FL_config[Valve_FL], self.flame_size), fill=255)
            draw.rectangle(self.flame_func(self.df_FL_config[Valve_FL]+self.flame_width, self.flame_size-self.flame_width*2), fill=0)
        self.img_FL.paste(self.img_blue, (0,0), mask_img_blue)

        mask_img_red = Image.new('L', self.img_FL.size, 0)
        draw = ImageDraw.Draw(mask_img_red)
        for Valve_FL in self.df_FL_config.loc[:, ~self.FL_status].columns:
            draw.rectangle(self.flame_func(self.df_FL_config[Valve_FL], self.flame_size), fill=255)
            draw.rectangle(self.flame_func(self.df_FL_config[Valve_FL]+self.flame_width, self.flame_size-self.flame_width*2), fill=0)
        self.img_FL.paste(self.img_red, (0,0), mask_img_red)

        img_FL_resize = self.img_FL.resize((int(self.img_FL.width/1.5), int(self.img_FL.height/1.5)))
        img_FL_resize.save(path_output + 'FuelLine_{}.bmp'.format(self.i%2))

    def flame_func(self, position, size):
        top_left_x = position[0]
        top_left_y = position[1]
        bottom_right_x = position[0] + size[0]
        bottom_right_y = position[1] + size[1]

        return (top_left_x, top_left_y, bottom_right_x, bottom_right_y)

"""
DES Attitude Panel
"""
class AttitudePanel(wx.Panel):
    def __init__(self, parent, stl, data, reflesh_time):
        super().__init__(parent, wx.ID_ANY)

        self.stl = stl
        self.stl.x -= 2.5
        self.stl.y -= 1.37
        self.stl.z -= 10.0

        self.df = data

        self.i = 0

        self.chartGenerator()

        layout = wx.GridSizer(rows=1, cols=1, gap=(0, 0))

        layout.Add(self.canvas, flag=wx.FIXED_MINSIZE)

        self.SetSizer(layout)

        self.timer_reload = wx.Timer(self)

        self.Bind(wx.EVT_TIMER, self.graphReloader, self.timer_reload)
        self.timer_reload.Start(reflesh_time)

    def chartGenerator(self):
        """ Generate data for Real time plot test """
        self.fig = Figure(figsize=(3, 3))
        self.ax = mplot3d.Axes3D(self.fig)
        self.canvas = FigureCanvasWxAgg(self, -1, self.fig)

        self.line0 = mplot3d.art3d.Line3DCollection(self.stl.vectors, linewidths=0.05, colors="blue")
        self.ax.add_collection3d(self.line0)

        self.scale = self.stl.points.flatten()
        self.ax.auto_scale_xyz(self.scale+5, self.scale+2, self.scale)

        self.ax.grid(False)
        self.ax.set_axis_off()

        self.canvas.draw()

        self.background = self.canvas.copy_from_bbox(self.ax.bbox)  # Save Empty Chart Format as Background

    def graphReloader(self, event):
        self.i += 1

        if self.i > len(self.df):
            sys.exit()

        self.stl_rotate = self.rotate_stl(stl=self.stl,
                                          roll=self.df.iat[self.i, 1],
                                          pitch=self.df.iat[self.i, 2],
                                          yaw=self.df.iat[self.i, 3])

        # Clear the current axes
        self.ax.cla()

        self.ax.grid(False)
        self.ax.set_axis_off()

        self.ax.add_collection3d(mplot3d.art3d.Line3DCollection(self.stl_rotate.vectors, linewidths=0.05, colors="blue"))

        self.ax.auto_scale_xyz(self.scale+5, self.scale+2, self.scale)

        self.canvas.draw()

    def rotate_stl(self, stl, roll, pitch, yaw):
        """
        Rotate stl in the (roll, pitch, yaw) direction
        """
        stl.rotate([1,0,0], np.deg2rad(roll))            # rotate stl model in roll angle
        stl.rotate([0,1,0], np.deg2rad(pitch))           # rotate stl model in pitch angle
        stl.rotate([0,0,1], np.deg2rad(yaw))             # rotate stl model in yaw angle
        return stl


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
            self.smt.append_to_file()

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
                    except AttributeError:
                        GUI_Frame.chart_panel.dfReloder()
                    else:
                        wx.CallAfter(GUI_Frame.chart_panel.dfReloder)
                    print('Plot DataFrame reloded')

            # incliment counter
            self.NNN += 1

        if self.NNN == 1:   print('Error : UDP program stopped')


"""
PCM
"""
class pcm_thread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

        # STEP 0: initialize
        #self.smt = tlm('smt')
        self.smt = tlm('pcm')
        #self.pcm = tlm('pcm')

        self.DATA_SAVE_INTERVAL = 500

    def __del__(self):
        ### STEP F: finalize
        del self.smt
        #del self.pcm

    def run(self):
        print('PCM Thread Launched!')

        self.NNN = 1
        while flag_GUI:
            # STEP 1: data receive
            self.smt.receive()

            # STEP 2: data reshape
            self.smt.reshape()

            # STEP 3: data save
            if self.NNN % self.DATA_SAVE_INTERVAL == 0:
                #self.smt.save()
                print('data_pcm.xlsx update time : {}'.format(int(self.NNN / self.DATA_SAVE_INTERVAL)))

            # STEP 4: data display
            try:
                GUI_Frame
            except NameError:
                if self.NNN % 50 == 0:  print('Generating GUI ...')
                pass
            else:
                if self.NNN % 50 == 0:
                    try:
                        GUI_Frame.chart_panel.df
                    except AttributeError:
                        GUI_Frame.chart_panel.dfReloder()
                    else:
                        wx.CallAfter(GUI_Frame.chart_panel.dfReloder)
                    print('Plot DataFrame reloded')

            # incliment counter
            self.NNN += 1

        if self.NNN == 1:   print('Error : UDP program stopped')


if __name__ == "__main__":
    print('DES QL Launched!')

    stl_original = mesh.Mesh.from_file(stl_file_path.format('Rocket_sample'))
    df_dummy_att = pd.read_csv(dummy_csv_att, header=None)

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
    GUI_Frame = MainWindow(stl_data=stl_original,
                            data_attitude=df_dummy_att,
                            reflesh_time_chart=1000,
                            reflesh_time_value=600,
                            reflesh_time_sys=10000,
                            reflesh_time_attitude=30000)
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
