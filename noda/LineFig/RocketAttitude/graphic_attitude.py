# edit by kazama tomoya 3/2/2020

import numpy as np                                                                                              # pip install numpy
from stl import mesh                                                                                            # pip install numpy-stl
from mpl_toolkits import mplot3d                                                                                # pip install matplotlib
import matplotlib.pyplot as plt
import math

###################################################################################################################################################################################################

def graph(t,stl):                                                                                               # define function for creating graph
    figure = plt.figure(figsize=(8,8),dpi=300)                                                                  # figure size and other config
    axes = mplot3d.Axes3D(figure)                                                                               # create 3D graph space
    axes.set_xlim(-2000,2000)                                                                                   # x-axis scalse range
    axes.set_ylim(-2000,2000)                                                                                   # y-axis scalse range
    axes.set_zlim(-2000,2000)                                                                                   # z-axis scalse range
    axes.add_collection3d(mplot3d.art3d.Line3DCollection(stl.vectors,linewidths=0.05,colors="black"))           # add 3D collection object to plot space (you can use Poly3DCollection, Path3DCollection and Line3DCollection)    add_collection3d(https://matplotlib.org/mpl_toolkits/mplot3d/api.html)  art3d(https://matplotlib.org/api/_as_gen/mpl_toolkits.mplot3d.art3d.Poly3DCollection.html)
    axes.set_title("Time = " + str(t) + " (sec)",loc='center',y=1)                                              # setting graph title
    plt.savefig("./gif/TIME-" + str(t) + ".png")                                                                # save graph
    plt.close(figure)                                                                                           # delete all information for graph

def stl_rotate(stl,roll,pitch,yaw):                                                                             # define function for rotation
    stl.z -= 473                                                                                                # z-axis transition
    stl.rotate([1,0,0],math.radians(roll))                                                                      # rotate stl model in roll angle
    stl.rotate([0,1,0],math.radians(pitch))                                                                     # rotate stl model in pitch angle
    stl.rotate([0,0,1],math.radians(yaw))                                                                       # rotate stl model in yaw angle
    return stl                                                                                                  # return of function

def stl_initialize(stl):                                                                                        # define function for initializing stl attitude
    stl = mesh.Mesh.from_file("./STL_model/Model.stl")                                                          # reimport stl model to stl
    return stl                                                                                                  # return of function

###################################################################################################################################################################################################

stl_data = mesh.Mesh.from_file('./STL_model/Model.stl')                                                         # import CAD model to stl_data

filename = "./sensor_data/sample.csv"
val      = np.loadtxt(filename,dtype="double",delimiter=",")                                                    # importing sensor data file

time     = val[:,0]                                                                                             # separate sensor data to time
roll     = val[:,1]                                                                                             # separate sensor data to roll angle (Integral value)
pitch    = val[:,2]                                                                                             # separate sensor data to pitch angle (Integral value)
yaw      = val[:,3]                                                                                             # separate sensor data to yaw angle (Integral value)

ex_time  = []                                                                                                   # define list for output time
N = len(time)                                                                                                   # number of arrays
"""
for i in range(N):
    ex_time.append(int(round(time[i]*100,3)))
"""                                                                   # change from 'float(double)' type to 'int' type
ex_time = [int(round(time[i]*100,3)) for i in range(N)]                                                       # this syntax is faster than upper

###################################################################################################################################################################################################

for i in range(N):
    pro_bar = ('#' * int((i+1)/N*10)) + ('-' * int(10-(i+1)/N*10))                                              # separate all step to 10 num for progress bar
    print('\rDoing now ... [' + pro_bar + ']' + str(round(i/N*100,1)) +
    ' % , Time = ' + str(round(time[i],1)) + ' sec', end='')                                                    # print progress bar
    if ex_time[i] % 10 == 0 :                                                                                   # set output delta time
        stl_data = stl_initialize(stl_data)                                                                     # initialize stl data
        stl_data = stl_rotate(stl_data,roll[i],pitch[i],yaw[i])                                                 # rotate stl data
        graph(time[i],stl_data)                                                                                 # graph create


print("##############     Congratulation!!     ##############")

###################################################################################################################################################################################################
