"""阵容深度与进阶竞技指标。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SquadDepth:
    depth_score: float  # 板凳深度 0-100
    rotation_flex: str  # 高 / 中 / 低 — 轮换弹性
    avg_squad_age: float
    bench_attack: float  # 替补进攻火力 0-100
    bench_defense: float
    note: str


@dataclass(frozen=True)
class AdvancedMetrics:
    clean_sheet_rate: float  # 零封率 %
    late_goal_rate: float  # 75分钟后进球占比 %
    comeback_win_rate: float  # 先丢球后取胜 %
    set_piece_goal_share: float  # 定位球进球占比 %
    cards_per_game: float  # 场均黄牌
    xg_overperformance: float  # 实际进球/xG 偏离（正=超预期）
    note: str


_DEPTH: dict[str, SquadDepth] = {
    "FRA": SquadDepth(92, "高", 26.8, 85, 88, "姆巴佩缺阵仍有图拉姆+科洛，深度顶级"),
    "ENG": SquadDepth(90, "高", 26.2, 82, 86, "英超国脚云集，轮换不影响战力"),
    "BRA": SquadDepth(88, "高", 27.1, 84, 82, "前场人才济济，后卫线厚度一般"),
    "ESP": SquadDepth(87, "高", 25.4, 80, 84, "青年军体能好但大赛替补经验偏少"),
    "GER": SquadDepth(86, "高", 26.5, 83, 80, "维尔茨/穆西亚拉可轮换多个位置"),
    "ARG": SquadDepth(78, "中", 28.9, 72, 80, "梅西替补后进攻组织下降明显"),
    "POR": SquadDepth(82, "中", 27.8, 78, 76, "B费/莱奥可轮换，中卫深度不足"),
    "NED": SquadDepth(80, "中", 27.2, 76, 78, "锋线选择有限，中场厚度尚可"),
    "BEL": SquadDepth(72, "低", 29.5, 68, 70, "黄金一代老化，替补差距大"),
    "CRO": SquadDepth(70, "低", 29.8, 65, 72, "核心老化，莫德里奇依赖度高"),
    "USA": SquadDepth(75, "中", 25.8, 74, 74, "本土联赛+欧洲混搭，深度中等"),
    "MEX": SquadDepth(68, "低", 28.2, 66, 70, "联赛水平有限，替补实力断层"),
    "JPN": SquadDepth(76, "中", 26.4, 72, 76, "旅欧球员多，战术执行力一致"),
    "MAR": SquadDepth(74, "中", 27.6, 70, 82, "防守型替补多，进攻变化少"),
    "KOR": SquadDepth(70, "低", 27.0, 68, 72, "孙兴慜依赖度高，替补火力不足"),
    "CAN": SquadDepth(65, "低", 26.0, 66, 68, "大赛阵容单薄，东道主或透支主力"),
}

_METRICS: dict[str, AdvancedMetrics] = {
    "ARG": AdvancedMetrics(42, 28, 35, 32, 2.1, 1.08, "大赛关键时刻效率高于数据"),
    "FRA": AdvancedMetrics(38, 32, 40, 28, 2.3, 1.05, "反击效率顶级，体能型球队"),
    "ESP": AdvancedMetrics(45, 25, 30, 22, 1.8, 1.12, "控球创造机会多，终结率近期提升"),
    "ENG": AdvancedMetrics(40, 35, 38, 38, 2.0, 1.04, "定位球威胁联赛顶级，头球得分占比高"),
    "GER": AdvancedMetrics(32, 30, 42, 25, 2.4, 0.98, "高压逼抢导致犯规偏多"),
    "BRA": AdvancedMetrics(35, 27, 33, 26, 2.2, 0.95, "技术流但近期终结效率波动"),
    "MAR": AdvancedMetrics(48, 22, 25, 30, 2.6, 0.92, "密集防守+纪律性强，进球偏少"),
    "CRO": AdvancedMetrics(36, 38, 45, 28, 2.5, 1.06, "老将经验，下半场和加时赛韧性强"),
    "JPN": AdvancedMetrics(35, 30, 35, 24, 1.9, 1.02, "团队足球，跑动距离大"),
    "KOR": AdvancedMetrics(30, 33, 38, 22, 2.3, 1.10, "孙兴慜个人能力可超预期得分"),
    "MEX": AdvancedMetrics(33, 25, 28, 35, 2.8, 0.90, "主场哨与定位球占比高"),
    "USA": AdvancedMetrics(28, 32, 36, 30, 2.1, 1.03, "体能充沛，下半场进球多"),
}


def _default_depth(rating: float) -> SquadDepth:
    s = min(85, 45 + rating * 0.4)
    flex = "高" if rating >= 85 else ("中" if rating >= 72 else "低")
    return SquadDepth(s, flex, 27.0, s - 8, s - 5, "按实力估算的板凳深度")


def _default_metrics(rating: float, attack: float, defense: float) -> AdvancedMetrics:
    return AdvancedMetrics(
        clean_sheet_rate=20 + defense * 0.25,
        late_goal_rate=25 + attack * 0.05,
        comeback_win_rate=20 + rating * 0.15,
        set_piece_goal_share=28,
        cards_per_game=2.2,
        xg_overperformance=0.98 + (attack - 75) / 200,
        note="按联赛与国家队数据估算",
    )


def get_squad_depth(code: str, rating: float) -> SquadDepth:
    return _DEPTH.get(code, _default_depth(rating))


def get_advanced_metrics(code: str, rating: float, attack: float, defense: float) -> AdvancedMetrics:
    return _METRICS.get(code, _default_metrics(rating, attack, defense))


def depth_multiplier(d: SquadDepth, matches_played: int) -> tuple[float, float]:
    """赛程深入后板凳深度影响增大。"""
    fatigue = max(0, matches_played - 2) * 0.02
    depth_factor = d.depth_score / 80.0
    if d.rotation_flex == "低":
        fatigue *= 1.5
    elif d.rotation_flex == "高":
        fatigue *= 0.6
    atk = 1.0 - fatigue / depth_factor
    defn = 1.0 + fatigue * 0.8 / depth_factor
    return max(0.88, min(1.05, atk)), max(0.92, min(1.12, defn))


def metrics_multiplier(m: AdvancedMetrics) -> tuple[float, float, float]:
    """返回 (进攻, 防守, 置信度调整)。"""
    atk = 0.95 + m.xg_overperformance * 0.08 + m.late_goal_rate / 500
    defn = 1.0 / (0.90 + m.clean_sheet_rate / 200)
    conf = -0.02 if m.cards_per_game >= 2.5 else 0.0
    return max(0.90, min(1.10, atk)), max(0.90, min(1.10, defn)), conf
