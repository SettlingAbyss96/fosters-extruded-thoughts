# Guides

The practical side: how to actually set things up. The handbook explains why, these explain how.

Everything on the list below is something I did on my own printer, so the details come from real
setups and real mistakes, not from memory of a forum post. Most of them aren't written yet.

| Guide | Status |
|---|---|
| [Mellow ALPS on Klipper: trigger signal vs raw load-cell data](alps-load-cell.md) | Research written, hardware on order |
| Raspberry Pi OS Lite, KIAUH and Kalico from scratch | To write |
| CAN with a BTT U2C: systemd-networkd, the transmit queue, why the bitrate is baked into the firmware, keeping NetworkManager off it | To write |
| Katapult: building it, the first flash over DFU, flashing over CAN and USB, double-reset entry, and the STM32F0 reset-after-DFU quirk | To write |
| An Octopus Pro H723 without Katapult: `flashtool.py -r` into ROM DFU, then `dfu-util` at `0x08020000` | To write |
| An EBB36/42 toolhead board on CAN | To write |
| Moonraker's update manager for plugins, and why plugin code needs a full service restart | To write |
| Reading Shake&Tune graphs, and using the diagonals to find which motor is the problem | To write |
| klipper_tmc_autotune on a Voron | To write |
| Tuning QGL at the probe's noise floor instead of chasing it | To write |
| Klicky plus a nozzle pin on Kalico's built-in `z_calibration` | To write |
| A speed test that doesn't lie (the missing `M400`) | To write |
| Z speed on a Voron 2.4, and how I found the limit the hard way | To write |
| Chamber heater safety: `verify_heater` values that protect you instead of being turned off | To write |
| PPA-CF: drying, chamber temperature, annealing | To write |
| Converting a Mellow LLL Plus buffer to Kalico | Mostly in the [plugin repo](https://github.com/SettlingAbyss96/kalico-filament-buffer) |
