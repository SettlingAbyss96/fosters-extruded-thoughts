# 12. The gaps

*Level 2 to 3. What research proved that nobody has built into slicers or firmware yet.*

This is the chapter the rest of the handbook was building toward. For each finding: who showed it,
where it lives today, what's missing, and what it would take. "Takes" means software only, small
hardware, or big hardware. "Payoff" is for this printer and the parts I care about.

I've tried to be careful about "nobody has built this." What I really mean is that I couldn't find
it in Orca, Klipper or Kalico, and that's what I say where I'm unsure.

## The big table

| # | Finding | Shown by | Where it lives today | What's missing | Takes | Payoff |
|---|---|---|---|---|---|---|
| 1 | Bonded area, not bond quality, limits PLA's Z strength. Lines 2.5× the nozzle width: 40 to 48% stronger | Allum 2020 and later, Moetazedian 2023 | Slicers allow wide lines, defaults sit around 1.1× | A strength profile that widens inner lines and watches $`h/w`$ and the nozzle tip | Software | High |
| 2 | Equivalent weld time predicts weld strength in high-$`T_g`$ plastics | Seppala 2017, Coogan & Kazmer 2020 | Nowhere. Slicers only cool for overhangs | A thermal history model that plans layer time and fan | Software, IR sensor optional | Medium to high for ABS, PPA |
| 3 | The old layer's temperature sets the interface as much as the nozzle does | Contact temperature physics | Nowhere | Chamber and layer time aware planning | Software | Medium |
| 4 | Preheating the old layer: about 50% stronger bonds | Ravi 2016, Kishore 2017 | Large-format machines | IR or hot air ahead of the nozzle | Hardware | Medium |
| 5 | Melt runs cooler at high flow, so temperature should follow flow | Anderegg 2019, Phan 2018 | A third-party post-processor | Built into firmware or slicer, with lookahead | Software | Medium to high at speed |
| 6 | PA depends on flow and temperature (shear thinning) | Physics, Orca's measurements | Orca adaptive PA (6+ manual tests), Kalico per-move PA | PA from a two-parameter physical model, calibrated automatically | Software + pressure sensor | Medium |
| 7 | Extrusion force tracks line width. Force feedback holds the width | ETH Zurich 2024 to 2025 | Research | A firmware loop on the pressure signal | Software + planned sensor | High |
| 8 | Pressure vs flow vs temperature maps pick settings for unknown materials | Read 2024 | Research | A cool-down sweep routine and parameter selection | Software + planned sensor | High |
| 9 | Slip can be measured and compensated | Greeff 2017, Moretti 2023 | Klipper corrects diameter only, motion sensors only detect jams | Encoder-based flow correction | Software + encoder | Medium |
| 10 | Starts and stops can be modeled and fed forward | Wu, Qian, Okwudire 2023 | Constant retraction, scarf seams (geometry) | Pressure-aware retraction from the PA state | Software | Medium |
| 11 | Thermal effects dominate machine error, multi-sensor models fix it | Mayr 2012 (machine tools) | One-sensor `z_thermal_adjust` | A multi-sensor regression plugin | Software | Medium |
| 12 | Per-motor waveform correction kills fine vertical artifacts | Prusa (phase stepping) | Prusa firmware only | A Klipper/Kalico version | Software + suitable drivers | Medium |
| 13 | Model inversion handles several modes and position-dependent dynamics | Okwudire (filtered B-splines) | Commercial (Ulendo) | An open version, position-dependent shaping | Software | Medium |
| 14 | Annealing shrink is separate from print shrink, and predictable | Crystallization physics, datasheets | One shrink number | Print shrink and annealing shrink per material | Software | High for PPA, nylon |
| 15 | Fiber-filled parts shrink differently along and across the lines | Tekinalp 2014 | One XY shrink number | Direction-aware compensation | Software (hard) | Medium for CF |
| 16 | A chamber close to $`T_g`$ cuts stress and warp | Physics, Stratasys's 70 to 90 °C | Hobby machines run about 50 to 60 °C | The 70 °C chamber | Hardware (in progress) | High |
| 17 | Part fan cooling power depends on the chamber temperature | Heat transfer | Fan percentage only | Chamber-aware fan scaling | Software | Medium |
| 18 | Interlocking layers raise Z strength | BrickLayers | A post-processing script, US patent | Testing it | Software (exists) | Medium |
| 19 | Z-pinning: more than 3.5× Z strength, near isotropic | ORNL | Research | Slicer support for aligned voids and vertical fills | Software | High for specific parts |
| 20 | Stress-aligned multi-axis paths: up to 6.35× the load | Fang 2020 | Research code | Extra axes | Big hardware | Out of scope |
| 21 | Nonplanar top layers on a 3-axis printer | Ahlers 2019 | A research Slic3r fork | A toolhead clearance model in a mainstream slicer | Software | Low to medium |
| 22 | Remelting gives near-isotropic parts | CNC Kitchen | A hobby trick | Shrink compensation and a written process | Process | High for small parts |
| 23 | A camera closed loop corrects flow, speed, Z and temperature | Brion & Pattinson 2022 | Research, first-layer checks on some commercial printers | Camera plus model | Software + camera | Medium, long term |
| 24 | A whole designed experiment in one print | Greeff 2018 | Slicers test one variable per tower | Multi-factor test plates plus regression | Software | Medium |
| 25 | Learning across prints with SPC gating | Chip fab practice | Nowhere | A logger plus estimators | Software | High |
| 26 | Heater power reveals the actual flow | Phan 2018, observability | MPC models it internally | A monitor with flags | Software | Medium |
| 27 | Wet filament shows up as lower viscosity | Rheology, moisture studies | Nowhere | Comparison against a baseline | Software (+ sensor) | Medium |
| 28 | Two-node chamber model with cascade control | Bacher & Madsen, Kalico `dual_loop_pid` | Kalico has the controller | Using it in the thermal module | Config | Medium |
| 29 | Layer time matters in both directions for high-$`T_g`$ welds | Thermal history | Slicers enforce a minimum layer time only | A warning when layers will be too cold, and the chamber or preheat to fix it | Software | Medium |
| 30 | Bead shape depends on the speed ratio and the gap | Comminal 2018 | A fixed bead model | Speed-aware width and flow | Software | Low to medium |

Details and references for each are in the chapter that covers the physics: welds in
[6](06-layer-bonding.md), extrusion in [4](04-extrusion-dynamics.md), heat in [3](03-melting.md) and
[9](09-heat-control.md), stress and shrink in [7](07-shrink-stress-warp.md), motion in
[8](08-motion.md), estimation in [10](10-sensing-estimation.md).

## Software only, on this printer, now

What I could do without buying anything, roughly in order:

1. **A strength profile in Orca.** Extra-wide inner walls and infill, watch $`h/w`$, check the Conch's tip is wide enough
2. **A print logger on the Pi.** Heater power, temperatures, live extruder velocity, fan, chamber. Per-print estimates and flags (chapter 10)
3. **Flow-dependent temperature.** Try the existing post-processor first. If it helps, think about a lookahead version in firmware
4. **A slow chamber cool-down** at the end of hot prints. A macro
5. **Chamber-aware part cooling.** Scale the part fan with how much cooling the chamber temperature leaves ([models](../calibration/models.md#cooling)). A macro wrapping `M106`
6. **Print shrink and annealing shrink** as separate values for PPA-CF, applied as separate presets for annealed parts
7. **A multi-sensor Z thermal model** fitted from QGL and autoz logs. A small plugin
8. **Test BrickLayers** on a few coupons
9. **CUSUM on the anchors** for machine health
10. **Test plates with several variables in one print.** [FullControl](https://github.com/FullControlXYZ/fullcontrol) is perfect for designing test toolpaths directly in Python
11. **Pressure-aware retraction.** Bigger, it's a Kalico change
12. **Dual-loop chamber control,** once the thermal module exists

## Small hardware

| Hardware | What it gets me |
|---|---|
| bd_pressureE (planned) | Pressure maps, force feedback, PA from physics, wet filament detection, the melt thermometer idea |
| BDwidth (planned) | Slip, diameter, the filament motion that pressure alone can't see |
| IR thermometer at the toolhead | Interface temperature, weld time. Needs a Kalico module |
| Contact microphone | Clog and skip detection (acoustic emission research) |
| Camera + line laser | First layer and layer profile measurement |
| Humidity sensors (dry box, room) | The disturbance nobody logs |
| IR or hot air preheater on the toolhead | Hotter interfaces for high-$`T_g`$ welds |

## Practices that cost nothing

From [chapter 11](11-materials.md#what-most-people-skip-across-the-board): dry everything, chamber
close to $`T_g`$ for ABS/ASA/PPA, cool and vent for PLA/PETG, extra-wide inner lines, part fan only
where needed, slow cool-down, annealing with a ramp and support, separate print and annealing shrink,
salt remelting for small solid parts.

## The Z-axis plan

From [chapter 6](06-layer-bonding.md#making-z-stronger-within-fffs-limits):

1. **Geometry first, for everything:** wider lines, lower $`h/w`$, a touch more flow, a wide nozzle land, maybe interlocking layers
2. **Thermal, for high-$`T_g`$ materials:** chamber, nozzle temperature, minimal fan, layer time, maybe preheat
3. **After the print:** annealing, salt remelting for small parts

And the one experiment that tells me which of those matters for which material: Z coupons at two
chamber temperatures, strength divided by measured bonded area.

## Things I haven't seen anyone try

These are my own ideas. I can't be sure nobody has done them, only that I haven't found it:

- **The printer as a calorimeter.** The slope of heater power against flow tells you how crystalline the filament is (chapter 3)
- **The pressure sensor as a melt thermometer.** Pressure at a known flow gives viscosity, viscosity gives an effective melt temperature (chapter 3)
- **A healing number as a slicer constraint.** Plan layer time, fan and chamber to hit a target weld time for each layer (chapter 6)
- **PA from two physical parameters** instead of a test grid (chapter 4)
- **Melt age as a firmware variable.** The age of the plastic at the nozzle falls out of the extruder history, and it sets the melt temperature, PA and how much the melt will expand at the next stop (chapter 4)
- **Restart length that depends on what came before,** shrinking with the flow before the stop and the travel time, to kill seam blobs (chapter 4)
- **Calibration transfer for vendor filament libraries,** using anchors measured on both machines ([library.md](../calibration/library.md))
- **Anchors as a community round robin,** so filament data from different printers can be compared (chapter 13)

## How I'd like to sequence it

If time allows. Each phase depends on the one before it working out:

| Phase | When | What |
|---|---|---|
| 1 | Now, software only | Logger, strength profile, cool-down ramp, chamber-aware fan, flow-temperature test, BrickLayers test |
| 2 | bd_pressureE + BDwidth | Pressure maps, PA from physics, slip loop, wet detection, force feedback |
| 3 | Rear thermal module | Two-node chamber model, cascade control, multi-sensor Z, predictive soak, weld time planning with an IR sensor |
| 4 | Later | Camera loop, z-pinning toolpaths, position-dependent shaping, phase stepping |
