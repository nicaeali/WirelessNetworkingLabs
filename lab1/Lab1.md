<!-- Student-facing draft. Instructor: confirm the new image reload, account access, and assigned RF configuration before distribution. -->
# Exploring OFDM and Digital Modulation

ECE-GY 6323 Wireless Networks | Lab1

In this experiment, you will send packets between two software-defined radios on COSMOS. Use the receiver's spectrum, waterfall, constellation, and packet counter to explore:

- how sample rate changes the bandwidth of an OFDM signal;
- how transmit gain changes the received signal level;
- how BPSK, QPSK, and 16-QAM trade data rate for reliable packet delivery;
- how the cyclic prefix affects the time needed to transmit a packet.

Arrange an approved **COSMOS sandbox 5 (SB5)** reservation and a COSMOS account with SSH access before beginning. You need a laptop with a terminal and a browser; the radios are already on the testbed.

## Background

A software-defined radio performs much of its signal processing in software. Here, GNU Radio creates and decodes the baseband waveform, and two USRP B210 radios transmit and receive it.

The documented SB5 link connects the radios through a coaxial cable and a fixed 60 dB attenuator. The attenuator reduces the signal power before it reaches the receiver. We will change transmit gain while keeping this physical path fixed.

![The Lab1 link: GNU Radio on node1-1 sends through a B210, a fixed attenuator, and a second B210 to GNU Radio on node1-2.](assets/lab1_link.svg)

*Lab1 topology. You control both nodes from your laptop using SSH and browser desktops. The documented SB5 arrangement is described in the [COSMOS OFDM laboratory](https://www.cosmos-lab.org/wiki/public/tutorials/sdr-gnuradio/ber/ofdm).*

Orthogonal frequency-division multiplexing (OFDM) divides a transmission across many subcarriers. Our waveform uses a 64-point FFT, 48 data subcarriers, and 4 pilot subcarriers. The remaining positions include the unused center frequency, or DC, and guard positions near the band edges.

Each packet carries 96 payload bytes and a CRC for error detection. You will choose BPSK, QPSK, or 16-QAM for the payload on both nodes. A cyclic prefix is added to each OFDM symbol, and a zero-filled gap lasting one OFDM symbol separates packets. These overheads affect packet rate even when the payload size stays fixed.

The transmitter does not automatically change modulation, and the receiver does not send acknowledgments. You will use your measurements to discuss adaptation and retransmission later in the lab.

## Run my experiment

### Reserve SB5

Before your planned lab time, use the [COSMOS portal](https://www.cosmos-lab.org/) to arrange an approved SB5 reservation under the course's access arrangements. Confirm with the TA that your account can load the course image, `ece6323-lab1.ndz`.

Plan approximately 100-110 minutes for the online activities, with additional time for imaging and cleanup. The plots and written analysis can be completed offline. Record your reservation's start time, end time, and time zone, and stop the experiment before the reservation ends.

We will use these resources and settings:

| Setting | Value |
|---|---|
| Console | `console.sb5.cosmos-lab.org` |
| Transmitter / receiver | `node1-1` / `node1-2` |
| Course image | `ece6323-lab1.ndz` |
| Program directory on both nodes | `/root/lab1` |
| Center frequency | 2.400 GHz |
| Default / half sample rate | 1,000,000 / 500,000 samples/s |
| Default TX / fixed RX gain | 89 / 40 dB |
| Digital amplitude | 0.025 |
| Default cyclic prefix | 16 samples |
| Radio ports | TX: `TX/RX`; RX: `RX2` |

Use the assigned 2.400 GHz setting for this cabled course experiment during your reservation. Keep the receiver gain, digital amplitude, and frequency fixed unless an activity explicitly changes a setting. If the TA announces different settings, record those and follow the TA's instructions.

### Load the course image

At the beginning of your reservation, open a terminal on your laptop. Replace `YOUR_USERNAME` with your own COSMOS username:

```bash
ssh YOUR_USERNAME@console.sb5.cosmos-lab.org
```

This is your **console terminal**. It controls the nodes. One member of your group should load the image; loading replaces the disks on the assigned nodes.

On the **console**, run:

```bash
omf tell offs -t node1-1,node1-2
omf load -i ece6323-lab1.ndz -t node1-1,node1-2
```

Wait until imaging reports success for both nodes. Then turn them on:

```bash
omf tell on -t node1-1,node1-2
omf stat -t node1-1,node1-2
```

Booting takes time. Wait until the nodes accept SSH before proceeding. If the image is reported as missing or unreadable, contact the TA.

### Open the transmitter and receiver terminals

Keep the console terminal open. You will use two additional laptop terminals: one for the transmitter and one for the receiver.

In a **new laptop terminal**, connect to the transmitter:

```bash
ssh -J YOUR_USERNAME@console.sb5.cosmos-lab.org \
  -L 127.0.0.1:18080:127.0.0.1:8080 root@node1-1
```

In another **new laptop terminal**, connect to the receiver:

```bash
ssh -J YOUR_USERNAME@console.sb5.cosmos-lab.org \
  -L 127.0.0.1:18081:127.0.0.1:8080 root@node1-2
```

The `-J` option connects through the console. The `-L` option lets your laptop browser reach each node's desktop. Use your own username for the console connection and `root` for the node connection. If a local port is already in use, close an older lab tunnel before reconnecting. Ask the TA about an unexpected SSH host-key warning.

In **both node terminals**, run:

```bash
export DISPLAY=:1
cd /root/lab1
uhd_find_devices
```

Look for a B210 in the discovery output. The serial numbers will differ between the nodes. If you reconnect later, repeat the `export DISPLAY=:1` and `cd /root/lab1` commands.

You should now have three terminals:

| Terminal | Prompt identifies | Use it for |
|---|---|---|
| Console | `YOUR_USERNAME@console.sb5` | Imaging and node power |
| Transmitter | `root@node1-1` | Running the TX program |
| Receiver | `root@node1-2` | Running the RX program |

**Lab report:** Record your group members, reservation time and time zone, image name, and experiment settings. Include one discovery output and identify the radio model. Include the command and terminal prompt with terminal evidence.

### Open the browser desktops

On your laptop, open two browser tabs:

- [Transmitter desktop](http://localhost:18080/vnc.html?autoconnect=1&resize=scale)
- [Receiver desktop](http://localhost:18081/vnc.html?autoconnect=1&resize=scale)

Connect if prompted. An empty desktop is normal until you start a program. Keep both node SSH terminals open while using the desktops.

**Tip:** Closing the browser does not stop a radio program. Stop the transmitter with **Ctrl-C** in its terminal, then stop the receiver in its terminal. When changing modulation, sample rate, or cyclic prefix, stop both programs and restart the receiver first, followed by the transmitter.

### Observe the receiver with the transmitter off

We will first measure a noise reference. Leave the transmitter stopped. In the **receiver terminal**, run:

```bash
python3 ofdm_rx.py --freq 2.4e9 --mod qpsk --rate 1e6
```

The receiver window should appear in its browser desktop. Open the **Frequency** tab. The horizontal axis is frequency in MHz; the vertical axis is relative power in dB. The plot is not a calibrated dBm measurement.

Choose a representative frequency region inside the band that the signal will occupy. Exclude the exact center bin, obvious narrow peaks, and the band edges. Keep this same region and the same display settings for later power comparisons.

**Lab report:** Save a TX-off spectrum screenshot. Estimate the noise level in your chosen region and record the region's frequency range. Is the floor approximately flat? Describe any narrow peaks without assuming their source. This is a cabled experiment, so a peak alone does not establish external Wi-Fi interference.

### Transmit QPSK and examine the signal

Leave the receiver running. In the **transmitter terminal**, run:

```bash
python3 ofdm_tx.py --freq 2.4e9 --mod qpsk --rate 1e6
```

The transmitter window contains a gain slider and a packets-per-second counter. Wait at least 15 seconds for startup and then for the counters to settle. Both windows should show **1000000 samples/s**, QPSK, and a 16-sample cyclic prefix. Check TX gain 89 dB and RX gain 40 dB. At this setting, the transmitter sends approximately 962 packets/s; the receiver should deliver close to that rate.

On the receiver, examine all three tabs:

- **Frequency** shows how received power is distributed across frequency.
- **Waterfall** shows how that spectrum changes with time. A change in transmit power should appear as a change in the band brightness.
- **Constellation** shows equalized payload symbols before symbol decisions and CRC checking. Some displayed symbols may belong to packets that later fail CRC.

The receiver counter measures packets passing CRC. It does not count every packet the radio detects. When packet acquisition stops, the constellation can retain its last samples; a frozen, clean-looking plot is not evidence of a working link.

**Lab report:** Save frequency, waterfall, and constellation screenshots. Estimate the center frequency and occupied bandwidth, explaining how you chose the band edges. Use the displayed sample rate to calculate the subcarrier spacing:

```text
Subcarrier spacing = sample rate / 64
```

Compare your result with the 15 kHz LTE subcarrier spacing discussed in class. The 48 data and 4 pilot tones span approximately 53 subcarrier-width intervals, including the center gap. Compare `53 x subcarrier spacing` with your measured bandwidth. This does not mean there are 53 active tones, and this waveform is not an LTE implementation. Also identify the number of QPSK clusters and the bits carried by each payload subcarrier symbol.

### Change the sample rate

Stop TX, then RX. Restart the **receiver** at half the sample rate:

```bash
python3 ofdm_rx.py --freq 2.4e9 --mod qpsk --rate 500e3
```

Then restart the **transmitter** at the same rate:

```bash
python3 ofdm_tx.py --freq 2.4e9 --mod qpsk --rate 500e3
```

Both windows should now show **500000 samples/s**. Wait for the link to settle and compare its bandwidth and packet rate with the first run.

**Lab report:** Save the half-rate spectrum and compare the bandwidth, subcarrier spacing, and average TX packet rate with the 1 MS/s run. Explain why symbol duration and packet rate change even though the packet format is unchanged.

Before continuing, stop TX and RX and restart both using the earlier **`--rate 1e6`** commands, receiver first. Confirm **1000000 samples/s** in both windows. The half-rate setting is only for this comparison.

### Change transmit gain and estimate SNR

Keep QPSK, the 1 MS/s sample rate, RX gain 40 dB, and digital amplitude 0.025 fixed. In the transmitter window, use the gain slider to select **79 dB**, then **89 dB**, then **69 dB**. Click the slider and use the arrow keys to make precise changes. Wait for the spectrum to settle after each change.

Estimate the typical level of the broad, relatively flat part of the spectrum, called the plateau. Use the same representative frequency region each time rather than the highest peak or the dip at DC. Packet decoding is not required at the lowest setting for this power comparison.

| TX gain (dB) | Plateau (relative dB) | TX-off floor (relative dB) | Difference D (dB) |
|---|---|---|---|
| 79 | | | |
| 89 | | | |
| 69 | | | |

**Lab report:** Complete the table. How far does the plateau move when gain increases from 79 to 89 dB? Is it close to the expected change? What linear power factors correspond to that increase and the subsequent decrease from 89 to 69 dB? Did the baseline noise change? Remember that a gain setting is not itself a transmit power in dBm.

The TX-on spectrum contains signal plus noise, while the TX-off spectrum estimates noise. For comparable spectral bins in a roughly flat region, estimate SNR as follows:

```text
D = plateau_dB - TX_off_floor_dB
gamma = 10^(D/10) - 1
SNR_dB = 10 log10(gamma), provided gamma > 0
```

At high SNR, `D` is close to SNR in dB. Near the noise floor, subtracting the noise contribution matters and visual estimates become unreliable. If the noise reference has drifted, stop TX and measure it again with the same RX gain, sample rate, FFT, and averaging settings. Do not compare differently configured plots or add spectral dB values to obtain total power.

**Lab report:** Estimate SNR at TX gain 89 dB. State the frequency region, noise reference, and any uncertainty in your reading. If signal and noise cannot be distinguished reliably, report that limitation instead of assigning a numerical SNR. For a strongly non-flat spectrum, retain the gain-axis measurements and discuss an SNR estimate with the TA.

Return TX gain to **89 dB** and check that packet delivery recovers before the next activity.

### Compare QPSK, BPSK, and 16-QAM

We will now compare packet delivery as transmit gain decreases. Keep the frequency, sample rate, 16-sample CP, RX gain, and digital amplitude unchanged. Start with the QPSK link already running at TX gain 89 dB.

For each modulation:

1. Wait at least 15 seconds after startup. Save a default-gain constellation and spectrum screenshot.
2. At each gain, allow 5 seconds for settling. Then collect ten TX and RX counter readings, approximately two seconds apart, over the same 20-second interval. Average TX and RX separately. Two group members or a screen recording can help capture both counters.
3. Reduce TX gain in 3 dB steps: **89, 86, 83, 80, 77, 74, 71 dB**. Stop the sweep after a complete interval with no delivered packets, or after reaching 71 dB. Stay within this range; the separate 69 dB point was only for the power comparison.
4. Save constellation screenshots at the default setting, near the transition to packet losses, and near the last setting with deliveries. Describe missing or frozen displays explicitly.
5. Restore TX gain to 89 dB and verify that the link recovers.

After the QPSK sweep, stop TX and RX. For **BPSK**, start the receiver with:

```bash
python3 ofdm_rx.py --freq 2.4e9 --mod bpsk --rate 1e6
```

Then start the transmitter with:

```bash
python3 ofdm_tx.py --freq 2.4e9 --mod bpsk --rate 1e6
```

Repeat the same measurement procedure. Then stop both programs and repeat for **16-QAM**, starting the receiver first:

```bash
python3 ofdm_rx.py --freq 2.4e9 --mod 16qam --rate 1e6
```

In the transmitter terminal:

```bash
python3 ofdm_tx.py --freq 2.4e9 --mod 16qam --rate 1e6
```

Use a table with the following columns for **each modulation**. Retain the individual readings, observation times, and screenshot filenames along with the averages.

| TX gain (dB) | D (dB) | SNR (dB) | Mean TX/s | Mean RX/s | Delivery p | Goodput (bit/s) |
|---|---|---|---|---|---|---|
| 89 | | | | | | |
| 86 | | | | | | |
| 83 | | | | | | |
| 80 | | | | | | |
| 77 | | | | | | |
| 74 | | | | | | |
| 71 | | | | | | |

Calculate the delivery fraction and payload goodput from your average counter readings:

```text
p = mean RX packets/s / mean TX packets/s
G = mean RX packets/s x 96 x 8       bits/s
```

The TX counter observes packets entering the transmit chain, rather than acknowledgments of RF transmission. Use steady intervals without persistent streaming errors. The two displays have independent timing; if your ratio exceeds 1, repeat the measurement rather than silently clamping the result. Record a failed software interval as invalid, and record a functioning interval with no deliveries as "0 observed."

**Lab report:** Include the three measurement tables and the selected constellation screenshots. Explain the following:

- How do the constellation spacing and observed spread change across modulations and gain settings? The plot shows equalized symbols, not raw antenna samples; its spread need not increase monotonically at every point.
- Plot delivery fraction versus estimated SNR for all three modulations. Also keep a plot versus TX gain so points with unreliable SNR estimates remain visible. Define "almost all packets" as `p >= 0.95`. What is the lowest measured SNR meeting that criterion for each modulation, or did your sweep fail to locate it?
- Why can a small number of bit errors cause an entire packet to be rejected? Explain why `1 - p` is neither a direct payload-CRC-failure count nor a bit error rate: acquisition and header failures can also prevent delivery.
- How do TX packet rates and occupied bandwidth compare across the three modulations? Note any unexpected change in plateau power at the same gain.

If delivery does not fall within the assigned gain range, report that result. Do not change frequency, RX gain, or digital amplitude to force a particular curve.

### Compare cyclic-prefix lengths

For the final online activity, we will keep QPSK and the 1 MS/s sample rate and compare CP lengths of 16 and 8 samples. Start with a fresh default-gain baseline: stop both programs, then run the following in the **receiver terminal**:

```bash
python3 ofdm_rx.py --freq 2.4e9 --mod qpsk --rate 1e6 --cp 16
```

In the **transmitter terminal**:

```bash
python3 ofdm_tx.py --freq 2.4e9 --mod qpsk --rate 1e6 --cp 16
```

Check TX gain 89 dB. After settling, average the counters using the same method as before. Stop both programs and change the CP to 8 on the **receiver**:

```bash
python3 ofdm_rx.py --freq 2.4e9 --mod qpsk --rate 1e6 --cp 8
```

Then start the **transmitter** with the same CP:

```bash
python3 ofdm_tx.py --freq 2.4e9 --mod qpsk --rate 1e6 --cp 8
```

Repeat the measurements and capture a constellation screenshot.

| CP (samples) | Mean TX/s | Mean RX/s | Delivery p | Goodput (bit/s) |
|---|---|---|---|---|
| 16 | | | | |
| 8 | | | | |

**Lab report:** Complete the table and calculate the CP overhead `CP / (64 + CP)` and CP duration `CP / sample_rate` for both settings. The frame and its one-symbol zero gap contain the same total number of OFDM-symbol durations in both runs. Use `(64 + 16) / (64 + 8)` to predict the packet-rate ratio and compare it with your measurements. Did the delivery fraction change? Explain why success with CP8 on this cabled link would not establish that it is sufficient for a wireless channel with long delayed echoes.

### Finish the online experiment

Stop TX with **Ctrl-C**, then stop RX. Save your screenshots and counter readings on your laptop. In the **console terminal**, run:

```bash
omf tell offs -t node1-1,node1-2
omf stat -t node1-1,node1-2
```

Confirm that both nodes are off. Close the remaining SSH sessions with `exit`. Students do not save or overwrite the course image.

### If something does not work

If a desktop does not open, a radio window closes, packet delivery remains zero at the default settings, or a terminal reports a buffer exception, save the exact message and contact the TA. Stop any running transmitter while resolving the problem. Do not restart desktop services or rerun setup scripts during measurements; doing so closes running GUI connections.

In your report, retain the unsuccessful interval and explain whether it was a software failure or a valid observation of low delivery. Repeat an invalid measurement after recovery rather than treating it as a zero-delivery data point.

## Analyze your measurements

Complete this part offline after releasing the nodes. Use the data you collected, including any limitations or unresolved points.

### Choose a modulation from measured goodput

Plot payload goodput against estimated SNR for BPSK, QPSK, and 16-QAM on the same axes. Mark unreliable SNR points separately on a TX-gain plot. For each measured SNR range, identify which modulation offers the largest goodput. Only identify crossover regions where your data support them; equal TX gain does not guarantee exactly equal measured SNR across modulations.

**Lab report:** Sketch the upper envelope of the three goodput curves and explain how it could guide an adaptive modulation policy. Relate this to adaptive modulation and coding (AMC): which part did you vary, and which part did you leave unchanged? In a real system, how would the receiver learn the selected packet format? In this experiment, you manually selected matching modulation settings on both nodes.

### Compare with a capacity estimate

At a reliable operating point, use the measured bandwidth `B` in Hz and the corresponding linear SNR `gamma`:

```text
gamma = 10^(SNR_dB/10)
C = B log2(1 + gamma)              bits/s
```

**Lab report:** Compare the best measured payload goodput at that operating point with this Shannon expression. Report `C`, `G`, and `C/G`, and explain at least two contributors to the difference, such as framing, pilots, CP, finite modulation, and packet losses. This comparison uses approximate bandwidth and SNR estimates; if measured goodput appears to exceed the estimate, examine the units and assumptions rather than concluding that the capacity bound was violated.

### Consider retransmissions

The experiment did not implement ARQ. For this thought experiment, assume independent transmission attempts, a constant success probability `p`, unlimited retries, and negligible feedback and turnaround time:

```text
Mean attempts per delivered packet = 1/p
Ideal delivered rate = attempt rate x p x 768       bits/s
```

**Lab report:** If `p = 0.25`, how many attempts are needed on average, and how many are retransmissions? At a comparable measured SNR where 16-QAM has losses, would its ideal ARQ goodput exceed QPSK's? Use each modulation's own attempt rate and success fraction. Explain how feedback overhead or correlated failures could change your conclusion. Do not divide already measured goodput by the number of attempts a second time.

## What to submit

Submit one PDF report containing the **Lab report** items throughout this handout. Include your configuration and discovery output; labeled screenshots; power, modulation, and CP tables; the individual counter readings or a link to them; delivery and goodput plots with units; and your analysis of adaptation, capacity, and retransmissions.

End with a short discussion of one nonideal behavior you observed, how a fixed 16-QAM link might perform when SNR fluctuates, and the overall rate-reliability tradeoff. Report incomplete or unresolved measurements honestly. A sweep that does not reveal a crossover is still an observation to explain.

## References

- ECE-GY 6323 Lectures 1 and 2: signal power, noise, SNR, modulation, CRC, ARQ, OFDM, and cyclic prefix.
- [COSMOS: GNU Radio OFDM Data Transfer with USRP X310](https://www.cosmos-lab.org/wiki/public/tutorials/sdr-gnuradio/gnuradioofdm). This lab adapts the OFDM link and spectrum observations to the course's B210 pair and packet-delivery measurements. Use this handout's B210 commands and course image.
- [COSMOS: OFDM Bit Error Rate at FR1](https://www.cosmos-lab.org/wiki/public/tutorials/sdr-gnuradio/ber/ofdm), for the documented SB5 hardware arrangement. Our measured packet-delivery fraction is distinct from BER.
