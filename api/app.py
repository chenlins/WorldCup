import sys
from pathlib import Path

import yaml
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles

from data.fixtures import TOURNAMENT_END, TOURNAMENT_START, all_match_dates
from predictor.engine import predict_by_date, predict_match, prediction_to_dict


def _web_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "web"  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent.parent / "web"


def create_app(config_path: str = "config.yaml") -> FastAPI:
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    app = FastAPI(title="2026 世界杯赛事分析", version="1.0.0")

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    @app.get("/api/dates")
    def api_dates():
        return {
            "start": TOURNAMENT_START,
            "end": TOURNAMENT_END,
            "dates": all_match_dates(),
        }

    @app.get("/api/analyze")
    def api_analyze(
        date: str = Query(..., description="YYYY-MM-DD"),
        extra_mode: str = Query(
            "none",
            description="扩展分析：none=无, human=人性分析, same_odds=同赔率赛事分析",
        ),
    ):
        mode = extra_mode.lower()
        if mode not in ("none", "human", "same_odds"):
            raise HTTPException(status_code=400, detail="extra_mode 须为 none、human 或 same_odds")
        try:
            return predict_by_date(date, extra_mode=mode)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    @app.get("/api/match/{match_id}")
    def api_match(
        match_id: int,
        extra_mode: str = Query("none", description="扩展分析模式"),
    ):
        mode = extra_mode.lower()
        if mode not in ("none", "human", "same_odds"):
            raise HTTPException(status_code=400, detail="extra_mode 须为 none、human 或 same_odds")
        try:
            return prediction_to_dict(predict_match(match_id, extra_mode=mode))
        except KeyError as e:
            raise HTTPException(status_code=404, detail="比赛不存在") from e
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    app.mount("/", StaticFiles(directory=str(_web_dir()), html=True), name="web")
    return app
