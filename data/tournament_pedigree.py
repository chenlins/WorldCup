"""大赛底蕴：世界杯履历、淘汰赛抗压、点球大战、教练大赛经验。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TournamentPedigree:
    code: str
    world_cup_titles: int
    recent_wc_best: str  # 近三届最好成绩
    knockout_matches: int  # 近十年大赛淘汰赛场次
    penalty_win_rate: float  # 点球大战胜率 0-1
    big_game_rating: float  # 大赛抗压综合 0-100
    coach_name: str
    coach_tournament_record: str  # 教练大赛履历简述
    mentality_note: str


def _ped(
    code: str,
    titles: int,
    recent: str,
    ko: int,
    pen: float,
    big: float,
    coach: str,
    record: str,
    note: str,
) -> TournamentPedigree:
    return TournamentPedigree(code, titles, recent, ko, pen, big, coach, record, note)


_PEDIGREE: dict[str, TournamentPedigree] = {
    "ARG": _ped("ARG", 3, "冠军(2022)", 18, 0.75, 96, "斯卡洛尼", "2022世界杯冠军教练", "卫冕冠军，淘汰赛心态成熟"),
    "FRA": _ped("FRA", 2, "亚军(2022)", 20, 0.60, 94, "德尚", "2018冠军+2022亚军", "大赛决赛常客，关键战稳定"),
    "BRA": _ped("BRA", 5, "8强(2022)", 16, 0.55, 88, "安切洛蒂", "欧冠+大赛经验丰富", "五冠底蕴但近年淘汰赛屡受挫"),
    "GER": _ped("GER", 4, "小组赛出局(2022)", 14, 0.70, 82, "纳格尔斯曼", "大赛改革期", "2022耻辱出局后重建，大赛经验仍在"),
    "ESP": _ped("ESP", 1, "4强(2022)", 15, 0.65, 86, "德拉富恩特", "欧洲杯冠军教练", "新生代崛起，大赛抗压待检验"),
    "ENG": _ped("ENG", 1, "亚军(2020欧洲杯)", 12, 0.50, 84, "索斯盖特", "连续大赛四强", "点球心魔仍存，大赛走更远"),
    "POR": _ped("POR", 0, "8强(2022)", 10, 0.45, 80, "马丁内斯", "世界杯+欧洲杯执教", "C罗最后一届，战意与波动并存"),
    "NED": _ped("NED", 0, "8强(2022)", 11, 0.40, 78, "科曼", "大赛老牌教练", "无冠魔咒，淘汰赛易翻车"),
    "BEL": _ped("BEL", 0, "小组赛(2022)", 8, 0.35, 72, "多梅尼科", "黄金一代末期", "黄金一代谢幕，大赛最后一舞"),
    "CRO": _ped("CRO", 0, "季军(2022)", 14, 0.80, 90, "达利奇", "连续大赛四强", "淘汰赛加时点球经验丰富"),
    "URU": _ped("URU", 2, "小组赛(2022)", 10, 0.55, 82, "贝尔萨", "南美大赛经验", "硬朗风格，淘汰赛难啃"),
    "COL": _ped("COL", 0, "小组赛(2018)", 6, 0.50, 74, "内斯托", "重建期", "大赛经验略逊"),
    "MEX": _ped("MEX", 0, "16强(2018)", 7, 0.30, 70, "奥索里奥", "东道主压力", "16强魔咒，主场期望压力大"),
    "USA": _ped("USA", 0, "16强(2002)", 4, 0.25, 68, "波切蒂诺", "大赛执教初期", "东道主+波切蒂诺，大赛磨合期"),
    "JPN": _ped("JPN", 0, "16强(2022)", 5, 0.50, 76, "森保一", "2022击败德西", "亚洲标杆，淘汰赛突破待完成"),
    "MAR": _ped("MAR", 0, "4强(2022)", 8, 0.60, 85, "雷格拉吉", "2022历史性四强", "世界杯黑马经验，防守韧性极强"),
    "SEN": _ped("SEN", 0, "16强(2002)", 3, 0.40, 70, "西塞", "非洲大赛经验", "非洲杯冠军底蕴"),
    "KOR": _ped("KOR", 0, "16强(2022)", 4, 0.45, 72, "洪明甫", "2022击败葡萄牙", "有爆冷大赛先例"),
    "CAN": _ped("CAN", 0, "小组赛(2022)", 2, 0.20, 62, "马尔基什", "东道主", "大赛经验有限，主场或激发潜能"),
}


def get_pedigree(code: str, rating: float) -> TournamentPedigree:
    if code in _PEDIGREE:
        return _PEDIGREE[code]
    ko = int(2 + rating / 15)
    big = min(75, 50 + rating * 0.25)
    return TournamentPedigree(
        code, 0, "小组赛", ko, 0.40, big,
        "未知", "大赛经验有限",
        "首次或极少世界杯深度经历，淘汰赛抗压存疑",
    )


def pedigree_multiplier(p: TournamentPedigree, is_knockout: bool) -> tuple[float, float]:
    """大赛底蕴对 (进攻信心, 防守稳定性) 的修正。"""
    base = p.big_game_rating / 85.0
    atk = 0.92 + base * 0.10
    defn = 1.0 / (0.92 + base * 0.08)
    if is_knockout:
        atk *= 0.98 + p.penalty_win_rate * 0.04
        defn *= 0.98 + (p.knockout_matches / 20) * 0.06
    return max(0.90, min(1.10, atk)), max(0.90, min(1.10, defn))
