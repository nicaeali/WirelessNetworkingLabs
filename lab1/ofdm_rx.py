#!/usr/bin/env python3
"""
Lab1 OFDM receiver.
Example:  python3 ofdm_rx.py --freq FREQ --mod qpsk [--rate 500e3] [--cp 8]
"""
import signal
import sys

from PyQt5 import Qt, QtCore
from gnuradio import gr, qtgui, uhd

import lab_common as lc

FFT_SIZE = 2048


class OfdmRx(gr.top_block):
    def __init__(self, a):
        gr.top_block.__init__(self, "Lab1 OFDM RX")
        self.usrp = uhd.usrp_source(lc.device_args(a.args),
                                    uhd.stream_args(cpu_format="fc32", channels=[0]))
        self.usrp.set_subdev_spec("A:A", 0)
        self.usrp.set_samp_rate(a.rate)
        self.usrp.set_center_freq(a.freq, 0)
        self.usrp.set_gain(a.gain, 0)
        self.usrp.set_antenna(a.ant, 0)
        rate = self.usrp.get_samp_rate()
        win = lc.fft_window()

        self.freq_sink = qtgui.freq_sink_c(FFT_SIZE, win, a.freq, rate, "Spectrum", 1)
        self.freq_sink.set_update_time(0.10)
        self.freq_sink.set_y_axis(-140, 0)
        self.freq_sink.set_y_label("Relative power", "dB")
        self.freq_sink.enable_grid(True)
        self.freq_sink.enable_autoscale(False)
        self.freq_sink.set_fft_average(0.2)

        self.waterfall = qtgui.waterfall_sink_c(FFT_SIZE, win, a.freq, rate, "Waterfall", 1)
        self.waterfall.set_update_time(0.10)
        self.waterfall.set_intensity_range(-140, 0)

        self.const_sink = qtgui.const_sink_c(1024, "Payload constellation", 1)
        self.const_sink.set_update_time(0.20)
        self.const_sink.set_x_axis(-1.6, 1.6)
        self.const_sink.set_y_axis(-1.6, 1.6)
        self.const_sink.enable_grid(True)

        self.ofdm = lc.make_ofdm_rx(a.mod, a.cp)
        self.counter = lc.PacketCounter()

        self.connect(self.usrp, self.freq_sink)
        self.connect(self.usrp, self.waterfall)
        self.connect(self.usrp, self.ofdm)
        self.connect((self.ofdm, 0), self.counter)
        self.connect((self.ofdm, 1), self.const_sink)


class RxWindow(Qt.QWidget):
    def __init__(self, tb, a):
        Qt.QWidget.__init__(self)
        self.tb = tb
        self.setWindowTitle("Lab1 - OFDM receiver")
        self.resize(1100, 750)
        layout = Qt.QVBoxLayout(self)

        layout.addWidget(Qt.QLabel(
            "Center frequency: %.3f MHz   |   Modulation: %s   |   "
            "Sample rate: %.0f samples/s   |   Cyclic prefix: %d samples   |   RX gain: %.0f dB"
            % (a.freq / 1e6, a.mod.upper(), tb.usrp.get_samp_rate(), a.cp, a.gain)))

        self.rate_label = Qt.QLabel("Packets passing CRC per second: ...")
        font = self.rate_label.font()
        font.setPointSize(16)
        self.rate_label.setFont(font)
        layout.addWidget(self.rate_label)

        tabs = Qt.QTabWidget()
        tabs.addTab(lc.wrap_widget(tb.freq_sink), "Frequency")
        tabs.addTab(lc.wrap_widget(tb.waterfall), "Waterfall")
        tabs.addTab(lc.wrap_widget(tb.const_sink), "Constellation")
        layout.addWidget(tabs)
        layout.addWidget(Qt.QLabel(
            "Equalized payload symbols before decisions and CRC. "
            "It stops updating when no packets are detected."))

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_rate)
        self.timer.start(2000)

    def update_rate(self):
        self.rate_label.setText(
            "Packets passing CRC per second: %.0f" % self.tb.counter.get_rate())


def main():
    a = lc.parse_args("Lab1 OFDM receiver", tx=False)
    qapp = Qt.QApplication(sys.argv)
    tb = OfdmRx(a)
    win = RxWindow(tb, a)
    tb.start()
    win.show()

    def shutdown(*_):
        tb.stop()
        tb.wait()
        qapp.quit()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    ctrl_c_timer = QtCore.QTimer()
    ctrl_c_timer.start(500)
    ctrl_c_timer.timeout.connect(lambda: None)
    qapp.aboutToQuit.connect(lambda: (tb.stop(), tb.wait()))
    qapp.exec_()


if __name__ == "__main__":
    main()
