#!/usr/bin/env python3
"""12-month cash flow model: OPC cross-border e-commerce, budget 120k RMB.
Path: months 1-3 AliExpress semi-managed validation -> month 4 Amazon Japan FBA launch.
All assumptions labeled; rates: 1 JPY = 0.048 RMB."""

JPY = 0.048
BASE_PRICE_JPY = 2980
UNIT_COST = 28.0     # 1688 incl. packaging
FREIGHT = 4.0        # fast sea to JP, ~0.4kg @ ~9-10 RMB/kg incl. clearance
FBA_FEE = 480 * JPY  # JP FBA small standard ~480 JPY
STORAGE = 2.0        # monthly storage allocated per unit

def unit_econ(price_factor=1.0, ads_rate=0.15, returns_rate=0.05):
    price = BASE_PRICE_JPY * JPY * price_factor
    commission = 0.15 * price
    ads = ads_rate * price
    returns = returns_rate * price
    net = price - UNIT_COST - FREIGHT - commission - FBA_FEE - STORAGE - ads - returns
    receipt = price - commission - FBA_FEE - STORAGE - ads - returns  # goods+freight prepaid at batch
    return price, net, receipt

# Sales ramp (units/month), month 4 = launch
sales = {4: 90, 5: 160, 6: 230, 7: 280, 8: 320, 9: 360, 10: 400, 11: 480, 12: 450}
# Batches: (order_month, units): cash out at order, arrives next month; size tracks observed demand
batches = [(3, 400), (5, 500), (7, 800), (9, 1000), (11, 900)]
BATCH_EXTRA = 1000   # inspection/labels/misc per batch

semi_rev = {m: (0 if m == 1 else 2000 if m == 2 else 4000 if m == 3 else 6000) for m in range(1, 13)}
SEMI_MARGIN = 0.12

fixed_monthly = {m: 350 + (210 if m >= 2 else 0) + (4900 * JPY if m >= 3 else 0) for m in range(1, 13)}
one_time = {
    1: [("company setup", 3000)],
    2: [("samples + semi-managed trial stock", 4000)],
    3: [("photography + JP listing translation", 2000)],
    4: [("JP trademark filing", 2500), ("extra launch ads", 1500)],
    5: [("extra launch ads", 1500)],
}
START_CASH = 120000

def run(scale=1.0, price_factor=1.0, ads_rate=0.15, label="BASE"):
    price, unit_net, unit_receipt = unit_econ(price_factor, ads_rate)
    cash, inv, pending = START_CASH, 0, 0.0
    print(f"\n=== {label}: sales x{scale:.0%}, price x{price_factor:.0%}, TACoS {ads_rate:.0%} "
          f"| unit net {unit_net:.1f} RMB ({unit_net/price:.1%}) ===")
    print(f"{'M':>2} {'sold':>5} {'rev(RMB)':>9} {'cash_in':>9} {'cash_out':>9} {'net':>8} {'cash_end':>9} {'inv_end':>7}")
    trough, trough_m = cash, 0
    for m in range(1, 13):
        for bm, units in batches:
            if bm == m - 1:
                inv += int(units * scale)
        sold = min(int(sales.get(m, 0) * scale), inv) if m in sales else 0
        inv -= sold
        receipts = sold * unit_receipt
        cash_in = pending + 0.5 * receipts + semi_rev[m] * SEMI_MARGIN  # 14-day payout lag
        pending = 0.5 * receipts
        out = fixed_monthly[m] + sum(a for _, a in one_time.get(m, []))
        for bm, units in batches:
            if bm == m:
                out += int(units * scale) * (UNIT_COST + FREIGHT) + BATCH_EXTRA
        cash += cash_in - out
        if cash < trough:
            trough, trough_m = cash, m
        print(f"{m:>2} {sold:>5} {sold*price + semi_rev[m]:>9.0f} {cash_in:>9.0f} {out:>9.0f} "
              f"{cash_in-out:>8.0f} {cash:>9.0f} {inv:>7}")
    inv_value = inv * (UNIT_COST + FREIGHT)
    print(f"-> trough {trough:,.0f} (M{trough_m}) | end cash {cash:,.0f} ({cash-START_CASH:+,.0f}) "
          f"| ending inventory {inv} units (cost value ~{inv_value:,.0f}) "
          f"| economic result ~{cash - START_CASH + inv_value:+,.0f}")

p, n, r = unit_econ()
print(f"UNIT ECONOMICS BASE (2,980 JPY SKU): price={p:.1f} RMB, unit net={n:.1f} ({n/p:.1%}), receipt={r:.1f}")
run(1.0, 1.0, 0.15, "BASE")
run(0.6, 0.9, 0.25, "PESSIMISTIC (40% sales miss + price cut 10% + ads blowout 25%)")
run(1.3, 1.0, 0.13, "OPTIMISTIC")
