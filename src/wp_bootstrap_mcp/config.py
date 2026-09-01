from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_WORKSPACE_ROOT = Path("/home/ron/development/rivedge-wordpress")
DEFAULT_ENV_REPO_URL = "git@github.com:liquidloose/wordpress-docker-tailscale.git"
DEFAULT_TAILNET_DNS_SUFFIX = "ferret-boa.ts.net"


@dataclass(frozen=True)
class ExtraClone:
    """A git repo cloned into a site subdirectory after the env repo."""

    url: str
    dest_subdir: str


DEFAULT_EXTRA_CLONES: tuple[ExtraClone, ...] = (
    ExtraClone(
        url="git@github.com:liquidloose/dark-and-light.git",
        dest_subdir="WordPress/wp-content/plugins/dark-and-light",
    ),
    ExtraClone(
        url="git@github.com:liquidloose/to-tha-top.git",
        dest_subdir="WordPress/wp-content/plugins/to-tha-top",
    ),
    ExtraClone(
        url="git@github.com:liquidloose/rivers-edge-theme.git",
        dest_subdir="WordPress/wp-content/themes/rivers-edge-theme",
    ),
)


@dataclass(frozen=True)
class Settings:
    workspace_root: Path
    env_repo_url: str
    tailnet_dns_suffix: str
    ts_authkey: str
    extra_clones: tuple[ExtraClone, ...] = field(
        default_factory=lambda: DEFAULT_EXTRA_CLONES
    )

    @classmethod
    def from_env(cls) -> Settings:
        raw_root = os.environ.get("WORKSPACE_ROOT", str(DEFAULT_WORKSPACE_ROOT))
        return cls(
            workspace_root=Path(raw_root).expanduser().resolve(),
            env_repo_url=os.environ.get("ENV_REPO_URL", DEFAULT_ENV_REPO_URL),
            tailnet_dns_suffix=os.environ.get(
                "TAILNET_DNS_SUFFIX", DEFAULT_TAILNET_DNS_SUFFIX
            ),
            ts_authkey=os.environ.get("TS_AUTHKEY", ""),
        )
