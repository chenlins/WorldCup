"""多维综合分析：十维框架 + 分析师研判（含市场共识校验）。"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from data.fixtures import Fixture
from data.group_context import GroupContext, get_group_context, group_intensity_multiplier
from data.head_to_head import HeadToHeadRecord, estimate_h2h, get_head_to_head
from data.market_consensus import (
    MarketConsensus,
    compute_market_consensus,
    market_multiplier,
    model_market_divergence,
)
from data.schedule_load import ScheduleLoad, get_schedule_load, schedule_multiplier
from data.team_extended import (
    AdvancedMetrics,
    SquadDepth,
    depth_multiplier,
    get_advanced_metrics,
    get_squad_depth,
    metrics_multiplier,
)
from data.team_profiles import (
    TeamProfile,
    form_multiplier,
    get_team_profile,
    home_away_multiplier,
    injury_impact,
)
from data.teams import Team, group_standings_prediction
from data.tournament_pedigree import TournamentPedigree, get_pedigree, pedigree_multiplier
from data.venues_meta import VenueMeta, get_venue_meta


@dataclass
class DimensionBlock:
    title: str
    summary: str
    points: list[str] = field(default_factory=list)
    impact: str = ""


@dataclass
class AnalystVerdict:
    summary: str
    risk_tags: list[str]
    confidence_level: str  # 高 / 中 / 低
    recommendation: str
    caveats: list[str]


@dataclass
class MatchDimensionAnalysis:
    team_basics: DimensionBlock
    head_to_head: DimensionBlock
    key_players: DimensionBlock
    tactical: DimensionBlock
    external: DimensionBlock
    tournament_pedigree: DimensionBlock
    squad_depth: DimensionBlock
    advanced_metrics: DimensionBlock
    schedule_load: DimensionBlock
    market_consensus: DimensionBlock
    analyst_verdict: AnalystVerdict
    market: MarketConsensus | None = None
    xg_home_adj: float = 1.0
    xg_away_adj: float = 1.0
    confidence_adj: float = 0.0


# 向后兼容别名
FiveDimensionAnalysis = MatchDimensionAnalysis

STYLE_CLASH: dict[tuple[str, str], tuple[float, str]] = {
    ("控球进攻", "密集防守"): (0.88, "控球方久攻不下风险高，易出小比分"),
    ("控球进攻", "防守反击"): (0.95, "控球方主导但需防反击，比分分布较广"),
    ("高位压迫", "防守反击"): (1.05, "对攻节奏快，易出大比分"),
    ("高位压迫", "密集防守"): (0.92, "压迫遇密集防守，需耐心破局"),
    ("防守反击", "防守反击"): (0.85, "双方谨慎，进球偏少"),
    ("均衡", "均衡"): (1.0, "战术均衡，比分由实力与细节决定"),
}

_DIM_WEIGHTS = {
    "basics": 0.14,
    "h2h": 0.09,
    "players": 0.14,
    "tactical": 0.11,
    "external": 0.08,
    "pedigree": 0.12,
    "depth": 0.11,
    "metrics": 0.11,
    "schedule": 0.09,
    "market": 0.07,
}


def _motivation(fixture: Fixture, home: Team, away: Team) -> tuple[str, list[str], float, float]:
    points: list[str] = []
    home_m, away_m = 1.0, 1.0

    if fixture.is_knockout:
        points.append(f"{fixture.stage}生死战，双方战意拉满，任何失误都可能出局。")
        home_m = away_m = 1.04
    elif fixture.group:
        standings = group_standings_prediction()
        grp = standings.get(fixture.group, [])
        if home.code in grp[:2] and away.code in grp[2:]:
            points.append(f"{home.name_zh} 出线形势乐观，可能轮换留力；{away.name_zh} 必须全力抢分。")
            home_m, away_m = 0.97, 1.06
        elif away.code in grp[:2] and home.code in grp[2:]:
            points.append(f"{away.name_zh} 出线热门，{home.name_zh} 本场为出线关键战，战意更足。")
            home_m, away_m = 1.06, 0.97
        elif home.code in grp[2:] and away.code in grp[2:]:
            points.append("双方均处于出线边缘，平局对双方可能均可接受，战意复杂。")
        else:
            points.append("小组赛初期，双方试探为主，战意正常。")

    if fixture.stage == "决赛":
        points.append("世界杯决赛，心理压力大，领先方倾向保守，进球效率或低于预期。")
        home_m *= 0.96
        away_m *= 0.96

    summary = "；".join(points[:2]) if points else "常规赛事战意"
    return summary, points, home_m, away_m


def _analyze_team_basics(
    home: Team, away: Team,
    home_prof: TeamProfile, away_prof: TeamProfile,
    fixture: Fixture,
    group_ctx: GroupContext | None,
) -> tuple[DimensionBlock, float, float]:
    hf, h_def = form_multiplier(home_prof.form)
    af, a_def = form_multiplier(away_prof.form)
    h_ha = home_away_multiplier(home_prof.form, True)
    a_ha = home_away_multiplier(away_prof.form, False)
    mot_summary, mot_points, h_mot, a_mot = _motivation(fixture, home, away)

    h_gm = group_intensity_multiplier(group_ctx, True)
    a_gm = group_intensity_multiplier(group_ctx, False)

    h_form, a_form = home_prof.form, away_prof.form
    points = [
        f"{home.name_zh} 近{h_form.played}场 {h_form.wins}胜{h_form.draws}平{h_form.losses}负，"
        f"场均进 {h_form.goals_per_game} 失 {h_form.conceded_per_game}，赛程密度{h_form.schedule_density}。",
        f"{away.name_zh} 近{a_form.played}场 {a_form.wins}胜{a_form.draws}平{a_form.losses}负，"
        f"场均进 {a_form.goals_per_game} 失 {a_form.conceded_per_game}。",
        f"主客场：{home.name_zh} 主场胜率 {h_form.home_win_rate*100:.0f}%，"
        f"{away.name_zh} 客场胜率 {a_form.away_win_rate*100:.0f}%。",
        *mot_points,
    ]
    if group_ctx:
        points.extend([
            f"{group_ctx.group}组第{group_ctx.match_round}轮：{group_ctx.scenario}（战意{group_ctx.intensity}）。",
            f"{home.name_zh}（预测第{group_ctx.home_standing}）：{group_ctx.home_needs}。",
            f"{away.name_zh}（预测第{group_ctx.away_standing}）：{group_ctx.away_needs}。",
        ])
        mot_summary = f"{group_ctx.group}组{group_ctx.scenario}"

    return (
        DimensionBlock("球队基础", mot_summary, points, "近期状态、主客场与出线形势已纳入 xG 修正"),
        hf * h_ha * h_mot * h_gm / h_def,
        af * a_ha * a_mot * a_gm / a_def,
    )


def _analyze_h2h(home: Team, away: Team, h2h: HeadToHeadRecord) -> tuple[DimensionBlock, float, float]:
    draw_rate = h2h.draws / h2h.meetings if h2h.meetings else 0.2
    points = [
        f"近 {h2h.meetings} 次交手：主方 {h2h.home_wins}胜 {h2h.draws}平 {h2h.away_wins}负。",
        f"场均比分约 {h2h.avg_home_goals:.1f}-{h2h.avg_away_goals:.1f}，场均总进球 {h2h.avg_total_goals:.1f}。",
        f"平局概率约 {draw_rate*100:.0f}%。",
    ]
    if h2h.recent_scores:
        points.append(f"近年比分：{'、'.join(h2h.recent_scores)}。")
    if h2h.note:
        points.append(h2h.note)

    total_adj = h2h.avg_total_goals / 2.5
    h_share = h2h.avg_home_goals / max(h2h.avg_total_goals, 0.1)
    psych = ""
    if h2h.home_wins >= h2h.meetings * 0.6:
        psych = "主队历史心理优势"
    elif h2h.away_wins >= h2h.meetings * 0.6:
        psych = "客队历史心理优势"

    return (
        DimensionBlock("历史交锋", h2h.note or f"交手 {h2h.meetings} 次", points, psych or "历史规律已微调进球预期"),
        0.7 + 0.6 * total_adj * h_share,
        0.7 + 0.6 * total_adj * (1 - h_share),
    )


def _analyze_players(
    home: Team, away: Team,
    home_prof: TeamProfile, away_prof: TeamProfile,
) -> tuple[DimensionBlock, float, float]:
    h_atk, h_def, h_notes = injury_impact(home_prof.key_players)
    a_atk, a_def, a_notes = injury_impact(away_prof.key_players)
    points = []
    for p in home_prof.key_players:
        status = "可出战" if p.available else "缺阵"
        points.append(f"{home.name_zh} {p.name}（{p.role}）{status}，状态 {p.form:.0f}/100")
    for p in away_prof.key_players:
        status = "可出战" if p.available else "缺阵"
        points.append(f"{away.name_zh} {p.name}（{p.role}）{status}，状态 {p.form:.0f}/100")
    points.extend(h_notes)
    points.extend(a_notes)
    unavailable = sum(1 for p in home_prof.key_players + away_prof.key_players if not p.available)
    summary = f"共 {unavailable} 名核心球员缺阵" if unavailable else "核心阵容基本齐整"
    return (
        DimensionBlock("核心人员", summary, points, "伤停与状态已修正攻防系数"),
        h_atk / h_def,
        a_atk / a_def,
    )


def _tactical_clash_multiplier(style_a: str, style_b: str) -> tuple[float, str]:
    if (style_a, style_b) in STYLE_CLASH:
        return STYLE_CLASH[(style_a, style_b)]
    rev = (style_b, style_a)
    if rev in STYLE_CLASH:
        mult, note = STYLE_CLASH[rev]
        return mult, note
    return 1.0, "战术风格常规碰撞"


def _analyze_tactical(
    home: Team, away: Team,
    home_prof: TeamProfile, away_prof: TeamProfile,
) -> tuple[DimensionBlock, float, float]:
    ht, at = home_prof.tactics, away_prof.tactics
    clash_mult, clash_note = _tactical_clash_multiplier(ht.style, at.style)
    points = [
        f"{home.name_zh}：{ht.style}，控球 {ht.possession:.0f}%，场均射门 {ht.shots_per_game:.1f}，射正率 {ht.shot_accuracy:.0f}%。",
        f"{away.name_zh}：{at.style}，控球 {at.possession:.0f}%，反击效率 {at.counter_attack:.0f}/100。",
        f"风格碰撞：{clash_note}。",
        f"定位球：主队进攻 {ht.set_piece_attack:.0f}/防守 {ht.set_piece_defense:.0f}，"
        f"客队进攻 {at.set_piece_attack:.0f}/防守 {at.set_piece_defense:.0f}。",
        f"教练调整：{home.name_zh} {ht.coach_adjust}；{away.name_zh} {at.coach_adjust}。",
    ]
    if ht.style == "控球进攻" and at.style in ("密集防守", "防守反击"):
        xg_h, xg_a = 1.02 * clash_mult, 0.98 / clash_mult
    elif at.style == "控球进攻" and ht.style in ("密集防守", "防守反击"):
        xg_h, xg_a = 0.98 / clash_mult, 1.02 * clash_mult
    else:
        xg_h = xg_a = clash_mult ** 0.5
    return DimensionBlock("战术风格", f"{ht.style} vs {at.style}", points, clash_note), xg_h, xg_a


def _analyze_external(
    home: Team, away: Team, fixture: Fixture, venue: VenueMeta,
) -> tuple[tuple[DimensionBlock, float, float], float]:
    points = [
        f"场地：{fixture.venue}（{venue.city}），海拔 {venue.altitude_m}m。",
        f"6月气候：{venue.june_climate}。",
        f"裁判尺度参考：{venue.referee_tendency}。",
        venue.external_note,
    ]
    xg_h, xg_a = 1.0, 1.0
    conf_adj = 0.0

    if venue.altitude_m >= 1500 and away.code not in ("MEX", "ECU", "COL"):
        xg_a *= 0.95
        points.append("高海拔对客队体能不利，下半场失球风险上升。")
    climate = venue.june_climate
    if "雨" in climate or "湿" in climate:
        xg_h *= 0.97
        xg_a *= 0.97
        conf_adj -= 0.03
        points.append("湿滑场地增加偶然性，技术发挥与传球精度可能下降。")
    if "炎热" in climate or "高温" in climate:
        xg_h *= 0.98
        xg_a *= 0.98
        points.append("高温下比赛节奏放缓，体能分配影响下半场比分。")
    if venue.referee_tendency == "偏严":
        points.append("偏严判罚或增加定位球/点球，改变比分概率上升。")
        conf_adj -= 0.02
    elif venue.referee_tendency == "偏松":
        points.append("偏松尺度有利于防守方，进球可能偏少。")

    usa_cities = {"洛杉矶", "旧金山", "西雅图", "达拉斯", "休斯顿", "堪萨斯城",
                  "亚特兰大", "迈阿密", "纽约", "费城", "波士顿", "纽约/新泽西"}
    if home.is_host:
        if (home.code == "MEX" and venue.city in {"墨西哥城", "瓜达拉哈拉", "蒙特雷"}) or \
           (home.code == "CAN" and venue.city in {"多伦多", "温哥华"}) or \
           (home.code == "USA" and venue.city in usa_cities):
            points.append(f"{home.name_zh} 东道主主场，球迷与气候适应加成显著。")

    return (
        DimensionBlock("外部影响", venue.external_note[:40], points, "场地与气候因素已纳入"),
        xg_h, xg_a,
    ), conf_adj


def _analyze_pedigree(
    home: Team, away: Team, fixture: Fixture,
) -> tuple[DimensionBlock, float, float]:
    hp = get_pedigree(home.code, home.rating)
    ap = get_pedigree(away.code, away.rating)
    h_atk, h_def = pedigree_multiplier(hp, fixture.is_knockout)
    a_atk, a_def = pedigree_multiplier(ap, fixture.is_knockout)

    points = [
        f"{home.name_zh}：{hp.world_cup_titles}次世界杯冠军，近届{hp.recent_wc_best}，"
        f"大赛抗压 {hp.big_game_rating:.0f}/100，点球胜率 {hp.penalty_win_rate*100:.0f}%。",
        f"教练 {hp.coach_name}（{hp.coach_tournament_record}）。",
        f"{away.name_zh}：{ap.world_cup_titles}次世界杯冠军，近届{ap.recent_wc_best}，"
        f"大赛抗压 {ap.big_game_rating:.0f}/100。",
        f"教练 {ap.coach_name}（{ap.coach_tournament_record}）。",
        hp.mentality_note,
        ap.mentality_note,
    ]
    summary = f"{home.name_zh} 大赛底蕴 {'强' if hp.big_game_rating >= 85 else '中'} vs {away.name_zh} {'强' if ap.big_game_rating >= 85 else '中'}"
    if fixture.is_knockout:
        summary += "；淘汰赛经验权重提升"

    return (
        DimensionBlock("大赛底蕴", summary, points, "大赛心理与教练履历已纳入"),
        h_atk / h_def,
        a_atk / a_def,
    )


def _analyze_depth(
    home: Team, away: Team,
    h_load: ScheduleLoad, a_load: ScheduleLoad,
) -> tuple[DimensionBlock, float, float]:
    hd = get_squad_depth(home.code, home.rating)
    ad = get_squad_depth(away.code, away.rating)
    h_atk, h_def = depth_multiplier(hd, h_load.matches_played)
    a_atk, a_def = depth_multiplier(ad, a_load.matches_played)

    points = [
        f"{home.name_zh}：板凳深度 {hd.depth_score:.0f}/100，轮换弹性{hd.rotation_flex}，"
        f"平均年龄 {hd.avg_squad_age:.1f}岁。{hd.note}",
        f"{away.name_zh}：板凳深度 {ad.depth_score:.0f}/100，轮换弹性{ad.rotation_flex}，"
        f"平均年龄 {ad.avg_squad_age:.1f}岁。{ad.note}",
    ]
    if hd.rotation_flex == "低" and h_load.matches_played >= 3:
        points.append(f"{home.name_zh} 深度不足+已赛{h_load.matches_played}场，后半程下滑风险。")
    if ad.rotation_flex == "低" and a_load.matches_played >= 3:
        points.append(f"{away.name_zh} 深度不足+已赛{a_load.matches_played}场，后半程下滑风险。")

    diff = hd.depth_score - ad.depth_score
    summary = "主队阵容厚度占优" if diff >= 8 else ("客队阵容厚度占优" if diff <= -8 else "双方阵容深度接近")
    return DimensionBlock("阵容深度", summary, points, "深度与轮换能力已纳入"), h_atk / h_def, a_atk / a_def


def _analyze_advanced(home: Team, away: Team) -> tuple[DimensionBlock, float, float, float]:
    hm = get_advanced_metrics(home.code, home.rating, home.attack, home.defense)
    am = get_advanced_metrics(away.code, away.rating, away.attack, away.defense)
    h_atk, h_def, h_conf = metrics_multiplier(hm)
    a_atk, a_def, a_conf = metrics_multiplier(am)

    points = [
        f"{home.name_zh}：零封率 {hm.clean_sheet_rate:.0f}%，75分钟后进球占比 {hm.late_goal_rate:.0f}%，"
        f"先丢球逆转率 {hm.comeback_win_rate:.0f}%，定位球进球占比 {hm.set_piece_goal_share:.0f}%。",
        f"场均黄牌 {hm.cards_per_game:.1f}，进球效率偏差 {hm.xg_overperformance:.2f}。{hm.note}",
        f"{away.name_zh}：零封率 {am.clean_sheet_rate:.0f}%，75分钟后进球占比 {am.late_goal_rate:.0f}%，"
        f"先丢球逆转率 {am.comeback_win_rate:.0f}%。场均黄牌 {am.cards_per_game:.1f}。{am.note}",
    ]
    if hm.late_goal_rate >= 32 or am.late_goal_rate >= 32:
        points.append("双方或一方有「晚进球」属性，下半场比分变数大。")
    if hm.cards_per_game >= 2.5 or am.cards_per_game >= 2.5:
        points.append("犯规偏多，红牌改变比分是重要尾部风险。")

    return (
        DimensionBlock("进阶数据", "零封/晚进球/逆转/纪律等综合指标", points, "高阶数据修正终结效率"),
        h_atk / h_def, a_atk / a_def, h_conf + a_conf,
    )


def _analyze_schedule(
    home: Team, away: Team, fixture: Fixture,
) -> tuple[DimensionBlock, float, float, ScheduleLoad, ScheduleLoad]:
    h_load = get_schedule_load(home.code, fixture)
    a_load = get_schedule_load(away.code, fixture)
    h_atk, h_def = schedule_multiplier(h_load)
    a_atk, a_def = schedule_multiplier(a_load)

    points = [
        f"{home.name_zh}：已赛 {h_load.matches_played} 场，休息 {h_load.rest_days} 天，"
        f"旅行负荷 {h_load.travel_zones} 级，累积疲劳{h_load.cumulative_fatigue}。{h_load.note}",
        f"{away.name_zh}：已赛 {a_load.matches_played} 场，休息 {a_load.rest_days} 天，"
        f"旅行负荷 {a_load.travel_zones} 级，累积疲劳{a_load.cumulative_fatigue}。{a_load.note}",
    ]
    if h_load.cumulative_fatigue == "高" or a_load.cumulative_fatigue == "高":
        points.append("2026 世界杯横跨北美三国，长途旅行+短休息是隐形变量。")

    fatigue_rank = {"低": 0, "中": 1, "高": 2}
    h_fat = fatigue_rank.get(h_load.cumulative_fatigue, 1)
    a_fat = fatigue_rank.get(a_load.cumulative_fatigue, 1)
    worse = home.name_zh if h_fat > a_fat else away.name_zh
    summary = f"赛程负荷：{h_load.cumulative_fatigue}/{a_load.cumulative_fatigue}"
    if h_fat != a_fat:
        summary += f"，{worse}更疲劳"

    return (
        DimensionBlock("赛程负荷", summary, points, "休息与旅行消耗已纳入"),
        h_atk / h_def, a_atk / a_def, h_load, a_load,
    )


def _analyze_market(home: Team, away: Team) -> tuple[DimensionBlock, float, float, MarketConsensus]:
    mkt = compute_market_consensus(home, away)
    h_mult = market_multiplier(mkt, "home")
    a_mult = market_multiplier(mkt, "away")
    points = [
        f"市场隐含概率：主胜 {mkt.home_win_implied*100:.1f}% / 平局 {mkt.draw_implied*100:.1f}% / "
        f"客胜 {mkt.away_win_implied*100:.1f}%。",
        f"参考赔率（十进制）：主 {mkt.home_odds} / 平 {mkt.draw_odds} / 客 {mkt.away_odds}。",
        f"市场热门：{mkt.favorite}（{mkt.margin*100:.1f}%）。",
        mkt.note,
        "市场反映全球资金流向与信息聚合，可与模型交叉验证。",
    ]
    return (
        DimensionBlock("市场共识", mkt.favorite, points, "市场隐含概率作校验参考"),
        h_mult, a_mult, mkt,
    )


def _build_analyst_verdict(
    home: Team, away: Team, fixture: Fixture,
    xg_h_adj: float, xg_a_adj: float,
    win_p: float, draw_p: float, loss_p: float,
    conf_adj: float,
    h2h: HeadToHeadRecord,
    home_prof: TeamProfile,
    away_prof: TeamProfile,
    market: MarketConsensus | None = None,
) -> AnalystVerdict:
    rating_diff = home.rating - away.rating
    max_p = max(win_p, draw_p, loss_p)
    risk_tags: list[str] = []
    caveats: list[str] = [
        "足球比赛存在极强偶然性，模型输出为概率而非确定性结论。",
        "红牌、点球误判、临场战术突变等不可完全量化。",
    ]

    if max_p < 0.45:
        risk_tags.append("势均力敌")
    if draw_p >= 0.28:
        risk_tags.append("平局陷阱")
    if abs(rating_diff) >= 15 and max_p < 0.55:
        risk_tags.append("冷门预警")
    if abs(xg_h_adj - xg_a_adj) >= 0.12:
        risk_tags.append("多维分歧")
    if h2h.avg_total_goals <= 2.0:
        risk_tags.append("偏小比分历史")
    elif h2h.avg_total_goals >= 3.2:
        risk_tags.append("大比分可能")

    h_injured = sum(1 for p in home_prof.key_players if not p.available)
    a_injured = sum(1 for p in away_prof.key_players if not p.available)
    if h_injured >= 2 or a_injured >= 2:
        risk_tags.append("伤病扰动")

    if fixture.is_knockout:
        risk_tags.append("淘汰赛加时/点球")
        caveats.append("淘汰赛平局后加时与点球大战进一步增加随机性。")

    market_note = ""
    effective_conf_adj = conf_adj
    if market:
        div, direction, _div_points = model_market_divergence(market, win_p, draw_p, loss_p)
        market_note = direction
        if div >= 0.12:
            risk_tags.append("市场分歧")
            effective_conf_adj -= 0.02
            caveats.append(f"模型与市场分歧 {div*100:.0f}pp：{direction}，建议降低仓位或观望。")
        elif div <= 0.05:
            risk_tags.append("市场一致")

    effective_conf = max_p + effective_conf_adj
    if effective_conf >= 0.58:
        conf_level = "高"
    elif effective_conf >= 0.48:
        conf_level = "中"
    else:
        conf_level = "低"

    if win_p >= draw_p and win_p >= loss_p:
        pick = f"倾向主胜（{win_p*100:.1f}%）"
        if rating_diff < -8:
            pick += "，但客队纸面更强需防冷"
    elif loss_p >= win_p:
        pick = f"倾向客胜（{loss_p*100:.1f}%）"
        if rating_diff > 8:
            pick += "，主队主场或有反弹"
    else:
        pick = f"倾向平局（{draw_p*100:.1f}%）"

    summary = (
        f"综合十维分析，{pick}。实力差 {rating_diff:+.0f} 分，"
        f"十维修正后主队 xG 系数 {xg_h_adj:.2f}、客队 {xg_a_adj:.2f}。"
    )
    if market_note:
        summary += f" {market_note}。"

    return AnalystVerdict(
        summary=summary,
        risk_tags=risk_tags or ["常规风险"],
        confidence_level=conf_level,
        recommendation=f"参考置信度：{conf_level}。{pick}。",
        caveats=caveats,
    )


def _weighted_combine(factors: dict[str, float]) -> float:
    total_w = sum(_DIM_WEIGHTS.get(k, 0.1) for k in factors)
    log_sum = 0.0
    for k, v in factors.items():
        w = _DIM_WEIGHTS.get(k, 0.1) / total_w
        log_sum += w * math.log(max(v, 0.01))
    return math.exp(log_sum)


def analyze_match_dimensions(
    home: Team, away: Team, fixture: Fixture,
) -> MatchDimensionAnalysis:
    home_prof = get_team_profile(home.code, home.rating, home.attack, home.defense)
    away_prof = get_team_profile(away.code, away.rating, away.attack, away.defense)
    venue = get_venue_meta(fixture.city)

    h2h = get_head_to_head(home.code, away.code) or estimate_h2h(
        home.code, away.code, home.rating, away.rating
    )

    group_ctx = get_group_context(fixture, home, away)
    market_blk, mkt_h, mkt_a, market = _analyze_market(home, away)

    basics, b_h, b_a = _analyze_team_basics(home, away, home_prof, away_prof, fixture, group_ctx)
    h2h_blk, h_h, h_a = _analyze_h2h(home, away, h2h)
    players, p_h, p_a = _analyze_players(home, away, home_prof, away_prof)
    tactical, t_h, t_a = _analyze_tactical(home, away, home_prof, away_prof)
    (external, e_h, e_a), conf_adj = _analyze_external(home, away, fixture, venue)
    pedigree, ped_h, ped_a = _analyze_pedigree(home, away, fixture)
    schedule, sch_h, sch_a, h_load, a_load = _analyze_schedule(home, away, fixture)
    depth, dep_h, dep_a = _analyze_depth(home, away, h_load, a_load)
    advanced, adv_h, adv_a, adv_conf = _analyze_advanced(home, away)
    conf_adj += adv_conf

    xg_home = _weighted_combine({
        "basics": b_h, "h2h": h_h, "players": p_h, "tactical": t_h,
        "external": e_h, "pedigree": ped_h, "depth": dep_h, "metrics": adv_h,
        "schedule": sch_h, "market": mkt_h,
    })
    xg_away = _weighted_combine({
        "basics": b_a, "h2h": h_a, "players": p_a, "tactical": t_a,
        "external": e_a, "pedigree": ped_a, "depth": dep_a, "metrics": adv_a,
        "schedule": sch_a, "market": mkt_a,
    })

    xg_home = max(0.72, min(1.28, xg_home))
    xg_away = max(0.72, min(1.28, xg_away))

    # 占位 verdict，win_p 由引擎二次填充；此处用临时值
    verdict = _build_analyst_verdict(
        home, away, fixture, xg_home, xg_away,
        0.4, 0.25, 0.35, conf_adj, h2h, home_prof, away_prof, market,
    )

    return MatchDimensionAnalysis(
        team_basics=basics,
        head_to_head=h2h_blk,
        key_players=players,
        tactical=tactical,
        external=external,
        tournament_pedigree=pedigree,
        squad_depth=depth,
        advanced_metrics=advanced,
        schedule_load=schedule,
        market_consensus=market_blk,
        analyst_verdict=verdict,
        market=market,
        xg_home_adj=xg_home,
        xg_away_adj=xg_away,
        confidence_adj=conf_adj,
    )


def finalize_verdict(
    dim: MatchDimensionAnalysis,
    home: Team, away: Team, fixture: Fixture,
    win_p: float, draw_p: float, loss_p: float,
) -> None:
    """引擎算出概率后，更新分析师研判。"""
    h2h = get_head_to_head(home.code, away.code) or estimate_h2h(
        home.code, away.code, home.rating, away.rating
    )
    home_prof = get_team_profile(home.code, home.rating, home.attack, home.defense)
    away_prof = get_team_profile(away.code, away.rating, away.attack, away.defense)
    verdict = _build_analyst_verdict(
        home, away, fixture, dim.xg_home_adj, dim.xg_away_adj,
        win_p, draw_p, loss_p, dim.confidence_adj, h2h, home_prof, away_prof, dim.market,
    )
    dim.analyst_verdict = verdict
    # 市场分歧可能调整了 conf_adj
    if dim.market:
        div, _, _ = model_market_divergence(dim.market, win_p, draw_p, loss_p)
        if div >= 0.12:
            dim.confidence_adj -= 0.02


# 向后兼容
analyze_five_dimensions = analyze_match_dimensions


def dimensions_to_dict(d: MatchDimensionAnalysis) -> dict:
    def block(b: DimensionBlock) -> dict:
        return {"title": b.title, "summary": b.summary, "points": b.points, "impact": b.impact}

    v = d.analyst_verdict
    return {
        "team_basics": block(d.team_basics),
        "head_to_head": block(d.head_to_head),
        "key_players": block(d.key_players),
        "tactical": block(d.tactical),
        "external": block(d.external),
        "tournament_pedigree": block(d.tournament_pedigree),
        "squad_depth": block(d.squad_depth),
        "advanced_metrics": block(d.advanced_metrics),
        "schedule_load": block(d.schedule_load),
        "market_consensus": block(d.market_consensus),
        "market_implied": {
            "home_win": d.market.home_win_implied if d.market else 0,
            "draw": d.market.draw_implied if d.market else 0,
            "away_win": d.market.away_win_implied if d.market else 0,
            "odds": {
                "home": d.market.home_odds if d.market else 0,
                "draw": d.market.draw_odds if d.market else 0,
                "away": d.market.away_odds if d.market else 0,
            },
        } if d.market else {},
        "analyst_verdict": {
            "summary": v.summary,
            "risk_tags": v.risk_tags,
            "confidence_level": v.confidence_level,
            "recommendation": v.recommendation,
            "caveats": v.caveats,
        },
        "xg_adjustments": {"home": round(d.xg_home_adj, 3), "away": round(d.xg_away_adj, 3)},
        "confidence_adj": round(d.confidence_adj, 3),
        "dimension_count": 10,
    }
