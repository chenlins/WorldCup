"""比分三步定位法：胜平负锁定 → 总进球框定 → 交叉筛选精准比分。"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field

from data.fixtures import Fixture
from data.head_to_head import HeadToHeadRecord, estimate_h2h, get_head_to_head
from data.market_consensus import MarketConsensus, compute_market_consensus
from data.team_extended import get_advanced_metrics
from data.team_profiles import TeamProfile, get_team_profile, injury_impact
from data.teams import Team
from data.venues_meta import VenueMeta, get_venue_meta
from predictor.types import ScoreLine


@dataclass
class ScoreRefinementResult:
    direction: str
    direction_detail: str
    excluded_outcomes: list[str]
    goal_range: tuple[int, int]
    goal_range_detail: str
    candidate_scores: list[str]
    final_score: str
    final_probability: float
    reasoning: list[str] = field(default_factory=list)
    xg_quality_note: str = ""
    odds_validation: str = ""


# 战术风格常见比分模板
_STYLE_TYPICAL: dict[str, list[tuple[int, int]]] = {
    "密集防守": [(0, 0), (1, 0), (0, 1), (1, 1)],
    "防守反击": [(1, 0), (0, 1), (1, 1), (0, 0), (2, 1)],
    "控球进攻": [(2, 1), (2, 0), (1, 1), (3, 1), (1, 0)],
    "高位压迫": [(2, 1), (3, 1), (1, 1), (2, 2), (2, 0)],
    "均衡": [(1, 1), (2, 1), (1, 0), (2, 0), (0, 1)],
}


def _outcome_type(home: int, away: int) -> str:
    if home > away:
        return "主胜"
    if home < away:
        return "客胜"
    return "平局"


def _parse_h2h_scores(h2h: HeadToHeadRecord) -> list[tuple[int, int]]:
    parsed: list[tuple[int, int]] = []
    for s in h2h.recent_scores:
        parts = s.split("-")
        if len(parts) == 2:
            try:
                parsed.append((int(parts[0]), int(parts[1])))
            except ValueError:
                pass
    return parsed


def _step1_lock_direction(
    win_p: float,
    draw_p: float,
    loss_p: float,
    knockout: bool,
) -> tuple[set[str], str, str, list[str]]:
    """第一步：锁定胜平负大方向，返回允许的结果类型集合。"""
    allowed: set[str] = {"主胜", "平局", "客胜"}
    excluded: list[str] = []

    unbeaten_home = win_p + draw_p
    unbeaten_away = loss_p + draw_p

    if win_p >= 0.50 and loss_p <= 0.22:
        direction = "主胜"
        detail = f"主胜概率 {win_p*100:.1f}% 明显领先，客胜仅 {loss_p*100:.1f}%"
        if unbeaten_home >= 0.72:
            allowed.discard("客胜")
            excluded.append("客胜")
            direction = "主队不败"
            detail += f"；主不败合计 {unbeaten_home*100:.1f}%，排除全部客胜比分"
    elif loss_p >= 0.50 and win_p <= 0.22:
        direction = "客胜"
        detail = f"客胜概率 {loss_p*100:.1f}% 明显领先"
        if unbeaten_away >= 0.72:
            allowed.discard("主胜")
            excluded.append("主胜")
            direction = "客队不败"
            detail += f"；客不败合计 {unbeaten_away*100:.1f}%，排除全部主胜比分"
    elif draw_p >= 0.30 and abs(win_p - loss_p) < 0.12:
        direction = "平局倾向"
        detail = f"平局 {draw_p*100:.1f}%，双方差距小，小比分平局权重提升"
    elif win_p >= loss_p + 0.15:
        direction = "主胜"
        detail = f"主胜 {win_p*100:.1f}% > 客胜 {loss_p*100:.1f}%，大方向倾向主队"
        if loss_p < 0.18:
            allowed.discard("客胜")
            excluded.append("客胜")
            detail += "，低客胜概率下剔除客胜比分"
    elif loss_p >= win_p + 0.15:
        direction = "客胜"
        detail = f"客胜 {loss_p*100:.1f}% > 主胜 {win_p*100:.1f}%"
        if win_p < 0.18:
            allowed.discard("主胜")
            excluded.append("主胜")
    else:
        direction = "开放"
        detail = "胜平负三项接近，暂不硬性排除任一方向"

    if knockout:
        detail += "；淘汰赛平局后进入加时/点球，平局比分仍保留但权重下调"

    return allowed, direction, detail, excluded


def _step2_goal_range(
    lam_h: float,
    lam_a: float,
    home_prof: TeamProfile,
    away_prof: TeamProfile,
    venue: VenueMeta,
    h2h: HeadToHeadRecord,
    fixture: Fixture,
) -> tuple[int, int, str]:
    """第二步：框定总进球范围。"""
    total_xg = lam_h + lam_a
    center = round(total_xg)

    ht, at = home_prof.tactics, away_prof.tactics
    def_styles = ("密集防守", "防守反击")
    both_def = ht.style in def_styles and at.style in def_styles
    either_def = ht.style in def_styles or at.style in def_styles

    lo = max(0, center - 1)
    hi = min(6, center + 2)

    if both_def:
        lo, hi = 0, min(3, hi)
        note = f"双方均为{ht.style if ht.style in def_styles else at.style}，总进球倾向 0-3"
    elif either_def:
        hi = min(hi, 4)
        note = "一方防守型，总进球上限压低"
    elif ht.style == "控球进攻" and at.style == "控球进攻":
        lo = max(1, lo)
        hi = min(5, hi + 1)
        note = "双方进攻型，总进球区间略宽"
    else:
        note = f"预期总 xG {total_xg:.2f}，常规区间 {lo}-{hi}"

    if h2h.avg_total_goals <= 2.0:
        hi = min(hi, 3)
        lo = min(lo, 2)
        note += f"；历史交锋场均仅 {h2h.avg_total_goals:.1f} 球"
    elif h2h.avg_total_goals >= 3.0:
        hi = min(6, hi + 1)
        note += f"；历史交锋场均 {h2h.avg_total_goals:.1f} 球偏多"

    h_inj, _, _ = injury_impact(home_prof.key_players)
    a_inj, _, _ = injury_impact(away_prof.key_players)
    if h_inj < 0.85 or a_inj < 0.85:
        hi = max(lo, hi - 1)
        note += "；核心射手/进攻球员缺阵，进球上限下调"

    climate = venue.june_climate
    if venue.altitude_m >= 1500:
        hi = max(lo, hi - 1)
        note += f"；{venue.city} 高海拔({venue.altitude_m}m)消耗客队体能，总进球压低"
    if "雨" in climate or "湿" in climate:
        hi = max(lo, hi - 1)
        note += "；雨战传控失误率上升，进球效率下降"
    if fixture.stage in ("半决赛", "决赛"):
        hi = max(lo, min(hi, 3))
        note += f"；{fixture.stage}战术趋于保守"

    if lo > hi:
        lo = hi

    return lo, hi, note


def _xg_quality_adjustment(
    home: Team,
    away: Team,
    lam_h: float,
    lam_a: float,
) -> tuple[float, float, str]:
    """进阶：xG 质量修正，区分稳定得分与运气型球队。"""
    hm = get_advanced_metrics(home.code, home.rating, home.attack, home.defense)
    am = get_advanced_metrics(away.code, away.rating, away.attack, away.defense)

    h_factor = 0.97 + hm.xg_overperformance * 0.06
    a_factor = 0.97 + am.xg_overperformance * 0.06

    notes = []
    if hm.xg_overperformance > 1.05:
        notes.append(f"{home.name_zh} 终结效率高于机会质量，xG 略向下修正防回归")
        h_factor *= 0.98
    elif hm.xg_overperformance < 0.95:
        notes.append(f"{home.name_zh} 机会创造优于转化，存在补涨空间")
        h_factor *= 1.02

    if am.xg_overperformance > 1.05:
        notes.append(f"{away.name_zh} 进球效率超预期，客场 xG 略下调")
        a_factor *= 0.98
    elif am.xg_overperformance < 0.95:
        a_factor *= 1.02

    return lam_h * h_factor, lam_a * a_factor, "；".join(notes) if notes else "xG 质量与历史转化效率匹配"


def _odds_score_validation(
    market: MarketConsensus,
    win_p: float,
    draw_p: float,
    loss_p: float,
    best: ScoreLine,
) -> str:
    """进阶：赔率交叉验证，识别异常偏离。"""
    m_home, m_draw, m_away = (
        market.home_win_implied,
        market.draw_implied,
        market.away_win_implied,
    )
    divs = [
        ("主胜", win_p - m_home),
        ("平局", draw_p - m_draw),
        ("客胜", loss_p - m_away),
    ]
    item, delta = max(divs, key=lambda x: abs(x[1]))

    if abs(delta) >= 0.15:
        return (
            f"模型与市场在「{item}」上分歧 {abs(delta)*100:.0f}pp，"
            f"当前首选比分 {best.home}-{best.away} 需警惕冷门陷阱"
        )
    if abs(delta) <= 0.06:
        return f"模型与市场方向一致，比分 {best.home}-{best.away} 与赔率逻辑吻合"
    return f"模型与市场轻度分歧（{item} {delta*100:+.0f}pp），比分预判中等置信"


def _step3_cross_filter(
    scores: list[ScoreLine],
    allowed: set[str],
    goal_lo: int,
    goal_hi: int,
    h2h_parsed: list[tuple[int, int]],
    home_prof: TeamProfile,
    away_prof: TeamProfile,
    knockout: bool,
) -> tuple[list[ScoreLine], list[str]]:
    """第三步：交叉筛选并重新加权。"""
    weighted: list[ScoreLine] = []
    typical = set(_STYLE_TYPICAL.get(home_prof.tactics.style, []))
    typical |= set(_STYLE_TYPICAL.get(away_prof.tactics.style, []))

    for s in scores:
        p = s.probability
        ot = _outcome_type(s.home, s.away)
        total = s.home + s.away

        if ot not in allowed:
            p *= 0.012

        if total < goal_lo:
            p *= 0.06 ** (goal_lo - total)
        elif total > goal_hi:
            p *= 0.10 ** (total - goal_hi)

        if (s.home, s.away) in h2h_parsed:
            p *= 1.35

        if (s.home, s.away) in typical:
            p *= 1.18

        if knockout and s.home == s.away:
            p *= 0.75

        weighted.append(ScoreLine(s.home, s.away, p))

    total_p = sum(x.probability for x in weighted) or 1.0
    for x in weighted:
        x.probability /= total_p
    weighted.sort(key=lambda x: x.probability, reverse=True)

    candidates = [f"{s.home}-{s.away}" for s in weighted[:8]]
    return weighted, candidates


def refine_score_prediction(
    home: Team,
    away: Team,
    fixture: Fixture,
    scores: list[ScoreLine],
    win_p: float,
    draw_p: float,
    loss_p: float,
    lam_h: float,
    lam_a: float,
    market: MarketConsensus | None = None,
) -> tuple[list[ScoreLine], str, float, float, ScoreRefinementResult]:
    """
    执行三步定位 + 进阶校验。
    返回 (精炼后比分列表, 最终比分, 修正后lam_h, 修正后lam_a, 三步解读)。
    """
    home_prof = get_team_profile(home.code, home.rating, home.attack, home.defense)
    away_prof = get_team_profile(away.code, away.rating, away.attack, away.defense)
    venue = get_venue_meta(fixture.city)
    h2h = get_head_to_head(home.code, away.code) or estimate_h2h(
        home.code, away.code, home.rating, away.rating
    )
    mkt = market or compute_market_consensus(home, away)

    lam_h, lam_a, xg_note = _xg_quality_adjustment(home, away, lam_h, lam_a)

    allowed, direction, dir_detail, excluded = _step1_lock_direction(
        win_p, draw_p, loss_p, fixture.is_knockout
    )
    goal_lo, goal_hi, goal_detail = _step2_goal_range(
        lam_h, lam_a, home_prof, away_prof, venue, h2h, fixture
    )
    h2h_parsed = _parse_h2h_scores(h2h)

    refined, candidates = _step3_cross_filter(
        copy.deepcopy(scores),
        allowed,
        goal_lo,
        goal_hi,
        h2h_parsed,
        home_prof,
        away_prof,
        fixture.is_knockout,
    )

    best = refined[0]
    odds_note = _odds_score_validation(mkt, win_p, draw_p, loss_p, best)

    reasoning = [
        f"【第一步·胜平负】{direction}：{dir_detail}",
        f"【第二步·总进球】范围 {goal_lo}-{goal_hi} 球：{goal_detail}",
    ]
    if h2h.recent_scores:
        reasoning.append(f"历史常见比分：{'、'.join(h2h.recent_scores)}")
    reasoning.append(
        f"【第三步·交叉筛选】保留 {len(candidates)} 个候选，"
        f"首选 {best.home}-{best.away}（{best.probability*100:.1f}%）"
    )
    if excluded:
        reasoning.append(f"已排除方向：{'、'.join(excluded)}")

    result = ScoreRefinementResult(
        direction=direction,
        direction_detail=dir_detail,
        excluded_outcomes=excluded,
        goal_range=(goal_lo, goal_hi),
        goal_range_detail=goal_detail,
        candidate_scores=candidates[:6],
        final_score=f"{best.home}-{best.away}",
        final_probability=best.probability,
        reasoning=reasoning,
        xg_quality_note=xg_note,
        odds_validation=odds_note,
    )

    return refined, result.final_score, lam_h, lam_a, result


def refinement_to_dict(r: ScoreRefinementResult) -> dict:
    return {
        "direction": r.direction,
        "direction_detail": r.direction_detail,
        "excluded_outcomes": r.excluded_outcomes,
        "goal_range": {"min": r.goal_range[0], "max": r.goal_range[1]},
        "goal_range_detail": r.goal_range_detail,
        "candidate_scores": r.candidate_scores,
        "final_score": r.final_score,
        "final_probability": round(r.final_probability, 4),
        "reasoning": r.reasoning,
        "xg_quality_note": r.xg_quality_note,
        "odds_validation": r.odds_validation,
    }
