# 3. Melting

*Level 2 to 3.*

## The hotend in one paragraph

The extruder gears push solid filament down through the heatbreak, a thin tube whose whole job is
to keep heat from creeping up, into the heater block. The block is hot, heat conducts into the
moving filament, the filament melts from the outside in, and the melt gets pushed out the nozzle.
The thermistor sits in the block. **It measures the metal, not the plastic.** Keep that in mind,
it comes back a lot.

## Heat creep

If heat leaks up the heatbreak, the filament softens before it's supposed to. Soft filament swells,
drags on the walls, and eventually jams. The heatbreak's heatsink and fan are what stop that.

This matters a lot for a hot chamber. The hotend fan cools the heatsink with chamber air, and its
cooling power goes roughly with the temperature difference between the heatsink and that air. At
70 °C chamber air there's much less difference to work with. PLA softens around 60 °C, so **PLA in
a 70 °C chamber is asking for heat creep jams.** That's one of several reasons the chamber modes in
[slicer.md](../calibration/slicer.md#chamber-modes) keep PLA cool. High-temperature plastics soften much higher,
so they don't care.

## How long it takes heat to get in

Heat conducts into the filament over a time that scales with the radius squared over the thermal
diffusivity:

```math
t_{cond} \sim \frac{r^2}{\alpha}, \qquad \alpha = \frac{k}{\rho\,c}
```

Common plastics have $`\alpha`$ around 0.06 to 0.11 mm²/s. For 1.75 mm filament ($`r = 0.875`$ mm)
that's on the order of 10 seconds for the center to fully catch up. The center doesn't have to reach
nozzle temperature, just get soft enough to flow, so call it a few seconds in practice.

Now compare that to how long the plastic actually spends in the hot zone. With a heated length $`L`$:

```math
t_{res} = \frac{L\,A_f}{Q}
```

For a 30 mm melt zone and 1.75 mm filament ($`A_f \approx 2.4`$ mm²):

| Flow | Time in the hot zone |
|---|---|
| 10 mm³/s | 7.2 s |
| 20 mm³/s | 3.6 s |
| 40 mm³/s | 1.8 s |

Somewhere around 20 mm³/s the middle of the filament stops getting enough time. That's why normal
hotends top out in the 15 to 30 mm³/s range, and why it's a heat problem, not a motor problem.

![Time the plastic spends in the hot zone vs flow, for three melt zone lengths, against the time the core needs](figures/melt-time.svg)

*Where each curve drops into the shaded band is roughly where that melt zone runs out of time.*

## The Graetz number

Put those two times together. The Fourier number (how far the heat got) is

```math
Fo = \frac{\alpha\,t_{res}}{r^2} = \frac{\pi\,\alpha\,L}{Q}
```

and its flipped version is the Graetz number, which compares how fast stuff flows through to how
fast heat conducts in:

```math
Gz = \frac{Q}{\alpha\,L}
```

Melting keeps up while $`Gz`$ stays under some critical value $`Gz^{\ast}`$, so per melt channel:

```math
Q_{max} \approx Gz^{\ast}\,\alpha\,L
```

That little formula explains most hotend marketing:

- **Longer melt zone, more flow.** Volcano, UHF, and so on. $`Q_{max}`$ scales with $`L`$
- **Splitting the filament multiplies it.** CHT-style and "high flow" nozzles split the melt into $`N`$ thinner streams. Each stream gets its own $`\alpha L`$ budget, so ideally $`Q_{max}`$ goes up by $`N`$. In practice less, since they share the heat going in
- **Filament diameter drops out,** at least in this crude version. Surprising, but it falls out of the math: a fatter filament has more area but needs more time
- **Material matters through $`\alpha`$.** Carbon fiber fillers conduct heat better, so CF filaments can melt faster than their base plastic

[Phan, Swain & Mackay (2018)](https://doi.org/10.1122/1.5022982) did this properly with a Nusselt vs
Graetz correlation built from pressure data. My version is the back-of-envelope cousin. The useful
thing about it: fit $`Gz^{\ast}`$ once with a known filament, and you can predict roughly how a longer
melt zone or a different material changes max flow before buying anything.

## Energy bookkeeping

The heater has to pay for two things: losses to the air and fans, and heating the plastic going
through.

```math
P_{heater} = P_{loss}(T,\ \text{fan}) + \rho\,Q\left[c\,(T_{n} - T_{f}) + X\,\Delta H_m\right]
```

The last term only matters for semi-crystalline plastics: $`X`$ is how crystalline the filament is
and $`\Delta H_m`$ is the heat it takes to melt those crystals.

Some numbers to get a feel:

| Plastic | Flow | Nozzle | Power for the plastic |
|---|---|---|---|
| PLA | 20 mm³/s | 210 °C | about 8 W |
| PETG | 30 mm³/s | 240 °C | about 18 W |

A typical hotend heater is 40 to 70 W, and losses eat 10 to 20 W of that at temperature. So there's
usually headroom on paper. **The heater rarely runs out first. Heat transfer into the core does.**

## The block isn't the melt

[Anderegg et al. (2019)](https://www.researchgate.net/publication/330392702_In-Situ_Monitoring_of_Polymer_Flow_Temperature_and_Pressure_in_Extrusion_Based_Additive_Manufacturing)
put a thermocouple and a pressure sensor right in the melt flow. The melt temperature dropped at
higher flow rates while the block happily sat at its setpoint. So the "nozzle temperature" in your
slicer is really "block temperature." At high flow, the plastic coming out is cooler than you think.

How much cooler? [Kapusuzoglu et al. (2026)](https://arxiv.org/abs/2608.18431) printed ABS through
a 0.8 mm nozzle in an enclosed printer, and at the printer's 260 °C limit the filament came out
roughly 40 to 50 °C below the setpoint. That's a big nozzle and a lot of plastic, so it's close to
the worst case, but it's the same story: the number on the screen is a heater setting, not a melt
temperature.

Which means it makes sense to run hotter when flowing more. There's already a post-processing
script that does exactly that:
[G-Code Flow Temperature Controller](https://github.com/sb53systems/G-Code-Flow-Temperature-Controller),
which ties nozzle temperature to volumetric flow (their example: 190 °C at 1 mm³/s, 220 °C at 15,
235 °C at 22). Nobody has built it into a mainstream slicer or firmware that I know of.

**Theory, untested:** I'd rather control the *melt* temperature than the block temperature. With a
pressure sensor and a viscosity model (chapter 2), measured pressure at a known flow tells me the
effective viscosity, and inverting the temperature shift gives an effective melt temperature. **The
pressure sensor becomes a melt thermometer.** Then the block target can be whatever it takes to
hold the melt where I want it.

## Two ways to hit the wall

| | Thermal limit | Heat transfer / force limit |
|---|---|---|
| What runs out | Heater power | Time for heat to reach the core |
| Block temperature | Drops | Holds steady |
| Pressure | Rises a bit | Spikes (cold, thick core) |
| What you see | Temperature droop, then underextrusion | Extruder clicking or skipping, matte rough strands |
| What helps | Bigger heater, MPC feedforward | Longer melt zone, HF nozzle, hotter, slower |

The [flow ladder](../calibration/filament.md#flow-ladder-by-mass) logs both at once, so it tells you
which wall you hit.

## Where MPC fits

Kalico's MPC (chapter 9) knows the flow coming from the planned moves and adds heater power before
the temperature drops. That fixes the thermal limit's droop. It can't fix the heat transfer limit,
because that's about time and distance, not power. Different problems, different fixes.

## The printer as a calorimeter

**Theory, untested.** That energy equation is also a measurement. At steady flow, the slope of heater
power against flow is

```math
\frac{dP_{heater}}{dQ} = \rho\left[c\,(T_n - T_f) + X\,\Delta H_m\right]
```

If $`\rho`$ and $`c`$ are known, the slope tells me $`X`$: how crystalline the filament came off the spool.
That varies by brand (PLA especially) and changes how it melts and prints. A printer is already a
crude differential scanning calorimeter. I haven't seen anyone use it that way.

## What I'd love to measure first

None of this is set up yet. These are the experiments I'm most curious about, if time allows:

- The flow ladder with heater power and block temperature logged at each step: which wall comes first, and where
- The same ladder on two hotends with the same anchor filament: how much a longer melt zone actually buys
- Heater power vs flow during normal prints, against the energy equation: does the slope match the material?

## References

- [Go, Schiffres, Stevens, Hart (2017)](https://www.sciencedirect.com/science/article/abs/pii/S2214860416302834). Rate limits of FFF: extruder force, heat transfer, motion
- [Go, Hart (2017)](https://arxiv.org/abs/1709.05918). Fast desktop-scale extrusion with a screw and laser heating
- [Phan, Swain, Mackay (2018)](https://doi.org/10.1122/1.5022982). Rheology and heat transfer in FFF, Nusselt vs Graetz
- [Anderegg et al. (2019)](https://www.researchgate.net/publication/330392702_In-Situ_Monitoring_of_Polymer_Flow_Temperature_and_Pressure_in_Extrusion_Based_Additive_Manufacturing). Pressure and melt temperature in the flow
- [Kapusuzoglu, Sato, Mahadevan, Witherell (2026)](https://arxiv.org/abs/2608.18431). ABS bond quality optimization; filament came out 40 to 50 °C below a 260 °C setpoint
- [Turner, Strong, Gold (2014)](https://www.semanticscholar.org/paper/A-review-of-melt-extrusion-additive-manufacturing-Turner-Strong/2f47b171bb818a99a3f1f3a4b652bdc0db682d19). Review of liquefier modeling
- [G-Code Flow Temperature Controller](https://github.com/sb53systems/G-Code-Flow-Temperature-Controller). Flow-dependent temperature as a post-processor
