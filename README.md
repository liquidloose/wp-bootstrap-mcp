# wp-bootstrap-mcp

Cursor MCP server that clones [wordpress-docker-tailscale](https://github.com/liquidloose/wordpress-docker-tailscale) into a numbered site folder, writes `.env` from `.env.sample`, overlays default editor settings, and clones the River's Edge theme plus the dark-and-light and to-tha-top plugins.

`TAILSCALE_MAGICDNS_HOSTNAME` is **required**. The agent must ask you for the MagicDNS first label (for example `josh-hines`) before calling `bootstrap_site`. It is never derived from the folder slug.

## Install

```bash
cd /path/to/wp-bootstrap-mcp
uv sync --extra dev
uv pip install -e .
```

This puts `wp-bootstrap-mcp` on your PATH via the project environment (`uv run wp-bootstrap-mcp`).

## Cursor registration

Add this to `~/.cursor/mcp.json` (merge with any existing `mcpServers`):

```json
{
  "mcpServers": {
    "wp-bootstrap": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/home/ron/development/wp-bootstrap-mcp",
        "wp-bootstrap-mcp"
      ],
      "env": {
        "WORKSPACE_ROOT": "/home/ron/development/rivedge-wordpress",
        "ENV_REPO_URL": "git@github.com:liquidloose/wordpress-docker-tailscale.git",
        "TAILNET_DNS_SUFFIX": "ferret-boa.ts.net",
        "TS_AUTHKEY": "${env:TS_AUTHKEY}"
      }
    }
  }
}
```

Then enable **wp-bootstrap** under **Customize → MCP**. Ask the agent to bootstrap a site; it should prompt you for the MagicDNS name, then call `bootstrap_site`.

If you prefer a bare command after `uv pip install -e .` into a venv that is already on `PATH`:

```json
"command": "wp-bootstrap-mcp"
```

## Environment

| Variable | Purpose |
| --- | --- |
| `WORKSPACE_ROOT` | Parent folder for `NN-slug` sites (default `/home/ron/development/rivedge-wordpress`) |
| `ENV_REPO_URL` | Git URL of the env repo |
| `TAILNET_DNS_SUFFIX` | Tailnet suffix (default `ferret-boa.ts.net`) |
| `TS_AUTHKEY` | Copied into the site `.env` when set; never invented |
| `WP_BOOTSTRAP_DEFAULTS` | Optional override for the bundled `defaults/` directory |

Do not commit site `.env` files. The server logs to stderr only.

## Tools

1. **`list_sites`** — Numbered folders under `WORKSPACE_ROOT` plus ports and MagicDNS from each `.env`.
2. **`bootstrap_site`** — Required `slug` and `magicdns_hostname`. Optional `content_repo_url`, `web_port`, `phpmyadmin_port`, `start_compose` (default `false`). Always clones [dark-and-light](https://github.com/liquidloose/dark-and-light) and [to-tha-top](https://github.com/liquidloose/to-tha-top) into `WordPress/wp-content/plugins/`, and [rivers-edge-theme](https://github.com/liquidloose/rivers-edge-theme) into `WordPress/wp-content/themes/`.
3. **`apply_defaults`** — Re-copy `.vscode/settings.json` and `bin/wp-plugins.txt`. Never overwrites `.env`.
4. **`clone_content_repo`** — Clone a second repo. Default dest `WordPress/wp-content`; refuses a tree with more than stock `index.php`.

## Tests

```bash
uv run pytest
```

## Publish to GitHub

From this directory, after `gh auth login`:

```bash
gh repo create liquidloose/wp-bootstrap-mcp --private --source=. --remote=origin --push
```
