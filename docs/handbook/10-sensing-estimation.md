# 10. Sensing and estimation

*Level 4. The math that turns sensor readings into knowledge.*

Everything so far has been physics. This chapter is about how a machine actually learns the numbers
in those equations, from noisy sensors, without me squinting at test prints. None of it is new. It's
standard control and statistics, borrowed from industries that figured it out decades ago.

## What we can see

The detailed list is in [sensors.md](../calibration/sensors.md). The short version: temperatures,
probe heights and the accelerometer today. Nozzle pressure, filament diameter and motion with the
planned sensors. Part mass with the scale. Part temperature and the actual bead shape, not at all.

## Observability

A hidden state is **observable** if some combination of measurements over time pins it down, even
though no sensor reads it directly. For a linear system

```math
\dot{x} = A x + B u, \qquad y = C x
```

the formal test is that the observability matrix has full rank:

```math
\operatorname{rank}\begin{bmatrix} C \\ CA \\ \vdots \\ CA^{n-1} \end{bmatrix} = n
```

Here's why that matters for a printer. Take the hotend model from chapter 9, with states block
temperature $T_b$ and sensor temperature $T_s$, measuring only $T_s$. Now add one more state: an
unknown, slowly varying "extra heat load" $d$, which is whatever the plastic is actually pulling out
of the block. Because $d$ shows up in the block dynamics and the block shows up in the sensor, the
augmented system is still observable. **A Kalman filter on the hotend can estimate how much plastic
is really flowing, from heater power and temperature alone.** That's the "heater power as a flow
sensor" idea from [library.md](../calibration/library.md#every-print-is-a-test), done properly.

Some things simply aren't observable with today's sensors. Nozzle pressure, for example: nothing
measures it and no model ties it uniquely to anything measured. That's why the pressure sensor
matters so much.

## Fitting a model: least squares

Say I log heater power and flow over a print and want the slope of

```math
P = a + b\,Q
```

Stack the data in a matrix $X$ (a column of ones and a column of flows) and the powers in $y$:

```math
\hat\theta = (X^T X)^{-1} X^T y, \qquad \operatorname{cov}(\hat\theta) = \sigma^2 (X^T X)^{-1}
```

The covariance comes for free, and it's just as important as the estimate. It says how much to trust
it.

## Updating as data comes in

Refitting from scratch every time is wasteful. Recursive least squares updates the estimate one
sample at a time, with a forgetting factor $\lambda$ (just under 1) so old data fades out:

```math
k_t = \frac{P_{t-1}\,x_t}{\lambda + x_t^T P_{t-1}\,x_t}
```

```math
\hat\theta_t = \hat\theta_{t-1} + k_t\left(y_t - x_t^T \hat\theta_{t-1}\right)
```

```math
P_t = \frac{1}{\lambda}\left(P_{t-1} - k_t\,x_t^T P_{t-1}\right)
```

The memory is roughly $1/(1 - \lambda)$ samples. Long memory for things that drift slowly (nozzle
wear), short memory for things that change during a print.

## The Kalman filter, scalar version

For one slowly drifting parameter $x$ (a flow residual, a PA value), measured with noise $r$, and
allowed to drift by $q$ between measurements:

```math
\text{predict:}\quad \hat{x}^- = \hat{x}, \qquad P^- = P + q
```

```math
\text{update:}\quad K = \frac{P^-}{P^- + r}, \qquad \hat{x} = \hat{x}^- + K\,(z - \hat{x}^-), \qquad P = (1 - K)\,P^-
```

With $q = 0$ that's exactly the "combine the prior and the measurement, weighted by how much you trust
each" update in [filament.md](../calibration/filament.md#how-sure-is-each-number). With $q > 0$ it also
knows things drift (filament getting wet, a nozzle wearing), so it never gets so confident that it
stops listening to new data.

## Designing tests that actually tell you something

Not all test points are equally useful. The Fisher information says how much a set of measurements
tells you about the parameters:

```math
I(\theta) = \sum_i \frac{1}{\sigma_i^2}\,\frac{\partial y_i}{\partial \theta}\left(\frac{\partial y_i}{\partial \theta}\right)^T, \qquad \operatorname{cov}(\hat\theta) \succeq I(\theta)^{-1}
```

The second part is the Cramér-Rao bound: no estimator can beat it. A **D-optimal** test design
picks the test points that maximize $\det I$.

You don't need the full machinery to use the intuition. To estimate a slope,

```math
\operatorname{var}(\hat{b}) = \frac{\sigma^2}{\sum_i (x_i - \bar{x})^2}
```

so **put the points at the ends.** That's why the flow ladder runs at two temperatures as far apart
as is safe, rather than five temperatures close together. And to locate a knee, cluster the points
near the knee, where the output is most sensitive to where the knee is.

**Persistent excitation** is the flip side: an estimator learns nothing about a slope if the input
never changes. A print at one constant flow says nothing about how heater power depends on flow.
Normal prints swing the flow around constantly, which is exactly why passive learning works.

Two related ideas from the research:

- [Single print optimisation](https://link.springer.com/article/10.1007/s00170-018-2518-4) (Greeff & Schilling 2018): merge a whole designed experiment into one G-code and print it once
- [Bayesian optimization](https://www.science.org/doi/10.1126/sciadv.aaz1708) (Gongora et al. 2020): pick each next experiment where it's expected to teach the most. About 60× fewer experiments than a grid search in their case

## Learning across prints

Chip fabs adjust a process between runs from measurements of the last run (Sachs, Hu & Ingolfsson,
1995). The basic EWMA run-to-run update, for a setting $u$ with sensitivity $\beta$ and target $y^{\ast}$:

```math
u_{k+1} = u_k - \frac{w}{\beta}\left(y_k - y^{\ast}\right)
```

Small $w$ is cautious and filters noise, larger $w$ reacts faster. The double EWMA version adds a
second filter that tracks steady drift, which is what nozzle wear looks like.

## When to react: SPC

The fastest way to make a process worse is to react to noise. Statistical process control says when
a change is real.

- **Shewhart rule:** flag a point more than $3\sigma$ from the mean. Catches big sudden shifts
- **CUSUM:** catches small, persistent shifts much faster:

```math
S_k = \max\left(0,\ S_{k-1} + x_k - \mu_0 - k\right), \qquad \text{alarm when } S_k > h
```

$k$ sets the size of shift you care about, $h$ how sure you want to be. For the monthly anchor check
(machine health), CUSUM on the anchor's numbers is the right tool: nozzle wear is a slow creep, not a
jump.

## Libraries are hierarchies

Family, brand line, color, spool. In statistics that's a hierarchical model, and the estimate at each
level gets "partially pooled" toward the level above:

```math
\hat\theta_{line} = \frac{n\,\bar{y}/\sigma^2 + \theta_{family}/\tau^2}{n/\sigma^2 + 1/\tau^2}
```

With few measurements ($n$ small) a line's estimate stays close to its family. With lots, it trusts
its own data. The spreads ($\tau$ between lines in a family, between colors in a line, between spools
in a color) can be estimated from the library itself once it has enough entries. That tells you, with
numbers, how much testing a new color actually needs compared to a new brand.

## Moving knowledge between machines

Calibration transfer (chemometrics, [Wang, Veltkamp & Kowalski 1991](https://pubs.acs.org/doi/10.1021/ac00023a016)):
measure a few standards on both machines and map one onto the other. For a ratio-type parameter it
collapses to one factor, estimated in log space:

```math
\hat{h} = \exp\left(\frac{1}{N}\sum_{a=1}^{N}\log\frac{y_{here}(a)}{y_{src}(a)}\right)
```

That's how the Bambu library maps onto this printer ([library.md](../calibration/library.md#the-catch-other-machines)).

## What I'd like to implement first

Nothing here exists yet. If I get to it, this is the order:

1. A logger on the Pi with recursive least squares on heater power vs flow, per print
2. CUSUM on the anchor's numbers, for machine health
3. EWMA run-to-run updates of the flow residual from weighed parts
4. Scalar Kalman updates for every library value, with drift ($q$) set per parameter

## References

- Ljung (1999). *System Identification: Theory for the User.* Prentice Hall
- Kalman (1960). *A new approach to linear filtering and prediction problems.* J. Basic Engineering 82
- Sachs, Hu, Ingolfsson (1995). *Run by run process control: combining SPC and feedback control.* IEEE Trans. Semiconductor Manufacturing 8(1)
- Page (1954). *Continuous inspection schemes.* Biometrika 41 (CUSUM)
- Montgomery. *Introduction to Statistical Quality Control.* Wiley
- Gelman et al. *Bayesian Data Analysis.* (Hierarchical models)
- [Wang, Veltkamp, Kowalski (1991)](https://pubs.acs.org/doi/10.1021/ac00023a016). Calibration transfer
- [Greeff, Schilling (2018)](https://link.springer.com/article/10.1007/s00170-018-2518-4) and [Gongora et al. (2020)](https://www.science.org/doi/10.1126/sciadv.aaz1708)
