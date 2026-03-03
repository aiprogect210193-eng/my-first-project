from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
from web import storage

app = FastAPI(title="Маркетинговый ИИ агент", version="1.0")

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def index():
    return FileResponse(str(STATIC_DIR / "index.html"))


# ── Leads ─────────────────────────────────────────────────────────────────────

class LeadIn(BaseModel):
    source: str                  # форма / telegram / звонок
    is_qualified: bool
    lead_date: str = ""
    campaign_name: str = ""
    keyword: str = ""
    rejection_reason: str = ""
    notes: str = ""


@app.post("/leads", status_code=201)
def add_lead(lead: LeadIn):
    lead_id = storage.save_lead(**lead.model_dump())
    return {"id": lead_id, "status": "ok"}


@app.get("/leads")
def list_leads(limit: int = 100, qualified: str = "all"):
    qualified_filter = None
    if qualified == "yes":
        qualified_filter = True
    elif qualified == "no":
        qualified_filter = False
    return storage.get_leads(limit=limit, qualified_only=qualified_filter)


@app.get("/leads/stats")
def lead_stats():
    return storage.get_lead_stats()


# ── Feedback ──────────────────────────────────────────────────────────────────

class FeedbackIn(BaseModel):
    message: str


@app.post("/feedback", status_code=201)
def add_feedback(fb: FeedbackIn):
    fid = storage.save_feedback(fb.message)
    return {"id": fid, "status": "ok"}


@app.get("/feedback")
def list_feedback(limit: int = 50):
    return storage.get_feedback(limit=limit)


# ── Reports ───────────────────────────────────────────────────────────────────

@app.get("/reports")
def list_reports():
    return storage.get_reports()


@app.get("/reports/{report_id}")
def get_report(report_id: int):
    report = storage.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Отчёт не найден")
    return report


# ── History ───────────────────────────────────────────────────────────────────

@app.get("/history")
def get_history(limit: int = 100):
    return storage.get_action_log(limit=limit)


# ── Recommendations ───────────────────────────────────────────────────────────

class RecommendationIn(BaseModel):
    content: str


@app.get("/recommendations")
def list_recommendations(limit: int = 10):
    return storage.get_recommendations(limit=limit)


@app.post("/recommendations", status_code=201)
def add_recommendation(rec: RecommendationIn):
    rid = storage.save_recommendation(rec.content)
    return {"id": rid, "status": "ok"}


# ── Dashboard aggregate ────────────────────────────────────────────────────────

@app.get("/stats/dashboard")
def dashboard_stats():
    """Все данные для дашборда одним запросом."""
    lead_stats = storage.get_lead_stats()
    recent_leads = storage.get_leads(limit=5)
    recent_reports = storage.get_reports(limit=5)
    recommendations = storage.get_recommendations(limit=3)
    history = storage.get_action_log(limit=5)
    return {
        "lead_stats": lead_stats,
        "recent_leads": recent_leads,
        "recent_reports": recent_reports,
        "recommendations": recommendations,
        "recent_history": history,
    }


# ── Manual trigger ────────────────────────────────────────────────────────────

@app.post("/optimize/now")
def trigger_optimization():
    """Запустить оптимизацию вручную."""
    try:
        from automation.weekly_cycle import run_weekly_cycle
        run_weekly_cycle()
        return {"status": "ok", "message": "Оптимизация запущена"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
