"""庄家最优比分：模拟竞彩/欧赔平台赔率结构，推算庄家最期盼的赛果。"""

from __future__ import annotations

import math
from dataclasses import dataclass

from data.market_consensus import MarketConsensus
from data.teams import Team
from predictor.types import ScoreLine


# 彩民热门比分热度（0-1，越高表示投注越集中、庄家赔付压力越大）
_PUBLIC_HEAT: dict[tuple[int, int], float] = {
    (1, 0): 0.94, (2, 1): 0.96, (2, 0): 0.90, (1, 1): 0.92, (0, 0): 0.78,
    (0, 1): 0.88, (1, 2): 0.86, (3, 1): 0.72, (3, 0): 0.68, (2, 2): 0.65,
    (3, 2): 0.55, (0, 2): 0.70, (2, 3): 0.58, (1, 3): 0.52, (4, 1): 0.45,
    (4, 0): 0.42, (3, 3): 0.38, (0, 3): 0.48, (4, 2): 0.35,
}

# 平台抽水率参考（胜平负/比分）
_PLATFORM_MARGIN = {
    "竞彩": 1.26,
    "欧赔均值": 1.18,
    "亚洲盘": 1.14,
}


@dataclass
class BookmakerScorePick:
    home: int
    away: int
    true_prob: float
    jc_odds: float  # 竞彩参考赔率
    euro_odds: float
    public_heat: float
    hope_index: float
    liability_rank: int  # 赔付压力排名，越低庄家越盼


@dataclass
class BookmakerAnalysis:
    optimal_score: str
    optimal_pick: BookmakerScorePick
    model_score: str
    summary: str
    points: list[str]
    tags: list[str]
    top_bookmaker_picks: list[dict]
    platform_note: str


def _public_heat(h: int, a: int) -> float:
    if (h, a) in _PUBLIC_HEAT:
        return _PUBLIC_HEAT[(h, a)]
    total = h + a
    if total <= 1:
        return 0.55
    if total >= 5:
        return 0.30
    return 0.40 + 0.05 * (3 - abs(total - 2.5))


def _platform_odds(true_prob: float, margin: float) -> float:
    """由真实概率反推庄家挂牌赔率（含抽水）。"""
    if true_prob <= 0.001:
        return 99.0
    implied = true_prob * margin
    return round(max(4.5, min(120.0, 1.0 / implied)), 2)


def _outcome_label(h: int, a: int) -> str:
    if h > a:
        return "主胜"
    if h < a:
        return "客胜"
    return "平局"


def analyze_bookmaker_optimal_score(
    home: Team,
    away: Team,
    scores: list[ScoreLine],
    win_p: float,
    draw_p: float,
    loss_p: float,
    market: MarketConsensus,
    model_score: str,
) -> BookmakerAnalysis:
    """
    庄家最优比分逻辑：
    1. 模拟竞彩/欧赔比分赔率；
    2. 估算彩民投注热度（热门比分赔付压力大）；
    3. 在「有一定发生概率」的比分中，选取庄家期望留存最高者。
    """
    fav_home = market.home_win_implied >= market.away_win_implied
    fav_margin = abs(market.home_win_implied - market.away_win_implied)

    picks: list[BookmakerScorePick] = []
    for s in scores:
        if s.probability < 0.025:
            continue
        heat = _public_heat(s.home, s.away)
        jc = _platform_odds(s.probability, _PLATFORM_MARGIN["竞彩"])
        euro = _platform_odds(s.probability, _PLATFORM_MARGIN["欧赔均值"])
        avg_odds = (jc + euro) / 2

        # 投注份额近似：彩民偏向低赔热门比分
        bet_share = heat / max(avg_odds, 1.0)
        payout_pressure = bet_share * avg_odds

        # 庄家期盼指数：真实概率 × 高赔 × 低赔付压力；逆向赛果额外加权
        hope = s.probability * (1.0 - heat) * math.log(avg_odds + 1)
        ot = _outcome_label(s.home, s.away)
        if fav_home and fav_margin >= 0.15:
            if ot in ("平局", "客胜"):
                hope *= 1.35
            elif ot == "主胜" and s.home - s.away >= 2:
                hope *= 0.85
        elif not fav_home and fav_margin >= 0.15:
            if ot in ("平局", "主胜"):
                hope *= 1.30

        if heat >= 0.90:
            hope *= 0.72

        picks.append(BookmakerScorePick(
            s.home, s.away, s.probability, jc, euro, heat, hope, 0,
        ))

    if not picks:
        best = scores[0]
        picks.append(BookmakerScorePick(
            best.home, best.away, best.probability,
            _platform_odds(best.probability, 1.26),
            _platform_odds(best.probability, 1.18),
            _public_heat(best.home, best.away), 0.5, 0,
        ))

    picks.sort(key=lambda x: x.hope_index, reverse=True)
    liability_sorted = sorted(picks, key=lambda x: x.public_heat * x.true_prob)
    for i, p in enumerate(liability_sorted):
        for pick in picks:
            if pick.home == p.home and pick.away == p.away:
                pick.liability_rank = i + 1

    optimal = picks[0]
    opt_str = f"{optimal.home}-{optimal.away}"

    points = [
        f"模型三步定位参考比分：{model_score}；庄家最优比分：{opt_str}。",
        f"竞彩参考赔率 {optimal.jc_odds} / 欧赔均值 {optimal.euro_odds}（真实概率约 {optimal.true_prob*100:.1f}%）。",
        f"彩民热度 {optimal.public_heat*100:.0f}%（越低庄家赔付压力越小）。",
        f"市场热门：{market.favorite}（{market.margin*100:.1f}%），"
        f"庄家倾向引导资金流向与赛果偏离热门选项。",
    ]

    if fav_home and _outcome_label(optimal.home, optimal.away) != "主胜":
        points.append("主队为市场热门，庄家更期盼平局或客胜等逆向比分，以消化主胜方向筹码。")
    elif not fav_home and _outcome_label(optimal.home, optimal.away) != "客胜":
        points.append("客队为市场热门，庄家更期盼主胜或平局等逆向赛果。")

    hot = max(picks, key=lambda x: x.public_heat)
    points.append(
        f"彩民最热比分 {hot.home}-{hot.away}（热度 {hot.public_heat*100:.0f}%），"
        f"若打出庄家赔付压力最大；最优比分赔付压力排名第 {optimal.liability_rank}。"
    )

    # 次优庄家期盼比分
    alt = picks[1:4]
    if alt:
        alt_text = "、".join(f"{p.home}-{p.away}" for p in alt)
        points.append(f"庄家次优期盼比分：{alt_text}。")

    tags = ["庄家视角", "竞彩/欧赔参考"]
    if optimal.public_heat < 0.60:
        tags.append("低赔付压力")
    if _outcome_label(optimal.home, optimal.away) != market.favorite.replace("主胜", "主胜").replace("客胜", "客胜"):
        if market.favorite == "主胜" and _outcome_label(optimal.home, optimal.away) != "主胜":
            tags.append("逆向赛果")
        elif market.favorite == "客胜" and _outcome_label(optimal.home, optimal.away) != "客胜":
            tags.append("逆向赛果")

    summary = (
        f"综合竞彩（抽水约26%）与欧赔（约18%）比分赔率结构，"
        f"庄家最期盼 {opt_str}（参考赔率 {optimal.jc_odds}），"
        f"较模型参考 {model_score} 更有利于庄家控制赔付。"
    )

    top_table = [
        {
            "score": f"{p.home}-{p.away}",
            "true_prob": round(p.true_prob, 4),
            "jc_odds": p.jc_odds,
            "euro_odds": p.euro_odds,
            "public_heat": round(p.public_heat, 3),
            "hope_index": round(p.hope_index, 4),
        }
        for p in picks[:5]
    ]

    return BookmakerAnalysis(
        optimal_score=opt_str,
        optimal_pick=optimal,
        model_score=model_score,
        summary=summary,
        points=points,
        tags=tags,
        top_bookmaker_picks=top_table,
        platform_note="赔率由泊松真实概率 × 平台抽水推算，参考竞彩、Bet365/威廉希尔欧赔均值结构。",
    )


def bookmaker_to_extended_dict(b: BookmakerAnalysis) -> dict:
    p = b.optimal_pick
    return {
        "mode": "bookmaker",
        "mode_label": "庄家最优比分",
        "title": "庄家最优比分",
        "summary": b.summary,
        "points": b.points,
        "impact": "输出替换为庄家视角最优比分，模型参考保留在对比中",
        "tags": b.tags,
        "bookmaker_optimal_score": b.optimal_score,
        "model_reference_score": b.model_score,
        "reference_odds": {
            "jincai": p.jc_odds,
            "europe_avg": p.euro_odds,
        },
        "public_heat": round(p.public_heat, 3),
        "hope_index": round(p.hope_index, 4),
        "top_picks": b.top_bookmaker_picks,
        "platform_note": b.platform_note,
        "probability_adjustment": {"win": 0, "draw": 0, "loss": 0},
    }
