"""Protected Continuity Event Generation & Simulation API.
Healthcare Infrastructure & Primary-care Planning Optimization Grid

Protected Business Operations:
- POST /api/v1/continuity/simulate-alert: Inserts a verified continuity event into PostgreSQL table
  'service_continuity', triggering Supabase Realtime broadcast to subscribed frontend dashboards.
- GET /api/v1/continuity/events: Retrieve recent continuity events.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.db.session import get_db

router = APIRouter(prefix="/api/v1/continuity", tags=["continuity-realtime"])


class SimulatedAlertRequest(BaseModel):
    phc_id: Optional[str] = None
    phc_code: Optional[str] = "PHC-DST-A1-01"
    service_id: str = "diarrhoeal_care"
    status: str = Field("CRITICAL", pattern="^(HEALTHY|WATCH|CRITICAL|COMPROMISED)$")
    hours_to_compromise: float = Field(14.0, ge=0.0, le=168.0)
    primary_bottleneck: str = "Oral Rehydration Salts (ORS) Depletion"


@router.post("/simulate-alert")
def simulate_continuity_alert(
    req: SimulatedAlertRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Protected business operation: inserts a continuity alert into Supabase PostgreSQL,
    which triggers Realtime WebSocket broadcast to connected dashboard command centers.
    """
    # Resolve PHC UUID
    res = db.execute(
        text("SELECT id, code, name FROM phcs WHERE code = :code LIMIT 1"),
        {"code": req.phc_code},
    ).fetchone()

    if not res:
        # Fallback to any PHC in database
        res = db.execute(text("SELECT id, code, name FROM phcs LIMIT 1")).fetchone()

    if not res:
        raise HTTPException(status_code=404, detail="No PHCs found in database.")

    phc_uuid = str(res[0])
    phc_code = str(res[1])
    phc_name = str(res[2])

    alert_id = str(uuid.uuid4())
    now_ts = datetime.utcnow()

    # Insert into service_continuity
    db.execute(
        text("""
            INSERT INTO service_continuity (
                id, phc_id, service_id, status, hours_to_compromise,
                primary_bottleneck, assessed_at, created_at, updated_at
            ) VALUES (
                :id, :phc_id, :service_id, :status, :hours,
                :bottleneck, :now, :now, :now
            )
        """),
        {
            "id": alert_id,
            "phc_id": phc_uuid,
            "service_id": req.service_id,
            "status": req.status,
            "hours": req.hours_to_compromise,
            "bottleneck": req.primary_bottleneck,
            "now": now_ts,
        },
    )

    # Also log in audit_logs
    import json
    db.execute(
        text("""
            INSERT INTO audit_logs (
                event_type, entity_name, entity_id, user_id, details_json, created_at
            ) VALUES (
                'REALTIME_CONTINUITY_ALERT_INSERT', 'service_continuity', :entity_id,
                'system_simulator', :details, :now
            )
        """),
        {
            "entity_id": alert_id,
            "details": json.dumps({
                "phc_code": phc_code,
                "phc_name": phc_name,
                "service_id": req.service_id,
                "status": req.status,
                "hours_to_compromise": req.hours_to_compromise,
                "bottleneck": req.primary_bottleneck,
            }),
            "now": now_ts,
        },
    )
    db.commit()

    return {
        "status": "INSERTED",
        "id": alert_id,
        "phc_code": phc_code,
        "phc_name": phc_name,
        "service_id": req.service_id,
        "continuity_status": req.status,
        "hours_to_compromise": req.hours_to_compromise,
        "primary_bottleneck": req.primary_bottleneck,
        "timestamp": now_ts.isoformat(),
        "realtime_broadcast": True,
        "message": "Continuous event persisted to PostgreSQL System-of-Record and published to Supabase Realtime channel.",
    }


@router.get("/events")
def get_recent_events(
    limit: int = 20,
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Fetch recent service continuity events directly from Supabase PostgreSQL."""
    rows = db.execute(
        text("""
            SELECT sc.id, p.code AS phc_code, p.name AS phc_name, sc.service_id,
                   sc.status, sc.hours_to_compromise, sc.primary_bottleneck, sc.assessed_at
            FROM service_continuity sc
            JOIN phcs p ON p.id = sc.phc_id
            ORDER BY sc.assessed_at DESC
            LIMIT :limit
        """),
        {"limit": limit},
    ).fetchall()

    return [
        {
            "id": str(r[0]),
            "phc_code": r[1],
            "phc_name": r[2],
            "service_id": r[3],
            "status": r[4],
            "hours_to_compromise": float(r[5]),
            "primary_bottleneck": r[6],
            "timestamp": r[7].isoformat() if r[7] else datetime.utcnow().isoformat(),
        }
        for r in rows
    ]
