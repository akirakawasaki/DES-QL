import wx
import wx.lib
import wx.lib.plot as plot
#Used for graph drawing
import random

#Value to draw
x_val = list(range(10))
y_val = [random.randint(0, 10) for i in range(10)]  # 0~10 random values up to 10

# [(x1, y1), (x2, y2),...(xn, yn)]Transformed to pass to the graph in the format
xy_val = list(zip(x_val, y_val))


class MainFrame(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, size=(500, 500))
        #panel creation
        self.panel = wx.Panel(self, -1)
        
        #graph creation
        self.plotter = plot.PlotCanvas(self, -1)
        self.plotter.enableLegend = True  #Set the legend display to True
        self.plotter.fontSizeTitle = 18  #Set the font size of the graph title to 18.(Default=15)
        self.plotter.fontSizeLegend = 18  #Set the font size of the legend to 18.(Default=7)
        self.plotter.fontSizeAxis = 18  #xy label,Set the font size of the coordinates to 18.(Default=10)

        #Enable the zoom or drag function. Only one can be enabled
        # self.plotter.enableZoom = True
        self.plotter.enableDrag = True

        #Create a line to display&drawing()
        line = plot.PolyLine(xy_val, legend='sample', colour='red', width=4)  
        gc = plot.PlotGraphics([line], 'WxLibPlot', 'xaxis', 'yaxis')  #Graph title and xy label added


        #Create a line to display&drawing
        line = plot.PolyLine(xy_val)
        gc = plot.PlotGraphics([line])
        self.plotter.Draw(gc)
        self.plotter.Refresh()

        #sizer creation&Installation
        sizer = wx.GridSizer(1, 1, gap=(0, 0))
        sizer.Add(self.plotter, flag=wx.EXPAND)
        self.SetSizer(sizer)

        #Display GUI in the center of the screen
        # self.Refresh()
        self.Center()
        self.Show()


def main():
    app = wx.App()
    MainFrame(None, -1, 'WxLibPlot')
    app.MainLoop()


if __name__ == '__main__':
    main()