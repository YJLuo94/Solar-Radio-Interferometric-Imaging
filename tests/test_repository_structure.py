from pathlib import Path


def test_expected_directories_exist():
    root = Path(__file__).resolve().parents[1]
    expected = [
        "pre_processing",
        "calibration",
        "self_calibration",
        "imaging",
        "pb_correction",
        "ms_processing",
        "output",
        "demo",
        "docs",
    ]
    for directory in expected:
        assert (root / directory).is_dir()
