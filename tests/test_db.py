"""Tests for database connectivity, models, and configuration loaders."""
from backend.core.config import get_settings, load_yaml_config
from backend.db.models import Base
from backend.db.session import check_db_connection


def test_settings_and_seed() -> None:
    """Verify settings load with random seed 42 and project identity."""
    settings = get_settings()
    assert settings.PROJECT_NAME == "HippoGrid"
    assert settings.RANDOM_SEED == 42


def test_yaml_config_loading() -> None:
    """Verify YAML configuration files load correctly."""
    params = load_yaml_config("params.yaml")
    assert "simulation" in params
    assert params["simulation"]["random_seed"] == 42
    assert "thresholds" in params

    services = load_yaml_config("service_map.yaml")
    assert "services" in services
    assert len(services["services"]) > 0


def test_orm_models_registered() -> None:
    """Verify that all core tables are mapped in the Declarative Base metadata."""
    tables = Base.metadata.tables.keys()
    assert "states" in tables
    assert "districts" in tables
    assert "phcs" in tables
    assert "warehouses" in tables
    assert "services" in tables
    assert "service_dependencies" in tables
    assert "medicines" in tables
    assert "service_continuity" in tables
    assert "audit_logs" in tables


def test_check_db_connection_contract() -> None:
    """Verify check_db_connection returns the expected contract structure."""
    result = check_db_connection()
    assert isinstance(result, dict)
    assert "connected" in result
    assert "status" in result
    assert "latency_ms" in result
