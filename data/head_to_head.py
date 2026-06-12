"""历史交锋数据：近 3-5 次交手记录与规律。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HeadToHeadRecord:
    home_code: str
    away_code: str
    meetings: int
    home_wins: int
    draws: int
    away_wins: int
    avg_total_goals: float
    avg_home_goals: float
    avg_away_goals: float
    recent_scores: tuple[str, ...]  # e.g. ("2-1", "1-1", "0-0")
    note: str = ""


def _h2h(
    h: str,
    a: str,
    meetings: int,
    hw: int,
    d: int,
    aw: int,
    avg_h: float,
    avg_a: float,
    scores: tuple[str, ...],
    note: str = "",
) -> HeadToHeadRecord:
    return HeadToHeadRecord(
        h, a, meetings, hw, d, aw,
        round(avg_h + avg_a, 2),
        avg_h, avg_a, scores, note,
    )


# 键为排序后的 (code_a, code_b) 元组
_H2H_DB: dict[tuple[str, str], HeadToHeadRecord] = {}


def _add(rec: HeadToHeadRecord) -> None:
    key = tuple(sorted([rec.home_code, rec.away_code]))
    _H2H_DB[key] = rec


# 经典对决与常见交手
_add(_h2h("ARG", "BRA", 5, 2, 1, 2, 1.4, 1.2, ("1-0", "0-0", "2-1", "1-1", "0-1"), "南美德比，小比分居多"))
_add(_h2h("ARG", "FRA", 4, 1, 1, 2, 1.5, 1.75, ("3-3", "2-0", "0-2", "4-3"), "对攻激烈，大比分频发"))
_add(_h2h("ENG", "GER", 5, 1, 2, 2, 1.2, 1.4, ("2-0", "1-1", "0-1", "1-2", "0-0"), "势均力敌，心理博弈明显"))
_add(_h2h("ESP", "GER", 4, 2, 1, 1, 1.5, 1.0, ("1-0", "2-1", "0-1", "1-1"), "技术 vs 压迫，控球方略优"))
_add(_h2h("POR", "ESP", 4, 0, 2, 2, 0.75, 1.5, ("0-0", "0-1", "1-2", "1-1"), "伊比利亚德比，客队心理优势"))
_add(_h2h("MEX", "USA", 5, 2, 2, 1, 1.4, 1.0, ("2-1", "1-1", "3-0", "0-0", "1-0"), "中北美宿敌，主场因素显著"))
_add(_h2h("MEX", "ARG", 3, 0, 1, 2, 0.67, 2.0, ("0-2", "1-1", "0-3"), "阿根廷历史占优"))
_add(_h2h("JPN", "KOR", 5, 2, 2, 1, 1.2, 1.0, ("2-1", "1-1", "0-0", "2-2", "1-0"), "东亚德比，平局概率高"))
_add(_h2h("MAR", "ESP", 3, 0, 1, 2, 0.67, 1.67, ("0-2", "2-2", "0-3"), "摩洛哥世界杯曾爆冷西班牙"))
_add(_h2h("URU", "BRA", 4, 1, 1, 2, 1.0, 1.5, ("0-2", "1-1", "0-1", "2-1"), "乌拉圭防守硬朗"))
_add(_h2h("NED", "ARG", 4, 1, 0, 3, 1.0, 2.25, ("2-2", "0-2", "1-3", "0-1"), "阿根廷近年占优"))
_add(_h2h("FRA", "ENG", 4, 2, 1, 1, 1.5, 1.0, ("2-1", "1-1", "2-0", "1-2"), "欧洲杯级别对抗"))
_add(_h2h("BEL", "FRA", 3, 0, 1, 2, 0.67, 2.0, ("1-2", "2-3", "0-1"), "法国进攻效率更高"))
_add(_h2h("CRO", "ARG", 3, 0, 0, 3, 0.67, 2.0, ("0-3", "0-2", "1-3"), "阿根廷大赛心理优势"))
_add(_h2h("SEN", "NED", 2, 0, 1, 1, 1.0, 2.0, ("0-2", "2-2"), "荷兰实力占优"))
_add(_h2h("KOR", "GER", 2, 1, 0, 1, 2.0, 1.5, ("2-0", "1-2"), "韩国曾爆冷德国"))


def get_head_to_head(code_a: str, code_b: str) -> HeadToHeadRecord | None:
    key = tuple(sorted([code_a, code_b]))
    rec = _H2H_DB.get(key)
    if not rec:
        return None
    # 若查询方与记录主客相反，交换统计
    if rec.home_code == code_a:
        return rec
    return HeadToHeadRecord(
        code_a, code_b,
        rec.meetings, rec.away_wins, rec.draws, rec.home_wins,
        rec.avg_total_goals, rec.avg_away_goals, rec.avg_home_goals,
        rec.recent_scores, rec.note,
    )


def estimate_h2h(code_a: str, code_b: str, rating_a: float, rating_b: float) -> HeadToHeadRecord:
    """无直接记录时，按实力差估算交锋规律。"""
    diff = rating_a - rating_b
    if abs(diff) < 5:
        hw, d, aw = 2, 2, 1
        note = "无直接近年大赛交手，双方实力接近，预计胶着"
    elif diff > 0:
        hw, d, aw = 3, 1, 1
        note = "无直接近年大赛交手，纸面实力主队略优"
    else:
        hw, d, aw = 1, 1, 3
        note = "无直接近年大赛交手，纸面实力客队略优"
    avg_total = 2.2 + abs(diff) / 80
    avg_h = avg_total * (0.52 + diff / 200)
    avg_a = avg_total - avg_h
    return HeadToHeadRecord(
        code_a, code_b, 5, hw, d, aw,
        round(avg_total, 2), round(avg_h, 2), round(avg_a, 2),
        (), note,
    )
