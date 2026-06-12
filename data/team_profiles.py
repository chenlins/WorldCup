"""球队扩展档案：近期状态、主客场差异、战术风格、核心球员。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RecentForm:
    """近 10 场竞技状态（含俱乐部+国家队综合参考）。"""

    played: int
    wins: int
    draws: int
    losses: int
    goals_per_game: float
    conceded_per_game: float
    home_win_rate: float  # 0-1，主场细分
    away_win_rate: float
    schedule_density: str  # 低 / 中 / 高 — 多线作战疲劳度


@dataclass(frozen=True)
class TacticalProfile:
    """战术风格基础数据。"""

    style: str  # 控球进攻 / 高位压迫 / 防守反击 / 密集防守 / 均衡
    possession: float  # 场均控球率 %
    shots_per_game: float
    shot_accuracy: float  # 射正率 %
    pass_accuracy: float
    set_piece_attack: float  # 定位球进攻 0-100
    set_piece_defense: float
    counter_attack: float  # 反击效率 0-100
    coach_adjust: str  # 教练临场调整倾向


@dataclass(frozen=True)
class KeyPlayer:
    name: str
    role: str  # 前锋 / 中场 / 后卫 / 门将
    importance: float  # 0-1 核心程度
    form: float  # 0-100 近期状态
    available: bool  # 是否可出战
    note: str = ""


@dataclass(frozen=True)
class TeamProfile:
    code: str
    form: RecentForm
    tactics: TacticalProfile
    key_players: tuple[KeyPlayer, ...]


def _form(
    w: int,
    d: int,
    l: int,
    gf: float,
    ga: float,
    home_wr: float,
    away_wr: float,
    density: str = "中",
) -> RecentForm:
    n = w + d + l
    return RecentForm(n, w, d, l, gf, ga, home_wr, away_wr, density)


def _tac(
    style: str,
    pos: float,
    shots: float,
    acc: float,
    pas: float,
    spa: float,
    spd: float,
    ctr: float,
    coach: str,
) -> TacticalProfile:
    return TacticalProfile(style, pos, shots, acc, pas, spa, spd, ctr, coach)


def _default_profile(code: str, rating: float, attack: float, defense: float) -> TeamProfile:
    """按实力评分生成合理默认档案。"""
    wr = rating / 100.0
    w = int(10 * wr * 0.55 + 2)
    w = min(w, 8)
    l = max(10 - w - 2, 1)
    d = 10 - w - l
    gf = 1.2 + attack / 45.0
    ga = 1.8 - defense / 55.0
    style = "控球进攻" if attack > 82 else ("防守反击" if attack < 72 else "均衡")
    pos = 45 + attack * 0.35
    return TeamProfile(
        code,
        _form(w, d, l, round(gf, 2), round(ga, 2), wr + 0.12, wr - 0.08),
        _tac(style, pos, 12 + attack / 10, 32 + attack / 5, 78 + rating / 20,
             55 + attack / 8, 50 + defense / 8, 50 + (attack - 70) / 2, "稳健型"),
        (KeyPlayer("主力核心", "中场", 0.7, rating - 5, True, "无重大伤停报告"),),
    )


# 重点球队精细化档案（基于 2024-2026 赛前公开信息综合）
_PROFILES: dict[str, TeamProfile] = {
    "ARG": TeamProfile(
        "ARG",
        _form(7, 2, 1, 2.1, 0.7, 0.82, 0.65, "中"),
        _tac("控球进攻", 58, 14.2, 38, 86, 72, 68, 55, "保守型，领先时控节奏"),
        (
            KeyPlayer("梅西", "前锋", 0.95, 88, True, "大赛经验丰富，定位球威胁大"),
            KeyPlayer("阿尔瓦雷斯", "前锋", 0.82, 85, True),
            KeyPlayer("恩佐·费尔南德斯", "中场", 0.80, 82, True),
            KeyPlayer("罗梅罗", "后卫", 0.75, 80, True),
        ),
    ),
    "FRA": TeamProfile(
        "FRA",
        _form(6, 2, 2, 2.0, 1.1, 0.78, 0.58, "高"),
        _tac("高位压迫", 52, 15.8, 36, 84, 70, 72, 78, "进攻型，擅长换人改变节奏"),
        (
            KeyPlayer("姆巴佩", "前锋", 0.95, 90, True, "反击核心，速度改变战局"),
            KeyPlayer("格列兹曼", "中场", 0.85, 83, True),
            KeyPlayer("楚阿梅尼", "中场", 0.78, 80, True),
            KeyPlayer("萨利巴", "后卫", 0.80, 86, True),
        ),
    ),
    "BRA": TeamProfile(
        "BRA",
        _form(5, 3, 2, 1.8, 1.0, 0.75, 0.55, "中"),
        _tac("控球进攻", 62, 16.5, 35, 87, 68, 65, 62, "技术流，边路渗透为主"),
        (
            KeyPlayer("维尼修斯", "前锋", 0.92, 88, True),
            KeyPlayer("罗德里戈", "前锋", 0.80, 82, True),
            KeyPlayer("帕奎塔", "中场", 0.78, 75, False, "伤病存疑，中场组织受影响"),
            KeyPlayer("马尔基尼奥斯", "后卫", 0.82, 84, True),
        ),
    ),
    "ENG": TeamProfile(
        "ENG",
        _form(6, 2, 2, 2.2, 0.9, 0.80, 0.52, "高"),
        _tac("高位压迫", 55, 15.2, 37, 85, 75, 70, 65, "身体对抗强，定位球威胁大"),
        (
            KeyPlayer("凯恩", "前锋", 0.93, 87, True),
            KeyPlayer("贝林厄姆", "中场", 0.88, 86, True),
            KeyPlayer("赖斯", "中场", 0.85, 84, True),
            KeyPlayer("斯通斯", "后卫", 0.78, 80, False, "轻伤，防线稳定性存疑"),
        ),
    ),
    "ESP": TeamProfile(
        "ESP",
        _form(7, 2, 1, 2.4, 0.8, 0.85, 0.62, "中"),
        _tac("控球进攻", 68, 17.0, 40, 91, 65, 72, 58, "传控压迫，控球消耗对手"),
        (
            KeyPlayer("亚马尔", "前锋", 0.88, 90, True, "状态火热，边路突破核心"),
            KeyPlayer("佩德里", "中场", 0.85, 85, True),
            KeyPlayer("罗德里", "中场", 0.90, 88, False, "长期伤缺，中场控制力大减"),
            KeyPlayer("拉波尔特", "后卫", 0.75, 78, True),
        ),
    ),
    "GER": TeamProfile(
        "GER",
        _form(5, 3, 2, 2.0, 1.2, 0.72, 0.50, "中"),
        _tac("高位压迫", 58, 16.0, 36, 86, 68, 68, 70, "高压逼抢，攻防转换快"),
        (
            KeyPlayer("维尔茨", "中场", 0.88, 87, True),
            KeyPlayer("穆西亚拉", "中场", 0.85, 85, True),
            KeyPlayer("哈弗茨", "前锋", 0.78, 80, True),
            KeyPlayer("吕迪格", "后卫", 0.80, 82, True),
        ),
    ),
    "MEX": TeamProfile(
        "MEX",
        _form(4, 3, 3, 1.5, 1.3, 0.70, 0.38, "低"),
        _tac("防守反击", 48, 11.5, 30, 80, 62, 65, 72, "主场气势足，反击犀利"),
        (
            KeyPlayer("希门尼斯", "前锋", 0.82, 78, True),
            KeyPlayer("阿尔瓦雷斯", "中场", 0.75, 76, True),
            KeyPlayer("桑切斯", "门将", 0.78, 80, True),
        ),
    ),
    "USA": TeamProfile(
        "USA",
        _form(5, 2, 3, 1.7, 1.2, 0.68, 0.42, "低"),
        _tac("高位压迫", 50, 13.0, 33, 82, 70, 68, 68, "体能充沛，主场作战积极"),
        (
            KeyPlayer("普利西奇", "前锋", 0.88, 84, True),
            KeyPlayer("麦肯尼", "中场", 0.78, 80, True),
            KeyPlayer("特纳", "门将", 0.80, 82, True),
        ),
    ),
    "JPN": TeamProfile(
        "JPN",
        _form(6, 2, 2, 1.9, 0.9, 0.65, 0.55, "中"),
        _tac("高位压迫", 54, 14.5, 38, 84, 60, 72, 75, "团队配合细腻，转换极快"),
        (
            KeyPlayer("久保建英", "前锋", 0.85, 86, True),
            KeyPlayer("三笘薰", "前锋", 0.82, 84, True),
            KeyPlayer("远藤航", "中场", 0.78, 80, True),
        ),
    ),
    "MAR": TeamProfile(
        "MAR",
        _form(5, 4, 1, 1.6, 0.8, 0.62, 0.48, "中"),
        _tac("防守反击", 42, 10.8, 32, 79, 58, 78, 80, "密集防守，反击效率高"),
        (
            KeyPlayer("阿什拉夫", "后卫", 0.82, 85, True),
            KeyPlayer("齐耶赫", "中场", 0.78, 76, True),
            KeyPlayer("恩内斯里", "门将", 0.80, 82, True),
        ),
    ),
}


def get_team_profile(code: str, rating: float = 70, attack: float = 70, defense: float = 70) -> TeamProfile:
    if code in _PROFILES:
        return _PROFILES[code]
    return _default_profile(code, rating, attack, defense)


def form_multiplier(form: RecentForm) -> tuple[float, float]:
    """根据近期状态返回 (进攻系数, 防守系数)。"""
    if form.played <= 0:
        return 1.0, 1.0
    win_rate = form.wins / form.played
    atk = 0.85 + form.goals_per_game / 3.0 + win_rate * 0.15
    defn = 1.15 - form.conceded_per_game / 3.0 - win_rate * 0.10
    if form.schedule_density == "高":
        atk *= 0.96
        defn *= 1.04
    return max(0.82, min(1.18, atk)), max(0.82, min(1.18, defn))


def home_away_multiplier(form: RecentForm, is_home: bool) -> float:
    wr = form.home_win_rate if is_home else form.away_win_rate
    return 0.88 + wr * 0.24


def injury_impact(players: tuple[KeyPlayer, ...]) -> tuple[float, float, list[str]]:
    """伤停对攻防的影响及说明。"""
    atk_penalty = 1.0
    def_penalty = 1.0
    notes: list[str] = []
    for p in players:
        if p.available:
            if p.form >= 85 and p.importance >= 0.85:
                boost = 1.0 + (p.form - 80) / 200
                if p.role in ("前锋", "中场"):
                    atk_penalty *= boost
                notes.append(f"{p.name} 状态火热（{p.form:.0f}），{p.note or '可改变比分走势'}")
            continue
        impact = p.importance
        if p.role == "前锋":
            atk_penalty *= 1.0 - impact * 0.35
            notes.append(f"核心前锋 {p.name} 缺阵，进球效率预计下降 {impact*35:.0f}%")
        elif p.role == "中场":
            atk_penalty *= 1.0 - impact * 0.22
            def_penalty *= 1.0 + impact * 0.12
            notes.append(f"中场核心 {p.name} 缺阵（{p.note or '组织与防守均受影响'}）")
        elif p.role == "后卫":
            def_penalty *= 1.0 + impact * 0.28
            notes.append(f"主力后卫 {p.name} 缺阵，失球概率上升")
        elif p.role == "门将":
            def_penalty *= 1.0 + impact * 0.20
            notes.append(f"主力门将 {p.name} 缺阵，门前稳定性下降")
    return atk_penalty, def_penalty, notes
