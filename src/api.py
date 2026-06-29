import json
import os

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse, Response
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "public", "data", "planning.json")
INDEX_HTML = os.path.join(BASE_DIR, "public", "index.html")

app = FastAPI(title="Planning ESTIAM", version="1.0.0")

REQUEST_COUNT = Counter(
    "planning_requests_total",
    "Total API requests",
    ["endpoint"],
)
ICS_REFRESH_TOTAL = Counter(
    "planning_ics_refresh_total",
    "Total ICS refreshes triggered",
)


def _load_planning() -> dict | None:
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None


@app.get("/")
def root():
    return FileResponse(INDEX_HTML)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/planning")
def get_planning():
    REQUEST_COUNT.labels(endpoint="/planning").inc()
    data = _load_planning()
    if data is None:
        return JSONResponse(
            status_code=503,
            content={"error": "Planning data not available, run /refresh first"},
        )
    return data


@app.get("/planning/week/{week_num}")
def get_week(week_num: int):
    REQUEST_COUNT.labels(endpoint="/planning/week").inc()
    data = _load_planning()
    if data is None:
        return JSONResponse(
            status_code=503,
            content={"error": "Planning data not available"},
        )
    week = data.get("weeks", {}).get(str(week_num))
    if week is None:
        return JSONResponse(
            status_code=404,
            content={"error": f"Week {week_num} not found"},
        )
    return week


@app.post("/refresh")
async def refresh():
    from scraper import get_courses_from_ics, get_current_and_next_week, save_planning_json

    ICS_REFRESH_TOTAL.inc()
    courses = await get_courses_from_ics()
    if courses is None:
        return JSONResponse(
            status_code=502,
            content={"error": "Failed to fetch ICS data"},
        )
    week_current, week_next = get_current_and_next_week()
    save_planning_json(courses, week_current, week_next)
    return {"status": "refreshed", "weeks": sorted(courses.keys())}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
