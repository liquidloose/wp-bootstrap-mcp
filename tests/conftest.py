from __future__ import annotations

import shutil
from pathlib import Path

import pytest

FIXTURE_ENV_REPO = Path(__file__).parent / "fixtures" / "env-repo"


@pytest.fixture
def env_repo(tmp_path: Path) -> Path:
    dest = tmp_path / "env-repo-src"
    shutil.copytree(FIXTURE_ENV_REPO, dest)
    return dest


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    root = tmp_path / "workspace"
    root.mkdir()
    return root


def copy_clone(src: Path):
    def _clone(url: str, dest: Path) -> None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            if any(dest.iterdir()):
                raise RuntimeError(f"clone dest not empty: {dest}")
            dest.rmdir()
        shutil.copytree(src, dest)

    return _clone


def map_clone(mapping: dict[str, Path]):
    """Copy a fixture tree chosen by git URL (env repo vs plugin/theme repos)."""

    def _clone(url: str, dest: Path) -> None:
        src = mapping.get(url)
        if src is None:
            raise RuntimeError(f"no fixture for clone url: {url}")
        copy_clone(src)(url, dest)

    return _clone
