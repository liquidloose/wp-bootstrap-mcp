from __future__ import annotations

from pathlib import Path

import pytest

from conftest import copy_clone, map_clone
from wp_bootstrap_mcp.bootstrap import (
    apply_defaults,
    bootstrap_site,
    clone_content_repo,
)
from wp_bootstrap_mcp.config import DEFAULT_EXTRA_CLONES, ExtraClone, Settings
from wp_bootstrap_mcp.envfile import parse_env_file
from wp_bootstrap_mcp.errors import BootstrapError
from wp_bootstrap_mcp.paths import next_site_path, validate_magicdns_hostname
from wp_bootstrap_mcp.sites import list_sites


def _settings(
    workspace: Path,
    ts_authkey: str = "",
    extra_clones: tuple[ExtraClone, ...] = (),
) -> Settings:
    return Settings(
        workspace_root=workspace,
        env_repo_url="git@example.com:env.git",
        tailnet_dns_suffix="ferret-boa.ts.net",
        ts_authkey=ts_authkey,
        extra_clones=extra_clones,
    )


def test_missing_hostname_does_nothing(workspace: Path, env_repo: Path) -> None:
    with pytest.raises(BootstrapError, match="MagicDNS hostname is required"):
        bootstrap_site(
            _settings(workspace),
            slug="josh-hines",
            magicdns_hostname="",
            clone_fn=copy_clone(env_repo),
        )
    assert list(workspace.iterdir()) == []


def test_blank_hostname_whitespace_does_nothing(
    workspace: Path, env_repo: Path
) -> None:
    with pytest.raises(BootstrapError, match="MagicDNS hostname is required"):
        bootstrap_site(
            _settings(workspace),
            slug="josh-hines",
            magicdns_hostname="   ",
            clone_fn=copy_clone(env_repo),
        )
    assert list(workspace.iterdir()) == []


def test_invalid_hostname_rejected() -> None:
    with pytest.raises(BootstrapError, match="first label"):
        validate_magicdns_hostname("josh.hines")
    with pytest.raises(BootstrapError, match="DNS label"):
        validate_magicdns_hostname("Josh-Hines")
    with pytest.raises(BootstrapError, match="DNS label"):
        validate_magicdns_hostname("-josh")


def test_next_folder_is_14_when_13_exists(workspace: Path) -> None:
    (workspace / "13-josh-hines").mkdir()
    dest = next_site_path(workspace, "new-site")
    assert dest.name == "14-new-site"


def test_existing_dest_refused(workspace: Path) -> None:
    (workspace / "13-josh-hines").mkdir()
    # next number is 14; a non-directory occupying that name must be refused
    (workspace / "14-taken").write_text("blocked", encoding="utf-8")
    with pytest.raises(BootstrapError, match="already exists"):
        next_site_path(workspace, "taken")


def test_bootstrap_writes_hostname_only_to_magicdns(
    workspace: Path, env_repo: Path
) -> None:
    (workspace / "13-josh-hines").mkdir()
    (workspace / "13-josh-hines" / ".env").write_text(
        "WEB_PORT= 9013\nPHP_MYADMIN_PORT=8013\n",
        encoding="utf-8",
    )
    result = bootstrap_site(
        _settings(workspace, ts_authkey="tskey-test"),
        slug="New Site",
        magicdns_hostname="josh-hines",
        clone_fn=copy_clone(env_repo),
    )
    dest = Path(result["path"])
    assert dest.name == "14-new-site"
    assert result["magicdns_hostname"] == "josh-hines"
    assert result["web_port"] == 9014
    assert result["phpmyadmin_port"] == 8014

    values = parse_env_file(dest / ".env")
    assert values["TAILSCALE_MAGICDNS_HOSTNAME"] == "josh-hines"
    assert values["TAILNET_DNS_SUFFIX"] == "ferret-boa.ts.net"
    assert values["WEB_PORT"] == "9014"
    assert values["PHP_MYADMIN_PORT"] == "8014"
    assert values["DB_NAME"] == "new-site"
    assert values["TS_AUTHKEY"] == "tskey-test"
    assert "Ayu Dark Bordered" in (dest / ".vscode" / "settings.json").read_text()
    assert "query-monitor" in (dest / "bin" / "wp-plugins.txt").read_text()


def test_apply_defaults_does_not_touch_env(
    workspace: Path, env_repo: Path
) -> None:
    result = bootstrap_site(
        _settings(workspace),
        slug="keep-env",
        magicdns_hostname="keep-env",
        clone_fn=copy_clone(env_repo),
    )
    dest = Path(result["path"])
    env_path = dest / ".env"
    original = env_path.read_text(encoding="utf-8")
    env_path.write_text(original + "\n# user note\n", encoding="utf-8")
    before = env_path.read_text(encoding="utf-8")

    apply_defaults(_settings(workspace), str(dest))
    assert env_path.read_text(encoding="utf-8") == before


def test_content_clone_refuses_non_empty_wp_content(
    workspace: Path, env_repo: Path, tmp_path: Path
) -> None:
    result = bootstrap_site(
        _settings(workspace),
        slug="busy",
        magicdns_hostname="busy-site",
        clone_fn=copy_clone(env_repo),
    )
    dest = Path(result["path"])
    extra = dest / "WordPress" / "wp-content" / "themes"
    extra.mkdir(parents=True)
    (extra / "keep.txt").write_text("nope", encoding="utf-8")

    with pytest.raises(BootstrapError, match="non-empty"):
        clone_content_repo(
            dest,
            "git@example.com:content.git",
            dest_subdir="WordPress/wp-content",
            clone_fn=copy_clone(tmp_path / "unused"),
        )


def test_content_clone_allows_stock_index_only(
    workspace: Path, env_repo: Path, tmp_path: Path
) -> None:
    result = bootstrap_site(
        _settings(workspace),
        slug="stock",
        magicdns_hostname="stock-site",
        clone_fn=copy_clone(env_repo),
    )
    dest = Path(result["path"])
    content_src = tmp_path / "content-src"
    content_src.mkdir()
    (content_src / "README.md").write_text("theme", encoding="utf-8")

    clone_content_repo(
        dest,
        "git@example.com:content.git",
        dest_subdir="WordPress/wp-content",
        clone_fn=copy_clone(content_src),
    )
    assert (dest / "WordPress" / "wp-content" / "README.md").is_file()
    assert not (dest / "WordPress" / "wp-content" / "index.php").exists()


def _extra_fixtures(tmp_path: Path) -> tuple[tuple[ExtraClone, ...], dict[str, Path]]:
    dark = tmp_path / "dark-and-light"
    dark.mkdir()
    (dark / "dark-and-light.php").write_text("plugin", encoding="utf-8")
    top = tmp_path / "to-tha-top"
    top.mkdir()
    (top / "to-tha-top.php").write_text("plugin", encoding="utf-8")
    theme = tmp_path / "rivers-edge-theme"
    theme.mkdir()
    (theme / "style.css").write_text("theme", encoding="utf-8")
    extras = (
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
    mapping = {
        extras[0].url: dark,
        extras[1].url: top,
        extras[2].url: theme,
    }
    return extras, mapping


def test_default_extra_clones_are_the_rivedge_stack() -> None:
    dests = {extra.dest_subdir for extra in DEFAULT_EXTRA_CLONES}
    urls = {extra.url for extra in DEFAULT_EXTRA_CLONES}
    assert dests == {
        "WordPress/wp-content/plugins/dark-and-light",
        "WordPress/wp-content/plugins/to-tha-top",
        "WordPress/wp-content/themes/rivers-edge-theme",
    }
    assert urls == {
        "git@github.com:liquidloose/dark-and-light.git",
        "git@github.com:liquidloose/to-tha-top.git",
        "git@github.com:liquidloose/rivers-edge-theme.git",
    }


def test_bootstrap_clones_plugins_and_theme(
    workspace: Path, env_repo: Path, tmp_path: Path
) -> None:
    extras, extra_map = _extra_fixtures(tmp_path)
    mapping = {"git@example.com:env.git": env_repo, **extra_map}
    result = bootstrap_site(
        _settings(workspace, extra_clones=extras),
        slug="extras",
        magicdns_hostname="extras-site",
        clone_fn=map_clone(mapping),
    )
    dest = Path(result["path"])
    assert (dest / extras[0].dest_subdir / "dark-and-light.php").is_file()
    assert (dest / extras[1].dest_subdir / "to-tha-top.php").is_file()
    assert (dest / extras[2].dest_subdir / "style.css").is_file()
    cloned_paths = {item["path"] for item in result["extra_clones"]}
    assert cloned_paths == {str(dest / extra.dest_subdir) for extra in extras}


def test_bootstrap_clones_extras_after_content_repo(
    workspace: Path, env_repo: Path, tmp_path: Path
) -> None:
    extras, extra_map = _extra_fixtures(tmp_path)
    content_src = tmp_path / "content-src"
    content_src.mkdir()
    (content_src / "index.php").write_text("content", encoding="utf-8")
    mapping = {
        "git@example.com:env.git": env_repo,
        "git@example.com:content.git": content_src,
        **extra_map,
    }
    result = bootstrap_site(
        _settings(workspace, extra_clones=extras),
        slug="with-content",
        magicdns_hostname="with-content",
        content_repo_url="git@example.com:content.git",
        clone_fn=map_clone(mapping),
    )
    dest = Path(result["path"])
    assert (dest / "WordPress" / "wp-content" / "index.php").read_text(
        encoding="utf-8"
    ) == "content"
    assert (dest / extras[0].dest_subdir / "dark-and-light.php").is_file()
    assert (dest / extras[2].dest_subdir / "style.css").is_file()


def test_list_sites_reads_env(workspace: Path) -> None:
    site = workspace / "13-josh-hines"
    site.mkdir()
    (site / ".env").write_text(
        "WEB_PORT= 9013\n"
        "PHP_MYADMIN_PORT=8013\n"
        "TAILSCALE_MAGICDNS_HOSTNAME=josh-hines\n",
        encoding="utf-8",
    )
    (workspace / "notes").mkdir()
    sites = list_sites(workspace)
    assert len(sites) == 1
    assert sites[0]["slug"] == "josh-hines"
    assert sites[0]["web_port"] == "9013"
    assert sites[0]["magicdns_hostname"] == "josh-hines"
