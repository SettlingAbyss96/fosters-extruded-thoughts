# 13. Where this goes

*Level 2. Theorizing. Nothing here is built yet.*

This is the part where I think out loud. Some of it I'm fairly sure will work. Some is a long shot.
All of it falls out of the earlier chapters if you follow them far enough.

## The printer as a lab instrument

Once a printer has a pressure sensor, a filament encoder, a good thermal model and a scale next to
it, it stops being just a machine that makes parts. It becomes a pretty decent materials lab:

- **A capillary rheometer.** The nozzle is literally a capillary. Pressure vs flow vs temperature is a viscosity curve ([Coogan & Kazmer 2019](https://www.researchgate.net/publication/330031420_In-line_rheological_monitoring_of_fused_deposition_modeling), [Read et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11636983/))
- **A calorimeter.** The slope of heater power against flow tells you how much energy the plastic takes, including how crystalline it came off the spool (chapter 3)
- **A moisture analyzer.** Wet filament is runnier than its own baseline (chapter 2)
- **A tribometer.** Slip vs extrusion force is a grip curve for that filament and those gears
- **A Z-only CMM.** The probe can touch the top of a printed part and measure warp

I think the interesting shift is that **the printer characterizes its feedstock while it prints.**
Not a separate test, just a side effect of running.

## Every part gets a birth certificate

If the machine logs the thermal history of every layer (chamber, bed, nozzle, fan, layer time,
maybe an IR reading of the surface), it can compute the equivalent weld time for every interface
(chapter 6). That's a predicted strength map of the part, layer by layer.

Then you can:

- Flag the layers that came out cold ("layer 212 had a 40 second layer time and the fan on")
- Change the plan mid-print to keep the welds where they need to be
- Hand someone a part with a record of how it was made, which aerospace and medical people care a lot about

## The slicer plans, the firmware tracks

[Read et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC11636983/) ran straight into the biggest wall
in this whole field: the slicer is disconnected from the machine. It writes fixed numbers into
G-code, and the firmware executes them blindly.

I think the long-term fix is to split the job differently:

- **The slicer plans intent:** this line should be 0.68 mm wide, this interface needs this much weld time, this region is an overhang
- **The firmware closes the loops:** extrusion force to hit the width ([ETH](https://arxiv.org/abs/2403.16042)), temperature and timing to hit the weld, pressure to hit the seam

The ETH group's [one-shot calibration](https://arxiv.org/abs/2512.24905) is already halfway there:
it optimizes the G-code against a model of the machine. Model predictive printing, basically.

## Closing the loop on the things we care about

Right now printers close loops on temperatures and positions, which are means to an end. What we
actually care about is line width, weld strength and part dimensions. The next generation of loops
should be on those:

| Thing I care about | Sensor | Loop |
|---|---|---|
| Line width | Extrusion force | Force feedback ([ETH](https://arxiv.org/abs/2403.16042)) |
| Weld strength | Interface temperature history | Layer time, fan, chamber, preheat |
| Dimensions | Probe, camera | Run-to-run correction of shrink and offset |
| Flow | Pressure, encoder, heater power | Real-time correction of slip and viscosity |

## Recycled filament and pellets

The main reason recycled filament and pellet printing are hard is that the feedstock varies: the
diameter wanders, the viscosity drifts as chains get cut each time the plastic is reprocessed. That's
exactly the problem adaptive extrusion solves. **A printer that measures and compensates viscosity
and diameter in real time makes variable feedstock usable.** I think that's a bigger deal for
sustainability than any single new material.

## Multi-material interfaces

Welding two different plastics is chapter 6 plus chemistry. Chains only cross the boundary if the
plastics are at least partly compatible. For incompatible pairs you need mechanical interlocking
instead: interlocking geometry, z-pins across the boundary, brick-style staggering. The same
weld-time planning applies, with a different healing number for each pair.

## Field-assisted bonding

If the weld is the weak spot, put energy right where the weld is:

- [Microwave-heated carbon nanotube coatings](https://www.science.org/doi/10.1126/sciadv.1700262), 275% stronger welds
- [IR preheating](https://doi.org/10.1016/j.addma.2016.11.008) and [laser preheating](https://asu.elsevierpure.com/en/publications/an-in-process-laser-localized-pre-deposition-heating-approach-to-) of the old layer
- Plasma and solvent treatments

The version I find most interesting for a hobby machine is a small IR emitter on the toolhead,
controlled by the weld model: only heat the old layer when the model says the next weld will come out
cold. Most layers wouldn't need it.

## Toolpaths designed for strength

Slicers fill volume. They don't design for strength. Things that would:

- Extra-wide lines where nobody sees them
- Interlocking layers
- Z-pins through infill
- Infill lines that follow the stress field within each layer (2.5D, no extra axes needed)
- Thinner layers only where Z strength matters

[FullControl](https://github.com/FullControlXYZ/fullcontrol) is the right tool to prototype all of
these, since it designs toolpaths directly instead of slicing a mesh.

## A shared, honest filament database

If enough people measured their filaments against the same common anchor (Bambu PLA Basic is
everywhere and very consistent), the data from different printers would become comparable. That's a
round robin, the way metrology labs check each other. Fill the gaps with matrix factorization
(the [recommender system](../research/other-fields.md#recommender-systems) trick) and you get a
filament library that works for everyone's printer, not just Bambu's. That could be its own open
repo, like the buffer plugin.

## Machine health

The same tools catch the machine drifting:

- **Nozzle wear:** the bore grows, the anchor's pressure drops at the same flow
- **Heater aging:** the MPC model's parameters drift
- **Belts stretching:** resonance frequencies drop
- **Partial clogs:** pressure up, flow down

CUSUM on those numbers (chapter 10) turns "the prints got worse" into "the nozzle's worn, swap it."

## Beyond plastic

None of this is specific to thermoplastics. Direct ink writing (silicones, pastes), concrete
printing, food and bioprinting all push a non-Newtonian material through a nozzle and stack it in
layers. Force-controlled extrusion, pressure maps, printability models
([Duty et al.](https://doi.org/10.1016/j.jmapro.2018.08.008)) and run-to-run learning all carry over.
The materials are different. The control problem isn't.

## What a printer spec sheet should say

Machine tools have test standards (ISO 230 covers things like positioning accuracy and thermal
effects). Printers have "max speed 500 mm/s." What I'd want instead:

- Max flow vs temperature, for a reference material
- PA vs flow
- Chamber and frame thermal time constants
- Z drift per degree of frame temperature
- Resonance frequencies and recommended accelerations
- Positioning accuracy across the bed

All of it measurable with the tools in this handbook.

## Where I'll start

1. The print logger and the strength profile (software, now)
2. The pressure sensor and the cool-down sweep (phase 2 in [chapter 12](12-gaps.md#how-id-sequence-it))
3. The thermal module, with weld time planning
4. The shared database, if the first three work

If you're reading this and you've built any of it, I'd love to know.
