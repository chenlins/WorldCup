"""小组赛出线形势：轮次、积分需求、净胜球压力。"""

from __future__ import annotations

from dataclasses import dataclass

from data.fixtures import FIXTURES, Fixture
from data.teams import Team, group_standings_prediction


@dataclass(frozen=True)
class GroupContext:
    group: str
    match_round: int  # 第1/2/3轮
    home_standing: int  # 预测排名 1-4
    away_standing: int
    home_needs: str
    away_needs: str
    scenario: str
    intensity: str  # 低 / 中 / 高 / 极高


def _group_round(fixture: Fixture, team_code: str) -> int:
    n = 0
    for f in FIXTURES:
        if f.id >= fixture.id:
            break
        if f.group == fixture.group and (f.home == team_code or f.away == team_code):
            n += 1
    return n + 1


def get_group_context(fixture: Fixture, home: Team, away: Team) -> GroupContext | None:
    if not fixture.group:
        return None

    standings = group_standings_prediction()
    grp = standings.get(fixture.group, [])
    if home.code not in grp or away.code not in grp:
        return None

    h_rank = grp.index(home.code) + 1
    a_rank = grp.index(away.code) + 1
    rnd = _group_round(fixture, home.code)

    def _needs(rank: int, rnd: int) -> str:
        if rnd == 1:
            return "开门红，建立积分优势"
        if rnd == 2:
            if rank <= 2:
                return "取胜可基本锁定出线"
            return "必须抢分，避免末轮被动"
        # 第3轮
        if rank == 1:
            return "争小组第一，淘汰赛对阵更优"
        if rank == 2:
            return "确保出线，可能需看其他场次"
        return "出线生死战，仅胜才有希望"

    h_needs = _needs(h_rank, rnd)
    a_needs = _needs(a_rank, rnd)

    if rnd == 3 and h_rank >= 3 and a_rank >= 3:
        scenario = "末轮弱队对决，胜者仍有出线希望，平局或双输"
        intensity = "极高"
    elif rnd == 3 and (h_rank <= 2) != (a_rank <= 2):
        scenario = "出线区 vs 追赶者，战意不对称"
        intensity = "高"
    elif rnd == 1:
        scenario = "小组赛开局，双方试探与磨合"
        intensity = "中"
    else:
        scenario = "中期抢分战，结果影响末轮形势"
        intensity = "高" if h_rank >= 3 or a_rank >= 3 else "中"

    return GroupContext(
        fixture.group, rnd, h_rank, a_rank,
        h_needs, a_needs, scenario, intensity,
    )


def group_intensity_multiplier(ctx: GroupContext | None, is_home: bool) -> float:
    if not ctx:
        return 1.0
    rank = ctx.home_standing if is_home else ctx.away_standing
    mult = 1.0
    if ctx.intensity == "极高":
        mult = 1.05 if rank >= 3 else 1.02
    elif ctx.intensity == "高" and rank >= 3:
        mult = 1.04
    # 出线热门末轮可能留力
    if ctx.match_round == 3 and rank == 1 and ctx.intensity != "极高":
        mult *= 0.98
    return mult
