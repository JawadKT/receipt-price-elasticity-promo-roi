import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
from utils import load_receipts, daily_agg, root
from features.price_change_detection import _smooth

fig_dir = root / "reports" / "figures"
tab = root / "reports" / "tables"


def price_change_fig(daily, events):
    # pick the product with the biggest detected move
    ev = events.reindex(events["pct_change"].abs().sort_values(ascending=False).index)
    prod = ev.iloc[0].product_name
    sub = daily[daily.product_name == prod].sort_values("date")
    plt.figure(figsize=(9, 4))
    plt.plot(sub.date, sub.daily_price, alpha=.4, label="daily median")
    plt.plot(sub.date, _smooth(sub.daily_price), lw=2, label="7d rolling median")
    for _, e in events[events.product_name == prod].iterrows():
        plt.axvline(pd.Timestamp(e.start_date), color="crimson", ls="--", alpha=.6)
    plt.title(f"detected price changes: {prod}")
    plt.legend(); plt.tight_layout()
    plt.savefig(fig_dir / "example_price_change.png", dpi=120); plt.close()


def elasticity_fig(est):
    e = est.sort_values("elasticity")
    plt.figure(figsize=(8, 7))
    y = range(len(e))
    plt.errorbar(e.elasticity, y, xerr=[e.elasticity - e.ci_low, e.ci_high - e.elasticity],
                 fmt="o", capsize=3)
    plt.axvline(0, color="k", lw=.8)
    plt.yticks(list(y), e.product_name)
    plt.xlabel("own-price elasticity (95% ci)")
    plt.title("elasticity estimates"); plt.tight_layout()
    plt.savefig(fig_dir / "elasticity_summary.png", dpi=120); plt.close()


def promo_fig(scen):
    plt.figure(figsize=(8, 5))
    for prod, g in scen.groupby("product_name"):
        plt.plot(g.discount_pct, g.revenue_change, marker="o", label=prod)
    plt.axhline(0, color="k", lw=.8)
    plt.xlabel("discount %"); plt.ylabel("daily revenue change")
    plt.title("promo roi curves"); plt.legend(fontsize=8); plt.tight_layout()
    plt.savefig(fig_dir / "promo_roi_curves.png", dpi=120); plt.close()


if __name__ == "__main__":
    daily = daily_agg(load_receipts())
    price_change_fig(daily, pd.read_csv(tab / "price_change_events.csv"))
    elasticity_fig(pd.read_csv(tab / "elasticity_estimates.csv"))
    scen = pd.read_csv(tab / "promo_scenarios.csv")
    if len(scen):
        promo_fig(scen)
    print("figures ->", fig_dir)
