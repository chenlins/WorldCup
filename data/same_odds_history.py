"""历届大赛同赔率档位赛果样本（用于同赔率赛事分析）。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OddsHistoryMatch:
    tournament: str
    match_label: str
    home_implied: float
    draw_implied: float
    away_implied: float
    score: str
    result: str  # home / draw / away
    note: str = ""


# 隐含概率 + 赛果（基于历届世界杯/欧洲杯公开赔率归纳）
HISTORY: list[OddsHistoryMatch] = [
    OddsHistoryMatch("2018世界杯", "法国 vs 澳大利亚", 0.72, 0.20, 0.08, "2-1", "home", "热门主队小胜"),
    OddsHistoryMatch("2018世界杯", "德国 vs 墨西哥", 0.68, 0.22, 0.10, "0-1", "away", "大热门首轮爆冷"),
    OddsHistoryMatch("2018世界杯", "阿根廷 vs 冰岛", 0.70, 0.21, 0.09, "1-1", "draw", "超级热门被逼平"),
    OddsHistoryMatch("2018世界杯", "西班牙 vs 葡萄牙", 0.55, 0.25, 0.20, "3-3", "draw", "势均力敌高比分平局"),
    OddsHistoryMatch("2018世界杯", "比利时 vs 日本", 0.66, 0.22, 0.12, "3-2", "home", "热门逆转"),
    OddsHistoryMatch("2018世界杯", "克罗地亚 vs 英格兰", 0.42, 0.28, 0.30, "2-1", "home", "主队略热晋级"),
    OddsHistoryMatch("2022世界杯", "阿根廷 vs 沙特", 0.78, 0.18, 0.04, "1-2", "away", "史诗级冷门"),
    OddsHistoryMatch("2022世界杯", "日本 vs 德国", 0.22, 0.28, 0.50, "2-1", "home", "弱队主场逆袭"),
    OddsHistoryMatch("2022世界杯", "摩洛哥 vs 比利时", 0.25, 0.30, 0.45, "2-0", "home", "非洲球队爆冷"),
    OddsHistoryMatch("2022世界杯", "克罗地亚 vs 巴西", 0.28, 0.30, 0.42, "0-0", "draw", "强队淘汰赛平局进点球"),
    OddsHistoryMatch("2022世界杯", "法国 vs 波兰", 0.74, 0.19, 0.07, "3-1", "home", "热门顺利过关"),
    OddsHistoryMatch("2022世界杯", "葡萄牙 vs 瑞士", 0.62, 0.24, 0.14, "6-1", "home", "热门大胜"),
    OddsHistoryMatch("2020欧洲杯", "意大利 vs 土耳其", 0.65, 0.23, 0.12, "3-0", "home", "开幕战热门取胜"),
    OddsHistoryMatch("2020欧洲杯", "法国 vs 瑞士", 0.58, 0.24, 0.18, "3-3", "draw", "热门被逼平后点球出局"),
    OddsHistoryMatch("2020欧洲杯", "丹麦 vs 芬兰", 0.60, 0.25, 0.15, "0-1", "away", "情绪因素下冷门"),
    OddsHistoryMatch("2014世界杯", "西班牙 vs 荷兰", 0.52, 0.26, 0.22, "1-5", "away", "卫冕冠军惨败"),
    OddsHistoryMatch("2014世界杯", "巴西 vs 德国", 0.48, 0.26, 0.26, "1-7", "away", "主场热门崩盘"),
    OddsHistoryMatch("2014世界杯", "哥斯达黎加 vs 意大利", 0.18, 0.28, 0.54, "1-0", "home", "弱队死守反击"),
    OddsHistoryMatch("2022世界杯", "韩国 vs 葡萄牙", 0.20, 0.28, 0.52, "2-1", "home", "出线生死战冷门"),
    OddsHistoryMatch("2018世界杯", "韩国 vs 德国", 0.12, 0.22, 0.66, "2-0", "home", "卫冕冠军出局战爆冷"),
    OddsHistoryMatch("2022世界杯", "沙特 vs 墨西哥", 0.38, 0.30, 0.32, "1-2", "away", "胶着赔率客队取胜"),
    OddsHistoryMatch("2018世界杯", "瑞典 vs 墨西哥", 0.40, 0.30, 0.30, "3-0", "home", "出线战主队完胜"),
    OddsHistoryMatch("2022世界杯", "美国 vs 英格兰", 0.22, 0.28, 0.50, "0-0", "draw", "弱队逼平热门"),
    OddsHistoryMatch("2018世界杯", "伊朗 vs 葡萄牙", 0.15, 0.25, 0.60, "1-1", "draw", "弱队死守逼平"),
    OddsHistoryMatch("2022世界杯", "突尼斯 vs 法国", 0.10, 0.22, 0.68, "1-0", "home", "轮换热门输球"),
    OddsHistoryMatch("2018世界杯", "塞尔维亚 vs 瑞士", 0.42, 0.30, 0.28, "1-2", "away", "势均力敌客队逆转"),
    OddsHistoryMatch("2020欧洲杯", "英格兰 vs 意大利", 0.45, 0.30, 0.25, "1-1", "draw", "决赛点球"),
    OddsHistoryMatch("2018世界杯", "乌拉圭 vs 葡萄牙", 0.38, 0.30, 0.32, "2-1", "home", "均势主队晋级"),
    OddsHistoryMatch("2022世界杯", "荷兰 vs 阿根廷", 0.35, 0.30, 0.35, "2-2", "draw", "完全均势点球大战"),
    OddsHistoryMatch("2018世界杯", "哥伦比亚 vs 英格兰", 0.36, 0.30, 0.34, "1-1", "draw", "均势淘汰赛点球"),
]


def find_similar_odds_matches(
    home_implied: float,
    draw_implied: float,
    away_implied: float,
    tolerance: float = 0.10,
    min_samples: int = 3,
) -> list[OddsHistoryMatch]:
    matched = [
        m for m in HISTORY
        if abs(m.home_implied - home_implied) <= tolerance
        and abs(m.away_implied - away_implied) <= tolerance
    ]
    if len(matched) >= min_samples:
        return matched
    # 放宽：仅匹配热门方向与平局率
    favorite_implied = max(home_implied, away_implied)
    return [
        m for m in HISTORY
        if abs(max(m.home_implied, m.away_implied) - favorite_implied) <= 0.12
        and abs(m.draw_implied - draw_implied) <= 0.08
    ]


def aggregate_odds_outcomes(matches: list[OddsHistoryMatch]) -> dict:
    if not matches:
        return {
            "count": 0,
            "home_rate": 0.33,
            "draw_rate": 0.33,
            "away_rate": 0.34,
            "avg_total_goals": 2.5,
            "upset_rate": 0.25,
            "samples": [],
        }
    hw = sum(1 for m in matches if m.result == "home")
    dr = sum(1 for m in matches if m.result == "draw")
    aw = sum(1 for m in matches if m.result == "away")
    n = len(matches)
    goals = []
    upsets = 0
    for m in matches:
        parts = m.score.split("-")
        if len(parts) == 2:
            goals.append(int(parts[0]) + int(parts[1]))
        fav = "home" if m.home_implied >= m.away_implied else "away"
        if m.result != fav and m.result != "draw":
            upsets += 1
        elif m.result == "away" and m.home_implied > m.away_implied + 0.15:
            upsets += 1
        elif m.result == "home" and m.away_implied > m.home_implied + 0.15:
            upsets += 1
    return {
        "count": n,
        "home_rate": hw / n,
        "draw_rate": dr / n,
        "away_rate": aw / n,
        "avg_total_goals": sum(goals) / len(goals) if goals else 2.5,
        "upset_rate": upsets / n,
        "samples": [
            {"label": m.match_label, "score": m.score, "result": m.result, "note": m.note}
            for m in matches[:6]
        ],
    }
