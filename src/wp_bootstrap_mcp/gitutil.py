from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

from wp_bootstrap_mcp.errors import BootstrapError

log = logging.getLogger(__name__)


def ssh_url_to_https(url: str) -> str | None:
    """Map git@github.com:owner/repo.git to HTTPS so public clones work without SSH."""
    if url.startswith("git@github.com:"):
        return "https://github.com/" + url.removeprefix("git@github.com:")
    if url.startswith("ssh://git@github.com/"):
        return "https://github.com/" + url.removeprefix("ssh://git@github.com/")
    return None


def _run_clone(url: str, dest: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "clone", "--depth", "1", url, str(dest)],
        check=True,
        capture_output=True,
        text=True,
    )


def git_clone(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        _run_clone(url, dest)
    except FileNotFoundError as exc:
        raise BootstrapError("git is not installed") from exc
    except subprocess.CalledProcessError as exc:
        https_url = ssh_url_to_https(url)
        if https_url and dest.exists():
            shutil.rmtree(dest)
        if https_url:
            log.warning("SSH clone failed; retrying with HTTPS")
            try:
                _run_clone(https_url, dest)
            except subprocess.CalledProcessError as https_exc:
                stderr = (https_exc.stderr or exc.stderr or "").strip()
                raise BootstrapError(f"git clone failed: {stderr or https_exc}") from https_exc
        else:
            stderr = (exc.stderr or "").strip()
            raise BootstrapError(f"git clone failed: {stderr or exc}") from exc
    log.info("cloned %s", dest)


def prepare_clone_dest(dest: Path, *, allow_stock_wp_content: bool) -> None:
    """Make dest missing or empty so `git clone` can write into it."""
    if not dest.exists():
        return
    if not dest.is_dir():
        raise BootstrapError(f"clone destination is not a directory: {dest}")
    entries = [p for p in dest.iterdir()]
    if not entries:
        return
    names = {p.name for p in entries}
    if allow_stock_wp_content and names <= {"index.php"}:
        for entry in entries:
            if entry.is_file() or entry.is_symlink():
                entry.unlink()
            else:
                shutil.rmtree(entry)
        return
    raise BootstrapError(
        f"refusing to clone into non-empty path {dest} "
        "(more than stock index.php). Pass an empty dest_subdir."
    )


def docker_compose_up(site_dir: Path) -> None:
    try:
        subprocess.run(
            ["docker", "compose", "up", "-d"],
            cwd=site_dir,
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise BootstrapError("docker is not installed") from exc
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        raise BootstrapError(f"docker compose up failed: {stderr or exc}") from exc
