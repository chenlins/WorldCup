"""赛程负荷：世界杯进程、休息天数、跨区旅行。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from data.fixtures import FIXTURES, Fixture
from data.teams import TEAMS

# 北美赛场分区（跨区旅行增加疲劳）
CITY_ZONE: dict[str, str] = {
    "墨西哥城": "MEX", "瓜达拉哈拉": "MEX", "蒙特雷": "MEX",
    "多伦多": "CAN", "温哥华": "CAN",
    "洛杉矶": "USA_W", "旧金山": "USA_W", "西雅图": "USA_W",
    "达拉斯": "USA_C", "休斯顿": "USA_C", "堪萨斯城": "USA_C",
    "亚特兰大": "USA_E", "迈阿密": "USA_E",
    "纽约": "USA_E", "费城": "USA_E", "波士顿": "USA_E", "纽约/新泽西": "USA_E",
}

ZONE_DISTANCE: dict[tuple[str, str], int] = {
    ("MEX", "CAN"): 3, ("MEX", "USA_W"): 2, ("MEX", "USA_C"): 2, ("MEX", "USA_E"): 3,
    ("CAN", "USA_W"): 3, ("CAN", "USA_C"): 2, ("CAN", "USA_E"): 2,
    ("USA_W", "USA_C"): 2, ("USA_W", "USA_E"): 3, ("USA_C", "USA_E"): 2,
}

STAGE_MATCHES_PLAYED: dict[str, int] = {
    "小组赛": 0,  # 由实际场次计算
    "32强": 3,
    "16强": 4,
    "8强": 5,
    "半决赛": 6,
    "三四名决赛": 7,
    "决赛": 7,
}


@dataclass(frozen=True)
class ScheduleLoad:
    matches_played: int
    rest_days: int
    travel_zones: int  # 跨区等级 0-3
    cumulative_fatigue: str  # 低 / 中 / 高
    last_city: str | None
    note: str


def _parse_date(s: str) -> date:
    y, m, d = s.split("-")
    return date(int(y), int(m), int(d))


def _team_in_fixture(f: Fixture, code: str) -> bool:
    if f.home == code or f.away == code:
        return True
    return False


def _zone_distance(z1: str, z2: str) -> int:
    if z1 == z2:
        return 0
    return ZONE_DISTANCE.get((z1, z2), ZONE_DISTANCE.get((z2, z1), 2))


def get_schedule_load(team_code: str, fixture: Fixture) -> ScheduleLoad:
    if team_code not in TEAMS:
        return ScheduleLoad(0, 7, 0, "低", None, "球队待定")

    current = _parse_date(fixture.date)
    prior: list[Fixture] = []

    for f in FIXTURES:
        if f.id >= fixture.id:
            break
        if _team_in_fixture(f, team_code):
            if not f.home_is_slot and not f.away_is_slot:
                prior.append(f)

    matches_played = len(prior)
    if fixture.is_knockout and matches_played < STAGE_MATCHES_PLAYED.get(fixture.stage, 3):
        matches_played = STAGE_MATCHES_PLAYED.get(fixture.stage, matches_played)

    rest_days = 7
    last_city = None
    if prior:
        last = prior[-1]
        rest_days = (current - _parse_date(last.date)).days
        last_city = last.city

    travel = 0
    if last_city:
        z_prev = CITY_ZONE.get(last_city, "USA_C")
        z_curr = CITY_ZONE.get(fixture.city, "USA_C")
        travel = _zone_distance(z_prev, z_curr)

    fatigue = "低"
    if matches_played >= 5 or rest_days <= 3:
        fatigue = "高"
    elif matches_played >= 3 or rest_days <= 4 or travel >= 2:
        fatigue = "中"

    notes = []
    if rest_days <= 3:
        notes.append(f"仅休息 {rest_days} 天，恢复不足")
    elif rest_days >= 6:
        notes.append(f"休息 {rest_days} 天，体能储备较好")
    if travel >= 2:
        notes.append(f"跨区旅行（{last_city or '?'} → {fixture.city}），时差与旅途消耗大")
    if matches_played >= 4:
        notes.append(f"已赛 {matches_played} 场，世界杯体能累积效应显现")

    return ScheduleLoad(
        matches_played, rest_days, travel, fatigue, last_city,
        "；".join(notes) if notes else "赛程负荷正常",
    )


def schedule_multiplier(load: ScheduleLoad) -> tuple[float, float]:
    atk, defn = 1.0, 1.0
    if load.rest_days <= 3:
        atk *= 0.94
        defn *= 1.05
    elif load.rest_days >= 6:
        atk *= 1.02
    if load.travel_zones >= 2:
        atk *= 0.96
        defn *= 1.03
    if load.cumulative_fatigue == "高":
        atk *= 0.95
        defn *= 1.04
    elif load.cumulative_fatigue == "中":
        atk *= 0.98
        defn *= 1.02
    return max(0.88, min(1.08, atk)), max(0.90, min(1.10, defn))
