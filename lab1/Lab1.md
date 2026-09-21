# Lab 1: Exploring OFDM and Digital Modulation

In this experiment, you will send packets between two software-defined radios on COSMOS. You will see: 
- how sample rate changes the bandwidth of an OFDM signal
- how transmit gain changes the received signal level
- how BPSK, QPSK, and 16-QAM trade data rate for reliable packet delivery

Note that to run this experiment, you will need to have reserved access to radio resources in advance. Refer to the “reserve a server” instructions in order to complete this step several days before you plan to run the experiment.

We will run this experiment on the COSMOS testbed. You should already have set up access to COSMOS before you begin this experiment. Then, log in to https://www.cosmos-lab.org/portal/login with your username and password.

## Background

A software-defined radio performs much of its signal processing in software. Here, GNU Radio creates and decodes the baseband waveform, and two USRP B210 radios and receive it.

TBD - incoming diagram

Orthogonal frequency-division multiplexing (OFDM) divides a transmission across many subcarriers. Our waveform uses a 64-point FFT, 48 data subcarriers, and 4 pilot subcarriers.

Each packet carries 96 payload bytes and a CRC for error detection. You will choose BPSK, QPSK, or 16-QAM for the payload on both nodes. 

The transmitter does not automatically change modulation, and the receiver does not send acknowledgments. You will use your measurements to discuss adaptation and retransmission later in the lab.

## Run my experiment

### Reserve SB5

Before your planned lab time, use the COSMOS portal to arrange an approved SB5 reservation. Plan approximately 100-110 minutes for the online activities, with additional time for imaging and cleanup. The plots and written analysis can be completed offline. 

## Connect and start the lab

At the beginning of your reservation, open a terminal on your laptop. Replace YOUR_USERNAME with your COSMOS username:
```
ssh YOUR_USERNAME@console.sb5.cosmos-lab.org
```
This is your console terminal. It controls the transmitter and receiver nodes. 

### Load the lab image

On the console, run:
```
omf tell offs -t node1-1,node1-2
omf load -i ece6323-lab1.ndz -t node1-1,node1-2
```

Wait for both nodes to report successful imaging. Then turn them on:
```
omf tell on -t node1-1,node1-2
omf stat -t node1-1,node1-2
```

Booting may take some time. Wait until both nodes are on and accept SSH. If the image is reported as missing or unreadable, contact the TA.

### Open the transmitter and receiver terminals 
Keep the console terminal open. You will use two additional terminals: one for the transmitter and one for the receiver. Open two terminals. In the first one, connect to the transmitter:
```
ssh -J YOUR_USERNAME@console.sb5.cosmos-lab.org -L 127.0.0.1:18080:127.0.0.1:8080 root@node1-1
```
In the second terminal, connect to the receiver:
```
ssh -J YOUR_USERNAME@console.sb5.cosmos-lab.org -L 127.0.0.1:18081:127.0.0.1:8080 root@node1-2
```
The `-J` option connects through the console. The `-L` option lets your laptop browser reach each node's desktop.

On both node terminals, run:
```
export DISPLAY=:1
cd /root/lab1
uhd_find_devices
```
Once the command finishes running, look for a B210 in the discovery output.

### Open the browser desktops

On your laptop, open two browser tabs:

- TX: http://localhost:18080/vnc.html?autoconnect=1&resize=scale
- RX: http://localhost:18081/vnc.html?autoconnect=1&resize=scale

If prompted, click connect. An blank screen is normal until you start transmitting/receiving.

### Observe the receiver with the transmitter off

We will first measure a noise reference. In the receiver terminal, rin:
```
python3 ofdm_rx.py --freq 2.4e9 --mod qpsk --rate 1e6
```
On the receiver browser tab, you will see three separate tabs on the GUI which are Frequency, Waterfall, and Constellation. Open the Frequency tab. The horizontal axis is frequency in MHz, the vertical axis is relative power in dB.

### Transmit QPSK and observe the signal

Leave the receiver running. In the transmitter terminal, run:
```
python3 ofdm_tx.py --freq 2.4e9 --mod qpsk --rate 1e6
```

The transmitter window contains a gain slider and a packets-per-second counter. Wait at least 15 seconds for startup and then for the counters to settle. Both windows should show 1000000 samples/s, QPSK, and a 16-sample cyclic prefix. Check TX gain 89 dB and RX gain 40 dB. At this setting, the transmitter sends approximately 962 packets/s; the receiver should deliver close to that rate.

On the receiver, examine all three tabs:
- Frequency shows how received power is distributed across frequency.
- Waterfall shows how that spectrum changes with time. A change in transmit power should appear as a change in the band brightness.
- Constellation shows equalized payload symbols before symbol decisions and CRC checking.

The receiver counter measures packets passing CRC. It does not count every packet the radio detects.

Lab report: Save frequency, waterfall, and constellation screenshots. Estimate the center frequency and occupied bandwidth, explaining how you chose the band edges. Use the displayed sample rate to calculate the subcarrier spacing: Subcarrier spacing = sample rate / 64. Compare your result with the 15 kHz LTE subcarrier spacing discussed in the class. Also, identify the number of QPSK clusters in the Constellation page.

<!-- ### Change the sample rate

Stop TX, then RX. Restart the receiver at half the sample rate:
```
python3 ofdm_rx.py --freq 2.4e9 --mod qpsk --rate 500e3
```
Then restart the transmitter at the same rate:
```
python3 ofdm_tx.py --freq 2.4e9 --mod qpsk --rate 500e
```

Both windows should now show 500000 samples/s. Wait for the link to settle and compare its bandwidth and packet rate with the first run. -->

### Change transmit gain and estimate SNR
Stop TX and RX and restart both using the earlier --rate 1e6 commands, receiver first.
Confirm 1000000 samples/s in both windows.

In the transmitter window, use the gain slider to select 79 dB, then 89 dB, then 69 dB. Click the slider and use the arrow keys to make precise changes. Wait for the spectrum to settle after each change.

Estimate the typical level of the broad, relatively flat part of the spectrum, called the plateau. Use the same representative frequency region each time rather than the highest peak or the dip at DC. 

| TX gain (dB) | Plateau (relative dB) | TX-off floor (relative dB) | Difference D (dB) |
|---|---|---|---|
| 79 | | | |
| 89 | | | |
| 69 | | | |

Lab report: Complete the table. How far does the plateau move when gain increases from 79 to 89 dB? Is it close to the expected change? What linear power factors correspond to that increase and the subsequent decrease from 89 to 69 dB? Did the baseline noise change?

The TX-on spectrum contains signal plus noise, while the TX-off spectrum estimates noise. For comparable spectral bins in a roughly flat region, estimate SNR as follows:
```
D = plateau_dB - TX_off_floor_dB
gamma = 10^(D/10) - 1
SNR_dB = 10 log10(gamma), provided gamma > 0
```

At high SNR, `D` is close to SNR in dB. Near the noise floor, subtracting the noise contribution matters and visual estimates become unreliable. If the noise reference has drifted, stop TX and measure it again with the same RX gain, sample rate, FFT, and averaging settings. Do not compare differently configured plots or add spectral dB values to obtain total power.

Lab report: Estimate SNR at TX gain 89 dB. State the frequency region, noise reference, and any uncertainty in your reading.

### Compare QPSK, BPSK, and 16-QAM

We will now compare packet delivery as transmit gain decreases. Keep the frequency, sample rate, 16-sample CP, RX gain, and digital amplitude unchanged. Start with the QPSK link running at TX gain 89 dB.

For each modulation: 
1. Wait at least 15 seconds after startup. Save a default-gain constellation and spectrum screenshot.
2. At each gain, allow 5 seconds for settling. Then collect ten TX and RX counter readings, approximately two seconds apart, over the same 20-second interval. Average TX and RX separately.
3. Reduce TX gain in 3 dB steps: 89, 86, 83, 80, 77, 74, 71 dB. Stop the sweep after a complete interval with no delivered packets, or after reaching 71 dB.
4. Save constellation screenshots at the default setting, near the transition to packet losses, and near the last setting with deliveries. Describe missing or frozen displays explicitly.
5. Restore TX gain to 89 dB and verify that the link recovers.

After QPSK sweep, stop TX and RX. For BPSK, start the receiver with:
```
python3 ofdm_rx.py --freq 2.4e9 --mod bpsk --rate 1e6
```
Then start the transmitter with:
```
python3 ofdm_tx.py --freq 2.4e9 --mod bpsk --rate 1e6
```
Repeat the same measurement procedure. Then stop both programs and repeat for 16-QAM, starting the receiver first:
```
python3 ofdm_rx.py --freq 2.4e9 --mod 16qam --rate 1e6
```
Then start the transmitter with:
```
python3 ofdm_tx.py --freq 2.4e9 --mod 16qam --rate 1e6
```
Lab report: