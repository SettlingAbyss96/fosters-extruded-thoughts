# 11. Materials in practice

*Level 2 to 3.*

The earlier chapters were general. This one goes material by material: what limits each one, what
actually makes it stronger or more accurate, and the practices I think most people skip. Numbers are
ballpark unless they come from a datasheet I link.

## The pattern behind all of them

Every material question in this handbook comes back to four things:

1. **How far the interface gets above $T_g$, and for how long** (chapter 6). Decides whether welds heal fully
2. **How far below $T_{set}$ the chamber is** (chapter 7). Decides built-in stress and warp
3. **How wet it is** (chapter 2). Decides viscosity, bubbles and strength
4. **Whether it crystallizes** (chapters 2 and 7). Decides heat resistance and annealing shrink

Keep those in mind and the advice below stops being a list of rules and starts making sense.

## PLA

- $T_g$ about 60 °C. Printed at 200 °C plus, so the interface lands way above $T_g$ and welds heal fully almost instantly. **For PLA, Z strength is a geometry problem** (chapter 6): wider lines, lower $h/w$, a bit more flow
- Hates a hot chamber: heat creep, soft parts, sagging. Cool chamber, vent if the box is insulated ([slicer.md](../calibration/slicer.md#pla-in-an-insulated-box-is-a-problem))
- Low shrink (about 0.2 to 0.3%), so it's the accuracy-easy material
- Absorbs some water. Wet PLA strings and gets brittle

**Not widespread:** extra-wide inner walls and infill for strength. Remelting in salt for small
structural parts (CNC Kitchen got PLA and PETG back to nearly their flat-printed strength).

## PETG

- Amorphous, $T_g$ about 80 °C
- Sticky, stringy, and quite sensitive to moisture. Most "PETG strings" problems are wet PETG
- Doesn't want a hot chamber either. Warm at most
- Bonds well, tough

**Not widespread:** drying it properly and printing from a dry box, every time. It fixes more PETG
problems than any retraction setting.

## ABS and ASA

- Amorphous, $T_g$ about 100 to 105 °C. The interface only gets 50 to 75 K above $T_g$ and cools fast, so **ABS is where temperature history really matters** for weld strength (chapter 6)
- Shrinks about 0.5 to 0.8% and builds a lot of thermal stress in a cold box. Warping and layer splits are its signature failures
- The fix is heat. Stratasys's own [patent](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/6722872) describes their machines building in a 70 to 90 °C chamber
- ASA behaves almost the same, with better UV resistance

**Not widespread:**

- **Run the chamber much closer to the glass transition** than hobby printers do. 70 °C instead of 50 roughly halves the built-in stress (chapter 7)
- **Minimal part cooling.** Only for overhangs and bridges. Every bit of cooling costs weld time
- **A slow, controlled cool-down** instead of shutting everything off at the end
- **Salt remelting** for small solid structural parts: [CNC Kitchen](https://www.cnckitchen.com/blog/testing-the-strength-of-3d-prints-re-melted-in-salt) measured ABS layer adhesion up 150%, to about 90% of solid material
- **Drying.** ABS absorbs less water than nylon, but it absorbs some

## PC and PC blends

- $T_g$ about 145 °C. Wants a really hot chamber, well past what this printer will have
- At 70 °C the chamber is 75 K below $T_g$. Small PC parts are fine, big ones will warp and split. PC-ABS blends are the realistic option here
- Very sensitive to moisture (hydrolysis). Dry it hot and long

## Nylon (PA6, PA12) and nylon-CF

- Semi-crystalline. $T_g$ around 50 °C dry, and lower when wet, because water plasticizes it
- **Extremely hygroscopic.** Wet nylon foams, strings, and makes weak parts. Dry it, print it from a dry box, and treat the dry box as part of the printer
- After printing it picks up water from the air again. That makes it tougher and less stiff. Whether that's good depends on the part
- CF versions shrink much less, are stiffer, and need a hardened nozzle

**Not widespread:** deciding on purpose whether a nylon part should be used dry (stiff) or
conditioned (tough), instead of letting the weather decide.

## PPA-CF

This is the one I'm printing toolhead and chamber parts from, so it gets the most detail. From
Bambu's [PPA-CF datasheet](https://store.bblcdn.eu/s8/default/f592e57fe69c40289897513bdd2b61bc/Bambus_PPA-CF_Technical_Data_Sheet_2ab26420-79f5-4692-888e-090006814050.pdf):

| Property | Value |
|---|---|
| $T_g$ (DSC) | 85 °C |
| $T_m$ | 258 °C |
| Annealing | 120 to 140 °C |
| Drying (blast oven) | 100 to 140 °C, 8 to 12 h |
| Heat deflection (1.8 MPa) | 196 °C |
| Density | 1.25 g/cm³ |
| Saturated water absorption | 1.30% |

What that means:

- **A 70 °C chamber is only 15 K below its $T_g$.** That's close to ideal: low built-in stress, slow but real stress relaxation during the print, and a hot old layer for the next one to weld to
- **It's semi-crystalline,** so annealing is where the heat resistance comes from. Annealing at 120 to 140 °C is well above $T_g$: the part is soft while it crystallizes
- **It shrinks during annealing,** on top of the print shrink. And because it's carbon fiber filled, that shrink is bigger across the lines than along them

**Practices I'd follow:**

1. **Dry it properly** (it's a polyamide, water hydrolyzes it), and print from a dry box
2. **Hardened nozzle,** and I'd stay on 0.6 or bigger to avoid fiber clogs
3. **70 °C chamber, minimal fan**
4. **Extra-wide inner walls and infill** where the part is structural (chapter 5)
5. **Anneal with a ramp:** heat slowly, hold at 120 to 140 °C, cool slowly. Support thin features (salt or sand) so they don't sag
6. **Measure the annealing shrink once** with the dimensional test part (before and after annealing, both directions relative to the line direction) and pre-scale for it

## TPU

- An elastomer: soft segments below room temperature give the rubberiness, hard segments hold it together
- Very compliant, so pressure advance is a completely different number from rigid plastics, and the slicer has to go slow
- Absorbs water, strings when wet
- Doesn't need a hot chamber

## What most people skip, across the board

| Practice | Why it works | Materials |
|---|---|---|
| Dry everything, print from a dry box | Water cuts chains and boils in the nozzle (chapter 2) | All, nylon/PPA/PC/PETG most |
| Chamber close to $T_g$ | Less built-in stress, better welds (chapters 6, 7) | ABS, ASA, PPA, PC |
| Cool PLA and PETG, vent insulated boxes | Heat creep, sagging | PLA, PETG |
| Extra-wide inner lines | More bonded area (chapter 5) | All |
| Part fan only where needed | Cooling costs weld time | ABS, ASA, PPA, PC |
| Slow cool-down | Less stress at the end | ABS, ASA, PPA, PC |
| Annealing with a ramp, with support | Crystallinity without distortion | PLA (some), nylon, PPA |
| Separate print and annealing shrink | Two different physical effects | Nylon, PPA |
| Salt remelt for small solid parts | Near-isotropic strength | PLA, PETG, ABS |

## References

- [Bambu PPA-CF datasheet](https://store.bblcdn.eu/s8/default/f592e57fe69c40289897513bdd2b61bc/Bambus_PPA-CF_Technical_Data_Sheet_2ab26420-79f5-4692-888e-090006814050.pdf)
- [Stratasys patent US 6722872](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/6722872)
- [CNC Kitchen: salt remelting](https://www.cnckitchen.com/blog/testing-the-strength-of-3d-prints-re-melted-in-salt)
- [Costanzo et al. (2020)](https://doi.org/10.3390/polym12122980). Polyamide crystallization and welds
- Moisture: [nylon](https://doi.org/10.3390/technologies13080376), [PLA blends](https://pmc.ncbi.nlm.nih.gov/articles/PMC11442157/)
