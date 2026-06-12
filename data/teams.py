"""2026 世界杯参赛球队实力数据（基于 FIFA 排名、近年大赛表现综合评估）。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Team:
    code: str
    name_en: str
    name_zh: str
    rating: float  # 综合实力 0-100
    attack: float  # 进攻 0-100
    defense: float  # 防守 0-100
    fifa_rank: int
    is_host: bool = False
    continent: str = ""


TEAMS: dict[str, Team] = {
    "ARG": Team("ARG", "Argentina", "阿根廷", 96, 94, 90, 1),
    "FRA": Team("FRA", "France", "法国", 95, 93, 91, 2),
    "BRA": Team("BRA", "Brazil", "巴西", 94, 92, 88, 3),
    "ENG": Team("ENG", "England", "英格兰", 92, 90, 89, 4),
    "ESP": Team("ESP", "Spain", "西班牙", 91, 89, 90, 5),
    "POR": Team("POR", "Portugal", "葡萄牙", 90, 88, 87, 6),
    "GER": Team("GER", "Germany", "德国", 89, 88, 86, 7),
    "NED": Team("NED", "Netherlands", "荷兰", 88, 87, 85, 8),
    "BEL": Team("BEL", "Belgium", "比利时", 87, 86, 84, 9),
    "URU": Team("URU", "Uruguay", "乌拉圭", 84, 82, 83, 10),
    "COL": Team("COL", "Colombia", "哥伦比亚", 83, 82, 81, 11),
    "CRO": Team("CRO", "Croatia", "克罗地亚", 83, 81, 82, 12),
    "MEX": Team("MEX", "Mexico", "墨西哥", 82, 80, 81, 14, is_host=True, continent="CONCACAF"),
    "USA": Team("USA", "United States", "美国", 81, 79, 80, 15, is_host=True, continent="CONCACAF"),
    "SUI": Team("SUI", "Switzerland", "瑞士", 80, 78, 81, 16),
    "JPN": Team("JPN", "Japan", "日本", 79, 78, 77, 17),
    "MAR": Team("MAR", "Morocco", "摩洛哥", 79, 77, 80, 13),
    "SEN": Team("SEN", "Senegal", "塞内加尔", 78, 77, 76, 18),
    "AUT": Team("AUT", "Austria", "奥地利", 77, 76, 75, 19),
    "NOR": Team("NOR", "Norway", "挪威", 77, 78, 74, 20),
    "ECU": Team("ECU", "Ecuador", "厄瓜多尔", 76, 75, 76, 21),
    "TUR": Team("TUR", "Türkiye", "土耳其", 75, 76, 73, 22),
    "CAN": Team("CAN", "Canada", "加拿大", 74, 73, 74, 23, is_host=True, continent="CONCACAF"),
    "KOR": Team("KOR", "Korea Republic", "韩国", 74, 73, 74, 24),
    "AUS": Team("AUS", "Australia", "澳大利亚", 73, 72, 73, 25),
    "PAR": Team("PAR", "Paraguay", "巴拉圭", 72, 71, 72, 26),
    "EGY": Team("EGY", "Egypt", "埃及", 72, 71, 72, 27),
    "IRN": Team("IRN", "Iran", "伊朗", 71, 70, 72, 28),
    "ALG": Team("ALG", "Algeria", "阿尔及利亚", 71, 70, 71, 29),
    "CIV": Team("CIV", "Côte d'Ivoire", "科特迪瓦", 70, 70, 69, 30),
    "SCO": Team("SCO", "Scotland", "苏格兰", 70, 69, 70, 31),
    "SWE": Team("SWE", "Sweden", "瑞典", 69, 68, 70, 32),
    "CZE": Team("CZE", "Czechia", "捷克", 69, 68, 69, 33),
    "GHA": Team("GHA", "Ghana", "加纳", 68, 68, 67, 34),
    "UZB": Team("UZB", "Uzbekistan", "乌兹别克斯坦", 67, 66, 67, 35),
    "RSA": Team("RSA", "South Africa", "南非", 66, 65, 66, 36),
    "BIH": Team("BIH", "Bosnia and Herzegovina", "波黑", 66, 65, 66, 37),
    "JOR": Team("JOR", "Jordan", "约旦", 65, 64, 65, 38),
    "IRQ": Team("IRQ", "Iraq", "伊拉克", 64, 63, 64, 39),
    "TUN": Team("TUN", "Tunisia", "突尼斯", 64, 63, 64, 40),
    "PAN": Team("PAN", "Panama", "巴拿马", 63, 62, 63, 41),
    "KSA": Team("KSA", "Saudi Arabia", "沙特", 63, 62, 63, 42),
    "CPV": Team("CPV", "Cabo Verde", "佛得角", 62, 61, 62, 43),
    "COD": Team("COD", "Congo DR", "刚果金", 62, 62, 61, 44),
    "NZL": Team("NZL", "New Zealand", "新西兰", 61, 60, 61, 45),
    "QAT": Team("QAT", "Qatar", "卡塔尔", 60, 59, 60, 46),
    "CUW": Team("CUW", "Curaçao", "库拉索", 58, 57, 58, 47),
    "HAI": Team("HAI", "Haiti", "海地", 56, 55, 56, 48),
}

GROUPS: dict[str, list[str]] = {
    "A": ["MEX", "RSA", "KOR", "CZE"],
    "B": ["CAN", "SUI", "QAT", "BIH"],
    "C": ["BRA", "MAR", "HAI", "SCO"],
    "D": ["USA", "PAR", "AUS", "TUR"],
    "E": ["GER", "CUW", "CIV", "ECU"],
    "F": ["NED", "JPN", "TUN", "SWE"],
    "G": ["BEL", "EGY", "IRN", "NZL"],
    "H": ["ESP", "CPV", "KSA", "URU"],
    "I": ["FRA", "SEN", "NOR", "IRQ"],
    "J": ["ARG", "ALG", "AUT", "JOR"],
    "K": ["POR", "UZB", "COL", "COD"],
    "L": ["ENG", "CRO", "GHA", "PAN"],
}


def get_team(code: str) -> Team:
    if code not in TEAMS:
        raise KeyError(f"Unknown team code: {code}")
    return TEAMS[code]


def group_standings_prediction() -> dict[str, list[str]]:
    """预测各组排名：按实力排序返回 [冠军, 亚军, 季军, 第四]。"""
    standings: dict[str, list[str]] = {}
    for group, codes in GROUPS.items():
        sorted_codes = sorted(codes, key=lambda c: TEAMS[c].rating, reverse=True)
        standings[group] = sorted_codes
    return standings


def expected_team_from_slot(slot: str) -> tuple[str, str, bool]:
    """
    从淘汰赛席位描述解析预期球队。
    返回 (code, 中文显示名, 是否不确定)。
    """
    standings = group_standings_prediction()

    slot_map = {
        "A组冠军": standings["A"][0],
        "A组亚军": standings["A"][1],
        "B组冠军": standings["B"][0],
        "B组亚军": standings["B"][1],
        "C组冠军": standings["C"][0],
        "C组亚军": standings["C"][1],
        "D组冠军": standings["D"][0],
        "D组亚军": standings["D"][1],
        "E组冠军": standings["E"][0],
        "E组亚军": standings["E"][1],
        "F组冠军": standings["F"][0],
        "F组亚军": standings["F"][1],
        "G组冠军": standings["G"][0],
        "G组亚军": standings["G"][1],
        "H组冠军": standings["H"][0],
        "H组亚军": standings["H"][1],
        "I组冠军": standings["I"][0],
        "I组亚军": standings["I"][1],
        "J组冠军": standings["J"][0],
        "J组亚军": standings["J"][1],
        "K组冠军": standings["K"][0],
        "K组亚军": standings["K"][1],
        "L组冠军": standings["L"][0],
        "L组亚军": standings["L"][1],
    }

    if slot in slot_map:
        code = slot_map[slot]
        return code, TEAMS[code].name_zh, False

    # 最佳第三名 — 取候选组中实力最强的第三名
    if "最佳第三名" in slot or "3rd" in slot.lower():
        groups_mentioned = []
        for g in "ABCDEFGHIJKL":
            if f"{g}组" in slot or f"Group {g}" in slot:
                groups_mentioned.append(g)
        if groups_mentioned:
            third_places = [standings[g][2] for g in groups_mentioned]
            best = max(third_places, key=lambda c: TEAMS[c].rating)
            return best, TEAMS[best].name_zh + "（预测最佳第三）", True
        # 默认取全部第三名中最强者
        all_third = [standings[g][2] for g in standings]
        best = max(all_third, key=lambda c: TEAMS[c].rating)
        return best, TEAMS[best].name_zh + "（预测最佳第三）", True

    return "TBD", slot, True
