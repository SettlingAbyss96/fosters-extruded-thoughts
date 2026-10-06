# Borrowed from other fields

Almost every problem on this list got solved somewhere else first, by people with way bigger
budgets. Worth stealing.

## Injection molding

Molders fight lot-to-lot resin variation every day. That's the brand-to-brand filament problem
with more money on the line.

- **Viscosity check in the machine.** "Scientific molding" runs a viscosity curve on the press itself (injection pressure vs fill time at a few speeds) and picks settings where viscosity changes hurt the least. That's the [flow ladder](../calibration/filament.md#flow-ladder-by-mass), and with a pressure sensor it's the cool-down sweep from [Read et al.](control.md#the-closest-thing-to-what-i-want)
- **Adjust every shot.** [ENGEL iQ weight control](https://www.engelglobal.com/en/us/digital-solutions/digital-solutions-injection-molding-manufacturing-process/optimize-plastic-viscosity) compares each shot's injection pressure curve to a reference and adjusts the switchover point and holding pressure to keep the injected volume the same. ENGEL claims 85% less part weight variation
- **Run in the middle of the window.** Find the edges of the process window, then sit in the middle, not at the edge where it's fastest

For this printer: with bd_pressureE, compare the pressure during a print to the reference for that
filament, and adjust temperature or flow to stay on it. That's "the filament is a bit different
today" handled live instead of by retuning.

## Filament and pipe extrusion lines

The factories that make filament measure diameter with laser micrometers and close a loop on the
puller speed. Melt pumps decouple output from viscosity, and melt pressure sensors sit everywhere.

For this printer: BDwidth is the laser micrometer. Its reading is for filament that hasn't reached
the nozzle yet, and the delay depends on flow:

```math
t_d = \frac{L_{path}}{v_f}, \qquad v_f = \frac{Q}{A_f}
```

100 mm of path at 10 mm³/s is about 24 seconds. So the correction has to be indexed by **filament
length, not time.** Turns out Klipper already does exactly that: `hall_filament_width_sensor`
applies its correction after the filament has moved `measurement_delay` millimeters, the distance
from the sensor to the melt zone. What it doesn't do is correct for slip, which an encoder on the
same filament path could add.

## Semiconductor fabs: run-to-run control and SPC

*The math: [handbook chapter 10](../handbook/10-sensing-estimation.md#learning-across-prints).*

Fabs adjust a recipe between runs based on measurements of the last run.
Sachs, Hu & Ingolfsson (1995) built the standard version: EWMA updates, a double EWMA to follow
slow drift, and SPC to decide whether a measurement is worth reacting to. Fabs also do "virtual
metrology": predict the measurement from machine sensor data so they don't have to measure every
wafer.

For this printer:

- The learning loop in [library.md](../calibration/library.md#every-print-is-a-test) is a run-to-run controller
- Double EWMA for slow drift, like nozzle wear
- Virtual metrology: predict flow residual from heater power and pressure instead of weighing every print. Weigh occasionally to keep the prediction honest

## Chemometrics: calibration transfer

A calibration built on one spectrometer doesn't work on the next one, even the same model.
[Wang, Veltkamp & Kowalski 1991](https://pubs.acs.org/doi/10.1021/ac00023a016) fixed that by
measuring a handful of standard samples on both instruments and fitting a mapping between them
(direct and piecewise direct standardization). It's still standard practice.

For this printer: Bambu's data is the "master instrument," this printer is the new one, the anchors
are the standard samples. For a ratio-type parameter, the mapping is one number:

```math
\hat{h} = \exp\left(\frac{1}{N}\sum_{a=1}^{N} \log\frac{y_{here}(a)}{y_{src}(a)}\right)
```

The spread of those log ratios is how much to trust it.

## Recommender systems

Netflix-style recommenders fill a mostly-empty users × movies table by assuming it's low rank
(Koren, Bell & Volinsky 2009, matrix factorization). Filaments × machines × settings is the same
kind of table: everybody has tested a few filaments on their own machine.

For this printer: the ratio assumption is the rank-1 version (a filament factor times a machine
factor). If a shared database ever happens, matrix factorization is how it gets filled
([library](../calibration/library.md#later-a-shared-library)).

## Statistics

*The math: [handbook chapter 10](../handbook/10-sensing-estimation.md#libraries-are-hierarchies).*

**Hierarchical models** (Gelman et al., *Bayesian Data Analysis*). Family → line → color → spool is
textbook partial pooling. A line's estimate is pulled toward its family when there's little data,
and trusts its own data when there's a lot:

```math
\hat\theta_{line} = \frac{n\,\bar{y}/\sigma^2 + \theta_{family}/\tau^2}{n/\sigma^2 + 1/\tau^2}
```

$`n`$ measurements with noise $`\sigma`$, family spread $`\tau`$. One weird spool doesn't drag the whole
line around, and a new color of a known line starts with a tight guess.

**Design of experiments.** Box & Wilson (1951) response surfaces, factorial designs. Taguchi
designs are all over the FFF papers: fine for screening, bad at catching interactions.

**Pairwise comparisons.** Bradley & Terry (1952) turn "A looks better than B" into scores:

```math
P(i \succ j) = \frac{e^{s_i}}{e^{s_i} + e^{s_j}}
```

Brochu, de Freitas & Ghosh (2007) used that inside Bayesian optimization to pick which pair to
compare next. For seams and surface looks, where I'm the only sensor: compare two prints, click
the better one, and the optimizer picks the next pair. Way less effort than rating everything.

## Metrology

- **Check standards and control charts:** the anchors, rerun monthly ([filament](../calibration/filament.md#compare-dont-start-from-scratch))
- **Gauge R&R:** how much of the spread is the measurement instead of the part. I'd run the same anchor twice before trusting any difference
- **Round robins** (ISO 5725): several labs measure the same reference material. Shared anchors across printer owners would be exactly that
- **Reference materials:** Prusament's per-spool data is the closest thing the hobby has

**Uncertainty budgets** (the GUM, JCGM 100:2008). Propagation for independent inputs:

```math
u_c^2(y) = \sum_i \left(\frac{\partial f}{\partial x_i}\right)^2 u^2(x_i)
```

That's how the weigh-a-meter error budget in
[filament.md](../calibration/filament.md#weigh-a-meter-true-cross-section) works.

## Machine tools: thermal error compensation

*Applied to this printer: [handbook chapter 9](../handbook/09-heat-control.md#the-frame-and-z-drift).*

[Mayr et al. 2012](https://www.researchgate.net/publication/256673861_Thermal_issues_in_machine_tools)
(CIRP keynote): thermal errors are 60 to 75% of all geometric error in machine tools, and the
usual fix is a few temperature sensors plus a fitted model.

For this printer: `z_thermal_adjust` uses one sensor. A fitted multi-sensor version is cheap:

```math
\Delta z \approx \sum_i k_i\,(T_i - T_{i,0})
```

with frame, chamber top, chamber bottom and bed as inputs, fitted from logged probe readings at
different temperatures. QGL and autoz already log what's needed.

## Buildings and HVAC

*Applied to this printer: [handbook chapter 9](../handbook/09-heat-control.md#the-chamber-is-a-small-building).*

- **Grey-box RC models** from logged data ([Bacher & Madsen 2011](https://doi.org/10.1016/j.enbuild.2011.02.005)). The chamber is a small building: identify its model from heat-up and cool-down logs, then control it with feedforward from the model
- **Displacement ventilation** ([REHVA Guidebook No. 1](https://www.dinmedia.de/en/publication/rehva-guidebook-no-1/104774508), Skistad 2002): supply air low and slow, take it out high, let buoyancy do the work. Comfort limits are around 0.15 to 0.25 m/s at floor level, and diffusers are kept to about 0.2 m/s face velocity

For this printer: the rear module does the opposite on purpose (warm air in low, so it rises and
mixes instead of layering), but the velocity numbers carry over. To keep the outlet at 0.2 m/s
while holding temperature at 5 L/s, the slot needs:

```math
A = \frac{\dot{V}}{v} = \frac{0.005}{0.2} = 0.025\ \text{m}^2
```

About 330 mm wide by 75 mm tall. Heat-up mode at 20 L/s through the same slot is 0.8 m/s, which is
fine since nothing's printing yet.

## Welding and wire-arc AM

- **Interpass temperature.** Welding codes specify a temperature range the previous pass has to be in before the next one goes on. Same idea for layers: hold the last layer in a window (hot enough to weld, cool enough not to sag) with layer time, fan and chamber
- **Layer height control.** Xiong & Zhang (2014, J. Materials Processing Technology 214) watched the nozzle-to-top distance with a camera in wire-arc AM and adjusted the deposition rate to keep layer heights constant. A camera or laser line could do that here someday

## Large-format polymer AM

ORNL's big printers ran into the weld problem first: [IR preheating the previous layer](https://doi.org/10.1016/j.addma.2016.11.008)
and [printability from material properties](https://doi.org/10.1016/j.jmapro.2018.08.008).
Details in [materials](materials.md#5-layers-welding-together).

## Self-driving labs

Robots running experiments picked by Bayesian optimization. The FDM version
([BEAR](https://www.science.org/doi/10.1126/sciadv.aaz1708)) is in [control](control.md#learning-across-layers-and-prints).

## References

Linked inline. The classics without links:

- Box, Wilson (1951). *On the experimental attainment of optimum conditions.* J. Royal Statistical Society B 13
- Bradley, Terry (1952). *Rank analysis of incomplete block designs: I. The method of paired comparisons.* Biometrika 39
- Brochu, de Freitas, Ghosh (2007). *Active preference learning with discrete choice data.* NeurIPS
- Gelman et al. *Bayesian Data Analysis.* (Hierarchical models)
- JCGM 100:2008. *Evaluation of measurement data: Guide to the expression of uncertainty in measurement (GUM).*
- ISO 5725. *Accuracy (trueness and precision) of measurement methods and results.*
- Koren, Bell, Volinsky (2009). *Matrix factorization techniques for recommender systems.* IEEE Computer 42(8)
- Sachs, Hu, Ingolfsson (1995). *Run by run process control: combining SPC and feedback control.* IEEE Trans. Semiconductor Manufacturing 8(1)
- Xiong, Zhang (2014). *Adaptive control of deposited height in GMAW-based layer additive manufacturing.* J. Materials Processing Technology 214
