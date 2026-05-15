"""
Dashboard summary endpoint.
Returns counts that the admin dashboard tiles can't easily compute from
the existing list endpoints (e.g. "submissions today").

"Today" means since local midnight in America/Chicago (Alabama),
NOT since UTC midnight, so the dashboard rolls over at the right time.
"""
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter
from sqlalchemy import func

from app.database import SessionLocal
from app.models import Observation, WalkaroundSubmission

router = APIRouter()


def _today_start_utc_naive() -> datetime:
    """
    Returns the UTC instant corresponding to 'today 00:00' in America/Chicago,
    as a naive datetime (no tzinfo), suitable for comparing against the
    naive created_at columns in our models (which use datetime.utcnow()).
    """
    central = ZoneInfo("America/Chicago")
    now_local = datetime.now(central)
    midnight_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    midnight_utc = midnight_local.astimezone(ZoneInfo("UTC"))
    return midnight_utc.replace(tzinfo=None)


@router.get("/dashboard/stats")
def dashboard_stats():
    db = SessionLocal()
    try:
        cutoff = _today_start_utc_naive()

        obs_today = (
            db.query(func.count(Observation.id))
              .filter(Observation.created_at >= cutoff)
              .scalar()
        ) or 0

        walk_today = (
            db.query(func.count(WalkaroundSubmission.id))
              .filter(WalkaroundSubmission.created_at >= cutoff)
              .scalar()
        ) or 0

        return {
            "submissions_today": int(obs_today) + int(walk_today),
            "observations_today": int(obs_today),
            "walkarounds_today": int(walk_today),
        }
    finally:
        db.close()
