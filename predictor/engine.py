"""世界杯赛事预测引擎：泊松进球模型 + 实力评分 + 分析师解读。"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from data.fixtures import FIXTURE_BY_ID, Fixture, fixtures_by_date
from data.team_profiles import get_team_profile
from data.teams import TEAMS, Team, expected_team_from_slot, get_team, group_standings_prediction
from predictor.dimensions import (
    MatchDimensionAnalysis,
    analyze_match_dimensions,
    dimensions_to_dict,
    finalize_verdict,
)
from predictor.score_refinement import refinement_to_dict, refine_score_prediction
from predictor.types import ScoreLine

# 固定种子保证预测可复现
random.seed(2026)


@dataclass
class MatchPrediction:
    match_id: int
    date: str
    time_et: str
    stage: str
    group: str | None
    venue: str
    city: str
    home_name: str
    away_name: str
    home_code: str
    away_code: str
    home_display: str
    away_display: str
    predicted_score: str
    predicted_home_goals: float
    predicted_away_goals: float
    win_prob: float
    draw_prob: float
    loss_prob: float
    outcome: str  # 主胜 / 平局 / 客胜
    confidence: float
    top_scores: list[ScoreLine]
    analysis: list[str]
    tactical: str
    key_factors: list[str]
    is_knockout: bool
    uncertainty_note: str = ""
    dimensions: dict = field(default_factory=dict)
    extra_mode: str = "none"
    extended_analysis: dict | None = None
    base_prediction: dict | None = None
    score_refinement: dict | None = None


STAGE_XG_FACTOR = {
    "小组赛": 1.0,
    "32强": 0.92,
    "16强": 0.88,
    "8强": 0.85,
    "半决赛": 0.82,
    "三四名决赛": 0.90,
    "决赛": 0.80,
}

# 淘汰赛晋级预测缓存
_bracket_cache: dict[int, tuple[str, str]] = {}


def _poisson(lam: float, k: int) -> float:
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return math.exp(-lam) * (lam**k) / math.factorial(k)


def _resolve_team(fixture: Fixture, side: str) -> tuple[str, str, str, bool]:
    """返回 (code, name_zh, display, uncertain)。"""
    raw = fixture.home if side == "home" else fixture.away
    is_slot = fixture.home_is_slot if side == "home" else fixture.away_is_slot

    if not is_slot and raw in TEAMS:
        t = get_team(raw)
        return raw, t.name_zh, t.name_zh, False

    # Mxx胜者/负者（须在通用席位解析之前）
    if raw.startswith("M") and ("胜者" in raw or "负者" in raw):
        mid = int(raw[1:raw.index("胜") if "胜" in raw else raw.index("负")])
        is_winner = "胜者" in raw
        h_code, a_code = _predict_bracket_match(mid)
        pred = _predict_match_internal(FIXTURE_BY_ID[mid], h_code, a_code)
        winner = pred.home_code if pred.win_prob >= pred.loss_prob else pred.away_code
        loser = pred.away_code if winner == pred.home_code else pred.home_code
        code = winner if is_winner else loser
        if code in TEAMS:
            t = get_team(code)
            return code, t.name_zh, f"{t.name_zh}（{raw}）", True
        return "TBD", raw, raw, True

    if is_slot:
        code, name, uncertain = expected_team_from_slot(raw)
        if code != "TBD":
            return code, get_team(code).name_zh, f"{name}（{raw}）", uncertain
        return "TBD", raw, raw, True

    return "TBD", raw, raw, True


def _host_bonus(team: Team, city: str) -> float:
    if not team.is_host:
        return 0.0
    mexico_cities = {"墨西哥城", "瓜达拉哈拉", "蒙特雷"}
    canada_cities = {"多伦多", "温哥华"}
    usa_hint = team.code == "USA"
    if team.code == "MEX" and city in mexico_cities:
        return 0.12
    if team.code == "CAN" and city in canada_cities:
        return 0.10
    if usa_hint:
        return 0.08
    return 0.0


def _expected_goals(
    home: Team,
    away: Team,
    stage: str,
    city: str,
    dim: MatchDimensionAnalysis | None = None,
) -> tuple[float, float]:
    factor = STAGE_XG_FACTOR.get(stage, 1.0)
    base = 2.55 * factor

    home_attack = home.attack / 50.0
    away_defense = (100 - away.defense) / 50.0 + 0.5
    away_attack = away.attack / 50.0
    home_defense = (100 - home.defense) / 50.0 + 0.5

    rating_diff = (home.rating - away.rating) / 100.0
    home_bonus = _host_bonus(home, city) + 0.06  # 通用主场优势
    away_penalty = -0.04

    lam_home = base * 0.52 * home_attack * away_defense * (1 + rating_diff + home_bonus)
    lam_away = base * 0.48 * away_attack * home_defense * (1 - rating_diff + away_penalty)

    if dim:
        lam_home *= dim.xg_home_adj
        lam_away *= dim.xg_away_adj

    lam_home = max(0.35, min(3.2, lam_home))
    lam_away = max(0.30, min(2.8, lam_away))
    return lam_home, lam_away


def _score_distribution(lam_h: float, lam_a: float, knockout: bool) -> list[ScoreLine]:
    scores: list[ScoreLine] = []
    max_g = 5 if not knockout else 4
    for h in range(max_g + 1):
        for a in range(max_g + 1):
            p = _poisson(lam_h, h) * _poisson(lam_a, a)
            if knockout and h == a:
                # 淘汰赛加时/点球：平分概率给双方
                p *= 0.55
            scores.append(ScoreLine(h, a, p))
    total = sum(s.probability for s in scores) or 1.0
    for s in scores:
        s.probability /= total
    scores.sort(key=lambda x: x.probability, reverse=True)
    return scores


def _outcome_probs(scores: list[ScoreLine], knockout: bool) -> tuple[float, float, float]:
    win = draw = loss = 0.0
    for s in scores:
        if s.home > s.away:
            win += s.probability
        elif s.home < s.away:
            loss += s.probability
        else:
            if knockout:
                win += s.probability * 0.5
                loss += s.probability * 0.5
            else:
                draw += s.probability
    total = win + draw + loss or 1.0
    return win / total, draw / total, loss / total


def _outcome_type_score(
    h: int, a: int, knockout: bool,
    win_p: float, draw_p: float, loss_p: float,
) -> str:
    if h > a:
        return "主胜"
    if h < a:
        return "客胜"
    if knockout:
        return "主胜" if win_p >= loss_p else "客胜"
    return "平局"


def _normalize_probs(win: float, draw: float, loss: float) -> tuple[float, float, float]:
    total = win + draw + loss or 1.0
    return win / total, draw / total, loss / total


def _prediction_snapshot(
    lam_h: float,
    lam_a: float,
    win_p: float,
    draw_p: float,
    loss_p: float,
    scores: list[ScoreLine],
    outcome: str,
    confidence: float,
) -> dict:
    best = scores[0]
    return {
        "predicted_score": f"{best.home}-{best.away}",
        "predicted_home_goals": round(lam_h, 2),
        "predicted_away_goals": round(lam_a, 2),
        "win_prob": round(win_p, 4),
        "draw_prob": round(draw_p, 4),
        "loss_prob": round(loss_p, 4),
        "outcome": outcome,
        "confidence": round(confidence, 4),
    }


def _build_analysis(
    home: Team,
    away: Team,
    fixture: Fixture,
    lam_h: float,
    lam_a: float,
    win_p: float,
    draw_p: float,
    loss_p: float,
    top: list[ScoreLine],
    uncertain: bool,
    dim: MatchDimensionAnalysis | None = None,
) -> tuple[list[str], str, list[str], str]:
    reasons: list[str] = []
    factors: list[str] = []

    if home.rating - away.rating >= 12:
        reasons.append(f"{home.name_zh} 整体实力明显占优（评分 {home.rating:.0f} vs {away.rating:.0f}），控球与压制能力更强。")
        factors.append("实力差距显著")
    elif away.rating - home.rating >= 12:
        reasons.append(f"{away.name_zh} 纸面实力领先，预计采取主动进攻节奏。")
        factors.append("客队实力碾压")
    else:
        reasons.append(f"双方实力接近（{home.rating:.0f} vs {away.rating:.0f}），比赛悬念较大，细节将决定走向。")
        factors.append("势均力敌")

    if home.is_host or away.is_host:
        host = home if home.is_host else away
        reasons.append(f"{host.name_zh} 作为东道主，在 {fixture.city} 拥有球迷与气候适应优势。")
        factors.append("东道主加成")

    if fixture.group:
        standings = group_standings_prediction()
        grp = standings[fixture.group]
        if home.code in grp[:2] and away.code in grp[2:]:
            reasons.append(f"{home.name_zh} 被预测为 {fixture.group} 组出线热门，{away.name_zh} 需全力抢分。")
        elif away.code in grp[:2] and home.code in grp[2:]:
            reasons.append(f"{away.name_zh} 出线形势更乐观，{home.name_zh} 本场必须积极进攻。")

    if fixture.stage != "小组赛":
        reasons.append(f"{fixture.stage}淘汰赛节奏更谨慎，领先方可能收缩防守，进球效率低于小组赛。")
        factors.append("淘汰赛战术保守")

    top3 = top[:3]
    score_text = "、".join(f"{s.home}-{s.away}({s.probability*100:.1f}%)" for s in top3)
    reasons.append(f"泊松模型最可能比分：{score_text}。")

    if draw_p >= 0.28 and not fixture.is_knockout:
        reasons.append(f"平局概率 {draw_p*100:.1f}% 偏高，双方可能各取所需或互有顾忌。")

    outcome = "主胜" if win_p >= draw_p and win_p >= loss_p else ("平局" if draw_p >= loss_p else "客胜")
    if outcome == "主胜":
        reasons.append(f"综合胜率：主胜 {win_p*100:.1f}% > 平局 {draw_p*100:.1f}% > 客胜 {loss_p*100:.1f}%。")
    elif outcome == "平局":
        reasons.append(f"综合胜率：平局 {draw_p*100:.1f}% 为最高概率结果。")
    else:
        reasons.append(f"综合胜率：客胜 {loss_p*100:.1f}% 为最高概率结果。")

    if dim:
        ht = get_team_profile(home.code, home.rating, home.attack, home.defense).tactics
        at = get_team_profile(away.code, away.rating, away.attack, away.defense).tactics
        tactical = (
            f"{home.name_zh}（{ht.style}）预期 xG {lam_h:.2f}，十维修正系数 {dim.xg_home_adj:.2f}；"
            f"{away.name_zh}（{at.style}）预期 xG {lam_a:.2f}，修正系数 {dim.xg_away_adj:.2f}。"
            f"风格碰撞：{dim.tactical.summary}。"
        )
        if dim.key_players.summary:
            reasons.append(f"人员层面：{dim.key_players.summary}。")
        if dim.external.summary:
            factors.append("外部因素")
        verdict = dim.analyst_verdict
        if verdict.risk_tags:
            factors.extend(t for t in verdict.risk_tags[:2] if t not in factors)
        reasons.append(verdict.summary)
    else:
        tactical = (
            f"{home.name_zh} 预期 xG {lam_h:.2f}，倾向{'高位压迫' if home.attack > away.defense else '稳守反击'}；"
            f"{away.name_zh} 预期 xG {lam_a:.2f}，"
            f"{'客场采取防反' if away.rating < home.rating else '有能力在中场争夺主导权'}。"
        )

    uncertainty = ""
    if uncertain:
        uncertainty = "本场对阵含淘汰赛席位占位，球队为基于小组预测的推断对阵，实际晋级后可能调整。"
        reasons.append(uncertainty)

    return reasons, tactical, factors, uncertainty


def _predict_match_internal(
    fixture: Fixture,
    home_code: str | None = None,
    away_code: str | None = None,
    extra_mode: str = "none",
) -> MatchPrediction:
    if home_code and away_code:
        home = get_team(home_code)
        away = get_team(away_code)
        home_disp = home.name_zh
        away_disp = away.name_zh
        uncertain = False
    else:
        hc, hn, hd, hu = _resolve_team(fixture, "home")
        ac, an, ad, au = _resolve_team(fixture, "away")
        home = get_team(hc) if hc in TEAMS else None
        away = get_team(ac) if ac in TEAMS else None
        if not home or not away:
            # fallback neutral
            home = get_team("BRA")
            away = get_team("ARG")
            hd, ad = fixture.home, fixture.away
        home_code, away_code = home.code, away.code
        home_disp, away_disp = hd, ad
        uncertain = hu or au

    dim = analyze_match_dimensions(home, away, fixture)
    lam_h, lam_a = _expected_goals(home, away, fixture.stage, fixture.city, dim)
    scores = _score_distribution(lam_h, lam_a, fixture.is_knockout)
    win_p, draw_p, loss_p = _outcome_probs(scores, fixture.is_knockout)

    finalize_verdict(dim, home, away, fixture, win_p, draw_p, loss_p)

    best = scores[0]
    outcome = "主胜" if win_p >= draw_p and win_p >= loss_p else ("平局" if draw_p >= loss_p else "客胜")
    confidence = max(0.32, min(0.92, max(win_p, draw_p, loss_p) + dim.confidence_adj))

    reasons, tactical, factors, uncertainty = _build_analysis(
        home, away, fixture, lam_h, lam_a, win_p, draw_p, loss_p, scores, uncertain, dim
    )

    for label, block in [
        ("近期状态", dim.team_basics),
        ("历史交锋", dim.head_to_head),
        ("核心伤停", dim.key_players),
        ("战术克制", dim.tactical),
        ("场地因素", dim.external),
        ("大赛底蕴", dim.tournament_pedigree),
        ("阵容深度", dim.squad_depth),
        ("进阶数据", dim.advanced_metrics),
        ("赛程负荷", dim.schedule_load),
        ("市场共识", dim.market_consensus),
    ]:
        if block.impact and label not in factors:
            factors.append(label)

    base_snapshot = None
    extended_dict = None
    mode = (extra_mode or "none").lower()
    if mode in ("human", "same_odds"):
        from predictor.extended_analysis import extended_to_dict, run_extended_analysis

        base_snapshot = _prediction_snapshot(
            lam_h, lam_a, win_p, draw_p, loss_p, scores, outcome, confidence
        )
        ext = run_extended_analysis(
            mode, home, away, fixture, win_p, draw_p, loss_p, lam_h, lam_a, dim.market
        )
        if ext:
            lam_h *= ext.lam_home_factor
            lam_a *= ext.lam_away_factor
            scores = _score_distribution(lam_h, lam_a, fixture.is_knockout)
            win_p, draw_p, loss_p = _outcome_probs(scores, fixture.is_knockout)
            win_p += ext.win_adj
            draw_p += ext.draw_adj
            loss_p += ext.loss_adj
            win_p, draw_p, loss_p = _normalize_probs(win_p, draw_p, loss_p)
            best = scores[0]
            outcome = (
                "主胜" if win_p >= draw_p and win_p >= loss_p
                else ("平局" if draw_p >= loss_p else "客胜")
            )
            confidence = max(
                0.32,
                min(0.92, max(win_p, draw_p, loss_p) + dim.confidence_adj + ext.confidence_delta),
            )
            reasons.insert(0, f"【{ext.mode_label}】{ext.summary}")
            for pt in ext.points[:3]:
                reasons.append(pt)
            for tag in ext.tags:
                if tag not in factors:
                    factors.append(tag)
            extended_dict = extended_to_dict(ext)

    scores, refined_score, lam_h, lam_a, refine_result = refine_score_prediction(
        home, away, fixture, scores, win_p, draw_p, loss_p, lam_h, lam_a, dim.market
    )
    win_p, draw_p, loss_p = _outcome_probs(scores, fixture.is_knockout)
    best = scores[0]
    outcome = _outcome_type_score(best.home, best.away, fixture.is_knockout, win_p, draw_p, loss_p)
    confidence = max(0.32, min(0.92, max(win_p, draw_p, loss_p) + dim.confidence_adj))

    reasons = [r for r in reasons if not r.startswith("泊松模型最可能比分")]
    top3 = scores[:3]
    score_text = "、".join(f"{s.home}-{s.away}({s.probability*100:.1f}%)" for s in top3)
    reasons.append(f"三步定位精选比分：{score_text}。")
    for line in refine_result.reasoning:
        reasons.append(line)
    if refine_result.xg_quality_note:
        reasons.append(f"xG 质量：{refine_result.xg_quality_note}")
    if refine_result.odds_validation:
        reasons.append(refine_result.odds_validation)
    if "三步定位" not in factors:
        factors.append("三步定位")

    if mode == "bookmaker":
        from predictor.bookmaker_score import analyze_bookmaker_optimal_score, bookmaker_to_extended_dict

        model_score = f"{best.home}-{best.away}"
        base_snapshot = _prediction_snapshot(
            lam_h, lam_a, win_p, draw_p, loss_p, scores, outcome, confidence
        )
        bk = analyze_bookmaker_optimal_score(
            home, away, scores, win_p, draw_p, loss_p, dim.market, model_score
        )
        bh, ba = bk.optimal_pick.home, bk.optimal_pick.away
        reasons.insert(0, f"【庄家最优比分】{bk.summary}")
        for pt in bk.points:
            reasons.append(pt)
        for tag in bk.tags:
            if tag not in factors:
                factors.append(tag)
        extended_dict = bookmaker_to_extended_dict(bk)
        best = ScoreLine(bh, ba, bk.optimal_pick.true_prob)
        outcome = _outcome_type_score(bh, ba, fixture.is_knockout, win_p, draw_p, loss_p)

    return MatchPrediction(
        match_id=fixture.id,
        date=fixture.date,
        time_et=fixture.time_et,
        stage=fixture.stage,
        group=fixture.group,
        venue=fixture.venue,
        city=fixture.city,
        home_name=home.name_zh,
        away_name=away.name_zh,
        home_code=home.code,
        away_code=away.code,
        home_display=home_disp,
        away_display=away_disp,
        predicted_score=f"{best.home}-{best.away}",
        predicted_home_goals=round(lam_h, 2),
        predicted_away_goals=round(lam_a, 2),
        win_prob=round(win_p, 4),
        draw_prob=round(draw_p, 4),
        loss_prob=round(loss_p, 4),
        outcome=outcome,
        confidence=round(confidence, 4),
        top_scores=scores[:5],
        analysis=reasons,
        tactical=tactical,
        key_factors=factors,
        is_knockout=fixture.is_knockout,
        uncertainty_note=uncertainty,
        dimensions=dimensions_to_dict(dim),
        extra_mode=mode,
        extended_analysis=extended_dict,
        base_prediction=base_snapshot,
        score_refinement=refinement_to_dict(refine_result),
    )


def _predict_bracket_match(match_id: int) -> tuple[str, str]:
    if match_id in _bracket_cache:
        return _bracket_cache[match_id]
    fixture = FIXTURE_BY_ID[match_id]
    pred = _predict_match_internal(fixture)
    _bracket_cache[match_id] = (pred.home_code, pred.away_code)
    return pred.home_code, pred.away_code


def predict_match(match_id: int, extra_mode: str = "none") -> MatchPrediction:
    fixture = FIXTURE_BY_ID[match_id]
    return _predict_match_internal(fixture, extra_mode=extra_mode)


def predict_by_date(date: str, extra_mode: str = "none") -> dict:
    matches = fixtures_by_date(date)
    if not matches:
        return {
            "date": date,
            "match_count": 0,
            "matches": [],
            "day_summary": "该日期无世界杯赛程。2026 世界杯于 6 月 11 日至 7 月 19 日举行。",
            "featured": None,
        }

    mode = (extra_mode or "none").lower()
    predictions = [_predict_match_internal(m, extra_mode=mode) for m in matches]
    featured = max(predictions, key=lambda p: p.confidence)

    day_parts = []
    if mode == "human":
        day_parts.append("已启用人性分析（热门压力、生死战心态等）修正结果。")
    elif mode == "same_odds":
        day_parts.append("已启用同赔率赛事分析，模型概率已与历届同档位赛果融合。")
    elif mode == "bookmaker":
        day_parts.append("已启用庄家最优比分模式，预测比分已切换为庄家视角最优赛果。")
    stages = {}
    for p in predictions:
        stages.setdefault(p.stage, 0)
        stages[p.stage] += 1
    stage_text = "、".join(f"{k}{v}场" for k, v in stages.items())
    day_parts.append(f"{date} 共 {len(predictions)} 场比赛（{stage_text}）。")

    high_conf = [p for p in predictions if p.confidence >= 0.55]
    if high_conf:
        names = "、".join(f"{p.home_name} vs {p.away_name}" for p in high_conf[:3])
        day_parts.append(f"高置信场次：{names}。")

    upsets = [p for p in predictions if p.confidence < 0.42]
    if upsets:
        day_parts.append(f"存在 {len(upsets)} 场势均力敌或冷门可能较大的对决。")

    market_div = [
        p for p in predictions
        if p.dimensions.get("analyst_verdict", {}).get("risk_tags", [])
        and "市场分歧" in p.dimensions["analyst_verdict"]["risk_tags"]
    ]
    if market_div:
        names = "、".join(f"{p.home_name} vs {p.away_name}" for p in market_div[:2])
        day_parts.append(f"模型与市场分歧场次：{names}。")

    return {
        "date": date,
        "match_count": len(predictions),
        "extra_mode": mode,
        "matches": [prediction_to_dict(p) for p in predictions],
        "day_summary": "".join(day_parts),
        "featured": prediction_to_dict(featured),
    }


def prediction_to_dict(p: MatchPrediction) -> dict:
    return {
        "match_id": p.match_id,
        "date": p.date,
        "time_et": p.time_et,
        "stage": p.stage,
        "group": p.group,
        "venue": p.venue,
        "city": p.city,
        "home_name": p.home_name,
        "away_name": p.away_name,
        "home_code": p.home_code,
        "away_code": p.away_code,
        "home_display": p.home_display,
        "away_display": p.away_display,
        "predicted_score": p.predicted_score,
        "predicted_home_goals": p.predicted_home_goals,
        "predicted_away_goals": p.predicted_away_goals,
        "win_prob": p.win_prob,
        "draw_prob": p.draw_prob,
        "loss_prob": p.loss_prob,
        "outcome": p.outcome,
        "confidence": p.confidence,
        "top_scores": [
            {"home": s.home, "away": s.away, "probability": round(s.probability, 4)}
            for s in p.top_scores
        ],
        "analysis": p.analysis,
        "tactical": p.tactical,
        "key_factors": p.key_factors,
        "is_knockout": p.is_knockout,
        "uncertainty_note": p.uncertainty_note,
        "dimensions": p.dimensions,
        "extra_mode": p.extra_mode,
        "extended_analysis": p.extended_analysis,
        "base_prediction": p.base_prediction,
        "score_refinement": p.score_refinement,
    }
