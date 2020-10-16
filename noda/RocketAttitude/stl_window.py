import numpy as np
from stl import mesh
from mpl_toolkits import mplot3d
import matplotlib.pyplot as plt

import time

save_folder_path = 'C:/Users/notze/Documents/ProgramCode/Python/GUI/wxPython/S_520_31/RocketAttitude/STL_model/'
stl_file_path = 'C:/Users/notze/Documents/ProgramCode/Python/GUI/wxPython/S_520_31/RocketAttitude/STL_model/{}.stl'

class STL_handle():
    def __init__(self):
        self.stl_original = mesh.Mesh.from_file(stl_file_path.format('Rocket_sample'))

        self.stl_original.x -= 2.5
        self.stl_original.y -= 1.37
        self.stl_original.z -= 10.0

        start = time.time()
        self.stl_rotate = self.rotate_stl(self.stl_original, 0., 0., 0.)
        process_time = time.time() - start

        print("Rotating Process Time [ms] = " + str(process_time * 10**3))
        self.plot_stl(self.stl_rotate)

    def create_stl(self, folder_path, file_name):
        # Define the vertices of an object
        self.vertices = np.array([\
                        [3, 0, 0],
                        [0, 3, 0],
                        [0, 0, 0],
                        [0, 0, 3]])

        # Select the three vertices that make up a triangular polygon
        self.faces = np.array([\
                    [0,1,2],
                    [0,1,3],
                    [0,2,3],
                    [1,2,3]])

        # Mesh (object) creation
        self.obj = mesh.Mesh(np.zeros(self.faces.shape[0], dtype=mesh.Mesh.dtype))
        for i, f in enumerate(self.faces):
            for j in range(3):
                self.obj.vectors[i][j] = self.vertices[f[j],:]

        # Save stl file
        self.obj.save(folder_path + file_name)

    def rotate_stl(self, stl, roll, pitch, yaw):
        """
        Rotate stl in the (roll, pitch, yaw) direction
        """
        stl.rotate([1,0,0], np.deg2rad(roll))            # rotate stl model in roll angle
        stl.rotate([0,1,0], np.deg2rad(pitch))           # rotate stl model in pitch angle
        stl.rotate([0,0,1], np.deg2rad(yaw))             # rotate stl model in yaw angle
        return stl

    def plot_stl(self, stl):
        fig = plt.figure()
        ax = mplot3d.Axes3D(fig)

        ax.add_collection3d(mplot3d.art3d.Line3DCollection(stl.vectors, linewidths=0.05, colors="black"))

        scale = stl.points.flatten()
        ax.auto_scale_xyz(scale, scale, scale)

        plt.show()

if __name__ == "__main__":
    R = STL_handle()
