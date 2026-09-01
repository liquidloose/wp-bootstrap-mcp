from __future__ import annotations

import json
import logging
import sys

from mcp.server.fastmcp import FastMCP

from wp_bootstrap_mcp.bootstrap import (
    apply_defaults as apply_defaults_impl,
    bootstrap_site as bootstrap_site_impl,
    clone_content_repo as clone_content_impl,
)
from wp_bootstrap_mcp.config import Settings
from wp_bootstrap_mcp.errors import BootstrapError
from wp_bootstrap_mcp.paths import resolve_site_dir
from wp_bootstrap_mcp.sites import list_sites as list_sites_impl

log = logging.getLogger("wp_bootstrap_mcp")

mcp = FastMCP("wp-bootstrap")


def _settings() -> Settings:
    return Settings.from_env()


def _ok(payload: object) -> str:
    return json.dumps(payload, indent=2)


def _err(exc: BootstrapError) -> str:
    return json.dumps({"error": str(exc)})


@mcp.tool()
def list_sites() -> str:
    """List numbered WordPress site folders under WORKSPACE_ROOT.

    Returns dirname, slug, path, WEB_PORT, PHP_MYADMIN_PORT, and
    TAILSCALE_MAGICDNS_HOSTNAME from each site's `.env` when present.
    """
    return _ok(list_sites_impl(_settings().workspace_root))


@mcp.tool()
def bootstrap_site(
    slug: str,
    magicdns_hostname: str,
    content_repo_url: str | None = None,
    web_port: int | None = None,
    phpmyadmin_port: int | None = None,
    start_compose: bool = False,
) -> str:
    """Clone wordpress-docker-tailscale, write `.env`, and apply editor defaults.

    Also clones dark-and-light and to-tha-top into wp-content/plugins, and
    rivers-edge-theme into wp-content/themes.

    magicdns_hostname is required: the MagicDNS first label only (e.g. josh-hines).
    Ask the user for it. Do not invent it or derive it from slug.
    Does not run docker compose unless start_compose is true.
    """
    try:
        result = bootstrap_site_impl(
            _settings(),
            slug=slug,
            magicdns_hostname=magicdns_hostname,
            content_repo_url=content_repo_url,
            web_port=web_port,
            phpmyadmin_port=phpmyadmin_port,
            start_compose=start_compose,
        )
    except BootstrapError as exc:
        return _err(exc)
    return _ok(result)


@mcp.tool()
def apply_defaults(site_dir: str) -> str:
    """Re-copy bundled VS Code settings and wp-plugins.txt onto an existing site.

    Never overwrites `.env`.
    """
    try:
        result = apply_defaults_impl(_settings(), site_dir)
    except BootstrapError as exc:
        return _err(exc)
    return _ok(result)


@mcp.tool()
def clone_content_repo(
    site_dir: str,
    git_url: str,
    dest_subdir: str = "WordPress/wp-content",
) -> str:
    """Clone a second git repo into a site subdirectory.

    Default dest is WordPress/wp-content. Refuses if that tree has more than
    the stock index.php unless dest_subdir is an empty path.
    """
    try:
        settings = _settings()
        dest = resolve_site_dir(settings.workspace_root, site_dir)
        result = clone_content_impl(dest, git_url, dest_subdir=dest_subdir)
    except BootstrapError as exc:
        return _err(exc)
    return _ok(result)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stderr,
        format="%(name)s %(levelname)s %(message)s",
    )
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
