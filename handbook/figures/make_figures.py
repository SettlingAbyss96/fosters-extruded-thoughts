"""Generate the handbook figures as plain SVG files.

No dependencies beyond the Python standard library, so anyone can rerun it:

    python make_figures.py

Every curve comes from the same toy models and numbers used in the chapters.
"""

import bisect
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
                 w=760, h=430, ml=78, mr=28, mt=60, mb=64, subtitle=None, title_x=None):
        self.title, self.subtitle, self.title_x = title, subtitle, title_x
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

    def area(self, pts, color, opacity=0.85, stroke=None):
        d = " ".join(f"{'M' if i == 0 else 'L'}{self.X(x):.1f},{self.Y(y):.1f}" for i, (x, y) in enumerate(pts))
        st = f' stroke="{stroke}" stroke-width="1.2"' if stroke else ""
        self.items.append(f'<path d="{d} Z" fill="{color}" fill-opacity="{opacity}"{st}/>')

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

    def svg(self, card=True):
        tx = self.title_x if self.title_x is not None else self.ml
        out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}" font-family="{FONT}">']
        if card:
            out.append(f'<rect x="0.5" y="0.5" width="{self.w - 1}" height="{self.h - 1}" rx="10" fill="white" stroke="{GRID}"/>')
            out.append(f'<text x="{tx}" y="28" font-size="16" font-weight="600" fill="{INK}">{esc(self.title)}</text>')
        else:
            out.append(f'<text x="{tx}" y="24" font-size="13.5" font-weight="600" fill="{INK}">{esc(self.title)}</text>')
        if self.subtitle:
            out.append(f'<text x="{tx}" y="47" font-size="12.5" fill="{GRAY}">{esc(self.subtitle)}</text>')
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
        if ch == 70:
            p.text(t_above, tg, f"{t_above:.1f} s above Tg", color=col, dx=6, dy=-10)
        else:
            p.text(t_above, tg, f"{t_above:.1f} s above Tg", color=col, anchor="end", dx=-6, dy=20)
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
             (0, 100), (-1.3, 1.0), subtitle=f"40 Hz resonance, damping 0.07. Second hit {t2 * 1000:.1f} ms later, {a2:.2f} vs {a1:.2f} in size")
    p.axes([0, 20, 40, 60, 80, 100], [-1, -0.5, 0, 0.5, 1])
    p.line([(t * 1000, ring(t, 1.0, 0)) for t in ts], GRAY, "One sharp move", width=2, dash="6 4")
    p.line([(t * 1000, ring(t, a1, 0)) for t in ts], BLUE, "First hit", width=2)
    p.line([(t * 1000, ring(t, a2, t2)) for t in ts], ORANGE, "Second hit, half a period later", width=2)
    p.line([(t * 1000, ring(t, a1, 0) + ring(t, a2, t2)) for t in ts], GREEN, "Sum: silent after the second hit", width=3.2)
    p.vline(t2 * 1000, INK, "second hit", label_y=-0.85)
    p.legend("br")
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
    p.text(150, frame[150][1], "frame still climbing after 2.5 h", dx=-10, dy=44, anchor="end")
    p.legend("br")
    save("chamber-two-node.svg", p.svg())


# Chapters 3 and 4: the melt zone model
# Plug flow through a bore whose wall sits at the setpoint. Same numbers as the chapters:
# ABS, alpha = 0.08 mm²/s, wall 250 °C, filament entering at 50 °C, Seppala's WLF fit.
ALPHA, T_WALL, T_IN, N_POW, R_FIL, A_FIL = 0.08, 250.0, 50.0, 0.4, 0.875, 2.405


def bessel(x, order):
    s, t, k = 0.0, 1.0 if order == 0 else x / 2, 0
    while abs(t) > 1e-17 or k < 5:
        s += t
        k += 1
        t *= -(x * x / 4) / (k * (k + order))
    return s


def _j0_zero(k):
    a, b = (k - 0.25) * math.pi - 0.6, (k - 0.25) * math.pi + 0.6
    fa = bessel(a, 0)
    for _ in range(80):
        m = (a + b) / 2
        if (bessel(m, 0) > 0) == (fa > 0):
            a = m
        else:
            b = m
    return (a + b) / 2


ZEROS = [_j0_zero(k) for k in range(1, 9)]
ZEROS += [(k - 0.25) * math.pi + 1 / (8 * (k - 0.25) * math.pi) for k in range(9, 400)]


def log_aT(T):
    return -4.65 * (T - 230.0) / (200.9 + T - 230.0)


def theta_mean(Fo):
    return sum(4 / l ** 2 * math.exp(-l * l * Fo) for l in ZEROS)


def theta_at(xi, Fo):
    return sum(2 / (l * bessel(l, 1)) * bessel(l * xi, 0) * math.exp(-l * l * Fo) for l in ZEROS[:8])


def pa_ratio(q, drop25):
    beta = drop25 / 25
    return (q / 5) ** (N_POW - 1) * 10 ** (log_aT(T_WALL - beta * q) - log_aT(T_WALL - beta * 5))


def p_rel(q, L):
    t_mean = T_WALL - (T_WALL - T_IN) * theta_mean(math.pi * ALPHA * L / q)
    return (q / 2) ** N_POW * 10 ** (log_aT(t_mean) - log_aT(T_WALL))


def step_temp(t, q1, q2, L=20.0):
    v = L * A_FIL
    t1, t2 = v / q1, v / q2
    age = t1 if t < 0 else (t1 - t * (q2 / q1 - 1) if t < t2 else t2)
    return T_WALL - (T_WALL - T_IN) * theta_mean(ALPHA * age / R_FIL ** 2)


def ooze_parts(t, q=10.0, L=20.0, tau=0.04, beta_v=4e-4):
    fo_l = math.pi * ALPHA * L / q
    elastic = pressure_ooze(t, q, tau)
    thermal = beta_v * (T_WALL - T_IN) * R_FIL ** 2 * q / ALPHA * sum(
        4 / l ** 4 * (1 - math.exp(-l * l * fo_l)) * (1 - math.exp(-l * l * ALPHA * t / R_FIL ** 2)) for l in ZEROS)
    return elastic / A_FIL, thermal / A_FIL


# Chapters 4 and 5: a toy nozzle for stops and seams. A linear spring C (gears, filament, melt)
# charged to whatever pressure the melt needs. The melt is either a plain resistance or chapter 2's
# filament A in a 0.4 nozzle (wall shear rate about 160/s per mm³/s). C is set so the time constant
# is tau_ref at q_ref.
FIL_A = (3000.0, 0.01, 0.35)


class ToyNozzle:
    def __init__(self, shear_thin=True, q_ref=8.14, tau_ref=0.03):
        eta0, lam, n = FIL_A
        if shear_thin:
            self.p = lambda q: q * eta0 / (1 + (lam * 160.0 * q) ** (1 - n))
        else:
            self.p = lambda q: q
        self.c = tau_ref / self.slope(q_ref)
        self.qs = logspace(1e-6, 100, 6000)
        self.ps = [self.p(q) for q in self.qs]

    def slope(self, q, d=1e-4):
        q = max(q, 2 * d)
        return (self.p(q + d) - self.p(q - d)) / (2 * d)

    def tau(self, q):
        return self.c * self.slope(q)

    def stored(self, q):
        return self.c * self.p(q)

    def flow(self, v):
        pr = v / self.c
        if pr <= 0:
            return 0.0
        i = bisect.bisect_left(self.ps, pr)
        if i == 0:
            return self.qs[0] * pr / self.ps[0]
        if i == len(self.ps):
            return self.qs[-1]
        f = (pr - self.ps[i - 1]) / (self.ps[i] - self.ps[i - 1])
        return self.qs[i - 1] + f * (self.qs[i] - self.qs[i - 1])


_DRAIN = {}


def pressure_ooze(t, q, tau):
    """Volume out of the stored pressure after the extruder stops (no PA, no retraction)."""
    if (q, tau) not in _DRAIN:
        noz = ToyNozzle(q_ref=q, tau_ref=tau)
        v, now, out, pts = noz.stored(q), 0.0, 0.0, [(0.0, 0.0)]
        while now < 12:
            dt = 1e-5 if now < 0.01 else (1e-4 if now < 0.1 else 1e-3)
            f = noz.flow(v)
            v, out, now = v - f * dt, out + f * dt, now + dt
            pts.append((now, out))
        _DRAIN[(q, tau)] = pts
    pts = _DRAIN[(q, tau)]
    i = min(max(bisect.bisect_left(pts, (t,)), 1), len(pts) - 1)
    (t0, a), (t1, b) = pts[i - 1], pts[i]
    return a + (b - a) * min(max((t - t0) / (t1 - t0), 0.0), 1.0)


def bead_area(w, h):
    return (w - h) * h + math.pi * h * h / 4


def seam_profile(noz, scarf=True, w=0.45, h=0.2, v=100.0, accel=5000.0, loop=94.2, length=20.0,
                 gap=0.04, pa=None, restart=0.0, follow_flow=False, dt=1e-5, smooth=0.04):
    """Cross-section error along one wall loop, folded so the seam point is x = 0.

    The toolhead starts and stops at rest with constant acceleration. The extruder runs Klipper-style
    PA (rate = q + K dq/dt, triangle-smoothed over `smooth`), or with follow_flow the exact inverse
    of the toy nozzle. `restart` is the stored volume (mm³) the nozzle starts the loop with.
    """
    area = bead_area(w, h)
    k_pa = noz.tau(area * v) if pa is None else pa
    end = loop + length if scarf else loop - gap

    def ratio(x):
        if not scarf:
            return 1.0
        if x < length:
            return x / length
        return 1.0 if x < loop else max(0.0, 1 - (x - loop) / length)

    t_acc, x_acc = v / accel, v * v / (2 * accel)
    t_end = 2 * t_acc + (end - 2 * x_acc) / v
    n = int(t_end / dt) + 1
    xs, qc = [], []
    for i in range(n):
        t = i * dt
        if t < t_acc:
            x, sp = accel * t * t / 2, accel * t
        elif t < t_end - t_acc:
            x, sp = x_acc + v * (t - t_acc), v
        else:
            r = max(t_end - t, 0.0)
            x, sp = end - accel * r * r / 2, accel * r
        xs.append(x)
        qc.append(area * sp * ratio(x))
    base = [noz.stored(q) for q in qc] if follow_flow else [k_pa * q for q in qc]
    raw = [qc[i] + (base[min(i + 1, n - 1)] - base[max(i - 1, 0)]) / (2 * dt) for i in range(n)]
    half = max(1, int(smooth / 4 / dt))
    for _ in range(2):
        acc = [0.0]
        for val in raw:
            acc.append(acc[-1] + val)
        raw = [(acc[min(n, i + half + 1)] - acc[max(0, i - half)]) / (2 * half + 1) for i in range(n)]
    stored, dep, bin_mm = restart, {}, 0.02
    for i in range(n):
        out = noz.flow(stored)
        stored += (raw[i] - out) * dt
        x = xs[i]
        if (scarf and x >= loop) or (not scarf and x > loop / 2):
            x -= loop
        b = math.floor(x / bin_mm)
        dep[b] = dep.get(b, 0.0) + out * dt
    keys = range(min(dep), max(dep) + 1)
    rel = {k: dep.get(k, 0.0) / (area * bin_mm) - 1 for k in keys}
    sig = w / 3 / bin_mm
    reach = int(3 * sig) + 1
    gauss = [math.exp(-0.5 * (d / sig) ** 2) for d in range(-reach, reach + 1)]
    prof = []
    for k in keys:
        s = ws = 0.0
        for d in range(-reach, reach + 1):
            if k + d in rel:
                s += gauss[d + reach] * rel[k + d]
                ws += gauss[d + reach]
        prof.append(((k + 0.5) * bin_mm, s / ws))
    return prof


def tip_drop(h, k, length=4e-3, radius=2e-3, t_block=250.0, t_air=40.0):
    m = math.sqrt(2 * h / (k * radius))
    return (t_block - t_air) * (1 - 1 / math.cosh(m * length))


def old_fraction(v_ratio, n):
    p = (n + 1) / n
    u_max = (3 * n + 1) / (n + 1)
    if 1 / v_ratio >= u_max:
        return 1.0
    xi_c = (1 - (1 / v_ratio) / u_max) ** (1 / p)
    flux = lambda x: x * x / 2 - x ** (p + 2) / (p + 2)
    return (flux(1) - flux(xi_c)) / flux(1)


# Chapter 14: the whole printer as one toy function. ABS on a 0.4 nozzle, put together from the
# chapters' own models: the tip drop (3, 4), plug-flow melting (3), r³-weighted pressure (4), PA as
# C n P / q (4), stored and thermal ooze (4), bead contact (5), landing temperature, cooling and
# weld time (6), built-in stress (7) and ringing (8). Nothing is fitted to a real print.
RHO_C = 2.1e-3                         # J/(mm³ K), ABS. Chapter 3: 25 mm³/s over 200 K is about 10 W
TG_ABS, CTE_ABS, E_ABS, NU_ABS, BETA_ABS = 105.0, 90e-6, 2000.0, 0.35, 4e-4
R_TIP = {"brass": 2.8, "steel": 12.7}  # K/W through the tip, a quarter of the heat goes that way
BASE = dict(v=150.0, h=0.2, w=0.45, t_set=250.0, t_ch=50.0, fan=0.3, area=1.0, L=20.0, nozzle="brass", a=5000.0)


def wall_temp(q, t_set, nozzle):
    t_w = t_set
    for _ in range(30):
        t_w = t_set - 0.25 * RHO_C * q * (t_w - T_IN) * R_TIP[nozzle]
    return t_w


def shift_eff(t_w, fo, n=120):
    """a_T of the melt leaving the zone, weighted by r³ the way the flow resistance is."""
    s = 0.0
    for i in range(n):
        xi = (i + 0.5) / n
        s += xi ** 3 / 10 ** log_aT(t_w - (t_w - T_IN) * theta_at(xi, fo)) / n
    return 1 / (4 * s)


def landing(t_m, t_ch, fan, h, t_layer):
    """Interface at landing (every layer lands on the one before), its cooling time, weld time at 230 °C."""
    tau_c = RHO_C * h * 1e6 / (20 + 280 * fan)
    e = math.exp(-t_layer / tau_c)
    t_i0 = (t_m + t_ch * (1 - e)) / (2 - e)
    teq, t, dt = 0.0, 0.0, 2e-3
    while t < t_layer:
        temp = t_ch + (t_i0 - t_ch) * math.exp(-t / tau_c)
        if temp <= TG_ABS:
            break
        teq += dt / 10 ** log_aT(temp)
        t += dt
    return t_i0, tau_c, teq


class WholePrinter:
    """Knobs in, states and outcomes out. Scaled to 5 MPa, PA 40 ms and a 70% weld at the base point."""

    def __init__(self):
        self.ref = None
        first = self(**BASE)
        self.ref = dict(p=first["p_raw"], q=first["q"], tau_rep=first["teq"] / 0.7 ** 4)
        self.base = self(**BASE)

    def __call__(self, v, h, w, t_set, t_ch, fan, area, L, nozzle, a):
        A = bead_area(w, h)
        q = A * v
        t_w = wall_temp(q, t_set, nozzle)
        fo = math.pi * ALPHA * L / q
        t_m = t_w - (t_w - T_IN) * theta_mean(fo)
        p_raw = q ** N_POW * shift_eff(t_w, fo)
        t_layer = 10.0 * area * BASE["w"] * BASE["v"] / (w * v)
        t_i0, tau_c, teq = landing(t_m, t_ch, fan, h, t_layer)
        o = dict(A=A, q=q, v=v, a=a, t_w=t_w, t_m=t_m, fo=fo, p_raw=p_raw, t_layer=t_layer, t_i0=t_i0,
                 tau_c=tau_c, teq=teq)
        if self.ref is None:
            return o
        r = self.ref
        o["p"] = 5.0 * p_raw / r["p"]
        o["tau"] = 0.04 * (p_raw / q) / (r["p"] / r["q"])
        fo_l = math.pi * ALPHA * L / q
        o["ooze_th"] = BETA_ABS * (t_w - T_IN) * R_FIL ** 2 * q / ALPHA * sum(
            4 / l ** 4 * (1 - math.exp(-l * l * fo_l)) for l in ZEROS)
        o["left"] = o["tau"] * q * (1 / N_POW - 1)
        o["stop_bead"] = (o["left"] + o["ooze_th"]) / A
        o["margin"] = fo / 0.3
        o["phi"] = 1 - h / w
        o["H"] = teq / r["tau_rep"]
        o["z"] = o["phi"] * min(1.0, o["H"] ** 0.25)
        o["stress"] = E_ABS * CTE_ABS * (TG_ABS - t_ch) / (1 - NU_ABS)
        o["ring"] = a / (2 * math.pi * 50) ** 2
        o["corner"] = 100 * (o["tau"] - 0.04) * a / v
        return o


KNOB_STEPS = [("Speed", "+20%", dict(v=180.0)), ("Layer", "0.20 → 0.24", dict(h=0.24)),
              ("Line width", "+20%", dict(w=0.54)), ("Nozzle", "+10 K", dict(t_set=260.0)),
              ("Chamber", "+10 K", dict(t_ch=60.0)), ("Part fan", "+20 points", dict(fan=0.5)),
              ("Part area", "+20%", dict(area=1.2)), ("Melt zone", "+20%", dict(L=24.0)),
              ("Nozzle", "brass → steel", dict(nozzle="steel")), ("Accel", "+20%", dict(a=6000.0))]

# name, unit, how to compare with the base point, which way is good for the part (0 = neither), what counts as a big change
OUTCOMES = [("Melt temperature", "K", lambda o, b: o["t_m"] - b["t_m"], 0, 5),
            ("Max flow margin", "%", lambda o, b: 100 * (o["margin"] / b["margin"] - 1), 1, 10),
            ("Nozzle pressure", "%", lambda o, b: 100 * (o["p"] / b["p"] - 1), -1, 20),
            ("PA needed", "%", lambda o, b: 100 * (o["tau"] / b["tau"] - 1), 0, 10),
            ("Corner error, old PA", "pts", lambda o, b: o["corner"] - b["corner"], -2, 5),
            ("Stop volume per bead", "%", lambda o, b: 100 * (o["stop_bead"] / b["stop_bead"] - 1), -1, 10),
            ("Interface temperature", "K", lambda o, b: o["t_i0"] - b["t_i0"], 1, 5),
            ("Weld time", "%", lambda o, b: 100 * (o["H"] / b["H"] - 1), 1, 50),
            ("Bonded fraction", "%", lambda o, b: 100 * (o["phi"] / b["phi"] - 1), 1, 5),
            ("Z strength", "%", lambda o, b: 100 * (o["z"] / b["z"] - 1), 1, 5),
            ("Built-in stress", "%", lambda o, b: 100 * (o["stress"] / b["stress"] - 1), -1, 10),
            ("Ringing", "%", lambda o, b: 100 * (o["ring"] / b["ring"] - 1), -1, 10),
            ("Throughput", "%", lambda o, b: 100 * (o["q"] / b["q"] - 1), 1, 10)]


def sensitivity_table():
    wp = WholePrinter()
    table = []
    for name, step, kw in KNOB_STEPS:
        o = wp(**dict(BASE, **kw))
        table.append([f(o, wp.base) for _, _, f, _, _ in OUTCOMES])
    return wp, table


def print_stretch(dt=0.05):
    """Infill, travel, outer wall, travel, inner wall. Melt age from the extruder history (chapter 4)."""
    phases = [(-4.0, 0.0, 10.0, "inner wall"), (0.0, 8.0, 20.0, "infill"), (8.0, 8.6, 0.0, "travel"),
              (8.6, 18.0, 5.0, "outer wall"), (18.0, 18.4, 0.0, "travel"), (18.4, 26.0, 10.0, "inner wall")]

    def flow(t):
        for a, b, q, _ in phases:
            if a <= t < b:
                return q
        return 10.0

    v_z = A_FIL * 20.0
    wp = WholePrinter()
    ref_fo = math.pi * ALPHA * 20.0 / wp.base["q"]
    ref_a = shift_eff(wall_temp(wp.base["q"], 250.0, "brass"), ref_fo, 48)

    def tau_needed(q, age):
        t_w = wall_temp(q, 250.0, "brass")
        return 0.04 * (q / wp.base["q"]) ** (N_POW - 1) * shift_eff(t_w, ALPHA * age / R_FIL ** 2, 48) / ref_a

    k_wall = tau_needed(5.0, v_z / 5.0)
    b = wp.base
    e = math.exp(-b["t_layer"] / b["tau_c"])
    t_old = BASE["t_ch"] + (b["t_i0"] - BASE["t_ch"]) * e

    def weld(t_m):
        return landing_from(t_m, t_old, b["tau_c"], b["t_layer"])

    wall_weld = weld(wall_temp(5.0, 250.0, "brass") - (wall_temp(5.0, 250.0, "brass") - T_IN) * theta_mean(ALPHA * v_z / 5.0 / R_FIL ** 2))
    cum, out, t = 0.0, [], -4.0
    hist = []
    while t <= 26.0 + 1e-9:
        q = flow(t)
        hist.append((t, cum))
        target = cum - v_z
        if target <= hist[0][1]:
            age = t - (hist[0][0] + (target - hist[0][1]) / 10.0)
        else:
            i = len(hist) - 1
            while hist[i][1] > target:
                i -= 1
            (t0, c0), (t1, c1) = hist[i], hist[min(i + 1, len(hist) - 1)]
            age = t - (t0 + (t1 - t0) * (target - c0) / (c1 - c0) if c1 > c0 else t0)
        t_w = wall_temp(q, 250.0, "brass")
        t_m = t_w - (t_w - T_IN) * theta_mean(ALPHA * age / R_FIL ** 2)
        pa = tau_needed(q, age) / k_wall if q > 0 else None
        strength = (weld(t_m) / wall_weld) ** 0.25 if q > 0 else None
        out.append((t, q, age, t_m, pa, strength))
        cum += q * dt
        t += dt
    return phases, out, k_wall


def landing_from(t_m, t_old, tau_c, t_layer):
    t_i0 = (t_m + t_old) / 2
    teq, t, dt = 0.0, 0.0, 2e-3
    while t < t_layer:
        temp = BASE["t_ch"] + (t_i0 - BASE["t_ch"]) * math.exp(-t / tau_c)
        if temp <= TG_ABS:
            break
        teq += dt / 10 ** log_aT(temp)
        t += dt
    return teq


def melt_profile():
    p = Plot("What actually reaches the nozzle", "Position across the bore (0 = center, 1 = wall)",
             "Temperature (°C)", (0, 1), (80, 260),
             subtitle="ABS, wall at 250 °C, filament in at 50 °C. Same Fo, same profile: only L/Q matters")
    p.axes([0, 0.2, 0.4, 0.6, 0.8, 1], [80, 120, 160, 200, 240])
    p.hline(105, GRAY)
    p.text(0.4, 105, "glass transition, 105 °C", color=GRAY, dy=16)
    xs = linspace(0, 1, 120)
    for fo, col, lab in [(1.0, GREEN, "Fo = 1.0  (20 mm at 5 mm³/s)"), (0.5, BLUE, "Fo = 0.5  (20 mm at 10 mm³/s)"),
                         (0.25, ORANGE, "Fo = 0.25 (10 mm at 10 mm³/s)"), (0.13, RED, "Fo = 0.13 (10 mm at 20 mm³/s)")]:
        p.line([(x, T_WALL - (T_WALL - T_IN) * theta_at(x, fo)) for x in xs], col, lab)
    p.legend("br")
    save("melt-profile.svg", p.svg())


def tip_fin():
    p = Plot("Steel's penalty lives at the tip", "Cooling on the tip, h (W/m²K, log scale)",
             "Tip colder than the block (K)", (10, 1000), (0, 60), xlog=True,
             subtitle="4 mm of nozzle below a 250 °C block, 2 mm radius, air at 40 °C. Fin model, before any melt flows")
    p.band_x(15, 40, GRAY)
    p.band_x(150, 600, GRAY)
    p.axes([10, 30, 100, 300, 1000], [0, 10, 20, 30, 40, 50, 60], ["10", "30", "100", "300", "1,000"])
    p.text(24.5, 30, "silicone sock", color=GRAY, anchor="middle")
    p.text(300, 30, "part fan", color=GRAY, anchor="middle")
    hs = logspace(10, 1000)
    for name, k, col in [("Hardened steel", 25, RED), ("Tungsten carbide", 90, PURPLE),
                         ("Brass", 115, BLUE), ("Copper", 350, ORANGE)]:
        p.line([(h, tip_drop(h, k)) for h in hs], col, name)
    p.legend("tl")
    save("tip-fin.svg", p.svg())


def washout():
    p = Plot("The old color tails off slowly", "Volume pushed through, in melt zone volumes",
             "Old plastic in what comes out (%, log scale)", (0, 8), (0.1, 100), ylog=True,
             subtitle="Plastic at the wall barely moves, so the last of the old color takes a while to leave")
    p.axes([0, 1, 2, 3, 4, 5, 6, 7, 8], [0.1, 1, 10, 100], ylabels=["0.1", "1", "10", "100"])
    p.hline(2, ORANGE, "2%")
    p.vline(3.2, ORANGE, "about 3.2 zone volumes", label_y=20)
    vs = linspace(0.3, 8, 400)
    p.line([(v, 100 * old_fraction(v, 1.0)) for v in vs], GRAY, "Newtonian", dash="6 4")
    p.line([(v, 100 * old_fraction(v, 0.4)) for v in vs], BLUE, "Shear-thinning melt, n = 0.4")
    p.legend("tr")
    save("washout.svg", p.svg())


def pa_flip():
    p = Plot("Same filament, opposite trends", "Flow (mm³/s)", "PA needed, relative to 5 mm³/s", (5, 30), (0, 2),
             subtitle="ABS at a 250 °C setpoint: shear thinning lowers PA, a cooler melt raises it")
    p.axes([5, 10, 15, 20, 25, 30], [0, 0.5, 1, 1.5, 2], ylabels=["0", "0.5×", "1×", "1.5×", "2×"])
    p.hline(1, GRAY, "tuned at 5 mm³/s")
    qs = linspace(5, 30)
    for drop, col, lab in [(0, GRAY, "Melt stays at the setpoint"), (10, BLUE, "Good brass setup (10 K cooler at 25)"),
                           (30, RED, "Steel under a hard fan (30 K cooler at 25)")]:
        p.line([(q, pa_ratio(q, drop)) for q in qs], col, lab)
        v = pa_ratio(25, drop)
        p.point(25, v, col)
        if drop == 30:
            p.text(25, v, f"{v:.2f}×", color=col, anchor="end", dx=-8, dy=-8)
        else:
            p.text(25, v, f"{v:.2f}×", color=col, dx=8, dy=16 if drop == 0 else -8)
    p.legend("tl")
    save("pa-flip.svg", p.svg())


def pressure_wall():
    p = Plot("The max flow wall, from the model", "Flow (mm³/s, log scale)",
             "Pressure, relative (log scale)", (2, 40), (1, 1000), xlog=True, ylog=True,
             subtitle="ABS, wall at 250 °C, relative to fully melted flow at 2 mm³/s. Curves stop where the core goes solid")
    p.axes([2, 5, 10, 20, 40], [1, 10, 100, 1000], ylabels=["1", "10", "100", "1,000"])
    qs = logspace(2, 40)
    p.line([(q, (q / 2) ** N_POW) for q in qs], GRAY, "Fully melted (goes as flow^0.4)", dash="6 4")
    for L, col in [(30, GREEN), (20, ORANGE), (10, RED)]:
        p.line([(q, p_rel(q, L)) for q in qs if math.pi * ALPHA * L / q >= 0.12], col, f"{L} mm melt zone")
    p.text(14, p_rel(14, 10), "slope 3 to 5 near the wall", color=RED, anchor="end", dx=-10, dy=-4)
    p.legend("tl")
    save("pressure-wall.svg", p.svg())


def melt_age_step():
    p = Plot("Speeding up hits fast, slowing down recovers slowly", "Time after the speed change (s)",
             "Melt temperature leaving the zone (°C)", (-1, 12), (210, 255),
             subtitle="20 mm melt zone, ABS. The exit temperature only depends on how long the plastic was in the zone")
    p.axes([0, 2, 4, 6, 8, 10, 12], [210, 220, 230, 240, 250])
    p.vline(0, GRAY, "speed changes")
    ts = linspace(-1, 12, 700)
    p.line([(t, step_temp(t, 5, 20)) for t in ts], RED)
    p.line([(t, step_temp(t, 20, 5)) for t in ts], BLUE)
    p.text(3, 217.6, "5 → 20 mm³/s: cools within 2.4 s", color=RED, dy=-8)
    p.text(6, step_temp(6, 20, 5), "20 → 5 mm³/s: takes 9.6 s to recover", color=BLUE, dy=24)
    save("melt-age-step.svg", p.svg())


def ooze_time():
    p = Plot("Ooze runs on two clocks", "Time after the extruder stops (s, log scale)",
             "Ooze (mm of filament)", (0.01, 10), (0, 0.8), xlog=True,
             subtitle="ABS at 10 mm³/s into a 20 mm melt zone. Pressure is mostly out in half a second, heat keeps pushing for seconds")
    p.axes([0.01, 0.1, 1, 10], [0, 0.2, 0.4, 0.6, 0.8], ["0.01", "0.1", "1", "10"])
    ts = logspace(0.01, 10)
    parts = [(t, *ooze_parts(t)) for t in ts]
    p.line([(t, e) for t, e, _ in parts], BLUE, "Pressure (elastic)")
    p.line([(t, h) for t, _, h in parts], ORANGE, "Heat (thermal expansion)")
    p.line([(t, e + h) for t, e, h in parts], GREEN, "Total", width=3.2)
    p.legend("tl")
    save("ooze-time.svg", p.svg())


# Chapter 5: the scarf joint, unrolled
def scarf_joint():
    p = Plot("A scarf seam, unrolled", "Along the loop (mm)", "Height (layers)", (-5, 25), (0, 2.6),
             subtitle="Orca, start height 0, 20 mm scarf. Height stretched about 27×")
    p.axes([-5, 0, 5, 10, 15, 20, 25], [0, 1, 2])
    p.area([(-5, 0), (25, 0), (25, 1), (-5, 1)], GRID, opacity=1, stroke=GRAY)
    p.area([(-5, 1), (0, 1), (20, 2), (25, 2), (25, 1)], "#bfdbfe", opacity=1, stroke=BLUE)
    p.area([(-5, 1), (0, 1), (0, 2), (-5, 2)], "#bfdbfe", opacity=1, stroke=BLUE)
    p.area([(0, 1), (20, 2), (0, 2)], "#fed7aa", opacity=1, stroke=ORANGE)
    p.text(10, 0.5, "layer below", color=GRAY, anchor="middle", dy=4)
    p.text(13.5, 1.1, "ramp: height and flow climb 0 → 1", color=BLUE, anchor="middle")
    p.text(6.5, 1.78, "end pass: full height, flow fades 1 → 0", color=ORANGE, anchor="middle")
    p.text(-2.5, 1.5, "loop end", color=BLUE, anchor="middle", dy=4)
    p.text(22.5, 1.5, "rest of loop", color=BLUE, anchor="middle", dy=4)
    p.vline(0, INK, "seam point", label_y=2.35)
    p.vline(20, INK, "L = 20 mm", label_y=2.35, anchor="end")
    save("scarf-joint.svg", p.svg())


SEAM_LIN = None
SEAM_CROSS = None


def _seam_nozzles():
    global SEAM_LIN, SEAM_CROSS
    if SEAM_LIN is None:
        SEAM_LIN, SEAM_CROSS = ToyNozzle(shear_thin=False), ToyNozzle()
    return SEAM_LIN, SEAM_CROSS


def scarf_lag():
    lin, _ = _seam_nozzles()
    p = Plot("The scarf cancels its own lag", "Along the loop, from the seam point (mm)",
             "Plastic laid vs planned (%)", (-5, 25), (-70, 70),
             subtitle="Linear toy nozzle, τ = 30 ms, PA set to half of that. 0.45 × 0.2 mm line at 100 mm/s")
    p.band_x(0, 20, ORANGE, "scarf", opacity=0.08)
    p.axes([-5, 0, 5, 10, 15, 20, 25], [-60, -30, 0, 30, 60])
    p.hline(0, GRAY, dash="2 3")
    butt = seam_profile(lin, scarf=False, pa=0.015)
    scarf = seam_profile(lin, scarf=True, pa=0.015)
    p.line([(x, 100 * e) for x, e in butt if -5 <= x <= 25], BLUE, "Butt seam")
    p.line([(x, 100 * e) for x, e in scarf if -5 <= x <= 25], ORANGE, "Scarf seam")
    p.legend("br")
    save("scarf-lag.svg", p.svg())


def scarf_restart():
    _, noz = _seam_nozzles()
    area = bead_area(0.45, 0.2)
    q = area * 100
    restart = noz.stored(q) - noz.tau(q) * q
    p = Plot("A scarf wants a different restart", "Along the loop, from the seam point (mm)",
             "Plastic laid vs planned (%)", (-5, 25), (-40, 120),
             subtitle="Shear-thinning toy nozzle (chapter 2's filament A), PA tuned at the wall flow. 0.45 × 0.2 mm at 100 mm/s")
    p.band_x(0, 20, ORANGE, "scarf", opacity=0.08)
    p.axes([-5, 0, 5, 10, 15, 20, 25], [-40, 0, 40, 80, 120])
    p.hline(0, GRAY, dash="2 3")
    cases = [(seam_profile(noz, scarf=False, restart=restart), GRAY, "Butt seam, normal restart", "6 4"),
             (seam_profile(noz, restart=restart), RED, "Scarf, same restart", None),
             (seam_profile(noz, restart=restart / 2), ORANGE, "Scarf, half the restart", None),
             (seam_profile(noz, follow_flow=True), GREEN, "Scarf, PA follows flow, no restart", None)]
    for prof, col, lab, dash in cases:
        p.line([(x, 100 * e) for x, e in prof if -5 <= x <= 25], col, lab, dash=dash)
    p.legend("tr")
    save("scarf-restart.svg", p.svg())


# Chapter 14: the coupling map. Columns run from what I set to what I care about
MAP_X = [20, 192, 364, 536, 708, 880, 1052]
MAP_W, MAP_BH = 150, 34
MAP_NODES = {
    "speed": (0, 92, "Speed"), "layer": (0, 150, "Layer height"), "width": (0, 208, "Line width"),
    "noz_t": (0, 266, "Nozzle temperature"), "path": (0, 324, "Nozzle and paste"),
    "zone": (0, 382, "Melt zone length"), "chamber": (0, 440, "Chamber"), "fan": (0, 498, "Part fan"),
    "pa": (0, 556, "PA setting"), "restart": (0, 614, "Restart and seam"), "accel": (0, 672, "Acceleration"),
    "flow": (1, 110, "Flow"), "hw": (1, 214, "h/w ratio"), "tlayer": (1, 318, "Layer time"),
    "shake": (1, 672, "Toolhead shake"),
    "tmelt": (2, 282, "Melt temperature"), "strain": (2, 470, "Thermal strain"),
    "visc": (3, 212, "Viscosity"), "tint": (3, 388, "Interface temperature"),
    "press": (4, 180, "Pressure"), "weld": (4, 400, "Weld (healing)"),
    "tau": (5, 150, "PA needed"), "stored": (5, 252, "Stored volume"),
    "time": (6, 92, "Print time"), "margin": (6, 172, "Max flow margin"), "seam": (6, 262, "Corner and seam error"),
    "dims": (6, 352, "Dimensions"), "zstr": (6, 442, "Z strength"), "warp": (6, 532, "Warp and stress"),
    "surface": (6, 672, "Surface"),
}
# source, target, +1 raises it, -1 lowers it, 0 has to match it; a fourth True means my theory or weak evidence
MAP_EDGES = [
    ("speed", "flow", 1), ("layer", "flow", 1), ("width", "flow", 1),
    ("layer", "hw", 1), ("width", "hw", -1), ("speed", "hw", 1, True),
    ("speed", "tlayer", -1), ("width", "tlayer", -1), ("accel", "shake", 1), ("accel", "time", -1),
    ("flow", "tmelt", -1), ("noz_t", "tmelt", 1), ("path", "tmelt", 1), ("zone", "tmelt", 1),
    ("chamber", "strain", -1), ("chamber", "tint", 1), ("fan", "tint", -1), ("tlayer", "tint", -1),
    ("layer", "tint", 1),
    ("flow", "visc", -1), ("tmelt", "visc", -1), ("tmelt", "tint", 1),
    ("visc", "press", 1), ("flow", "press", 1), ("tint", "weld", 1),
    ("press", "tau", 1), ("flow", "tau", -1), ("press", "stored", 1),
    ("flow", "time", -1), ("flow", "margin", -1), ("zone", "margin", 1), ("press", "margin", -1),
    ("tau", "seam", 1), ("pa", "seam", 0), ("stored", "seam", 1), ("restart", "seam", 0),
    ("tmelt", "seam", 1, True),
    ("hw", "zstr", -1), ("weld", "zstr", 1), ("strain", "zstr", -1, True), ("strain", "warp", 1),
    ("shake", "surface", 1), ("shake", "dims", 1, True), ("seam", "dims", 1),
]


def coupling_map():
    W, H = 1222, 770
    colors = {1: BLUE, -1: RED, 0: GRAY}
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">',
           f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="10" fill="white" stroke="{GRID}"/>',
           '<defs>']
    for sign, col in colors.items():
        out.append(f'<marker id="arrow{sign + 1}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
                   f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 Z" fill="{col}"/></marker>')
    out.append('</defs>')
    out.append(f'<text x="20" y="30" font-size="16" font-weight="600" fill="{INK}">Everything pulls on everything: the coupling map</text>')
    out.append(f'<text x="20" y="50" font-size="12.5" fill="{GRAY}">Blue raises what it points at, red lowers it, gray has to match it. Dashed is my theory or thin evidence</text>')
    heads = [(MAP_X[0] + MAP_W / 2, "What I set"), ((MAP_X[1] + MAP_X[5] + MAP_W) / 2, "What happens inside the machine and the part"),
             (MAP_X[6] + MAP_W / 2, "What I care about")]
    for x, s in heads:
        out.append(f'<text x="{x:.0f}" y="76" font-size="13.5" font-weight="600" text-anchor="middle" fill="{INK}">{esc(s)}</text>')
    for e in MAP_EDGES:
        src, dst, sign = e[0], e[1], e[2]
        dashed = len(e) > 3 and e[3]
        (c1, y1, _), (c2, y2, _) = MAP_NODES[src], MAP_NODES[dst]
        y1, y2 = y1 + MAP_BH / 2, y2 + MAP_BH / 2
        if c1 == c2:
            x = MAP_X[c1] + MAP_W
            d = f"M{x},{y1} C{x + 34},{y1} {x + 34},{y2} {x + 2},{y2}"
        else:
            x1, x2 = MAP_X[c1] + MAP_W, MAP_X[c2] - 2
            k = (x2 - x1) * 0.45
            d = f"M{x1},{y1} C{x1 + k},{y1} {x2 - k},{y2} {x2},{y2}"
        da = ' stroke-dasharray="5 4"' if dashed else ""
        out.append(f'<path d="{d}" fill="none" stroke="{colors[sign]}" stroke-width="1.7" opacity="0.62"{da} '
                   f'marker-end="url(#arrow{sign + 1})"/>')
    for key, (c, y, label) in MAP_NODES.items():
        edge = INK if c == 0 else (GREEN if c == 6 else PURPLE)
        out.append(f'<rect x="{MAP_X[c]}" y="{y}" width="{MAP_W}" height="{MAP_BH}" rx="7" fill="white" stroke="{edge}" stroke-width="1.4"/>')
        out.append(f'<text x="{MAP_X[c] + MAP_W / 2}" y="{y + 22}" font-size="12.5" text-anchor="middle" fill="{INK}">{esc(label)}</text>')
    ly = H - 26
    for i, (sign, lab) in enumerate([(1, "raises"), (-1, "lowers"), (0, "has to match")]):
        x = 20 + i * 150
        out.append(f'<line x1="{x}" y1="{ly - 4}" x2="{x + 34}" y2="{ly - 4}" stroke="{colors[sign]}" stroke-width="2.2" marker-end="url(#arrow{sign + 1})"/>')
        out.append(f'<text x="{x + 44}" y="{ly}" font-size="12.5" fill="{INK}">{lab}</text>')
    out.append(f'<line x1="470" y1="{ly - 4}" x2="504" y2="{ly - 4}" stroke="{GRAY}" stroke-width="2.2" stroke-dasharray="5 4"/>')
    out.append(f'<text x="514" y="{ly}" font-size="12.5" fill="{INK}">my theory or thin evidence</text>')
    out.append("</svg>")
    save("coupling-map.svg", "\n".join(out) + "\n")


# Chapter 14: every time scale in the handbook on one axis
def timescales():
    rows = [("Step pulses", 5e-6, 1e-4, GRAY, "8"),
            ("Melt relaxation time", 1e-3, 0.3, BLUE, "2"),
            ("Melt crossing the nozzle", 3e-3, 3e-2, BLUE, "2"),
            ("Ringing period, 36 to 75 Hz", 0.013, 0.028, GRAY, "8"),
            ("Input shaper", 0.02, 0.03, GRAY, "8"),
            ("PA time constant", 0.01, 0.06, BLUE, "4"),
            ("Pressure tail after a stop", 0.05, 1.0, BLUE, "4"),
            ("Scarf ramp", 0.1, 0.4, BLUE, "5"),
            ("Sintering and useful weld time", 0.1, 2.0, ORANGE, "6"),
            ("Thermal ooze", 0.13, 5.0, BLUE, "4"),
            ("MPC reach time", 1.5, 3.0, PURPLE, "9"),
            ("Melt age, one transit", 2.0, 10.0, BLUE, "3, 4"),
            ("Bead cooling under the fan", 2.0, 30.0, ORANGE, "6"),
            ("Layer time", 3.0, 60.0, ORANGE, "6"),
            ("Chamber air", 300.0, 900.0, PURPLE, "9"),
            ("Stress relaxation, annealing", 600.0, 3e4, GREEN, "7"),
            ("Frame and Z drift", 1800.0, 2e4, PURPLE, "9"),
            ("Moisture pickup", 1e4, 1e6, GREEN, "2, 11"),
            ("Nozzle wear", 1e6, 3e7, GREEN, "10")]
    n = len(rows)
    p = Plot("Every clock in the handbook", "Time (log scale)", "", (3e-6, 3e8), (0, n), xlog=True,
             w=900, h=110 + 24 * n, ml=230, mr=24, mt=64, mb=52, title_x=20,
             subtitle="Bars span the usual range. The shaded band is where most of the trouble lives")
    p.band_x(0.01, 10, RED, "the crowded decades", opacity=0.07)
    ticks = [1e-5, 1e-3, 0.1, 10, 1e3, 1e5, 1e7]
    p.axes(ticks, [], ["10 µs", "1 ms", "0.1 s", "10 s", "17 min", "1 day", "4 months"])
    for i, (label, a, b, col, ch) in enumerate(rows):
        yc = n - i - 0.5
        x0, x1 = p.X(a), p.X(b)
        y0 = p.Y(yc) - 7
        p.items.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{max(x1 - x0, 3):.1f}" height="14" rx="4" fill="{col}" opacity="0.8"/>')
        p.items.append(f'<text x="{p.ml - 8}" y="{p.Y(yc) + 4:.1f}" font-size="12.5" text-anchor="end" fill="{INK}">{esc(label)}</text>')
        p.items.append(f'<text x="{max(x1 - x0, 3) + x0 + 6:.1f}" y="{p.Y(yc) + 4:.1f}" font-size="11.5" fill="{GRAY}">ch. {ch}</text>')
    save("timescales.svg", p.svg())


# Chapter 14: the sensitivity matrix, one knob step at a time around the base point
def sensitivity():
    wp, table = sensitivity_table()
    nk, no = len(KNOB_STEPS), len(OUTCOMES)
    cw, ch, left, top = 80, 30, 250, 104
    W, H = left + nk * cw + 24, top + no * ch + 64
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">',
           f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="10" fill="white" stroke="{GRID}"/>',
           f'<text x="20" y="30" font-size="16" font-weight="600" fill="{INK}">One knob at a time: what moves, and how much</text>',
           f'<text x="20" y="50" font-size="12.5" fill="{GRAY}">Toy model, ABS, 0.45 × 0.2 mm at 150 mm/s, 250 °C, 50 °C chamber, 20 mm melt zone. Green is better for the part, red is worse, blue is neither</text>']
    for j, (name, step, _) in enumerate(KNOB_STEPS):
        cx = left + j * cw + cw / 2
        out.append(f'<text x="{cx}" y="{top - 26}" font-size="12.5" font-weight="600" text-anchor="middle" fill="{INK}">{esc(name)}</text>')
        out.append(f'<text x="{cx}" y="{top - 10}" font-size="11.5" text-anchor="middle" fill="{GRAY}">{esc(step)}</text>')
    minus = chr(0x2212)
    for i, (name, unit, _, good, scale) in enumerate(OUTCOMES):
        y = top + i * ch
        if i % 2 == 0:
            out.append(f'<rect x="12" y="{y}" width="{W - 24}" height="{ch}" fill="#f9fafb"/>')
        out.append(f'<text x="{left - 10}" y="{y + 19}" font-size="12.5" text-anchor="end" fill="{INK}">{esc(name)}</text>')
        for j in range(nk):
            v = table[j][i]
            x = left + j * cw
            if abs(v) < (0.05 if unit == "K" else 0.5):
                out.append(f'<text x="{x + cw / 2}" y="{y + 19}" font-size="12" text-anchor="middle" fill="{GRID}">·</text>')
                continue
            if good == 0:
                col = BLUE
            elif good == -2:
                col = RED
            else:
                col = GREEN if v * good > 0 else RED
            alpha = 0.12 + 0.6 * min(1.0, abs(v) / (2 * scale))
            out.append(f'<rect x="{x + 3}" y="{y + 3}" width="{cw - 6}" height="{ch - 6}" rx="4" fill="{col}" opacity="{alpha:.2f}"/>')
            num = f"{abs(v):.1f}" if unit == "K" else f"{abs(v):.0f}"
            sign = "+" if v > 0 else minus
            suffix = " K" if unit == "K" else ("" if unit == "pts" else "%")
            out.append(f'<text x="{x + cw / 2}" y="{y + 19}" font-size="12" text-anchor="middle" fill="{INK}">{sign}{num}{suffix}</text>')
    out.append(f'<text x="20" y="{H - 22}" font-size="12" fill="{GRAY}">Corner error is in percentage points of flow during acceleration, with PA left where it was tuned. '
               f'Weld time and Z strength use the 1/4 power from chapter 6</text>')
    out.append("</svg>")
    save("sensitivity.svg", "\n".join(out) + "\n")


# Chapter 14: the same stretch of print, every chapter at once
def print_stretch_fig():
    phases, out, k_wall = print_stretch()
    ts = [r[0] for r in out]
    shade = {"infill": ORANGE, "outer wall": BLUE, "inner wall": GREEN, "travel": GRAY}
    panels = []

    def panel(title, ylabel, ylim, yticks, last=False):
        p = Plot(title, "Time (s)" if last else "", ylabel, (-4, 26), ylim, w=900, h=200 if not last else 228,
                 ml=86, mr=24, mt=40, mb=56 if last else 30)
        for a, b, _, name in phases:
            p.band_x(max(a, -4), min(b, 26), shade[name], name if not panels and name != "travel" else None, opacity=0.08)
        p.axes([-4, 0, 4, 8, 12, 16, 20, 24], yticks, None if last else [""] * 8)
        panels.append(p)
        return p

    p = panel("Flow the slicer asks for", "mm³/s", (0, 24), [0, 5, 10, 15, 20])
    p.line([(t, q) for t, q, *_ in out], INK, width=2.2)
    p = panel("Melt temperature leaving the nozzle", "°C", (205, 255), [210, 230, 250])
    p.line([(t, tm) for t, _, _, tm, _, _ in out], RED)
    p = panel("PA needed, relative to PA tuned on the outer wall", "×", (0.5, 2.0), [0.5, 1, 1.5, 2])
    p.hline(1, GRAY, dash="2 3")
    for seg in _segments([(t, pa) for t, _, _, _, pa, _ in out]):
        p.line(seg, PURPLE)
    p = panel("Weld strength, relative to a settled outer wall", "×", (0.4, 1.1), [0.4, 0.6, 0.8, 1.0], last=True)
    p.hline(1, GRAY, dash="2 3")
    for seg in _segments([(t, s) for t, _, _, _, _, s in out]):
        p.line(seg, ORANGE)
    W = 900
    H = 70 + sum(pp.h for pp in panels)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">',
             f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="10" fill="white" stroke="{GRID}"/>',
             f'<text x="20" y="30" font-size="16" font-weight="600" fill="{INK}">Eight seconds of infill, then an outer wall</text>',
             f'<text x="20" y="50" font-size="12.5" fill="{GRAY}">Toy model, ABS at 250 °C, 20 mm melt zone. The wall inherits the infill for about ten seconds</text>']
    y = 62
    for pp in panels:
        inner = pp.svg(card=False).split("\n", 1)[1].rsplit("</svg>", 1)[0]
        parts.append(f'<svg x="0" y="{y}" width="{pp.w}" height="{pp.h}" viewBox="0 0 {pp.w} {pp.h}">{inner}</svg>')
        y += pp.h
    parts.append("</svg>")
    save("print-stretch.svg", "\n".join(parts) + "\n")


# Chapter 14: one real print, counted. A four-plate PETG toolbox (202 g, 5 h 48 min) sliced for a
# Bambu P2S in Bambu Studio, the G-code counted line by line. Steps are what my Voron's motors would
# take for the same moves (320 microsteps per mm on A and B, four Z motors, Galileo 2 extruder).
TOOLBOX_HOURS = 20882 / 3600
TOOLBOX = [("Motor microsteps", 1338132223), ("G-code moves", 318033), ("Corners over 10°", 148964),
           ("Heater control updates", 139213), ("Extrusion starts and stops", 39606), ("Retractions", 7375),
           ("Wall loops started (seams)", 5923), ("Fan speed changes", 1572), ("Layers", 582)]
TOOLBOX_TRANSIENTS = 196527            # starts, stops, corners, retractions and layer changes
OBICO_HAZARD = 1067608 / 89.8e6        # failures caught per hour of monitored printing


def print_numbers():
    rows = [("Polymer chains crossing the welds", 9e16, "about 10¹⁷ (rough)", PURPLE)] + \
           [(n, v, f"{v:,}", BLUE) for n, v in TOOLBOX]
    n = len(rows)
    p = Plot("One toolbox, counted", "How many times it happens (log scale)", "", (1, 1e18), (0, n), xlog=True,
             w=900, h=110 + 30 * n, ml=230, mr=24, mt=64, mb=52, title_x=20,
             subtitle="Four plates of PETG on a Bambu P2S, 202 g, 5 h 48 min. Steps as my Voron's motors would take them")
    ticks = [1, 1e3, 1e6, 1e9, 1e12, 1e15, 1e18]
    p.axes(ticks, [], ["1", "thousand", "million", "billion", "10¹²", "10¹⁵", "10¹⁸"])
    for i, (label, v, txt, col) in enumerate(rows):
        yc = n - i - 0.5
        x0, x1 = p.X(1), p.X(v)
        p.items.append(f'<rect x="{x0:.1f}" y="{p.Y(yc) - 9:.1f}" width="{x1 - x0:.1f}" height="18" rx="4" fill="{col}" opacity="0.8"/>')
        p.items.append(f'<text x="{p.ml - 8}" y="{p.Y(yc) + 4:.1f}" font-size="12.5" text-anchor="end" fill="{INK}">{esc(label)}</text>')
        inside = x1 > p.w - 160
        p.items.append(f'<text x="{x1 - 8 if inside else x1 + 6:.1f}" y="{p.Y(yc) + 4:.1f}" font-size="12" '
                       f'text-anchor="{"end" if inside else "start"}" fill="{"white" if inside else INK}">{esc(txt)}</text>')
    save("print-numbers.svg", p.svg())


def print_odds():
    per_hour = TOOLBOX_TRANSIENTS / TOOLBOX_HOURS
    p = Plot("The odds of finishing", "Print length (hours, log scale)", "Chance it finishes (%)", (0.5, 100), (0, 100),
             xlog=True, subtitle=f"Every corner, start, stop and retraction as its own small risk, about {round(per_hour, -3):,.0f} of them an hour")
    p.axes([0.5, 1, 2, 5, 10, 20, 50, 100], [0, 20, 40, 60, 80, 100], ["0.5", "1", "2", "5", "10", "20", "50", "100"])
    ts = logspace(0.5, 100)
    for pe, col, lab in [(1e-6, RED, "1 in a million per event"), (1e-7, ORANGE, "1 in 10 million"),
                         (1e-8, GREEN, "1 in 100 million")]:
        p.line([(t, 100 * math.exp(-pe * per_hour * t)) for t in ts], col, lab)
    p.line([(t, 100 * math.exp(-OBICO_HAZARD * t)) for t in ts], INK, "Obico: one caught failure per 84 h", dash="6 4")
    for t, lab, xt, yt in [(TOOLBOX_HOURS, "the toolbox", 2.3, 64), (24, "a day", 13, 50)]:
        s = 100 * math.exp(-OBICO_HAZARD * t)
        p.point(t, s, INK)
        p.callout(xt, yt, t, s, f"{lab}: {s:.0f}%", anchor="end")
    p.legend("bl")
    save("print-odds.svg", p.svg())


def _segments(pts):
    segs, cur = [], []
    for x, y in pts:
        if y is None:
            if cur:
                segs.append(cur)
            cur = []
        else:
            cur.append((x, y))
    if cur:
        segs.append(cur)
    return segs


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
    melt_profile()
    tip_fin()
    washout()
    pa_flip()
    pressure_wall()
    melt_age_step()
    ooze_time()
    scarf_joint()
    scarf_lag()
    scarf_restart()
    coupling_map()
    timescales()
    sensitivity()
    print_stretch_fig()
    print_numbers()
    print_odds()
