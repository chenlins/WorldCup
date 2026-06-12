"""2026 世界杯完整赛程（104 场）。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Fixture:
    id: int
    date: str  # YYYY-MM-DD
    time_et: str
    home: str  # team code or slot label
    away: str
    group: str | None  # None for knockout
    stage: str
    venue: str
    city: str
    is_knockout: bool = False
    home_is_slot: bool = False
    away_is_slot: bool = False


def _gs(
    mid: int,
    date: str,
    time_et: str,
    home: str,
    away: str,
    group: str,
    venue: str,
    city: str,
) -> Fixture:
    return Fixture(
        id=mid,
        date=date,
        time_et=time_et,
        home=home,
        away=away,
        group=group,
        stage="小组赛",
        venue=venue,
        city=city,
    )


def _ko(
    mid: int,
    date: str,
    time_et: str,
    home: str,
    away: str,
    stage: str,
    venue: str,
    city: str,
    home_slot: bool = False,
    away_slot: bool = False,
) -> Fixture:
    return Fixture(
        id=mid,
        date=date,
        time_et=time_et,
        home=home,
        away=away,
        group=None,
        stage=stage,
        venue=venue,
        city=city,
        is_knockout=True,
        home_is_slot=home_slot,
        away_is_slot=away_slot,
    )


FIXTURES: list[Fixture] = [
    # 小组赛
    _gs(1, "2026-06-11", "15:00", "MEX", "RSA", "A", "Estadio Azteca", "墨西哥城"),
    _gs(2, "2026-06-11", "22:00", "KOR", "CZE", "A", "Estadio Akron", "瓜达拉哈拉"),
    _gs(3, "2026-06-12", "15:00", "CAN", "BIH", "B", "BMO Field", "多伦多"),
    _gs(4, "2026-06-12", "21:00", "USA", "PAR", "D", "SoFi Stadium", "洛杉矶"),
    _gs(5, "2026-06-13", "21:00", "HAI", "SCO", "C", "Gillette Stadium", "波士顿"),
    _gs(6, "2026-06-13", "00:00", "AUS", "TUR", "D", "BC Place", "温哥华"),
    _gs(7, "2026-06-13", "18:00", "BRA", "MAR", "C", "MetLife Stadium", "纽约/新泽西"),
    _gs(8, "2026-06-13", "15:00", "QAT", "SUI", "B", "Levi's Stadium", "旧金山湾区"),
    _gs(9, "2026-06-14", "19:00", "CIV", "ECU", "E", "Lincoln Financial Field", "费城"),
    _gs(10, "2026-06-14", "13:00", "GER", "CUW", "E", "NRG Stadium", "休斯顿"),
    _gs(11, "2026-06-14", "16:00", "NED", "JPN", "F", "AT&T Stadium", "达拉斯"),
    _gs(12, "2026-06-14", "22:00", "SWE", "TUN", "F", "Estadio BBVA", "蒙特雷"),
    _gs(13, "2026-06-15", "18:00", "KSA", "URU", "H", "Hard Rock Stadium", "迈阿密"),
    _gs(14, "2026-06-15", "12:00", "ESP", "CPV", "H", "Mercedes-Benz Stadium", "亚特兰大"),
    _gs(15, "2026-06-15", "21:00", "IRN", "NZL", "G", "SoFi Stadium", "洛杉矶"),
    _gs(16, "2026-06-15", "15:00", "BEL", "EGY", "G", "Lumen Field", "西雅图"),
    _gs(17, "2026-06-16", "15:00", "FRA", "SEN", "I", "MetLife Stadium", "纽约/新泽西"),
    _gs(18, "2026-06-16", "18:00", "IRQ", "NOR", "I", "Gillette Stadium", "波士顿"),
    _gs(19, "2026-06-16", "21:00", "ARG", "ALG", "J", "Arrowhead Stadium", "堪萨斯城"),
    _gs(20, "2026-06-16", "00:00", "AUT", "JOR", "J", "Levi's Stadium", "旧金山湾区"),
    _gs(21, "2026-06-17", "19:00", "GHA", "PAN", "L", "BMO Field", "多伦多"),
    _gs(22, "2026-06-17", "16:00", "ENG", "CRO", "L", "AT&T Stadium", "达拉斯"),
    _gs(23, "2026-06-17", "13:00", "POR", "COD", "K", "NRG Stadium", "休斯顿"),
    _gs(24, "2026-06-17", "22:00", "UZB", "COL", "K", "Estadio Azteca", "墨西哥城"),
    _gs(25, "2026-06-18", "12:00", "CZE", "RSA", "A", "Mercedes-Benz Stadium", "亚特兰大"),
    _gs(26, "2026-06-18", "15:00", "SUI", "BIH", "B", "SoFi Stadium", "洛杉矶"),
    _gs(27, "2026-06-18", "18:00", "CAN", "QAT", "B", "BC Place", "温哥华"),
    _gs(28, "2026-06-18", "21:00", "MEX", "KOR", "A", "Estadio Akron", "瓜达拉哈拉"),
    _gs(29, "2026-06-19", "21:00", "BRA", "HAI", "C", "Lincoln Financial Field", "费城"),
    _gs(30, "2026-06-19", "18:00", "SCO", "MAR", "C", "Gillette Stadium", "波士顿"),
    _gs(31, "2026-06-19", "23:00", "TUR", "PAR", "D", "Levi's Stadium", "旧金山湾区"),
    _gs(32, "2026-06-19", "15:00", "USA", "AUS", "D", "Lumen Field", "西雅图"),
    _gs(33, "2026-06-20", "16:00", "GER", "CIV", "E", "BMO Field", "多伦多"),
    _gs(34, "2026-06-20", "20:00", "ECU", "CUW", "E", "Arrowhead Stadium", "堪萨斯城"),
    _gs(35, "2026-06-20", "13:00", "NED", "SWE", "F", "NRG Stadium", "休斯顿"),
    _gs(36, "2026-06-20", "00:00", "TUN", "JPN", "F", "Estadio BBVA", "蒙特雷"),
    _gs(37, "2026-06-21", "18:00", "URU", "CPV", "H", "Hard Rock Stadium", "迈阿密"),
    _gs(38, "2026-06-21", "12:00", "ESP", "KSA", "H", "Mercedes-Benz Stadium", "亚特兰大"),
    _gs(39, "2026-06-21", "15:00", "BEL", "IRN", "G", "SoFi Stadium", "洛杉矶"),
    _gs(40, "2026-06-21", "21:00", "NZL", "EGY", "G", "BC Place", "温哥华"),
    _gs(41, "2026-06-22", "20:00", "NOR", "SEN", "I", "MetLife Stadium", "纽约/新泽西"),
    _gs(42, "2026-06-22", "17:00", "FRA", "IRQ", "I", "Lincoln Financial Field", "费城"),
    _gs(43, "2026-06-22", "13:00", "ARG", "AUT", "J", "AT&T Stadium", "达拉斯"),
    _gs(44, "2026-06-22", "23:00", "JOR", "ALG", "J", "Levi's Stadium", "旧金山湾区"),
    _gs(45, "2026-06-23", "16:00", "ENG", "GHA", "L", "Gillette Stadium", "波士顿"),
    _gs(46, "2026-06-23", "19:00", "PAN", "CRO", "L", "BMO Field", "多伦多"),
    _gs(47, "2026-06-23", "13:00", "POR", "UZB", "K", "NRG Stadium", "休斯顿"),
    _gs(48, "2026-06-23", "22:00", "COL", "COD", "K", "Estadio Akron", "瓜达拉哈拉"),
    _gs(49, "2026-06-24", "18:00", "SCO", "BRA", "C", "Hard Rock Stadium", "迈阿密"),
    _gs(50, "2026-06-24", "18:00", "MAR", "HAI", "C", "Mercedes-Benz Stadium", "亚特兰大"),
    _gs(51, "2026-06-24", "15:00", "SUI", "CAN", "B", "BC Place", "温哥华"),
    _gs(52, "2026-06-24", "15:00", "BIH", "QAT", "B", "Lumen Field", "西雅图"),
    _gs(53, "2026-06-24", "21:00", "CZE", "MEX", "A", "Estadio Azteca", "墨西哥城"),
    _gs(54, "2026-06-24", "21:00", "RSA", "KOR", "A", "Estadio BBVA", "蒙特雷"),
    _gs(55, "2026-06-25", "16:00", "CUW", "CIV", "E", "Lincoln Financial Field", "费城"),
    _gs(56, "2026-06-25", "16:00", "ECU", "GER", "E", "MetLife Stadium", "纽约/新泽西"),
    _gs(57, "2026-06-25", "19:00", "JPN", "SWE", "F", "AT&T Stadium", "达拉斯"),
    _gs(58, "2026-06-25", "19:00", "TUN", "NED", "F", "Arrowhead Stadium", "堪萨斯城"),
    _gs(59, "2026-06-25", "22:00", "TUR", "USA", "D", "SoFi Stadium", "洛杉矶"),
    _gs(60, "2026-06-25", "22:00", "PAR", "AUS", "D", "Levi's Stadium", "旧金山湾区"),
    _gs(61, "2026-06-26", "15:00", "NOR", "FRA", "I", "Gillette Stadium", "波士顿"),
    _gs(62, "2026-06-26", "15:00", "SEN", "IRQ", "I", "BMO Field", "多伦多"),
    _gs(63, "2026-06-26", "23:00", "EGY", "IRN", "G", "Lumen Field", "西雅图"),
    _gs(64, "2026-06-26", "23:00", "NZL", "BEL", "G", "BC Place", "温哥华"),
    _gs(65, "2026-06-26", "20:00", "CPV", "KSA", "H", "NRG Stadium", "休斯顿"),
    _gs(66, "2026-06-26", "20:00", "URU", "ESP", "H", "Estadio Akron", "瓜达拉哈拉"),
    _gs(67, "2026-06-27", "17:00", "PAN", "ENG", "L", "MetLife Stadium", "纽约/新泽西"),
    _gs(68, "2026-06-27", "17:00", "CRO", "GHA", "L", "Lincoln Financial Field", "费城"),
    _gs(69, "2026-06-27", "22:00", "ALG", "AUT", "J", "Arrowhead Stadium", "堪萨斯城"),
    _gs(70, "2026-06-27", "22:00", "JOR", "ARG", "J", "AT&T Stadium", "达拉斯"),
    _gs(71, "2026-06-27", "19:30", "COL", "POR", "K", "Hard Rock Stadium", "迈阿密"),
    _gs(72, "2026-06-27", "19:30", "COD", "UZB", "K", "Mercedes-Benz Stadium", "亚特兰大"),
    # 32 强
    _ko(73, "2026-06-28", "15:00", "A组亚军", "B组亚军", "32强", "SoFi Stadium", "洛杉矶", True, True),
    _ko(74, "2026-06-29", "16:30", "E组冠军", "A/B/C/D/F最佳第三名", "32强", "Gillette Stadium", "波士顿", True, True),
    _ko(75, "2026-06-29", "21:00", "F组冠军", "C组亚军", "32强", "Estadio BBVA", "蒙特雷", True, True),
    _ko(76, "2026-06-29", "13:00", "C组冠军", "F组亚军", "32强", "NRG Stadium", "休斯顿", True, True),
    _ko(77, "2026-06-30", "17:00", "I组冠军", "C/D/F/G/H最佳第三名", "32强", "MetLife Stadium", "纽约/新泽西", True, True),
    _ko(78, "2026-06-30", "13:00", "E组亚军", "I组亚军", "32强", "AT&T Stadium", "达拉斯", True, True),
    _ko(79, "2026-06-30", "21:00", "A组冠军", "C/E/F/H/I最佳第三名", "32强", "Estadio Azteca", "墨西哥城", True, True),
    _ko(80, "2026-07-01", "12:00", "L组冠军", "E/H/I/J/K最佳第三名", "32强", "Mercedes-Benz Stadium", "亚特兰大", True, True),
    _ko(81, "2026-07-01", "20:00", "D组冠军", "B/E/F/I/J最佳第三名", "32强", "Levi's Stadium", "旧金山湾区", True, True),
    _ko(82, "2026-07-01", "16:00", "G组冠军", "A/E/H/I/J最佳第三名", "32强", "Lumen Field", "西雅图", True, True),
    _ko(83, "2026-07-02", "19:00", "K组亚军", "L组亚军", "32强", "BMO Field", "多伦多", True, True),
    _ko(84, "2026-07-02", "15:00", "H组冠军", "J组亚军", "32强", "SoFi Stadium", "洛杉矶", True, True),
    _ko(85, "2026-07-02", "23:00", "B组冠军", "E/F/G/I/J最佳第三名", "32强", "BC Place", "温哥华", True, True),
    _ko(86, "2026-07-03", "18:00", "J组冠军", "H组亚军", "32强", "Hard Rock Stadium", "迈阿密", True, True),
    _ko(87, "2026-07-03", "21:30", "K组冠军", "D/E/I/J/L最佳第三名", "32强", "Arrowhead Stadium", "堪萨斯城", True, True),
    _ko(88, "2026-07-03", "14:00", "D组亚军", "G组亚军", "32强", "AT&T Stadium", "达拉斯", True, True),
    # 16 强
    _ko(89, "2026-07-04", "17:00", "M74胜者", "M77胜者", "16强", "Lincoln Financial Field", "费城", True, True),
    _ko(90, "2026-07-04", "13:00", "M73胜者", "M75胜者", "16强", "NRG Stadium", "休斯顿", True, True),
    _ko(91, "2026-07-05", "16:00", "M76胜者", "M78胜者", "16强", "MetLife Stadium", "纽约/新泽西", True, True),
    _ko(92, "2026-07-05", "20:00", "M79胜者", "M80胜者", "16强", "Estadio Azteca", "墨西哥城", True, True),
    _ko(93, "2026-07-06", "15:00", "M83胜者", "M84胜者", "16强", "AT&T Stadium", "达拉斯", True, True),
    _ko(94, "2026-07-06", "20:00", "M81胜者", "M82胜者", "16强", "Lumen Field", "西雅图", True, True),
    _ko(95, "2026-07-07", "12:00", "M86胜者", "M88胜者", "16强", "Mercedes-Benz Stadium", "亚特兰大", True, True),
    _ko(96, "2026-07-07", "16:00", "M85胜者", "M87胜者", "16强", "BC Place", "温哥华", True, True),
    # 8 强
    _ko(97, "2026-07-09", "16:00", "M89胜者", "M90胜者", "8强", "Gillette Stadium", "波士顿", True, True),
    _ko(98, "2026-07-10", "15:00", "M93胜者", "M94胜者", "8强", "SoFi Stadium", "洛杉矶", True, True),
    _ko(99, "2026-07-11", "17:00", "M91胜者", "M92胜者", "8强", "Hard Rock Stadium", "迈阿密", True, True),
    _ko(100, "2026-07-11", "21:00", "M95胜者", "M96胜者", "8强", "Arrowhead Stadium", "堪萨斯城", True, True),
    # 半决赛
    _ko(101, "2026-07-14", "15:00", "M97胜者", "M98胜者", "半决赛", "AT&T Stadium", "达拉斯", True, True),
    _ko(102, "2026-07-15", "15:00", "M99胜者", "M100胜者", "半决赛", "Mercedes-Benz Stadium", "亚特兰大", True, True),
    # 三四名
    _ko(103, "2026-07-18", "17:00", "M101负者", "M102负者", "三四名决赛", "Hard Rock Stadium", "迈阿密", True, True),
    # 决赛
    _ko(104, "2026-07-19", "15:00", "M101胜者", "M102胜者", "决赛", "MetLife Stadium", "纽约/新泽西", True, True),
]

FIXTURE_BY_ID: dict[int, Fixture] = {f.id: f for f in FIXTURES}

TOURNAMENT_START = "2026-06-11"
TOURNAMENT_END = "2026-07-19"


def fixtures_by_date(date: str) -> list[Fixture]:
    return [f for f in FIXTURES if f.date == date]


def all_match_dates() -> list[str]:
    return sorted({f.date for f in FIXTURES})
