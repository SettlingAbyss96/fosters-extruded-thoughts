# Quality problems, broken down

Each thing that goes wrong on a print, split into what actually causes it. Order is roughly
"check this first." Most of these share causes, which is the whole point of the
[dependency order](README.md#calibration-order-first-pass).

## Seams

*Longer version: [handbook chapter 4](../handbook/04-extrusion-dynamics.md#seams-are-pressure-transients), and the scarf joint in [chapter 5](../handbook/05-laying-a-line.md#where-a-line-starts-and-stops).*

A seam is a **pressure transient.** The loop ends, the nozzle has to go to zero flow, travel, then
come back to exactly the right flow at the start of the next loop. Any error in that pressure state
shows up right there.

| Cause | Why | Measured by |
|---|---|---|
| PA | Wrong PA means pressure is wrong at the end and start of every loop | Pressure sensor, PA test |
| PA vs flow | One PA value, but walls print at a different flow than the PA test | Pressure sensor at several flows |
| Retraction / unretract amount and speed | Has to take pressure to zero and put it back exactly | Pressure sensor |
| Travel time | Leftover pressure oozes during travel | Pressure decay ([ooze](models.md#ooze-and-retraction)) |
| Wipe, seam gap, scarf seam | Geometry of how the loop closes | Camera, me |
| Temperature | Viscosity, ooze | Thermistor, MPC |
| Moisture | Steam, random blobs | Dry box humidity |
| Outer wall speed and accel | Bigger transient to control | Known |

As a control problem: target pressure at the loop end is zero, during travel zero, at the restart
exactly the steady-state pressure for the wall's flow. With a pressure sensor that's something you
can measure on every loop, not judge from a photo.

## Dimensions

| Cause | Why | Measured by |
|---|---|---|
| Shrinkage | Material cools after it sets | Calipers on the test part (slope) |
| Contour offset | Real bead wider or narrower than the model | Calipers (offset) |
| Flow chain | Too much plastic pushes walls out | Scale |
| Skew | Frame not square | Calilantern |
| Axis scale | Belt/pulley | Calipers |
| First-layer squish | Elephant foot | Calipers at the bottom, camera |
| PA, shaper smoothing | Corners bulge or round off | Calipers on corners |
| Warp | Part pulls up | Probe on the part |

## First layer

| Cause | Why | Measured by |
|---|---|---|
| Z offset | The squish | Autoz, load cell |
| Bed shape / mesh | Squish varies across the bed | Probe |
| Gantry level | Same | QGL |
| Thermal drift during the first layer | Frame still moving | Frame sensor ([soak](slicer.md#soak-stop-guessing)) |
| First-layer flow and width | Squish again | Flow chain |
| Bed temp and surface | Adhesion | Thermistor, me |
| Dirty nozzle | Drags and blobs | Blobifier, brush |

## Corners bulging or rounded

| Cause | Why | Measured by |
|---|---|---|
| PA | Pressure overshoot at decel | Pressure sensor, PA test |
| Accel, square corner velocity | Size of the transient | Known |
| Shaper smoothing | Rounds corners at high accel | Accelerometer, shaper results |

## Ringing / ghosting

*Physics: [handbook chapter 8](../handbook/08-motion.md#resonance-and-ringing).*

| Cause | Why | Measured by |
|---|---|---|
| Shaper | Wrong or missing frequency | Accelerometer |
| Accel above what the shaper allows | Residual vibration | Shaper recommendation |
| Belts, A/B asymmetry | Two different frequencies on one axis | Belt test, vibrations profile |
| Motor resonance speeds | Vibration at specific speeds | Vibrations profile |
| Temperature | Belts and frame change hot | Accelerometer at 70 °C |

## Stringing and ooze

| Cause | Why | Measured by |
|---|---|---|
| Moisture | Steam pushes plastic out | Dry box humidity |
| Temperature | Lower viscosity | Thermistor |
| PA | Leftover pressure at the stop | Pressure sensor |
| Retraction | Only after the above | Pressure decay |
| Travel path and time | More time to ooze | Known |

## Under-extrusion at speed

*Physics: [handbook chapter 3](../handbook/03-melting.md#two-ways-to-hit-the-wall).*

| Cause | Why | Measured by |
|---|---|---|
| Past max flow | Hotend can't melt it fast enough | Pressure knee, heater pegged |
| Temperature droop under flow | PID reacts late | MPC fixes it ([MPC](slicer.md#hotend-mpc-with-filament-feedforward)) |
| Extruder slip | High pressure, gears lose grip | BDwidth encoder, buffer drift |
| Filament diameter | Thin spot | BDwidth |

## Overhangs and bridges

| Cause | Why | Measured by |
|---|---|---|
| Cooling vs chamber temperature | Less cooling in a hot chamber | Chamber sensors ([cooling](models.md#cooling)) |
| Speed, layer time | Time to set | Known |
| Temperature | Viscosity, sag | Thermistor |
| Line width | Thinner sets faster | Known |

## Warping, curl, layer splits

*Physics: [handbook chapter 7](../handbook/07-shrink-stress-warp.md#stress-builds-up-layer-by-layer).*

| Cause | Why | Measured by |
|---|---|---|
| Chamber temperature and gradient | Uneven shrink | Chamber sensors (3 planned) |
| Cooling | Too much on hot materials | Fan, chamber |
| Bed temp and adhesion | Holds the part down | Thermistor |
| Layer time | Interface too cold | Known |
| Part geometry | Long thin stuff curls | Known |

## Layer adhesion / strength

*The full story, including where the research disagrees: [handbook chapter 6](../handbook/06-layer-bonding.md).*

| Cause | Why | Measured by |
|---|---|---|
| Interface temperature | Layers have to fuse | Hidden. IR sensor, chamber |
| Flow | Gaps between lines | Scale |
| Cooling | Cold interface | Fan, chamber |
| Moisture | Bubbles, weak layers | Dry box humidity |
