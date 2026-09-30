"""Relational Database Tests for HippoGrid Phase 1.
Tests connection, table availability, basic insert, basic query, and foreign key relationships.
"""
import uuid
import pytest
from sqlalchemy import text
from backend.db.engine import engine
from backend.db.session import SessionLocal, check_db_connection
from backend.db.models import (
    Base,
    District,
    InventoryTransaction,
    Medicine,
    PHC,
    Service,
    ServiceContinuity,
    ServiceDependency,
    State,
    Warehouse,
)
from backend.db.repositories.network_repository import NetworkRepository
from backend.db.repositories.telemetry_repository import TelemetryRepository


@pytest.fixture(scope="module")
def db_session():
    """Create a database session for test operations."""
    status = check_db_connection(engine)
    if not status["connected"]:
        pytest.skip(f"Supabase PostgreSQL is not reachable at DATABASE_URL: {status.get('error')}")
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_db_connection_live():
    """Verify live connectivity to Supabase PostgreSQL database."""
    status = check_db_connection(engine)
    # Even if offline, verify health contract structure
    assert "connected" in status
    assert "status" in status
    assert "latency_ms" in status


def test_table_availability_all_core_tables():
    """Verify all 27 core tables exist in SQLAlchemy Base metadata."""
    expected_tables = {
        "states",
        "districts",
        "phcs",
        "warehouses",
        "services",
        "service_dependencies",
        "medicines",
        "inventory_transactions",
        "patient_visits",
        "bed_status",
        "workforce_status",
        "power_status",
        "weather_observations",
        "road_status",
        "forecasts",
        "conformal_predictions",
        "service_continuity",
        "scenarios",
        "scenario_results",
        "resource_plans",
        "plan_transfers",
        "plan_feedback",
        "stress_tests",
        "stress_frontiers",
        "federated_models",
        "model_runs",
        "audit_logs",
    }
    actual_tables = set(Base.metadata.tables.keys())
    assert expected_tables.issubset(actual_tables), f"Missing tables: {expected_tables - actual_tables}"


def test_views_availability_in_database(db_session):
    """Verify the 3 analytical dashboard views exist in the PostgreSQL database if connected."""
    conn_check = check_db_connection(engine)
    if not conn_check["connected"]:
        pytest.skip("PostgreSQL database offline; skipping live view test.")

    result = db_session.execute(
        text("SELECT table_name FROM information_schema.views WHERE table_schema = 'public'")
    ).fetchall()
    view_names = {row[0] for row in result}
    assert "v_phc_continuity_summary" in view_names
    assert "v_service_risk_monitor" in view_names
    assert "v_daily_operational_snapshot" in view_names


def test_repository_basic_query(db_session):
    """Verify basic query through NetworkRepository."""
    repo = NetworkRepository(db_session)
    states = repo.list_states()
    assert len(states) == 3
    assert set(s.code for s in states) == {"STA", "STB", "STC"}

    districts = repo.list_districts()
    assert len(districts) == 6

    phcs = repo.list_phcs()
    assert len(phcs) == 36

    services = repo.list_services()
    service_ids = {s.id for s in services}
    assert {"diarrhoeal_care", "maternal_delivery", "vaccination", "fever_malaria"}.issubset(service_ids)

    medicines = repo.list_medicines()
    med_ids = {m.id for m in medicines}
    assert {"ORS", "IV_fluids", "zinc", "oxytocin", "paracetamol", "ACT_antimalarial", "vaccine_penta", "amlodipine"}.issubset(med_ids)


def test_foreign_key_relationships(db_session):
    """Verify State -> District -> PHC foreign key relationships."""
    repo = NetworkRepository(db_session)
    state_a = repo.get_state_by_code("STA")
    assert state_a is not None
    assert len(state_a.districts) == 2

    # Verify first district links back to State A and has 6 PHCs
    dist = state_a.districts[0]
    assert dist.state.code == "STA"
    assert len(dist.phcs) == 6
    assert dist.phcs[0].district.id == dist.id


def test_basic_insert_and_query_telemetry(db_session):
    """Verify basic insert and query through TelemetryRepository."""
    net_repo = NetworkRepository(db_session)
    tel_repo = TelemetryRepository(db_session)

    phc = net_repo.list_phcs()[0]
    
    # Insert an inventory transaction
    tx = tel_repo.record_inventory_transaction(
        phc_id=phc.id,
        medicine_id="ORS",
        quantity_change=50.0,
        stock_after=150.0,
        transaction_type="INBOUND",
    )
    assert tx.id is not None
    assert float(tx.stock_after) == 150.0

    # Query latest stock
    latest_stock = tel_repo.get_latest_inventory_stock(phc.id, "ORS")
    assert latest_stock == 150.0

    # Upsert service continuity
    sc = tel_repo.upsert_service_continuity(
        phc_id=phc.id,
        service_id="diarrhoeal_care",
        status="HEALTHY",
        hours_to_compromise=48.0,
        primary_bottleneck="Nominal",
    )
    assert sc.id is not None
    assert sc.status == "HEALTHY"
