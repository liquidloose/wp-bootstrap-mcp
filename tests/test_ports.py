from __future__ import annotations

from pathlib import Path

from wp_bootstrap_mcp.ports import allocate_ports, next_port, used_ports


def _write_env(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def test_used_ports_skips_env_sample(workspace: Path) -> None:
    _write_env(
        workspace / "13-josh-hines" / ".env",
        "WEB_PORT= 9013\nPHP_MYADMIN_PORT=8013\n",
    )
    _write_env(
        workspace / "13-josh-hines" / ".env.sample",
        "WEB_PORT= 9005\nPHP_MYADMIN_PORT=8085\n",
    )
    _write_env(
        workspace / "unrelated" / ".env.sample",
        "WEB_PORT= 9999\n",
    )
    assert used_ports(workspace, "WEB_PORT") == {9013}
    assert used_ports(workspace, "PHP_MYADMIN_PORT") == {8013}


def test_next_port_is_max_plus_one(workspace: Path) -> None:
    _write_env(workspace / "02-fr-mirror" / ".env", "WEB_PORT=9002\n")
    _write_env(workspace / "13-josh-hines" / ".env", "WEB_PORT= 9013\n")
    assert next_port(workspace, "WEB_PORT", default=9005) == 9014


def test_allocate_ports_defaults_when_none_used(workspace: Path) -> None:
    web, pma = allocate_ports(workspace)
    assert web == 9005
    assert pma == 8085


def test_allocate_ports_honors_overrides(workspace: Path) -> None:
    _write_env(workspace / "13-josh-hines" / ".env", "WEB_PORT=9013\n")
    web, pma = allocate_ports(workspace, web_port=8100, phpmyadmin_port=8200)
    assert web == 8100
    assert pma == 8200
