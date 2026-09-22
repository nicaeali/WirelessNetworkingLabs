"""Shared settings and helpers for Lab1 (OFDM, modulation, CRC)."""
import argparse
import socket
import time

import numpy as np
import pmt
from gnuradio import blocks, digital, gr

# ----------------------------------------------------------------------
# INSTRUCTOR SETTINGS - edit these after calibration (guide, Step 10)
# ----------------------------------------------------------------------
DEFAULTS = dict(
    rate=1e6,        # sample rate (samples/s)
    cp=16,           # cyclic prefix length (samples)
    tx_gain=89.0,    # default TX gain (dB)
    rx_gain=40.0,    # default RX gain (dB)
    amp=0.025,        # digital amplitude at TX (keep OFDM peaks below clipping)
    tx_ant="TX/RX",  # TX antenna port
    rx_ant="RX2",    # RX antenna port
)

# UHD device arguments per node: hostname prefix -> args. "" = first radio found.
DEVICE_ARGS = {
    # "sdr2-s1-lg1": "resource=rio0,type=x300",
    # "sdr2-md1": "resource=rio0,type=x300",
}
# ----------------------------------------------------------------------

PACKET_LEN = 96           # payload bytes per packet
LEN_TAG = "packet_len"    # tagged-stream length key
FFT_LEN = 64
BPS = {"bpsk": 1, "qpsk": 2, "16qam": 4}


def device_args(cli_value):
    if cli_value is not None:
        return cli_value
    host = socket.gethostname()
    for prefix, args in DEVICE_ARGS.items():
        if host.startswith(prefix):
            return args
    return "type=b200"


def parse_args(description, tx):
    p = argparse.ArgumentParser(description=description)
    p.add_argument("--freq", type=float, required=True, help="center frequency (Hz)")
    p.add_argument("--mod", choices=list(BPS), default="qpsk")
    p.add_argument("--rate", type=float, default=DEFAULTS["rate"])
    p.add_argument("--cp", type=int, default=DEFAULTS["cp"])
    p.add_argument("--gain", type=float,
                   default=DEFAULTS["tx_gain"] if tx else DEFAULTS["rx_gain"])
    p.add_argument("--ant", default=DEFAULTS["tx_ant"] if tx else DEFAULTS["rx_ant"])
    p.add_argument("--args", default=None, help="UHD device args")
    if tx:
        p.add_argument("--amp", type=float, default=DEFAULTS["amp"])
    return p.parse_args()


def fft_window():
    try:
        from gnuradio.fft import window
        return window.WIN_BLACKMAN_hARRIS
    except (ImportError, AttributeError):
        from gnuradio.filter import firdes
        return firdes.WIN_BLACKMAN_hARRIS


def random_bytes_source(seed=42, n_packets=2000):
    rng = np.random.RandomState(seed)
    data = rng.randint(0, 256, PACKET_LEN * n_packets).tolist()
    return blocks.vector_source_b(data, True)


def packetizer():
    return blocks.stream_to_tagged_stream(gr.sizeof_char, 1, PACKET_LEN, LEN_TAG)


class SpacedOfdmTx(gr.hier_block2):
    """One OFDM-symbol zero gap prevents back-to-back acquisition losses."""
    def __init__(self, mod, cp):
        import ofdm_lab_txrx as lab
        gr.hier_block2.__init__(self, "Lab OFDM transmitter",
            gr.io_signature(1, 1, gr.sizeof_char),
            gr.io_signature(1, 1, gr.sizeof_gr_complex))
        tx = lab.ofdm_tx(fft_len=FFT_LEN, cp_len=cp, packet_length_tag_key=LEN_TAG,
                         bps_header=1, bps_payload=BPS[mod])
        gap = digital.burst_shaper_cc([1+0j], 0, FFT_LEN+cp, False, LEN_TAG)
        self.connect(self, tx, gap, self)


def make_ofdm_tx(mod, cp):
    return SpacedOfdmTx(mod, cp)


def make_ofdm_rx(mod, cp):
    import ofdm_lab_txrx as lab
    return lab.ofdm_rx(fft_len=FFT_LEN, cp_len=cp, frame_length_tag_key="frame_length",
                       packet_length_tag_key=LEN_TAG, bps_header=1, bps_payload=BPS[mod])


class PacketCounter(gr.sync_block):
    """Counts packets (one length tag per packet). Read with get_rate()."""

    def __init__(self, len_tag=LEN_TAG):
        gr.sync_block.__init__(self, name="Packet counter",
                               in_sig=[np.uint8], out_sig=None)
        self.key = pmt.intern(len_tag)
        self.count = 0
        self._last_count = 0
        self._last_t = time.time()

    def work(self, input_items, output_items):
        n = len(input_items[0])
        start = self.nitems_read(0)
        self.count += len(self.get_tags_in_range(0, start, start + n, self.key))
        return n

    def get_rate(self):
        now = time.time()
        rate = (self.count - self._last_count) / max(now - self._last_t, 1e-6)
        self._last_count, self._last_t = self.count, now
        return rate


def wrap_widget(sink):
    """Turn a qtgui sink into a PyQt5 widget."""
    from PyQt5 import Qt
    try:
        import sip
    except ImportError:
        from PyQt5 import sip
    return sip.wrapinstance(sink.qwidget(), Qt.QWidget)
