# 4. Extrusion dynamics

*Level 3 to 4. This is where it turns into control theory.*

## The problem in one sentence

The extruder pushes filament in, but plastic comes out late, and keeps coming out after the
extruder stops.

Every corner bulge, every zit at a seam, every gap after a travel move comes from that one
sentence. So let's model it.

## A spring and a resistor

Between the drive gears and the nozzle tip, the system stores a bit of plastic under pressure.
Filament squishes, the melt compresses, things flex. Call that **compliance** $`C`$: push in a little
extra volume and the pressure goes up by $`dP = dV/C`$. Meanwhile the nozzle resists flow. For now,
assume flow out is just pressure over a resistance $`R`$.

Volume in minus volume out equals volume stored:

```math
C\,\frac{dP}{dt} = q_{in} - q_{out}, \qquad q_{out} = \frac{P}{R}
```

Substitute and you get a first-order lag between what the extruder pushes and what comes out:

```math
\tau\,\frac{dq_{out}}{dt} = q_{in} - q_{out}, \qquad \tau = RC
```

That's an RC circuit, same as electronics. Start extruding at flow $`q_0`$ and the output creeps up:

```math
q_{out}(t) = q_0\left(1 - e^{-t/\tau}\right)
```

Stop, and it bleeds off:

```math
q_{out}(t) = q_0\,e^{-t/\tau}
```

The plastic missing at the start is exactly the plastic that oozes at the end, $`q_0 \tau`$. On a
direct drive, $`\tau`$ is usually tens of milliseconds. Tiny, but at 200 mm/s the toolhead covers
several millimeters in that time.

## What pressure advance does

If we know $`\tau`$, we can cheat: push a little extra while the flow is ramping up, and a little less
while it ramps down.

```math
q_{in} = q + \tau\,\frac{dq}{dt}
```

Plug that into the lag equation and $`q_{out} = q`$ exactly. In terms of extruder position $`e`$
(millimeters of filament):

```math
e_{cmd}(t) = e(t) + K\,\dot{e}(t), \qquad K = \tau
```

That's literally what Klipper does: the extruder position becomes the nominal position plus
pressure advance times the nominal extruder velocity (see the
[Kinematics doc](https://www.klipper3d.org/Kinematics.html)). $`K`$ is in seconds. **Pressure advance
isn't a magic tuning number, it's the time constant of your nozzle.**

During deceleration $`\dot e`$ drops, so the extruder actually pulls back a bit. That's why PA looks
like tiny retractions at every corner.

## Seeing it in the frequency domain

Same thing in Laplace terms. The nozzle is a first-order low-pass:

```math
G(s) = \frac{Q_{out}(s)}{Q_{in}(s)} = \frac{1}{\tau s + 1}
```

Pressure advance is a lead term:

```math
C(s) = 1 + K s \quad\Rightarrow\quad C(s)\,G(s) = \frac{1 + K s}{1 + \tau s} = 1 \ \text{when}\ K = \tau
```

It's an exact inverse of the plant. The catch: $`1 + Ks`$ is a differentiator, and a trapezoidal
velocity profile has sharp corners where acceleration jumps. Differentiate a jump and you ask the
extruder for infinite acceleration. So Klipper smooths the advance over a short window,
`pressure_advance_smooth_time` (40 ms by default). Smoothing is a low-pass, so the real system is
more like

```math
H(s) \approx \frac{(1 + K s)\,S(s)}{1 + \tau s}
```

with $`S(s)`$ the smoothing filter. It rounds off the corners of the compensation and adds a little
delay. Shorter smoothing tracks better but jerks the extruder harder. That's the trade.

**What wrong PA does.** During steady acceleration the flow ramps at a constant rate $`\dot q`$, and
the output settles to

```math
q_{out} = q - (\tau - K)\,\dot{q}
```

Too little PA ($`K < \tau`$) underextrudes while speeding up and overextrudes while slowing down,
which is the classic bulging corner. Too much does the opposite and leaves gaps.

How big is that? A 0.65 × 0.3 mm line at 5,000 mm/s² ramps the flow at about 975 mm³/s². If $`K`$
is off by just 0.01 s, that's about 10 mm³/s of error. At 150 mm/s the line itself is only about
29 mm³/s, so **a 10 ms PA error is a 30% flow error at the corners.** That's why PA matters more
the harder you accelerate.

![Flow out of the nozzle for no pressure advance, correct pressure advance and too much pressure advance](figures/pa-step-response.svg)

*Same nozzle, three PA settings. The dashed line is what the slicer asked for.*

## The nozzle's resistance, for a real melt

So far I assumed $`q_{out} = P/R`$, a constant resistance. Real melts shear-thin (chapter 2). For a
power-law melt through a round bore of radius $`R`$ and length $`L`$, the pressure drop works out to

```math
\Delta P = \frac{2 L K}{R}\left[\frac{(3n+1)\,Q}{n\,\pi R^3}\right]^{n}
```

Sanity check: with $`n = 1`$ (Newtonian, $`K = \mu`$) that becomes the classic Hagen-Poiseuille
$`8 \mu L Q / (\pi R^4)`$. Good.

Two things fall out:

- **Pressure goes as $`Q^n`$,** not linearly. Double the flow and pressure only goes up by $`2^n`$
- **Pressure goes as $`R^{-(1+3n)}`$.** For a Newtonian fluid that's the famous $`1/d^4`$. For $`n = 0.4`$ it's $`d^{-2.2}`$

That second one corrects something I wrote earlier in the calibration docs. I said a pressure sensor
could tell a 0.4 from a 0.6 nozzle because pressure goes as $`1/d^4`$, a 5× difference. For a
realistic shear-thinning melt it's more like $`(0.6/0.4)^{2.2} \approx 2.4`$×, and the melt zone and
taper add resistance that doesn't depend on the bore at all. Still easy to tell apart, just not 5×.

## Why PA changes with flow and temperature

Linearize the power law around whatever flow you're printing at. The incremental resistance is

```math
R_{inc} = \frac{dP}{dq} = n\,\frac{P}{q}
```

so the effective time constant is

```math
\tau_{eff} = C\,R_{inc} = C\,n\,\frac{P(q)}{q} \propto q^{\,n-1}
```

With $`n = 0.4`$, doubling the flow multiplies $`\tau_{eff}`$ by $`2^{-0.6} \approx 0.66`$. **Faster
printing needs less PA.** That's exactly what people found empirically, and it's why Orca added
[adaptive pressure advance](https://github.com/OrcaSlicer/OrcaSlicer/wiki/adaptive_pressure_advance_calib):
you run at least six PA tests at different flows and accelerations, and it fits a curve
through them.

![Pressure advance needed vs flow for three power-law indices](figures/pa-vs-flow.svg)

*The more a melt shear-thins (smaller n), the faster the PA it needs drops off with flow.*

Temperature does the same thing through the shift factor from chapter 2. The melt's consistency
$`K`$ scales with $`a_T`$, so

```math
\tau_{eff}(q, T) \approx \tau_0\left(\frac{q}{q_0}\right)^{n-1}\frac{a_T(T)}{a_T(T_0)}
```

Hotter means runnier, which means less PA.

Acceleration is the one I can't derive cleanly. Orca's testing says higher accel wants less PA too.
My guesses: the smoothing window becomes a bigger fraction of a short acceleration phase, and the
compliance itself is probably nonlinear (gear teeth bite deeper under load, so the spring stiffens).
I'd want pressure data before believing any of my explanations.

**Theory, untested:** the plumbing for variable PA already exists. Orca emits per-feature PA, and
Kalico has `per_move_pressure_advance`, which applies PA changes to moves already in the queue
instead of about 250 ms later. What's missing is the physics. If a pressure sweep gives me $`n`$ and
the temperature shift, the formula above gives PA everywhere from two numbers instead of a six-test
grid.

## Where the spring is

What actually makes up $`C`$? My list, roughly in order of how much I suspect each one matters on a
direct drive:

- **Gear teeth biting into the filament.** They bite deeper as the force goes up
- **Softened filament just above the melt,** which can bulge into the clearance of the bore
- **The filament column between the gears and the heatbreak** flexing in its clearance
- **The idler spring**
- **Melt compressibility.** Polymer melts have a bulk modulus around a GPa, so 50 mm³ of melt at 5 MPa only stores about 0.25 mm³

On a Bowden setup, the tube stretching and the long filament compressing dwarf all of that, which is
why Bowden PA values are several times bigger.

I haven't found anyone who measured cleanly which of these dominates on a direct drive. A pressure
sensor would settle it: $`C = \tau / R_{inc}`$, and $`\tau`$ and $`R_{inc}`$ both come straight off a
pressure trace.

## How much is actually stored

At steady flow the stored volume is

```math
V_s = C\,P = \tau\,q \quad \text{(linear case)}
```

With $`\tau = 0.04`$ s and $`q = 15`$ mm³/s that's 0.6 mm³, about **a quarter of a millimeter of
filament.** That's all the "pressure" there is.

Direct drive retractions are usually 0.4 to 1 mm. More than the stored pressure. So retraction is
doing a second job: covering melt that expands as it reheats when flow stops, gravity, steam from
wet filament, and the meniscus at the tip. And with PA on, most of the pressure is already gone by
the time the move ends. **If you tuned retraction without PA, your retraction is doing PA's job.**
That's why the order is PA first, retraction second.

## Seams are pressure transients

What happens at the end of a loop:

1. Decelerate. PA pulls back, pressure drops
2. Retract (maybe), wipe (maybe)
3. Travel. Whatever pressure is left oozes out, plus thermal expansion
4. Unretract
5. Accelerate. PA pushes extra, pressure builds back
6. Start the next loop, and hope the pressure is exactly right

Any error in that sequence shows up right at the seam as a zit, a blob, or a gap. Orca's
scarf joint seam attacks it with geometry: ramp
the layer height along the seam so the start and end overlap gradually and the error gets spread
out. [Wu, Qian & Okwudire (2023)](https://doi.org/10.1016/j.addma.2023.103850) attacked it with
control: they measured extrusion force with a servo extruder, modeled retraction and re-advance,
and built a feedforward for starts and stops.

**Theory, untested:** pressure-aware retraction. The PA model already knows the pressure state at
the moment the extrusion stops. Retract exactly what's left plus a learned ooze term, and unretract
exactly what's needed to land at the next loop's steady-state pressure. With a pressure sensor you
can check it on every single loop.

## Slip

The gears grip the filament with some maximum force. Extrusion force is pressure times filament
area, $`F = P A_f`$. As $`F`$ gets close to the grip limit the filament starts slipping a little, before
it outright skips. Slip doesn't announce itself, it just quietly underextrudes.

Greeff & Schilling (2017) measured the
real filament speed and closed the loop on slip. With an encoder (BDwidth, or the motion sensors
people already use for jam detection), the slip ratio is

```math
s = 1 - \frac{v_{actual}}{v_{cmd}}
```

and the fix is to command $`e/(1 - s)`$, up to a point. Past that point you're at the force wall from
chapter 3 and no amount of compensation helps. Klipper currently uses motion sensors for runout and
jam detection only. Nothing compensates slip.

## Diameter wobble

Area goes as diameter squared, so

```math
\frac{\Delta A}{A} = 2\,\frac{\Delta d}{d}
```

A ±0.02 mm wobble on 1.75 mm filament is ±2.3% flow. Klipper already compensates for this if you
have a width sensor: `hall_filament_width_sensor` reads the diameter and applies a flow correction
(`M221`) after the filament has traveled `measurement_delay` millimeters, the distance from the
sensor to the melt zone. So the "index by filament distance, not time" idea is already in there.
What it doesn't do: correct for slip, or see ovality with a single-axis sensor.

## What I'd like to build next

None of these exist on my machine yet, and some may never happen. They're the gaps I find most exciting, in the order I'd tackle them if time allows:

1. PA as a function of flow and temperature from a two-parameter physical model, fit from a pressure sweep
2. Pressure-aware retraction and unretraction
3. Slip compensation from an encoder
4. Melt temperature control instead of block temperature (chapter 3)
5. Closed-loop extrusion force, like the [ETH Zurich work](https://arxiv.org/abs/2403.16042), which used force to hold line width (chapter 5)

## References

- [Bellini, Güçeri, Bertoldi (2004)](https://orbit.dtu.dk/en/publications/liquefier-dynamics-in-fused-deposition/). The liquefier as a dynamic system
- [Tronvoll et al. (2019)](https://www.emerald.com/rpj/article/25/5/830/363878/Investigating-pressure-advance-algorithms-for). First academic look at advance algorithms
- [Wu, Qian, Okwudire (2023)](https://doi.org/10.1016/j.addma.2023.103850). Retraction and advancement modeling with feedforward
- Greeff, Schilling (2017). *Closed loop control of slippage during filament transport in molten material extrusion.* Additive Manufacturing 14
- [Guidetti et al. (2024)](https://arxiv.org/abs/2403.16042). Force controlled printing
- [Klipper: Pressure advance](https://www.klipper3d.org/Pressure_Advance.html) and [Kinematics](https://www.klipper3d.org/Kinematics.html)
- [Orca: adaptive pressure advance](https://github.com/OrcaSlicer/OrcaSlicer/wiki/adaptive_pressure_advance_calib)
- [Kalico](https://github.com/KalicoCrew/kalico) for `per_move_pressure_advance`
