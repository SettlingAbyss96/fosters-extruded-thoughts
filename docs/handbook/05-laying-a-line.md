# 5. Laying down a line

*Level 2 to 3.*

## Mass conservation is the whole slicer

The slicer's core assumption is simple: whatever volume goes out of the nozzle ends up as a line
of a known shape. If the line has cross-section $A$ and the toolhead moves at $v$, then

```math
Q = A\,v
```

Pick a line width $w$ and layer height $h$, assume a shape, get $A$, and the extrusion per
millimeter falls right out. Everything about extrusion amounts in a slicer is this one equation.
The interesting question is what shape the line really is.

## The bead shape

Most slicers (Orca included) model a line as a rectangle with round ends:

```math
A = (w - h)\,h + \frac{\pi h^2}{4}
```

That's what you get if a blob gets flattened between the nozzle and the layer below and bulges out
at the sides. It's a decent model when the line is well squished, and it gets worse when it isn't.

[Comminal et al. (2018)](https://doi.org/10.1016/j.addma.2017.12.013) simulated the actual deposition
flow and found two numbers decide the shape:

- **The gap:** nozzle height above the layer below, relative to the nozzle diameter
- **The speed ratio:** how fast the toolhead moves compared to how fast the melt flows in the nozzle

Fast with a big gap gives an almost round strand that barely touches what's under it. Slow with a
small gap gives a flat one with rounded edges, pressed firmly down. And the force the strand pushes
down with drops linearly as the speed ratio goes up. **Printing faster at the same line width
means less squish.** Keep that in mind for chapter 6.

On top of that, the melt swells when it leaves the nozzle (die swell, chapter 2), so the strand
starts out wider than the bore.

## Squish

Squish is how hard the bead gets pressed into the layer below. It comes from the gap (layer height
vs nozzle) and from flow: overextrude a little and the extra plastic has to go somewhere, so it
presses harder and fills more of the corners.

The first layer is the extreme case. The gap is set by the Z offset, and that's why the first layer
is so sensitive to it: a 0.05 mm Z error on a 0.3 mm first layer is a 17% change in the gap, and
the squish changes even more than that.

## Contact between layers

Stack rounded-rectangle beads on top of each other and look at the cross-section. The flat part of
each bead touches the flat part of the one below, but the round ends leave little triangular voids
at the corners. In the idealized geometry:

```math
\phi_c \approx \frac{w - h}{w} = 1 - \frac{h}{w}
```

is the fraction of each layer that's actually bonded to the layer below, and

```math
\text{void fraction} \approx \frac{h^2\left(1 - \frac{\pi}{4}\right)}{w\,h} \approx 0.21\,\frac{h}{w}
```

is how much of the part is empty space between lines.

| Setup | $w$ | $h$ | Bonded fraction | Voids |
|---|---|---|---|---|
| 0.4 nozzle, typical | 0.45 | 0.20 | 56% | 9% |
| 0.4 nozzle, thick layers | 0.45 | 0.28 | 38% | 13% |
| 0.6 nozzle, typical | 0.68 | 0.30 | 56% | 9% |
| 0.6 nozzle, extra wide | 1.50 | 0.30 | 80% | 4% |

Real beads flow into the corners somewhat, so measured contact comes out higher than this. But the
trend is the point. **The ratio $h/w$ decides how much of each layer is actually stuck to the next
one.** Thick layers on narrow lines leave less than half the cross-section bonded.

## Extra-wide lines

This is one of my favorite findings in the whole literature, because it's so simple.
[Allum et al.](https://www.sciencedirect.com/science/article/pii/S2214860422007230) printed
lines at least 250% of the nozzle diameter wide: one 1.2 mm line from a 0.4 mm nozzle instead of
three 0.4 mm lines. Contact between layers went from 63% to 90%, and strength, strain at fracture
and toughness went up 40 to 48%. And it printed 67% faster.

Why isn't everyone doing this? Partly habit: default line widths sit around 1.1 to 1.2× the nozzle
because that gives nice surfaces and modest flow. And there's a real physical catch: **the nozzle
tip has to be flat and wide enough to iron the whole bead.** A narrow, pointy tip can't press down a
line wider than its flat face. So extra-wide lines want a nozzle with a wide flat land, and enough
melt capacity for the higher flow.

For inner walls and infill on structural parts, where nobody sees the surface, this is basically free
strength. More in chapter 6.

## Line width conventions

Why the defaults are what they are:

- **Outer walls** at about 1.0 to 1.1× the nozzle look best and hold dimensions
- **Inner walls and infill** can go much wider. Wider means fewer, fatter lines, faster prints, better contact
- **Top surfaces** narrower and slower look smoother

The slicer's job would be easier if it reasoned about this as "contact fraction vs surface finish
vs flow limit" instead of a pile of separate width settings. That's a theme in [chapter 12](12-gaps.md).

## Overlap and top surfaces

- **Wall/infill overlap** pushes the infill into the walls so they bond. It's fixing the same corner voids from above, sideways
- **Ironing** runs the hot nozzle back over the top surface with a trickle of flow to flatten it. It's squish applied after the fact

## What I'd test

- Z-direction tensile coupons at three $h/w$ ratios on the 0.6 nozzle, including an extra-wide case
- Cut and polish the coupons, measure the actual bonded width under a USB microscope, compare to $1 - h/w$
- Whether the Conch's tip is flat and wide enough for 1.5 mm lines, before trying it

## References

- [Comminal, Serdeczny, Pedersen, Spangenberg (2018)](https://doi.org/10.1016/j.addma.2017.12.013). Strand deposition flow: gap and speed ratio decide the shape
- [Allum et al.](https://www.sciencedirect.com/science/article/pii/S2214860422007230). Extra-wide deposition: 90% vs 63% contact, 40 to 48% stronger, 67% faster
- [Allum, Moetazedian, Gleadall, Silberschmidt (2020)](https://www.sciencedirect.com/science/article/abs/pii/S2214860420306692). Anisotropy comes from geometry (chapter 6)
