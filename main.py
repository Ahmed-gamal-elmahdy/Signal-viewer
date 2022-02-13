import re
import sys
import numpy as np
import pandas as pd
from pandas.plotting import table
import pyqtgraph as pg
from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QFileDialog
from matplotlib import pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from signal import Ui_MainWindow


class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(ApplicationWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        def append_color_combobox():
            colors = ["red", "blue", "green", "black"]
            palettes = ["Greys", "rainbow", "plasma", "inferno", "viridis"]
            self.ui.color_plot_combobox.addItems(colors)
            self.ui.palettes_combobox.addItems(palettes)

        append_color_combobox()
        self.ui.signal_plot_combobox.currentTextChanged.connect(
            lambda: self.ui.plot_tabwidget.setCurrentIndex(self.ui.signal_plot_combobox.currentIndex()))
        self.ui.plot_tabwidget.currentChanged.connect(
            lambda: self.ui.signal_plot_combobox.setCurrentIndex(self.ui.plot_tabwidget.currentIndex()))
        self.ui.signal_show_button.clicked.connect(lambda: self.ui.plot_tabwidget.show())
        self.ui.signal_hide_button.clicked.connect(lambda: self.ui.plot_tabwidget.hide())
        self.ui.spectro_show_button.clicked.connect(lambda: self.ui.spectro_tabwidget.show())
        self.ui.spectro_hide_button.clicked.connect(lambda: self.ui.spectro_tabwidget.hide())
        self.ui.signal_pause_button.clicked.connect(lambda: self.timer.stop())
        self.ui.signal_play_button.clicked.connect(lambda: self.timer.start())
        self.ui.speed_plot_slider.setMaximum(1000)
        self.ui.speed_plot_slider.setMinimum(100)
        self.ui.speed_plot_slider.setSingleStep(100)
        self.ui.speed_plot_slider.setValue(500)
        self.ui.min_slider.setMinimum(0)
        self.ui.min_slider.setMaximum(70)
        self.ui.min_slider.setValue(35)
        self.ui.min_slider.setSingleStep(10)
        self.ui.max_slider.setMinimum(70)
        self.ui.max_slider.setMaximum(180)
        self.ui.max_slider.setValue(105)
        self.ui.max_slider.setSingleStep(10)
        self.ui.speed_plot_slider.valueChanged.connect(lambda: speed())
        self.ui.plot_tabwidget.currentChanged.connect(lambda: updatescroll())
        self.ui.signal_plot_scrollbar.sliderReleased.connect(lambda: updatescroll())
        self.ui.signal_plot_scrollbar.valueChanged.connect(lambda: check())
        self.spectro_tab = QtWidgets.QWidget()
        self.spectro_tab.setObjectName("spectro_tab")
        self.ui.spectro_tabwidget.addTab(self.spectro_tab, "Spectrogram")
        self.ui.spectro_tabwidget.setCurrentIndex(self.ui.spectro_plot_combobox.currentIndex())
        self.ui.spectro_plot_combobox.addItem("Choose Signal..")
        self.ui.spectro_plot_combobox.currentIndexChanged.connect(lambda: spectrogramUpdate())
        self.ui.palettes_combobox.currentIndexChanged.connect(lambda: spectrogramUpdate())
        self.ui.max_slider.sliderReleased.connect(lambda: spectrogramUpdate())
        self.ui.min_slider.sliderReleased.connect(lambda: spectrogramUpdate())
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(lambda: update())
        self.timer.start()
        self.ui.actionOpen.triggered.connect(lambda: open_file())
        self.ui.actionExport_as_pdf.triggered.connect(lambda: export())
        signal_path = []
        plot_reference_lines = []
        currentTimeIndex = []
        pens = [(255, 0, 0), (13, 152, 186), (34, 139, 34), (0, 0, 0)]

        def updatescroll():
            try:
                index = self.ui.plot_tabwidget.currentIndex()
                data = pd.read_csv(signal_path[index], header=None, names=["x", "y"])
                time = data['x']
                self.ui.signal_plot_scrollbar.setMinimum(0)
                self.ui.signal_plot_scrollbar.setMaximum(len(time))
                currentTimeIndex[index] = self.ui.signal_plot_scrollbar.value()
                check()
                update()
            except:
                pass

        def check():
            if self.ui.signal_plot_scrollbar.value() == self.ui.signal_plot_scrollbar.maximum():
                self.ui.signal_plot_scrollbar.setValue(0)

        def speed():
            interval = 1000 - (self.ui.speed_plot_slider.value())
            self.timer.setInterval(interval)

        def update():
            for index in range(len(currentTimeIndex)):
                curindex = currentTimeIndex[index]  # set current time index
                curplot = plot_reference_lines[index]  # get the correct grap to that index
                data = pd.read_csv(signal_path[index], header=None, names=["x", "y"])
                time = data['x']
                self.ui.signal_plot_scrollbar.setValue(curindex)
                if curindex + 5 < len(time) - 45:
                    self.pen = pg.mkPen(color=pens[self.ui.color_plot_combobox.currentIndex()])
                    curplot.setPen(self.pen)
                    self.ui.plot_tabwidget.widget(index).setXRange(time[curindex],
                                                                   time[curindex + 50])
                    self.ui.plot_tabwidget.widget(index).setLabel(axis='bottom', text='Time (Sec)')
                    self.ui.plot_tabwidget.widget(index).setLabel(axis='left', text='Amplitude (mv)')
                    curindex += 5
                else:
                    curindex = 0
                currentTimeIndex[index] = curindex

        def open_file():
            for i in range(1):
                filename = QFileDialog.getOpenFileName(filter="csv(*.csv)")
                signal_path.append(filename[0])
                result = re.search('a/(.*).csv', filename[0])
                self.ui.signal_plot_combobox.addItem(result.group(1))
                self.ui.spectro_plot_combobox.addItem(result.group(1))
                addtab(result.group(1))

        def addtab(name):
            index = len(signal_path) - 1
            plot_tab = pg.PlotWidget()
            plot_tab.setBackground("w")
            plot_tab.setObjectName("plot_tab_" + str(index))
            self.ui.plot_tabwidget.addTab(plot_tab, name)
            plot()

        def plot():
            index = len(signal_path) - 1
            data = pd.read_csv(signal_path[index], header=None, names=["x", "y"])
            time = data['x']
            amplitude = data['y']
            pen = pg.mkPen(color=pens[self.ui.color_plot_combobox.currentIndex()])
            curplot = self.ui.plot_tabwidget.widget(index)
            self.ui.signal_plot_scrollbar.setMinimum(0)
            self.ui.signal_plot_scrollbar.setMaximum(len(time))
            curplot.setYRange(min(amplitude), max(amplitude))
            self.ui.plot_tabwidget.widget(index).setLimits(xMin=min(time), xMax=max(time),
                                                           yMin=min(amplitude), yMax=max(amplitude))
            currentTimeIndex.append(0)
            plot_reference_lines.append(curplot.plot(time, amplitude, pen=pen))

        def spectrogram():
            index = self.ui.spectro_plot_combobox.currentIndex() - 1
            data = pd.read_csv(signal_path[index], header=None, names=["x", "y"])
            time = data['x']
            amplitude = data['y']
            fig = plt.figure()
            canvas = FigureCanvas(fig)
            spectro_tab = QtWidgets.QWidget()
            spectro_tab.setObjectName("spectro_tab")
            self.ui.spectro_tabwidget.addTab(spectro_tab, "Spectrogram")
            self.ui.spectro_tabwidget.setCurrentIndex(self.ui.spectro_plot_combobox.currentIndex())
            lay = QtWidgets.QVBoxLayout(self.ui.spectro_tabwidget.currentWidget())
            lay.setContentsMargins(0, 0, 0, -0)
            lay.addWidget(canvas)
            fs = 1 / abs(time[1] - time[0])
            palette = self.ui.palettes_combobox.currentText()
            plt.specgram(amplitude, Fs=fs, cmap=palette)
            plt.xlabel('Time')
            plt.ylabel('Frequency')
            plt.clim(vmin=-1 * self.ui.min_slider.value(), vmax=-1 * self.ui.max_slider.value())
            plt.colorbar()

        def spectrogramUpdate():
            self.ui.spectro_tabwidget.removeTab(self.ui.spectro_tabwidget.currentIndex())
            spectrogram()

        def export():

            index = self.ui.signal_plot_combobox.currentIndex()
            curindex = currentTimeIndex[self.ui.plot_tabwidget.currentIndex()]
            data = pd.read_csv(signal_path[index], header=None, names=["x", "y"])
            time = data['x']
            amplitude = data['y']
            fs = 1 / abs(time[1] - time[0])
            width = 6
            height = 8
            size = (width, height)
            fig = plt.figure(figsize=size)
            ax1 = fig.add_subplot(311)
            time_sample = time[curindex:curindex + 50]
            amp_sample = amplitude[curindex:curindex + 50]
            time_mean = str(round(np.average(time_sample), 3))+"Sec"
            amp_mean = str(round(np.average(amp_sample), 3))+"mV"
            time_std = str(round(np.std(time_sample), 3))+"Sec"
            amp_std = str(round(np.std(amp_sample), 3))+"mV"
            duration = str(round(time[curindex + 50] - time[curindex], 3))+"Sec"
            ax1.plot(time_sample, amp_sample)
            max_amp = str(round(np.max(amp_sample), 3))+"mV"
            min_amp = str(round(np.min(amp_sample), 3))+"mV"
            statistics = {
                "Avg time": [time_mean],
                "Avg amp": [amp_mean],
                "Time std": [time_std],
                "Amp std": [amp_std],
                "duration": [duration],
                "Max amp": [max_amp],
                "Min amp": [min_amp]
            }
            data_frame = pd.DataFrame(statistics, index=[self.ui.signal_plot_combobox.currentText()])
            ax2 = fig.add_subplot(312)
            palette = self.ui.palettes_combobox.currentText()
            ax2.specgram(amplitude, Fs=fs, cmap=palette)
            ax3 = fig.add_subplot(313, frame_on=False)
            ax3.xaxis.set_visible(0)
            ax3.yaxis.set_visible(0)
            table_data = table(ax3, data_frame, loc='upper center')
            table_data.auto_set_font_size(False)
            table_data.set_fontsize(8)
            table_data.scale(1.2, 1.2)
            filename, _ = QFileDialog.getSaveFileName(self, 'export pdf', self.ui.signal_plot_combobox.currentText(),
                                                      'Pdf files(.pdf);;All files()')
            pdf_file = PdfPages(filename + ".pdf")
            pdf_file.savefig()
            pdf_file.close()


def main():
    app = QtWidgets.QApplication(sys.argv)
    application = ApplicationWindow()
    application.show()
    app.exec_()


if __name__ == "__main__":
    main()
