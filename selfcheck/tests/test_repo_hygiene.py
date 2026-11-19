from pathlib import Path

from repo_hygiene import check_repo, format_human


ROOT = Path(__file__).resolve().parents[2]


def test_repository_is_clean():
    violations = check_repo(ROOT, strict=False)
    errors = [item for item in violations if item.severity == "error"]
    assert not errors, format_human(errors)


def test_hygiene_detects_junk(tmp_path):
    (tmp_path / ".idea").mkdir()
    (tmp_path / ".idea" / "workspace.xml").write_text("<project/>", encoding="utf-8")

    (tmp_path / "venv").mkdir()
    (tmp_path / "venv" / "python").write_text("binary", encoding="utf-8")

    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "module.pyc").write_text("binary", encoding="utf-8")

    (tmp_path / ".env").write_text("demo=true\n", encoding="utf-8")
    (tmp_path / "debug.log").write_text("log\n", encoding="utf-8")

    violations = check_repo(tmp_path, strict=True, use_git=False)
    codes = {item.code for item in violations}

    assert "IDE_DIR" in codes
    assert "VIRTUALENV_DIR" in codes
    assert "CACHE_DIR" in codes
    assert "SECRET_FILE" in codes
    assert "JUNK_FILE" in codes
    assert "REQUIRED_FILE" in codes
