from __future__ import annotations

from pathlib import Path

from wp_bootstrap_mcp.envfile import parse_env_file
from wp_bootstrap_mcp.paths import SITE_DIR_RE


def list_sites(workspace_root: Path) -> list[dict[str, str | None]]:
    sites: list[dict[str, str | None]] = []
    if not workspace_root.is_dir():
        return sites
    children = sorted(
        (p for p in workspace_root.iterdir() if p.is_dir()),
        key=lambda p: p.name,
    )
    for child in children:
        match = SITE_DIR_RE.match(child.name)
        if not match:
            continue
        values = parse_env_file(child / ".env")
        sites.append(
            {
                "dirname": child.name,
                "slug": match.group(2),
                "path": str(child.resolve()),
                "web_port": values.get("WEB_PORT"),
                "phpmyadmin_port": values.get("PHP_MYADMIN_PORT"),
                "magicdns_hostname": values.get("TAILSCALE_MAGICDNS_HOSTNAME"),
            }
        )
    return sites
