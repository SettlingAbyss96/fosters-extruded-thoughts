# Variables

Every variable I can think of that changes how a print comes out. Kinds:

| Kind | Meaning |
|---|---|
| **Knob** | Something I set (slicer or firmware) |
| **State** | Something physical that's actually there and changes, seen or hidden |
| **Property** | Fixed for a given piece of hardware or material. Identify once |
| **Disturbance** | Changes on its own and I don't control it |
| **Output** | What I actually care about in the part |

**Depends on** is what the variable is keyed by. That's where it gets stored, and what makes it
go stale. **Seen by** is what can measure it, now or planned. "Hidden" means nothing measures it
directly yet. Timescales match the [loops](README.md#loops-by-timescale).

Not complete. Add as I go.

## Hardware geometry

| Variable | Kind | Depends on | Seen by | Timescale |
|---|---|---|---|---|
| Nozzle diameter | Property | Nozzle | Declared. Pressure sensor could check it | Hardware |
| Nozzle type (standard, HF, hardened, ObXidian) | Property | Nozzle | Declared | Hardware |
| Nozzle stickout | Property | Nozzle, hotend | Autoz pin, load cell | Hardware |
| Melt zone length / heat transfer | Property | Hotend, nozzle type | Max flow test, heater duty | Hardware |
| Extruder gear ratio, rotation distance | Property | Extruder | Mark-and-measure, BDwidth encoder | Hardware |
| Toolhead mass | Property | Toolhead | Shaper results | Hardware |
| Belt tension / stiffness | State | Belts, temperature | Shake&Tune belt test, shaper | Weeks, temperature |
| Skew (XY, XZ, YZ) | Property | Frame | Calilantern | Rare |
| Axis scale (A/B rotation distance) | Property | Pulleys, belts | Dimensional test | Rare |
| Gantry level | State | Z motors, temperature | QGL probe | Every print |
| Bed shape | State | Bed, temperature | Mesh probe | Every print |
| Z offset (nozzle to bed) | State | Nozzle, probe, temperature | Autoz, load cell | Every print |

## Thermal

| Variable | Kind | Depends on | Seen by | Timescale |
|---|---|---|---|---|
| Hotend block temperature | State | Heater, flow, fan, chamber | Hotend thermistor | Real time |
| Melt temperature at the nozzle | State | Block temp, flow | **Hidden.** MPC model estimates it | Real time |
| Hotend heater power | Knob / state | Controller | Heater duty (known to MPC) | Real time |
| Bed surface temperature | State | Bed heater, chamber | Hidden. Bed thermistor is underneath | Real time |
| Chamber air temperature by height | State | Heater, blowers, bed, insulation | 2 thermistors now, 3 planned | Minutes |
| Frame temperature | State | Chamber, time | Frame thermistor | Minutes to hours |
| Part temperature (last layer) | State | Melt temp, cooling, chamber, layer time | Hidden. IR sensor possible | Real time |
| Motor / driver temperatures | State | Current, chamber | Hidden (MCU temp only) | Minutes |
| Room temperature | Disturbance | Weather, house | Nothing outside the box yet | Hours |
| Part fan airflow | Knob | Fan, duct | Fan tach if 4-pin | Real time |

## Filament

| Variable | Kind | Depends on | Seen by | Timescale |
|---|---|---|---|---|
| Diameter (and ovality) | Disturbance | Spool, position on the spool | BDwidth | Along the spool |
| Density | Property | Material, brand | Scale + known length | Per brand |
| Heat capacity | Property | Material | Datasheet | Per material |
| Moisture | Disturbance | Storage, time | Humidity sensor in the dry box. Maybe pressure noise (bubbles) | Days |
| Viscosity vs temperature and shear | Property | Material, brand, color/additives | Pressure sensor at several flows and temps | Per brand |
| Glass transition / heat deflection | Property | Material | Datasheet | Per material |
| Thermal shrinkage | Property | Material, chamber temp, cooling | Dimensional test | Per material + chamber mode |

## Extrusion

| Variable | Kind | Depends on | Seen by | Timescale |
|---|---|---|---|---|
| Commanded extrusion | Knob | G-code | Known | Real time |
| Extruder slip | State | Pressure, gear grip, filament | BDwidth encoder vs commanded. Buffer drift (crude) | Real time |
| Nozzle melt pressure | State | Flow, viscosity, nozzle | **Hidden now.** bd_pressureE, load cell | Real time |
| Actual flow out of the nozzle | State | Pressure, nozzle | Hidden. Model from pressure. Heater power (crude) | Real time |
| Pressure advance | Property | Nozzle, hotend, extruder, material, temp, flow | PA test now, bd_pressure later | Hardware × material |
| Max volumetric flow | Property | Hotend, nozzle, material, temp | Flow test, heater saturation, pressure knee | Hardware × material |
| Ooze after a stop | Property | Pressure decay, temp, moisture | Pressure decay curve | Hardware × material |
| Retraction / unretract | Knob | Should follow PA and ooze | Stringing tests now | Hardware × material |
| Buffer position | State | Feed vs consumption | Buffer sensors | Real time |

## Motion

| Variable | Kind | Depends on | Seen by | Timescale |
|---|---|---|---|---|
| Speed, accel, square corner velocity, minimum cruise ratio | Knob | Slicer, limits | Known | Real time |
| Resonance frequencies and damping | Property | Mass, belts, frame, temperature | Accelerometer | Hardware, maybe chamber mode |
| Input shaper | Knob | Resonances | Accelerometer | Hardware |
| Motor resonance speeds | Property | Motors, drivers, current | Vibrations profile | Hardware |
| A/B asymmetry | State | Drive path | Vibrations profile | Until fixed |

## Bead and layer

| Variable | Kind | Depends on | Seen by | Timescale |
|---|---|---|---|---|
| Line width | Knob, **derived** | Nozzle, feature | Known | Hardware |
| Layer height | Knob, limits derived | Nozzle | Known | Per print |
| First-layer squish | State | Z offset, first-layer flow, bed shape | Camera, probe | Every print |
| Actual bead shape | Output | Flow, width, height, temp, speed | Hidden. Mass, dimensions, microscope | Per material |
| Flow residual | Property | Bead model error | Scale, dimensions | Per material × nozzle |
| Wall/infill overlap | Knob | Bead shape | Known | Rarely |

## Part outputs

| Variable | Kind | Depends on | Seen by |
|---|---|---|---|
| Dimensional error | Output | Shrinkage, contour offset, skew, scale | Calipers, maybe probe for Z |
| Seams | Output | Pressure transient, retraction, travel, temp | Camera, me |
| Ringing / ghosting | Output | Shaper, accel, belts | Accelerometer (predict), camera |
| Corner bulge | Output | PA, accel, corner velocity | Camera, calipers |
| Stringing | Output | Temp, moisture, retraction, travel | Camera |
| Overhangs, bridges | Output | Cooling vs chamber temp, speed, temp | Camera |
| Warping, curl | Output | Chamber, cooling, bed, adhesion, geometry | Probe on the part after printing, camera |
| Layer adhesion / strength | Output | Interface temp, flow, layer time | Break test |
| First layer | Output | Z offset, mesh, flow, bed temp, surface | Camera |
| Mass | Output | Flow chain | Scale |

## Environment and time

| Variable | Kind | Depends on | Seen by |
|---|---|---|---|
| Chamber setpoint | Knob | Material | Known |
| Soak time | Knob, **derived** | Frame drift rate | Frame sensor ([soak](slicer.md#soak-stop-guessing)) |
| Room humidity | Disturbance | House | Nothing yet |
| Layer time | Derived | Geometry, speed | Known from the G-code |
| Drafts | Disturbance | Door, fans, blowers | Chamber sensors (spread) |
