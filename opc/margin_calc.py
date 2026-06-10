#!/usr/bin/env python3
"""单品利润计算器（亚马逊日本站）

用法示例：
  python margin_calc.py --name 高龄猫餐架 --price-jpy 3480 --cost 32 --weight 0.45
  python margin_calc.py --name 猫防灾套装 --price-jpy 11800 --cost 95 --weight 1.8 --fba-jpy 650

判定标准（写死在代码里，防止自我安慰）：
  净利率 >= 20%  -> GO（可以做）
  15% ~ 20%      -> WATCH（压成本/提价后再算一次）
  < 15%          -> KILL（放弃，不要赌广告会降）
"""
import argparse

JPY = 0.048  # 日元->人民币汇率，按需更新


def main() -> None:
    p = argparse.ArgumentParser(description="单品利润计算器（日本站FBA）")
    p.add_argument("--name", default="候选品", help="产品名（仅用于显示）")
    p.add_argument("--price-jpy", type=float, required=True, help="售价（日元）")
    p.add_argument("--cost", type=float, required=True, help="1688采购价含包装（人民币）")
    p.add_argument("--weight", type=float, required=True, help="单件毛重（kg，含包装）")
    p.add_argument("--freight-per-kg", type=float, default=30.0, help="头程单价（元/kg，空运专线默认30）")
    p.add_argument("--commission", type=float, default=0.15, help="平台佣金率，默认15%%")
    p.add_argument("--fba-jpy", type=float, default=480.0, help="FBA配送费（日元），小件默认480")
    p.add_argument("--ads-rate", type=float, default=0.15, help="广告占比TACoS，默认15%%")
    p.add_argument("--returns-rate", type=float, default=0.05, help="退货预提，默认5%%")
    p.add_argument("--storage", type=float, default=2.0, help="月仓储分摊（元/件），默认2")
    p.add_argument("--jpy-rate", type=float, default=JPY, help="日元汇率，默认0.048")
    a = p.parse_args()

    price = a.price_jpy * a.jpy_rate
    freight = a.weight * a.freight_per_kg
    commission = a.commission * price
    fba = a.fba_jpy * a.jpy_rate
    ads = a.ads_rate * price
    returns = a.returns_rate * price
    total_cost = a.cost + freight + commission + fba + ads + returns + a.storage
    net = price - total_cost
    margin = net / price

    print(f"\n== {a.name} | 售价 {a.price_jpy:,.0f} 日元（约 {price:.0f} 元）==")
    rows = [
        ("采购成本", a.cost), ("头程运费", freight), (f"佣金 {a.commission:.0%}", commission),
        ("FBA配送费", fba), (f"广告 {a.ads_rate:.0%}", ads),
        (f"退货预提 {a.returns_rate:.0%}", returns), ("仓储分摊", a.storage),
    ]
    for label, v in rows:
        print(f"  {label:<12} {v:>8.1f} 元  ({v / price:.1%})")
    print(f"  {'成本合计':<12} {total_cost:>8.1f} 元  ({total_cost / price:.1%})")
    print(f"  {'单件净利':<12} {net:>8.1f} 元  净利率 {margin:.1%}")

    if margin >= 0.20:
        verdict = "GO —— 可以做，按现金流模型排批次"
    elif margin >= 0.15:
        verdict = "WATCH —— 先谈供应价或提价，压不进20%再放弃"
    else:
        verdict = "KILL —— 放弃。不要赌广告会降、不要赌运费会跌"
    print(f"  判定：{verdict}\n")


if __name__ == "__main__":
    main()
