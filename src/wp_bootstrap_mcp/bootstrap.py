from __future__ import annotations

import logging
from pathlib import Path

from wp_bootstrap_mcp.config import Settings
from wp_bootstrap_mcp.defaults import apply_editor_defaults
from wp_bootstrap_mcp.envfile import write_site_env
from wp_bootstrap_mcp.errors import BootstrapError
from wp_bootstrap_mcp.gitutil import docker_compose_up, git_clone, prepare_clone_dest
from wp_bootstrap_mcp.paths import (
    next_site_path,
    resolve_site_dir,
    sanitize_slug,
    validate_magicdns_hostname,
)
from wp_bootstrap_mcp.ports import allocate_ports

log = logging.getLogger(__name__)


def bootstrap_site(
    settings: Settings,
    *,
    slug: str,
    magicdns_hostname: str,
    content_repo_url: str | None = None,
    web_port: int | None = None,
    phpmyadmin_port: int | None = None,
    start_compose: bool = False,
    clone_fn=git_clone,
) -> dict[str, str | int | bool | list[str] | list[dict[str, str]]]:
    hostname = validate_magicdns_hostname(magicdns_hostname)
    dest = next_site_path(settings.workspace_root, slug)
    web, pma = allocate_ports(
        settings.workspace_root,
        web_port=web_port,
        phpmyadmin_port=phpmyadmin_port,
    )
    db_name = sanitize_slug(slug)

    clone_fn(settings.env_repo_url, dest)
    sample = dest / ".env.sample"
    if not sample.is_file():
        raise BootstrapError(f"cloned repo is missing .env.sample: {sample}")

    replacements = {
        "WEB_PORT": str(web),
        "PHP_MYADMIN_PORT": str(pma),
        "TAILSCALE_MAGICDNS_HOSTNAME": hostname,
        "TAILNET_DNS_SUFFIX": settings.tailnet_dns_suffix,
        "DB_NAME": db_name,
        "TS_AUTHKEY": settings.ts_authkey,
    }
    write_site_env(sample, dest / ".env", replacements)
    written = apply_editor_defaults(dest)

    if content_repo_url:
        clone_content_repo(
            dest,
            content_repo_url,
            dest_subdir="WordPress/wp-content",
            clone_fn=clone_fn,
        )

    extra_cloned: list[dict[str, str]] = []
    for extra in settings.extra_clones:
        extra_cloned.append(
            clone_content_repo(
                dest,
                extra.url,
                dest_subdir=extra.dest_subdir,
                clone_fn=clone_fn,
            )
        )

    if start_compose:
        docker_compose_up(dest)

    return {
        "path": str(dest),
        "dirname": dest.name,
        "slug": dest.name.split("-", 1)[1] if "-" in dest.name else dest.name,
        "web_port": web,
        "phpmyadmin_port": pma,
        "magicdns_hostname": hostname,
        "tailnet_dns_suffix": settings.tailnet_dns_suffix,
        "defaults_written": written,
        "compose_started": start_compose,
        "extra_clones": extra_cloned,
    }


def apply_defaults(settings: Settings, site_dir: str) -> dict[str, list[str] | str]:
    dest = resolve_site_dir(settings.workspace_root, site_dir)
    written = apply_editor_defaults(dest)
    return {"path": str(dest), "defaults_written": written}


def clone_content_repo(
    site_dir: Path,
    git_url: str,
    dest_subdir: str = "WordPress/wp-content",
    clone_fn=git_clone,
) -> dict[str, str]:
    if not git_url or not git_url.strip():
        raise BootstrapError("content repo URL is required")
    dest = site_dir / dest_subdir
    allow_stock = dest_subdir in {"WordPress/wp-content", "WordPress/wp-content/"}
    prepare_clone_dest(dest, allow_stock_wp_content=allow_stock)
    clone_fn(git_url.strip(), dest)
    return {"path": str(dest), "url": git_url.strip()}
