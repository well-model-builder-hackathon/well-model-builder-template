import json
import math
from pathlib import Path


CASES_DIR = Path(__file__).resolve().parent / "cases" / "public"


def load_json(name: str) -> dict:
    path = CASES_DIR / name
    return json.loads(path.read_text(encoding="utf-8"))


def assert_finite(values, label: str) -> None:
    assert isinstance(values, list) and values, f"{label}: ожидался непустой массив"
    for index, value in enumerate(values):
        assert isinstance(value, (int, float)) and not isinstance(value, bool), (
            f"{label}[{index}]: ожидалось число, получено {value!r}"
        )
        assert math.isfinite(float(value)), f"{label}[{index}]: {value!r} не finite"
