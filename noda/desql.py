"""
Standard libraries
"""
import decimal
import socket
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
from stl.utils import b
from mpl_toolkits import mplot3d

from PIL import Image, ImageDraw

"""
Local libraries
"""
#n/a


"""
External file path
"""
# configuration
path_cfg_tlm = r'./config_tlm.xlsx'
df_cfg_img = r'./config_img.xlsx'

# image
path_FL = r'./LineFig/DES_FuelLine.bmp'


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
        self.system_panel = SystemPanel(root_panel, reflesh_time_sys)

        # Attitude panel : Show the DES attitude
        self.attitude_panel = AttitudePanel(root_panel, stl_data, data_attitude, reflesh_time_attitude)

        # Set layout of panels
        root_layout = wx.GridBagSizer()
        root_layout.Add(self.chart_panel, pos=wx.GBPosition(0,0), span=wx.GBSpan(2,1), flag=wx.EXPAND | wx.ALL, border=10)
        root_layout.Add(self.system_panel, pos=wx.GBPosition(0,1), flag=wx.EXPAND | wx.ALL, border=10)
        root_layout.Add(self.attitude_panel, pos=wx.GBPosition(1,1), flag=wx.EXPAND | wx.ALL, border=10)

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

    def __init__(self, parent, reflesh_time_graph, reflesh_time_value):
        super().__init__(parent, wx.ID_ANY)

        # load smt data config
        self.df_cfg_plot = th_smt.smt.df_cfg.copy()
        self.df_cfg_plot.reset_index()
        self.p_number = np.array(list(self.df_cfg_plot.query('type == "p"').index))
        self.T_number = np.array(list(self.df_cfg_plot.query('type == "T"').index))

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

    def chartGenerator(self):
        ''' Time history plots '''
        self.fig = Figure(figsize=(6, 4))
        self.ax1 = self.fig.add_subplot(211)
        self.ax2 = self.fig.add_subplot(212)
        self.canvas = FigureCanvasWxAgg(self, -1, self.fig)

        self.ax1.set_ylim([0.0, 1.5])
        self.ax2.set_ylim([200.0, 600.0])

        ''' Current value indicators '''
        self.row_value = 4
        self.col_value = 6

        # generate DataButton instances
        self.DataButton = []
        for index in th_smt.smt.df.columns[self.p_number]:
            self.DataButton.append(wx.ToggleButton(self, wx.ID_ANY, index))
        self.DataButton.append(wx.ToggleButton(self, wx.ID_ANY, 'Pc,rde'))
        self.DataButton.append(wx.ToggleButton(self, wx.ID_ANY, 'Pc,pde'))
        
        for index in th_smt.smt.df.columns[self.T_number]:
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
        self.DataButton[self.p_number[8]-self.p_number[0]].SetValue(True)                       # Pple,o
        self.DataButton[self.T_number[6]-self.T_number[0]+len(self.p_number)+2].SetValue(True)  # Tth,rde
        self.DataButton[self.T_number[7]-self.T_number[0]+len(self.p_number)+2].SetValue(True)  # Tcpde

    def dfReloder(self):
        self.df = th_smt.smt.df.copy()

    def graphReloader(self, event):
        # set axis captions
        self.ax1.cla()
        self.ax1.set_xlabel('Frame No.')
        self.ax1.set_ylabel('p [MPa]')

        self.ax2.cla()
        self.ax2.set_xlabel('Frame No.')
        self.ax2.set_ylabel('T [K]')

        # plot pressure histories
        for i_p in self.p_number:
            if self.DataButton[i_p-self.p_number[0]].GetValue():
                self.ax1.plot(self.df.iloc[-100::20, 2], self.df.iloc[-100::20, i_p], label=self.df.columns[i_p])

        # plot temperature histories
        for i_T in self.T_number:
            if self.DataButton[i_T-self.T_number[0]+len(self.p_number)].GetValue():
                self.ax2.plot(self.df.iloc[-100::20, 2], self.df.iloc[-100::20, i_T], label=self.df.columns[i_T])

        # draw alert line
        self.ax1.axhline(y=1.0, xmin=0, xmax=1, color='red')
        self.ax2.axhline(y=500.0, xmin=0, xmax=1, color='red')

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

        self.ax1.set_ylim([0.0, 1.5])
        self.ax2.set_ylim([200.0, 600.0])

        self.ax1.legend(loc="upper left")
        self.ax2.legend(loc="upper left")

        self.canvas.draw()

    def valueReloader(self, event):
        # update current values
        for i_sensor in self.p_number:
            self.SensorValue[i_sensor-self.p_number[0]].SetLabel(str(np.round(self.df.iloc[-1, i_sensor], 2)))
        self.SensorValue[i_sensor-self.p_number[0]+1].SetLabel('0.10')
        self.SensorValue[i_sensor-self.p_number[0]+2].SetLabel('0.10')
        for i_sensor in self.T_number:
            self.SensorValue[i_sensor-self.T_number[0]+len(self.p_number)+2].SetLabel(str(np.round(self.df.iloc[-1, i_sensor])))

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

    def __init__(self, parent, reflesh_time):
        super().__init__(parent, wx.ID_ANY)

        self.FL_status = pd.Series([True, False, True, False, True, False, True, False, True], index=self.df_FL_config.columns)
        # True : Open
        # False: Close

        self.FuelLine = wx.Bitmap(r'LineFig/FuelLine.bmp')
        self.StaticFL = wx.StaticBitmap(self, wx.ID_ANY, self.FuelLine)

        self.i = 0

        # layout feeding system status pane
        layout = wx.GridSizer(rows=1, cols=1, gap=(0,0))
        layout.Add(self.StaticFL, flag=wx.FIXED_MINSIZE)
        self.SetSizer(layout)

        # set refresh timer
        self.timer_reload = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.SysReloader, self.timer_reload)
        self.timer_reload.Start(reflesh_time)

    def SysReloader(self, event):
        self.i += 1

        self.FL_status = ~self.FL_status
        self.ImgReloader()

        self.FuelLine = wx.Bitmap(r'LineFig/FuelLine_{}.bmp'.format(self.i%2))
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
        img_FL_resize.save(r'LineFig/FuelLine_{}.bmp'.format(self.i%2))

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
        #self.fig.subplots_adjust(bottom=0.07, top=0.97)
        self.ax = mplot3d.Axes3D(self.fig)
        self.canvas = FigureCanvasWxAgg(self, -1, self.fig)

        self.ax.add_collection3d(mplot3d.art3d.Line3DCollection(self.stl.vectors, linewidths=0.05, colors="blue"))

        self.scale = self.stl.points.flatten()
        self.ax.auto_scale_xyz(self.scale+5, self.scale+2, self.scale)

        self.canvas.draw()

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

        self.ax.set_xlabel('x')
        self.ax.set_ylabel('y')
        self.ax.set_zlabel('z')

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
Datagram Handler
"""
class tlm():

    W2B = 2

    NUM_OF_FRAMES = 8

    LEN_HEADER  = 4
    LEN_PAYLOAD = 64

    BUFSIZE = W2B * (LEN_HEADER + LEN_PAYLOAD) * NUM_OF_FRAMES       # 1088 bytes
    #BUFSIZE = 1088
    #BUFSIZE = 1280
    #BUFSIZE = 2176

    '''
    Convert thermoelectric voltage (in uV) to temperature (in K)
    '''
    def uv2k(self, val, type):
        if type != 'K': print('ERROR!')

        # Ref.: NIST Monograph 175
        if val < 0.0:
            c0 = 0.0
            c1 = 2.5173462e-2
            c2 = -1.1662878e-6
            c3 = -1.0833638e-9
            c4 = -8.9773540e-13
            c5 = -3.7342377e-16
            c6 = -8.6632643e-20
            c7 = -1.0450598e-23
            c8 = -5.1920577e-28
            c9 = 0.0
        elif val < 20644.0:
            c0 = 0.0
            c1 = 2.508355e-2
            c2 = 7.860106e-8
            c3 = -2.503131e-10
            c4 = 8.315270e-14
            c5 = -1.228034e-17
            c6 = 9.804036e-22
            c7 = -4.413030e-26
            c8 = 1.057734e-30
            c9 = -1.052755e-35
        else:
            c0 = -1.318058e2
            c1 = 4.830222e-2
            c2 = -1.646031e-6
            c3 = 5.464731e-11
            c4 = -9.650715e-16
            c5 = 8.802193e-21
            c6 = -3.110810e-26
            c7 = 0.0
            c8 = 0.0
            c9 = 0.0

        y =  c0 \
           + c1 * val \
           + c2 * val**2 \
           + c3 * val**3 \
           + c4 * val**4 \
           + c5 * val**5 \
           + c6 * val**6 \
           + c7 * val**7 \
           + c8 * val**8 \
           + c9 * val**9 \
           + 273.15         # convert deg-C to Kelvin

        return y

    '''
    Convert temperature (in K) to thermoelectric voltage (in uV)
    '''
    def k2uv(self, val, type):
        if type != 'K': print('ERROR!')

        val2 = val - 273.15     # convert Kelvin to deg-C

        # Ref.: NIST Monograph 175
        if val2 < 0.0:
            c0 = 0.0
            c1 = 3.9450128025e1
            c2 = 2.3622373598e-2
            c3 = -3.2858906784e-4
            c4 = -4.9904828777e-6
            c5 = -6.7509059173e-8
            c6 = -5.7410327428e-10
            c7 = -3.1088872894e-12
            c8 = -1.0451609365e-14
            c9 = -1.9889266878e-17
            c10 = -1.6322697486e-20
            alp0 = 0.0
            alp1 = 0.0
        else:
            c0 = -1.7600413686e1
            c1 = 3.8921204975e1
            c2 = 1.8558770032e-2
            c3 = -9.9457592874e-5
            c4 = 3.1840945719e-7
            c5 = -5.6072844889e-10
            c6 = 5.6075059059e-13
            c7 = -3.2020720003e-16
            c8 = 9.7151147152e-20
            c9 = -1.2104721275e-23
            c10 = 0.0
            alp0 = 1.185976e2
            alp1 = -1.183432e-4

        y =  c0 \
            + c1 * val2 \
            + c2 * val2**2 \
            + c3 * val2**3 \
            + c4 * val2**4 \
            + c5 * val2**5 \
            + c6 * val2**6 \
            + c7 * val2**7 \
            + c8 * val2**8 \
            + c9 * val2**9 \
            + c10 * val2**10 \
            + alp0 * np.exp(alp1 * (val2 - 126.9686)**2)

        return y

    '''
    Convert thermistor voltage to resistance
    '''
    def v2ohm(self, val):
        # Ref.: Converting NI 9213 Data (FPGA Interface)
        return (1.0e4 * 32 * val) / (2.5 - 32 * val)

    '''
    Convert thermistor resistance to temperature (in K)
    '''
    def ohm2k(self, val):
        if val > 0:
            # Ref.: Converting NI 9213 Data (FPGA Interface)
            a = 1.2873851e-3
            b = 2.3575235e-4
            c = 9.4978060e-8
            y = 1.0 / (a + b * np.log(val) + c * (np.log(val)**3)) - 1.0
        else:
            y = 273.15

        return y

    '''
    Constractor
    '''
    def __init__(self, tlm_type):
        #self.HOST = socket.gethostname()
        self.HOST = ''
        self.TLM_TYPE = tlm_type

        #print(self.TLM_TYPE)
        #print(self.BUFSIZE)

        #self.PORT = 70
        if self.TLM_TYPE == 'smt':
            self.PORT = 49157
            self.DATA_PATH = './data_smt.xlsx'
        elif self.TLM_TYPE == 'pcm':
            self.PORT = 49158
            self.DATA_PATH = './data_pcm.xlsx'
        else:
            print('Error: Type of the telemeter is wrong!')

        #print(self.PORT)

        # create a scoket for UPD/IP communication
        self.udpSoc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # bind a port
        self.udpSoc.bind((self.HOST, self.PORT))

        # load configuration
        if self.TLM_TYPE == 'smt':
            self.df_cfg = pd.read_excel('./config_tlm.xlsx', sheet_name='smt')
        elif self.TLM_TYPE == 'pcm':
            self.df_cfg = pd.read_excel('./config_tlm.xlsx', sheet_name='pcm')

        self.NUM_OF_ITEMS = len(self.df_cfg.index)
        self.SUP_COM      = self.df_cfg['sup com'].max()

        # configure output file
        self.df = pd.DataFrame(index=[], columns=self.df_cfg['item'])

        # initialize data index
        self.iData = 0

    '''
    Destractor
    '''
    def __del__(self):
        self.udpSoc.close()

    def save(self):
        self.df.to_excel(self.DATA_PATH)

    def receive(self):
        #print('tlm.receive called')
        self.data, self.addr = self.udpSoc.recvfrom(self.BUFSIZE)

    def reshape(self):
        # sweep frames in a major frame
        for iFrame in range(self.NUM_OF_FRAMES):
            #print(f"iData: {self.iData}")

            adrs_tmp = iFrame * self.W2B * (self.LEN_HEADER + self.LEN_PAYLOAD)
            #print(f"adrs_tmp: {adrs_tmp}")

            # initialize the row by filling wit NaN
            self.df.loc[self.iData] = np.nan

            # pick up data from the datagram
            '''
            When w assgn < 0
            '''
            # Days from January 1st on GSE
            adrs = adrs_tmp + self.W2B * 0
            self.df.iat[self.iData,0] =  (self.data[adrs]   >> 4  ) * 100 \
                                       + (self.data[adrs]   & 0x0F) * 10  \
                                       + (self.data[adrs+1] >> 4  ) * 1

            # GSE timestamp in [sec]
            adrs = adrs_tmp + self.W2B * 0
            self.df.iat[self.iData,1] =  (self.data[adrs+1] & 0x0F) * 10  * 3600 \
                                       + (self.data[adrs+2] >> 4  ) * 1   * 3600 \
                                       + (self.data[adrs+2] & 0x0F) * 10  * 60   \
                                       + (self.data[adrs+3] >> 4  ) * 1   * 60   \
                                       + (self.data[adrs+3] & 0x0F) * 10         \
                                       + (self.data[adrs+4] >> 4  ) * 1          \
                                       + (self.data[adrs+4] & 0x0F) * 100 / 1000 \
                                       + (self.data[adrs+5] >> 4  ) * 10  / 1000 \
                                       + (self.data[adrs+5] & 0x0F) * 1   / 1000

            '''
            When w assgn >= 0
            '''
            for iItem in range(2, self.NUM_OF_ITEMS):
                # designate byte addres with the datagram
                adrs = adrs_tmp + self.W2B * (self.LEN_HEADER + self.df_cfg.at[iItem,'w assgn'])

                # frame/loop counter
                if self.df_cfg.at[iItem,'type'] == 'counter':
                    self.df.iat[self.iData,iItem] = \
                        int.from_bytes((self.data[adrs], self.data[adrs+1]), byteorder='big', signed=False)
                    #self.df.iat[self.iData,iItem] =  self.data[adrs]   * 2**8 \
                    #                               + self.data[adrs+1]

                # DES timestamp in [sec]
                elif self.df_cfg.at[iItem,'type'] == 'des time':
                    self.df.iat[self.iData,iItem] = \
                        int.from_bytes((self.data[adrs], self.data[adrs+1], self.data[adrs+2], self.data[adrs+3]),
                                        byteorder='big', signed=False) \
                            / 1000.0
                    #self.df.iat[self.iData,iItem] = (  self.data[adrs]   * 2**(24) \
                    #                                 + self.data[adrs+1] * 2**(16) \
                    #                                 + self.data[adrs+2] * 2**(8)  \
                    #                                 + self.data[adrs+3] * 2**(0)  ) / 1000.0

                # pressure in [MPa]
                elif self.df_cfg.at[iItem,'type'] == 'p':
                    self.df.iat[self.iData,iItem] = \
                          self.df_cfg.at[iItem,'coeff a'] / 2**11 \
                            * int.from_bytes((self.data[adrs], self.data[adrs+1]), byteorder='big', signed=True) \
                        + self.df_cfg.at[iItem,'coeff b']

                # temperature in [K]
                elif self.df_cfg.at[iItem,'type'] == 'T':
                    # TC thermoelectric voltage in [uV]
                    Vtc =  self.df_cfg.at[iItem,'coeff a'] / 2**18 * 1e6 \
                            * int.from_bytes((self.data[adrs], self.data[adrs+1]), byteorder='big', signed=True) \
                         + self.df_cfg.at[iItem,'coeff b']
                    Ttc = self.uv2k(Vtc + Vcjc - Vaz, 'K')

                    self.df.iat[self.iData,iItem] = Ttc

                    #print(f"Vtc : {Vtc}")
                    #print(f"Vcjc: {Vcjc}")
                    #print(f"Vaz : {Vaz}")

                # auto-zero coefficient in [uV]
                elif self.df_cfg.at[iItem,'type'] == 'az':
                    Vaz =  self.df_cfg.at[iItem,'coeff a'] / 2**18 * 1e6 \
                            * int.from_bytes((self.data[adrs], self.data[adrs+1]), byteorder='big', signed=True) \
                         + self.df_cfg.at[iItem,'coeff b']

                    self.df.iat[self.iData,iItem] = Vaz

                # cold-junction compensation coefficient in [uV]
                elif self.df_cfg.at[iItem,'type'] == 'cjc':
                    cjc =  self.df_cfg.at[iItem,'coeff a'] / 2**18 \
                            * int.from_bytes((self.data[adrs], self.data[adrs+1]), byteorder='big', signed=True) \
                         + self.df_cfg.at[iItem,'coeff b']
                    Rcjc = self.v2ohm(cjc)
                    Tcjc = self.ohm2k(Rcjc)
                    Vcjc = self.k2uv(Tcjc, 'K')

                    #print(f"CJC : {cjc}")
                    #print(f"Rcjc: {Rcjc}")
                    #print(f"Tcjc: {Tcjc}")
                    #print(f"Vcjc: {Vcjc}")

                    self.df.iat[self.iData,iItem] = Vcjc

                # analog pressure in [MPa]
                elif self.df_cfg.at[iItem,'type'] == 'p ana':
                    if iFrame % self.df_cfg.at[iItem,'sub com mod'] != self.df_cfg.at[iItem,'sub com res']: continue

                    self.df.iat[self.iData,iItem] = \
                          self.df_cfg.at[iItem,'coeff a'] / 2**16 * 5.0 \
                            * int.from_bytes((self.data[adrs],self.data[adrs+1]), byteorder='big', signed=True) \
                        + self.df_cfg.at[iItem,'coeff b']

                # voltage in [V]
                elif self.df_cfg.at[iItem,'type'] == 'V':
                    self.df.iat[self.iData,iItem] = \
                          self.df_cfg.at[iItem,'coeff a'] \
                            * int.from_bytes((self.data[adrs],self.data[adrs+1]), byteorder='big', signed=True) \
                        + self.df_cfg.at[iItem,'coeff b']

                # relay status (boolean)
                elif self.df_cfg.at[iItem,'type'] == 'rel':
                    self.df.iat[self.iData,iItem] = \
                        (self.data[adrs + self.df_cfg.at[iItem,'coeff b']] & int(self.df_cfg.at[iItem,'coeff a'])) \
                            / self.df_cfg.at[iItem,'coeff a']
                    #self.df.iat[self.iData,iItem] = \
                    #   int.from_bytes((self.data[adrs],self.data[adrs+1]), byteorder='big', signed=False)

                # others
                else:
                    self.df.iat[self.iData,iItem] = \
                          self.df_cfg.at[iItem,'coeff a'] \
                            * int.from_bytes((self.data[adrs], self.data[adrs+1]), byteorder='big', signed=False) \
                        + self.df_cfg.at[iItem,'coeff b']

            self.iData += 1

"""
SMT
"""
class smt_thread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        
        # STEP 0: initialize
        self.smt = tlm('smt')
        #self.smt = tlm('pcm')
        #self.pcm = tlm('pcm')

        self.DATA_SAVE_INTERVAL = 500

    def __del__(self):
        ### STEP F: finalize
        del self.smt
        #del self.pcm

    def run(self):
        print('SMT Thread Launched!')

        self.NNN = 1
        while flag_GUI:
            # STEP 1: data receive
            self.smt.receive()

            # STEP 2: data reshape
            self.smt.reshape()

            # STEP 3: data save
            if self.NNN % self.DATA_SAVE_INTERVAL == 0:
                #self.smt.save()
                print('data_smt.xlsx update time : {}'.format(int(self.NNN / self.DATA_SAVE_INTERVAL)))

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
    
    th_pcm = pcm_thread()
    th_pcm.setDaemon(True)

    flag_GUI = True

    th_smt.start()
    th_pcm.start()

    time.sleep(1)
    while True:
        if th_smt.smt.df.empty:
            print("UDP port received no data...")
            time.sleep(2)
        else:
            print("UDP port received data!")
            break

    app = wx.App()
    GUI_Frame = MainWindow(stl_data=stl_original, 
                            data_attitude=df_dummy_att,
                            reflesh_time_chart=1000, 
                            reflesh_time_value=500, 
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









