from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_WORKSPACE_ROOT = Path("/home/ron/development/rivedge-wordpress")
DEFAULT_ENV_REPO_URL = "git@github.com:liquidloose/wordpress-docker-tailscale.git"
DEFAULT_TAILNET_DNS_SUFFIX = "ferret-boa.ts.net"


@dataclass(frozen=True)
class Settings:
    workspace_root: Path
    env_repo_url: str
    tailnet_dns_suffix: str
    ts_authkey: str

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
