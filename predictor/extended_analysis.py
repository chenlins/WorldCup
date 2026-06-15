"""扩展分析模式：人性分析、同赔率赛事分析。"""

from __future__ import annotations

from dataclasses import dataclass

from data.fixtures import Fixture
from data.group_context import get_group_context
from data.market_consensus import MarketConsensus, compute_market_consensus
from data.same_odds_history import aggregate_odds_outcomes, find_similar_odds_matches
from data.teams import Team
from data.tournament_pedigree import get_pedigree
from predictor.dimensions import MatchDimensionAnalysis


@dataclass
class ExtendedResult:
    mode: str
    mode_label: str
    title: str
    summary: str
    points: list[str]
    impact: str
    win_adj: float
    draw_adj: float
    loss_adj: float
    lam_home_factor: float
    lam_away_factor: float
    confidence_delta: float
    tags: list[str]


def _normalize_triple(w: float, d: float, l: float) -> tuple[float, float, float]:
    s = w + d + l or 1.0
    return w / s, d / s, l / s


def analyze_human_nature(
    home: Team,
    away: Team,
    fixture: Fixture,
    win_p: float,
    draw_p: float,
    loss_p: float,
    market: MarketConsensus,
) -> ExtendedResult:
    points: list[str] = []
    tags: list[str] = []
    w_adj = d_adj = l_adj = 0.0
    lam_h = lam_a = 1.0
    conf_delta = 0.0

    fav_side = "home" if market.home_win_implied >= market.away_win_implied else "away"
    fav_prob = max(market.home_win_implied, market.away_win_implied)
    dog_prob = min(market.home_win_implied, market.away_win_implied)

    # 热门压力
    if fav_prob >= 0.68:
        tags.append("热门压力")
        points.append(
            f"市场大热（隐含 {fav_prob*100:.0f}%），历史显示超级热门存在轻敌、保守和被逼平风险"
            "（如2018阿根廷1-1冰岛、2022阿根廷1-2沙特）。"
        )
        if fav_side == "home":
            w_adj -= 0.04
            d_adj += 0.025
            l_adj += 0.015
            lam_h *= 0.97
        else:
            l_adj -= 0.04
            d_adj += 0.025
            w_adj += 0.015
            lam_a *= 0.97
        conf_delta -= 0.02

    # 弱队无包袱
    if dog_prob <= 0.15:
        tags.append("弱队逆袭窗口")
        points.append("弱队无出线/晋级包袱时，往往敢于一搏，密集防守+偷反击易制造冷门。")
        if fav_side == "home":
            l_adj += 0.03
            w_adj -= 0.02
            lam_a *= 1.04
        else:
            w_adj += 0.03
            l_adj -= 0.02
            lam_h *= 1.04

    # 东道主情感加成
    if home.is_host:
        tags.append("主场狂热")
        points.append(f"{home.name_zh} 东道主作战，球迷情绪可提升首球前压迫强度，但过大压力也可能导致急躁失误。")
        w_adj += 0.02
        lam_h *= 1.03

    # 大赛底蕴心理
    hp = get_pedigree(home.code, home.rating)
    ap = get_pedigree(away.code, away.rating)
    if hp.penalty_win_rate < 0.45 and fixture.is_knockout:
        points.append(f"{home.name_zh} 点球大战历史胜率偏低，淘汰赛平局后心理负担加重。")
        d_adj += 0.015
        conf_delta -= 0.01
    if ap.big_game_rating >= 88 and hp.big_game_rating < 82:
        points.append(f"{away.name_zh} 大赛抗压明显优于主队，关键球处理更冷静。")
        l_adj += 0.02
        w_adj -= 0.02

    # 出线生死战心理
    gctx = get_group_context(fixture, home, away)
    if gctx and gctx.intensity == "极高":
        tags.append("生死战心态")
        points.append("出线生死战：落后方会大举进攻留下空档，领先方可能极度保守，比分波动大。")
        d_adj -= 0.01
        lam_h *= 1.02
        lam_a *= 1.02
        conf_delta -= 0.02

    # 决赛/半决赛压力
    if fixture.stage in ("决赛", "半决赛"):
        tags.append("大赛窒息感")
        points.append(f"{fixture.stage}舞台下球员心理紧绷，过度保守或个别失误会放大，领先方倾向控节奏。")
        d_adj += 0.02
        lam_h *= 0.96
        lam_a *= 0.96
        conf_delta -= 0.02

    # 实力接近的「怕输」心态
    if abs(home.rating - away.rating) < 6 and not fixture.is_knockout:
        tags.append("互有顾忌")
        points.append("实力接近时双方怕输心态上升，上半场试探偏多，平局概率人为抬高。")
        d_adj += 0.025
        w_adj -= 0.012
        l_adj -= 0.012

    # 复仇/德比心理（简化：排名接近+同洲）
    if home.continent and home.continent == away.continent and abs(home.rating - away.rating) < 10:
        points.append("同区域对手交锋，球员更熟悉彼此，情绪对抗可能压倒纸面实力。")

    summary = "人性层面：" + (
        "热门存在轻敌与保守风险，需防平局/冷门。" if fav_prob >= 0.65
        else "双方心理博弈均衡，细节与情绪转折是关键。"
    )
    impact = "已根据热门压力、主客场情绪、生死战心态微调概率"

    return ExtendedResult(
        mode="human",
        mode_label="人性分析",
        title="人性分析",
        summary=summary,
        points=points or ["本场心理因素影响相对中性。"],
        impact=impact,
        win_adj=w_adj,
        draw_adj=d_adj,
        loss_adj=l_adj,
        lam_home_factor=lam_h,
        lam_away_factor=lam_a,
        confidence_delta=conf_delta,
        tags=tags or ["心理中性"],
    )


def analyze_same_odds(
    home: Team,
    away: Team,
    fixture: Fixture,
    win_p: float,
    draw_p: float,
    loss_p: float,
    market: MarketConsensus,
) -> ExtendedResult:
    similar = find_similar_odds_matches(
        market.home_win_implied,
        market.draw_implied,
        market.away_win_implied,
    )
    agg = aggregate_odds_outcomes(similar)

    points = [
        f"当前参考赔率：主 {market.home_odds} / 平 {market.draw_odds} / 客 {market.away_odds}，"
        f"隐含 {market.home_win_implied*100:.1f}% / {market.draw_implied*100:.1f}% / {market.away_win_implied*100:.1f}%。",
        f"匹配历届大赛同档位样本 {agg['count']} 场。",
        f"历史赛果分布：主胜 {agg['home_rate']*100:.0f}% / 平局 {agg['draw_rate']*100:.0f}% / "
        f"客胜 {agg['away_rate']*100:.0f}%，场均总进球 {agg['avg_total_goals']:.1f}。",
        f"历史 upset 率约 {agg['upset_rate']*100:.0f}%（弱队/非热门取胜或逼平）。",
    ]
    for s in agg["samples"][:4]:
        res_zh = {"home": "主胜", "draw": "平", "away": "客胜"}.get(s["result"], s["result"])
        points.append(f"参照：{s['label']} {s['score']}（{res_zh}）— {s['note']}")

    # 模型 75% + 历史同赔率 25% 融合
    blend = 0.25
    hist_w, hist_d, hist_l = agg["home_rate"], agg["draw_rate"], agg["away_rate"]
    new_w = win_p * (1 - blend) + hist_w * blend
    new_d = draw_p * (1 - blend) + hist_d * blend
    new_l = loss_p * (1 - blend) + hist_l * blend

    w_adj = new_w - win_p
    d_adj = new_d - draw_p
    l_adj = new_l - loss_p

    total_goals_factor = agg["avg_total_goals"] / 2.5
    lam_h = (total_goals_factor ** 0.5) * (0.98 + hist_w * 0.04)
    lam_a = (total_goals_factor ** 0.5) * (0.98 + hist_l * 0.04)

    tags = ["同赔率校验"]
    if agg["upset_rate"] >= 0.35:
        tags.append("历史冷门率高")
    if agg["draw_rate"] >= 0.35:
        tags.append("历史平局偏多")

    conf_delta = -0.015 if agg["count"] < 4 else 0.0
    if agg["upset_rate"] >= 0.4:
        conf_delta -= 0.02

    summary = (
        f"同赔率历史 {agg['count']} 场：主胜 {hist_w*100:.0f}% / 平 {hist_d*100:.0f}% / "
        f"客胜 {hist_l*100:.0f}%，已与模型概率融合。"
    )

    return ExtendedResult(
        mode="same_odds",
        mode_label="同赔率赛事分析",
        title="同赔率赛事分析",
        summary=summary,
        points=points,
        impact=f"模型75% + 历史同档位25% 融合，样本{agg['count']}场",
        win_adj=w_adj,
        draw_adj=d_adj,
        loss_adj=l_adj,
        lam_home_factor=lam_h,
        lam_away_factor=lam_a,
        confidence_delta=conf_delta,
        tags=tags,
    )


def run_extended_analysis(
    mode: str,
    home: Team,
    away: Team,
    fixture: Fixture,
    win_p: float,
    draw_p: float,
    loss_p: float,
    lam_h: float,
    lam_a: float,
    market: MarketConsensus | None = None,
) -> ExtendedResult | None:
    if mode in ("none", "", None):
        return None
    mkt = market or compute_market_consensus(home, away)
    if mode == "human":
        return analyze_human_nature(home, away, fixture, win_p, draw_p, loss_p, mkt)
    if mode == "same_odds":
        return analyze_same_odds(home, away, fixture, win_p, draw_p, loss_p, mkt)
    return None


def extended_to_dict(ext: ExtendedResult) -> dict:
    return {
        "mode": ext.mode,
        "mode_label": ext.mode_label,
        "title": ext.title,
        "summary": ext.summary,
        "points": ext.points,
        "impact": ext.impact,
        "tags": ext.tags,
        "probability_adjustment": {
            "win": round(ext.win_adj, 4),
            "draw": round(ext.draw_adj, 4),
            "loss": round(ext.loss_adj, 4),
        },
    }
