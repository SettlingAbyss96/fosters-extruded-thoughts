"""Generate the handbook figures as plain SVG files.

No dependencies beyond the Python standard library, so anyone can rerun it:

    python make_figures.py

Every curve comes from the same toy models and numbers used in the chapters.
"""

import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = "Segoe UI, Helvetica, Arial, sans-serif"
BLUE = "#2563eb"
ORANGE = "#ea580c"
GREEN = "#16a34a"
RED = "#dc2626"
GRAY = "#6b7280"
PURPLE = "#7c3aed"
INK = "#111827"
GRID = "#e5e7eb"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def fmt(v):
    if abs(v) >= 1000 and float(v).is_integer():
        return f"{int(v):,}"
    if float(v).is_integer():
        return str(int(v))
    return f"{v:g}"


class Plot:
    def __init__(self, title, xlabel, ylabel, xlim, ylim, xlog=False, ylog=False,
                 w=760, h=430, ml=78, mr=28, mt=60, mb=64, subtitle=None):
        self.title, self.subtitle = title, subtitle
        self.xlabel, self.ylabel = xlabel, ylabel
        self.xlim, self.ylim = xlim, ylim
        self.xlog, self.ylog = xlog, ylog
        self.w, self.h = w, h
        self.ml, self.mr, self.mt, self.mb = ml, mr, mt, mb
        self.back = []
        self.items = []
        self.legend_items = []

    def _t(self, v, lim, log):
        if log:
            a, b = math.log10(lim[0]), math.log10(lim[1])
            return (math.log10(v) - a) / (b - a)
        return (v - lim[0]) / (lim[1] - lim[0])

    def X(self, x):
        return self.ml + self._t(x, self.xlim, self.xlog) * (self.w - self.ml - self.mr)

    def Y(self, y):
        return self.h - self.mb - self._t(y, self.ylim, self.ylog) * (self.h - self.mt - self.mb)

    def axes(self, xticks, yticks, xlabels=None, ylabels=None):
        x0, x1 = self.ml, self.w - self.mr
        y0, y1 = self.mt, self.h - self.mb
        for i, t in enumerate(xticks):
            x = self.X(t)
            self.back.append(f'<line x1="{x:.1f}" y1="{y0}" x2="{x:.1f}" y2="{y1}" stroke="{GRID}"/>')
            lab = xlabels[i] if xlabels else fmt(t)
            self.back.append(f'<text x="{x:.1f}" y="{y1 + 20}" font-size="13" text-anchor="middle" fill="{GRAY}">{esc(lab)}</text>')
        for i, t in enumerate(yticks):
            y = self.Y(t)
            self.back.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" stroke="{GRID}"/>')
            lab = ylabels[i] if ylabels else fmt(t)
            self.back.append(f'<text x="{x0 - 8}" y="{y + 4:.1f}" font-size="13" text-anchor="end" fill="{GRAY}">{esc(lab)}</text>')
        self.back.append(f'<line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y1}" stroke="{INK}" stroke-width="1.2"/>')
        self.back.append(f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1}" stroke="{INK}" stroke-width="1.2"/>')

    def band_x(self, a, b, color, label=None, opacity=0.12):
        x0, x1 = self.X(a), self.X(b)
        self.back.append(f'<rect x="{x0:.1f}" y="{self.mt}" width="{x1 - x0:.1f}" height="{self.h - self.mt - self.mb}" fill="{color}" opacity="{opacity}"/>')
        if label:
            self.back.append(f'<text x="{(x0 + x1) / 2:.1f}" y="{self.mt + 16}" font-size="12.5" text-anchor="middle" fill="{color}">{esc(label)}</text>')

    def band_y(self, a, b, color, label=None, opacity=0.12, label_x=None):
        y0, y1 = self.Y(b), self.Y(a)
        self.back.append(f'<rect x="{self.ml}" y="{y0:.1f}" width="{self.w - self.ml - self.mr}" height="{y1 - y0:.1f}" fill="{color}" opacity="{opacity}"/>')
        if label:
            lx = self.X(label_x) if label_x is not None else self.w - self.mr - 6
            anchor = "middle" if label_x is not None else "end"
            self.back.append(f'<text x="{lx:.1f}" y="{(y0 + y1) / 2 + 4:.1f}" font-size="12.5" text-anchor="{anchor}" fill="{color}">{esc(label)}</text>')

    def hline(self, y, color, label=None, dash="6 4"):
        yy = self.Y(y)
        self.items.append(f'<line x1="{self.ml}" y1="{yy:.1f}" x2="{self.w - self.mr}" y2="{yy:.1f}" stroke="{color}" stroke-width="1.5" stroke-dasharray="{dash}"/>')
        if label:
            self.items.append(f'<text x="{self.w - self.mr - 6}" y="{yy - 6:.1f}" font-size="12.5" text-anchor="end" fill="{color}">{esc(label)}</text>')

    def vline(self, x, color, label=None, dash="4 4", label_y=None, anchor="start"):
        xx = self.X(x)
        self.items.append(f'<line x1="{xx:.1f}" y1="{self.mt}" x2="{xx:.1f}" y2="{self.h - self.mb}" stroke="{color}" stroke-width="1.4" stroke-dasharray="{dash}"/>')
        if label:
            ly = self.Y(label_y) if label_y is not None else self.mt + 16
            dx = 5 if anchor == "start" else -5
            self.items.append(f'<text x="{xx + dx:.1f}" y="{ly:.1f}" font-size="12.5" text-anchor="{anchor}" fill="{color}">{esc(label)}</text>')

    def line(self, pts, color, label=None, width=2.6, dash=None):
        pts = [(x, y) for x, y in pts
               if self.xlim[0] <= x <= self.xlim[1] and self.ylim[0] <= y <= self.ylim[1]]
        d = " ".join(f"{'M' if i == 0 else 'L'}{self.X(x):.1f},{self.Y(y):.1f}"
                     for i, (x, y) in enumerate(pts))
        da = f' stroke-dasharray="{dash}"' if dash else ""
        self.items.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round"{da}/>')
        if label:
            self.legend_items.append((label, color, dash))

    def point(self, x, y, color, r=4.5):
        self.items.append(f'<circle cx="{self.X(x):.1f}" cy="{self.Y(y):.1f}" r="{r}" fill="{color}" stroke="white" stroke-width="1.5"/>')

    def text(self, x, y, s, color=INK, size=12.5, anchor="start", dx=0, dy=0, weight="normal"):
        self.items.append(f'<text x="{self.X(x) + dx:.1f}" y="{self.Y(y) + dy:.1f}" font-size="{size}" text-anchor="{anchor}" fill="{color}" font-weight="{weight}">{esc(s)}</text>')

    def callout(self, xt, yt, xp, yp, s, color=INK, anchor="start"):
        self.items.append(f'<line x1="{self.X(xt):.1f}" y1="{self.Y(yt) + 4:.1f}" x2="{self.X(xp):.1f}" y2="{self.Y(yp):.1f}" stroke="{GRAY}" stroke-width="1"/>')
        dx = 4 if anchor == "start" else -4
        self.items.append(f'<text x="{self.X(xt) + dx:.1f}" y="{self.Y(yt):.1f}" font-size="12.5" text-anchor="{anchor}" fill="{color}">{esc(s)}</text>')

    def legend(self, pos="tr"):
        if not self.legend_items:
            return
        n = len(self.legend_items)
        bw = max(len(l) for l, _, _ in self.legend_items) * 7.2 + 48
        bh = n * 20 + 12
        x = self.w - self.mr - bw - 10 if pos.endswith("r") else self.ml + 10
        y = self.mt + 10 if pos.startswith("t") else self.h - self.mb - bh - 10
        self.items.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{bh}" rx="6" fill="white" stroke="{GRID}"/>')
        for i, (lab, col, dash) in enumerate(self.legend_items):
            yy = y + 18 + i * 20
            da = f' stroke-dasharray="{dash}"' if dash else ""
            self.items.append(f'<line x1="{x + 10:.1f}" y1="{yy - 4:.1f}" x2="{x + 34:.1f}" y2="{yy - 4:.1f}" stroke="{col}" stroke-width="3"{da}/>')
            self.items.append(f'<text x="{x + 42:.1f}" y="{yy:.1f}" font-size="12.5" fill="{INK}">{esc(lab)}</text>')

    def svg(self):
        out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}" font-family="{FONT}">',
               f'<rect x="0.5" y="0.5" width="{self.w - 1}" height="{self.h - 1}" rx="10" fill="white" stroke="{GRID}"/>',
               f'<text x="{self.ml}" y="28" font-size="16" font-weight="600" fill="{INK}">{esc(self.title)}</text>']
        if self.subtitle:
            out.append(f'<text x="{self.ml}" y="47" font-size="12.5" fill="{GRAY}">{esc(self.subtitle)}</text>')
        out += self.back + self.items
        cx = (self.ml + self.w - self.mr) / 2
        out.append(f'<text x="{cx:.1f}" y="{self.h - 16}" font-size="13.5" text-anchor="middle" fill="{INK}">{esc(self.xlabel)}</text>')
        cy = (self.mt + self.h - self.mb) / 2
        out.append(f'<text x="24" y="{cy:.1f}" font-size="13.5" text-anchor="middle" fill="{INK}" transform="rotate(-90 24 {cy:.1f})">{esc(self.ylabel)}</text>')
        out.append("</svg>")
        return "\n".join(out) + "\n"


def save(name, svg):
    with open(os.path.join(HERE, name), "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)
    print("wrote", name)


def logspace(a, b, n=300):
    la, lb = math.log10(a), math.log10(b)
    return [10 ** (la + (lb - la) * i / (n - 1)) for i in range(n)]


def linspace(a, b, n=300):
    return [a + (b - a) * i / (n - 1) for i in range(n)]


# Chapter 2: shear thinning, and why MFI is a weak predictor
def shear_thinning():
    def cross(g, eta0, lam, n):
        return eta0 / (1 + (lam * g) ** (1 - n))

    a = (3000.0, 0.01, 0.35)
    target = cross(10, *a)
    lam_b, n_b = 0.02, 0.55
    b = (target * (1 + (lam_b * 10) ** (1 - n_b)), lam_b, n_b)

    p = Plot("Same MFI, different printing", "Shear rate (1/s, log scale)",
             "Viscosity (Pa·s, log scale)", (0.1, 1e5), (30, 6000), xlog=True, ylog=True,
             subtitle="Two made-up filaments that match where MFI is measured, and differ where you print")
    p.band_x(3, 30, GRAY, "MFI test")
    p.band_x(300, 5000, ORANGE, "Nozzle, printing")
    p.axes([0.1, 1, 10, 100, 1000, 10000, 100000], [30, 100, 300, 1000, 3000],
           ["0.1", "1", "10", "100", "1k", "10k", "100k"], ["30", "100", "300", "1,000", "3,000"])
    gs = logspace(0.1, 1e5)
    p.line([(g, cross(g, *a)) for g in gs], BLUE, "Filament A (shear-thins more)")
    p.line([(g, cross(g, *b)) for g in gs], PURPLE, "Filament B (shear-thins less)")
    ea, eb = cross(1000, *a), cross(1000, *b)
    p.point(10, target, INK)
    p.text(10, target, "same here", dx=8, dy=-10)
    p.point(1000, ea, BLUE)
    p.point(1000, eb, PURPLE)
    p.text(1000, eb, f"{round(100 * (eb / ea - 1))}% apart here", dx=8, dy=-10)
    p.legend("bl")
    save("shear-thinning.svg", p.svg())


# Chapter 2: WLF shift factor with the universal constants
def wlf_shift():
    def speedup(d):
        return 17.44 * d / (51.6 + d)

    p = Plot("A few tens of degrees near Tg changes everything", "Degrees above Tg (K)",
             "Speed-up vs at Tg (log10)", (0, 100), (0, 12.5),
             subtitle="WLF equation with the universal constants (C1 = 17.44, C2 = 51.6 K)")
    p.axes([0, 20, 40, 60, 80, 100], [0, 2, 4, 6, 8, 10, 12])
    p.line([(d, speedup(d)) for d in linspace(0, 100)], BLUE)
    for d, lab in [(10, "700×"), (30, "2.6 million×"), (50, "400 million×"), (75, "20 billion×")]:
        p.point(d, speedup(d), BLUE)
        p.text(d, speedup(d), lab, dx=8, dy=16)
    p.vline(65, ORANGE, "ABS interface, 50 °C chamber", label_y=2.2, anchor="end")
    p.vline(75, GREEN, "70 °C chamber", label_y=1.2)
    p.text(36, 11.2, "65 K to 75 K above Tg: about 4× faster", color=INK, anchor="middle")
    save("wlf-shift.svg", p.svg())


# Chapter 3: time in the hot zone vs flow
def melt_time():
    af = math.pi * 1.75 ** 2 / 4
    p = Plot("Where max flow comes from", "Flow (mm³/s)", "Time in the hot zone (s)",
             (0, 45), (0, 16), subtitle="1.75 mm filament. The shaded band is roughly how long the core needs")
    p.band_y(3, 6, ORANGE, "time the core needs (rough)", label_x=36)
    p.axes([0, 10, 20, 30, 40], [0, 4, 8, 12, 16])
    for L, col in [(20, GRAY), (30, BLUE), (40, GREEN)]:
        p.line([(q, L * af / q) for q in linspace(L * af / 15.8, 45)], col, f"{L} mm melt zone")
    q_mid = 30 * af / 4.5
    p.point(q_mid, 4.5, BLUE)
    p.callout(24, 10, q_mid, 4.5, f"30 mm zone: about {q_mid:.0f} mm³/s")
    p.legend("tr")
    save("melt-time.svg", p.svg())


# Chapter 4: pressure advance on a trapezoidal flow profile
def pa_step():
    tau = 0.04
    t_on, ramp, t_off = 0.05, 0.04, 0.25

    def q_cmd(t):
        if t < t_on:
            return 0.0
        if t < t_on + ramp:
            return (t - t_on) / ramp
        if t < t_off:
            return 1.0
        if t < t_off + ramp:
            return 1 - (t - t_off) / ramp
        return 0.0

    def dq(t):
        if t_on <= t < t_on + ramp:
            return 1 / ramp
        if t_off <= t < t_off + ramp:
            return -1 / ramp
        return 0.0

    def sim(K, dt=1e-5, t_end=0.4):
        q, out, t = 0.0, [], 0.0
        while t <= t_end:
            qin = q_cmd(t) + K * dq(t)
            q += dt * (qin - q) / tau
            if int(round(t / dt)) % 200 == 0:
                out.append((t * 1000, q))
            t += dt
        return out

    p = Plot("What pressure advance does", "Time (ms)", "Flow out (fraction of target)",
             (0, 400), (-0.4, 2.0), subtitle="First-order nozzle with τ = 40 ms, trapezoidal flow command")
    p.axes([0, 100, 200, 300, 400], [-0.4, 0, 0.4, 0.8, 1.2, 1.6])
    p.line([(t * 1000, q_cmd(t)) for t in linspace(0, 0.4, 801)], GRAY, "Commanded", width=2, dash="6 4")
    p.line(sim(0), BLUE, "No PA: late, then oozes")
    p.line(sim(tau), GREEN, "PA = τ: right on")
    p.line(sim(1.6 * tau), ORANGE, "Too much PA: overshoot, then a gap")
    p.legend("tr")
    save("pa-step-response.svg", p.svg())


# Chapter 4: effective PA vs flow for shear-thinning melts
def pa_vs_flow():
    p = Plot("Faster printing needs less PA", "Flow relative to where PA was tuned",
             "PA needed, relative", (0.25, 4), (0, 2.5),
             subtitle="Power-law melt: the effective time constant goes as flow to the power (n − 1)")
    p.axes([0.25, 1, 2, 3, 4], [0, 0.5, 1, 1.5, 2, 2.5], ["0.25×", "1×", "2×", "3×", "4×"])
    qs = linspace(0.25, 4)
    for n, col in [(1.0, GRAY), (0.6, BLUE), (0.4, ORANGE)]:
        lab = "n = 1 (honey)" if n == 1 else f"n = {n}"
        p.line([(q, q ** (n - 1)) for q in qs], col, lab)
    p.point(2, 2 ** -0.6, ORANGE)
    p.text(2, 2 ** -0.6, "0.66 at twice the flow", anchor="end", dx=-10, dy=26)
    p.legend("tr")
    save("pa-vs-flow.svg", p.svg())


# Chapter 5: bead cross-sections, normal vs extra wide
def bead_contact():
    s = 280.0
    W, H = 900, 340
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">',
           f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="10" fill="white" stroke="{GRID}"/>',
           f'<text x="40" y="30" font-size="16" font-weight="600" fill="{INK}">Same layer height, wider line: more of each layer is stuck to the next</text>',
           f'<text x="40" y="50" font-size="12.5" fill="{GRAY}">Idealized rounded-rectangle beads. Red = bonded contact between layers. White gaps = voids</text>']

    def bead(x0, y0, w, h):
        wp, hp, r = w * s, h * s, h * s / 2
        return (f'<path d="M{x0 + r:.1f},{y0:.1f} H{x0 + wp - r:.1f} A{r:.1f},{r:.1f} 0 0 1 {x0 + wp - r:.1f},{y0 + hp:.1f} '
                f'H{x0 + r:.1f} A{r:.1f},{r:.1f} 0 0 1 {x0 + r:.1f},{y0:.1f} Z" fill="#fcd9b6" stroke="#c2410c" stroke-width="1.5"/>')

    def panel(x0, y0, w, h, count, label, frac):
        for layer in range(2):
            for i in range(count):
                out.append(bead(x0 + i * w * s, y0 + layer * h * s, w, h))
        for i in range(count):
            bx = x0 + i * w * s
            r = h * s / 2
            yc = y0 + h * s
            out.append(f'<line x1="{bx + r:.1f}" y1="{yc:.1f}" x2="{bx + w * s - r:.1f}" y2="{yc:.1f}" stroke="{RED}" stroke-width="4"/>')
        cx = x0 + count * w * s / 2
        out.append(f'<text x="{cx:.1f}" y="{y0 + 2 * h * s + 34:.1f}" font-size="14" text-anchor="middle" fill="{INK}">{esc(label)}</text>')
        out.append(f'<text x="{cx:.1f}" y="{y0 + 2 * h * s + 56:.1f}" font-size="15" font-weight="600" text-anchor="middle" fill="{RED}">{esc(frac)}</text>')

    panel(60, 120, 0.45, 0.2, 3, "0.4 nozzle: three 0.45 mm lines, 0.2 mm layers", "about 56% bonded")
    panel(500, 120, 1.2, 0.2, 1, "Extra wide: one 1.2 mm line, 0.2 mm layers", "about 83% bonded")
    out.append("</svg>")
    save("bead-contact.svg", "\n".join(out) + "\n")


# Chapter 5: bonded fraction vs width-to-height ratio
def contact_fraction():
    p = Plot("Bonded fraction between layers", "Line width / layer height",
             "Bonded fraction (%)", (1, 8), (0, 100),
             subtitle="Idealized geometry: bonded fraction = 1 − h/w")
    p.axes([1, 2, 3, 4, 5, 6, 7, 8], [0, 20, 40, 60, 80, 100])
    p.line([(r, 100 * (1 - 1 / r)) for r in linspace(1, 8)], BLUE)
    for r, lab, dy in [(0.45 / 0.28, "0.4 nozzle, 0.45 × 0.28 mm", 18),
                       (0.45 / 0.20, "0.4 nozzle, 0.45 × 0.20 mm", 18),
                       (1.5 / 0.3, "0.6 nozzle, extra wide 1.5 × 0.3 mm", 22),
                       (1.2 / 0.2, "0.4 nozzle, extra wide 1.2 × 0.2 mm", -14)]:
        y = 100 * (1 - 1 / r)
        p.point(r, y, ORANGE)
        if dy < 0:
            p.text(r, y, lab, anchor="end", dx=-6, dy=dy)
        else:
            p.text(r, y, lab, dx=8, dy=dy)
    save("contact-fraction.svg", p.svg())


# Chapter 6: interface temperature after deposition, two chamber temperatures
def interface_temp():
    tg, tau = 105.0, 5.0
    cases = [(50.0, 170.0, ORANGE, "50 °C chamber"), (70.0, 180.0, GREEN, "70 °C chamber")]
    p = Plot("ABS: how long the interface stays above Tg", "Time after the bead lands (s)",
             "Interface temperature (°C)", (0, 10), (40, 200),
             subtitle="Toy model: starts halfway between nozzle (250 °C) and old layer, cools with τ = 5 s")
    p.axes([0, 2, 4, 6, 8, 10], [40, 80, 120, 160, 200])
    p.hline(tg, RED, "ABS Tg, about 105 °C")
    for ch, t0, col, lab in cases:
        p.line([(t, ch + (t0 - ch) * math.exp(-t / tau)) for t in linspace(0, 10)], col, lab)
        t_above = tau * math.log((t0 - ch) / (tg - ch))
        p.point(t_above, tg, col)
        p.text(t_above, tg, f"{t_above:.1f} s above Tg", color=col, dx=6, dy=-10 if ch == 70 else 20)
    p.legend("tr")
    save("interface-temperature.svg", p.svg())


# Chapter 6: equivalent weld time accumulated, same two cases
def weld_time():
    tg, tau = 105.0, 5.0

    def log_a(d):
        return -17.44 * d / (51.6 + d)

    ref = log_a(30)
    results = []
    for ch, t0, col, lab in [(50.0, 170.0, ORANGE, "50 °C chamber"), (70.0, 180.0, GREEN, "70 °C chamber")]:
        dt, t, acc, pts = 1e-3, 0.0, 0.0, []
        while t <= 10:
            d = ch + (t0 - ch) * math.exp(-t / tau) - tg
            if d > 0:
                acc += dt * 10 ** (ref - log_a(d))
            if t >= 0.02 and int(round(t / dt)) % 20 == 0:
                pts.append((t, acc))
            t += dt
        results.append((pts, col, lab, acc))
    hi = 10 ** math.ceil(math.log10(max(r[3] for r in results)))
    p = Plot("Most of the weld happens in the first second", "Time after the bead lands (s)",
             "Weld time (s at Tg + 30 K, log)", (0, 10), (1, hi), ylog=True,
             subtitle="Same toy model, weighted by the WLF shift factor (universal constants)")
    yt = [10 ** k for k in range(0, int(math.log10(hi)) + 1)]
    p.axes([0, 2, 4, 6, 8, 10], yt, None, [fmt(v) for v in yt])
    for pts, col, lab, acc in results:
        p.line(pts, col, f"{lab}: {acc:,.0f} s total")
    ratio = results[1][3] / results[0][3]
    p.text(5, results[0][3], f"about {ratio:.0f}× more weld time with the hotter chamber", dx=0, dy=40, anchor="middle")
    p.legend("br")
    save("weld-time.svg", p.svg())


# Chapter 7: Stoney toy model, which layers drive warp
def stoney_layers():
    total = math.pi ** 2 / 6
    shares = [100 / (m * m) / total for m in range(1, 11)]
    cum = [sum(shares[:i + 1]) for i in range(10)]
    p = Plot("Toy model: warp gets decided in the first few layers", "Layers already printed when the new one goes down (m)",
             "Share of bending tendency (%)", (0.5, 10.5), (0, 100),
             subtitle="Stoney's formula per layer goes as 1/m². Bars: each layer. Line: running total")
    p.axes(list(range(1, 11)), [0, 20, 40, 60, 80, 100])
    bw = (p.X(1.4) - p.X(1.0))
    for i, v in enumerate(shares, start=1):
        x = p.X(i) - bw / 2
        y = p.Y(v)
        p.back.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{p.Y(0) - y:.1f}" fill="{BLUE}" opacity="0.85"/>')
    p.line([(i, c) for i, c in enumerate(cum, start=1)], ORANGE, "Running total")
    for i in range(1, 11):
        p.point(i, cum[i - 1], ORANGE, r=3.5)
    p.text(3, cum[2], f"first 3 layers: {cum[2]:.0f}%", dx=10, dy=24)
    p.legend("br")
    save("stoney-layers.svg", p.svg())


# Chapter 8: zero-vibration input shaper, two impulses cancelling
def input_shaping():
    f, z = 40.0, 0.07
    w0 = 2 * math.pi * f
    wd = w0 * math.sqrt(1 - z * z)
    t2 = math.pi / wd
    K = math.exp(-z * math.pi / math.sqrt(1 - z * z))
    a1, a2 = 1 / (1 + K), K / (1 + K)

    def ring(t, a, ti):
        if t < ti:
            return 0.0
        return a * math.exp(-z * w0 * (t - ti)) * math.sin(wd * (t - ti))

    ts = linspace(0, 0.1, 1001)
    p = Plot("How a ZV shaper cancels ringing", "Time (ms)", "Toolhead ringing (relative)",
             (0, 100), (-1.0, 1.0), subtitle=f"40 Hz resonance, damping 0.07. Second hit {t2 * 1000:.1f} ms later, {a2:.2f} vs {a1:.2f} in size")
    p.axes([0, 20, 40, 60, 80, 100], [-1, -0.5, 0, 0.5, 1])
    p.line([(t * 1000, ring(t, 1.0, 0)) for t in ts], GRAY, "One sharp move", width=2, dash="6 4")
    p.line([(t * 1000, ring(t, a1, 0)) for t in ts], BLUE, "First hit", width=2)
    p.line([(t * 1000, ring(t, a2, t2)) for t in ts], ORANGE, "Second hit, half a period later", width=2)
    p.line([(t * 1000, ring(t, a1, 0) + ring(t, a2, t2)) for t in ts], GREEN, "Sum: silent after the second hit", width=3.2)
    p.vline(t2 * 1000, INK, "second hit", label_y=-0.85)
    p.legend("tr")
    save("input-shaping.svg", p.svg())


# Chapter 9: two-node chamber, air vs frame
def chamber_two_node():
    tr, target, pmax = 22.0, 70.0, 500.0
    ca, cw, h, ua, uw = 3000.0, 30000.0, 6.0, 2.0, 2.0
    ta, tw, t, dt = tr, tr, 0.0, 1.0
    air, frame, reached = [], [], None
    while t <= 180 * 60:
        hold = h * (ta - tw) + ua * (ta - tr)
        power = pmax if ta < target else min(pmax, max(0.0, hold))
        ta += dt * (power - h * (ta - tw) - ua * (ta - tr)) / ca
        tw += dt * (h * (ta - tw) - uw * (tw - tr)) / cw
        if reached is None and ta >= target - 0.05:
            reached = t / 60
        if int(t) % 60 == 0:
            air.append((t / 60, ta))
            frame.append((t / 60, tw))
        t += dt
    p = Plot("The air gets there fast. The frame doesn't", "Time since the heater turned on (min)",
             "Temperature (°C)", (0, 180), (20, 80),
             subtitle="Two-node chamber model, made-up but plausible numbers, heater holding the air at 70 °C")
    p.axes([0, 30, 60, 90, 120, 150, 180], [20, 40, 60, 80])
    p.hline(target, GRAY, "target")
    p.line(air, BLUE, "Chamber air")
    p.line(frame, ORANGE, "Frame and panels")
    p.text(reached, target, f"air at target in about {reached:.0f} min", dx=8, dy=24)
    p.text(150, frame[150][1], "frame still climbing after 2.5 h", dx=-10, dy=30, anchor="end")
    p.legend("br")
    save("chamber-two-node.svg", p.svg())


if __name__ == "__main__":
    shear_thinning()
    wlf_shift()
    melt_time()
    pa_step()
    pa_vs_flow()
    bead_contact()
    contact_fraction()
    interface_temp()
    weld_time()
    stoney_layers()
    input_shaping()
    chamber_two_node()
