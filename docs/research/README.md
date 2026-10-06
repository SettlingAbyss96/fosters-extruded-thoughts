# Research

The science behind the [calibration](../calibration/README.md) plan, so I'm not reinventing stuff
people already figured out. The [handbook](../handbook/README.md) explains all of it from the ground
up, and its [gaps chapter](../handbook/12-gaps.md) lists what research proved that nobody has built
yet. Three areas:

| Page | What's in it |
|---|---|
| [Materials](materials.md) | What the plastic does from the spool to the part: viscosity, melting limits, the bead, layer welding, crystallization, warping, moisture, fillers |
| [Control](control.md) | Extrusion, motion, monitoring and learning work on FFF, closest to this printer first |
| [Other fields](other-fields.md) | Injection molding, filament factories, chip fabs, chemometrics, recommender systems, statistics, metrology, machine tools, HVAC, welding |

Every paper linked here, I checked it exists and says roughly what I say it says (abstract or
summary level, not a full read of every one). Classics without links are textbook stuff.

## Steal these first

Ranked by payoff for the effort:

| # | Idea | From | Lands in |
|---|---|---|---|
| 1 | **Settings from a pressure–flow–temperature map, with a cool-down sweep** | [Read et al. 2024](control.md#the-closest-thing-to-what-i-want) | bd_pressureE + BDwidth intake. Basically my hardware plan, already proven |
| 2 | **Calibration transfer with anchors** | [Chemometrics](other-fields.md#chemometrics-calibration-transfer) | [library.md](../calibration/library.md): Bambu and Orca data mapped onto this machine |
| 3 | **Run-to-run updates with SPC gating** | [Chip fabs](other-fields.md#semiconductor-fabs-run-to-run-control-and-spc) | Learning from every print without chasing noise |
| 4 | **Partial pooling** | [Statistics](other-fields.md#statistics) | Family → line → color → spool inheritance |
| 5 | **Equivalent weld time** | [Materials](materials.md#5-layers-welding-together) | Chamber, layer time and fan policy for strength, in numbers |
| 6 | **Graetz number melting limit** | [Materials](materials.md#2-melting-how-fast-the-hotend-can-go) | Hotend choice, HF nozzles |
| 7 | **Live viscosity compensation** | [Injection molding](other-fields.md#injection-molding) | Pressure vs reference during a print |
| 8 | **Force tracks line width** | [ETH Zurich](control.md#eth-zurich-lygeros-balta-guidetti-and-others) | The pressure sensor as a width sensor |
| 9 | **Multi-sensor thermal compensation** | [Machine tools](other-fields.md#machine-tools-thermal-error-compensation) | Z drift |
| 10 | **Phase stepping, FBS racking compensation** | [Motion](control.md#motion) | The A/B motor problem |
| 11 | **Pairwise comparisons + preference optimization** | [Statistics](other-fields.md#statistics) | Seams and looks, with me as the sensor |
| 12 | **Phone-camera one-shot calibration** | [ETH Zurich](control.md#eth-zurich-lygeros-balta-guidetti-and-others) | Cheap camera path |

## Things that changed my mind

- **The hardware I'm planning has already been proven.** Read et al. built a load cell between the gears and the hotend plus a filament encoder, and picked working settings for filaments nobody had a profile for. That's bd_pressureE + BDwidth
- **Datasheet melt flow index runs about 100× slower than printing,** so it's a weak predictor. Measuring on the machine beats any datasheet
- **Insulating the box makes ABS easier and PLA harder.** Thermal stress about halves at 70 °C, while PLA needs venting
- **Wet filament should show up as "runnier than expected"** before it shows up in the print. The passive checks can catch it
- **The pressure sensor matters more than any other upgrade on the list.** It shows up in PA, max flow, ooze, viscosity, line width, clogs and wet filament

## Reading order

1. [Das et al. 2021](https://doi.org/10.1021/acsapm.0c01228), rheology review. The big picture of why filaments differ
2. [Read et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11636983/). Open access, closest to the plan
3. [Seppala et al. 2017](https://pubs.rsc.org/en/content/articlelanding/2017/sm/c7sm00950j). Layer welding, what the chamber is really for
4. [Go et al. 2017](https://www.sciencedirect.com/science/article/abs/pii/S2214860416302834). Speed limits
5. [Force controlled printing](https://arxiv.org/abs/2403.16042). What the pressure sensor could become

## To do

- [ ] Actually read the top five properly, not just the abstracts
- [ ] Check whether Read et al.'s code or data is public
- [ ] Get an MFI value for every filament that has a datasheet, to test how bad a predictor it is here
- [ ] Watch for new ETH Zurich papers, they're putting out a lot on exactly this
