# Material science of FFF

What happens to the plastic from the spool to the finished part, one stage at a time, and what
each stage means for this printer.

```mermaid
flowchart LR
    A[Melt] --> B[Flow through<br/>the nozzle]
    B --> C[Bead lands]
    C --> D[Layers weld]
    D --> E[Cools: shrink,<br/>warp, crystallize]
```

## 1. Melt viscosity

*Long version: [handbook chapter 2](../handbook/02-polymers-101.md).*

**Polymer melts get runnier the faster they flow** (shear thinning). A common model is the Cross
model:

```math
\eta(\dot\gamma, T) = \frac{\eta_0(T)}{1 + (\lambda\dot\gamma)^{1-n}}
```

with $n < 1$. And they get runnier with temperature. Close to Tg (within about 100 °C) the WLF
equation describes it:

```math
\log_{10} a_T = \frac{-C_1\,(T - T_r)}{C_2 + T - T_r}, \qquad \eta_0(T) = a_T\,\eta_0(T_r)
```

The part that matters: **one shift factor $a_T$ rescales everything at once.** Viscosity,
relaxation times, and how fast chains diffuse across a weld all shift by the same factor with
temperature (time-temperature superposition). That's the physics behind the "matching
temperature" idea in [filament.md](../calibration/filament.md#matching-temperature): match the
melt state and a lot of other behavior comes along with it.

**How fast is printing, in rheology terms?** The wall shear rate in the nozzle bore is about:

```math
\dot\gamma_w \approx \frac{4Q}{\pi R^3}
```

At 20 mm³/s that's about 900 per second in a 0.6 nozzle and about 3200 in a 0.4. The melt flow
index on a datasheet is measured at roughly 10 per second. So **MFI is measured two orders of
magnitude slower than printing**, and two filaments with the same MFI can print differently if
they shear-thin differently. Good prior, bad predictor.

**Viscoelasticity** matters too: the strand comes out wider than the nozzle (die swell), and the
melt has some memory of being stretched. [Duty et al. 2018](https://doi.org/10.1016/j.jmapro.2018.08.008)
built a "is this printable" model on exactly that: can it be pushed through the nozzle at the
needed rate, and does it hold its shape once it's out.

For this printer:

- PA isn't a constant: the nozzle's resistance depends on flow and temperature ([models](../calibration/models.md#nozzle-pressure))
- The nozzle is a capillary rheometer. With a pressure sensor it measures viscosity directly ([Coogan & Kazmer 2019](https://www.researchgate.net/publication/330031420_In-line_rheological_monitoring_of_fused_deposition_modeling), [Anderegg et al. 2019](https://www.researchgate.net/publication/330392702_In-Situ_Monitoring_of_Polymer_Flow_Temperature_and_Pressure_in_Extrusion_Based_Additive_Manufacturing), [Read et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11636983/))
- Datasheet MFI is a starting point for a new filament's profile, never the answer

## 2. Melting: how fast the hotend can go

*Long version: [handbook chapter 3](../handbook/03-melting.md).*

[Go et al. 2017](https://www.sciencedirect.com/science/article/abs/pii/S2214860416302834) broke
FFF speed into three limits: how hard the extruder can push, how fast heat gets into the
filament, and how fast the gantry moves. Melting turned out to be the limit in a lot of machines.

The heat side has a neat scaling. Heat has to conduct into the middle of the filament while it
moves through the heated length $L$. [Phan, Swain & Mackay 2018](https://doi.org/10.1122/1.5022982)
did this properly with a Nusselt vs Graetz number correlation. The back-of-envelope version: the
Graetz number compares flow to conduction,

```math
Gz = \frac{Q}{\alpha L}, \qquad \alpha = \frac{k}{\rho c_p}
```

and melting keeps up while $Gz$ stays under some critical value. So per melt channel:

```math
Q_{max} \approx Gz^{\ast}\,\alpha\,L
```

What falls out:

- **Max flow scales with heated length.** That's why long melt zones (UHF) help
- **Splitting the filament into channels multiplies it.** That's what HF and CHT-style nozzles do: $N$ thin streams instead of one fat one
- **Material thermal diffusivity matters.** Fillers like carbon fiber conduct heat better, so they melt faster
- **Filament diameter mostly drops out** (in this crude version), surprisingly

$Gz^{\ast}$ is fitted once from the anchor's flow ladder, then the heated length and the material
predict the rest. That's how I'd compare the Conch to a Rapido 2 UHF on paper before buying.

Also worth knowing: [Go & Hart](https://arxiv.org/abs/1709.05918) pushed desktop FFF way past
the usual limits with a screw feed and laser heating. Different machine, same three limits.

## 3. Flow through the nozzle (where PA comes from)

*Long version: [handbook chapter 4](../handbook/04-extrusion-dynamics.md).*

[Bellini, Güçeri & Bertoldi 2004](https://orbit.dtu.dk/en/publications/liquefier-dynamics-in-fused-deposition/)
was the first to treat the liquefier as a dynamic system with a lag between pushing filament and
plastic coming out, the thing pressure advance compensates for.
[Tronvoll et al. 2019](https://www.emerald.com/rpj/article/25/5/830/363878/Investigating-pressure-advance-algorithms-for)
were the first to look at advance algorithms academically (Marlin's Linear Advance).
[Wu, Qian & Okwudire 2023](https://doi.org/10.1016/j.addma.2023.103850) modeled retraction and
re-advance, measured the extrusion force with a servo extruder, and built a feedforward for starts
and stops. That's seams, done as control.

The lag comes from compliance: filament squishing between the gears and the melt, and the melt
itself compressing. Stiff filament (PLA) and soft filament (TPU) have very different compliance,
which is why PA is per material and doesn't transfer between families.

## 4. The bead

*Long version: [handbook chapter 5](../handbook/05-laying-a-line.md).*

[Comminal et al. 2018](https://doi.org/10.1016/j.addma.2017.12.013) simulated how the strand lands.
Two numbers decide its shape: the gap between the nozzle and the layer below, and the ratio of
print speed to flow speed in the nozzle. Fast with a big gap gives an almost round strand, slow
with a small gap gives a flat one with rounded edges. The force the strand puts on the layer
below drops linearly as the speed ratio goes up.

For this printer:

- Orca's rounded-rectangle bead model is only right in the squished regime
- The contour offset from the [dimensional test](../calibration/models.md#dimensions) is this effect
- The first layer is this effect with a probe-set gap

## 5. Layers welding together

*Long version, including where the research disagrees: [handbook chapter 6](../handbook/06-layer-bonding.md).*

How strong a part is across layers comes down to the weld between them. Two steps:

1. **The surfaces touch and flow together** (neck growth, like sintering). [Bellehumeur et al. 2004](https://doi.org/10.1016/S1526-6125(04)70071-7) modeled this with the cooling of ABS strands
2. **Polymer chains wiggle across the interface and tangle up again** (reptation). Classic result from Wool & O'Connor (1981): weld strength grows with contact time to the 1/4 power, until the chains have fully crossed:

```math
\frac{\sigma}{\sigma_\infty} = \left(\frac{t}{\tau_{rep}}\right)^{1/4}, \qquad t < \tau_{rep}
```

The catch is the temperature drops fast after the strand lands, and $\tau_{rep}$ shoots up as it
cools. [Seppala et al. 2017](https://pubs.rsc.org/en/content/articlelanding/2017/sm/c7sm00950j)
(NIST) handled that with an **equivalent isothermal weld time**, measured with an IR camera:

```math
t_{eq} = \int \frac{dt}{a_T(T(t))}
```

The hot moments count enormously, the cold ones count for nothing.
[McIlroy & Olmsted 2017](https://www.sciencedirect.com/science/article/abs/pii/S0032386117306213)
added another reason welds come out weaker than solid plastic: flowing through the nozzle
stretches and partly untangles the chains, and they need time to relax before they weld properly.
[Kishore et al. 2017](https://doi.org/10.1016/j.addma.2016.11.008) (ORNL, large format) heated
the previous layer with IR to near Tg before printing on it, and the bond strength went up a lot.

For this printer:

- **A hot chamber keeps the weld from cooling as far,** so $t_{eq}$ goes up. That's the strength argument for 70 °C, in numbers
- **Layer time and part cooling fan trade directly against strength.** The fan that saves an overhang costs weld time
- An IR sensor at the toolhead ([sensors](../calibration/sensors.md#cheap-things-to-add)) would give $T(t)$ for real, and $t_{eq}$ per layer

## 6. Crystallization (PLA, PA, PPA, PP, PEEK)

Semi-crystalline plastics crystallize depending on how fast they cool and how long they spend
between Tg and the melting point. Crystallinity changes stiffness, heat resistance, shrinkage and
warping. [Northcutt et al. 2018](https://www.sciencedirect.com/science/article/abs/pii/S0032386118308541)
(NIST) watched it happen during printing with IR and Raman, and print conditions changed how fast
it crystallized. [Costanzo et al. 2020](https://doi.org/10.3390/polym12122980) did the same kind
of thing for polyamides, linking crystallization speed to how the welds form.

For this printer:

- **PPA-CF annealing makes sense now.** Printed in a cooler chamber it comes out partly crystallized, annealing finishes the job, and the part shrinks and stiffens while it does. Measure that shrink once (dimensional test before and after annealing) and pre-scale the parts
- A hot chamber crystallizes more during printing. Less annealing shrink, but maybe weaker welds since crystals form before the chains cross. Something to test, not assume

## 7. Shrinkage, stress, warping

*Long version: [handbook chapter 7](../handbook/07-shrink-stress-warp.md).*

Each new layer goes down hot on cooler layers. It wants to shrink as it cools, the layer under it
says no, and stress builds up layer by layer. It comes out as warp, curl, or layers splitting.
Rough size of it:

```math
\varepsilon_{th} \approx \alpha\,(T_{set} - T_{chamber}), \qquad \sigma \approx \frac{E\,\varepsilon_{th}}{1 - \nu}
```

$T_{set}$ is where the plastic stops flowing: about Tg for amorphous plastics, the crystallization
temperature for semi-crystalline ones. ABS ($\alpha \approx 90 \times 10^{-6}$ /K, $E \approx 2$ GPa):

| Chamber | ΔT from Tg (105 °C) | Built-in stress (upper bound) |
|---|---|---|
| 25 °C | 80 K | about 22 MPa |
| 70 °C | 35 K | about 10 MPa |

ABS breaks around 40 MPa. Some of that stress relaxes, so these are upper bounds, but it shows
why ABS cracks in a cold box and why 70 °C roughly halves the problem.
[Armillotta et al.](https://www.semanticscholar.org/paper/Warpage-of-FDM-parts:-Experimental-tests-and-model-Armillotta-Bellotti/9ee2ce3b84cf9620980c53c3bcd8544d8db7b4b5)
built a warp model for ABS blocks and found the worst warp at medium part heights, with heat from
the newest layer spreading stress into several layers below.

## 8. Moisture and degradation

Water does three things to a filament:

- **Plasticizes** it (nylon especially): softer, weaker
- **Hydrolyzes** it in the melt (PLA, PETG, PC, nylon): the heat plus water cuts the polymer chains. Lower viscosity, weaker parts, and **drying doesn't undo it**
- **Boils** in the nozzle: bubbles, popping, stringing

Studies on [nylon](https://doi.org/10.3390/technologies13080376) and
[PLA blends](https://pmc.ncbi.nlm.nih.gov/articles/PMC11442157/) show it in print quality and
strength. Long hot dwell does its own damage too (oxidation, color change).

For this printer: **wet filament shows up as "runnier than its library value."** Lower pressure
for the same flow, a flow ladder knee that moved up. The passive checks in
[library.md](../calibration/library.md#every-print-is-a-test) can flag "probably wet" before the
prints go bad. Dry first, before touching settings.

## 9. Fillers (CF, GF, matte, glow, wood)

- **Stiffer and they conduct heat better**, so they melt faster ([section 2](#2-melting-how-fast-the-hotend-can-go))
- **Fibers line up with the print path.** [Tekinalp et al. 2014](https://doi.org/10.1016/j.compscitech.2014.10.009) (ORNL) printed ABS with chopped carbon fiber: strength up about 115%, stiffness up about 700%, along the print direction. Across it, much less. Shrinkage goes anisotropic too
- **Abrasive.** The nozzle wears and the bore grows. The nozzle's resistance climbs steeply as the bore shrinks (between $d^{-2}$ and $d^{-4}$ depending on how shear-thinning the melt is), so wear shifts PA and flow slowly. The monthly anchor check catches that
- **Matte and glow fillers** move density and flow, which is why density is such a good tell

## 10. Predicting printability from properties

- [Duty et al. 2018](https://doi.org/10.1016/j.jmapro.2018.08.008): screen a material from its rheology and thermal properties (extrudable at the needed rate? holds its shape?)
- [Read et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11636983/): measure pressure vs flow vs temperature on the machine and pick settings from that, even for materials nobody had printed before. More in [control](control.md#the-closest-thing-to-what-i-want)
- [Das et al. 2021](https://doi.org/10.1021/acsapm.0c01228): a long review tying polymer rheology to print properties. The place to start reading

## Where this lands on the printer

| Finding | What I do with it |
|---|---|
| Shear thinning, one shift factor for everything | Matching temperature, PA that changes with flow |
| MFI measured 100× slower than printing | Datasheets as priors only |
| Graetz number heat limit | Compare hotends on paper, HF nozzles for high-flow materials |
| Bead shape from gap and speed ratio | Bead model, contour offset, first layer |
| Equivalent weld time | Chamber, layer time and fan policy for strength. IR sensor |
| Crystallization | PPA-CF annealing compensation |
| Thermal strain | Why 70 °C for ABS/ASA, with numbers |
| Moisture | "Probably wet" flag, dry before tuning |
| Fillers | Nozzle wear check, anisotropic shrink |

## References

- Armillotta, Bellotti, Cavallaro (2018). *Warpage of FDM parts: Experimental tests and analytic model.* Robotics and Computer-Integrated Manufacturing 50. [link](https://www.semanticscholar.org/paper/Warpage-of-FDM-parts:-Experimental-tests-and-model-Armillotta-Bellotti/9ee2ce3b84cf9620980c53c3bcd8544d8db7b4b5)
- Anderegg et al. (2019). *In-situ monitoring of polymer flow temperature and pressure in extrusion based additive manufacturing.* Additive Manufacturing 26. [link](https://www.researchgate.net/publication/330392702_In-Situ_Monitoring_of_Polymer_Flow_Temperature_and_Pressure_in_Extrusion_Based_Additive_Manufacturing)
- Bellehumeur, Li, Sun, Gu (2004). *Modeling of bond formation between polymer filaments in the fused deposition modeling process.* J. Manufacturing Processes 6(2). [doi](https://doi.org/10.1016/S1526-6125(04)70071-7)
- Bellini, Güçeri, Bertoldi (2004). *Liquefier dynamics in fused deposition.* J. Manufacturing Science and Engineering 126(2). [link](https://orbit.dtu.dk/en/publications/liquefier-dynamics-in-fused-deposition/)
- Comminal, Serdeczny, Pedersen, Spangenberg (2018). *Numerical modeling of the strand deposition flow in extrusion-based additive manufacturing.* Additive Manufacturing 20. [doi](https://doi.org/10.1016/j.addma.2017.12.013)
- Coogan, Kazmer (2019). *In-line rheological monitoring of fused deposition modeling.* J. Rheology 63(1). [link](https://www.researchgate.net/publication/330031420_In-line_rheological_monitoring_of_fused_deposition_modeling)
- Costanzo, Croce, Spotorno, Fenni, Cavallo (2020). *Fused deposition modeling of polyamides: crystallization and weld formation.* Polymers 12(12). [doi](https://doi.org/10.3390/polym12122980)
- Das, Gilmer, Biria, Bortner (2021). *Importance of polymer rheology on material extrusion additive manufacturing.* ACS Applied Polymer Materials 3(3). [doi](https://doi.org/10.1021/acsapm.0c01228)
- Duty et al. (2018). *What makes a material printable? A viscoelastic model for extrusion-based 3D printing of polymers.* J. Manufacturing Processes 35. [doi](https://doi.org/10.1016/j.jmapro.2018.08.008)
- Go, Schiffres, Stevens, Hart (2017). *Rate limits of additive manufacturing by fused filament fabrication and guidelines for high-throughput system design.* Additive Manufacturing 16. [link](https://www.sciencedirect.com/science/article/abs/pii/S2214860416302834)
- Go, Hart (2017). *Fast desktop-scale extrusion additive manufacturing.* [arXiv](https://arxiv.org/abs/1709.05918)
- Kishore et al. (2017). *Infrared preheating to improve interlayer strength of big area additive manufacturing (BAAM) components.* Additive Manufacturing 14. [doi](https://doi.org/10.1016/j.addma.2016.11.008)
- McIlroy, Olmsted (2017). *Disentanglement effects on welding behaviour of polymer melts during the fused-filament-fabrication method for additive manufacturing.* Polymer 123. [link](https://www.sciencedirect.com/science/article/abs/pii/S0032386117306213)
- Northcutt, Orski, Migler, Kotula (2018). *Effect of processing conditions on crystallization kinetics during materials extrusion additive manufacturing.* Polymer 154. [link](https://www.sciencedirect.com/science/article/abs/pii/S0032386118308541)
- Phan, Swain, Mackay (2018). *Rheological and heat transfer effects in fused filament fabrication.* J. Rheology 62(5). [doi](https://doi.org/10.1122/1.5022982)
- Read et al. (2024). *Online measurement for parameter discovery in fused filament fabrication.* Integrating Materials and Manufacturing Innovation 13. [link](https://pmc.ncbi.nlm.nih.gov/articles/PMC11636983/)
- Seppala, Han, Hillgartner, Davis, Migler (2017). *Weld formation during material extrusion additive manufacturing.* Soft Matter 13. [link](https://pubs.rsc.org/en/content/articlelanding/2017/sm/c7sm00950j)
- Tekinalp et al. (2014). *Highly oriented carbon fiber–polymer composites via additive manufacturing.* Composites Science and Technology 105. [doi](https://doi.org/10.1016/j.compscitech.2014.10.009)
- Tronvoll, Popp, Elverum, Welo (2019). *Investigating pressure advance algorithms for filament-based melt extrusion additive manufacturing.* Rapid Prototyping Journal 25(5). [link](https://www.emerald.com/rpj/article/25/5/830/363878/Investigating-pressure-advance-algorithms-for)
- Williams, Landel, Ferry (1955). *The temperature dependence of relaxation mechanisms in amorphous polymers and other glass-forming liquids.* J. American Chemical Society 77. (The WLF equation)
- Wool, O'Connor (1981). *A theory of crack healing in polymers.* J. Applied Physics 52. (Weld strength vs time)
- Wu, Qian, Okwudire (2023). *Modeling and feedforward control of filament advancement and retraction in material extrusion additive manufacturing.* Additive Manufacturing 78. [doi](https://doi.org/10.1016/j.addma.2023.103850)
- Moisture: [Influence of filament moisture on 3D printing nylon](https://doi.org/10.3390/technologies13080376) (Technologies, 2025) and [Effect of filament moisture on tensile properties and morphology of FDM PLA/PBS parts](https://pmc.ncbi.nlm.nih.gov/articles/PMC11442157/)
