"""市场共识：由实力指数推导的隐含胜率，用于与模型交叉验证。"""

from __future__ import annotations

import math
from dataclasses import dataclass

from data.teams import Team


@dataclass(frozen=True)
class MarketConsensus:
    home_win_implied: float
    draw_implied: float
    away_win_implied: float
    home_odds: float  # 欧洲十进制赔率参考
    draw_odds: float
    away_odds: float
    favorite: str  # 主胜 / 平局 / 客胜
    margin: float  # 热门方隐含概率
    note: str


def _host_edge(home: Team, away: Team) -> float:
    edge = 0.06
    if home.is_host:
        edge += 0.05
    if away.is_host:
        edge -= 0.03
    return edge


def compute_market_consensus(home: Team, away: Team) -> MarketConsensus:
    """基于 FIFA 排名与实力评分推导赛前市场隐含概率（无实时赔率时的专业估算）。"""
    rank_edge = (away.fifa_rank - home.fifa_rank) / 80.0
    rating_edge = (home.rating - away.rating) / 55.0
    combined = rating_edge + rank_edge * 0.35 + _host_edge(home, away)

    # Logistic 映射为主胜概率
    home_win = 1.0 / (1.0 + math.exp(-combined * 2.2))
    closeness = 1.0 - min(abs(home.rating - away.rating) / 40.0, 1.0)
    draw = 0.18 + closeness * 0.14
    if home.is_host or away.is_host:
        draw -= 0.02
    draw = max(0.16, min(0.32, draw))

    total = home_win + draw
    away_win = max(0.08, 1.0 - total)
    if away_win < 0.08:
        scale = 0.92 / (home_win + draw)
        home_win *= scale
        draw *= scale
        away_win = 0.08

    s = home_win + draw + away_win
    home_win, draw, away_win = home_win / s, draw / s, away_win / s

    probs = [("主胜", home_win), ("平局", draw), ("客胜", away_win)]
    favorite, margin = max(probs, key=lambda x: x[1])

    def _odds(p: float) -> float:
        return round(max(1.12, min(15.0, 1.0 / max(p, 0.05))), 2)

    note = f"市场参考热门：{favorite}（隐含 {margin*100:.1f}%）"
    if abs(home.rating - away.rating) < 6:
        note += "；实力接近，盘口或倾向平局分流"

    return MarketConsensus(
        home_win_implied=round(home_win, 4),
        draw_implied=round(draw, 4),
        away_win_implied=round(away_win, 4),
        home_odds=_odds(home_win),
        draw_odds=_odds(draw),
        away_odds=_odds(away_win),
        favorite=favorite,
        margin=round(margin, 4),
        note=note,
    )


def market_multiplier(consensus: MarketConsensus, side: str) -> float:
    """轻微向市场热门倾斜（权重很低，仅作校验）。"""
    if side == "home":
        p = consensus.home_win_implied
    elif side == "away":
        p = consensus.away_win_implied
    else:
        return 1.0
    return 0.97 + p * 0.06


def model_market_divergence(
    consensus: MarketConsensus,
    win_p: float,
    draw_p: float,
    loss_p: float,
) -> tuple[float, str, list[str]]:
    """
    模型 vs 市场分歧度。
    返回 (最大分歧, 分歧方向说明, 要点列表)。
    """
    diffs = [
        ("主胜", win_p - consensus.home_win_implied),
        ("平局", draw_p - consensus.draw_implied),
        ("客胜", loss_p - consensus.away_win_implied),
    ]
    item, delta = max(diffs, key=lambda x: abs(x[1]))
    max_div = abs(delta)
    points = [
        f"市场隐含：主胜 {consensus.home_win_implied*100:.1f}% / 平 {consensus.draw_implied*100:.1f}% / "
        f"客胜 {consensus.away_win_implied*100:.1f}%。",
        f"参考赔率：主 {consensus.home_odds} / 平 {consensus.draw_odds} / 客 {consensus.away_odds}。",
        consensus.note,
    ]
    direction = ""
    if max_div >= 0.10:
        if delta > 0:
            direction = f"模型比市场更看好{item}（+{delta*100:.1f}pp）"
            points.append(f"分歧：{direction}，存在价值偏离或模型捕捉到市场低估因素。")
        else:
            direction = f"模型比市场更看低{item}（{delta*100:.1f}pp）"
            points.append(f"分歧：{direction}，市场可能已定价伤病/战意等信息。")
    else:
        direction = "模型与市场基本一致"
        points.append("模型与市场方向一致，预判稳定性较高。")

    return max_div, direction, points
