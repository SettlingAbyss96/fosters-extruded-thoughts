# Models

The physics that links the [variables](variables.md). Simple models are fine. The point is
knowing which knobs are really the same underlying thing, and what a sensor reading actually
tells me.

## Flow chain

How much plastic actually comes out per mm of commanded extrusion:

```math
Q = \frac{\pi d_f^2}{4}\,\dot{e}_{cmd}\,\frac{r_{true}}{r_{cfg}}\,(1 - s)
```

| Symbol | What | Measured by |
|---|---|---|
| $d_f$ | Real filament diameter | BDwidth |
| $\dot{e}_{cmd}$ | Commanded extrusion rate | Known |
| $r_{true}/r_{cfg}$ | Real vs configured rotation distance | Mark-and-measure, BDwidth encoder |
| $s$ | Slip at the gears (goes up with pressure) | BDwidth encoder vs commanded |

The slicer's "flow ratio" lumps all four together **plus** the bead shape into one number, which
is why it changes with every spool and never sticks. Measure each factor on its own and what's
left is the [bead residual](#bead), which is small and stable.

## Nozzle pressure

The nozzle behaves like a capacitor and a resistor. The filament and melt between the gears and
the tip squish a little (compliance $C$), and the nozzle resists flow (resistance $R$):

```math
C\,\frac{dP}{dt} = q_{in} - \frac{P}{R}, \qquad q_{out} = \frac{P}{R}
```

which is a first-order lag between what the extruder pushes and what comes out:

```math
\tau\,\frac{dq_{out}}{dt} = q_{in} - q_{out}, \qquad \tau = RC
```

Pressure advance pushes $q_{in} = q + \tau\\,\dot{q}$, so $q_{out}$ follows $q$. Kalico's PA value
$K$ is in seconds, and it's this $\tau$. **PA isn't a magic number, it's the time constant of the
nozzle.**

The resistance is mostly the nozzle bore and the melt zone:

```math
R \approx \frac{128\,\eta\,L}{\pi d^4}
```

and the melt viscosity $\eta$ drops with temperature and with shear rate (polymer melts thin out
the faster they flow):

```math
\eta(T, \dot\gamma) = \eta_0\, e^{\frac{E_a}{R_g}\left(\frac{1}{T} - \frac{1}{T_0}\right)} \left(\frac{\dot\gamma}{\dot\gamma_0}\right)^{n-1}, \qquad n < 1
```

What falls out of that:

- **PA changes with flow and temperature.** $R$ isn't constant, so one PA value is always a compromise. That's what Orca's adaptive PA option is about (PA as a function of flow and accel)
- **A pressure sensor can identify the material.** Pressure vs flow at two or three temperatures fits $\eta_0$, $E_a$ and $n$. Then PA and max flow can be *predicted* for that material, from a few minutes of extruding into the air
- **A pressure sensor can check the nozzle.** For a Newtonian fluid $R \propto 1/d^4$, but a shear-thinning melt goes more like $d^{-(1+3n)}$, so 0.4 vs 0.6 is about 2.4× for $n = 0.4$ instead of 5× ([handbook](../handbook/04-extrusion-dynamics.md#the-nozzles-resistance-for-a-real-melt)). The melt zone adds resistance that doesn't depend on the bore, so the real ratio is smaller still. Easy to tell apart anyway

## Ooze and retraction

When the extruder stops, pressure bleeds off through the nozzle:

```math
P(t) = P_0\,e^{-t/\tau}, \qquad V_{ooze} = \int_0^{\infty} \frac{P}{R}\,dt = C\,P_0
```

With PA right, the extruder already pulled back as the flow ramped down, so $P_0 \approx 0$ and
there's almost nothing to ooze. What's left: melt expanding as it reheats, gravity, steam from
wet filament.

- **Retraction gets calibrated after PA,** and it should come out small
- **Needing big retraction means PA is off or the filament is wet.** Retraction is covering for something else
- The pressure sensor sees the decay curve directly, so ooze becomes a measurement

## Melt capacity

The hotend can't heat plastic faster than the heater can supply energy:

```math
Q_{max} \le \frac{P_{heater} - P_{loss}}{\rho\,c\,(T_{nozzle} - T_{fil})}
```

The real limit is lower, because the middle of the filament doesn't reach temperature in time.
Signs you're past it:

- Pressure rises faster than the viscosity model says (cold core, thicker melt)
- Heater sits at 100%
- Extruder skips

Sweep the flow up and find the knee. Run at some margin below it (80%?).

Flipped around, at steady flow the heater power tells me the actual flow:

```math
Q \approx \frac{P_{heater} - P_{loss}(T,\ \text{fan})}{\rho\,c\,(T_{nozzle} - T_{fil})}
```

MPC already models $P_{loss}$, so that's a free, crude flow sensor.

## Bead

Orca models a line as a rectangle with round ends:

```math
A = (w - h)\,h + \frac{\pi h^2}{4}
```

Line width $w$ comes from the nozzle, layer height $h$ is a choice, and the commanded extrusion
follows from $A$. Not tuned.

**Flow residual from mass:** once $d_f$ and density are known, weigh a print:

```math
f = \frac{m_{measured}}{\rho\,V_{commanded}}
```

$V_{commanded}$ comes from the G-code. A scale replaces the flow cube. Density and the real
filament area come off the scale too ([filament](filament.md#weigh-a-meter-true-cross-section)).

## Dimensions

A test part with outside widths and holes at several sizes:

```math
x_{meas} = s\,x_{nom} + 2b \quad \text{(outside)}, \qquad x_{meas} = s\,x_{nom} - 2b \quad \text{(holes)}
```

Least squares over all the features gives both at once:

- $s$ from the **slope**: shrinkage (or axis scale)
- $b$ from the **offset**, which flips sign between outsides and holes: the bead is wider or narrower than the model thinks

One print, two parameters, no guessing which knob caused what. Separate $s_{xy}$ and $s_z$. Skew
stays with Calilantern.

Shrinkage is roughly the material's expansion times how far it cools after it sets:

```math
\frac{\Delta L}{L} \approx \alpha\,(T_{set} - T_{room})
```

and the chamber changes when it sets, so $s$ is keyed by material **and** chamber mode.

## Cooling

Heat leaving the last layer:

```math
\dot{q} = h(\text{fan})\,A\,(T_{part} - T_{chamber})
```

A hot chamber shrinks the driving difference. ABS against a Tg around 105 °C: about 80 K of margin
in a 25 °C room, about 35 K in a 70 °C chamber. Same fan percentage, roughly half the cooling or
less. **Fan settings tuned cold don't carry over to 70 °C.** Better to describe cooling as the
cooling rate needed, and turn it into a fan percentage using the actual chamber temperature.

It's also a trade-off with layer adhesion: overhangs want the layer cold fast, strength wants the
interface hot. A hot chamber is what lets both happen.

## Z drift and soak

Frame drift and the predictive soak are in [slicer.md](../slicer.md#soak-stop-guessing). Chamber
heat balance is in the [roadmap](../roadmap.md#how-much-heater).

## Motion

Shaper limits and why they scale with stiffness and mass: [input shaper](../tuning/input-shaper.md).
The link to everything else: corner quality depends on the shaper's smoothing, the accel, and PA
together. Shaper first, then PA at the accel I actually print at.

## Couplings

Where knobs secretly fight each other, and the order that untangles them:

| Coupled | How | Untangle by |
|---|---|---|
| PA ↔ retraction | Retraction covers for bad PA | PA first, retraction after |
| Flow ↔ line width ↔ dimensions | All three move the outside of the part | Flow chain by mass, then contour offset by dimensions |
| Temperature ↔ PA, max flow, ooze | Viscosity drives all three | Identify viscosity, derive the rest |
| Z offset ↔ first-layer flow | Both set the squish | Z by sensor (autoz / load cell), flow from the chain |
| Shaper ↔ accel ↔ corners ↔ PA | Smoothing rounds corners, PA bulges them | Shaper, then PA at print accel |
| Cooling ↔ chamber ↔ adhesion | Hotter chamber, less cooling, better layers | Cooling by needed rate, not fan % |
