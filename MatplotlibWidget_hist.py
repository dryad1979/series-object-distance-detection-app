# import sys
import matplotlib

matplotlib.use("Qt5Agg")
# from PyQt5.QtWidgets import QApplication, QVBoxLayout, QSizePolicy, QWidget
from PyQt5.QtWidgets import QVBoxLayout, QSizePolicy, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib import cycler, rcParams
from matplotlib.figure import Figure

import numpy as np


class MyMplCanvas(FigureCanvas):
    """FigureCanvas的最終的父類其實是QWidget。"""

    def __init__(self, parent=None):
        # Set the default color cycle
        rcParams['axes.prop_cycle'] = cycler(color=["#326186", "#28502E", "#F6BA42", "#A30B37", "#F26419",
                                                    "#196157", "#70B8FF"]) 
        font = {'family' : 'Calibri',
                'size'   : 10}
        matplotlib.rc('font', **font)
        # rcParams.update({'font.size': 10})

        # Create a new figure
        self.fig = Figure(tight_layout=True)
        self.ax_1 = self.fig.add_subplot(121)
        self.ax_2 = self.fig.add_subplot(222)
        self.ax_3 = self.fig.add_subplot(224)
        
        self.ax_1.set_title('Swing range distribution', fontsize=12)
        self.ax_1.set_xlabel('Swing range (mm)')
        self.ax_1.set_ylabel('Count')
        self.ax_2.set_title('Swing overlap of the first 20% sheets', fontsize=12)
        self.ax_2.set_xlabel('Time (0.1 s)')
        self.ax_2.set_ylabel('Distance (mm)')
        self.ax_3.set_title('Swing overlap of the last 20% sheets', fontsize=12)
        self.ax_3.set_xlabel('Time (0.1 s)')
        self.ax_3.set_ylabel('Distance (mm)')

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        '''
		定義FigureCanvas的尺寸策略，意思是設定FigureCanvas，使之盡可能地向外填充空間。
		'''
        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        # FigureCanvas.updateGeometry(self)
        

    def plot_hist(self, x):
        self.ax_1.cla()
        start=2.5*(x.min()//2.5)
        self.ax_1.hist(x, bins=np.arange(start, x.max() + 2.5, 2.5))
        self.ax_1.set_title('Swing range distribution', fontsize=12)
        self.ax_1.set_xlabel('Swing range (mm)')
        self.ax_1.set_ylabel('Count')
        self.ax_1.grid(True)
        self.draw()
        
    def plot_swing(self, overlap, ind_first20, ind_last20):
        self.ax_2.cla()
        self.ax_2.plot(overlap[:, ind_first20], lw = 1)
        self.ax_2.set_xlim(xmin=0)
        self.ax_2.set_title('Swing overlap of the first 20% sheets', fontsize=12)
        self.ax_2.set_xlabel('Time (0.1 s)')
        self.ax_2.set_ylabel('Distance (mm)')
        self.ax_2.grid(True)
        
        self.ax_3.cla()
        self.ax_3.plot(overlap[:, ind_last20], lw = 1)
        self.ax_3.set_xlim(self.ax_2.get_xlim())
        self.ax_3.set_ylim(self.ax_2.get_ylim())
        self.ax_3.set_title('Swing overlap of the last 20% sheets', fontsize=12)
        self.ax_3.set_xlabel('Time (0.1 s)')
        self.ax_3.set_ylabel('Distance (mm)')
        self.ax_3.grid(True)
        self.draw()


class MatplotlibWidget_hist(QWidget):
    def __init__(self, parent=None):
        super(MatplotlibWidget_hist, self).__init__(parent)
        self.initUi()

    def initUi(self):
        self.layout = QVBoxLayout(self)
        self.mpl = MyMplCanvas(self)
        self.mpl_ntb = NavigationToolbar(self.mpl, self)  # 增加完整的 toolbar

        self.layout.addWidget(self.mpl)
        self.layout.addWidget(self.mpl_ntb) #排列toolbar


# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     ui = MatplotlibWidget_hist()
#     ui.mpl.plot_hist()  # 測試靜態圖效果
#     ui.show()
#     sys.exit(app.exec_())
