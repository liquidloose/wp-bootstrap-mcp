from wp_bootstrap_mcp.gitutil import ssh_url_to_https


def test_ssh_url_to_https() -> None:
    assert (
        ssh_url_to_https("git@github.com:liquidloose/wordpress-docker-tailscale.git")
        == "https://github.com/liquidloose/wordpress-docker-tailscale.git"
    )
    assert (
        ssh_url_to_https("ssh://git@github.com/liquidloose/foo.git")
        == "https://github.com/liquidloose/foo.git"
    )
    assert ssh_url_to_https("https://github.com/liquidloose/foo.git") is None
    assert ssh_url_to_https("git@gitlab.com:group/foo.git") is None
