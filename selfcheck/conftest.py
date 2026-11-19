import os
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from helpers import load_json  # noqa: E402


def pytest_addoption(parser):
    parser.addoption(
        "--compose-file",
        default=None,
        help="Путь к docker-compose.yml участника",
    )
    parser.addoption(
        "--no-stack",
        action="store_true",
        help="Не запускать compose, использовать уже запущенные сервисы",
    )
    parser.addoption(
        "--keep-stack",
        action="store_true",
        help="Не гасить compose после тестов",
    )
    parser.addoption(
        "--stack-timeout",
        type=int,
        default=180,
        help="Сколько секунд ждать readiness сервисов",
    )
    parser.addoption(
        "--services",
        default="ipr,vlp,nodal",
        help="Сервисы compose для запуска: ipr,vlp,nodal",
    )
    parser.addoption("--ipr-url", default=os.getenv("IPR_URL", "http://localhost:8003"))
    parser.addoption("--vlp-url", default=os.getenv("VLP_URL", "http://localhost:8002"))
    parser.addoption("--nodal-url", default=os.getenv("NODAL_URL", "http://localhost:8004"))


@pytest.fixture(scope="session")
def ipr_url(request):
    return request.config.getoption("--ipr-url").rstrip("/")


@pytest.fixture(scope="session")
def vlp_url(request):
    return request.config.getoption("--vlp-url").rstrip("/")


@pytest.fixture(scope="session")
def nodal_url(request):
    return request.config.getoption("--nodal-url").rstrip("/")


@pytest.fixture(scope="session")
def client():
    with httpx.Client(timeout=60.0) as http_client:
        yield http_client


def _compose_command(compose_file: Path, *args: str) -> list[str]:
    return [
        "docker",
        "compose",
        "-f",
        str(compose_file),
        "-p",
        "wmb-selfcheck",
        *args,
    ]


def _wait_ready(client, ipr_url, vlp_url, nodal_url, timeout: int) -> None:
    ipr_request = load_json("ipr_request.json")
    vlp_request = load_json("vlp_request.json")
    nodal_request = load_json("nodal_request.json")

    checks = [
        ("VLP", lambda: client.get(f"{vlp_url}/vlp/health")),
        ("IPR", lambda: client.post(f"{ipr_url}/ipr/calc", json=ipr_request)),
        ("Nodal", lambda: client.post(f"{nodal_url}/nodal/calc", json=nodal_request)),
    ]

    started = time.monotonic()
    last_errors = {}
    while time.monotonic() - started < timeout:
        for name, check in checks:
            try:
                response = check()
            except httpx.HTTPError as error:
                last_errors[name] = str(error)
                continue
            if response.status_code == 200:
                last_errors.pop(name, None)
            else:
                last_errors[name] = f"HTTP {response.status_code}: {response.text[:200]}"
        if not last_errors:
            return
        time.sleep(2)

    details = "; ".join(f"{name}: {error}" for name, error in last_errors.items())
    raise AssertionError(
        f"Сервисы не поднялись за {timeout} секунд. {details}"
    )


@pytest.fixture(scope="session")
def stack(request, client, ipr_url, vlp_url, nodal_url):
    if request.config.getoption("--no-stack"):
        yield
        return

    compose_option = request.config.getoption("--compose-file")
    if not compose_option:
        pytest.fail(
            "Укажите --compose-file путь/к/docker-compose.yml "
            "или запустите с --no-stack"
        )

    compose_file = Path(compose_option).resolve()
    if not compose_file.exists():
        pytest.fail(f"Compose-файл не найден: {compose_file}")

    services_option = request.config.getoption("--services")
    services = [
        item
        for item in services_option.replace(",", " ").split()
        if item
    ]

    subprocess.run(
        _compose_command(compose_file, "up", "-d", "--build", *services),
        cwd=compose_file.parent,
        check=True,
    )

    try:
        _wait_ready(
            client,
            ipr_url,
            vlp_url,
            nodal_url,
            request.config.getoption("--stack-timeout"),
        )
        yield
    finally:
        if not request.config.getoption("--keep-stack"):
            subprocess.run(
                _compose_command(compose_file, "down", "-v", "--remove-orphans"),
                cwd=compose_file.parent,
                check=False,
            )


@pytest.fixture
def ipr_request():
    return load_json("ipr_request.json")


@pytest.fixture
def vlp_request():
    return load_json("vlp_request.json")


@pytest.fixture
def nodal_request():
    return load_json("nodal_request.json")
