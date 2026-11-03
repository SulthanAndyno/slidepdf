"""Tests for engine detection and selection."""

from slidepdf.core.engines.detector import EngineDetector
from slidepdf.core.models import EngineType


def test_detector_defaults():
    detector = EngineDetector()
    best = detector.get_best_engine()
    assert best is not None
    assert best.engine_type in [EngineType.NATIVE, EngineType.LIBREOFFICE, EngineType.MSOFFICE]


def test_detector_native_always_available():
    detector = EngineDetector()
    native = detector.get_engine(EngineType.NATIVE)
    assert native.is_available() is True
    assert "pure-Python" in native.get_details()


def test_diagnostics_structure():
    detector = EngineDetector()
    diag = detector.diagnose_system()
    assert "os" in diag
    assert "python" in diag
    assert "best_engine" in diag
    assert "native_status" in diag
