"""Проверка состава репозитория: мусор, секреты, большие файлы.

Модуль не проверяет качество кода и не запускает сервисы. Он смотрит только
на то, что участник положил в репозиторий.

Использование:
    python repo_hygiene.py . --json
    python repo_hygiene.py submission --strict --json > report-hygiene.json
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class Violation:
    code: str
    path: str
    severity: str
    message: str


ERROR_DIRS = {
    ".idea": "IDE_DIR",
    ".vscode": "IDE_DIR",
    ".vs": "IDE_DIR",
    "venv": "VIRTUALENV_DIR",
    ".venv": "VIRTUALENV_DIR",
    "env": "VIRTUALENV_DIR",
    "__pycache__": "CACHE_DIR",
    ".pytest_cache": "CACHE_DIR",
    ".mypy_cache": "CACHE_DIR",
    ".ruff_cache": "CACHE_DIR",
    "node_modules": "NODE_MODULES_DIR",
}
WARNING_DIRS = {
    "target": "BUILD_DIR",
    "dist": "BUILD_DIR",
    "build": "BUILD_DIR",
    "coverage": "COVERAGE_DIR",
    "htmlcov": "COVERAGE_DIR",
}

ERROR_FILE_GLOBS = (
    "*.pyc",
    "*.pyo",
    ".env",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    "id_rsa",
    "id_ed25519",
    "report.xml",
    "report-hygiene.json",
)
WARNING_FILE_GLOBS = (
    "*.log",
    ".DS_Store",
    "Thumbs.db",
    "desktop.ini",
    ".coverage",
    "*.class",
    "*.jar",
)

HIDDEN_PATH_PREFIXES = (
    "cases/hidden/",
    "well-model-builder-grader/",
    "grader/",
)

REQUIRED_FILES = (
    "docker-compose.yml",
    "README.md",
    "services/ipr/Dockerfile",
    "services/vlp/Dockerfile",
    "services/nodal/Dockerfile",
)

TEXT_SUFFIXES = {
    ".env",
    ".ini",
    ".java",
    ".js",
    ".json",
    ".md",
    ".properties",
    ".py",
    ".toml",
    ".ts",
    ".txt",
    ".yaml",
    ".yml",
}

SECRET_PATTERNS = (
    re.compile(r"OPENAI_API_KEY\s*=\s*[^\s#]+"),
    re.compile(r"GITHUB_TOKEN\s*=\s*[^\s#]+"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)

LARGE_WARNING_BYTES = 5 * 1024 * 1024
LARGE_ERROR_BYTES = 10 * 1024 * 1024
TOTAL_WARNING_BYTES = 50 * 1024 * 1024
TOTAL_ERROR_BYTES = 100 * 1024 * 1024


def _tracked_files(root: Path) -> list[Path] | None:
    if not (root / ".git").exists():
        return None

    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"],
            capture_output=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None

    output = result.stdout.decode("utf-8", errors="replace")
    return [Path(item) for item in output.split("\0") if item]


def _walk_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for current_root, dirs, names in os.walk(root):
        dirs[:] = [name for name in dirs if name != ".git"]
        base = Path(current_root)
        for name in names:
            files.append((base / name).relative_to(root))
    return files


def _add(
    violations: list[Violation],
    seen: set[tuple[str, str, str]],
    code: str,
    path: str,
    severity: str,
    message: str,
) -> None:
    key = (code, path, severity)
    if key in seen:
        return
    seen.add(key)
    violations.append(Violation(code, path, severity, message))


def _scan_secret(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)


def check_repo(
    root: Path,
    *,
    strict: bool = True,
    use_git: bool = True,
) -> list[Violation]:
    root = Path(root).resolve()
    files = _tracked_files(root) if use_git else None
    if files is None:
        files = _walk_files(root)

    violations: list[Violation] = []
    seen: set[tuple[str, str, str]] = set()
    total_size = 0

    for relative in files:
        path = relative.as_posix()
        parts = relative.parts
        if not parts:
            continue

        for part in parts[:-1]:
            if part in ERROR_DIRS:
                _add(
                    violations,
                    seen,
                    ERROR_DIRS[part],
                    path,
                    "error",
                    f"Запрещённая папка: {part}/",
                )
            elif part in WARNING_DIRS:
                _add(
                    violations,
                    seen,
                    WARNING_DIRS[part],
                    path,
                    "warning",
                    f"Не коммитьте артефакты сборки: {part}/",
                )

        for prefix in HIDDEN_PATH_PREFIXES:
            if path.startswith(prefix):
                _add(
                    violations,
                    seen,
                    "HIDDEN_TESTS",
                    path,
                    "error",
                    "В репозитории найдены скрытые проверочные материалы",
                )
                break

        name = relative.name
        if any(fnmatch.fnmatch(name, pattern) for pattern in ERROR_FILE_GLOBS):
            _add(
                violations,
                seen,
                "JUNK_FILE",
                path,
                "error",
                f"Запрещённый файл: {name}",
            )
        elif any(fnmatch.fnmatch(name, pattern) for pattern in WARNING_FILE_GLOBS):
            _add(
                violations,
                seen,
                "JUNK_FILE",
                path,
                "warning",
                f"Нежелательный файл: {name}",
            )

        full_path = root / relative
        try:
            size = full_path.stat().st_size
        except OSError:
            continue
        total_size += size

        if size > LARGE_ERROR_BYTES:
            _add(
                violations,
                seen,
                "LARGE_FILE",
                path,
                "error",
                f"Файл больше 10 МБ: {size / 1024 / 1024:.1f} МБ",
            )
        elif size > LARGE_WARNING_BYTES:
            _add(
                violations,
                seen,
                "LARGE_FILE",
                path,
                "warning",
                f"Файл больше 5 МБ: {size / 1024 / 1024:.1f} МБ",
            )

        if name == ".env":
            _add(
                violations,
                seen,
                "SECRET_FILE",
                path,
                "error",
                "Не коммитьте .env; используйте .env.example",
            )
        elif relative.suffix in TEXT_SUFFIXES and size <= 1024 * 1024:
            if _scan_secret(full_path):
                _add(
                    violations,
                    seen,
                    "SECRET_PATTERN",
                    path,
                    "error",
                    "В файле найден похожий на секрет токен",
                )

    for required in REQUIRED_FILES:
        if not (root / required).exists():
            _add(
                violations,
                seen,
                "REQUIRED_FILE",
                required,
                "error" if strict else "warning",
                f"Нет обязательного файла: {required}",
            )

    if total_size > TOTAL_ERROR_BYTES:
        _add(
            violations,
            seen,
            "REPO_SIZE",
            ".",
            "error",
            f"Репозиторий больше 100 МБ: {total_size / 1024 / 1024:.1f} МБ",
        )
    elif total_size > TOTAL_WARNING_BYTES:
        _add(
            violations,
            seen,
            "REPO_SIZE",
            ".",
            "warning",
            f"Репозиторий больше 50 МБ: {total_size / 1024 / 1024:.1f} МБ",
        )

    return sorted(violations, key=lambda item: (item.severity, item.code, item.path))


def format_human(violations: list[Violation]) -> str:
    if not violations:
        return "OK: состав репозитория чистый"

    lines = []
    for item in violations:
        lines.append(
            f"[{item.severity.upper()}] {item.code}: {item.path} — {item.message}"
        )
    errors = sum(1 for item in violations if item.severity == "error")
    warnings = sum(1 for item in violations if item.severity == "warning")
    lines.append(f"\nИтого: {errors} error, {warnings} warning")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Проверка состава репозитория")
    parser.add_argument("path", nargs="?", default=".", help="Корень репозитория")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Считать отсутствие обязательных файлов ошибкой",
    )
    parser.add_argument("--json", action="store_true", help="Вывести JSON")
    parser.add_argument(
        "--no-git",
        action="store_true",
        help="Не использовать git ls-files, обходить файлы вручную",
    )
    args = parser.parse_args()

    violations = check_repo(
        Path(args.path),
        strict=args.strict,
        use_git=not args.no_git,
    )

    if args.json:
        print(json.dumps([asdict(item) for item in violations], ensure_ascii=False, indent=2))
    else:
        print(format_human(violations))

    return 1 if any(item.severity == "error" for item in violations) else 0


if __name__ == "__main__":
    raise SystemExit(main())
