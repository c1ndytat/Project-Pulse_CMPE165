"""
Project Pulse — Monte Carlo simulation of 4-year NPV (Part J)

Re-uses the Part D NPV model, but replaces single-point estimates with
ranges (triangular distributions: min / most likely / max), then runs the
model 10,000 times to see the full distribution of possible NPVs.

Run:  python monte_carlo.py
Requires: numpy, matplotlib  (pip install numpy matplotlib)
Outputs: printed summary, mc_trials.csv, mc_histogram.png, mc_sensitivity.png, mc_pilot_gate.png
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SEED = 165          # fixed seed -> anyone who runs this gets identical results
N_TRIALS = 10_000
rng = np.random.default_rng(SEED)

# ---- Fixed assumptions (same as Part D) ----
DISCOUNT_RATE = 0.14
PRO_PRICE = 40                                   # $/team/year
BASE_UNIVERSITIES = np.array([3, 8, 14, 18])     # Years 1-4 (Part D base case)
BASE_PRO_TEAMS = np.array([200, 500, 900, 1200])
BASE_OPEX = np.array([20_000, 30_000, 40_000, 45_000])

# ---- Uncertain variables: (min, most likely, max) ----
# The "most likely" value is always the Part D base-case value.
VARIABLES = {
    "Development cost ($)":            (100_000, 120_000, 170_000),  # overruns more likely than savings
    "Universities licensed by Year 4": (6,       18,      24),       # adoption is the biggest unknown (risk R1)
    "License price ($/yr)":            (4_500,   6_000,   7_000),
    "Operating cost multiplier":       (0.9,     1.0,     1.4),      # hosting/support can grow faster than planned
}

def draw(name):
    lo, mode, hi = VARIABLES[name]
    return rng.triangular(lo, mode, hi, N_TRIALS)

dev_cost   = draw("Development cost ($)")
univ_y4    = draw("Universities licensed by Year 4")
lic_price  = draw("License price ($/yr)")
opex_mult  = draw("Operating cost multiplier")

# Adoption scales the whole growth path. Pro-team adoption moves together with
# university adoption (correlated risks, Lecture 6 slide 29).
adoption_factor = univ_y4 / BASE_UNIVERSITIES[-1]
universities = np.outer(adoption_factor, BASE_UNIVERSITIES)
pro_teams    = np.outer(adoption_factor, BASE_PRO_TEAMS)
opex         = np.outer(opex_mult, BASE_OPEX)

revenue   = universities * lic_price[:, None] + pro_teams * PRO_PRICE
cash_flow = revenue - opex                                   # Years 1-4
discount  = 1 / (1 + DISCOUNT_RATE) ** np.arange(1, 5)
npv = (cash_flow * discount).sum(axis=1) - dev_cost

# ---- Scenario B: stage the investment behind a pilot (stop option) ----
# A one-team pilot gives a noisy early signal of adoption. If the signal is
# weak, management stops and loses only the pilot cost instead of the full build.
PILOT_COST = 15_000
GO_THRESHOLD = 18                       # continue only if pilot signals >= 18 universities by Year 4 (the Part D base case)
signal = univ_y4 * rng.normal(1.0, 0.15, N_TRIALS)
go = signal >= GO_THRESHOLD
npv_gated = np.where(go, npv - PILOT_COST, -PILOT_COST)

# ---- Results ----
p10, p50, p90 = np.percentile(npv, [10, 50, 90])
p_neg = (npv < 0).mean()
base_npv = ((BASE_UNIVERSITIES * 6000 + BASE_PRO_TEAMS * PRO_PRICE - BASE_OPEX) * discount).sum() - 120_000
p_below_base = (npv < base_npv).mean()

# Break-even adoption: smallest Year-4 university count where NPV<0 risk falls below 20%
bins = np.arange(6, 25, 2)
breakeven = None
for b in bins:
    sel = univ_y4 >= b
    if sel.sum() > 0 and (npv[sel] < 0).mean() < 0.20:
        breakeven = b; break

print(f"Trials:                    {N_TRIALS:,}")
print(f"Base-case NPV (Part D):    ${base_npv:,.0f}")
print(f"Mean NPV:                  ${npv.mean():,.0f}")
print(f"Median NPV:                ${p50:,.0f}")
print(f"P10 (downside) NPV:        ${p10:,.0f}")
print(f"P90 (upside) NPV:          ${p90:,.0f}")
print(f"Min / Max NPV:             ${npv.min():,.0f} / ${npv.max():,.0f}")
print(f"P(NPV < 0):                {p_neg:.1%}")
print(f"P(NPV < base case):        {p_below_base:.1%}")
print(f"P(dev cost > $150K):       {(dev_cost > 150_000).mean():.1%}")
print(f"--- With pilot gate (stop if signal < {GO_THRESHOLD}) ---")
print(f"Share of trials that continue: {go.mean():.1%}")
print(f"Mean NPV (gated):          ${npv_gated.mean():,.0f}")
print(f"P10 / P90 NPV (gated):     ${np.percentile(npv_gated,10):,.0f} / ${np.percentile(npv_gated,90):,.0f}")
print(f"P(NPV < 0) (gated):        {(npv_gated < 0).mean():.1%}")
print(f"P(loss > $15K) (gated):    {(npv_gated < -PILOT_COST).mean():.1%}   vs. full commitment: {(npv < -PILOT_COST).mean():.1%}")
needed_cut = max(0, -npv_gated.mean() / go.mean())
print(f"Dev-cost cut needed for gated mean NPV >= 0: ${needed_cut:,.0f}")
print(f"Adoption for <20% loss risk: >= {breakeven} universities by Year 4")

# Sensitivity: correlation of each input with NPV
inputs = {"Universities by Year 4": univ_y4, "License price": lic_price,
          "Development cost": dev_cost, "Operating cost multiplier": opex_mult}
corr = {k: np.corrcoef(v, npv)[0, 1] for k, v in inputs.items()}
for k, v in sorted(corr.items(), key=lambda kv: -abs(kv[1])):
    print(f"Correlation with NPV — {k:28s} {v:+.2f}")

# ---- Save trials ----
np.savetxt("mc_trials.csv",
           np.column_stack([np.arange(1, N_TRIALS + 1), dev_cost, univ_y4, lic_price, opex_mult, npv, go, npv_gated]),
           delimiter=",", fmt=["%d", "%.0f", "%.2f", "%.0f", "%.3f", "%.0f", "%d", "%.0f"],
           header="trial,dev_cost,universities_y4,license_price,opex_multiplier,npv_full_commitment,pilot_go,npv_with_pilot_gate", comments="")

# ---- Chart 1: NPV distribution ----
fig, ax = plt.subplots(figsize=(10, 5.5))
ax.hist(npv[npv < 0] / 1000, bins=np.arange(-200, 150, 5), color="#C62828", alpha=0.85, label=f"NPV < 0  ({p_neg:.0%} of trials)")
ax.hist(npv[npv >= 0] / 1000, bins=np.arange(-200, 150, 5), color="#2F5496", alpha=0.85, label="NPV ≥ 0")
def k(v): return f"{'−' if v < 0 else ''}${abs(v)/1000:,.0f}K"
ymax = ax.get_ylim()[1]; ax.set_ylim(0, ymax * 1.25)
for x, lab, ls in [(0, "Break-even", "-"), (npv.mean(), f"Mean {k(npv.mean())}", "--"),
                   (base_npv, f"Part D base {k(base_npv)}", ":")]:
    ax.axvline(x / 1000, color="black", ls=ls, lw=1.3)
    ax.text(x / 1000, ymax * 1.22, lab, fontsize=9, rotation=90, va="top", ha="right")
ax.set_title(f"Project Pulse — Distribution of 4-year NPV ({N_TRIALS:,} Monte Carlo trials)")
ax.set_xlabel("NPV ($ thousands)"); ax.set_ylabel("Number of trials"); ax.legend(loc="upper left")
plt.tight_layout(); plt.savefig("mc_histogram.png", dpi=130); plt.close()

# ---- Chart 2: sensitivity ----
items = sorted(corr.items(), key=lambda kv: abs(kv[1]))
fig, ax = plt.subplots(figsize=(8, 3.8))
ax.barh([k for k, _ in items], [v for _, v in items],
        color=["#2F5496" if v > 0 else "#C62828" for _, v in items])
ax.axvline(0, color="black", lw=0.8)
for i, (_, v) in enumerate(items):
    ax.text(v + (0.02 if v > 0 else -0.02), i, f"{v:+.2f}", va="center", ha="left" if v > 0 else "right", fontsize=9)
ax.set_xlim(-1, 1); ax.set_xlabel("Correlation with NPV")
ax.set_title("Which uncertainty drives NPV the most?")
plt.tight_layout(); plt.savefig("mc_sensitivity.png", dpi=130); plt.close()

# ---- Chart 3: full commitment vs. pilot gate ----
def k(v): return f"{'−' if v < 0 else ''}${abs(v)/1000:,.0f}K"
labels = ["Commit full budget\nnow", "Pilot first,\ncontinue only if strong"]
p_big_loss = [(npv < -PILOT_COST).mean(), (npv_gated < -PILOT_COST).mean()]
p10s = [np.percentile(npv, 10), np.percentile(npv_gated, 10)]
fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
cols = ["#C62828", "#2E7D32"]
axes[0].bar(labels, [p * 100 for p in p_big_loss], color=cols)
for i, p in enumerate(p_big_loss): axes[0].text(i, p * 100 + 1, f"{p:.1%}", ha="center", fontsize=11, weight="bold")
axes[0].set_ylabel("% of trials"); axes[0].set_ylim(0, 60)
axes[0].set_title("Probability of losing more than $15K")
axes[1].bar(labels, [v / 1000 for v in p10s], color=cols)
for i, v in enumerate(p10s): axes[1].text(i, v / 1000 - 6, k(v), ha="center", fontsize=11, weight="bold")
axes[1].axhline(0, color="black", lw=0.8); axes[1].set_ylim(-110, 5)
axes[1].set_ylabel("NPV ($ thousands)"); axes[1].set_title("Downside (P10) NPV")
fig.suptitle("Staging the investment behind a pilot caps the downside", weight="bold")
plt.tight_layout(); plt.savefig("mc_pilot_gate.png", dpi=130); plt.close()
