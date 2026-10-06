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

- **Longer melt zone, more flow.** Volcano, UHF, and so on. $`Q_{max}`$ scales with $`L`$, up to a point: past some length the molten column's own resistance wins (chapter 4)
- **Splitting the filament multiplies it.** CHT-style and "high flow" nozzles split the melt into $`N`$ thinner streams. Each stream gets its own $`\alpha L`$ budget, so ideally $`Q_{max}`$ goes up by $`N`$. In practice less, since they share the heat going in
- **Filament diameter drops out,** at least in this crude version. Surprising, but it falls out of the math: a fatter filament has more area but needs more time
- **Material matters through $`\alpha`$.** Carbon fiber fillers conduct heat better, so CF filaments can melt faster than their base plastic

[Phan, Swain & Mackay (2018)](https://doi.org/10.1122/1.5022982) did this properly with a Nusselt vs
Graetz correlation built from pressure data. My version is the back-of-envelope cousin. The useful
thing about it: fit $`Gz^{\ast}`$ once with a known filament, and you can predict roughly how a longer
melt zone or a different material changes max flow before buying anything.

## Inside the melt zone

The Graetz number says whether the core gets hot in time. The full solution says how hot every part
of it gets, and that's what the nozzle actually receives. Treat the filament (radius $`R`$) as a plug
moving through a bore whose wall sits at $`T_w`$ (a 1.75 mm bore, so the filament touches the wall;
real bores are bigger, see "The bore isn't 1.75 mm"), and let $`\theta = (T_w - T)/(T_w - T_{in})`$, so 1
is still cold and 0 is at wall temperature. The classic solution is a Bessel series:

```math
\theta(r, z) = \sum_{k} \frac{2}{\lambda_k J_1(\lambda_k)}\,J_0\!\left(\frac{\lambda_k r}{R}\right) e^{-\lambda_k^2 Fo}, \qquad \bar\theta = \sum_k \frac{4}{\lambda_k^2}\,e^{-\lambda_k^2 Fo}
```

$`\lambda_k`$ are the zeros of $`J_0`$ (2.405, 5.520, 8.654...), $`\bar\theta`$ is the average across the
bore, and $`Fo = \pi\alpha z/Q`$ as above. The thing to notice: **$`L`$ and $`Q`$ only ever show up
together, as $`L/Q`$.** Doubling the melt zone and halving the flow give the same temperature profile.

What leaves a melt zone for ABS ($`\alpha = 0.08`$ mm²/s, wall at 250 °C, filament entering at 50 °C):

| $`Fo`$ at the exit | Example | Mean | Core | Viscosity, mean vs wall | Core vs wall |
|---|---|---|---|---|---|
| 1.0 | 20 mm at 5 mm³/s | 249.6 °C | 249.0 °C | 1.02× | 1.04× |
| 0.5 | 20 mm at 10 mm³/s | 242 °C | 233 °C | 1.4× | 2.3× |
| 0.25 | 10 mm at 10, or 20 at 20 | 218 °C | 175 °C | 5.3× | about 150× |
| 0.13 | 10 mm at 20 mm³/s | 183 °C | about 100 °C | about 70× | still solid |

Viscosities use Seppala's ABS fit from chapter 6, which is extrapolated well below its range for the
core, so read those as orders of magnitude. The knee is around $`Fo \approx 0.3`$, which puts
$`Gz^{\ast}`$ near 10. Above it the melt is close to uniform. Below it you don't have a melt, you have
a stiff core inside a runny sleeve. Two things push the whole table toward the cold end: latent heat
in semi-crystalline plastics (effectively $`T_{in}`$ drops by $`X\,\Delta H_m/c`$), and a wall that
isn't really at the setpoint (the heat path below).

![Temperature across the bore at the exit of the melt zone, for four Fourier numbers](figures/melt-profile.svg)

*At Fo = 0.25 the core is 75 K below the wall. At 0.13 it's still sitting near the glass transition.*

## Seen from the inside

The experiments back the picture. [Kattinger et al. (2023)](https://doi.org/10.1016/j.addma.2023.103762) X-rayed a running hot
end and found less of the nozzle wall in contact with melt at higher feed rates, while the heater
temperature made no visible difference to how much of the nozzle was full. [Osswald et al.
(2018)](https://doi.org/10.1016/j.addma.2018.04.030) modeled the fast extreme, where the filament barely melts on the way down
and instead melts through a thin film where it's pressed into the cone.

**What leaves the nozzle (theory).** Laminar flow keeps streamlines in order through the cone, so
the extrudate should come out with the hottest plastic on the outside and the coolest in the middle.
That's good for the weld, since the surface touching the layer below is the hot part. But a stiff,
elastic core should swell more coming out and lock in more stress.

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
hold the melt where I want it. [Coogan & Kazmer (2019)](https://www.researchgate.net/publication/330031420_In-line_rheological_monitoring_of_fused_deposition_modeling) already turned a nozzle into
an in-line rheometer with a pressure transducer and a thermocouple, and temperature inaccuracy was one
of the corrections that mattered most. Running it backwards, from viscosity to temperature, is the part
I haven't seen.

## The nozzle is part of the heat path

The thermistor sits in the block, the plastic is in the nozzle. In between, heat has to cross the
thread joint and the nozzle wall, and each one is a thermal resistance:

```math
T_{melt} \approx T_{block} - P_{fil}\left(R_{contact} + R_{nozzle}\right), \qquad R_{nozzle} \approx \frac{L}{k\,A}
```

$`P_{fil}`$ is the power going into the plastic (about 7 W for ABS at 15 mm³/s, from the bookkeeping
above), and $`k`$ is the nozzle's conductivity:

| Nozzle | $`k`$ (rough, W/m·K) |
|---|---|
| Copper alloys | 300 to 390 |
| Silicon carbide | 120 to 200 |
| Brass | about 115 |
| Tungsten carbide | 80 to 110 |
| Ruby tip (brass body) | 35 to 40 |
| Hardened steel | 20 to 30 |

Steel conducts four to five times worse than brass, so wherever heat has to travel through the
nozzle itself, steel's drop is four to five times bigger (where that is gets worked out below). The
community tests agree. [CNC Kitchen](https://www.cnckitchen.com/blog/prusament-pc-blend-review)
got **73% stronger** PC Blend layers with brass than steel at the same 275 °C, and
[MyTechFun](https://mytechfun.com/video/308) saw steel give about a third of brass's layer adhesion.
Same setpoint, cooler melt, weaker welds (chapter 6).

Two things follow. **Matching max flow doesn't mean matching melt temperature:** a flow test shows
when the extruder gives up, not how hot the plastic was when it got through. And the thread joint
matters less than I first thought (next section), but a real high-temperature paste like
[Slice's boron nitride paste](https://www.sliceengineering.com/products/boron-nitride-paste) still
earns its place on the heater cartridge and thermistor, where contact decides how fast and how
honestly the controller sees the block. Regular CPU paste is made for 150 to 180 °C and bakes out at ABS
temperatures, metal-filled pastes don't belong near the thermistor or heater, and liquid metal
attacks aluminum blocks.

Orca and Bambu Studio ask for your nozzle material, but as far as I can tell only to warn about
abrasive filament. Nothing offsets the temperature. After a nozzle swap I'd recalibrate MPC (chapter 9)
and test hotter.

## Where the heat path actually bites

There are two places heat can get stuck, and they behave completely differently.

**Inside the block,** heat goes radially through the threads and the nozzle wall into the plastic.
That makes the wall a convective boundary, and the eigenvalues from "Inside the melt zone" become the
roots of $`\lambda J_1(\lambda) = Bi\,J_0(\lambda)`$, where $`Bi = hR/k_p`$ compares the wall's conductance
to the plastic's. Plastic conducts about 0.17 W/m·K, over a hundred times worse than even steel, so
$`Bi`$ is huge and barely matters:

| Wall | $`Bi`$ | Melting rate vs a perfect wall |
|---|---|---|
| Brass nozzle | about 540 | 99.6% |
| Hardened steel nozzle | about 120 | 98.3% |
| Dry threads, poor contact | about 46 | 95.8% |
| Steel and a poor dry joint | about 33 | 94% |

The plastic is its own bottleneck. Worst case, it's like losing about 6% of the melt zone. I didn't expect
that. The clearance around the filament matters far more (two sections down).

**Below the block,** the cone and tip stick out into the part fan. That's a fin: heat comes down from
the block and the fan pulls it off the sides. For a stick-out $`L_f`$ of radius $`r_f`$:

```math
\Delta T_{tip} = (T_{block} - T_{air})\left(1 - \frac{1}{\cosh(m L_f)}\right), \qquad m = \sqrt{\frac{2h}{k\,r_f}}
```

For 4 mm of stick-out, $`r_f = 2`$ mm and a 250 °C block:

| Tip cooling | Copper | Brass | Tungsten carbide | Hardened steel |
|---|---|---|---|---|
| Silicone sock ($`h \approx 25`$) | 0.1 K | 0.4 K | 0.5 K | 1.7 K |
| Fan, moderate ($`h \approx 200`$) | 1.0 K | 2.9 K | 3.7 K | 12.8 K |
| Fan, hard ($`h \approx 500`$) | 2.4 K | 7.1 K | 9.0 K | 29.6 K |

![How far the nozzle tip drops below the block, against cooling on the tip, for four nozzle materials](figures/tip-fin.svg)

*Under a sock, nothing matters much. Under a hard fan, steel's tip drops four times as far as brass's.*

The melt also draws its last heat through that stretch: $`L_f/(k\pi r_f^2)`$ is about 2.8 K/W in brass
and 12.7 K/W in steel, so every 2 W the plastic still needs costs 5.5 K or 25 K. The $`h`$ values are
rough guesses, but the ratios aren't. **Steel's penalty lives at the tip:** the cone, the orifice and
the flat land that presses the bead down, which is right where the weld gets made. It also means a
silicone sock does more for a steel nozzle than any paste.

## The bore isn't 1.75 mm

All the math above assumes the filament fills the bore. It doesn't. All-metal heatbreaks and nozzle
inlets for 1.75 mm filament are nominally about 2 mm, at least the V6-style parts and MK8-style
nozzles. Bambu, Revo, Dragon and Rapido don't publish their bores. I might check the Conch with gauge pins
at some point and add the number here. That clearance fills with melt, and it does three things.

**It insulates.** The film is plastic, the same weak conductor as the core, in series with it. For a
concentric film the Biot number depends only on the geometry, not the material:

```math
Bi = \frac{1}{\ln(R_{bore}/R_f)}
```

| Bore | Gap per side | $`Bi`$ | Melting rate | Melt zone needed to match |
|---|---|---|---|---|
| 1.80 mm | 25 µm | 36 | 94% | 1.06× |
| 1.90 mm | 75 µm | 12 | 85% | 1.18× |
| 2.00 mm | 125 µm | 7.5 | 77% | 1.30× |
| 2.10 mm | 175 µm | 5.5 | 71% | 1.42× |

A 2 mm bore costs about as much as 30% of melt zone length, which dwarfs the nozzle material inside
the block. In this model the knee for a 20 mm zone drops from about 17 to 13 mm³/s for ABS. The
filament usually rides against one side rather than sitting centered, so the real penalty should be
somewhat smaller than the concentric number. Then again, Kattinger's X-rays found less of the wall in
contact with melt at higher feed rates, so at speed part of that gap may not be melt at all.

**It adds slow volume.** A 2 mm bore holds about 30% more melt than the filament itself, and all of it
is the slow layer at the wall, which is exactly what makes purging take a while (below).

**It leaks backward.** Pressure pushes melt up the gap toward the cold zone, and flow through a thin
annular gap of width $`\delta`$ goes as its cube:

```math
q_{back} \approx \frac{\pi D\,\delta^3}{12\,\eta}\,\frac{dP}{dz}
```

A 1.9 mm bore leaks about a fifth of what a 2.0 mm one does. That backflow freezing in the heatbreak
is the classic jam. Going tighter isn't free either: filament tolerance (often ±0.05 mm), ovality and
thermal swelling (about 0.016 mm at 100 K above room) all eat the clearance. 2 mm is where the
published parts land, and it costs real melting capacity. [Serdeczny et al. (2020)](https://doi.org/10.1016/j.addma.2020.101454)
simulated an ABS hot end and found a recirculation region right in this gap, between the wall and the
incoming filament, and to match their feeding force measurements they had to back out a thermal
resistance at the wall.

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

## How long plastic stays in

Not everything leaves at the same time. Once it's molten, plastic sticks to the wall, so the layer
next to the wall barely moves while the middle runs ahead. For a power-law melt, with $`\xi = r/R`$:

```math
u(\xi) = \bar u\,\frac{3n+1}{n+1}\left(1 - \xi^{(n+1)/n}\right)
```

The first new plastic shows up after pushing $`(n+1)/(3n+1)`$ of the zone's volume $`V_z`$ (0.64 for
$`n = 0.4`$), and the old plastic tails off slowly. For a Newtonian melt the old fraction in what comes
out after pushing $`V`$ is exactly

```math
c_{old} = \left(\frac{V_z}{2V}\right)^2, \qquad V \ge V_z/2
```

and $`n = 0.4`$ is close:

| Volume pushed | 1 $`V_z`$ | 2 $`V_z`$ | 3 $`V_z`$ | 5 $`V_z`$ |
|---|---|---|---|---|
| Old plastic in the outflow | 24% | 5% | 2.2% | 0.8% |

![Fraction of old plastic in the outflow against volume pushed through, Newtonian and shear-thinning](figures/washout.svg)

*Every extra zone volume buys less. Shear thinning flattens the profile and helps a little.*

Getting under 2% takes about 3.2 zone volumes: roughly 75 mm³ for a 10 mm melt zone with a 1.75 mm
bore, 230 mm³ for 30 mm. A real 2 mm bore adds about 30%, all of it the slow kind. That's the same
order as the flush volumes slicers use for color changes, and it scales with the melt zone, so a long high-flow hotend pays for its flow on every swap. Dead
pockets, like a gap between the nozzle and the heat break, add an even longer tail. That slow layer at
the wall also sits hot far longer than the average transit time, which is my guess for where
discolored, degraded plastic comes from.

The tail also explains a purge rule of thumb. [Polymaker's guide](https://wiki.polymaker.com/the-basics/fun-3d-printing-facts/reduce-purge-waste) puts black to
white at 250 to 300 mm of filament and white to black at 60 to 80, about 4× apart. From
$`c = (V_z/2V)^2`$, the volume needed goes as $`1/\sqrt{c}`$, so 4× more purge means the eye catches
about 16× less black in white than white in black. That sounds about right to me (theory).

## What I'd love to measure first

These are the experiments I'm most curious about, if time allows:

- The flow ladder with heater power and block temperature logged at each step: which wall comes first, and where
- The same ladder on two hotends with the same anchor filament: how much a longer melt zone actually buys, and whether the pressure slope climbs past $`q^{0.4}`$ near $`Fo \approx 0.3`$ like the model says
- A thermal camera on the nozzle tip with and without the silicone sock, brass against steel, to check the fin numbers
- Heater power vs flow during normal prints, against the energy equation: does the slope match the material?
- Brass, tungsten carbide and hardened steel nozzles in the same hotend, each with and without boron nitride paste: the flow ladder plus Z coupons at the same setpoint, to see how much is the melt and how much is the joint

## References

- [Go, Schiffres, Stevens, Hart (2017)](https://www.sciencedirect.com/science/article/abs/pii/S2214860416302834). Rate limits of FFF: extruder force, heat transfer, motion
- [Go, Hart (2017)](https://arxiv.org/abs/1709.05918). Fast desktop-scale extrusion with a screw and laser heating
- [Phan, Swain, Mackay (2018)](https://doi.org/10.1122/1.5022982). Rheology and heat transfer in FFF, Nusselt vs Graetz
- [Anderegg et al. (2019)](https://www.researchgate.net/publication/330392702_In-Situ_Monitoring_of_Polymer_Flow_Temperature_and_Pressure_in_Extrusion_Based_Additive_Manufacturing). Pressure and melt temperature in the flow
- [Kapusuzoglu, Sato, Mahadevan, Witherell (2026)](https://arxiv.org/abs/2608.18431). ABS bond quality optimization; filament came out 40 to 50 °C below a 260 °C setpoint
- [Kattinger, Kornely, Ehrler, Bonten (2023)](https://doi.org/10.1016/j.addma.2023.103762). X-ray CT of melting inside a running hot end
- [Osswald, Puentes, Kattinger (2018)](https://doi.org/10.1016/j.addma.2018.04.030). Melting model with a thin film at the filament tip
- [Serdeczny, Comminal, Mollah, Pedersen, Spangenberg (2020)](https://doi.org/10.1016/j.addma.2020.101454). CFD of the hot end: recirculation in the gap, wall thermal resistance
- [Coogan, Kazmer (2019)](https://www.researchgate.net/publication/330031420_In-line_rheological_monitoring_of_fused_deposition_modeling). An in-line rheometer built into the nozzle
- [Polymaker, reduce purge waste](https://wiki.polymaker.com/the-basics/fun-3d-printing-facts/reduce-purge-waste). Purge lengths for different color changes
- [Turner, Strong, Gold (2014)](https://www.semanticscholar.org/paper/A-review-of-melt-extrusion-additive-manufacturing-Turner-Strong/2f47b171bb818a99a3f1f3a4b652bdc0db682d19). Review of liquefier modeling
- [G-Code Flow Temperature Controller](https://github.com/sb53systems/G-Code-Flow-Temperature-Controller). Flow-dependent temperature as a post-processor
- [CNC Kitchen, Prusament PC Blend review](https://www.cnckitchen.com/blog/prusament-pc-blend-review). Brass vs steel nozzle at the same temperature: 73% stronger layers with brass
- [MyTechFun, hardened steel vs brass layer adhesion](https://mytechfun.com/video/308). About a third of the layer adhesion with hardened steel at the same temperature
- [Slice Engineering, boron nitride paste](https://www.sliceengineering.com/products/boron-nitride-paste). High-temperature, electrically insulating thermal paste for hotends
