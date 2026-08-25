from __future__ import annotations

import os
import shutil
from pathlib import Path

from wp_bootstrap_mcp.errors import BootstrapError


def defaults_root() -> Path:
    env = os.environ.get("WP_BOOTSTRAP_DEFAULTS")
    if env:
        return Path(env).expanduser().resolve()
    # src/wp_bootstrap_mcp/defaults.py → repo root / defaults (editable install)
    candidate = Path(__file__).resolve().parents[2] / "defaults"
    if candidate.is_dir():
        return candidate
    packaged = Path(__file__).resolve().parent / "data"
    if packaged.is_dir():
        return packaged
    raise BootstrapError("could not find bundled defaults directory")


def vscode_settings_src() -> Path:
    path = defaults_root() / "vscode" / "settings.json"
    if not path.is_file():
        raise BootstrapError(f"missing bundled VS Code settings: {path}")
    return path


def wp_plugins_src() -> Path | None:
    path = defaults_root() / "wp-plugins.txt"
    return path if path.is_file() else None


def apply_editor_defaults(site_dir: Path) -> list[str]:
    """Copy bundled editor settings and plugin list. Never touches `.env`."""
    written: list[str] = []
    vscode_dir = site_dir / ".vscode"
    vscode_dir.mkdir(parents=True, exist_ok=True)
    dest_settings = vscode_dir / "settings.json"
    shutil.copy2(vscode_settings_src(), dest_settings)
    written.append(str(dest_settings))

    plugins = wp_plugins_src()
    if plugins is not None:
        bin_dir = site_dir / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)
        dest_plugins = bin_dir / "wp-plugins.txt"
        shutil.copy2(plugins, dest_plugins)
        written.append(str(dest_plugins))
    return written
