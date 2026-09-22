#!/usr/bin/env python3
"""
Lab1 OFDM transmitter.
Example:  python3 ofdm_tx.py --freq FREQ --mod qpsk [--rate 500e3] [--cp 8]
"""
import signal
import sys

from PyQt5 import Qt, QtCore
from gnuradio import blocks, gr, uhd

import lab_common as lc


class OfdmTx(gr.top_block):
    def __init__(self, a):
        gr.top_block.__init__(self, "Lab1 OFDM TX")
        self.src = lc.random_bytes_source()
        self.pkt = lc.packetizer()
        self.counter = lc.PacketCounter()
        self.ofdm = lc.make_ofdm_tx(a.mod, a.cp)
        self.scale = blocks.multiply_const_cc(complex(a.amp))
        self.usrp = uhd.usrp_sink(lc.device_args(a.args),
                                  uhd.stream_args(cpu_format="fc32", channels=[0]))
        self.usrp.set_subdev_spec("A:A", 0)
        self.usrp.set_samp_rate(a.rate)
        self.usrp.set_center_freq(a.freq, 0)
        self.usrp.set_gain(a.gain, 0)
        self.usrp.set_antenna(a.ant, 0)

        self.connect(self.src, self.pkt, self.ofdm, self.scale, self.usrp)
        self.connect(self.pkt, self.counter)


class TxWindow(Qt.QWidget):
    def __init__(self, tb, a):
        Qt.QWidget.__init__(self)
        self.tb = tb
        self.setWindowTitle("Lab1 - OFDM transmitter")
        layout = Qt.QVBoxLayout(self)

        actual_rate = tb.usrp.get_samp_rate()
        layout.addWidget(Qt.QLabel(
            "Center frequency: %.3f MHz   |   Modulation: %s   |   "
            "Sample rate: %.0f samples/s   |   Cyclic prefix: %d samples"
            % (a.freq / 1e6, a.mod.upper(), actual_rate, a.cp)))

        self.rate_label = Qt.QLabel("Packets sent per second: ...")
        font = self.rate_label.font()
        font.setPointSize(16)
        self.rate_label.setFont(font)
        layout.addWidget(self.rate_label)

        gr_range = tb.usrp.get_gain_range(0)
        gmin, gmax = int(gr_range.start()), int(gr_range.stop())
        self.gain_label = Qt.QLabel()
        self.slider = Qt.QSlider(QtCore.Qt.Horizontal)
        self.slider.setRange(gmin, gmax)
        self.slider.setSingleStep(1)
        self.slider.setPageStep(1)
        self.slider.setValue(int(round(a.gain)))
        self.slider.valueChanged.connect(self.set_gain)
        layout.addWidget(self.gain_label)
        layout.addWidget(self.slider)
        layout.addWidget(Qt.QLabel(
            "Tip: click the slider, then use the arrow keys for exact 1 dB steps."))
        self.set_gain(self.slider.value())

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_rate)
        self.timer.start(2000)

    def set_gain(self, value):
        self.tb.usrp.set_gain(float(value), 0)
        self.gain_label.setText("TX gain: %d dB" % value)

    def update_rate(self):
        self.rate_label.setText("Packets sent per second: %.0f" % self.tb.counter.get_rate())


def main():
    a = lc.parse_args("Lab1 OFDM transmitter", tx=True)
    qapp = Qt.QApplication(sys.argv)
    tb = OfdmTx(a)
    win = TxWindow(tb, a)
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
