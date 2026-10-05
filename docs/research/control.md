# Control and sensing for FFF

What's been done on the control side, closest to this printer first.

## The closest thing to what I want

### Read et al. 2024 (NIST + MIT): settings from pressure maps

[Online Measurement for Parameter Discovery in Fused Filament Fabrication](https://pmc.ncbi.nlm.nih.gov/articles/PMC11636983/).
This is basically the [filament](../calibration/filament.md) idea, already built and tested:

- **Hardware:** a load cell between the drive gears and the hotend as a pressure stand-in, plus a filament sensor (encoder idler for real feed rate and slip, hall sensor for diameter). That's more or less what bd_pressureE + BDwidth would give me
- **Test:** heat to 290 °C, start extruding at a fixed flow, **turn the heater off**, and log pressure while the nozzle cools. Stop when the drive slips below 75%. Repeat at 5 flows (5 to 25 mm³/s). Each trace takes 90 s to 5 min, so 10 to 30 min per machine and material
- **Model:** pressure linear in temperature at each flow, with the slope and offset depending on flow:

```math
P = (-cQ + d + 1)\,T + eQ^2 + f
```

- **Picking settings:** temperature = the temperature where it first flows + 80 °C. Flow = a fraction of the max force before slip (0.75 for max-rate features, 0.2 / 0.1 / 0.05 for more important ones). One set of these two numbers for everything
- **Results:** PLA, wood PLA, an algae-based filament and a bio PETG on 0.4 and 0.8 nozzles. Temperatures landed inside the manufacturer's range in all but one case, no failed prints, stringing on two. Benchy only 12% faster, because acceleration was the limit, not flow
- **Their own limitations:** nozzle data alone isn't enough to pick everything, the slicer is disconnected from the machine (same complaint as [slicer.md](../slicer.md)), and an uncalibrated load cell can't compare machines

What I take from it:

- **The cool-down sweep.** One pass covers every temperature at a given flow. Way faster than stepping the temperature, and it needs the pressure sensor, not the scale
- Relative settings (fraction of max force) instead of absolute numbers, same as the ratio idea
- Proof the approach works on materials nobody had a profile for

### ETH Zurich (Lygeros, Balta, Guidetti and others)

A whole line of work on closed-loop extrusion:

- [Force controlled printing](https://arxiv.org/abs/2403.16042) (2024): force sensor in the extruder, feedback on extrusion force. Line width tracks force closely, so controlling force controls width: 33% to 233% of the nozzle diameter, and it held the width while the layer height was messed with from 20% to 200% of nominal
- [One-shot camera calibration](https://arxiv.org/abs/2512.24905) (2025): photograph two printed patterns with a phone, fit a model, generate optimized G-code. Quality at 3600 mm/min matching normal printing at 1600 mm/min
- [Closed-loop reference optimization](https://arxiv.org/abs/2512.16333) (2025): LQR with force feedback for line width, about 40% lower tracking error and much faster settling
- [Bayesian optimization with an in-situ laser sensor](https://arxiv.org/abs/2210.15239) (2022): surface roughness measured during printing, used to pick parameters

What I take from it: **a pressure/force sensor isn't just for PA.** It's a line-width sensor. And
the phone-camera calibration is the cheapest possible path to the same idea.

## Extrusion

| Work | What | For me |
|---|---|---|
| [Bellini et al. 2004](https://orbit.dtu.dk/en/publications/liquefier-dynamics-in-fused-deposition/) | Liquefier as a dynamic system | Where the PA model comes from |
| [Tronvoll et al. 2019](https://www.emerald.com/rpj/article/25/5/830/363878/Investigating-pressure-advance-algorithms-for) | First academic look at advance algorithms | Linear PA's limits |
| [Wu, Qian, Okwudire 2023](https://doi.org/10.1016/j.addma.2023.103850) | Model + feedforward for retraction and re-advance, force measured with a servo extruder | Seams as a control problem |
| Greeff & Schilling 2017, *Closed loop control of slippage during filament transport* (Additive Manufacturing 14) | Measured real filament speed and closed the loop on slip | BDwidth encoder loop |
| [Moretti & Rossi 2023](https://journals.sagepub.com/doi/abs/10.1089/3dp.2021.0236) | Closed-loop filament feed control | Same |
| [Coogan & Kazmer 2019](https://www.researchgate.net/publication/330031420_In-line_rheological_monitoring_of_fused_deposition_modeling) | Pressure transducer + thermocouple in a custom nozzle: an in-line rheometer, checked against a lab capillary rheometer | The nozzle measures viscosity |
| [Anderegg et al. 2019](https://www.researchgate.net/publication/330392702_In-Situ_Monitoring_of_Polymer_Flow_Temperature_and_Pressure_in_Extrusion_Based_Additive_Manufacturing) | Pressure + melt temperature inside the flow. Melt temperature drops at high flow | The hotend thermistor doesn't see what the plastic sees |
| [Phan, Swain, Mackay 2018](https://doi.org/10.1122/1.5022982) | Pressure in the nozzle during normal printing, measured from the extruder's drive power | Extruder load as a pressure signal |
| Kalico MPC | Hotend model with filament feedforward | Already in the firmware ([slicer.md](../slicer.md#hotend-mpc-with-filament-feedforward)) |

## Motion

| Work | What | For me |
|---|---|---|
| Singer & Seering 1990, Singhose et al. (EI shapers) | Input shaping: cancel a resonance by splitting each move into timed pieces | What Klipper's shapers are |
| [Okwudire's filtered B-splines](https://www.sciencedirect.com/science/article/abs/pii/S0957415817301277) | Invert a model of the machine's dynamics and pre-distort the commands. Handles several modes at once | Alternative to input shaping. Commercial version: [Ulendo](https://www.ulendo.io/solutions/ulendo-vc) |
| [FBS with position-varying dynamics](https://arxiv.org/abs/2209.06791) | Dynamics change with where the toolhead is | My shaper is measured at one spot |
| [FBS for H-frame racking](https://arxiv.org/abs/2105.09878) | Software compensation of gantry racking on H-frame printers | CoreXY has the same racking problem. Worth reading for the A/B asymmetry |
| [Prusa phase stepping](https://help.prusa3d.com/article/phase-stepping-core-one_914247) | Per-motor drive waveform tuned with an accelerometer to kill VFAs and noise from motor variance | The A/B motors behave differently. This is the same idea |

## Watching the print

| Work | What | For me |
|---|---|---|
| [Brion & Pattinson 2022](https://www.nature.com/articles/s41467-022-31985-y) | Camera + neural net trained on PLA, worked on printers, cameras and materials it hadn't seen, and corrected flow, speed, Z offset and temperature live | Proof camera closed-loop works across machines. Too big a project for now |
| Wu, Wang, Yu [2016](https://link.springer.com/article/10.1007/s00170-015-7809-4) and 2017 | Acoustic emission to spot machine faults and filament breaks | A cheap contact mic could catch clogs and skipping |
| [Vibration sensors for in-situ diagnosis](https://pmc.ncbi.nlm.nih.gov/articles/PMC6603584/) (2019) | Accelerometers to diagnose print faults | I already have the accelerometer |
| Reviews: [in-situ monitoring and control in material extrusion](https://doi.org/10.3390/jeta3030021) (2025), [the extrusion process in FFF](https://link.springer.com/article/10.1007/s00170-021-06918-6) (2021), [FDM system models and control strategies](https://www.mdpi.com/2076-3417/12/11/5400) (2022) | Overviews | Start here for anything not on this page |

## Learning across layers and prints

| Work | What | For me |
|---|---|---|
| Bristow, Tharayil, Alleyne 2006 (IEEE Control Systems Magazine) | Iterative learning control survey: a repeated task learns from its last attempt | Printing repeats layers |
| Hoelzle & Barton: [spatial ILC](https://mae.osu.edu/hrl/publications), [multi-layer spatial ILC](https://www.sciencedirect.com/science/article/pii/S2405896319316465), [layerwise height control](https://dl.acm.org/doi/10.1016/j.automatica.2024.111756) (2024) | ILC where the repetition is in space, layer to layer | Layer height or width correction from a camera, someday |
| [Greeff & Schilling 2018](https://link.springer.com/article/10.1007/s00170-018-2518-4), single print optimisation | A DOE's worth of test object variants merged into one G-code, one print, regression on the results | That's the [intake plate](../calibration/filament.md#the-intake-plate-where-this-is-going) |
| [Papazetis & Vosniakos 2019](https://link.springer.com/article/10.1007/s00170-018-2820-1) | Map the good process window from a minimal set of experiments | Fewer test prints |
| [Gongora et al. 2020 (BEAR)](https://www.science.org/doi/10.1126/sciadv.aaz1708) | Five FDM printers, a robot arm, a scale and a testing machine, run by Bayesian optimization. About 60× fewer experiments than a grid search | Self-driving test rig. With a scale in it, which I like |

## Chamber and thermal

| Work | What | For me |
|---|---|---|
| [Bacher & Madsen 2011](https://doi.org/10.1016/j.enbuild.2011.02.005) | Identify RC thermal models of buildings from logged data | The chamber model, from logs instead of guesses |
| [Mayr et al. 2012](https://www.researchgate.net/publication/256673861_Thermal_issues_in_machine_tools) | Thermal errors are 60 to 75% of the geometric error in machine tools. Measured and compensated with a few temperature sensors | Z drift compensation with more than one sensor ([other fields](other-fields.md#machine-tools-thermal-error-compensation)) |

## Commercial printers already closing loops

- **Bambu X1:** lidar measures PA (flow dynamics) and checks the first layer
- **Prusa MK4 / Core One:** load cell in the nozzle for probing, phase stepping for the motors
- **Ulendo:** FBS vibration compensation as a commercial product for printers

None of it is magic. It's the same sensors and models as above, packaged.

## What I'm taking

| Idea | Where it goes |
|---|---|
| Cool-down sweep with pressure + slip | bd_pressureE + BDwidth intake, replaces most of the flow ladder |
| Force tracks line width | Pressure sensor as a width sensor, not just PA |
| Retraction as modeled feedforward | Seams |
| Slip closed loop | BDwidth encoder |
| Phone-camera one-shot calibration | Cheap camera path before any real vision project |
| Single print optimisation | The intake plate |
| Grey-box chamber model | Chamber control, from logs |
| Multi-sensor thermal compensation | Z drift |
| Phase stepping, FBS racking | A/B motor problem |
| Acoustic emission | Maybe. Cheap clog and skip detector |

Not doing: training a big neural net from scratch, CFD of the nozzle, building a robot to swap
prints. Interesting, wrong scale.

## References

Linked inline. The ones without links:

- Bristow, Tharayil, Alleyne (2006). *A survey of iterative learning control.* IEEE Control Systems Magazine 26(3)
- Greeff, Schilling (2017). *Closed loop control of slippage during filament transport in molten material extrusion.* Additive Manufacturing 14
- Singer, Seering (1990). *Preshaping command inputs to reduce system vibration.* J. Dynamic Systems, Measurement, and Control 112
- Singhose, Seering, Singer: the extra-insensitive (EI) shaper papers from the 1990s
- Wu, Wang, Yu (2017). *Real-time FDM machine condition monitoring and diagnosis based on acoustic emission and hidden semi-Markov model.* Int. J. Advanced Manufacturing Technology 90
