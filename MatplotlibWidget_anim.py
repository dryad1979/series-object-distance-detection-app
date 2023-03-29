# import sys
import matplotlib

matplotlib.use("Qt5Agg")
# from PyQt5.QtWidgets import QApplication, QVBoxLayout, QSizePolicy, QWidget
from PyQt5.QtWidgets import QVBoxLayout, QSizePolicy, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

import matplotlib.animation as animation
import matplotlib.dates as mdates
from datetime import timedelta

class MyMplCanvas(FigureCanvas):
    """FigureCanvas的最終的父類其實是QWidget。"""

    def __init__(self, parent=None):

        self.fig = Figure()     # 新建一個figure
        self.ax = self.fig.add_subplot(111)  # 建立一個子圖，如果要建立複合圖，可以在這裡修改
        self.fig.subplots_adjust(right=0.95, bottom=0.15) 

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        '''
		定義FigureCanvas的尺寸策略，意思是設定FigureCanvas，使之盡可能地向外填充空間。
		'''
        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        # FigureCanvas.updateGeometry(self)
        
        # Store x and y
        self.x = []
        self.y = []
        
        # Store a figure and ax
        self.line, = self.ax.plot(self.x, self.y)
        self.ax.grid(True)
        self.fig.suptitle('Distance change over time', fontsize=12)
        self.ax.set_xlabel('Time')
        self.ax.set_ylabel('Distance (mm)')
        self.ax.tick_params(axis='x', labelrotation = 30)
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        
        # Call superclass constructors
        self.anim = animation.FuncAnimation(self.fig, self.animate, init_func=self.plot_init, 
                                            interval=200, blit=False)
        self.paused = True

    def plot_init(self):
        self.ax.set_ylim(ymin=200, ymax=700)
        return self.line,

    def animate(self, i):
        if i==0:
            self.anim.pause()
            return self.line,
        self.line.set_xdata(self.x)
        self.line.set_ydata(self.y)
        try:
            self.ax.set_xlim(xmin=self.x[-1]-timedelta(minutes=1),xmax=self.x[-1])
        except IndexError:
            pass
        return self.line,
        
    def update_line_data(self, x, y):
        self.x.append(x)
        self.x = self.x[-1000:]
        self.y.append(y)
        self.y = self.y[-1000:]
    
    def toggle_pause(self, *args, **kwargs):
        if self.paused:
            self.anim.resume()
        else:
            self.anim.pause()
        self.paused = not self.paused
        
    def plot_clear(self):
        self.x = []
        self.y = []
        self.line.set_xdata(self.x)
        self.line.set_ydata(self.y)
        self.draw()


class MatplotlibWidget_anim(QWidget):
    def __init__(self, parent=None):
        super(MatplotlibWidget_anim, self).__init__(parent)
        self.initUi()

    def initUi(self):
        self.mpl = MyMplCanvas(self)
        self.mpl_ntb = NavigationToolbar(self.mpl, self)  # 增加完整的 toolbar
        
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.mpl)
        self.layout.addWidget(self.mpl_ntb) #排列toolbar


# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     ui = MatplotlibWidget_anim()
#     ui.show()
#     sys.exit(app.exec_())
