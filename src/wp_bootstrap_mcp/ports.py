from __future__ import annotations

import re
from pathlib import Path

from wp_bootstrap_mcp.envfile import parse_env_file

DEFAULT_WEB_PORT = 9005
DEFAULT_PHPMYADMIN_PORT = 8085
_PORT_RE = re.compile(r"^\d+$")


def _parse_port(raw: str | None) -> int | None:
    if raw is None:
        return None
    value = raw.strip()
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        value = value[1:-1].strip()
    if not _PORT_RE.match(value):
        return None
    return int(value)


def used_ports(workspace_root: Path, key: str) -> set[int]:
    """Ports declared in immediate child `.env` files (not `.env.sample`)."""
    found: set[int] = set()
    if not workspace_root.is_dir():
        return found
    for child in workspace_root.iterdir():
        if not child.is_dir():
            continue
        env_path = child / ".env"
        if not env_path.is_file():
            continue
        values = parse_env_file(env_path)
        port = _parse_port(values.get(key))
        if port is not None:
            found.add(port)
    return found


def next_port(workspace_root: Path, key: str, default: int) -> int:
    used = used_ports(workspace_root, key)
    if not used:
        return default
    return max(used) + 1


def allocate_ports(
    workspace_root: Path,
    *,
    web_port: int | None = None,
    phpmyadmin_port: int | None = None,
) -> tuple[int, int]:
    web = web_port if web_port is not None else next_port(
        workspace_root, "WEB_PORT", DEFAULT_WEB_PORT
    )
    pma = phpmyadmin_port if phpmyadmin_port is not None else next_port(
        workspace_root, "PHP_MYADMIN_PORT", DEFAULT_PHPMYADMIN_PORT
    )
    return web, pma
