# Filament library without the testing

The intake tests in [filament.md](filament.md) work, but doing them for every new filament is
exactly the kind of chore I'm trying to get rid of. What I actually want is the Bambu experience:
pick the spool, hit print, it's fine.

That works on the Bambus because somebody else did the testing. Bambu tested their filaments on
their hotends, and the printers measure the rest themselves. So the plan:

1. **Borrow other people's testing.** There's a lot more tested data out there than I thought
2. **Map it onto this machine once,** using a few anchors measured here
3. **Let the machine check it during normal prints,** no test prints
4. **Only test when something looks off**

The tests in [filament.md](filament.md) become the exception path: anchors, oddball materials,
and whatever the machine flags.

## Tested data that already exists

| Source | What's in it | Notes |
|---|---|---|
| Bambu Studio system profiles | About 2,050 profiles covering 126 filaments, already on this PC. Max flow, density, flow ratio, temps, cooling | Tuned on Bambu hotends. Bambu PLA Basic: 1.26 g/cm³, 21 mm³/s, flow 0.98. Bambu PETG HF: 1.28, 21, 245 °C, 0.95. eSUN PLA+: 1.25, 16 |
| My own Bambus | PA per filament (Bambu measures it, "flow dynamics"), my tuned shrinkage and flow | The X1C measures PA by itself |
| [OrcaFilamentLibrary](https://github.com/OrcaSlicer/OrcaSlicer/pull/8057) | Vendor-neutral filament profiles in Orca, any printer can inherit them | Same kind of data as Bambu's, more brands |
| [3D Filament Profiles](https://3dfilamentprofiles.com/) | Community submissions: PA K values, temps, more | Quality varies. There's a [converter to Orca profiles](https://github.com/mhord/OrcaSlicer_Filament_Profile_Generator) |
| [SpoolmanDB](https://github.com/Donkie/SpoolmanDB) | Density, diameter, spool weights, temps per brand, line and color | Feeds [Spoolman](https://github.com/Donkie/Spoolman), which plugs into Moonraker |
| [OpenPrintTag](https://blog.prusa3d.com/the-openprinttag-is-here-a-brand-new-nfc-tag-standard-for-smart-filament-is-now-shipped-with-a-new-redesigned-prusament-spool_123878/) | Open NFC tag standard from Prusa: brand, material, diameter, weights, temps, remaining filament (writable) | Comes on the new Prusament spools. Blank tags exist for other spools |
| [OpenSpool](https://simplyprint.io/features/filament-management/nfc/openspool) | DIY NFC tags: plain JSON on cheap NTAG stickers | Write once per spool with a phone |
| [Prusament](https://prusament.com/) spool QR | Measured diameter, ovality and deviation for that exact spool | The only brand I know of that ships per-spool measurements |
| Manufacturer datasheets | Density, melt flow index, Tg, heat deflection | Good priors, weak on how it actually prints |

## The catch: other machines

*The math behind mapping one machine onto another: [handbook chapter 10](../handbook/10-sensing-estimation.md#moving-knowledge-between-machines).*

All of that was measured on somebody else's hotend. Bambu PLA Basic's 21 mm³/s is the Bambu
hotend with a 0.4, not the Conch with a 0.6. Temperatures mostly transfer. Max flow and PA don't.

The fix is to borrow **the differences between filaments**, not the raw numbers. If Bambu's data
says filament $f$ flows 20% less than Bambu PLA Basic, it probably flows about 20% less on my
machine too. Measure a few anchors here that also exist in the source, and for everything else:

```math
y_{here}(f) \approx y_{here}(a)\,\frac{y_{src}(f)}{y_{src}(a)}
```

With several anchors, it's one fitted number per parameter and per source, in log space:

```math
\log y_{here} = \log h + \log y_{src}
```

$h$ is "this machine relative to that source." The scatter between anchors says how far to trust
it. Chemists have done exactly this with spectrometers since the 90s, it's called calibration
transfer: measure a handful of standards on both instruments, map one onto the other
([research](../research/other-fields.md#chemometrics-calibration-transfer)). The anchors are my
standards.

Where it breaks: when two filaments hit different limits (one runs out of heat, the other out of
extruder force), or for materials nowhere near any anchor. That's what the scatter and the
passive checks below are for.

## Know what's loaded without typing anything

- **Spoolman** on the Pi, hooked into Moonraker. Every spool gets an ID, usage gets tracked, SpoolmanDB fills in the brand data
- **Spool ID:** QR label first (Spoolman prints them), NFC later (OpenPrintTag or OpenSpool, phone or a reader on the Pi)
- Picking the spool sets the machine's active spool (`SPOOL_SET`), which pulls its profile and area correction
- `PRINT_START` checks the sliced filament against the active spool and complains if they don't match

## Every print is a test

*The estimation side (observability, recursive least squares, run-to-run): [handbook chapter 10](../handbook/10-sensing-estimation.md#observability).*

The machine already logs enough to check a filament during normal prints. Kalico reports live
extruder velocity and heater power through Moonraker, so a small logger on the Pi can watch every
print. Normal prints swing the flow around all the time (walls, infill, travel), which is exactly
what an estimator needs.

| Signal | Have it? | Tells me |
|---|---|---|
| Heater power vs flow | Now | Heat load per mm³, and when the heater runs out of headroom (max flow) |
| Hotend temp droop at high flow | Now | How close to the melt limit |
| Buffer drift | Now | Slip |
| Weighing finished parts vs Orca's estimate | When the scale shows up | Flow residual |
| Pressure transients | bd_pressureE | PA, viscosity, wet filament (it gets runnier), clogs |
| Diameter + filament motion | BDwidth | Spool area, slip |
| Camera | Later | First layer, stringing, spaghetti |

The heater one works today. Power going into the hotend is losses plus heating the plastic:

```math
P_{heater} = P_{loss}(T,\ \text{fan}) + \rho\,c\,(T - T_{fil})\,Q
```

Fit the slope of heater power against flow over a print. For a known material, $\rho c$ is known
within about 10%, so a slope that's off means the plastic actually going through isn't what was
commanded (slip, partial clog) or the material isn't what the profile says.

Each print nudges the estimates, the way fabs tune a process between wafers
([run-to-run control](../research/other-fields.md#semiconductor-fabs-run-to-run-control-and-spc)):

```math
\hat{\theta}_{k+1} = \hat{\theta}_k + w\,(\theta_k - \hat{\theta}_k), \qquad 0 < w \le 1
```

Small $w$ ignores noise, big $w$ reacts fast. And it only updates when the new number is outside
the noise band, so it doesn't chase noise.

## Only test when something's off

The machine raises a flag when:

- An estimate wanders more than 3σ from the library value
- The heater runs out of headroom below the expected max flow
- Slip shows up where it shouldn't
- I see a defect. [quality.md](quality.md) says which parameter, so I test that one only
- A filament has no data anywhere and isn't close to any anchor (CF, PPA, TPU)

| Situation | What I do | Time |
|---|---|---|
| Known line, new spool | Pick it or scan it | 0 |
| Known line, new color | Pick it, the machine watches the first prints | 0 |
| New line with data somewhere | Import, the machine maps it | 1 min |
| New line, no data, common material | Family defaults + watched prints, ladder only if flagged | 0 to 15 min |
| Odd stuff (CF, PPA, TPU) | Full intake | 30 to 60 min |
| A flag goes off | Test that parameter | 5 to 15 min |

## Buy filament that comes with data

The cheapest tested library is buying filament somebody already tested. Consistent brands with
published profiles (Bambu, Polymaker, Prusament, whatever's in the Orca library) cost nothing.
Random cheap brands are where all the testing time goes. Not exciting, but true.

## Later: a shared library

If other people running pressure sensors on Klipper logged their filaments against the same
common anchors (Bambu PLA Basic is everywhere and very consistent), the library would fill itself.
Filaments × machines is a big table with holes in it, and recommender systems are built to fill
exactly those ([research](../research/other-fields.md#recommender-systems)):

```math
y_{f,m} \approx \sum_{k=1}^{r} u_{f,k}\,v_{m,k}
```

$r = 1$ is the ratio idea above: a filament factor times a machine factor. Could be a public repo,
like the buffer plugin.

## To do

- [ ] Spoolman on the Pi, connected to Moonraker
- [ ] Pull density, max flow, flow ratio and temps from the Bambu/Orca libraries for everything I own
- [ ] Logger on the Pi: heater power, temperature, live extruder velocity, fan, per print
- [ ] Pick anchors that exist in the Bambu library, measure them here, fit $h$
- [ ] Flags in the logger (3σ, headroom, slip)
- [ ] QR labels from Spoolman, NFC later
- [ ] Check how good the 3D Filament Profiles data really is before trusting any of it
