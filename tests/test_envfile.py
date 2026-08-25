from __future__ import annotations

from pathlib import Path

from wp_bootstrap_mcp.envfile import parse_env_file, substitute_env_sample

SAMPLE = """WEB_PORT= 9005
PHP_MYADMIN_PORT=8085
DB_NAME= "database-name"
TS_AUTHKEY=
TAILSCALE_MAGICDNS_HOSTNAME=rivedge-site
TAILNET_DNS_SUFFIX=ferret-boa.ts.net
# comment stays
"""


def test_substitute_preserves_spacing_and_quotes() -> None:
    out = substitute_env_sample(
        SAMPLE,
        {
            "WEB_PORT": "9014",
            "PHP_MYADMIN_PORT": "8094",
            "DB_NAME": "josh-hines",
            "TS_AUTHKEY": "tskey-secret",
            "TAILSCALE_MAGICDNS_HOSTNAME": "josh-hines",
            "TAILNET_DNS_SUFFIX": "ferret-boa.ts.net",
        },
    )
    assert "WEB_PORT= 9014" in out
    assert "PHP_MYADMIN_PORT=8094" in out
    assert 'DB_NAME= "josh-hines"' in out
    assert "TS_AUTHKEY=tskey-secret" in out
    assert "TAILSCALE_MAGICDNS_HOSTNAME=josh-hines" in out
    assert "TAILNET_DNS_SUFFIX=ferret-boa.ts.net" in out
    assert "# comment stays" in out
    assert "rivedge-site" not in out


def test_parse_env_file_strips_quotes_and_spaces(tmp_path: Path) -> None:
    path = tmp_path / ".env"
    path.write_text('WEB_PORT= 9014\nDB_NAME= "josh-hines"\n', encoding="utf-8")
    values = parse_env_file(path)
    assert values["WEB_PORT"] == "9014"
    assert values["DB_NAME"] == "josh-hines"
