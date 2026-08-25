from __future__ import annotations

import re
from pathlib import Path

from wp_bootstrap_mcp.errors import BootstrapError

SITE_DIR_RE = re.compile(r"^(\d+)-(.+)$")
SLUG_CLEAN_RE = re.compile(r"[^a-z0-9-]")
MULTI_HYPHEN_RE = re.compile(r"-{2,}")
# DNS label: lowercase letters, digits, hyphens; no dots; no leading/trailing hyphen.
HOSTNAME_RE = re.compile(r"^(?!-)[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")


def sanitize_slug(slug: str) -> str:
    cleaned = slug.strip().lower().replace("_", "-").replace(" ", "-")
    cleaned = SLUG_CLEAN_RE.sub("", cleaned)
    cleaned = MULTI_HYPHEN_RE.sub("-", cleaned).strip("-")
    if not cleaned:
        raise BootstrapError("slug is empty after sanitizing")
    return cleaned


def validate_magicdns_hostname(hostname: str | None) -> str:
    if hostname is None or not str(hostname).strip():
        raise BootstrapError(
            "MagicDNS hostname is required; ask the user for the first label "
            "(e.g. josh-hines). Do not derive it from the folder slug."
        )
    value = str(hostname).strip()
    if "." in value:
        raise BootstrapError(
            "MagicDNS hostname must be the first label only (no dots). "
            "The tailnet suffix is applied separately."
        )
    if not HOSTNAME_RE.match(value):
        raise BootstrapError(
            "MagicDNS hostname must be a DNS label: lowercase letters, digits, "
            "and hyphens only; it cannot start or end with a hyphen."
        )
    return value


def existing_site_numbers(workspace_root: Path) -> list[int]:
    numbers: list[int] = []
    if not workspace_root.is_dir():
        return numbers
    for child in workspace_root.iterdir():
        if not child.is_dir():
            continue
        match = SITE_DIR_RE.match(child.name)
        if match:
            numbers.append(int(match.group(1)))
    return numbers


def next_site_number(workspace_root: Path) -> int:
    numbers = existing_site_numbers(workspace_root)
    return (max(numbers) + 1) if numbers else 1


def format_site_dirname(number: int, slug: str) -> str:
    return f"{number:02d}-{slug}"


def next_site_path(workspace_root: Path, slug: str) -> Path:
    sanitized = sanitize_slug(slug)
    dirname = format_site_dirname(next_site_number(workspace_root), sanitized)
    dest = workspace_root / dirname
    if dest.exists():
        raise BootstrapError(f"destination already exists: {dest}")
    return dest


def resolve_site_dir(workspace_root: Path, site_dir: str) -> Path:
    path = Path(site_dir).expanduser()
    if not path.is_absolute():
        path = workspace_root / path
    path = path.resolve()
    if not path.is_dir():
        raise BootstrapError(f"site directory does not exist: {path}")
    return path
