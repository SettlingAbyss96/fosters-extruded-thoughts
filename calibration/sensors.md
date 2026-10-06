# Sensors

What can see what. The whole point is to stop using test prints and my eyes as the sensor for
things a real sensor could measure.

## Have now

| Sensor | Where | Measures |
|---|---|---|
| Accelerometer (on the EBB, CAN) | Toolhead | Resonances, belt comparison, vibration vs speed |
| Klicky probe | Toolhead (dockable) | Bed shape, gantry level, Z of anything it can touch |
| Nozzle Z pin | Bed, rear | Nozzle tip height (autoz) |
| Hotend thermistor | Hotend | Block temperature |
| Bed thermistor | Under the bed | Bed heater temperature |
| Chamber thermistors ×2 | Top, low | Chamber air |
| Frame thermistor | Frame | Frame temperature |
| Buffer sensors | LLL Plus | Buffer position: feed vs consumption |
| TMC drivers | Octopus, EBB | Motor load (StallGuard), only in StealthChop on the 2209s |
| Webcam | Chamber | Pictures. Crowsnest isn't even back on yet |

## Coming

| Sensor | Measures |
|---|---|
| bd_pressureE | Nozzle force → melt pressure. PA, ooze, maybe max flow and clogs |
| ALPS load cell | Nozzle force. Probing, and pressure like above |
| BDwidth | Filament diameter, plus filament movement (slip, runout, jam) |
| 3rd chamber thermistor | Chamber gradient |
| PT1000 hotend | Block temperature without the 280 °C limit |
| Blobifier bucket switch | Bucket is in |

## Cheap things to add

| Sensor | Cost | Why |
|---|---|---|
| 0.001 g scale | **Ordered** | Filament area, density, moisture, the flow ladder, part mass ([filament](filament.md#fast-tests)) |
| Room temp + humidity sensor | ~$5 | The disturbance nobody logs |
| Humidity sensor in the dry box | ~$5 | Moisture is a huge hidden variable for stringing and seams |
| IR temperature sensor at the toolhead | ~$15 | Last-layer temperature, hidden right now |
| Fixed camera aimed at the bed edge, plus a line laser | ~$30 | First-layer profile, seams, stringing. Vision work, later |
| USB microscope | ~$30 | Real bead width and seam close-ups |

## Manual tools

| Tool | Use |
|---|---|
| Calipers / micrometer | Dimensional test part, entered as numbers into a fit, not judged by eye |
| Scale | See above |
| Me | Only for actual taste: seam placement, surface looks. Rate them, so the rating is data |

## Using what I already have, smarter

- **Heater power as a flow sensor.** At steady flow, the extra heater power is about $`\rho c Q \Delta T`$ ([models](models.md#melt-capacity)). MPC already knows the power, so actual flow can be backed out. If it's less than commanded, something's slipping or clogged. When the heater pegs at 100%, that's max flow
- **Buffer drift as a slip detector.** The buffer is calibrated against the commanded extrusion. If the extruder slips, it uses less filament than commanded and the buffer slowly fills. Crude, but free
- **Probe as a Z-only CMM.** Touch the top of a printed test part in a few spots: warp and Z shrink without calipers. With the load cell later, maybe XY edges too
- **Accelerometer during a print.** Vibration at the speeds actually being printed, not just in test patterns. Could also catch extruder clicks
- **TMC load on the extruder** as a crude pressure sensor. Only works in StealthChop, and the extruder is in SpreadCycle for good reasons. Probably a dead end, the pressure sensor does this properly

## What can see what

*What "observable" means formally, and why the pressure sensor matters so much: [handbook chapter 10](../handbook/10-sensing-estimation.md#observability).*

Rows are things I want to know. ● can measure it directly, ○ indirectly or crudely.

| Want to know | Accel | Probe / pin | Thermistors | Heater power | Buffer | Pressure / load cell | BDwidth | Scale | Calipers | Camera |
|---|---|---|---|---|---|---|---|---|---|---|
| Resonances, shaper | ● | | | | | | | | | ○ |
| Bed shape, level, Z offset | | ● | | | | ● | | | | |
| Frame / chamber drift | | ○ | ● | | | | | | | |
| Melt pressure | | | | | | ● | | | | |
| PA | | | | | | ● | | | ○ | ○ |
| Max flow | | | | ○ | | ● | ○ | | | |
| Extruder slip | | | | ○ | ○ | ○ | ● | | | |
| Filament diameter | | | | | | | ● | | | |
| Actual flow / flow residual | | | | ○ | | ○ | ○ | ● | ○ | |
| Shrinkage, contour offset | | ○ | | | | | | | ● | |
| Warp | | ● | | | | | | | ○ | ○ |
| Seams, stringing | | | | | | ○ | | | | ● |
| First layer | | | | | | | | | | ● |
| Ooze | | | | | | ● | | | | ○ |

The pressure sensor column is the big one. It turns PA, max flow and ooze from "print a test and
look" into "measure it."
