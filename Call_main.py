# coding: utf-8

import sys
from PyQt5.QtCore import pyqtSignal, QSettings, QThread, QTimer
from PyQt5.QtWidgets import QApplication, QFileDialog, QMainWindow, QMessageBox, QTabBar, QWidget
from swing_mainWindow import Ui_MainWindow
import sheet_swing_calculation as ssc

import logging
from logging.handlers import TimedRotatingFileHandler
import traceback
import os
import re
import serial
import serial.tools.list_ports
from datetime import datetime, timedelta


def setupLogger():
    # Produce formater first
    formatter = logging.Formatter('%(asctime)s - line:%(lineno)s - %(levelname)s - %(message)s')
    # Setup Handler
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(formatter)
    # Setup File Handler
    if not os.path.exists('./log/'):
        os.makedirs('./log/')
    filename = './log/Swing Detection.log'
    timedfile = TimedRotatingFileHandler(filename=filename, 
                                         when='midnight', backupCount=60, 
                                         encoding='utf-8')
    timedfile.suffix = "%Y-%m-%d.log"
    timedfile.extMatch = re.compile(r"^\d{4}-\d{2}-\d{2}.log$")
    timedfile.setLevel(logging.DEBUG)
    timedfile.setFormatter(formatter)
    # Setup Logger
    logger.handlers.clear()
    logger.addHandler(console)
    logger.addHandler(timedfile)
    logger.setLevel(logging.DEBUG)

# Call the logger
logger = logging.getLogger(__name__)

class TabBar(QTabBar):
    def sizeHint(self):
        hint = super().sizeHint()
        if self.isVisible() and self.parent():
            if not self.shape() & self.RoundedEast:
                # horizontal
                hint.setWidth(self.parent().width())
            else:
                # vertical
                hint.setHeight(self.parent().height())
        return hint

    def tabSizeHint(self, index):
        hint = super().tabSizeHint(index)
        if not self.shape() & self.RoundedEast:
            hint.setHeight(50)
            averageSize = int(self.width() / self.count())
            if super().sizeHint().width() < self.width() and hint.width() < averageSize:
                hint.setWidth(averageSize)
        else:
            hint.setWidth(50)
            averageSize = self.height() / self.count()
            if super().sizeHint().height() < self.height() and hint.height() < averageSize:
                hint.setHeight(averageSize)
        return hint


class SerialThread(QThread):
    signal_ser_raw = pyqtSignal(str, datetime)
    signal_ser_empty = pyqtSignal()
    signal_ser_status = pyqtSignal()
    def __init__(self,myWin,parent=None):
        super(SerialThread,self).__init__(parent)
        self.myWin=myWin
        self.active=False

    def run(self):
        logger.info('Start moniroting thread')
        #parameter setting
        self.active=True
        while self.active:
            # read data from serial port
            try:
                raw_data=self.myWin.ser.readline().decode().strip()
                raw_time = datetime.now()
                if not len(raw_data):
                    self.signal_ser_empty.emit()
                else:
                    self.signal_ser_raw.emit(raw_data, raw_time)
            except UnicodeDecodeError:
                logger.error(f'{traceback.format_exc()}')
            except Exception:
                logger.error(f'{traceback.format_exc()}')
                self.active=False
                continue
            # print(raw_time)
            # print(raw_data)
        logger.info('Stop moniroting thread')
        self.signal_ser_status.emit()
        
    def exit(self):
        self.active=False

class MyMainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MyMainWindow, self).__init__(parent)
        self.setupUi(self)
        self.setup_control()
        
    # to do or start up
    def setup_control(self):
        # setup logger
        setupLogger()
        logger.debug('Begin of application: Swing Detection')
        # set main window's title
        self.setWindowTitle('Swing Detection v1.3')
        # set up tab
        self.tabBar=TabBar(self.tabWidget)
        self.tabWidget.setTabBar(self.tabBar)
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tabWidget.addTab(self.tab1, "Real-Time Record")
        self.tabWidget.addTab(self.tab2, "History Data Analysis")
        self.tabWidget.setStyleSheet('QTabBar { font-size: 14pt; font-family: Gill Sans; }')
        # get COM ports list
        port_list = serial.tools.list_ports.comports()
        com_list = []
        for com in port_list:
            com=str(com).split()
            self.comboBox_port.addItem(com[0])
            com_list.append(com[0])
        # set default setting
        self.settings = QSettings('Swing_Detection', 'v1')
        keys = self.settings.allKeys()
        if len(keys)<7:
            self.settings.setValue('COM port', self.comboBox_port.currentText())
            self.settings.setValue('baudrate', '9600')
            self.settings.setValue('save route', './')
            self.settings.setValue('load file', './')
            self.settings.setValue('distance from', 0)
            self.settings.setValue('distance to', 0)
            self.settings.setValue('cycle', {'small':{'check': False, 'length': 0},
                                             'big':{'check': False, 'length':0}})
        # load setting
        if self.settings.value('COM port') not in com_list:
            self.settings.setValue('COM port', self.comboBox_port.currentText())
        self.comboBox_port.setCurrentText(self.settings.value('COM port'))
        self.comboBox_baud.setCurrentText(self.settings.value('baudrate'))
        self.textEdit_saveroute.setText(self.settings.value('save route'))
        self.textEdit_loadfile.setText(self.settings.value('load file'))
        self.spinBox_disfrom.setValue(self.settings.value('distance from'))
        self.spinBox_disto.setValue(self.settings.value('distance to'))
        self.cycle_condition = self.settings.value('cycle')
        self.checkBox_cyclesmall.setChecked(self.cycle_condition['small']['check'])
        self.doubleSpinBox_cyclesmall.setValue(self.cycle_condition['small']['length'])
        self.checkBox_cyclebig.setChecked(self.cycle_condition['big']['check'])
        self.doubleSpinBox_cyclebig.setValue(self.cycle_condition['big']['length'])
        # variables
        self.swing_data = ''
        # connect signal
        self.push_renew.clicked.connect(self.renew_port)
        self.comboBox_port.currentTextChanged.connect(lambda: self.settings.setValue('COM port', self.comboBox_port.currentText()))
        self.comboBox_baud.currentTextChanged.connect(lambda: self.settings.setValue('baudrate', self.comboBox_baud.currentText()))
        self.push_saveroute.clicked.connect(self.saveroute_choose)
        self.textEdit_saveroute.textChanged.connect(lambda: self.settings.setValue('save route', self.textEdit_saveroute.toPlainText()))
        self.push_start.clicked.connect(self.monitor_state)
        self.push_clear.clicked.connect(self.clear_data)
        self.push_save.clicked.connect(self.save_data)
        self.push_loadfile.clicked.connect(self.load_file)
        self.textEdit_loadfile.textChanged.connect(lambda: self.settings.setValue('load file', self.textEdit_loadfile.toPlainText()))
        self.spinBox_disfrom.valueChanged.connect(lambda: self.settings.setValue('distance from', self.spinBox_disfrom.value()))
        self.spinBox_disto.valueChanged.connect(lambda: self.settings.setValue('distance to', self.spinBox_disto.value()))
        self.checkBox_cyclesmall.stateChanged.connect(lambda: self.cycle_condition_change('small', 'check'))
        self.doubleSpinBox_cyclesmall.valueChanged.connect(lambda: self.cycle_condition_change('small', 'length'))
        self.checkBox_cyclebig.stateChanged.connect(lambda: self.cycle_condition_change('big', 'check'))
        self.doubleSpinBox_cyclebig.valueChanged.connect(lambda: self.cycle_condition_change('big', 'length'))
        self.push_run.clicked.connect(self.swing_calculation)
        
    def renew_port(self):
        # clear old list and add new list
        old = self.comboBox_port.currentText()
        self.comboBox_port.clear()
        port_list = serial.tools.list_ports.comports()
        com_list = []
        for com in port_list:
            com=str(com).split()
            self.comboBox_port.addItem(com[0])
            com_list.append(com[0])
        if old in com_list:
            self.comboBox_port.setCurrentText(old)
        else:
            self.settings.setValue('COM port', self.comboBox_port.currentText())
        
    def saveroute_choose(self):
        folder_path = QFileDialog.getExistingDirectory(self,
                  "Choose save folder",
                   self.textEdit_saveroute.toPlainText())     # start path
        if folder_path:
            self.textEdit_saveroute.setText(folder_path)
        
    def monitor_state(self):
        if self.push_start.isChecked():
            self.push_start.setText("Monitoring...")
            self.lineEdit_COM.setText("searching...")
            self.lineEdit_COM.setStyleSheet("color: blue; font-size: 10pt; font-family: Calibri;")
            # create serial, thread and timer instance
            try:
                self.ser=serial.Serial(self.comboBox_port.currentText(),self.comboBox_baud.currentText(),timeout=2)
            except serial.SerialException:
                logger.error(f'{traceback.format_exc()}')
                QMessageBox.critical(self, 'Error', 
                                     'The access to the COM port is denied.\nPlease choose a right COM port.')
                self.push_start.setChecked(False)
                self.push_start.setText("Start")
                self.lineEdit_COM.setText("disconnected")
                self.lineEdit_COM.setStyleSheet("color: red; font-size: 10pt; font-family: Calibri;")
                return
            self.ser_thread = SerialThread(myWin=self)
            # connect signal from thread to main window
            self.ser_thread.signal_ser_raw.connect(self.data_process)
            self.ser_thread.signal_ser_empty.connect(self.COM_empty)
            self.ser_thread.signal_ser_status.connect(self.exit_thread)
            # start the thread and plot
            self.ser_thread.start()
            self.plot_trend.mpl.toggle_pause()
            # calculate the delta time and start the single shot timer
            time1 = datetime.now()
            # time2 = time1+timedelta(minutes=1)
            # time2 = datetime(time2.year, time2.month, time2.day, time2.hour, time2.minute, 2)
            time2 = time1+timedelta(days=1)
            time2 = datetime(time2.year, time2.month, time2.day, 0, 0, 2)
            delta = time2-time1
            self.timer_midnight = QTimer()
            self.timer_midnight.setSingleShot(True)
            self.timer_midnight.timeout.connect(self.save_midnight)
            self.timer_midnight.start(round(delta.total_seconds()*1000))
        else:
            self.ser_thread.exit()
            
    def data_process(self, raw, time):
        result_raw = re.match('\$,\d+$', raw)
        if result_raw:
            self.lineEdit_COM.setText("connected")
            self.lineEdit_COM.setStyleSheet("color: green; font-size: 10pt; font-family: Calibri;")
            data = int(raw.split(',')[1])
        else:
            self.lineEdit_COM.setText("wrong format")
            self.lineEdit_COM.setStyleSheet("color: orange; font-size: 10pt; font-family: Calibri;")
            logger.warning(f'Data format from serial port is wrong. Raw string: {raw}')
            return
        self.swing_data = self.swing_data+re.sub('\$', time.strftime('%Y-%m-%d %H:%M:%S.%f'), raw)+'\n'
        self.plot_trend.mpl.update_line_data(time, data)
        
    def COM_empty(self):
        if self.push_start.isChecked():
            self.lineEdit_COM.setText("searching...")
            self.lineEdit_COM.setStyleSheet("color: blue; font-size: 10pt; font-family: Calibri;")
            logger.warning(f'{self.comboBox_port.currentText()} is empty.')
            
    def exit_thread(self):
        # end monitoring
        self.push_start.setChecked(False)
        self.push_start.setText("Start")
        self.lineEdit_COM.setText("disconnected")
        self.lineEdit_COM.setStyleSheet("color: red; font-size: 10pt; font-family: Calibri;")
        # stop the serial and timer
        self.timer_midnight.stop()
        self.plot_trend.mpl.toggle_pause()
        self.ser.close()
        # delete the serial, thread and timer instance
        del self.ser_thread
        del self.ser
        del self.timer_midnight
        
            
    def save_midnight(self):
        # save daily data
        # fileTime = datetime.now()-timedelta(minutes=1)
        # fileName = os.path.join(self.textEdit_saveroute.toPlainText(),fileTime.strftime('%y%m%d_%H%M00')+'.txt')
        # split_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        fileTime = datetime.now()-timedelta(days=1)
        fileName = os.path.join(self.textEdit_saveroute.toPlainText(),fileTime.strftime('%y%m%d')+'.txt')
        split_time = datetime.now().strftime('%Y-%m-%d')
        swing_split = re.split(split_time, self.swing_data, 1)
        self.swing_data = split_time+swing_split[1]
        with open(fileName,'w') as f:
            print(f'Distance range: {self.spinBox_notefrom.value()} ~ {self.spinBox_noteto.value()}', file=f)
            f.write(swing_split[0])
        # set the next timer
        time1 = datetime.now()
        # time2 = time1+timedelta(minutes=1)
        # time2 = datetime(time2.year, time2.month, time2.day, time2.hour, time2.minute, 2)
        time2 = time1+timedelta(days=1)
        time2 = datetime(time2.year, time2.month, time2.day, 0, 0, 2)
        delta = time2-time1
        self.timer_midnight = QTimer()
        self.timer_midnight.setSingleShot(True)
        self.timer_midnight.timeout.connect(self.save_midnight)
        self.timer_midnight.start(round(delta.total_seconds()*1000))
        
    def clear_data(self):
        self.swing_data = ''
        self.plot_trend.mpl.plot_clear()
        
    def save_data(self):
        fileTime = datetime.now().strftime('%y%m%d_%H%M%S')
        fileName = os.path.join(self.textEdit_saveroute.toPlainText(),fileTime+'.txt')
        name = QFileDialog.getSaveFileName(self, 'Save File',
                                           fileName,
                                           "Text files (*.txt)")
        if name[0]:
            with open(name[0],'w') as f:
                print(f'Distance range: {self.spinBox_notefrom.value()} ~ {self.spinBox_noteto.value()}', file=f)
                f.write(self.swing_data)
    
    def load_file(self):
        name = QFileDialog.getOpenFileName(self, 'Load History Data',
                                           self.textEdit_loadfile.toPlainText(),
                                           "Text files (*.txt)")
        if name[0]:
            self.textEdit_loadfile.setText(name[0])
            with open(name[0]) as f:
                dis_range = re.match('Distance range: (\d+) ~ (\d+)', f.readline())
                if dis_range:
                    self.spinBox_disfrom.setValue(int(dis_range.group(1)))
                    self.spinBox_disto.setValue(int(dis_range.group(2)))
        
    def cycle_condition_change(self, key_1, key_2):
        if key_2 == 'check':
            self.cycle_condition[key_1][key_2] = not self.cycle_condition[key_1][key_2]
        elif key_2 == 'length':
            self.cycle_condition[key_1][key_2] = self.sender().value()
        self.settings.setValue('cycle', self.cycle_condition)
        
    def swing_calculation(self):
        # read file data
        self.hist_time = []
        self.hist_swing = []
        try:
            with open(self.textEdit_loadfile.toPlainText()) as f:
                f.readline()
                for line in f:
                    data = line.split(',')
                    # self.hist_time.append(data[0])
                    self.hist_swing.append(int(data[1]))
        except FileNotFoundError:
            QMessageBox.critical(self, 'Error', 
                                 'Can not find the file.')
            self.push_run.setChecked(False)
            return
        # calculation
        if self.cycle_condition['small']['check']:
            cycle_min = self.cycle_condition['small']['length']*10
        else:
            cycle_min = 0
        if self.cycle_condition['big']['check']:
            cycle_max = self.cycle_condition['big']['length']*10
        else:
            cycle_max = 36000   # 1 hour
        try:
            sheet_count, swing_overlap = ssc.get_each_sheet(self.hist_swing, 
                                                            self.spinBox_disfrom.value(), self.spinBox_disto.value(), 
                                                            cycle_min, cycle_max)
        except ssc.SwingException:
            QMessageBox.critical(self, 'Error', 
                                 'Swing is not in the distance range or the sample is not enough.\nPlease check your input or raw data.')
            self.push_run.setChecked(False)
            return
        swing_range, avg_all, avg_first20, avg_last20, ind_first20, ind_last20 = ssc.get_swing_range(swing_overlap, sheet_count)
        # show the answer
        self.lineEdit_count.setText(str(sheet_count))
        self.lineEdit_avgall.setText("%.2f" % avg_all)
        if avg_first20 != 'NA':
            self.lineEdit_avgfirst.setText("%.2f" % avg_first20)
            self.lineEdit_avglast.setText("%.2f" % avg_last20)
        else:
            self.lineEdit_avgfirst.setText(avg_first20)
            self.lineEdit_avglast.setText(avg_last20)
        # plot histogram
        self.plot_hist.mpl.plot_hist(swing_range)
        self.plot_hist.mpl.plot_swing(swing_overlap, ind_first20, ind_last20)
        # reset run button
        self.push_run.setChecked(False)
        
    def closeEvent(self, event):
        reply = QMessageBox.information(self, 'Warning', 'Are you sure to quit?',
                                     QMessageBox.Yes, QMessageBox.No)
        if reply==QMessageBox.Yes:
            event.accept()
            if self.push_start.isChecked():
                self.push_start.setChecked(False)
                self.monitor_state()
            # clear handlers of logger and shutdown logger
            logger.debug('End of application: Swing Detection')
            logger.handlers.clear()
            logging.shutdown()
        else:
            event.ignore()
        

if __name__=="__main__":  
    app = QApplication(sys.argv)  
    myWin = MyMainWindow()
    myWin.show()  
    sys.exit(app.exec_())  