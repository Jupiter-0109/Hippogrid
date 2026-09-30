"""Test suite for HippoGrid Phase 16 End-to-End Demonstration Script.
Healthcare Infrastructure & Primary-care Planning Optimization Grid
"""
import io
import sys
from unittest.mock import patch
import pytest

from scripts.demo import run_demo


def test_demo_execution_end_to_end():
    """Verify that demo.py executes without error and prints all 5-day lifecycle stages."""
    captured_stdout = io.StringIO()
    with patch("sys.stdout", captured_stdout):
        run_demo()

    output = captured_stdout.getvalue()

    # Core narrative checks
    assert "HIPPOGRID" in output
    assert "DAY -4" in output
    assert "DAY -3" in output
    assert "DAY -2" in output
    assert "DAY -1" in output
    assert "DAY 0" in output
    assert "STRESS LAB" in output
    assert "AUDIT TRAIL" in output

    # Specific assertions
    assert "PHC-DST-A1-04" in output
    assert "Conformal Uncertainty Bounds" in output
    assert "Service Capability Horizon (SCH)" in output
    assert "Oral Rehydration Salts (ORS)" in output
    assert "HIPPOGRID_ORTOOLS" in output
    assert "WITHOUT PLAN" in output
    assert "HIPPOGRID PLAN" in output
    assert "Verified D=S+U" in output
    assert "RESILIENCE FRONTIER" in output.upper()
    assert "AUDIT LOG ENTRY" in output
    assert "ortools-v1.0" in output
